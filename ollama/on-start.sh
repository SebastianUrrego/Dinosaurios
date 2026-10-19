#!/bin/bash
# Lifecycle config "on-start" del notebook SageMaker "dinosaurios-ollama" (ml.m5.xlarge).
# Se ejecuta como root en CADA arranque. SageMaker solo conserva
# /home/ec2-user/SageMaker entre reinicios, así que todo vive ahí:
#   - data-root de Docker -> /home/ec2-user/SageMaker/docker
#   - modelos de Ollama   -> /home/ec2-user/SageMaker/ollama
# El script tiene 5 min de límite: Docker se reinicia aquí mismo (en primer plano)
# y la descarga del modelo y la API de la app se lanzan en segundo plano con nohup.
set -euxo pipefail

P=/home/ec2-user/SageMaker
MODELO_OLLAMA=gemma4:e2b
LOG=$P/logs/on-start.log

mkdir -p "$P/docker" "$P/ollama" "$P/logs"
chown ec2-user:ec2-user "$P/logs"

# 1) Docker con data-root persistente (se conserva el resto de daemon.json)
python3 - <<'PY'
import json, os
f = "/etc/docker/daemon.json"
cfg = json.load(open(f)) if os.path.exists(f) and os.path.getsize(f) else {}
cfg["data-root"] = "/home/ec2-user/SageMaker/docker"
json.dump(cfg, open(f, "w"), indent=2)
PY
systemctl restart docker
docker info --format '{{.DockerRootDir}}'

# 2) Ollama (solo CPU) con los modelos en el disco persistente
if docker inspect ollama >/dev/null 2>&1; then
  docker start ollama
else
  docker run -d --name ollama --restart unless-stopped \
    -p 127.0.0.1:11434:11434 -v "$P/ollama:/root/.ollama" \
    -e OLLAMA_KEEP_ALIVE=30m ollama/ollama
fi

# 3) Tareas largas en segundo plano
nohup bash -c "
  set -x
  echo INICIO \$(date)
  until curl -sf localhost:11434/api/version; do sleep 2; done
  docker exec ollama ollama pull $MODELO_OLLAMA
  docker exec ollama ollama list
  echo ARRANQUE_COMPLETO \$(date)
" >> "$LOG" 2>&1 &

# 4) API de la app y túnel ngrok (app/sagemaker/iniciar.sh), si ya se configuró api.env
API=$P/Dinosaurios/app/sagemaker/iniciar.sh
if [ -f "$P/api.env" ] && [ -f "$API" ]; then
  nohup sudo -u ec2-user bash "$API" >> "$P/logs/api.log" 2>&1 &
fi

echo "on-start terminado (tareas largas siguen en $LOG)"
