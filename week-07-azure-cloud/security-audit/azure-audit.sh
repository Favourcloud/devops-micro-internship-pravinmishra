#!/usr/bin/env bash
# Read-only Azure security audit. Cloud writes are deliberately absent.
set -euo pipefail
umask 077
HERE=$(cd -- "$(dirname -- "$0")" && pwd)
OUT=${DMI_AUDIT_OUTPUT:-"$HERE/reports"}
mkdir -p "$OUT"
SCRATCH=$(mktemp -d)
trap 'rm -rf "$SCRATCH"' EXIT
RG=dmi-w07-labs-20260926-rg
read_check() {
  local target=$1; shift
  if ! az "$@" --only-show-errors -o json > "$SCRATCH/$target.json" 2> "$SCRATCH/$target.stderr"; then
    printf '{"query_error":true}\n' > "$SCRATCH/$target.json"
  fi
}
check_nsg() { read_check nsg network nsg list -g "$RG"; }
check_storage() { read_check storage storage account list -g mini-finance-rg; }
check_disks() { read_check disks disk list -g "$RG"; }
check_mysql() { read_check mysql mysql flexible-server list -g "$RG"; }
check_nsg
check_storage
check_disks
check_mysql
python3 "$HERE/analyze.py" "$SCRATCH" "$OUT"
