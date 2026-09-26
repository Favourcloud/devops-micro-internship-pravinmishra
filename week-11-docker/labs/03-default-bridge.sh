#!/usr/bin/env bash
set -euo pipefail
docker stop react-multistage
docker network ls
docker images
docker search nginx --limit 3
docker pull nginx
docker run -d --name myweb -p 80:80 nginx
docker exec myweb sh -c 'sed -i "s|<body>|<body><p>Eze Favour · DMI Week 11 · Default bridge</p>|" /usr/share/nginx/html/index.html'
docker ps
curl -fsS http://127.0.0.1/
