#!/usr/bin/env bash
# Prepara una instancia EC2 recién creada para correr los contenedores.
# Funciona en Ubuntu 24.04 y en Amazon Linux 2023.
#
# Uso (dentro de la EC2, por SSH):
#   chmod +x scripts/ec2-setup.sh && sudo ./scripts/ec2-setup.sh
set -euo pipefail

[ "$(id -u)" -eq 0 ] || { echo "Ejecuta con sudo"; exit 1; }
. /etc/os-release
USUARIO="${SUDO_USER:-ubuntu}"

echo "==> Sistema detectado: $PRETTY_NAME"

if [ "$ID" = "ubuntu" ] || [ "$ID" = "debian" ]; then
  apt-get update -y
  apt-get install -y ca-certificates curl git
  # Script oficial de Docker: instala Docker Engine + plugin de Compose (repo oficial).
  curl -fsSL https://get.docker.com | sh

elif [ "$ID" = "amzn" ]; then
  dnf install -y docker git
  # Amazon Linux no trae el plugin de Compose en sus repos: se instala el binario oficial.
  ARCH=$(uname -m)  # x86_64 o aarch64 (instancias Graviton)
  mkdir -p /usr/local/lib/docker/cli-plugins
  curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-${ARCH}" \
    -o /usr/local/lib/docker/cli-plugins/docker-compose
  chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
  # Buildx (necesario para `docker compose build` en versiones recientes)
  BX=$(curl -fsSL https://api.github.com/repos/docker/buildx/releases/latest | grep -oP '"tag_name": "\K[^"]+')
  BXARCH=$([ "$ARCH" = "aarch64" ] && echo arm64 || echo amd64)
  curl -fsSL "https://github.com/docker/buildx/releases/download/${BX}/buildx-${BX}.linux-${BXARCH}" \
    -o /usr/local/lib/docker/cli-plugins/docker-buildx
  chmod +x /usr/local/lib/docker/cli-plugins/docker-buildx
else
  echo "Distribución no soportada por este script: $ID"; exit 1
fi

systemctl enable --now docker
# Permite usar `docker` sin sudo (aplica al volver a iniciar sesión SSH).
usermod -aG docker "$USUARIO"

# Swap de 2 GB: una t3.micro tiene 1 GB de RAM y los builds + MongoDB pueden agotarla.
if ! swapon --show | grep -q /swapfile; then
  echo "==> Creando swap de 2 GB"
  fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo
docker --version
docker compose version
echo
echo "==> Listo. Cierra la sesión SSH y vuelve a entrar para usar docker sin sudo."
