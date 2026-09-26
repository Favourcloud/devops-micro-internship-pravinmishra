I'll run the audit script now.
---

## Audit results — 2026-09-26 23:14 UTC | epicbook-audit-rerun:1.0.0

**PASS=6 WARN=0 FAIL=0** — all six checks cleared after the rebuild.

---

### Check-by-check explanation

| # | Check | Result | Evidence & meaning |
|---|-------|--------|--------------------|
| 1 | **exists** | PASS | Container `epicbook-audit-rerun` is present and in a running state. The daemon can reach it; no crash-loop or exit. |
| 2 | **user** | PASS | `docker inspect` shows `User: node` — the process is not configured as root. The caveat in the message (`runtime UID should also be verified`) means the script reads the image config; a `USER` directive set to a name only confirms intent, not that the name resolves to a non-zero UID inside the container at exec time. |
| 3 | **healthcheck** | PASS | An effective `HEALTHCHECK` instruction is present in the image. The caveat (`readiness is a separate observation`) is correct: a configured probe does not prove the container is currently healthy — it only means the daemon will run the probe periodically. |
| 4 | **image** | PASS | Tag `epicbook-audit-rerun:1.0.0` is a versioned string, not `latest`. The note `(mutable; digest preferred)` stands — a tag can be re-pushed over the same name, so a SHA-256 digest (`@sha256:…`) is the only immutable reference. |
| 5 | **privileged** | PASS | `docker inspect` confirms `Privileged: false`. The container cannot access host devices or bypass kernel namespace isolation. |
| 6 | **ports** | PASS | 1 declared port, 0 published. The service exposes a port internally but does not bind it to a host interface — correct isolation for a training container. |

---

### Comparison with the previous root/no-healthcheck/latest baseline

| Check | Baseline | Rebuilt |
|-------|----------|---------|
| user | **FAIL** — root | PASS — `node` |
| healthcheck | **FAIL** — none | PASS — probe configured |
| image tag | **WARN** — `latest` | PASS — `1.0.0` |
| privileged, ports, exists | PASS | PASS (unchanged) |

Three prior findings are resolved. No regressions introduced.

---

### Remaining limits (~80 words)

1. **UID resolution not confirmed.** The `user` check reads image metadata; actual runtime UID inside the container is not verified. If `node` maps to UID 0 in `/etc/passwd`, the PASS is misleading.
2. **Tag mutability.** `1.0.0` is a better habit than `latest` but is still re-pushable. Pin to a digest for a reproducible build.
3. **Health probe not observed.** PASS only means the instruction exists; probe exit code and interval behavior are unconfirmed.
4. **Scope is six checks.** Capabilities (`--cap-drop ALL`), read-only filesystem, seccomp/AppArmor profiles, and secret handling are outside this audit's coverage.
