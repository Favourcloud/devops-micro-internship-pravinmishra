Running the inspection script now.
---

## Six-Check Audit Plan — EpicBook Training Container (`/epicbook-audit-rerun`)

**Observed baseline:** container is running, image tag `epicbook-audit:latest`, no User field set, no Healthcheck configured, not privileged, port 8080/tcp exposed but not published to the host.

---

### Check 1 — Existence and Running State
Verify the container exists AND is in `Running: true` state. These are distinct: a container can exist (stopped/exited) without running. **Expected finding:** pass — confirmed running above.

### Check 2 — Root User
Inspect the `User` field from `docker inspect`. An empty string means the image defaults to root (UID 0). **Expected finding:** FAIL — `User` is `""`, meaning the process runs as root. Recommendation: add `USER` directive in Dockerfile.

### Check 3 — Effective HEALTHCHECK
Distinguish between a HEALTHCHECK instruction present in the image config versus the actual runtime health status. `Healthcheck: null` means no check is configured at all — there is nothing to evaluate at runtime. **Expected finding:** FAIL — `null`, no healthcheck defined. Recommendation: add a `HEALTHCHECK` instruction.

### Check 4 — Versioned Image or Immutable Digest
`epicbook-audit:latest` is a mutable floating tag; it provides no reproducibility guarantee. An immutable reference requires a `sha256:` digest (`image@sha256:…`). **Expected finding:** FAIL — tag only, no digest pinning. Recommendation: pin to a digest in the Dockerfile `FROM` line.

### Check 5 — Privileged Mode
Inspect `Privileged` flag. Privileged mode grants full host kernel capability access and is a critical risk. **Expected finding:** PASS — `Privileged: false`.

### Check 6 — Exposed vs. Published Ports
Distinguish `ExposedPorts` (declared in image, internal only) from `PublishedPorts` (bound to host interface, externally reachable). **Expected finding:** PARTIAL PASS — port 8080/tcp is exposed but `PublishedPorts` is `{}`, so no host binding exists. Acceptable for an isolated training container; flag for review if host access is unintended.

---

**Report semantics:** each check emits PASS / FAIL / WARN with the raw observed value and a single concrete remediation. Checks 2, 3, and 4 are expected FAIL; checks 5 and 6 PASS; check 1 PASS.
