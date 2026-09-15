# Week 08 Assignment 06 — local drift/policy reviewer

**Student: Eze Favour. Status: local branch-only implementation; not merged or published.**

This isolated project implements the assignment's local artifacts, not its operational completion. Six genuine local editor/terminal screenshots are attached; no real Terraform plan, cloud request, apply, destroy, Claude Skill invocation, or LinkedIn publication was performed. There is no Terraform scaffold or paid resource here. The existing worktree's other labs and active root Claude settings are unchanged by this project.

- [Assignment submission](../assignment-06-ai-assisted-terraform-drift-and-policy-review.md)
- [Seven-section summary](drift-review-summary.md)
- [Context/safety rules](CLAUDE.md)
- [Checker](AI%20Assignment/tf-drift-check.sh), [schema](lib/schema.jq), [ingress policy](lib/ingress.jq), [private evidence helper](lib/evidence.py)
- [Manual Skill](.claude/skills/tf-drift-review/SKILL.md), [isolated hook configuration](.claude/settings.json), [hook implementation](.claude/hooks/review_gate.py)
- [Detected fixture report](reports/drift-detected-report.txt), [resolved fixture report](reports/resolved-report.txt), [local validation evidence](reports/local-validation.json)

## Genuine local screenshots

Captured on 15 September 2026 in an isolated **Visual Studio Code 1.137.0** profile, with Eze Favour visible in each assignment window. Only that window was captured; the PNGs are unmodified. [Provenance](screenshots/manifest.json) records capture-processing timestamps, image/source SHA256 hashes and the actual terminal commands. Native local OCR and image inspection were used; no remote OCR service or cloud access was needed.

| Screenshot | Evidence |
| --- | --- |
| [3](screenshots/screenshot-03-context.png) | `CLAUDE.md` and all four context/safety sections |
| [4](screenshots/screenshot-04-variables-checks.png) | Bash variables and `checks` array |
| [5](screenshots/screenshot-05-policy-checks.png) | Both check functions and relevant jq ingress logic in split view |
| [6](screenshots/screenshot-06-validation-permissions.png) | Actual `bash -n` exit 0, executable permissions and source hash |
| [9](screenshots/screenshot-09-skill-configuration.png) | Skill frontmatter, allowed tools and safety rules |
| [14](screenshots/screenshot-14-hook-configuration.png) | `PreToolUse` configuration, not a runtime invocation |

For screenshot 6, `ls -l -g -o` omits local owner/group names while preserving the real permissions output. These six images do not establish a live baseline, a Claude session, a successful hook load or a human-applied resolution. Screenshots **1, 2, 7, 8, 10, 11, 12, 13, 15, 16, 17, 18 and 19**, plus the LinkedIn publication screenshot, remain pending. No placeholder was replaced with synthetic live evidence.

## Reproduce without cloud access

Prerequisites: Bash, `jq`, Python 3.13 standard library. No package installation, Terraform executable, provider credentials, network, framework, JavaScript, or build step is needed for local validation. `jq` and Python 3.13 were already available.

From the repository root:

```bash
cd week-08-terraform/drift-review
bash -n "AI Assignment/tf-drift-check.sh"
python3.13 -m unittest discover -s tests -v
```

The suite runs the checker as a subprocess, feeds JSON to the hook, and tests the guarded live command path **only with a fake Terraform executable created inside ignored project-local test directories**. No actual infrastructure commands are attempted, including blocked applies. The apply strings in tests are JSON data consumed by the hook, never executed.

To generate fresh demonstration reports without overwriting the committed evidence:

```bash
mkdir -p .review-data
bash "AI Assignment/tf-drift-check.sh" --fixture fixtures/detected.json --report .review-data/detected-report.txt
# Expected checker exit 2: fixture FAIL. Capture $? immediately in your shell.
bash "AI Assignment/tf-drift-check.sh" --fixture fixtures/clean.json --report .review-data/resolved-report.txt
# Expected checker exit 0: fixture HEALTHY in the limited synthetic scope.
python3.13 tests/run_validation.py --report .review-data/local-validation.json
```

Use a **new report filename** on every rerun, or deliberately archive old local evidence yourself. Existing files and symlinks are rejected; no `--force` flag exists. Parent directories must already exist. Paths containing spaces or shell metacharacters are passed literally when quoted. Checker report exit codes differ from Terraform's:

| Checker exit | Report status | Meaning |
| --- | --- | --- |
| 0 | HEALTHY | No pending changes/findings/unknowns in the supported input scope; fixture results are not actual infrastructure health |
| 1 | WARN | Non-destructive/resource/output/refresh changes, public web exception, or incomplete/unsupported evidence needs review |
| 2 | FAIL | Delete/replacement or unsafe public ingress |
| 3 | ERROR or no new report | Dependency, input, schema, plan/show, output, or evidence-lifecycle failure; never approval |

