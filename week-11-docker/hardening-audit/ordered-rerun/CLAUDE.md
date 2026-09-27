# Eze Favour — Week 11 Docker hardening rerun

This new workspace is for an ordered, read-only audit of the isolated EpicBook training container. The public EpicBook service must remain unchanged. Codex operates under learner delegation; do not claim personal learner execution.

First execute only `./inspect-container.sh` and propose a six-check audit plan. There is no audit script in this workspace yet. Do not create or edit any file during planning. Later, use the `/docker-audit` skill and exactly `./run-audit.sh` to gather a fresh report and recommend specific corrections.

Never edit Dockerfiles, Compose, audit source or wrappers. Never execute docker build/run/stop/rm/rmi, SSH directly, a general shell, or an alternate wrapper. An independently controlled operator reviews the recommendation, edits the Dockerfile and rebuilds outside Claude. Only the fixed audit wrapper may write its bounded local report after the script exists.
