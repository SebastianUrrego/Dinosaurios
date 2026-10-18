# Isla de los Dinosaurios

Laboratorio II de Procesamiento de Lenguaje Natural (Universidad Sergio Arboleda, 2026 S02). Es una aplicación que crea un dinosaurio ficticio:

```
Modelo de caracteres → Nombre → Ollama → Identidad → Imagen → Chat
```

## Avance

| Etapa | Estado | Resultado |
|---|---|---|
| 1. Generador de nombres | ✅ Listo | GRU 2×256, top-p 0.9, 10 nombres nuevos → **Aborosaurus** |
| 2. Identidad con Ollama | ✅ Listo | SageMaker `ml.m5.xlarge` + Docker + lifecycle on-start, `gemma4:e2b` |
| 3. Imagen | ✅ Listo | `amused/amused-512` en Colab (T4), semilla 0 de 4 candidatas |
| 4. App web y chat | ⏳ Pendiente | |

## Estructura

| Carpeta | Componente |
|---|---|
| `generador_nombres/` | RNN de caracteres: preprocesamiento, entrenamiento, muestreo y evidencias ([detalle](generador_nombres/README.md)) |
| `ollama/` | Ollama en SageMaker: lifecycle on-start, verificación e identidad ([detalle](ollama/README.md)) |
| `imagen/` | Imagen text-to-image en Colab: notebook, candidatas e imagen final ([detalle](imagen/README.md)) |
| `app/` | Aplicación web y chat |
| `docs/` | Capturas y diagramas |

---

## 1. Generador de nombres

Modelo de lenguaje a nivel de caracteres entrenado con `dinos.csv` (1524 nombres únicos). Cada nombre
se prepara como `<S> + letras + <E>`, se rellena con `<PAD>` hasta `T + 1 = 28` y se separa en
`X = [x0..x26]`, `Y = [x1..x27]`. La división es 90/10 con semilla 42. Durante la generación, cada
carácter producido se usa para predecir el siguiente (generación autoregresiva).

### Dos configuraciones

| | A | B (elegida) |
|---|---|---|
| Arquitectura | LSTM, 1 capa | GRU, 2 capas (dropout 0.3) |
| Estado oculto | 128 | 256 |
| Parámetros | 87 613 | 625 853 |
| Épocas | 40 | 40 |
| Pérdida | `CrossEntropyLoss(ignore_index=<PAD>)` | igual |
| Optimizador | Adam, lr 0.003, lote 64 | igual |
| **Mejor época** | **16** | **9** |
| Pérdida train / val en la mejor época | 1.358 / 1.584 | 1.352 / **1.560** |

![Curvas de pérdida de entrenamiento y validación](generador_nombres/resultados/curvas_perdida.png)

La línea punteada marca la **mejor época**, donde la pérdida de validación es mínima. Después de ese
punto, el entrenamiento sigue bajando pero la validación sube: el modelo empieza a memorizar los
nombres (sobreajuste). Por eso cada modelo se guarda en su mejor época. B llega antes a ese punto
porque tiene 7 veces más parámetros, y obtiene la menor pérdida de validación.

### Muestreo

Se compararon tres temperaturas (0.5, 1.0 y 1.5), top-k = 5 y top-p = 0.9, con 200 nombres por estrategia:

![Comparación de estrategias de muestreo](generador_nombres/resultados/muestreo.png)

- **T = 0.5** es la más conservadora: muchos nombres terminan en *-saurus*, pero el 13 % no son nuevos.
- **T = 1.5** es muy diversa, pero genera nombres impronunciables como *Nmsendutliavenlonlyus*.
- **top-p = 0.9** logra el mejor equilibrio: 96.5 % nuevos, 100 % únicos y 71.5 % con sufijo realista. Es la estrategia elegida.

### Diez nombres nuevos (ninguno está en `dinos.csv`)

| | | | | |
|---|---|---|---|---|
| Ereidasaurus | Crothongosaurus | Coratosaurus | Deistavuraptor | Dyrotaphalus |
| Pispondylus | **Aborosaurus** | Hopalophosaurus | Taivelasaurus | Alticoelia |

**Seleccionado: Aborosaurus.** No es una copia, aunque se parece a nombres reales como *Abrosaurus*
u *Orosaurus*: el modelo aprendió sus patrones sin copiarlos.

---

## 2. Identidad con Ollama

