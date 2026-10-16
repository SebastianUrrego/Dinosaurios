"""Genera nombres nuevos con el modelo ya entrenado (no reentrena). Lo usa el botón "Nuevo Dinosaurio".

Uso: python generar.py [-n 5] [--temperatura 1.0] [--top-k K] [--top-p 0.9]
"""
import argparse

from datos import cargar_nombres
from modelo import cargar, generar

_modelo, _vocab, _conocidos = None, None, None


def nuevo_nombre(temperatura=1.0, top_k=None, top_p=0.9, intentos=50):
    """Devuelve un nombre de 4+ letras que no esté en dinos.csv."""
    global _modelo, _vocab, _conocidos
    if _modelo is None:
        _modelo, _vocab, _ = cargar()
        _conocidos = set(cargar_nombres())
    for _ in range(intentos):
        nombre = generar(_modelo, _vocab, temperatura, top_k, top_p)
        if len(nombre) >= 4 and nombre not in _conocidos:
            return nombre.capitalize()
    raise RuntimeError("No se obtuvo un nombre nuevo; revisa los parámetros de muestreo")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("-n", type=int, default=5)
    p.add_argument("--temperatura", type=float, default=1.0)
    p.add_argument("--top-k", type=int)
    p.add_argument("--top-p", type=float, default=0.9)
    a = p.parse_args()
    for _ in range(a.n):
        print(nuevo_nombre(a.temperatura, a.top_k, a.top_p))
