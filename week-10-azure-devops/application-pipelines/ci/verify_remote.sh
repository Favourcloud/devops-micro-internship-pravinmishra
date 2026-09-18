#!/usr/bin/env bash
set -euo pipefail

test "$#" -eq 2
case "$1" in
  static) expected_target='week10-a2' ;;
  react) expected_target='week10-a3' ;;
  *) exit 2 ;;
esac
case "$2" in preflight|verify) ;; *) exit 2 ;; esac

root='/var/www/html'
marker='/var/www/.dmi-week10-target'
test "$(id -u)" -ne 0
test "$(id -un)" = 'week10deploy'
test -d /var/www
test ! -L /var
test ! -L /var/www
test "$(stat -c '%u:%g:%a' /var/www)" = '0:0:755'
test -d "$root"
test ! -L "$root"
test -w "$root"
test -f "$marker"
test -r "$marker"
test ! -L "$marker"
test "$(stat -c '%u:%g:%a' "$marker")" = '0:0:644'
test "$(stat -c '%s' "$marker")" -eq 10
test "$(cat -- "$marker")" = "$expected_target"
test ! -e "$root/src"
test ! -e "$root/node_modules"
unsafe_entry="$(find "$root" -mindepth 1 ! -type f ! -type d -print -quit)"
test -z "$unsafe_entry"
systemctl is-active --quiet nginx

if test "$2" = preflight; then
  printf '%s\n' 'Dedicated target and non-root deployment account verified.'
  exit 0
fi

cd -- "$root"
test -s index.html
test -s dmi-site.sha256
sha256sum --strict --check dmi-site.sha256
expected_hash="$(sha256sum index.html | cut -d ' ' -f 1)"
served_hash="$(curl --noproxy '*' --fail --silent --show-error --connect-timeout 5 --max-time 15 http://127.0.0.1/ | sha256sum | cut -d ' ' -f 1)"
test "$served_hash" = "$expected_hash"

if test "$1" = react; then
  route_hash="$(curl --noproxy '*' --fail --silent --show-error --connect-timeout 5 --max-time 15 http://127.0.0.1/dmi-week10-route-check | sha256sum | cut -d ' ' -f 1)"
  test "$route_hash" = "$expected_hash"
  missing_status="$(curl --noproxy '*' --silent --show-error --connect-timeout 5 --max-time 15 --output /dev/null --write-out '%{http_code}' http://127.0.0.1/static/dmi-week10-missing.js)"
  test "$missing_status" = 404
fi

printf '%s\n' 'Eze Favour | Payload checksums and local Nginx HTTP verified.' '/var/www/html:'
find . -mindepth 1 -maxdepth 1 -printf '%f\n' | sort
