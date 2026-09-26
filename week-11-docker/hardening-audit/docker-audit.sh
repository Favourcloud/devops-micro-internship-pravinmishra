#!/usr/bin/env bash
# Read-only Docker calls; the only writes are a local report and temporary JSON.
set -euo pipefail
container=${1:-epicbook-audit}
[[ "$container" =~ ^[a-zA-Z0-9][a-zA-Z0-9_.-]*$ ]] || { echo 'Invalid container name' >&2; exit 2; }
umask 077
mkdir -p reports
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
report=reports/docker-hardening-report.txt
pass=0; warn=0; fail=0
result() { printf '%s | %s | %s\n' "$1" "$2" "$3"; case "$1" in PASS) pass=$((pass+1));; WARN) warn=$((warn+1));; FAIL) fail=$((fail+1));; esac; }
check_exists() { if docker inspect --type container "$container" > "$tmp/container.json" 2>/dev/null; then result PASS exists "$container exists"; else result FAIL exists "$container does not exist"; return 1; fi; }
check_user() { local user;user=$(jq -r '.[0].Config.User // ""' "$tmp/container.json");if [[ -z "$user" || "$user" == root || "$user" == root:* || "$user" == 0 || "$user" == 0:* ]];then result FAIL user 'Container configured as root';else result PASS user "Configured user: $user";fi; }
check_healthcheck() { if jq -e '.[0].Config.Healthcheck.Test | type == "array" and length > 0 and .[0] != "NONE"' "$tmp/container.json" >/dev/null 2>&1;then result PASS healthcheck 'HEALTHCHECK is defined';else result FAIL healthcheck 'No effective HEALTHCHECK';fi; }
check_image_pin() { local ref;ref=$(jq -r '.[0].Config.Image' "$tmp/container.json");if [[ "$ref" == *@sha256:* ]];then result PASS image 'Digest-pinned image';elif [[ "${ref##*/}" == *:* && "${ref##*:}" != latest ]];then result PASS image "Versioned image tag: $ref (mutable; digest preferred)";else result FAIL image "Unversioned image: $ref";fi; }
check_privileged() { if jq -e '.[0].HostConfig.Privileged == false' "$tmp/container.json" >/dev/null;then result PASS privileged 'Privileged mode is disabled';else result FAIL privileged 'Privileged mode is enabled';fi; }
check_ports() { local exposed published;exposed=$(jq '.[0].Config.ExposedPorts // {} | length' "$tmp/image.json");published=$(jq '.[0].HostConfig.PortBindings // {} | length' "$tmp/container.json");if ((exposed<=1 && published<=1));then result PASS ports "$exposed image port(s), $published published binding(s)";else result WARN ports "$exposed image port(s), $published binding(s); review necessity";fi; }
{
 printf 'Eze Favour | DMI Week 11 | Read-only Docker hardening audit\nUTC: %s\nContainer: %s\n' "$(date -u +%FT%TZ)" "$container"
 if check_exists;then
  image_id=$(jq -r '.[0].Image' "$tmp/container.json")
  docker image inspect "$image_id" > "$tmp/image.json"
  check_user;check_healthcheck;check_image_pin;check_privileged;check_ports
 else
  for check in user healthcheck image privileged ports;do result WARN "$check" 'Not evaluated: target missing';done
 fi
 printf 'SUMMARY: PASS=%s WARN=%s FAIL=%s\n' "$pass" "$warn" "$fail"
} > "$report"
cat "$report"
# A completed audit can legitimately contain failures; missing target is visible in its report.
