#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
echo 'Eze Favour | DMI Week 11 | Docker cloud-init'
apt-get update
apt-get install -y ca-certificates curl gnupg git jq python3
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
. /etc/os-release
printf 'deb [arch=%s signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu %s stable\n' "$(dpkg --print-architecture)" "$VERSION_CODENAME" > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
install -d -m 0755 /etc/docker
cat > /etc/docker/daemon.json <<'JSON'
{"log-driver":"local","log-opts":{"max-size":"10m","max-file":"3"},"live-restore":true}
JSON
systemctl enable docker
systemctl restart docker
usermod -aG docker ubuntu
install -d -o ubuntu -g ubuntu /opt/week11
docker version
docker compose version
touch /var/lib/week11-bootstrap-ready
echo 'Eze Favour | Docker installation complete'
