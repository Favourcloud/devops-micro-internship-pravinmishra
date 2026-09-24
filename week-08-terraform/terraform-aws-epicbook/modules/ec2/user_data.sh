#!/bin/bash
set -Eeuo pipefail
umask 077
export DEBIAN_FRONTEND=noninteractive
trap 'echo "EpicBook bootstrap failed; do not treat Nginx alone as readiness." >&2' ERR

retry() {
  local attempt
  for attempt in 1 2 3 4 5; do
    if "$@"; then return 0; fi
    sleep 10
  done
  return 1
}

# Installation runs only on a future, explicitly authorized EC2 instance.
retry timeout 300 apt-get -o Acquire::Retries=3 -o Acquire::http::Timeout=30 update -qq
retry timeout 600 apt-get -o Acquire::Retries=3 -o Acquire::http::Timeout=30 install -y -qq ca-certificates curl xz-utils git nginx mysql-client python3-boto3
systemctl stop nginx
id epicbook >/dev/null 2>&1 || useradd --system --create-home --home-dir /var/lib/epicbook --shell /usr/sbin/nologin epicbook
install -d -m 0755 /opt/epicbook /usr/local/lib/epicbook
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
curl --fail --silent --show-error --location --retry 3 --connect-timeout 10 --max-time 180 \
  https://nodejs.org/dist/v22.23.3/node-v22.23.3-linux-x64.tar.xz -o "$work/node.tar.xz"
printf '%s  %s\n' 'df450af89261115ef9f9e3830c3eeb2cc9213b63c720b1af623cb5dcbe2e02de' "$work/node.tar.xz" | sha256sum -c -
tar -xJf "$work/node.tar.xz" --strip-components=1 -C /usr/local
curl --fail --silent --show-error --location --retry 3 --connect-timeout 10 --max-time 60 \
  https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem -o /etc/ssl/certs/rds-global-bundle.pem
chmod 0644 /etc/ssl/certs/rds-global-bundle.pem

cd /opt/epicbook
git init -q
git remote add origin https://github.com/pravinmishraaws/theepicbook.git
timeout 180 git fetch -q --depth=1 origin 763becebb8d3f5663a76bb30facddc25be63cfd5
git checkout -q --detach FETCH_HEAD
test "$(git rev-parse HEAD)" = 763becebb8d3f5663a76bb30facddc25be63cfd5
chown -R epicbook:epicbook /opt/epicbook
timeout 600 runuser -u epicbook -- env HOME=/var/lib/epicbook /usr/local/bin/npm ci --omit=dev --ignore-scripts --no-audit --no-fund
chown -R root:root /opt/epicbook
chmod -R a+rX,go-w /opt/epicbook
rm config/config.json
ln -s /run/epicbook/config.json config/config.json
cat > /etc/epicbook-runtime.json <<'EPICBOOK_METADATA'
${runtime_config}
EPICBOOK_METADATA
chmod 0600 /etc/epicbook-runtime.json
cat > /usr/local/lib/epicbook/runtime.py <<'EPICBOOK_PYTHON'
${runtime_py}
EPICBOOK_PYTHON
chmod 0700 /usr/local/lib/epicbook/runtime.py

cat > /etc/systemd/system/epicbook-config.service <<'UNIT'
[Unit]
Description=Prepare EpicBook database and ephemeral runtime config
Wants=network-online.target
After=network-online.target
Before=epicbook.service
[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /usr/local/lib/epicbook/runtime.py prepare
TimeoutStartSec=900
RemainAfterExit=yes
UMask=0077
StandardOutput=null
StandardError=journal
UNIT
cat > /etc/systemd/system/epicbook.service <<'UNIT'
[Unit]
Description=Pinned upstream EpicBook application
Requires=epicbook-config.service
After=network-online.target epicbook-config.service
StartLimitIntervalSec=120
StartLimitBurst=3
[Service]
User=epicbook
Group=epicbook
WorkingDirectory=/opt/epicbook
Environment=NODE_ENV=production PORT=8080
ExecStart=/usr/local/bin/node server.js
Restart=on-failure
RestartSec=10
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadOnlyPaths=/run/epicbook
IPAddressDeny=169.254.169.254/32 fd00:ec2::254/128
# Upstream may print Sequelize configuration on error: never put raw app logs into cloud-init/journal.
StandardOutput=null
StandardError=null
[Install]
WantedBy=multi-user.target
UNIT
cat > /etc/nginx/sites-available/epicbook <<'NGINX'
server {
    listen 80 default_server;
    server_name _;
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 5s;
        proxy_read_timeout 15s;
    }
}
NGINX
rm -f /etc/nginx/sites-enabled/default
ln -s /etc/nginx/sites-available/epicbook /etc/nginx/sites-enabled/epicbook
nginx -t
systemctl daemon-reload
systemctl enable --now epicbook.service
systemctl enable --now nginx
catalogue_ready() {
  systemctl is-active --quiet epicbook && curl --fail --silent --max-time 5 http://127.0.0.1/ > "$work/page" && grep -q 'Add to Cart' "$work/page"
}
for attempt in $(seq 1 30); do
  if catalogue_ready; then
    echo 'EpicBook seeded catalogue readiness passed; browser/cart/order verification still required.'
    exit 0
  fi
  sleep 5
done
echo 'EpicBook catalogue readiness failed (not a default Nginx success).' >&2
exit 1
