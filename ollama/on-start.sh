#!/bin/bash
# Lifecycle configuration "on-start" de la notebook instance de SageMaker.
# Se ejecuta como root en cada arranque y SageMaker lo cancela a los 5 minutos.
# Docker se reinicia aquí, en primer plano: reiniciarlo en segundo plano, cuando el
# lifecycle ya terminó, dejaba el arranque del notebook colgado hasta el límite.
# Solo la primera descarga de la imagen (lenta) va en segundo plano.
# Log: /home/ec2-user/SageMaker/logs/on-start.log
set -ex

P=/home/ec2-user/SageMaker
LOG=$P/logs/on-start.log
mkdir -p "$P/docker" "$P/ollama" "$P/logs"
chown ec2-user:ec2-user "$P/logs"
echo "=== $(date) inicio ===" >> "$LOG"

# 1. data-root de Docker en el disco persistente (conserva las demás opciones de daemon.json)
python3 - <<'PY'
import json, os
path = "/etc/docker/daemon.json"
cfg = {}
if os.path.exists(path) and os.path.getsize(path):
    with open(path) as f:
        cfg = json.load(f)
cfg["data-root"] = "/home/ec2-user/SageMaker/docker"
os.makedirs("/etc/docker", exist_ok=True)
with open(path, "w") as f:
    json.dump(cfg, f, indent=2)
PY
systemctl restart docker
docker info --format 'Docker data-root: {{.DockerRootDir}}' | tee -a "$LOG"

# 2. Contenedor de Ollama; los modelos quedan en $P/ollama
RUN="docker run -d --name ollama --restart unless-stopped \
  -p 127.0.0.1:11434:11434 -v $P/ollama:/root/.ollama \
  -e OLLAMA_KEEP_ALIVE=30m ollama/ollama"
if docker inspect ollama >/dev/null 2>&1; then
  docker start ollama
elif docker image inspect ollama/ollama >/dev/null 2>&1; then
  $RUN
else
  # Primera vez: la imagen pesa ~5.5 GB y su descarga puede pasar de 5 minutos
  nohup bash -c "$RUN" >> "$LOG" 2>&1 < /dev/null &
fi

# 3. Dejar constancia en el log cuando la API responda
nohup bash -c 'until curl -sf http://localhost:11434/api/version; do sleep 2; done; echo; echo "=== $(date) fin ==="' \
  >> "$LOG" 2>&1 < /dev/null &

echo "on-start terminado"
