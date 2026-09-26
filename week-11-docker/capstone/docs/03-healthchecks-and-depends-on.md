# Healthchecks and startup order

The MySQL healthcheck runs an authenticated `SELECT 1` using its application account. The backend's `/health` checks a real database connection and returns 503 when the database cannot be reached. The frontend's `/health` checks whether its HTTP service responds, while its page routes handle dependency failures explicitly. Nginx has a local HTTP probe. Startup uses `depends_on: condition: service_healthy` in the order database, backend, frontend, reverse proxy.

App probes run every ten seconds, allow a startup period, and have bounded timeouts. The actual deployment used `docker compose up -d --wait`, followed by inspection of all four healthy states. Restart policies recover an exited process. **Compose does not automatically restart a merely unhealthy container or continually enforce startup dependencies.** A readiness status is therefore an observation, not high availability. Fault tests deliberately stopped the backend and the database and verified HTTP responses and recovery.

See [deployment evidence](../../evidence/2026-09-26/a6-deploy.txt) and [recovery](../../evidence/2026-09-26/a6-recovery.txt).
