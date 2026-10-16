# Ollama en SageMaker

| Archivo | Uso |
|---|---|
| `on-start.sh` | Lifecycle configuration *on-start*: mueve el `data-root` de Docker a `/home/ec2-user/SageMaker/docker`, levanta el contenedor `ollama` (modelos en `/home/ec2-user/SageMaker/ollama`) y descarga el modelo en segundo plano. Log: `/home/ec2-user/SageMaker/logs/on-start.log`. |
| `verificar_ollama.ipynb` | Comprueba la instalación, guarda nombre y versión del modelo en `modelo.json` y prueba una instrucción. |
| `identidad.ipynb` | Genera la identidad de Aborosaurus con dos modelos (mismo prompt, salida JSON) y guarda la elegida en `identidad.json`. |

## Configuración

| | |
|---|---|
| Notebook | `dinosaurios-ollama`, `ml.m5.xlarge` (4 vCPU, 16 GB), disco 50 GB, rol `LabRole`, `us-east-1` |
| Versión de Ollama | 0.40.5 |
| Ollama | contenedor `ollama/ollama` (CPU), `127.0.0.1:11434` |
| Modelo | `llama3.2:3b`, 3.2B parámetros, GGUF Q4_K_M, digest `a80c4f17acd5` (detalle en `modelo.json`) |
| Lifecycle | `dinosaurios-on-start` → `on-start.sh` |

## Crear o actualizar el lifecycle

El script se sube **como archivo desde CloudShell**, nunca pegado en el formulario de la consola:
al pegarlo desde Windows queda con saltos de línea `\r\n`, la primera línea se vuelve
`#!/bin/bash\r`, el script no arranca y SageMaker falla con *"took longer than 5 minutes"*.

En CloudShell (`Acciones → Cargar archivo` con `on-start.sh`):

```bash
sed -i 's/\r$//' ~/on-start.sh
aws sagemaker create-notebook-instance-lifecycle-config \
  --notebook-instance-lifecycle-config-name dinosaurios-on-start \
  --on-start Content=$(base64 -w0 ~/on-start.sh)
# si ya existe: update-notebook-instance-lifecycle-config con los mismos parámetros
```

Comprobar que no quedaron `^M`:

```bash
aws sagemaker describe-notebook-instance-lifecycle-config \
  --notebook-instance-lifecycle-config-name dinosaurios-on-start \
  --query 'OnStart[0].Content' --output text | base64 -d | cat -A | head -3
```

Al arrancar, el notebook queda listo cuando el log termina en `ARRANQUE_COMPLETO`:

```bash
tail -n 8 /home/ec2-user/SageMaker/logs/on-start.log; docker ps --filter name=ollama
```

## Identidad de Aborosaurus

Mismo prompt (raíces reales de nombres, salida JSON, temperatura 0.4, semilla 42) con dos modelos:

| | `llama3.2:3b` | `gemma4:e2b` |
|---|---|---|
| Significado | "cabeza imitadora": no usa las raíces dadas | "lagarto del árbol" (*arbor-* + *-saurus*) |
| Coherencia | carnívoro con "dientes de molar"; el campo hábitat describe la dieta | herbívoro arborícola: patas largas para trepar, dientes finos para hojas, vive en el dosel |
| `prompt_imagen` | incluye el nombre y se contradice ("large, medium-sized") | solo rasgos visibles y entorno |

Se eligió **`gemma4:e2b`**. La identidad final está en `identidad.json` y las dos salidas en
`identidad_llama3.2_3b.json` e `identidad_gemma4_e2b.json`. Un detalle a vigilar: 6 m y 1.5 t es
mucho peso para un trepador; el chat no debe contradecirlo, pero puede matizarlo.

## Entrada / salida

- **Recibe:** `POST /api/generate` o `/api/chat` con `model` y `prompt`/`messages`.
- **Devuelve:** JSON con el texto generado en `response` (o `message.content`).
