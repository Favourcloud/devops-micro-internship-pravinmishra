# Ordered Docker hardening audit rerun

Eze Favour · 27 September 2026, Africa/Lagos · events below use UTC.

The new workspace began with only `CLAUDE.md` and the inspection wrapper. The earlier attempt is preserved in [the original review](../OPERATOR-REVIEW.md); this new attempt corrects its plan-before-script sequence and replaces A7’s numbered evidence with direct editor/terminal captures.

| Step | Recorded UTC evidence |
|---|---|
| Claude plan started | 2026-09-26T23:02:19.429084+00:00 |
| Plan finished, audit script still absent | 2026-09-26T23:02:55.408902+00:00 |
| New script created after plan | [creation record](../../evidence/2026-09-27-ordered-rerun/script-created.json) |
| First live audit | 2026-09-26T23:10:35Z; 3 PASS, 3 FAIL |
| Skill created after first audit | 2026-09-26T23:10:56.464631+00:00 |
| Baseline skill finished | 2026-09-26T23:11:55.528360+00:00 |
| Operator rebuilt the isolated training container | 2026-09-26T23:13:35.581498+00:00 |
| Final skill finished | 2026-09-26T23:14:39.105721+00:00; 6 PASS |

[All dated records](../../evidence/2026-09-27-ordered-rerun/) · [assignment and direct screenshots](../../assignment-07-ai-assisted-docker-container-hardening-audit.md).

## Reviewed corrections to Claude’s advice

The raw responses are kept unchanged. The operator corrected these points before relying on them:

- Pinning `FROM` alone does not repair the runtime `Config.Image` tag. The operator retained the pinned Node 22 Bookworm base and launched the rebuilt image as `epicbook-audit-rerun:1.0.0`; a release tag remains mutable.
- The existing `node` user was used instead of introducing Claude’s generic `appuser`. The actual runtime UID was separately verified as 1000.
- The implemented Node `fetch` probe uses the app’s `/health` endpoint on port 8080. Actual `healthy` status was verified outside the read-only Claude session.
- The final response’s comparison incorrectly labels the original image result WARN. The actual baseline report says FAIL. The authoritative change is **3 PASS / 3 FAIL → 6 PASS / 0 FAIL**.
- Running once does not prove there was never a crash loop; disabling privileged mode alone does not prove immunity to host/device access or namespace escape. A missing healthcheck does not prevent Docker from observing an exited main process; it prevents application-level probe status. No broad security guarantee follows from these six checks.
- The plan’s “PARTIAL PASS” wording was normalized to the specified PASS/WARN/FAIL report contract. One declared internal port and zero host bindings pass the narrow port-count check.

## Source and reproducibility

The [script](docker-audit.sh) uses six named check functions and read-only Docker inspect calls. It writes a local report; exit code 0 means the audit completed, so inspect the report’s failure count. [Tests](test_audit.py) cover hardening failures, stopped or missing containers, disabled probes, registry-port/tag ambiguity, missing image metadata, null/multiple host bindings, invalid names and command-guard bypass attempts. All 15 passed in [the recorded test run](../../evidence/2026-09-27-ordered-rerun/audit-tests.txt).

For a new ordered rerun, start a fresh directory containing only [CLAUDE.md](CLAUDE.md) and [inspect-container.sh](inspect-container.sh); configure `DMI_AUDIT_SSH_CONFIG` for an authorized host alias. Run the read-only plan first. Only afterwards create the audit script and fixed wrapper, validate and run it, then install the [skill](.claude/skills/docker-audit/SKILL.md). Configure [guard.py](guard.py) as a PreToolUse hook with `DMI_AUDIT_ROOT` set to the workspace, and allow only Read, the two fixed Bash wrappers and Skill(docker-audit). Use an existing AWS Bedrock profile with Claude Code; credentials are not part of this submission. The operator separately reviews and performs the [rebuild commands](../../evidence/2026-09-27-ordered-rerun/operator-rebuild-command.sh). Do not point the training workflow at an unrelated or production container.

The three actual Bedrock sessions cost approximately $0.179826 before taxes. Build layers were reused where Docker reported CACHED; cached execution is not described as a clean uncached build.

## Execution and assessment boundary

Codex performed implementation, terminal actions and Dockerfile edits under the learner’s authorization. Claude could inspect and recommend; its guard did not allow source edits or container lifecycle commands. This is an actual ordered workflow, but it is not evidence that the learner personally typed the commands or manually edited files. DMI alone determines whether delegated work satisfies that wording and awards grades.

The public EpicBook stack remained healthy throughout the isolated training rerun and separately passed all six checks. Existing demos remain online as requested. Training copies publish no external host ports. The shared-volume browser rerun used a separate volume and loopback-only listener reached by SSH; it preserved the original data.
