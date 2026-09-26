#!/usr/bin/env bash
set -euo pipefail
docker stop frontend api database
docker rm frontend api database
docker network rm frontend-network backend-network
docker images
docker search nginx --limit 3
docker pull nginx
mkdir -p "$HOME/nginx-logs"
docker run -d --name myweb -p 80:80 -v "$HOME/nginx-logs:/var/log/nginx" nginx
docker exec myweb sh -c 'sed -i "s|<body>|<body><p>Eze Favour · DMI Week 11 · Bind-mounted logs</p>|" /usr/share/nginx/html/index.html'
docker ps
curl -fsS http://127.0.0.1/
ls -l "$HOME/nginx-logs"
# Capture the running website before executing 04-bind-mount-remove.sh.
