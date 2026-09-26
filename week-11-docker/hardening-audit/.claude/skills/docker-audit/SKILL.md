---
name: docker-audit
description: Gather a fresh six-check Docker hardening report and recommend, but never apply, a Dockerfile fix.
allowed-tools: Read, Bash(./run-audit.sh)
---
Run exactly `./run-audit.sh` once. Read `reports/docker-hardening-report.txt` from that run. Explain every PASS, WARN and FAIL with the evidence provided. Recommend explicit Dockerfile lines such as `USER node` and `HEALTHCHECK`, plus a versioned tag where required. Do not edit any source or execute deployment, rebuild, stop, remove, privileged, or cleanup commands. Report honest failures; do not treat a report file's existence as proof of a passing audit. Keep the distinction between a versioned tag and an immutable digest.
