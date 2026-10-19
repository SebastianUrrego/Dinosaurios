#!/bin/bash
# Construye y levanta la API del notebook (contenedor dinos-api) y el túnel (contenedor ngrok).
# Se ejecuta una vez como ec2-user, y de nuevo solo si cambia el código de la API:
#   bash /home/ec2-user/SageMaker/Dinosaurios/app/sagemaker/iniciar.sh
# Los dos contenedores usan --restart unless-stopped, como Ollama: Docker los vuelve a levantar
# en cada arranque del notebook, sin que el lifecycle tenga que esperar procesos que no terminan.
#
# Configuración (no va al repo): /home/ec2-user/SageMaker/api.env con
#   API_KEY=...            clave que también usa la web
#   NGROK_AUTHTOKEN=...    token de la cuenta de ngrok
#   NGROK_DOMAIN=...       dominio fijo de ngrok (p. ej. algo.ngrok-free.dev)
set -euo pipefail

P=/home/ec2-user/SageMaker
DIR=$(cd "$(dirname "$0")" && pwd)
ENV_FILE=$P/api.env
mkdir -p "$P/hf"

sed -i 's/\r$//' "$ENV_FILE"   # por si el archivo se editó en Windows
set -a; source "$ENV_FILE"; set +a

# 1) Imagen de la API (la primera vez tarda unos minutos; luego usa la caché de Docker)
docker build -q -t dinos-api "$DIR"

# 2) Contenedores con red del host: la API llega a Ollama en localhost:11434 y ngrok a la API en :8000
pkill -f "venv-api/bin/uvicorn" || true   # versión anterior, sin contenedores
pkill -f "$P/bin/ngrok" || true
docker rm -f dinos-api ngrok >/dev/null 2>&1 || true
docker run -d --name dinos-api --restart unless-stopped --network host \
  --env-file "$ENV_FILE" -v "$P/hf:/hf" dinos-api
docker run -d --name ngrok --restart unless-stopped --network host \
  -e NGROK_AUTHTOKEN="$NGROK_AUTHTOKEN" ngrok/ngrok:latest http 8000 --url "https://$NGROK_DOMAIN"

# 3) Comprobar
for i in $(seq 1 30); do
  curl -sf -H "X-API-Key: $API_KEY" localhost:8000/salud && break
  sleep 2
done
echo
echo "API pública en https://$NGROK_DOMAIN  (logs: docker logs dinos-api / docker logs ngrok)"
