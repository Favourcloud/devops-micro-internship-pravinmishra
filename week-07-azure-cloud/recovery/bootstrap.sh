#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y ca-certificates curl git nginx mysql-client python3 python3-pip unzip
if ! test -f /swapfile; then
  fallocate -l 3G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi
cd /tmp
curl -fsSLO https://nodejs.org/dist/v22.23.2/node-v22.23.2-linux-x64.tar.xz
curl -fsSLO https://nodejs.org/dist/v22.23.2/SHASUMS256.txt
grep ' node-v22.23.2-linux-x64.tar.xz$' SHASUMS256.txt | sha256sum -c -
tar -xJf node-v22.23.2-linux-x64.tar.xz -C /usr/local --strip-components=1
node --version
npm --version
touch /var/lib/week07-bootstrap-ready
