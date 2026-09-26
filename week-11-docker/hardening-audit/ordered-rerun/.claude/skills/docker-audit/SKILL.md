---
name: docker-audit
description: Gather six fresh Docker hardening checks and recommend fixes.
allowed-tools: Read, Bash(./run-audit.sh)
---
# Eze Favour — read-only Docker audit skill

1. Execute exactly `./run-audit.sh` once.
2. Read `reports/docker-hardening-report.txt` from that run.
3. Explain each PASS, WARN and FAIL using its actual evidence.
4. Recommend exact Dockerfile fixes for USER and HEALTHCHECK,
   and a versioned runtime image tag or immutable digest.

Never edit source or run build, stop, remove, privileged or
cleanup commands. An operator reviews and implements changes
outside this Claude session. A configured probe is not proof
of current health; a versioned tag can still be mutable.
