#!/bin/bash
set -Eeuo pipefail
trap 'printf "Nginx bootstrap failed at line %s\n" "$LINENO" >&2' ERR

retry() {
  local attempt
  for attempt in 1 2 3 4 5; do
    if "$@"; then
      return 0
    fi
    if [ "$attempt" -lt 5 ]; then
      sleep "$((attempt * 10))"
    fi
  done
  return 1
}

export DEBIAN_FRONTEND=noninteractive
retry apt-get -o Acquire::Retries=3 -o DPkg::Lock::Timeout=120 update
retry apt-get -o Acquire::Retries=3 -o DPkg::Lock::Timeout=120 install -y --no-install-recommends nginx curl ca-certificates

cat > /var/www/html/index.nginx-debian.html <<'HTML'
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Eze Favour | Week 08 AWS VM</title>
</head>
<body>
  <h1>Nginx — Week 08 Assignment 2</h1>
  <p>Eze Favour · DevOps Micro Internship</p>
  <p>Ubuntu on EC2, provisioned with Terraform.</p>
</body>
</html>
HTML

nginx -t
systemctl enable --now nginx
systemctl is-active --quiet nginx
curl --fail --silent --show-error --retry 6 --retry-connrefused --retry-delay 2 http://127.0.0.1/ |
  grep -F 'Nginx — Week 08 Assignment 2'
