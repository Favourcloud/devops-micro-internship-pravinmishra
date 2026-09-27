#!/usr/bin/env bash
# Eze Favour — created after the recorded Claude plan in this rerun.
# Docker calls are read-only. Writes are limited to temp JSON and a local report.
set -euo pipefail
container=${1:-epicbook-audit-rerun}
[[ "$container" =~ ^[a-zA-Z0-9][a-zA-Z0-9_.-]*$ ]] || { echo 'Invalid container name' >&2; exit 2; }
umask 077
mkdir -p reports
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
pass=0; warn=0; fail=0
result() {
  printf '%s | %s | %s\n' "$1" "$2" "$3"
  case "$1" in PASS) pass=$((pass+1));; WARN) warn=$((warn+1));; FAIL) fail=$((fail+1));; esac
}
check_exists() {
  if ! docker inspect --type container "$container" > "$tmp/container.json" 2>/dev/null; then
    result FAIL exists "$container does not exist or cannot be inspected"; return 1
  fi
  if jq -e '.[0].State.Running == true' "$tmp/container.json" >/dev/null; then
    result PASS exists "$container exists and is running"
  else
    result WARN exists "$container exists but is not running"
  fi
}
check_user() {
  local user
  user=$(jq -r '.[0].Config.User // ""' "$tmp/container.json")
  if [[ -z "$user" || "$user" =~ ^(root|0)(:.*)?$ ]]; then
    result FAIL user 'Configured user defaults to root / UID 0'
  else
    result PASS user "Configured user: $user; runtime UID should also be verified"
  fi
}
check_healthcheck() {
  if jq -e '.[0].Config.Healthcheck.Test | type == "array" and length > 0 and .[0] != "NONE"' "$tmp/container.json" >/dev/null 2>&1; then
    result PASS healthcheck 'Effective HEALTHCHECK configured; readiness is a separate observation'
  else
    result FAIL healthcheck 'No effective HEALTHCHECK'
  fi
}
check_image_pin() {
  local ref
  ref=$(jq -r '.[0].Config.Image' "$tmp/container.json")
  if [[ "$ref" =~ @sha256:[0-9a-f]{64}$ ]]; then
    result PASS image 'Runtime image reference uses an immutable digest'
  elif [[ "${ref##*/}" == *:* && -n "${ref##*:}" && "${ref##*:}" != latest ]]; then
    result PASS image "Versioned runtime tag: $ref (mutable; digest preferred)"
  else
    result FAIL image "Unversioned runtime image: $ref"
  fi
}
check_privileged() {
  if jq -e '.[0].HostConfig.Privileged == false' "$tmp/container.json" >/dev/null; then
    result PASS privileged 'Privileged mode disabled'
  else
    result FAIL privileged 'Privileged mode enabled or unknown'
  fi
}
check_ports() {
  local image_id exposed published
  image_id=$(jq -r '.[0].Image' "$tmp/container.json")
  if ! docker image inspect "$image_id" > "$tmp/image.json" 2>/dev/null; then
    result WARN ports 'Image inspection failed; port review incomplete'; return
  fi
  exposed=$(jq '.[0].Config.ExposedPorts // {} | length' "$tmp/image.json")
  published=$(jq '.[0].HostConfig.PortBindings // {} | [.[] | select(. != null and length > 0)] | length' "$tmp/container.json")
  if (( exposed <= 1 && published <= 1 )); then
    result PASS ports "$exposed declared port(s), $published published port(s)"
  else
    result WARN ports "$exposed declared, $published published; review necessity and firewall separately"
  fi
}
{
  printf 'Eze Favour | Week 11 | Read-only Docker hardening audit\nUTC: %s\nContainer: %s\n' "$(date -u +%FT%TZ)" "$container"
  if check_exists; then
    check_user
    check_healthcheck
    check_image_pin
    check_privileged
    check_ports
  else
    for check in user healthcheck image privileged ports; do result WARN "$check" 'Not evaluated: target unavailable'; done
  fi
  printf 'SUMMARY: PASS=%s WARN=%s FAIL=%s\n' "$pass" "$warn" "$fail"
} > "$tmp/report.txt"
cp "$tmp/report.txt" reports/docker-hardening-report.txt
cat reports/docker-hardening-report.txt
# Exit 0 means the audit ran; the report honestly records security failures.
