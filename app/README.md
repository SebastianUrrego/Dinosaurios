# Aplicación web y chat

```
Navegador ──► Web en EC2 (app/web) ──► generador de nombres (GRU, generador_nombres/)
                    │
                    └── HTTPS (ngrok) + X-API-Key ──► API en SageMaker (app/sagemaker)
                                                         ├──► Ollama gemma4:e2b: identidad y chat
                                                         └──► SD-Turbo en CPU: imagen
```

Flujo de **Nuevo Dinosaurio**: el GRU ya entrenado genera un nombre nuevo (sin reentrenar) → Ollama crea la
identidad → SD-Turbo genera la imagen una sola vez → Ollama escribe la presentación → se guarda todo y el
chat se reinicia con el nuevo dinosaurio.

| Carpeta | Dónde corre | Qué hace |
|---|---|---|
| `web/` | EC2 (Ubuntu 24.04, puerto 80) | Página, generador de nombres, orquestación y almacenamiento de cada dinosaurio (`web/datos/<id>/`) |
| `sagemaker/` | Notebook `dinosaurios-ollama`: contenedores Docker `dinos-api` (`127.0.0.1:8000`) y `ngrok` | Identidad y chat con Ollama, imagen con SD-Turbo |

## Qué recibe y devuelve cada componente

### API de SageMaker (`sagemaker/api.py`)

Todas las peticiones llevan la cabecera `X-API-Key`.

| Ruta | Recibe | Devuelve |
|---|---|---|
| `POST /identidad` | `{"nombre": "Aborosaurus"}` | `{"identidad": {nombre, significado, periodo, apariencia, habitat, alimentacion, comportamiento, rasgo_distintivo, prompt_imagen}, "modelo", "segundos"}` |
| `POST /chat` | `{"identidad": {...}, "mensajes": [{"role": "user"\|"assistant", "content"}], "presentacion": false}` | `{"respuesta", "modelo", "segundos"}` |
| `POST /imagen` | `{"nombre", "prompt_imagen", "semilla"}` | `{"png_base64", "prompt", "modelo", "pasos", "semilla", "segundos"}` (PNG 512×512) |
| `GET /salud` | — | `{"ollama", "modelo_ollama", "modelo_disponible", "modelo_imagen", "imagen_cargada"}` |

El chat envía la identidad completa como mensaje de sistema **en cada petición**, con la regla de no
contradecirla, y solo los últimos 10 mensajes del historial.

### Web (`web/main.py`)

| Ruta | Recibe | Devuelve |
|---|---|---|
| `GET /api/dinosaurio` | — | Dinosaurio actual: nombre, identidad, modelos usados e `imagen_url` |
| `GET /api/modelo` | — | Información del modelo de nombres: arquitectura, parámetros, mejor época, pérdida, muestreo |
| `GET /api/presentacion` | — | `{"respuesta", "imagen_url"}`: la presentación se genera una vez y se guarda |
| `POST /api/chat` | `{"mensajes": [...]}` | `{"respuesta", "imagen_url"}`: `imagen_url` solo si el usuario pide la descripción (descríbete, cómo eres, foto…) |
| `POST /api/nuevo` | — | `{"trabajo", "pasos"}`: inicia Nuevo Dinosaurio en segundo plano |
| `GET /api/trabajos/{id}` | — | `{"estado": "en_curso"\|"listo"\|"error", "paso", "nombre", "dino", "segundos"}` |
| `GET /api/estado` | — | Si SageMaker responde, y qué modelos tiene |
| `GET /imagenes/{id}.png` | — | Imagen del dinosaurio |

El primer dinosaurio es **Aborosaurus**: se carga de `ollama/identidad.json` e `imagen/aborosaurus.png`.

## Puesta en marcha

### 1. ngrok (una vez)

Crear una cuenta gratuita en ngrok, copiar el **authtoken** y reclamar el **dominio fijo** gratuito
(*Domains*). Así la URL no cambia entre sesiones.

### 2. SageMaker

En una terminal de JupyterLab, con el repo clonado en `/home/ec2-user/SageMaker/Dinosaurios`:

```bash
cp Dinosaurios/app/sagemaker/api.env.example /home/ec2-user/SageMaker/api.env
nano /home/ec2-user/SageMaker/api.env            # API_KEY, NGROK_AUTHTOKEN, NGROK_DOMAIN
bash Dinosaurios/app/sagemaker/iniciar.sh        # construye la imagen la primera vez (~5 min)
```

`iniciar.sh` crea dos contenedores con `--restart unless-stopped`, igual que Ollama: Docker los
levanta solos en cada arranque del notebook y el lifecycle solo hace un `docker start` instantáneo.
Solo hay que volver a ejecutarlo si cambia el código de la API. Logs: `docker logs dinos-api` y `docker logs ngrok`.

> El lifecycle **no** debe lanzar procesos que no terminan (por ejemplo `nohup uvicorn &`): SageMaker
> espera a que acaben y el arranque falla con *"took longer than 5 minutes"*.

### 3. Web en local (prueba)

```bash
cd app/web
cp .env.example .env        # SAGEMAKER_URL y API_KEY
pip install -r requirements.txt
pip install torch --index-url https://download.pytorch.org/whl/cpu
uvicorn main:app --port 8000
```

### 4. Web en AWS (EC2)

EC2 `t3.small`, Ubuntu 24.04, disco de 16 GB, security group con el puerto 80 abierto (y 22 solo desde tu IP).
En la instancia:

```bash
git clone https://github.com/SebastianUrrego/Dinosaurios.git && cd Dinosaurios
cp app/web/.env.example app/web/.env && nano app/web/.env
sudo bash app/web/instalar_ec2.sh
```

El sitio queda en `http://<IP pública>` como servicio `dinosaurios` (`sudo systemctl status dinosaurios`).

## Seguridad

- `api.env` y `app/web/.env` están fuera del repositorio (`.gitignore`).
- La API de SageMaker solo escucha en `127.0.0.1` y ngrok la publica con HTTPS; sin la `X-API-Key` responde 401.
- Ollama no se publica: solo lo usa la API desde el mismo notebook.
