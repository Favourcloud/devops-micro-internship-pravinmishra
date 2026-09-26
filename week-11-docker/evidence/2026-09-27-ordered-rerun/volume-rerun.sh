set -eu
printf 'Eze Favour | Week 11 | Shared volume rerun | '; date -u +%FT%TZ
docker network create week11-volume-rerun
docker volume create week11-volume-rerun
docker run --rm -v week11-volume-rerun:/shared node:22-bookworm-slim chown 1000:1000 /shared
docker run -d --name week11-volume-backend --network week11-volume-rerun --read-only --tmpfs /tmp --cap-drop ALL --security-opt no-new-privileges -v week11-volume-rerun:/shared volume-backend:1.0
docker run -d --name week11-volume-frontend --network week11-volume-rerun --read-only --tmpfs /tmp --cap-drop ALL --security-opt no-new-privileges -v week11-volume-rerun:/shared:ro -p 127.0.0.1:18814:8080 volume-frontend:1.0
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
docker exec week11-volume-backend curl -fsS http://localhost/write
curl -fsS http://127.0.0.1:18814/
