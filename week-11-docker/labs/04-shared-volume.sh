#!/usr/bin/env bash
set -euo pipefail
cd /opt/week11
find volumes -maxdepth 2 -type f
docker network create mynetwork
docker volume create shared-data
docker run --rm -v shared-data:/shared node:22-bookworm-slim chown 1000:1000 /shared
cat volumes/backend/Dockerfile volumes/frontend/Dockerfile
docker build --progress=plain -t volume-backend:1.0 volumes/backend
docker build --progress=plain -t volume-frontend:1.0 volumes/frontend
docker run -d --name backend --network mynetwork -v shared-data:/shared volume-backend:1.0
docker run -d --name frontend --network mynetwork -v shared-data:/shared:ro -p 80:8080 volume-frontend:1.0
docker ps
for i in $(seq 1 20); do docker exec backend curl -fsS http://localhost/write && break || sleep 1; done
curl -fsS http://127.0.0.1/
