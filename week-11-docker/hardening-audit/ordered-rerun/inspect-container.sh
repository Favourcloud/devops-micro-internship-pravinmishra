#!/usr/bin/env bash
set -euo pipefail
: "${DMI_AUDIT_SSH_CONFIG:?Set the operator-controlled SSH config}"
printf 'Eze Favour | Ordered audit planning | UTC %s\n' "$(date -u +%FT%TZ)"
test ! -e docker-audit.sh && echo 'Confirmed: no audit script exists in this new workspace.'
ssh -F "$DMI_AUDIT_SSH_CONFIG" w11-epicbook bash -s <<'REMOTE'
docker inspect epicbook-audit-rerun --format '{"Name":{{json .Name}},"Running":{{json .State.Running}},"Image":{{json .Config.Image}},"User":{{json .Config.User}},"Healthcheck":{{json .Config.Healthcheck}},"Privileged":{{json .HostConfig.Privileged}},"PublishedPorts":{{json .HostConfig.PortBindings}},"ExposedPorts":{{json .Config.ExposedPorts}}}'
REMOTE
