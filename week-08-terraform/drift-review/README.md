# Week 08 Assignment 06 — local drift/policy reviewer

**Student: Eze Favour. Status: the earlier implementation and 14 screenshots were merged in PR #2; subsequent enrollment/continuation updates remain on the working branch. No LinkedIn/Medium publication is claimed.**

[PR #2](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/pull/2) was merged by GitHub Copilot with explicit user approval at **2026-09-16 11:13:58 UTC**, producing commit `d244042`. Enrollment setup commit `976212b` was pushed afterward and is **not part of that merged PR**. This continuation does not merge subsequent changes. Git merge approval is not human approval of the Terraform resolution.

The [actual operational record](reports/live/operations.json) verifies a real baseline, an **unapplied** public-SSH configuration proposal, a clean technical reset, and deletion of only the newly created VPC/security group. Terraform/checker exits were 0/2/0; AWS cleanup verification at 18:25:59Z found empty states/inventory and exact-resource `NotFound` results. GitHub Copilot executed separately authorized operations, not Claude or a manually operating human. The user explicitly confirmed that [human resolution approval remains pending](reports/live/human-resolution.json); autonomous cleanup and general continuation permission do not complete that requirement. Previous fixture reports remain synthetic. [Claude runtime attempts](reports/live/claude-runtime.json) are blocked by Marketplace enrollment authorization: no successful review or hook execution is claimed. Earlier coursework and personal settings were unchanged by the isolated lab. Publication remains pending.

The [16 September enrollment setup and continuation record](enrollment-proposal/SETUP-20260916.md) distinguishes the earlier verified IAM setup from the current authentication blocker: the required local enrollment profile is absent, and MFA completion/live enrollment remain unverified. The reviewed access window ends at **13:30 UTC (14:30 Lagos) on 16 September**; an expired window requires a newly reviewed proposal, not a silent extension.

- [Assignment submission](../assignment-06-ai-assisted-terraform-drift-and-policy-review.md)
- [Seven-section summary](drift-review-summary.md)
- [Context/safety rules](CLAUDE.md)
- [Checker](AI%20Assignment/tf-drift-check.sh), [schema](lib/schema.jq), [ingress policy](lib/ingress.jq), [private evidence helper](lib/evidence.py)
- [Manual Skill](.claude/skills/tf-drift-review/SKILL.md), [isolated hook configuration](.claude/settings.json), [hook implementation](.claude/hooks/review_gate.py)
- [Detected fixture report](reports/drift-detected-report.txt), [resolved fixture report](reports/resolved-report.txt), [local validation evidence](reports/local-validation.json)
- Actual live reports: [baseline](reports/live/baseline-report.txt), [unapplied proposal](reports/live/drift-detected-report.txt), [technical reset](reports/live/resolved-report.txt); [sanitized baseline execution output](reports/live/baseline-execution.txt)

## Genuine local screenshots

**14 genuine images** were captured on 15 September 2026 in an isolated **Visual Studio Code 1.137.0** profile, with Eze Favour visible in each assignment window. Native application ownership was verified as `com.microsoft.VSCode`, not Cursor. Only the task window was captured; the PNGs are unmodified. [Provenance](screenshots/manifest.json) records capture timestamps, image/source SHA256 hashes, source scope and actual terminal commands. Native local OCR and image inspection were used; no remote OCR service or cloud access was needed for capture.

| Screenshot | Evidence / completion boundary |
| --- | --- |
| [1](screenshots/screenshot-01-clean-plan.png) | Actual historical clean-plan output, displayed as a sanitized editor export; not a terminal rerun |
| [2](screenshots/screenshot-02-workspace.png) | Actual workspace with `AI Assignment/`, `reports/` and prepared Terraform projects; not deployment evidence |
| [3](screenshots/screenshot-03-context.png) | Current `CLAUDE.md` and four sections; genuinely recaptured after the operational/approval edits |
| [4](screenshots/screenshot-04-variables-checks.png) | Bash variables and `checks` array |
| [5](screenshots/screenshot-05-policy-checks.png) | Both check functions and relevant jq ingress logic in split view |
| [6](screenshots/screenshot-06-validation-permissions.png) | Actual terminal `bash -n` exit 0, executable permissions and source hash |
| [7](screenshots/screenshot-07-healthy-baseline.png) | Actual historical LIVE HEALTHY report, timestamp and plan hash in the editor |
| [8](screenshots/screenshot-08-baseline-exit.png) | Actual recorded checker subprocess exit 0 in a labeled historical editor export, not a shell rerun |
| [9](screenshots/screenshot-09-skill-configuration.png) | Current Skill frontmatter/tools/safety rules; genuinely recaptured, configuration only |
| 10 — PENDING | Successful clean Claude Skill review does not exist |
| [11](screenshots/screenshot-11-unapplied-proposal.png) | Public input example copied byte-identically for actual planning; NEVER APPLY; not out-of-band drift |
| 12 — PENDING | Successful Claude risk analysis does not exist |
| [13](screenshots/screenshot-13-live-detected-report.png) | Actual historical LIVE FAIL report: one unsafe ingress finding, zero refresh drift |
| [14](screenshots/screenshot-14-hook-configuration.png) | `PreToolUse` configuration, not runtime loading/enforcement |
| 15 — PENDING | Actual Claude runtime hook denial does not exist |
| 16 — PENDING | Genuine human resolution approval remains outstanding |
| 17 — PENDING | Successful final Claude review does not exist |
| [18](screenshots/screenshot-18-saved-reports.png) | Actual Bash directory listings; synthetic parent reports distinguished from historical live records |
| [19](screenshots/screenshot-19-summary.png) | Current seven-section summary, explicitly recording pending requirements rather than a completed loop |

For screenshots 6/18, `ls` options `-g -o` omit local owner/group names, not command results. Screenshot 18 source-hashes only the four required detected/reset reports; other entry metadata describes the capture time, before final validation regeneration. A listing does not prove file contents. Screenshots 1/8 omit raw refresh identifiers and replace the private plan path with `[PRIVATE PLAN PATH]` **in the text export before display**, not in image pixels. Screenshots 1/7/8/13 are historical editor exports of genuine results, not live terminal captures or current-state claims. None establishes Claude execution or human approval. Slots **10/12/15/16/17**, plus the LinkedIn publication/URL/screenshot, remain pending. No synthetic live evidence, human approval or completed loop was fabricated.

## Terraform preparation and current access blockers

The [sanitized preflight record](reports/live-preflight.json) is **read-only access evidence, not a deployment report**. Both prepared projects passed `terraform fmt -check` and `terraform validate -json` with Terraform 1.13.5 and the pinned AWS provider 6.64.0. Validation ran against byte-identical source/lock files in the existing private initialized prototypes; no provider binaries, state, account bindings or credentials are committed.

- [Network project](terraform/network/main.tf): one isolated VPC, with no subnet, gateway, public IP, compute instance, endpoint or workload.
- [Review project](terraform/security-group/main.tf): one unattached security group with empty ingress and egress by default. The `test_public_ssh` switch is **for an unapplied plan only**. Never apply with it enabled.
- These are deliberately separate Terraform roots/states. The existing checker supports security-group ingress, not VPC policy; review the entire security-group plan without filtering resources to force HEALTHY. A healthy result cannot certify the support VPC, AWS-created default network objects or the account's overall security posture.
- Both providers require the explicit `dmi-week8` profile, `ap-south-1`, a private verified `expected_account_id`, and the fixed `DmiLab` ownership tag. The security-group project additionally requires the private ID of the dedicated lab VPC. Never substitute an earlier assignment's VPC or state.

**Verified:** the profile authenticates as the intended non-root IAM user. Read-only VPC/security-group checks succeed. `CreateVpc --dry-run` returns `DryRunOperation` with the exact proposed tags; the untagged request is denied. No resources matched `DmiLab=dmi-week8*` in the selected account/region at the recorded time; this is not an account-wide inventory.

**Subsequent verified progress (15 September 2026):** scoped creation/cleanup policies and simulations were reviewed, then fresh non-root access and empty lab-tagged inventory were verified. After explicit user approval, GitHub Copilot applied reviewed saved create plans. Both roots produced genuine no-change baselines. Actual-resource DeleteVpc/DeleteSecurityGroup dry-runs established permission only; later real deletion applies and empty state/inventory checks established **completed cleanup**. The SSH proposal changed only a temporary configuration input, never the deployed ingress. A supplementary DescribeSubnets check was denied; no permission expansion occurred, and the exact VPC deletion was subsequently verified. The original preflight remains historical, not rewritten. See [operations](reports/live/operations.json) for timestamps and hashes.

Claude Code's earlier tool-free connection through restricted Bedrock Haiku (`global.anthropic.claude-haiku-4-5-20251001-v1:0`, origin ap-south-1, global routing) returned `BEDROCK_CONNECTION_OK`: 120 input/10 output tokens, reported $0.00017. The user separately approved up to **$0.50 additional usage**. Subsequent attempts found an unknown Skill, then fixed discovery, but hit HTTP 403 Marketplace enrollment authorization. No model review, Read call or runtime hook event succeeded. Additional reported cost is $0; **$0.18 is reserved for incomplete usage records, not verified charges**; $0.32 remains unreserved. Stop inference retries until access is restored. A CLI threshold is not an AWS account cap. OmniRoute stays stopped and personal settings unchanged.

[AWS documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html) explains that initial invocations can temporarily succeed during automatic enrollment (up to 15 minutes), then fail if prerequisites are missing. An authorized administrator must complete the chosen model's one-time Marketplace enrollment, valid-payment and Anthropic use-case prerequisites. After enrollment, the restricted inference role does **not** need Marketplace permissions. Do not broaden that role, use root, switch models or resubmit billed tests as a workaround. The exact missing prerequisite is not independently verified. Account credentials/MFA and license acceptance belong with the authorized human.

The [Bedrock access continuation runbook](BEDROCK_ACCESS.md) records the latest read-only identity/tooling checks and the exact administrator handoff. The available standard profiles did not establish non-root administrator access, and AWS CLI 2.26.1 predates the documented model-availability commands. No new inference or provisioning was performed during those checks; all five pending screenshot slots and the budget reservations remain unchanged.

Keep runtime copies, initialization data, state, private variables and raw evidence inside ignored `.review-data/`. Never apply the public-SSH proposal. No instance, NAT gateway, public IP, endpoint or paid workload component was created; expected resource-type charges were $0, not an audited account-billing result. The VPC's AWS-created defaults were outside the checker's policy scope. Both approved lab resources are now deleted. Recreating them later requires a new reviewed plan and authorization; existing reports are historical and must not be relabeled fresh.

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

## Human-authorized live evidence gathering — separate from Claude

A real clean baseline is now recorded separately from local synthetic validation. The manual Skill/hook intentionally does **not** allow live planning; it permits only reading the three named sanitized live reports. The hook emits factual inspection context without overriding normal permissions.

Only an independently authorized operator or agent, outside Claude, may run the following command against a specifically reviewed, already initialized Terraform project. Verify code, provider/data-source binaries (including external programs), backend, selected workspace, variable sources and credentials first. Use read-only credentials where possible; planning may refresh remote state, obtain locks, read remote APIs and execute provider/data-source code. This is not general sandboxing, nor an assurance that every provider has zero side effects.

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

The configuration is scoped to **this nested project**, not root `.claude/settings.json`. Actual bounded attempts used the isolated Bedrock environment, an explicit copy of this hook configuration with its path bound to the lab, no external MCP servers, `dontAsk` permissions and no Terraform executable/configuration/state in Claude's working context. Empty setting sources initially prevented Skill discovery. A byte-identical copy of only this Skill in a fresh task-local Claude config, with only that controlled user setting source enabled, fixed discovery. This is **isolated registration, not proof of normal project auto-discovery**. API authentication failed before any Read/tool/hook event, so effective hook execution remains unverified. Root/personal settings were not enabled as a shortcut.

After an administrator restores model access, use bounded runs within the remaining approved budget. Verify actual hook lifecycle events and a safe denial, not merely init metadata, a model refusal or a JSON unit test. Keep Terraform unavailable, the cwd free of configuration/state, ordinary permissions restrictive, and the process identity Bedrock-only for any negative control. No apply/destroy permission may be granted to demonstrate the block.

Official schema references checked during implementation:

- [Claude Code Skills](https://code.claude.com/docs/en/skills): `disable-model-invocation: true` and `allowed-tools: Bash Read Grep`.
- [Claude Code Hooks](https://code.claude.com/docs/en/hooks): `hooks.PreToolUse[]`, wildcard matcher, command hook exec-form `command`/`args`, JSON stdin, exit 0 to continue normal permission flow and exit 2 to block. Use a current version supporting exec-form args; verify rather than assuming older installations support it.

`noWrite` is an explicit body instruction, **not an unsupported YAML field**. Allowed tools are not a Bash sandbox. The hook applies an exact finite command allowlist, not a broad regex or general shell parser. Read/Grep paths are confined to selected review files/directories. Unknown tools, arbitrary shell commands, alternate whitespace, wrappers, chaining, pipes, redirects, substitutions, environment assignments, unexpected Bash input options and background execution are rejected without evaluating or normalizing the command. Approved Bash commands only inspect fixed reports/script syntax or run the fixture checker to one new ignored report.

The hook consults `.review-data/current-report.txt` for its denial explanation. A current FAIL produces a FAIL reason; missing, malformed, stale (>15 minutes), future-dated or fixture reports never authorize anything. **Apply, destroy and auto-approve remain denied even with a fresh LIVE HEALTHY report.** Inspecting a stale report is allowed as historical inspection, not evidence of present health. Allowed tools return 0 without a permission override, leaving normal Claude permission checks in place.

This guard assumes trusted source files/interpreters/PATH and a correctly loaded synchronous hook. It is not an OS sandbox, an organizational policy engine, a report signature or control over human terminals. It does not make inherited settings, disabled hooks, malicious executable replacement, shell startup files, filesystem races or actions outside Claude safe. Human infrastructure actions belong outside the AI workflow and require independent review and authorization.

## Validation, source parity and pending completion

Run `python3.13 tests/run_validation.py --report NEW_PATH` to regenerate counts, source hashes, fixture results, screenshot inventory and limitations. The tracked [validation record](reports/local-validation.json) is generated, not hand-written test evidence. It hashes public source/fixtures/docs/sanitized reports, accepted screenshots and their manifest, and the assignment submission; it excludes itself, private runtime data, state, variables and provider directories. Tests check PNG/image/source hashes, correct attachments, pending placeholders, live-record consistency, explicit pending human approval, real-vs-reserved model costs and Git exclusions. They do **not** repeat AWS operations or Claude requests. Hashes are integrity checks, not signed attestations. Prior validation and captures remain in Git history.

[Source metadata](tests/assignment-source.json) records the pinned assignment commit `9b394ef8efecd7db1f582995a03665f6f8afc2a4`, upstream blob `2c00e004853ae2eb146928eb86d19459b538be1b` (14,111 bytes), and original local blob `921e3a543890792187fd0e502b84759e09426dd0` (14,120 bytes). The only original text difference was the subtitle's `Cohort 3`. Tests retain all required headings/questions, all checklist items, all 19 numbered screenshot sections with their accepted attachments or explicit pending placeholders, and the LinkedIn screenshot placeholder.

Pending: administrator-restored model access; actual Claude clean/risk/final Skill reviews and safe runtime hook denial (screenshots **10, 12, 15, 17**); genuine human resolution approval (**16**); a properly ordered review-before-resolution loop; separately authorized LinkedIn publication/URL/screenshot. The real baseline/proposal/technical reset and cleanup are verified, but general continuation permission must not be reinterpreted as personal review or resolution approval. Required filenames and Copilot explanations do not substitute for Claude reasoning. No merge, Medium publication or LinkedIn publication is authorized.
