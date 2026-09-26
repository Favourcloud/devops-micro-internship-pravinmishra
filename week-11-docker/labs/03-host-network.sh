#!/usr/bin/env bash
set -euo pipefail
docker stop frontend backend
docker rm frontend backend
docker network rm mynetwork
docker run -d --network host --name fastapp nginx
docker ps
curl -fsS http://127.0.0.1/
docker inspect fastapp --format '{{.HostConfig.NetworkMode}}'
docker stop fastapp
docker rm fastapp
