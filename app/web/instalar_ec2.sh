#!/bin/bash
# Instala la web en una EC2 Ubuntu 24.04 y la deja como servicio (systemd) en el puerto 80.
# Uso, dentro del repo clonado en la EC2:
#   1. crear app/web/.env con SAGEMAKER_URL y API_KEY (ver app/web/.env.example)
#   2. sudo bash app/web/instalar_ec2.sh
set -euo pipefail

WEB=$(cd "$(dirname "$0")" && pwd)
RAIZ=$(cd "$WEB/../.." && pwd)
USUARIO=${SUDO_USER:-ubuntu}

apt-get update -q
apt-get install -y -q python3-venv
sudo -u "$USUARIO" python3 -m venv "$RAIZ/.venv"
sudo -u "$USUARIO" "$RAIZ/.venv/bin/pip" install -q --upgrade pip
sudo -u "$USUARIO" "$RAIZ/.venv/bin/pip" install -q torch --index-url https://download.pytorch.org/whl/cpu
sudo -u "$USUARIO" "$RAIZ/.venv/bin/pip" install -q -r "$WEB/requirements.txt"

cat > /etc/systemd/system/dinosaurios.service <<EOF
[Unit]
Description=Isla de los Dinosaurios (web)
After=network-online.target

[Service]
User=$USUARIO
WorkingDirectory=$WEB
ExecStart=$RAIZ/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 80
AmbientCapabilities=CAP_NET_BIND_SERVICE
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable dinosaurios
systemctl restart dinosaurios
sleep 5
curl -s localhost/api/estado
echo
echo "Web en http://$(curl -s https://checkip.amazonaws.com)"
