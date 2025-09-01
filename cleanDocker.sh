#!/usr/bin/env bash
set -e

echo "[INFO] Limpando Docker (containers, volumes, imagens e builds)..."

# Para todos os containers em execução
echo "[INFO] Parando todos os containers..."
docker stop $(docker ps -aq) 2>/dev/null || true

# Remove todos os containers
echo "[INFO] Removendo todos os containers..."
docker rm $(docker ps -aq) 2>/dev/null || true

# Remove todas as imagens
echo "[INFO] Removendo todas as imagens..."
docker rmi -f $(docker images -q) 2>/dev/null || true

# Remove todos os volumes
echo "[INFO] Removendo todos os volumes..."
docker volume rm $(docker volume ls -q) 2>/dev/null || true

# Remove todas as redes não utilizadas
echo "[INFO] Removendo redes não utilizadas..."
docker network prune -f

# Remove cache de builds
echo "[INFO] Limpando cache de builds..."
docker builder prune -af

echo "[OK] Docker limpo com sucesso!"
