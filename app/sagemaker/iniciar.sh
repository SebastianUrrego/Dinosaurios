#!/bin/bash
# Levanta la API del notebook (api.py) y la publica con ngrok. Se ejecuta como ec2-user:
#   bash /home/ec2-user/SageMaker/Dinosaurios/app/sagemaker/iniciar.sh
# Configuración (no va al repo): /home/ec2-user/SageMaker/api.env con
#   API_KEY=...            clave que también usa la web
#   NGROK_AUTHTOKEN=...    token de la cuenta de ngrok
#   NGROK_DOMAIN=...       dominio fijo de ngrok (p. ej. algo.ngrok-free.app)
# Todo lo instalado queda en el disco persistente. Log: /home/ec2-user/SageMaker/logs/api.log
set -euo pipefail

P=/home/ec2-user/SageMaker
DIR=$(cd "$(dirname "$0")" && pwd)
VENV=$P/venv-api
LOG=$P/logs/api.log
mkdir -p "$P/logs" "$P/bin" "$P/hf"

set -a; source "$P/api.env"; set +a
export HF_HOME=$P/hf

# 1) Entorno de Python (solo la primera vez)
if [ ! -x "$VENV/bin/uvicorn" ]; then
  /home/ec2-user/anaconda3/envs/python3/bin/python -m venv "$VENV"
  "$VENV/bin/pip" install -q --upgrade pip
  "$VENV/bin/pip" install -q torch --index-url https://download.pytorch.org/whl/cpu
  "$VENV/bin/pip" install -q -r "$DIR/requirements.txt"
fi

# 2) ngrok (solo la primera vez)
if [ ! -x "$P/bin/ngrok" ]; then
  curl -sSL https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz | tar -xz -C "$P/bin"
fi

# 3) Reiniciar API y túnel
pkill -f "uvicorn api:app" || true
pkill -f "$P/bin/ngrok" || true
cd "$DIR"
nohup "$VENV/bin/uvicorn" api:app --host 127.0.0.1 --port 8000 >> "$LOG" 2>&1 &
nohup "$P/bin/ngrok" http 8000 --authtoken "$NGROK_AUTHTOKEN" --url "https://$NGROK_DOMAIN" \
  --log stdout >> "$P/logs/ngrok.log" 2>&1 &

for i in $(seq 1 30); do
  curl -sf -H "X-API-Key: $API_KEY" localhost:8000/salud && break
  sleep 2
done
echo
echo "API pública en https://$NGROK_DOMAIN"
