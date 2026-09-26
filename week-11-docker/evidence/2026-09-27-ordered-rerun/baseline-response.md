Running `./run-audit.sh` now.
## Audit results — epicbook-audit-rerun (2026-09-26T23:11:44Z)

**PASS | exists** — Container is present and running. No action needed.

**FAIL | user** — The effective UID inside the container is 0 (root). Any process exploit grants full container privileges. Fix: add a dedicated non-root user.

**FAIL | healthcheck** — No `HEALTHCHECK` instruction is defined in the image. Docker cannot detect a crashed app process; orchestrators and monitoring tools receive no signal. Fix: declare an explicit probe.

**FAIL | image** — The runtime image is tagged `epicbook-audit:latest`. `latest` is mutable; a future `docker pull` can silently swap in a different image layer, breaking reproducibility and auditability.

**PASS | privileged** — `--privileged` is not set. The container does not have host-level device or capability access.

**PASS | ports** — One port is declared internally; zero are published to the host. The attack surface is correctly minimised for this isolated training environment.

---

### Recommended Dockerfile lines (operator implements)

**Non-root user** — add before the final `CMD`/`ENTRYPOINT`:
```dockerfile
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser
```

**Healthcheck on port 8080** — add after `EXPOSE`:
```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD node -e "require('http').get('http://localhost:8080/health', r => process.exit(r.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))"
```

**Versioned image tag** — replace `node:latest` (or whichever base is used) with a pinned, slim variant, e.g.:
```dockerfile
FROM node:20.19.2-slim
```
Pin to a specific patch release and verify against a published digest; re-pin on each deliberate upgrade.

---

3 FAILs, 3 PASSes. The three fixes above address every failing check. An operator should edit the Dockerfile and rebuild outside this session.
