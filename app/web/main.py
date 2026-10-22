"""Web de la Isla de los Dinosaurios: ficha del dinosaurio, chat y botón Nuevo Dinosaurio.

Flujo: modelo de caracteres (aquí) -> nombre -> Ollama en SageMaker -> identidad -> SD-Turbo en SageMaker
-> imagen -> chat. Variables de entorno (o app/web/.env): SAGEMAKER_URL y API_KEY.

Uso: uvicorn main:app --host 0.0.0.0 --port 8000
"""
import base64
import json
import random
import re
import sys
import threading
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
load_dotenv(AQUI / ".env")
sys.path.insert(0, str(RAIZ / "generador_nombres"))

import sagemaker  # noqa: E402
from generar import nuevo_nombre  # noqa: E402

DATOS = AQUI / "datos"          # un directorio por dinosaurio: dino.json + imagen.png
PRINCIPAL = "aborosaurus"       # el dinosaurio del laboratorio: la página siempre empieza por él
PASOS = ["Nombre (GRU)", "Identidad (Ollama)", "Imagen (SD-Turbo)", "Presentación"]
PIDE_IMAGEN = re.compile(r"descr[ií]b|c[oó]mo eres|c[oó]mo te ves|\bverte\b|aspecto|apariencia|"
                         r"\bfoto|imagen|mu[eé]strate|pres[eé]ntate|qui[eé]n eres", re.IGNORECASE)

app = FastAPI(title="Isla de los Dinosaurios")


@app.middleware("http")
async def revalidar(request, call_next):
    """Que el navegador revalide la página, el JS y el CSS: tras un despliegue, una versión vieja
    guardada en caché llamaría a rutas que ya no existen."""
    respuesta = await call_next(request)
    if not request.url.path.startswith("/imagenes/"):
        respuesta.headers["Cache-Control"] = "no-cache"
    return respuesta


# ---------- Dinosaurios guardados ----------

def slug(nombre):
    return re.sub(r"[^a-z]", "", nombre.lower())


def leer(s):
    ruta = DATOS / slug(s) / "dino.json"
    if not ruta.exists():
        raise HTTPException(404, f"No existe el dinosaurio {s}")
    return json.loads(ruta.read_text(encoding="utf-8"))


def guardar(dino):
    carpeta = DATOS / dino["id"]
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "dino.json").write_text(json.dumps(dino, indent=2, ensure_ascii=False), encoding="utf-8")


def listar():
    """Aborosaurus primero y después los creados con el botón, del más nuevo al más antiguo."""
    dinos = [json.loads(p.read_text(encoding="utf-8")) for p in DATOS.glob("*/dino.json")]
    otros = sorted((d for d in dinos if d["id"] != PRINCIPAL), key=lambda d: d.get("creado", ""), reverse=True)
    return [d for d in dinos if d["id"] == PRINCIPAL] + otros


def publico(dino):
    """Lo que ve el navegador: el dinosaurio con la URL de su imagen."""
    return {**dino, "imagen_url": f"/imagenes/{dino['id']}.png"}


def sembrar_aborosaurus():
    """El primer dinosaurio es el del laboratorio: identidad de ollama/ e imagen de imagen/."""
    if (DATOS / "aborosaurus" / "dino.json").exists():
        return
    ident = json.loads((RAIZ / "ollama" / "identidad.json").read_text(encoding="utf-8"))
    info = json.loads((RAIZ / "imagen" / "imagen_info.json").read_text(encoding="utf-8"))
    dino = {"id": "aborosaurus", "nombre": ident["identidad"]["nombre"], "identidad": ident["identidad"],
            "modelo_ollama": ident["modelo_ollama"], "imagen": info, "presentacion": None,
            "creado": ident["fecha"]}
    guardar(dino)
    (DATOS / "aborosaurus" / "imagen.png").write_bytes((RAIZ / "imagen" / "aborosaurus.png").read_bytes())


DATOS.mkdir(exist_ok=True)
sembrar_aborosaurus()


# ---------- Ficha, modelo y estado ----------

@app.get("/api/dinosaurios")
def dinosaurios():
    """Galería: todos los dinosaurios guardados, con Aborosaurus primero."""
    return [{"id": d["id"], "nombre": d["nombre"], "imagen_url": publico(d)["imagen_url"],
             "creado": d.get("creado"), "principal": d["id"] == PRINCIPAL} for d in listar()]


@app.get("/api/dinosaurios/{s}")
def dinosaurio(s: str):
    return publico(leer(s))