All results are read-only review outcomes; **none authorize mutation**. An error before report initialization prints a fixed diagnostic and creates no report. Later errors publish a sanitized ERROR report if possible. Final-report publication is an atomic, no-clobber hard link; failed publication cannot replace old evidence.

## Fixtures, scope and policy

[clean.json](fixtures/clean.json) describes a fictional AWS security group with empty ingress and no pending changes. [detected.json](fixtures/detected.json) adds an `update` with inbound TCP/22 from `0.0.0.0/0`. [empty.json](fixtures/empty.json) represents a valid empty Terraform project plan. The resolved demonstration reuses the clean fixture; no Terraform file or real environment was changed or repaired. Tests derive additional explicit synthetic cases in private, discarded directories.

The Bash `checks` array invokes `check_destructive_actions` and `check_open_ingress`, each using `jq`. A standard-library helper validates JSON syntax/duplicate keys and classifies CIDRs with `ipaddress`; jq validates schema and makes the policy decisions.

- Supported JSON format versions: 1.0–1.2. Missing root `planned_values`, malformed changes/actions, duplicate keys, invalid JSON constants and unknown action lists fail ERROR. Optional Terraform arrays may be absent in an empty/no-change plan, but explicit null/wrong types are invalid. No-op before/after values must agree.
- Every `delete` in `resource_changes` or `resource_drift` is FAIL, including both replacement orders. No-op and empty plans are distinguished from create/update/read, output-only and refresh-only changes.
- Inline `aws_security_group.ingress`, `aws_security_group_rule` with `type: ingress`, and `aws_vpc_security_group_ingress_rule` are inspected in changes, refresh observations and nested planned values. Equivalent type/provider/value representations are deduplicated; counts describe findings, not billing-resource totals.
- Restricted CIDRs are **only RFC1918 IPv4 or IPv6 ULA**. Other valid CIDRs, including narrower globally routed ranges, `/0`, split `/1`, noncanonical addresses normalized for classification, and reserved ranges, are conservatively treated as public. Unparseable or wrong-family CIDRs are unknown, never safe. Known group/self references count as restricted, but transitive group membership is not analyzed. Prefix-list sources are unknown because their membership is unavailable offline.
- Public TCP exactly port 80 or exactly 443 is **WARN**, not HEALTHY: a human must establish intentional web exposure, TLS/application controls and least privilege. Ranges covering both web ports and other ports are FAIL. Public SSH, RDP, database ports, UDP, ICMP and all-protocol rules are FAIL. Invalid ports/protocols/source combinations are unknown/WARN (or ERROR for malformed structure), never unconditional approval.
- Unknown values, deferred/incomplete plans and non-passing Terraform checks are WARN; top-level errored plans are ERROR. Unsupported resources/providers are WARN even for a no-op, so this policy cannot certify unrelated infrastructure. Security-group egress is explicitly outside scope. IAM, storage encryption, ACLs, reachability, organizational exceptions and full cloud posture are not assessed. A HEALTHY empty plan is valid but says nothing about untracked resources.

The report exposes only fixed descriptions, counts, mode, UTC time and source SHA256. It deliberately omits resource addresses, CIDRs, variables, output values, local paths, account IDs, and provider messages. A hash identifies bytes; it is not an attestation of authenticity, freshness, provider trust, or human approval. Fixture input age is unrestricted because it is an explicit static demonstration. Every run copies input to a new private workspace; previous output is never reused.

## Later human-authorized live evidence gathering — NOT performed

A real clean baseline and remote provider access are not available/authorized for this submission. Do not run this section just to complete local validation. The manual Skill/hook intentionally does **not** allow live mode.

Only a human who has independently authorized a specific trusted, already initialized Terraform project may run the following command in their own terminal. Verify code, provider/data-source binaries (including external programs), backend, selected workspace, variable sources and credentials first. Use read-only credentials where possible; planning may refresh remote state, obtain locks, read remote APIs and execute provider/data-source code. This is not general sandboxing, nor an assurance that every provider has zero side effects.

```bash
# Documentation example only: substitute a reviewed directory and NEW output name.
bash "AI Assignment/tf-drift-check.sh" --live --terraform-dir "/absolute/path/to/trusted-terraform-project" --authorize-live-read-only --report .review-data/human-authorized-review.txt
```

Inside the supplied directory, the only Terraform invocations are:

```text
terraform plan -input=false -no-color -detailed-exitcode -out=<new-private-workspace>/plan.binary
terraform show -json <new-private-workspace>/plan.binary
```

There is no auto-init, apply, destroy, refresh command, backend configuration, workspace switching, var injection or auto-approve. `TF_CLI_ARGS`, `TF_CLI_ARGS_plan`, and `TF_CLI_ARGS_show` overrides are rejected; Terraform debug logging overrides are unset. Other environment/tool resolution is trusted and must be reviewed by the human.

