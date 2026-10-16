"""Preprocesamiento de dinos.csv para el modelo de lenguaje a nivel de caracteres."""
from pathlib import Path

import torch

PAD, INICIO, FIN = "<PAD>", "<S>", "<E>"
RUTA_DATOS = Path(__file__).parent / "data" / "dinos.csv"


def cargar_nombres(ruta=RUTA_DATOS):
    """Paso 1: normaliza (minúsculas, sin espacios) y quita duplicados conservando el orden."""
    nombres, vistos = [], set()
    for linea in Path(ruta).read_text(encoding="utf-8").splitlines():
        nombre = linea.strip().lower()
        if nombre and nombre not in vistos:
            vistos.add(nombre)
            nombres.append(nombre)
    return nombres


class Vocabulario:
    """Paso 2 y 3: relación carácter <-> id, con <PAD>=0, <S>=1 y <E>=2."""

    def __init__(self, simbolos):
        self.itos = list(simbolos)
        self.stoi = {s: i for i, s in enumerate(self.itos)}
        self.pad, self.inicio, self.fin = self.stoi[PAD], self.stoi[INICIO], self.stoi[FIN]

    @classmethod
    def desde_nombres(cls, nombres):
        return cls([PAD, INICIO, FIN] + sorted(set("".join(nombres))))

    def __len__(self):
        return len(self.itos)

    def codificar(self, nombre):
        return [self.inicio] + [self.stoi[c] for c in nombre] + [self.fin]

    def decodificar(self, ids):
        especiales = {self.pad, self.inicio, self.fin}
        return "".join(self.itos[i] for i in ids if i not in especiales)


def preparar(nombres, vocab):
    """Pasos 4 a 6: longitud máxima T, relleno con <PAD> y pares X/Y desplazados un carácter.

    Cada secuencia preparada es [x0, x1, ..., xT] (T + 1 elementos), de modo que
    X = [x0..x_{T-1}] e Y = [x1..xT] tienen longitud T.
    """
    secuencias = [vocab.codificar(n) for n in nombres]
    T = max(len(s) for s in secuencias) - 1
    rellenas = [s + [vocab.pad] * (T + 1 - len(s)) for s in secuencias]
    datos = torch.tensor(rellenas, dtype=torch.long)
    return datos[:, :-1], datos[:, 1:], T


def dividir(n, frac_validacion=0.1, semilla=42):
    """Índices aleatorios (reproducibles) de entrenamiento y validación."""
    perm = torch.randperm(n, generator=torch.Generator().manual_seed(semilla))
    n_val = int(n * frac_validacion)
    return perm[n_val:], perm[:n_val]
