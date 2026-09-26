set -eu
cd /opt/week11/capstone
printf 'Eze Favour | Operator rebuild | '; date -u +%FT%TZ
printf '%s\n' '$ docker build --progress=plain -f /opt/week11/audit-rerun/Dockerfile.hardened -t epicbook-audit-rerun:1.0.0 backend'
docker build --progress=plain -f /opt/week11/audit-rerun/Dockerfile.hardened -t epicbook-audit-rerun:1.0.0 backend
printf '%s\n' 'Replacing only the isolated training container epicbook-audit-rerun'
docker stop epicbook-audit-rerun
docker rm epicbook-audit-rerun
printf '%s\n' '$ docker run -d --name epicbook-audit-rerun [same private network, no host ports, read-only secret mounts, dropped capabilities] epicbook-audit-rerun:1.0.0'
docker run -d --name epicbook-audit-rerun --network week11-epicbook_back-tier --read-only --tmpfs /tmp --cap-drop ALL --security-opt no-new-privileges --memory 256m --pids-limit 100 -v /opt/week11/capstone/secrets/db_password:/run/secrets/db_password:ro -v /opt/week11/capstone/secrets/session:/run/secrets/session:ro epicbook-audit-rerun:1.0.0
for i in $(seq 1 30); do
  state=$(docker inspect -f '{{.State.Health.Status}}' epicbook-audit-rerun)
  if [ "$state" = healthy ]; then break; fi
  sleep 2
done
[ "$state" = healthy ]
printf '%s\n' '$ docker inspect: selected nonsecret state'
docker inspect -f 'Name={{.Name}} Running={{.State.Running}} Health={{.State.Health.Status}} User={{.Config.User}} Image={{.Config.Image}}' epicbook-audit-rerun
printf '%s\n' '$ docker exec epicbook-audit-rerun id'
docker exec epicbook-audit-rerun id
printf '%s\n' '$ docker ps (public stack still healthy)'
docker ps --format 'table {{.Names}}\t{{.Status}}' --filter name=week11-epicbook
