#!/usr/bin/env bash
set -euo pipefail
cd /opt/week11
printf 'Eze Favour | React single-stage and multi-stage comparison\n'
cat react/.dockerignore react/Dockerfile.single react/Dockerfile
docker build --progress=plain -t react-single -f react/Dockerfile.single react
docker run -d --name react-single -p 3000:3000 react-single
docker build --progress=plain -t react-multistage -f react/Dockerfile react
docker stop static-site
docker run -d --name react-multistage --restart unless-stopped --read-only --tmpfs /tmp --cap-drop ALL --security-opt no-new-privileges -p 80:8080 react-multistage
docker image inspect react-single react-multistage --format '{{.RepoTags}} {{.Size}}'
docker ps
