"""Cliente de la API del notebook de SageMaker (app/sagemaker/api.py), publicada con ngrok."""
import os

import requests


class NoDisponible(Exception):
    """SageMaker no responde o devolvió un error."""


def _config():
    return os.getenv("SAGEMAKER_URL", "").strip().strip("\"'").rstrip("/"), {
        "X-API-Key": os.getenv("API_KEY", ""),
        "ngrok-skip-browser-warning": "1",  # evita la página de aviso de ngrok
    }


def _pedir(metodo, ruta, cuerpo=None, timeout=300):
    url, cabeceras = _config()
    if not url:
        raise NoDisponible("SAGEMAKER_URL no está configurada")
    try:
        r = requests.request(metodo, url + ruta, json=cuerpo, headers=cabeceras, timeout=timeout)
    except requests.RequestException as e:
        raise NoDisponible(f"No se pudo conectar con SageMaker: {e.__class__.__name__}") from e
    if r.status_code != 200:
        if "html" in r.headers.get("content-type", ""):  # página de error de ngrok
            raise NoDisponible(f"SageMaker no respondió a tiempo en {ruta} (ngrok {r.status_code}); "
                               "revisa que el notebook esté encendido")
        raise NoDisponible(f"SageMaker respondió {r.status_code} en {ruta}: {r.text[:200]}")
    return r.json()


def salud():
    return _pedir("GET", "/salud", timeout=10)


def identidad(nombre):
    return _pedir("POST", "/identidad", {"nombre": nombre})


def chat(identidad, mensajes, presentacion=False):
    return _pedir("POST", "/chat", {"identidad": identidad, "mensajes": mensajes, "presentacion": presentacion})


def imagen(nombre, prompt_imagen, semilla):
    return _pedir("POST", "/imagen", {"nombre": nombre, "prompt_imagen": prompt_imagen, "semilla": semilla})
