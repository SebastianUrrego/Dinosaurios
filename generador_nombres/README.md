# Generador de nombres (RNN de caracteres)

| Archivo | Qué hace |
|---|---|
| `datos.py` | Preprocesamiento: normaliza, vocabulario, `<S>`/`<E>`, longitud `T`, relleno `<PAD>`, pares X/Y |
| `modelo.py` | Modelo Embedding → RNN/LSTM/GRU → Linear y generación autoregresiva (temperatura, top-k, top-p) |
| `entrenar.py` | Entrena las dos configuraciones y guarda curvas, `experimentos.json` y el mejor `modelo.pt` |
| `muestreo.py` | Compara estrategias de muestreo y genera los diez nombres (`muestreo.md`, `muestreo.json`, `muestreo.png`) |
| `generar.py` | Genera nombres nuevos con el modelo ya entrenado (lo usa el botón **Nuevo Dinosaurio**) |

```bash
pip install -r requirements.txt
python entrenar.py      # ~1 min en CPU
python muestreo.py
python generar.py -n 5  # sin reentrenar
```

**Entrada:** `data/dinos.csv` (un nombre por línea). **Salida de `generar.py`:** un nombre capitalizado que no está en el dataset.

## Preprocesamiento

1. Minúsculas y sin espacios; se quitan 12 duplicados → **1524 nombres**.
2. Vocabulario: `<PAD>`=0, `<S>`=1, `<E>`=2 y las 26 letras (29 símbolos).
3. Cada nombre queda como `<S> + letras + <E>`.
4. Longitud máxima de las secuencias preparadas: 28 símbolos, es decir `[x0..xT]` con **T = 27**.
5. Relleno con `<PAD>` hasta 28.
6. `X = [x0..x26]`, `Y = [x1..x27]`.

División 90/10 con semilla 42: 1372 de entrenamiento y 152 de validación.

## Experimentos

| | A | B |
|---|---|---|
| Arquitectura | LSTM | GRU |
| Capas | 1 | 2 (dropout 0.3) |
| Estado oculto | 128 | 256 |
| Embedding | 32 | 32 |
| Parámetros | 87 613 | 625 853 |
| Épocas | 40 | 40 |
| Pérdida | `CrossEntropyLoss(ignore_index=<PAD>)` | igual |
| Optimizador | Adam (lr 0.003), lote 64, clip 1.0 | igual |
| Mejor época (val) | 16 | 9 |
| Pérdida train / val en la mejor época | 1.358 / 1.584 | 1.352 / **1.560** |

![Curvas de pérdida](resultados/curvas_perdida.png)

Las dos configuraciones sobreajustan: la pérdida de entrenamiento sigue bajando, pero la de
validación toca su mínimo y luego sube. B, con 7 veces más parámetros, llega antes al mínimo (época 9)
y sobreajusta más rápido. Se guarda cada modelo en su mejor época de validación y se elige **B**
(1.560 frente a 1.584). La diferencia es pequeña: A es una alternativa razonable si se busca un modelo más liviano.

## Muestreo

200 nombres por estrategia con el modelo B ([detalle](resultados/muestreo.md)):

| Estrategia | nuevos % | únicos % | sufijo real % |
|---|---|---|---|
| T = 0.5 | 87.0 | 92.5 | 78.0 |
| T = 1.0 | 99.0 | 100.0 | 57.5 |
| T = 1.5 | 97.0 | 98.5 | 30.0 |
| top-k = 5 | 93.0 | 97.5 | 68.5 |
| **top-p = 0.9** | 96.5 | 100.0 | 71.5 |

- **T = 0.5** concentra la probabilidad: casi todo termina en *-saurus*, pero el 13 % son copias del dataset o se repiten.
- **T = 1.5** da diversidad a costa de la forma: aparecen nombres impronunciables como *Nmsendutliavenlonlyus*.
- **T = 1.0** es la más novedosa, pero conserva la cola de caracteres poco probables.
- **top-k = 5** recorta esa cola, aunque con un k fijo a veces deja demasiadas opciones y otras muy pocas.
- **top-p = 0.9** adapta el corte a cada paso y logra el mejor equilibrio: 96.5 % nuevos, ninguno repetido y 71.5 % con sufijo realista. Es la estrategia elegida, y también la que usa la app.

## Diez nombres (top-p = 0.9)

Ereidasaurus, Crothongosaurus, Coratosaurus, Deistavuraptor, Dyrotaphalus, Pispondylus,
Aborosaurus, Hopalophosaurus, Taivelasaurus, Alticoelia. Ninguno está en `dinos.csv`.

**Nombre seleccionado:** **Aborosaurus**. No está en el dataset, aunque se parece a nombres reales como *Abrosaurus*, *Orosaurus* o *Torosaurus*: el modelo aprendió sus patrones sin copiarlos, que es lo que pide la guía.
