# Week 08 Assignment 06 — local drift/policy reviewer

**Student: Eze Favour. Status: the genuine clean/risk/final review cycle, human decision, cleanup and all 19 numbered screenshots are verified and present on `main` through PR #3. No manual human Terraform execution or LinkedIn/Medium publication is claimed.**

[PR #2](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/pull/2) was merged by GitHub Copilot with explicit user approval at **2026-09-16 11:13:58 UTC**, producing commit `d244042`. Enrollment setup commit `976212b` and the later continuation were not part of PR #2, but subsequently reached `main` through [PR #3](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/pull/3), merged at **2026-09-16 16:48:27 UTC** (`f05bb7d`). On 17 September, all 19 screenshots on inspected `main` commit `faa96981d6edb4cb3fd67c56a98864f222d59da7` were verified byte-identical to the retained originals. This status correction does not rerun the historical operations, change their source hashes, authorize another merge, or establish whole-week completion. Git merge approval is not human approval of the Terraform resolution.

## Verified 16 September cycle — safe resolution approved

The [current-cycle record](reports/live/cycle-20260916.json) documents separately authorized creation of one dedicated VPC and one closed, unattached security group. Exact new bindings, ownership, empty ingress/egress and absence of attachments were verified. Both baseline plans exited 0; the actual Bash checker returned **LIVE / HEALTHY / 0 at 15:12:53Z**. The proposal checker returned **LIVE / FAIL / 2 at 15:25:59Z**: one proposed update, one unsafe ingress finding, zero refresh drift. Public SSH was supplied **only as a planning-process environment input**, never applied; no persistent override was created. Local states remained unchanged by planning/checking.

Genuine manually invoked `/tf-drift-review` runs completed the [clean review](reports/live/claude-clean-review-20260916.json) and [risk review](reports/live/claude-risk-review-20260916.json). Each had exactly three complete successful Reads, three matching native Read hooks, actual inspection context, exact report timestamp/hash citations and zero API retries. Claude recommended **“Do not apply this configuration.”** It distinguished a configuration proposal from drift and marked SSH/22 as context-inferred; the operator separately verified the actual private TCP/22 plan. The clean response's “human-generated report” attribution is explicitly corrected: **Copilot generated the evidence under user authorization**. A preceding wrong-path clean attempt had three denied Reads and no review; it remains recorded, not disguised as success. Correcting absolute project paths did not weaken the hook or permissions.

The separate [fresh-FAIL native control](reports/live/native-hook-fail-20260916.json), started at **15:30:33Z**, made one actual `Bash` request for `terraform apply -input=false`. The matching native `PreToolUse:Bash` process exited **2**, its actual stderr ended **`report=FAIL`**, and the matching tool result was an error. Terraform did not execute. The actual checker report was copied byte-identically without changing its timestamp. This proves Task 7's runtime scenario independently of the earlier missing-report control and of screenshot completion.

**Personal resolution subsequently approved:** the initial focused question returned user unavailable, and no decision was inferred. The user later replied **“approved”** after the actual public-SSH findings and Claude recommendation had been presented. The [dated decision record](reports/live/human-resolution-20260916.json), recorded at **15:45:45Z**, interprets this narrowly as **rejecting the unapplied public-SSH proposal and retaining empty ingress/egress**. It is not permission to apply public SSH, extend enrollment permissions or increase spending. No persistent override existed to remove. Fresh final plans at **15:46:19–15:47:10Z** returned no-op/0 for both roots; the actual [final checker report](reports/live/resolved-report.txt) returned **LIVE / HEALTHY / 0 at 15:50:12Z**, all counts zero and state unchanged. The [genuine final Claude review](reports/live/claude-final-review-20260916.json), started at **15:51:21Z**, verified those exact bytes through three complete Reads and three matching native hooks, with zero retries. The human owned the resolution decision; Copilot executed the separately authorized operations, not a manually operating human. HEALTHY is limited-scope evidence, not global safety or mutation authorization.

## Preserved history, permissions and budget

The **15 September** [operations record](reports/live/operations.json) documents the earlier baseline, unapplied copied-input proposal, technical reset and cleanup verified at **18:25:59Z**. Those resources were deleted. Canonical baseline/proposal/final reports now belong to the **16 September cycle**; earlier report bytes remain archived privately and in Git history. Its [Claude failures](reports/live/claude-runtime.json) and [user clarification](reports/live/human-resolution.json) remain unchanged dated history. Previous canonical report bytes were preserved privately before the new baseline/proposal reports were promoted. Earlier coursework resources were not targeted. Capture tooling reported an earlier failed launch into shared VS Code storage; its side effects are not yet established, so this continuation does **not** claim that all personal settings were unchanged.

The [enrollment timeline](enrollment-proposal/SETUP-20260916.md) and [sanitized evidence](reports/continuation-20260916.json) verify private MFA authentication, user-triggered SDK offer acceptance at **13:26:22Z**, and independent readiness at **13:27:31Z**. The session expired at **13:29Z** and the unchanged policy window at **13:30Z / 14:30 Lagos**. No renewal, repeat acceptance or identity/access-key removal is claimed. These enrollment results are distinct from the subsequent actual model reviews.

The [first native denial](reports/live/native-hook-denial-20260916.json), at **14:08:21–14:08:34Z**, used a **missing/invalid report**, not FAIL. One implicit HTTP 403 retry occurred inside that invocation; its cause was not established and no operator rerun occurred. Subsequent launches use `CLAUDE_CODE_MAX_RETRIES=0`. Private runner/accounting tests passed **46 normally and 46 under `-O`**. Guarded operator compatibility fixes—owner-controlled AWS directory handling, verified same-inode short temporary paths, and exact Terraform Boolean/string validation—passed **68 normally and 68 under `-O`**; original refusal artifacts were retained.

The user authorized up to **$0.32 of the existing $0.50 additional model allowance**, preserving **$0.18 for unknown historical usage**. Reported additional usage is approximately **$0.141731**; total accounted including that reservation is **$0.321731**, leaving approximately **$0.178269**. The reservation is not a verified charge; the earlier $0.00017 connection test is separate. Neither the CLI threshold nor this ledger is an AWS account spending cap or billing audit. The post-decision final review succeeded; **no further model call is needed**. Exact-plan lab creation and reviewed cleanup had separate approval; public SSH deployment remains forbidden.

- [Assignment submission](../assignment-06-ai-assisted-terraform-drift-and-policy-review.md)
- [Seven-section summary](drift-review-summary.md)
- [Context/safety rules](CLAUDE.md)
- [Checker](AI%20Assignment/tf-drift-check.sh), [schema](lib/schema.jq), [ingress policy](lib/ingress.jq), [private evidence helper](lib/evidence.py)
- [Manual Skill](.claude/skills/tf-drift-review/SKILL.md), [isolated hook configuration](.claude/settings.json), [hook implementation](.claude/hooks/review_gate.py)
- [Detected fixture report](reports/drift-detected-report.txt), [resolved fixture report](reports/resolved-report.txt), [local validation evidence](reports/local-validation.json)
- Actual live reports: [baseline](reports/live/baseline-report.txt), [unapplied proposal](reports/live/drift-detected-report.txt), [technical reset](reports/live/resolved-report.txt); [sanitized baseline execution output](reports/live/baseline-execution.txt)

## Genuine local screenshots

**All 19 genuine numbered images are integrated.** Seven unchanged 15 September images are retained; seven changed-source slots were recaptured and five native-runtime/decision slots added on 16 September. Captures used isolated **Visual Studio Code 1.137.0**, with Eze Favour visible in each assignment window. Native application ownership was verified as `com.microsoft.VSCode`, not Cursor. Only the task window was captured; original PNG pixels are unmodified. [Provenance](screenshots/manifest.json) records capture timestamps, image/source SHA256 hashes, source scope and actual terminal commands. Local native OCR/privacy checks, original-byte hashes and PNG chunk CRCs passed for the new captures. No remote OCR service, model call or cloud operation was needed for capture.

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
| [10](screenshots/screenshot-10-clean-agentic-review.png) | Recorded export of the genuine clean Skill review; not a fresh Claude session |
| [11](screenshots/screenshot-11-unapplied-proposal.png) | Historical copied-input example; the new cycle used the equivalent input only in planning-process environment variables |
| [12](screenshots/screenshot-12-risk-assessment.png) | Recorded genuine risk Skill review: do not apply the proposal |
| [13](screenshots/screenshot-13-live-detected-report.png) | Current-cycle recorded LIVE FAIL report: one unsafe ingress finding, zero refresh drift |
| [14](screenshots/screenshot-14-hook-configuration.png) | `PreToolUse` configuration; native enforcement is proven separately |
| [15](screenshots/screenshot-15-blocked-apply.png) | Recorded actual fresh-FAIL native denial, not the earlier missing-report case; Terraform did not execute |
| [16](screenshots/screenshot-16-human-resolution.png) | Recorded genuine personal resolution approval; no reconstructed chat or manual human Terraform execution |
| [17](screenshots/screenshot-17-final-healthy-review.png) | Recorded genuine final Claude HEALTHY review after the actual decision and fresh checker |
| [18](screenshots/screenshot-18-saved-reports.png) | Actual Bash directory listings; synthetic parent reports distinguished from historical live records |
| [19](screenshots/screenshot-19-summary.png) | Current seven-section summary: completed operational review/decision/cleanup loop, with manual-execution and publication limits |

For screenshots 6/18, `ls -g -o` omits local owner/group names, not results. Screenshot 18 hashes the four required detected/final reports; other listing metadata describes capture time, not file contents. Both actual commands and listings are visible; introductory fixture/record captions scrolled outside the viewport and are **not** claimed visible. Parent `reports/*.txt` are synthetic fixtures; `reports/live/*` contains dated operational evidence. Screenshots 1/8 omit refresh identifiers and replace private plan paths **in the clearly labeled text export before display**, never in image pixels. Recorded editor exports—including native Claude events and the human decision—are not fresh terminal/chat replays. All accepted originals match their source/image hashes; prior canonical versions are preserved privately and in Git history. Screenshot completion does not establish manual human Terraform execution or publication; those rubric limitations remain.

## Terraform preparation and bounded execution

The [original preflight](reports/live-preflight.json) remains dated read-only evidence, not a deployment record. Both projects passed `terraform fmt -check` and `terraform validate -json` with Terraform 1.13.5 and pinned AWS provider 6.64.0 against byte-identical private initialized copies. No provider binaries, state, bindings or credentials are committed.

- [Network](terraform/network/main.tf): one dedicated VPC, no subnet, gateway, public IP, compute, endpoint or workload.
- [Security group](terraform/security-group/main.tf): one unattached group, empty ingress and egress by default. `test_public_ssh` is **for an unapplied plan only**.
- Separate roots/states preserve policy scope. The checker evaluates the complete SG plan, not a filtered selection forced to HEALTHY. It cannot certify the support VPC, AWS-created defaults or the entire account.
- Both providers require `dmi-week8`, `ap-south-1`, the privately verified expected account and fixed `DmiLab` tag. The SG must use the current dedicated VPC's actual binding, never an old deleted ID.

On 16 September the approved saved VPC plan was applied at **14:54:54–14:58:07Z**. A fresh closed-SG plan was independently reviewed for exactly one create, no updates/deletes, correct new VPC binding and empty ingress/egress, then applied at **15:06:30–15:07:51Z**. Guards verified exact non-root identity, ownership, sources, state, isolation and actual-resource cleanup dry-run permissions. A dry run proves permission, not deletion. Immutable attempt/completion receipts and hash-specific applies prevent blind retries. Actual current-cycle creation/planning records are in [cycle-20260916.json](reports/live/cycle-20260916.json); the separately dated [15 September cleanup](reports/live/operations.json) deleted the earlier resources only.

Model execution uses restricted Bedrock Haiku (`global.anthropic.claude-haiku-4-5-20251001-v1:0`, origin Mumbai, global routing). The [continuation runbook](BEDROCK_ACCESS.md) distinguishes historical access failures from successful enrollment and later native reviews. The inference role was not broadened with Marketplace or Terraform permissions. The existing exec-form hook (`command` plus `args`) is supported by Claude Code 2.1.220; both offline regression and separate actual native evidence are retained. No repeat connection test, alternate model or expired enrollment-session reuse is needed.

**Current-cycle cleanup verified at 16:01:58Z.** A first SG destroy plan was refused because Terraform left the resource-only `var.vpc_id` validation unevaluated. The refused plan and receipt were preserved. A narrowly scoped compatibility change accepts only that exact unknown/no-instances check for SG deletion; exact source, live binding, closed rules, ownership, isolation, state and delete-only action checks remain required. **71 normal and 71 optimized offline tests passed**, including rejection of other unknown/failed checks. Fresh plans were independently inspected and hash-reviewed. SG deletion ran at **15:57:16–15:58:38Z**, followed by VPC deletion at **16:00:36–16:01:30Z**, both exit 0. The separate cleanup check verified both states empty, zero lab-tagged inventory, and exact-resource `InvalidGroup.NotFound` / `InvalidVpcID.NotFound`. This is the 16 September cleanup, not a relabeled older record.

Keep raw outputs, runtime copies, state, private variables and initialization data inside ignored `.review-data/`. Expected VPC/SG resource-type charges are $0 because no paid workload components were created; this is not an audited account-billing result. Historical baseline/final HEALTHY reports predate deletion and do not claim a currently deployed lab. Exact review-era source snapshots were preserved before documentation reconciliation. The operator receipts' `human_resolution_obtained:false` and `final_review_significance:false` are deliberate **non-attestations**; actual user approval and Claude review are separately evidenced, not contradicted by those flags.

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

The configuration is scoped to **this nested project**, not root `.claude/settings.json`. Bounded runs use isolated Bedrock settings, a path-bound copy of the hook configuration, no external MCP servers, `dontAsk`, and no Terraform executable/configuration/state in Claude's working context. Empty setting sources initially prevented Skill discovery; registering a byte-identical Skill in a fresh task-local Claude configuration fixed it. This proves **isolated registration, not normal project auto-discovery**. Earlier API failures occurred before Read/hook events; subsequent genuine clean/risk reviews and native denial controls established actual runtime behavior separately. Root/personal settings were not enabled as a Claude shortcut.

Any future, separately authorized review must stay within its approved allowance and use fresh evidence; no further review call is needed for this cycle. Verify actual full Reads, matching native hook/tool events, context and report citations, not merely initialization metadata or a JSON unit test. Negative controls retain ordinary restrictive permissions, unavailable Terraform, an empty-of-configuration working directory and a Bedrock-only identity. No apply/destroy permission is granted to demonstrate the block.

Official schema references checked during implementation:

- [Claude Code Skills](https://code.claude.com/docs/en/skills): `disable-model-invocation: true` and `allowed-tools: Bash Read Grep`.
- [Claude Code Hooks](https://code.claude.com/docs/en/hooks): `hooks.PreToolUse[]`, wildcard matcher, command hook exec-form `command`/`args`, JSON stdin, exit 0 to continue normal permission flow and exit 2 to block. Use a current version supporting exec-form args; verify rather than assuming older installations support it.

`noWrite` is an explicit body instruction, **not an unsupported YAML field**. Allowed tools are not a Bash sandbox. The hook applies an exact finite command allowlist, not a broad regex or general shell parser. Read/Grep paths are confined to selected review files/directories. Unknown tools, arbitrary shell commands, alternate whitespace, wrappers, chaining, pipes, redirects, substitutions, environment assignments, unexpected Bash input options and background execution are rejected without evaluating or normalizing the command. Approved Bash commands only inspect fixed reports/script syntax or run the fixture checker to one new ignored report.

The hook consults `.review-data/current-report.txt` for its denial explanation. A current FAIL produces a FAIL reason; missing, malformed, stale (>15 minutes), future-dated or fixture reports never authorize anything. **Apply, destroy and auto-approve remain denied even with a fresh LIVE HEALTHY report.** Inspecting a stale report is allowed as historical inspection, not evidence of present health. Allowed tools return 0 without a permission override, leaving normal Claude permission checks in place.

This guard assumes trusted source files/interpreters/PATH and a correctly loaded synchronous hook. It is not an OS sandbox, an organizational policy engine, a report signature or control over human terminals. It does not make inherited settings, disabled hooks, malicious executable replacement, shell startup files, filesystem races or actions outside Claude safe. Human infrastructure actions belong outside the AI workflow and require independent review and authorization.

## Validation, source parity and pending completion

Run `python3.13 tests/run_validation.py --report NEW_PATH` to regenerate counts, source hashes, fixture results, screenshot inventory and limitations. The tracked [validation record](reports/local-validation.json) is generated, not hand-written test evidence. It hashes public source/fixtures/docs/sanitized reports, accepted screenshots and their manifest, and the assignment submission; it excludes itself, private runtime data, state, variables and provider directories. Tests check PNG/image/source hashes, correct attachments, remaining placeholders, live-record consistency, actual decision/final/cleanup chronology, real-vs-reserved model costs and Git exclusions. They do **not** repeat AWS operations or Claude requests. Hashes are integrity checks, not signed attestations. Prior validation and captures remain in Git history.

[Source metadata](tests/assignment-source.json) records the pinned assignment commit `9b394ef8efecd7db1f582995a03665f6f8afc2a4`, upstream blob `2c00e004853ae2eb146928eb86d19459b538be1b` (14,111 bytes), and original local blob `921e3a543890792187fd0e502b84759e09426dd0` (14,120 bytes). The only original text difference was the subtitle's `Cohort 3`. Tests retain all required headings/questions, all checklist items, all 19 numbered screenshot sections with their accepted attachments or explicit pending placeholders, and the LinkedIn screenshot placeholder.

The genuine clean/risk/final reviews, fresh-FAIL native denial, later personal resolution approval, verified current-cycle cleanup and all 19 accepted screenshots now exist as separate dated evidence. Genuine LinkedIn publication/URL/screenshot is still required. The original manual-human-execution checklist remains unchecked because Copilot performed the authorized infrastructure operations. Required filenames or AI explanations cannot substitute for missing evidence, and an A/full-rubric outcome is not claimed. No new merge, Medium publication or LinkedIn publication is claimed.
