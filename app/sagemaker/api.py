"""API del notebook de SageMaker: identidad y chat con Ollama, imagen con SD-Turbo en CPU.

Escucha en 127.0.0.1:8000 y se publica con ngrok. Toda petición debe traer la cabecera
X-API-Key con el valor de la variable de entorno API_KEY.

Uso: uvicorn api:app --host 127.0.0.1 --port 8000
"""
import base64
import io
import json
import os
import threading
import time

import requests
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from prompts import (CLAVES_IDENTIDAD, PLANTILLA_IDENTIDAD, PLANTILLA_IMAGEN, PRESENTACION,
                     SISTEMA_CHAT, SISTEMA_IDENTIDAD)

OLLAMA = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODELO_OLLAMA = os.getenv("OLLAMA_MODEL", "gemma4:e2b")
MODELO_IMAGEN = os.getenv("IMAGE_MODEL", "stabilityai/sd-turbo")
API_KEY = os.environ["API_KEY"]


def verificar_clave(x_api_key: str = Header(default="")):
    if x_api_key != API_KEY:
        raise HTTPException(401, "API key inválida")


app = FastAPI(title="Isla de los Dinosaurios - SageMaker", dependencies=[Depends(verificar_clave)])


# ---------- Ollama ----------

def ollama_chat(mensajes, opciones, formato=None):
    # gemma4 es un modelo con razonamiento: sin think=False escribe un análisis largo antes de
    # responder y en CPU cada petición tarda minutos. keep_alive=-1 lo deja cargado en memoria.
    cuerpo = {"model": MODELO_OLLAMA, "messages": mensajes, "stream": False, "options": opciones,
              "think": False, "keep_alive": -1}
    if formato:
        cuerpo["format"] = formato
    r = requests.post(f"{OLLAMA}/api/chat", json=cuerpo, timeout=300)
    r.raise_for_status()
    return r.json()["message"]["content"]


class PedidoIdentidad(BaseModel):
    nombre: str


@app.post("/identidad")
def identidad(p: PedidoIdentidad):
    """Recibe un nombre y devuelve la identidad en JSON con las claves de CLAVES_IDENTIDAD."""
    inicio = time.time()
    mensajes = [{"role": "system", "content": SISTEMA_IDENTIDAD},
                {"role": "user", "content": PLANTILLA_IDENTIDAD.format(nombre=p.nombre)}]
    for _ in range(2):  # un reintento si el modelo deja claves vacías
        ident = json.loads(ollama_chat(mensajes, {"temperature": 0.4}, formato="json"))
        if all(ident.get(k) for k in CLAVES_IDENTIDAD):
            break
    faltan = [k for k in CLAVES_IDENTIDAD if not ident.get(k)]
    if faltan:
        raise HTTPException(502, f"Ollama no completó: {faltan}")
    ident["nombre"] = p.nombre
    return {"identidad": ident, "modelo": MODELO_OLLAMA, "segundos": round(time.time() - inicio, 1)}


class PedidoChat(BaseModel):
    identidad: dict
    mensajes: list[dict] = []   # [{"role": "user"|"assistant", "content": "..."}]
    presentacion: bool = False


@app.post("/chat")
def chat(p: PedidoChat):
    """Recibe la identidad y el historial; responde como el dinosaurio sin contradecir su identidad."""
    inicio = time.time()
    sistema = SISTEMA_CHAT.format(**{k: p.identidad.get(k, "") for k in CLAVES_IDENTIDAD})
    historial = [m for m in p.mensajes if m.get("role") in ("user", "assistant")][-10:]
    if p.presentacion:
        historial = [{"role": "user", "content": PRESENTACION}]
    respuesta = ollama_chat([{"role": "system", "content": sistema}] + historial,
                            {"temperature": 0.7, "num_predict": 250})
    return {"respuesta": respuesta.strip(), "modelo": MODELO_OLLAMA, "segundos": round(time.time() - inicio, 1)}


# ---------- Imagen ----------

_pipe, _candado, _candado_carga = None, threading.Lock(), threading.Lock()


def cargar_pipe():
    global _pipe
    with _candado_carga:
        if _pipe is None:
            import torch
            from diffusers import AutoPipelineForText2Image
            torch.set_num_threads(os.cpu_count())
            _pipe = AutoPipelineForText2Image.from_pretrained(MODELO_IMAGEN, torch_dtype=torch.float32)
    return _pipe


class PedidoImagen(BaseModel):
    nombre: str
    prompt_imagen: str
    semilla: int = 0


@app.post("/imagen")
def imagen(p: PedidoImagen):
    """Recibe nombre y rasgos visuales; devuelve un PNG 512x512 en base64."""
    import torch
    prompt = PLANTILLA_IMAGEN.format(nombre=p.nombre, prompt_imagen=p.prompt_imagen.strip())
    with _candado:  # una imagen a la vez: en CPU no gana nada paralelizar
        inicio = time.time()
        img = cargar_pipe()(prompt, num_inference_steps=4, guidance_scale=0.0,
                            generator=torch.Generator().manual_seed(p.semilla)).images[0]
        segundos = round(time.time() - inicio, 1)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return {"png_base64": base64.b64encode(buf.getvalue()).decode(), "prompt": prompt,
            "modelo": MODELO_IMAGEN, "pasos": 4, "semilla": p.semilla, "segundos": segundos}


# ---------- Estado ----------

@app.get("/salud")
def salud():
    try:
        version = requests.get(f"{OLLAMA}/api/version", timeout=5).json()["version"]
        modelos = [m["name"] for m in requests.get(f"{OLLAMA}/api/tags", timeout=5).json()["models"]]
        en_memoria = [m["name"] for m in requests.get(f"{OLLAMA}/api/ps", timeout=5).json()["models"]]
    except requests.RequestException:
        version, modelos, en_memoria = None, [], []
    return {"ollama": version, "modelo_ollama": MODELO_OLLAMA, "modelo_disponible": MODELO_OLLAMA in modelos,
            "modelo_cargado": MODELO_OLLAMA in en_memoria,
            "modelo_imagen": MODELO_IMAGEN, "imagen_cargada": _pipe is not None}


# Carga SD-Turbo en segundo plano al arrancar, para que la primera imagen no espere la descarga
threading.Thread(target=cargar_pipe, daemon=True).start()
