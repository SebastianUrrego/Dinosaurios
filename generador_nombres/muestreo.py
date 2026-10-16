"""Compara estrategias de muestreo con el modelo entrenado y elige los diez nombres.

Salidas en resultados/: muestreo.json y muestreo.md
Uso: python muestreo.py
"""
import json
from pathlib import Path

import torch

from datos import cargar_nombres
from modelo import cargar, generar

RESULTADOS = Path(__file__).parent / "resultados"
SEMILLA = 7
N_MUESTRAS = 200
SUFIJOS = ("saurus", "raptor", "odon", "venator", "don", "ops", "rex", "mimus", "titan", "ceratops")

ESTRATEGIAS = [
    ("T = 0.5", {"temperatura": 0.5}),
    ("T = 1.0", {"temperatura": 1.0}),
    ("T = 1.5", {"temperatura": 1.5}),
    ("top-k = 5 (T = 1.0)", {"temperatura": 1.0, "top_k": 5}),
    ("top-p = 0.9 (T = 1.0)", {"temperatura": 1.0, "top_p": 0.9}),
]
ESTRATEGIA_ELEGIDA = "top-p = 0.9 (T = 1.0)"


def evaluar(modelo, vocab, conocidos, params):
    g = torch.Generator().manual_seed(SEMILLA)
    nombres = [generar(modelo, vocab, generador=g, **params) for _ in range(N_MUESTRAS)]
    validos = [n for n in nombres if len(n) >= 4]
    nuevos = [n for n in validos if n not in conocidos]
    return nombres, {
        "nuevos_%": round(100 * len(nuevos) / N_MUESTRAS, 1),
        "unicos_%": round(100 * len(set(nombres)) / N_MUESTRAS, 1),
        "longitud_media": round(sum(map(len, nombres)) / N_MUESTRAS, 1),
        "sufijo_real_%": round(100 * sum(n.endswith(SUFIJOS) for n in nombres) / N_MUESTRAS, 1),
        "ejemplos": [n.capitalize() for n in dict.fromkeys(nuevos)][:8],
    }


def diez_nombres(modelo, vocab, conocidos, params):
    g = torch.Generator().manual_seed(SEMILLA + 1)
    elegidos = []
    while len(elegidos) < 10:
        n = generar(modelo, vocab, generador=g, **params)
        if len(n) >= 4 and n not in conocidos and n.capitalize() not in elegidos:
            elegidos.append(n.capitalize())
    return elegidos


def main():
    modelo, vocab, ckpt = cargar()
    conocidos = set(cargar_nombres())
    resultados = {}
    for nombre, params in ESTRATEGIAS:
        _, metricas = evaluar(modelo, vocab, conocidos, params)
        resultados[nombre] = {"parametros": params, **metricas}
        print(nombre, {k: v for k, v in metricas.items() if k != "ejemplos"})

    params = dict(ESTRATEGIAS)[ESTRATEGIA_ELEGIDA]
    diez = diez_nombres(modelo, vocab, conocidos, params)
    informe = {"modelo": ckpt["config"]["nombre"], "muestras_por_estrategia": N_MUESTRAS, "semilla": SEMILLA,
               "estrategias": resultados, "estrategia_elegida": ESTRATEGIA_ELEGIDA, "diez_nombres": diez}
    (RESULTADOS / "muestreo.json").write_text(json.dumps(informe, indent=2, ensure_ascii=False), encoding="utf-8")

    filas = "\n".join(
        f"| {n} | {r['nuevos_%']} | {r['unicos_%']} | {r['longitud_media']} | {r['sufijo_real_%']} | {', '.join(r['ejemplos'][:5])} |"
        for n, r in resultados.items())
    md = f"""# Muestreo

Modelo: **{ckpt['config']['nombre']}**. {N_MUESTRAS} nombres por estrategia (semilla {SEMILLA}).

- **nuevos %**: nombres de 4 o más letras que no están en `dinos.csv`.
- **sufijo real %**: terminan en un sufijo frecuente de dinosaurios reales ({', '.join(SUFIJOS)}).

| Estrategia | nuevos % | únicos % | long. media | sufijo real % | ejemplos |
|---|---|---|---|---|---|
{filas}

## Diez nombres ({ESTRATEGIA_ELEGIDA})

{chr(10).join(f'{i}. {n}' for i, n in enumerate(diez, 1))}
"""
    (RESULTADOS / "muestreo.md").write_text(md, encoding="utf-8")
    print("\nDiez nombres:", ", ".join(diez))


if __name__ == "__main__":
    main()
