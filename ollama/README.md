# Ollama en SageMaker

| Archivo | Uso |
|---|---|
| `on-start.sh` | Lifecycle configuration *on-start*: mueve el `data-root` de Docker a `/home/ec2-user/SageMaker/docker` y levanta el contenedor `ollama` (modelos en `/home/ec2-user/SageMaker/ollama`). |
| `verificar_ollama.ipynb` | Comprueba la instalación, descarga el modelo, guarda nombre y versión en `modelo.json` y prueba una instrucción. |

## Pasos

1. SageMaker → *Lifecycle configurations* → *Create* → **Notebook instance** → pegar `on-start.sh` en **Start notebook**.
2. Notebook instance `ml.m5.xlarge`, rol `LabRole`, volumen de 50 GB y la lifecycle configuration del paso 1.
3. Al abrir Jupyter, clonar el repo dentro de `/home/ec2-user/SageMaker` y ejecutar `verificar_ollama.ipynb`.

La API queda en `http://localhost:11434` (solo local). Para exponerla a la aplicación se usa ngrok (paso posterior).

## Entrada / salida

- **Recibe:** `POST /api/generate` o `/api/chat` con `model` y `prompt`/`messages`.
- **Devuelve:** JSON con el texto generado en `response` (o `message.content`).
