#!/usr/bin/env bash
set -euo pipefail
sha256sum "$HOME/nginx-logs/access.log" "$HOME/nginx-logs/error.log"
docker stop myweb
docker rm myweb
ls -l "$HOME/nginx-logs"
sha256sum "$HOME/nginx-logs/access.log" "$HOME/nginx-logs/error.log"
cat "$HOME/nginx-logs/access.log"