Ollama corre en un notebook de SageMaker (`ml.m5.xlarge`, 50 GB, rol `LabRole`) dentro de Docker.
El lifecycle script **on-start** pone el `data-root` de Docker y los modelos en
`/home/ec2-user/SageMaker`, de modo que todo se conserva entre reinicios, y en cada arranque deja
Ollama funcionando sin intervención.

![Lifecycle on-start completado](docs/capturas/1_lifecycle_on_start.png)

Verificación desde el notebook (Ollama 0.40.5, modelo y digest registrados en `ollama/modelo.json`):

![Verificación de Ollama](docs/capturas/2_verificacion_ollama.png)

### Comparación de modelos

Se usó el mismo prompt con los dos modelos. El prompt incluye raíces reales (-saurus, -raptor,
-odon, -venator, arbor-…) y pide la respuesta en JSON, con temperatura 0.4 y semilla 42.

| | `llama3.2:3b` | `gemma4:e2b` (elegido) |
|---|---|---|
| Significado del nombre | "cabeza imitadora": no usa las raíces dadas | "lagarto del árbol" (*arbor-* + *-saurus*) |
| Coherencia | carnívoro con "dientes de molar"; en hábitat describe la dieta | herbívoro arborícola coherente en todos los campos |

<details>
<summary>Salida de llama3.2:3b</summary>

![Identidad con llama3.2:3b](docs/capturas/3_identidad_llama.png)
</details>

![Identidad con gemma4:e2b](docs/capturas/4_identidad_gemma.png)

### Identidad de Aborosaurus

| | |
|---|---|
| **Significado** | "Lagarto del árbol", por su adaptación a la vida arbórea |
| **Periodo** | Cretácico Medio |
| **Apariencia** | Unos 6 m de largo y 1.5 t; cuerpo esbelto con patas largas para trepar; escamas verde oliva que lo camuflan en el follaje |
| **Hábitat** | Bosques húmedos, en las copas de árboles altos y en laderas boscosas cerca de los ríos |
| **Alimentación** | Herbívoro: hojas, brotes y frutos; dientes finos para rasgar y triturar vegetación tierna |
| **Comportamiento** | Solitario y lento en el dosel; ante una amenaza se esconde con movimientos rápidos entre la vegetación |
| **Rasgo distintivo** | Membranas cutáneas en las extremidades superiores para adherirse a ramas y troncos |

Esta identidad ([`ollama/identidad.json`](ollama/identidad.json)) es la entrada de la imagen y del chat.

---

## 3. Imagen

La imagen se generó en Google Colab (GPU Tesla T4) con `amused/amused-512`. El prompt es corto
y combina el nombre con el `prompt_imagen` que escribió Ollama:

> Aborosaurus, a dinosaur. A medium-sized, slender dinosaur with long limbs clinging to a massive tree
> branch in a dense, humid forest canopy. Olive green scales, browsing on leaves. Soft, dappled sunlight.

Se generaron 4 candidatas (semillas 0 a 3; 12 pasos, guía 10.0, 512×512):

![Candidatas](imagen/candidatas.png)

| Semilla | ¿Encaja con la identidad? |
|---|---|
| **0** | ✅ Esbelto, verde oliva, patas largas, bosque húmedo: **elegida** |
| 1 | Cuadrúpedo robusto, demasiado pesado para un trepador |
| 2 | Color azul verdoso, se aleja del verde oliva |
| 3 | Dientes de carnívoro, contradice la dieta herbívora |

<p align="center"><img src="imagen/aborosaurus.png" alt="Aborosaurus" width="400"></p>

Ninguna candidata lo muestra agarrado a una rama: aMUSEd es un modelo pequeño y sigue mal las poses
concretas. La elegida conserva lo principal de la identidad: cuerpo esbelto, color verde oliva y
entorno de bosque húmedo. La imagen se genera una sola vez y la app la reutiliza en el chat.

---

## Configuración

Copia `.env.example` a `.env` y completa los valores. El archivo `.env` no se versiona.

## Ejecución

| Componente | Cómo ejecutarlo |
|---|---|
| Generador de nombres | `cd generador_nombres && pip install -r requirements.txt && python entrenar.py && python muestreo.py`; nombres nuevos sin reentrenar: `python generar.py -n 5` |
| Ollama | lifecycle `ollama/on-start.sh` (ver [ollama/README.md](ollama/README.md)), luego `verificar_ollama.ipynb` e `identidad.ipynb` en SageMaker |
| Imagen | `imagen/generar_imagen.ipynb` en Colab con GPU; resultado en `imagen/aborosaurus.png` |
| App | _pendiente_ |

## Enlaces

- Sitio web: _pendiente_
