#!/usr/bin/env bash
set -euo pipefail
cd /opt/week11
docker stop myweb
docker rm myweb
docker network create mynetwork
cat networking/custom/frontend/Dockerfile
docker build --progress=plain -t custom-frontend:1.0 networking/custom/frontend
docker run -d --name frontend --network mynetwork -p 80:8080 custom-frontend:1.0
docker run -d --name backend --network mynetwork nginx
docker ps
docker network inspect mynetwork
for i in $(seq 1 20); do curl -fsS http://127.0.0.1/ && break || sleep 1; done
docker exec frontend curl -fsS http://backend
