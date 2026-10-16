"""Modelo recurrente de caracteres y generación autoregresiva con temperatura, top-k y top-p."""
from pathlib import Path

import torch
from torch import nn

from datos import Vocabulario

RUTA_MODELO = Path(__file__).parent / "resultados" / "modelo.pt"
CELDAS = {"rnn": nn.RNN, "lstm": nn.LSTM, "gru": nn.GRU}


class ModeloCaracteres(nn.Module):
    """Embedding -> RNN/LSTM/GRU -> capa lineal con un logit por símbolo del vocabulario."""

    def __init__(self, tam_vocab, tipo="lstm", dim_embedding=32, oculto=128, capas=1, dropout=0.0):
        super().__init__()
        self.embedding = nn.Embedding(tam_vocab, dim_embedding, padding_idx=0)
        self.rnn = CELDAS[tipo](dim_embedding, oculto, capas, batch_first=True,
                                dropout=dropout if capas > 1 else 0.0)
        self.salida = nn.Linear(oculto, tam_vocab)

    def forward(self, x, estado=None):
        h, estado = self.rnn(self.embedding(x), estado)
        return self.salida(h), estado


def probabilidades(logits, temperatura=1.0, top_k=None, top_p=None):
    """Convierte los logits de un paso en la distribución de la que se muestrea."""
    logits = logits / temperatura
    if top_k is not None:
        umbral = torch.topk(logits, top_k).values[..., -1, None]
        logits = logits.masked_fill(logits < umbral, float("-inf"))
    if top_p is not None:
        orden, idx = torch.sort(logits, descending=True)
        p = torch.softmax(orden, dim=-1)
        # Se descarta un símbolo si la masa acumulada antes de él ya alcanza p
        fuera = (torch.cumsum(p, dim=-1) - p) >= top_p
        logits = logits.masked_fill(fuera.scatter(-1, idx, fuera), float("-inf"))
    return torch.softmax(logits, dim=-1)


@torch.no_grad()
def generar(modelo, vocab, temperatura=1.0, top_k=None, top_p=None, max_len=30, generador=None):
    """Genera un nombre carácter a carácter: cada salida se usa como la siguiente entrada."""
    modelo.eval()
    x = torch.tensor([[vocab.inicio]])
    estado, ids = None, []
    for _ in range(max_len):
        logits, estado = modelo(x, estado)
        logits = logits[0, -1]
        logits[[vocab.pad, vocab.inicio]] = float("-inf")  # nunca se generan
        siguiente = torch.multinomial(probabilidades(logits, temperatura, top_k, top_p), 1, generator=generador).item()
        if siguiente == vocab.fin:
            break
        ids.append(siguiente)
        x = torch.tensor([[siguiente]])
    return vocab.decodificar(ids)


def guardar(ruta, modelo, vocab, config, T):
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    torch.save({"config": config, "vocab": vocab.itos, "T": T, "pesos": modelo.state_dict()}, ruta)


def cargar(ruta=RUTA_MODELO):
    ckpt = torch.load(ruta, map_location="cpu")
    vocab = Vocabulario(ckpt["vocab"])
    c = ckpt["config"]
    modelo = ModeloCaracteres(len(vocab), c["tipo"], c["dim_embedding"], c["oculto"], c["capas"], c["dropout"])
    modelo.load_state_dict(ckpt["pesos"])
    modelo.eval()
    return modelo, vocab, ckpt