@app.get("/api/modelo")
def modelo():
    """Información básica del modelo que crea los nombres."""
    res = RAIZ / "generador_nombres" / "resultados"
    exp = json.loads((res / "experimentos.json").read_text(encoding="utf-8"))
    mue = json.loads((res / "muestreo.json").read_text(encoding="utf-8"))
    sel = next(e for e in exp["experimentos"] if e["nombre"] == exp["modelo_seleccionado"])
    return {"arquitectura": sel["tipo"].upper(), "capas": sel["capas"], "oculto": sel["oculto"],
            "parametros": sel["parametros"], "mejor_epoca": sel["mejor_epoca"],
            "perdida_validacion": sel["perdida_validacion_mejor"], "nombres_entrenamiento": exp["datos"]["nombres_unicos"],
            "muestreo": mue["estrategia_elegida"]}


@app.get("/api/estado")
def estado():
    try:
        return {"sagemaker": True, **sagemaker.salud()}
    except sagemaker.NoDisponible as e:
        return {"sagemaker": False, "detalle": str(e)}


@app.get("/imagenes/{s}.png")
def imagen(s: str):
    ruta = DATOS / slug(s) / "imagen.png"
    if not ruta.exists():
        raise HTTPException(404)
    return FileResponse(ruta, media_type="image/png")


# ---------- Chat ----------

def presentar(dino):
    """La presentación se genera una vez por dinosaurio y se guarda."""
    if not dino.get("presentacion"):
        dino["presentacion"] = sagemaker.chat(dino["identidad"], [], presentacion=True)["respuesta"]
        guardar(dino)
    return dino["presentacion"]


@app.get("/api/presentacion/{s}")
def presentacion(s: str):
    dino = leer(s)
    try:
        texto = presentar(dino)
    except sagemaker.NoDisponible as e:
        raise HTTPException(503, str(e))
    return {"respuesta": texto, "imagen_url": publico(dino)["imagen_url"]}


class PedidoChat(BaseModel):
    id: str = PRINCIPAL
    mensajes: list[dict]


@app.post("/api/chat")
def chat(p: PedidoChat):
    dino = leer(p.id)
    mensajes = [{"role": m["role"], "content": str(m["content"])[:1000]}
                for m in p.mensajes if m.get("role") in ("user", "assistant")]
    try:
        r = sagemaker.chat(dino["identidad"], mensajes)
    except sagemaker.NoDisponible as e:
        raise HTTPException(503, str(e))
    ultimo = next((m["content"] for m in reversed(mensajes) if m["role"] == "user"), "")
    pide = bool(PIDE_IMAGEN.search(ultimo))
    return {"respuesta": r["respuesta"], "imagen_url": publico(dino)["imagen_url"] if pide else None}


# ---------- Nuevo Dinosaurio ----------

trabajos, candado = {}, threading.Lock()


def crear_dinosaurio(tid):
    t = trabajos[tid]
    try:
        t["paso"] = 0  # el modelo ya entrenado genera el nombre; no se reentrena
        nombre = nuevo_nombre()
        while (DATOS / slug(nombre)).exists():
            nombre = nuevo_nombre()
        t["nombre"] = nombre

        t["paso"] = 1
        r_id = sagemaker.identidad(nombre)
        ident = r_id["identidad"]

        t["paso"] = 2
        semilla = random.randint(0, 9999)
        r_img = sagemaker.imagen(nombre, ident["prompt_imagen"], semilla)

        dino = {"id": slug(nombre), "nombre": nombre, "identidad": ident, "modelo_ollama": r_id["modelo"],
                "pistas": r_id.get("pistas"),
                "imagen": {k: r_img[k] for k in ("modelo", "prompt", "pasos", "semilla")},
                "presentacion": None, "creado": time.strftime("%Y-%m-%d %H:%M:%S")}
        guardar(dino)
        (DATOS / dino["id"] / "imagen.png").write_bytes(base64.b64decode(r_img["png_base64"]))

        t["paso"] = 3
        presentar(dino)
        t.update(estado="listo", dino=publico(dino))
    except Exception as e:  # el error se muestra en la página
        t.update(estado="error", error=str(e))
    finally:
        t["segundos"] = round(time.time() - t["inicio"])


@app.post("/api/nuevo")
def nuevo():
    with candado:
        en_curso = next((tid for tid, t in trabajos.items() if t["estado"] == "en_curso"), None)
        if en_curso:
            return {"trabajo": en_curso, "pasos": PASOS}
        tid = uuid.uuid4().hex[:8]
        trabajos[tid] = {"estado": "en_curso", "paso": 0, "inicio": time.time()}
    threading.Thread(target=crear_dinosaurio, args=(tid,), daemon=True).start()
    return {"trabajo": tid, "pasos": PASOS}


@app.get("/api/trabajos/{tid}")
def trabajo(tid: str):
    if tid not in trabajos:
        raise HTTPException(404)
    t = trabajos[tid]
    return {**t, "pasos": PASOS, "segundos": t.get("segundos", round(time.time() - t["inicio"]))}


app.mount("/", StaticFiles(directory=AQUI / "static", html=True), name="static")
