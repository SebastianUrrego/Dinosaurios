"""Entrena y compara dos configuraciones del modelo de caracteres.

Salidas en resultados/:
  experimentos.json   configuración, pérdida, optimizador y métricas de cada experimento
  curvas_perdida.png  pérdida de entrenamiento y validación por época
  modelo.pt           mejor modelo (menor pérdida de validación), usado por generar.py y la app

Uso: python entrenar.py
"""
import json
import random
import time
from pathlib import Path

import matplotlib
import torch
from torch import nn

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from datos import Vocabulario, cargar_nombres, dividir, preparar
from modelo import RUTA_MODELO, ModeloCaracteres, guardar

SEMILLA = 42
RESULTADOS = Path(__file__).parent / "resultados"
TAM_LOTE = 64

CONFIGURACIONES = [
    {"nombre": "A: LSTM 1x128", "tipo": "lstm", "capas": 1, "oculto": 128, "dropout": 0.0,
     "dim_embedding": 32, "epocas": 40, "lr": 3e-3},
    {"nombre": "B: GRU 2x256", "tipo": "gru", "capas": 2, "oculto": 256, "dropout": 0.3,
     "dim_embedding": 32, "epocas": 40, "lr": 3e-3},
]


def perdida_media(modelo, criterio, X, Y, optimizador=None):
    """Pérdida media por carácter real (los <PAD> no cuentan). Si hay optimizador, entrena."""
    entrenando = optimizador is not None
    modelo.train(entrenando)
    orden = torch.randperm(len(X)) if entrenando else torch.arange(len(X))
    total, n_tokens = 0.0, 0
    for i in range(0, len(X), TAM_LOTE):
        idx = orden[i:i + TAM_LOTE]
        x, y = X[idx], Y[idx]
        with torch.set_grad_enabled(entrenando):
            logits, _ = modelo(x)
            perdida = criterio(logits.reshape(-1, logits.size(-1)), y.reshape(-1))
            tokens = (y != criterio.ignore_index).sum().item()
            if entrenando:
                optimizador.zero_grad()
                (perdida / tokens).backward()
                nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
                optimizador.step()
        total += perdida.item()
        n_tokens += tokens
    return total / n_tokens


def entrenar(config, vocab, datos):
    torch.manual_seed(SEMILLA)
    random.seed(SEMILLA)
    X_tr, Y_tr, X_val, Y_val = datos
    modelo = ModeloCaracteres(len(vocab), config["tipo"], config["dim_embedding"],
                              config["oculto"], config["capas"], config["dropout"])
    # reduction="sum" + ignore_index: suma solo los caracteres reales; luego se divide por su número
    criterio = nn.CrossEntropyLoss(ignore_index=vocab.pad, reduction="sum")
    optimizador = torch.optim.Adam(modelo.parameters(), lr=config["lr"])

    historial = {"entrenamiento": [], "validacion": []}
    mejor = {"validacion": float("inf")}
    inicio = time.time()
    for epoca in range(1, config["epocas"] + 1):
        p_tr = perdida_media(modelo, criterio, X_tr, Y_tr, optimizador)
        p_val = perdida_media(modelo, criterio, X_val, Y_val)
        historial["entrenamiento"].append(p_tr)
        historial["validacion"].append(p_val)
        if p_val < mejor["validacion"]:
            mejor = {"epoca": epoca, "validacion": p_val, "entrenamiento": p_tr,
                     "pesos": {k: v.clone() for k, v in modelo.state_dict().items()}}
        print(f"[{config['nombre']}] época {epoca:2d}  train {p_tr:.4f}  val {p_val:.4f}")

    modelo.load_state_dict(mejor.pop("pesos"))
    resumen = {
        **config,
        "funcion_perdida": "CrossEntropyLoss(ignore_index=<PAD>)",
        "optimizador": f"Adam(lr={config['lr']})",
        "tam_lote": TAM_LOTE,
        "parametros": sum(p.numel() for p in modelo.parameters()),
        "mejor_epoca": mejor["epoca"],
        "perdida_entrenamiento_mejor": round(mejor["entrenamiento"], 4),
        "perdida_validacion_mejor": round(mejor["validacion"], 4),
        "segundos": round(time.time() - inicio, 1),
        "historial": historial,
    }
    return modelo, resumen


def graficar(resumenes, ruta):
    fig, ejes = plt.subplots(1, len(resumenes), figsize=(6 * len(resumenes), 4), sharey=True)
    for eje, r in zip(ejes, resumenes):
        epocas = range(1, len(r["historial"]["entrenamiento"]) + 1)
        eje.plot(epocas, r["historial"]["entrenamiento"], label="entrenamiento")
        eje.plot(epocas, r["historial"]["validacion"], label="validación")
        eje.axvline(r["mejor_epoca"], color="gray", linestyle=":", label=f"mejor época ({r['mejor_epoca']})")
        eje.set_title(r["nombre"])
        eje.set_xlabel("época")
        eje.grid(alpha=0.3)
        eje.legend()
    ejes[0].set_ylabel("pérdida (entropía cruzada por carácter)")
    fig.tight_layout()
    fig.savefig(ruta, dpi=120)


def main():
    nombres = cargar_nombres()
    vocab = Vocabulario.desde_nombres(nombres)
    X, Y, T = preparar(nombres, vocab)
    idx_tr, idx_val = dividir(len(nombres), semilla=SEMILLA)
    datos = (X[idx_tr], Y[idx_tr], X[idx_val], Y[idx_val])
    print(f"{len(nombres)} nombres únicos | vocabulario {len(vocab)} | T = {T} | "
          f"entrenamiento {len(idx_tr)} | validación {len(idx_val)}")

    RESULTADOS.mkdir(exist_ok=True)
    modelos, resumenes = [], []
    for config in CONFIGURACIONES:
        modelo, resumen = entrenar(config, vocab, datos)
        modelos.append(modelo)
        resumenes.append(resumen)

    graficar(resumenes, RESULTADOS / "curvas_perdida.png")
    i_mejor = min(range(len(resumenes)), key=lambda i: resumenes[i]["perdida_validacion_mejor"])
    guardar(RUTA_MODELO, modelos[i_mejor], vocab, CONFIGURACIONES[i_mejor], T)

    informe = {
        "datos": {"nombres_unicos": len(nombres), "vocabulario": vocab.itos, "T": T,
                  "entrenamiento": len(idx_tr), "validacion": len(idx_val), "semilla": SEMILLA},
        "experimentos": resumenes,
        "modelo_seleccionado": resumenes[i_mejor]["nombre"],
    }
    (RESULTADOS / "experimentos.json").write_text(json.dumps(informe, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Modelo seleccionado: {resumenes[i_mejor]['nombre']} -> {RUTA_MODELO}")


if __name__ == "__main__":
    main()