Terraform code **0** means no changes, **1** means a planning error, **2** means changes. Only 0/2 proceed to `show`; other exits, missing binary, failed show, invalid JSON or inconsistent zero/change evidence produce ERROR. Each run gets a fresh private directory and must produce a new binary; a stale saved plan cannot be substituted by this workflow. No pre-existing plan output is accepted in live mode. Live WARN/FAIL reports still require human judgment, not automatic remediation.

`umask 077` protects new artifacts. Raw plan JSON, binary and private logs exist only inside a new `.review-run-*` directory under the explicit report's parent, and cleanup runs on normal exit/error/HUP/INT/TERM. SIGKILL, power loss, disk failures and malicious filesystem races cannot be fully handled; leftover private directories are ignored and a human must remove them securely. Do not place real evidence outside ignored `.review-data/`, and never commit raw plans/logs. Local disk permissions and a hook do not protect against a hostile OS user.

## Hook and manual Skill boundary

The configuration is scoped to **this new nested project**, not the active root `.claude/settings.json`. For a later human-approved Claude session, start in this directory and explicitly select this settings file if your installation resolves project settings at the Git root; confirm the effective `PreToolUse` hook and `${CLAUDE_PROJECT_DIR}` path before using the Skill. Parent/personal/managed settings can also apply and must be reviewed. No Claude runtime execution or settings-load test was performed here.

Official schema references checked during implementation:

- [Claude Code Skills](https://code.claude.com/docs/en/skills): `disable-model-invocation: true` and `allowed-tools: Bash Read Grep`.
- [Claude Code Hooks](https://code.claude.com/docs/en/hooks): `hooks.PreToolUse[]`, wildcard matcher, command hook exec-form `command`/`args`, JSON stdin, exit 0 to continue normal permission flow and exit 2 to block. Use a current version supporting exec-form args; verify rather than assuming older installations support it.

`noWrite` is an explicit body instruction, **not an unsupported YAML field**. Allowed tools are not a Bash sandbox. The hook applies an exact finite command allowlist, not a broad regex or general shell parser. Read/Grep paths are confined to selected review files/directories. Unknown tools, arbitrary shell commands, alternate whitespace, wrappers, chaining, pipes, redirects, substitutions, environment assignments, unexpected Bash input options and background execution are rejected without evaluating or normalizing the command. Approved Bash commands only inspect fixed reports/script syntax or run the fixture checker to one new ignored report.

The hook consults `.review-data/current-report.txt` for its denial explanation. A current FAIL produces a FAIL reason; missing, malformed, stale (>15 minutes), future-dated or fixture reports never authorize anything. **Apply, destroy and auto-approve remain denied even with a fresh LIVE HEALTHY report.** Inspecting a stale report is allowed as historical inspection, not evidence of present health. Allowed tools return 0 without a permission override, leaving normal Claude permission checks in place.

This guard assumes trusted source files/interpreters/PATH and a correctly loaded synchronous hook. It is not an OS sandbox, an organizational policy engine, a report signature or control over human terminals. It does not make inherited settings, disabled hooks, malicious executable replacement, shell startup files, filesystem races or actions outside Claude safe. Human infrastructure actions belong outside the AI workflow and require independent review and authorization.

## Validation, source parity and pending completion

Run `python3.13 tests/run_validation.py --report NEW_PATH` to regenerate sanitized counts, source hashes, fixture results and explicit limitations. The tracked [validation record](reports/local-validation.json) is generated, not hand-written test evidence. It hashes project source/fixtures/docs/reports, all six screenshots and their provenance manifest, and the assignment submission (excluding itself and ignored runtime data); timestamps and runtime durations will differ on rerun. Screenshot regressions check PNG/image hashes, captured source hashes, the six correct attachments and the thirteen remaining numbered placeholders. Hashes are integrity checks, not signed attestations. The original pre-screenshot validation snapshot remains available in Git commit `0fb5b4b`.

[Source metadata](tests/assignment-source.json) records the pinned assignment commit `9b394ef8efecd7db1f582995a03665f6f8afc2a4`, upstream blob `2c00e004853ae2eb146928eb86d19459b538be1b` (14,111 bytes), and original local blob `921e3a543890792187fd0e502b84759e09426dd0` (14,120 bytes). The only original text difference was the subtitle's `Cohort 3`. Tests retain all required headings/questions, all checklist items, all 19 numbered screenshot sections (six actual attachments and thirteen pending placeholders), and the LinkedIn screenshot placeholder.

Pending: authorized real clean baseline and final plan, actual Claude Skill/hook sessions, actual controlled infrastructure/configuration difference and classification, independent human resolution, the remaining 13 numbered screenshots, and LinkedIn post/URL/screenshot. Required report filenames alone do not complete Task 8. GitHub Copilot assisted code, tests and draft answers; that assistance is not evidence of Claude reasoning or a live operational outcome.
