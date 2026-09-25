#!/usr/bin/env bash
# Original Codex-assisted implementation. No supplied instructor kit was available.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
umask 077
mkdir -p reports
REPORT=reports/pipeline-health-report.txt
EVIDENCE=reports/evidence.json
printf 'Eze Favour\nOverall Status: RUNNING\n' > "$REPORT"
if ! python3 fetch.py; then
  printf 'Eze Favour\nOverall Status: ERROR\nEvidence retrieval incomplete; do not infer health.\n' > "$REPORT"
  cat "$REPORT"
  exit 2
fi
check_auth() { python3 classify.py has AUTH; }
check_terraform() { python3 classify.py has TERRAFORM; }
check_ansible() { python3 classify.py has ANSIBLE; }
check_application() { python3 classify.py has APPLICATION; }
checks=(check_auth check_terraform check_ansible check_application)
categories=()
for check in "${checks[@]}"; do
  if "$check"; then categories+=("${check#check_}"); fi
done
set +e
if test "${#categories[@]}" -gt 0; then
  python3 classify.py report "${categories[@]}"
else
  python3 classify.py report
fi
status=$?
set -e
cat "$REPORT"
exit "$status"
