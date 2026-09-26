# Review of the actual Claude evidence

Eze Favour · DMI Week 11 · 26 September 2026

Codex performed the cloud work and Dockerfile edits under the learner's delegation. Claude Code used AWS Bedrock Sonnet 4.6 with fixed read-only inspection/audit wrappers and scoped file reads. It could write its local report through the wrapper but could not build, stop, remove, or edit the deployed application. The raw responses are retained as observations, not treated as automatically correct instructions.

## Corrections applied by the operator

- `docker inspect` proves existence, including for a stopped container. Running state and health were separately checked; the final live inspection records `Running=true` and `Health=healthy`.
- Container root is a hardening risk, but a container escape does not invariably grant host root. User namespaces, runtime isolation, capabilities and the particular vulnerability affect the outcome.
- No `HEALTHCHECK` means no Docker health status, not “healthy by default.” Compose does not automatically restart an unhealthy container or route traffic around it. `depends_on: service_healthy` gates startup; runtime recovery needs separate handling.
- A version tag such as `1.0.0` is mutable. This audit accepts it for the assignment's non-`latest` check and explicitly reports the limitation. Base images and the Docker Hub verification pull use digests; local app image IDs are recorded.
- Generic `wget`/port-3000 suggestions in the raw responses do not fit this Node Bookworm image and its port 8080. The operator implemented a Node `fetch` probe against `http://127.0.0.1:8080/health`, then verified real healthy status and UID 1000.
- Counting exposed/published ports is a coarse review signal, not a firewall proof. The database's lack of host bindings and the internal back-tier network were checked separately.

## Sequence and scope disclosure

A Codex audit-script draft existed before the successful Claude planning run. Claude then inspected the live training container and produced its six-check plan; the final script was validated, the real skill ran, Codex changed the Dockerfile outside Claude, and the skill ran again. This is not evidence of a learner-personal “plan before any first draft” sequence. The assignment's request for the learner to edit manually remains an assessor interpretation; delegated work is not relabelled as personal execution.

The intentional baseline used the real EpicBook backend in a separate `epicbook-audit` container with no host port. It omitted USER and HEALTHCHECK and used `latest`, producing 3 PASS / 3 FAIL. The rebuilt training container produced 6 PASS. The public service was not weakened to manufacture a baseline; it was separately audited after its final release. The failed first Claude command was blocked by the guard and is excluded from successful completion evidence. Read-only reporting preserves diagnosis while an independently controlled operator reviews and performs changes.

See [the evidence directory](../evidence/2026-09-26/), [six-check script](docker-audit.sh), [skill](.claude/skills/docker-audit/SKILL.md), and [behavioral tests](test_audit.py).

The final public `week11-epicbook-backend-1` was separately audited at 22:15 UTC: 6 PASS, running and healthy. [Live report](../evidence/2026-09-26/a7-public-stack-audit.txt).
