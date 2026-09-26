#!/usr/bin/env bash
set -euo pipefail
: "${DMI_AUDIT_SSH_CONFIG:?Set the operator-controlled SSH config}"
ssh -F "$DMI_AUDIT_SSH_CONFIG" w11-epicbook 'docker inspect epicbook-audit --format '\''{"Name":{{json .Name}},"Image":{{json .Config.Image}},"User":{{json .Config.User}},"Healthcheck":{{json .Config.Healthcheck}},"Privileged":{{json .HostConfig.Privileged}},"Ports":{{json .HostConfig.PortBindings}}}'\'''
