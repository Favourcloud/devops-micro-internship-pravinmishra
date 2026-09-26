# Logging and observability

The reverse proxy writes structured JSON request lines into `./logs/nginx/access.log`, a bind mount owned by its non-root runtime UID. Error output goes to the adjacent error log. Frontend and backend emit JSON to stdout with service, method, path, status and duration. They do not log cookies, credentials or request bodies. Docker's JSON-file logging for each Compose service rotates at 10 MB across three files. The engine default for other lab containers uses its local rotating driver.

Use `docker compose logs --tail 50 frontend backend` to inspect application errors and `docker compose exec -T --interactive=false reverse-proxy tail /var/log/nginx/access.log` for proxy traffic. Healthchecks provide dependency status but are not a monitoring/alerting service. Nginx bind-mounted logs need host rotation in a sustained production deployment; the runbook calls for a seven-day retention and reload after rotation. No external alerting integration is claimed.

The separate bind-mount exercise proved that the Nginx log files and hashes remained after the container was removed. The named-volume exercise demonstrated immediate writer-to-reader updates and persistence after both containers were removed; the reader mount was confirmed read-only.

[Actual live JSON log capture](../../evidence/2026-09-26/a6-json-logs.txt), recorded at 22:15 UTC after access was restored. Client addresses are omitted from public proxy output.
