#!/bin/bash
# Lifecycle configuration "on-start" de la notebook instance de SageMaker.
# Se ejecuta como root en cada arranque. SageMaker cancela el script a los 5 minutos,
# por eso la parte lenta (reiniciar Docker y levantar Ollama) corre en segundo plano.
# Log: /home/ec2-user/SageMaker/logs/on-start.log
set -e

mkdir -p /home/ec2-user/SageMaker/docker /home/ec2-user/SageMaker/ollama /home/ec2-user/SageMaker/logs
chown ec2-user:ec2-user /home/ec2-user/SageMaker/logs

cat > /tmp/ollama-start.sh <<'EOF'
set -euo pipefail
echo "=== $(date) inicio ==="

# 1. data-root de Docker en el disco persistente (conserva las demás opciones de daemon.json)
python3 - <<'PY'
import json, os
path = "/etc/docker/daemon.json"
cfg = {}
if os.path.exists(path):
    with open(path) as f:
        txt = f.read().strip()
        cfg = json.loads(txt) if txt else {}
cfg["data-root"] = "/home/ec2-user/SageMaker/docker"
os.makedirs("/etc/docker", exist_ok=True)
with open(path, "w") as f:
    json.dump(cfg, f, indent=2)
PY

systemctl restart docker || service docker restart
for i in $(seq 1 30); do docker info >/dev/null 2>&1 && break; sleep 2; done
docker info --format 'Docker data-root: {{.DockerRootDir}}'

# 2. Contenedor de Ollama; los modelos quedan en /home/ec2-user/SageMaker/ollama
if docker ps -a --format '{{.Names}}' | grep -qx ollama; then
  docker start ollama
else
  docker run -d --name ollama --restart unless-stopped \
    -p 127.0.0.1:11434:11434 \
    -v /home/ec2-user/SageMaker/ollama:/root/.ollama \
    ollama/ollama
fi

# 3. Esperar a que la API responda
for i in $(seq 1 60); do curl -sf http://localhost:11434/api/version && break; sleep 2; done
echo
echo "=== $(date) fin ==="
EOF

nohup bash /tmp/ollama-start.sh >> /home/ec2-user/SageMaker/logs/on-start.log 2>&1 &
