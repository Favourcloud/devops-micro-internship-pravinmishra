#!/usr/bin/env bash
set -euo pipefail
: "${DMI_AUDIT_SSH_CONFIG:?Set the operator-controlled SSH config}"
umask 077
mkdir -p reports
ssh -F "$DMI_AUDIT_SSH_CONFIG" w11-epicbook 'cd /opt/week11/audit && ./docker-audit.sh epicbook-audit' > reports/docker-hardening-report.txt
cat reports/docker-hardening-report.txt
