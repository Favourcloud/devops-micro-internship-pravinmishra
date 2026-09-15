# Assignment 6 — AI-Assisted Terraform Drift and Policy Review

Part of the DevOps Micro Internship (DMI) Cohort 3 with Agentic AI

---

## Student Details

**Full Name:** Eze Favour

**GitHub Repository/Folder URL:** https://github.com/Favourcloud/devops-micro-internship-pravinmishra/tree/main/week-08-terraform/drift-review

The URL is the intended source folder on `main`; these deliverables are currently **local branch-only, not merged or published**, so that new folder may not yet be available through the main-branch URL. Local source: [drift-review/](drift-review/README.md).

## Current Submission Status — Local Work Only

| Requirement | Current evidence | Status |
| --- | --- | --- |
| Project context, script, isolated Skill/hook | [README/runbook](drift-review/README.md), [CLAUDE.md](drift-review/CLAUDE.md), [checker](drift-review/AI%20Assignment/tf-drift-check.sh), [Skill](drift-review/.claude/skills/tf-drift-review/SKILL.md), [hook settings](drift-review/.claude/settings.json) | Implemented locally; Claude runtime not exercised |
| Deterministic policy/hook tests | [Tests](drift-review/tests/test_review.py), [generated validation record](drift-review/reports/local-validation.json) | Local subprocess validation only; fake Terraform for exit-code tests |
| Required report filenames | [Detected report](drift-review/reports/drift-detected-report.txt), [resolved report](drift-review/reports/resolved-report.txt) | Generated from explicit synthetic fixtures; **not live infrastructure evidence** |
| Seven-section summary | [drift-review-summary.md](drift-review/drift-review-summary.md) | Completed for actual local work and explicit limitations |
| Clean/final baseline, controlled live change, human resolution | No authorized real plan/provider access | **Pending — Tasks 1, 4, 6 and 8 operational outcomes not completed** |
| Claude invocation and actual hook integration | Only JSON-input hook simulation, no Claude execution | **Pending — Tasks 5 and 7 runtime evidence** |
| Local screenshots 3, 4, 5, 6, 9 and 14 | Six genuine VS Code/terminal captures embedded below; [capture provenance](drift-review/screenshots/manifest.json) | **Captured — local source/configuration and actual syntax/permissions checks only** |
| Remaining screenshots and LinkedIn publication | 13 numbered placeholders and publication evidence retained below | **Pending; nothing posted and no live evidence fabricated** |

**Evidence boundary:** Every report marked `FIXTURE` is an offline demonstration. A synthetic `HEALTHY` is not my actual infrastructure baseline. The existence of both report filenames does not complete Task 8. No live Terraform plan/apply/destroy or cloud API request was made. GitHub Copilot assisted the implementation, tests, draft answers and local capture setup; I have not invoked the implemented Claude Skill. Screenshots 3, 4, 5, 6, 9 and 14 are genuine local captures with Eze Favour visible. The other 13 numbered screenshots and LinkedIn publication screenshot remain pending. Static Skill/hook screenshots do not prove runtime invocation.

**Source parity:** Compared the complete original template with pinned upstream commit `9b394ef8efecd7db1f582995a03665f6f8afc2a4`, blob `2c00e004853ae2eb146928eb86d19459b538be1b` (14,111 bytes). The original local template only added `Cohort 3` to its opening subtitle. All required headings, questions, 19 numbered screenshot sections, publication placeholders, and checklist items are preserved. Six numbered placeholders now contain genuine local captures; 13 remain pending. [Metadata and regression checks](drift-review/tests/assignment-source.json) record the original requirements.

---

## Purpose

Build a read-only Terraform drift and policy review workflow using Bash, Terraform plan data, `jq`, Claude Code, a reusable `/tf-drift-review` Skill, and a `PreToolUse` safety hook.

The workflow must follow this pattern:

```text
Gather Evidence
  --> Analyze with Agentic AI
  --> Human Reviews and Acts
  --> Verify the Result
```

The `/tf-drift-review` Skill and `tf-drift-check.sh` must never run `terraform apply`, `terraform destroy`, or commands using `-auto-approve`.

---

# Task 1 — Confirm the Clean Baseline and Create the Workspace

## Goal

Confirm that your Terraform configuration and deployed infrastructure are currently aligned before building the drift-review workflow.

## Evidence

### Screenshot 1 — Clean Terraform Plan

Add a screenshot of `terraform plan` showing no pending changes.

Add your screenshot here.

---

### Screenshot 2 — Assignment Workspace

Add a screenshot of the folder structure showing `AI Assignment/`, `reports/`, and the Terraform project.

Add your screenshot here.

## Questions

### 1. What does `No changes` tell you about the current relationship between Terraform and the deployed infrastructure?

For the selected configuration, workspace, state and refreshed provider evidence, Terraform proposes no managed changes. It does not certify untracked resources, every security control, or future state. I have not established a real `No changes` baseline here; the clean result is synthetic only.

### 2. Why is a clean baseline important before introducing a test change?

I need it to distinguish my intentional change from pre-existing differences and to make the before/after comparison meaningful. An authorized live clean baseline remains pending, so my fixture comparison cannot prove anything changed in deployed infrastructure.

---

# Task 2 — Create Project Context and Safety Rules in `CLAUDE.md`

## Goal

Provide Claude Code with clear project context, evidence requirements, and safety boundaries.

## Evidence

### Screenshot 3 — Project Context and Safety Rules

Add a screenshot of `CLAUDE.md` open in VS Code showing the Project Overview, Review Workflow, Safety Rules, and Output Rules.

![Screenshot 3 — Eze Favour's project context and four safety/workflow sections in VS Code](drift-review/screenshots/screenshot-03-context.png)

Captured locally on 15 September 2026. This shows the actual context file, not a Claude invocation.

## Questions

### 1. Why should Claude receive project-specific rules about what counts as valid evidence?

I want the reviewer to distinguish a real current plan from an old report, invented explanation, or synthetic fixture, and to state the exact policy scope. My `CLAUDE.md` requires provenance, timestamps, hashes and explicit unknowns, rather than treating an AI opinion as infrastructure evidence.

### 2. Why must the human remain responsible for running `terraform apply`?

Applying a plan can delete or replace resources, interrupt service, expose data, or incur costs. An authorized human must review the exact fresh plan, workspace and consequences through the normal change process. This review workflow never applies anything; no human apply was performed for this submission.

### 3. Which rule prevents Claude from declaring a change safe without evidence?

The Output Rules in my local `CLAUDE.md` say never to declare safety without complete, fresh evidence within the stated limited scope. Missing, stale, malformed, unknown or fixture evidence cannot be converted into a live safety approval, and even HEALTHY cannot authorize mutation.

---

# Task 3 — Build the Terraform Drift and Policy Check Script

## Goal

Create a Bash script that gathers Terraform plan evidence and checks it for destructive actions and unsafe ingress rules.

## Evidence

### Screenshot 4 — Script Variables and Checks Array

Add a screenshot of the top section of `tf-drift-check.sh` showing the variables and `checks` array.

![Screenshot 4 — Actual Bash variables and checks array in VS Code](drift-review/screenshots/screenshot-04-variables-checks.png)

Captured locally on 15 September 2026; source view only.

---

### Screenshot 5 — Destructive-Action and Open-Ingress Checks

Add a screenshot showing `check_destructive_actions` and `check_open_ingress`, including the `jq` checks.

![Screenshot 5 — Destructive-action and open-ingress functions with the jq ingress policy in split view](drift-review/screenshots/screenshot-05-policy-checks.png)

Captured locally on 15 September 2026. The left editor shows both actual Bash functions and jq invocations; the right shows the relevant ingress-policy logic, not the entire policy file.

---

### Screenshot 6 — Script Validation and Permissions

Add a screenshot showing successful `bash -n` and `ls -l` output.

![Screenshot 6 — Genuine terminal syntax exit 0, executable permissions and script SHA256](drift-review/screenshots/screenshot-06-validation-permissions.png)

Actual local commands ran on 15 September 2026: `bash -n` returned 0, `ls -l -g -o` showed `-rwxr-xr-x`, and `test -x` returned 0. The `-g -o` options omit local owner/group names; no screenshot pixels were changed. No Terraform or cloud command ran.

## Questions

### 1. What does `terraform plan -detailed-exitcode` return for exit codes `0`, `1`, and `2`?

Terraform returns 0 for a successful plan with no changes, 1 for an error, and 2 for a successful plan with changes. I tested these branches using fake Terraform executables only. My checker separately uses 0/HEALTHY, 1/WARN, 2/FAIL and 3/ERROR; those are not Terraform's exit-code meanings.

### 2. Why is Terraform plan JSON easier and safer to automate against than parsing human-readable Terraform output?

It has structured actions, before/after values and unknown flags that jq can validate and inspect without relying on display wording or colors. JSON still needs schema validation and careful handling of unknown values. Raw plans can contain secrets, so my script uses private scratch data and outputs only sanitized counts/provenance.

### 3. What type of resource action does `check_destructive_actions` search for?

It searches the actions arrays in resource changes and refresh-drift observations for `delete`, and reports the count without exposing resource identifiers. Other changes are reported separately rather than mislabeled clean.

### 4. Why does finding a `delete` action also help detect replacements?

Replacement contains both create and delete, in either order depending on lifecycle behavior. Searching for membership of `delete` detects both `["delete", "create"]` and `["create", "delete"]`, not just deletion-only arrays.

### 5. Why must this script never run `terraform apply`?

Its job is evidence collection and policy checks, not change authorization. Automatically applying findings would merge analysis with a potentially destructive action and remove human oversight. Even the guarded future live mode permits only plan and show; trusted-project authorization is still required because providers/data sources execute code.

---

# Task 4 — Run the Script Against the Clean Baseline

## Goal

Verify that the review workflow reports a healthy result against your clean Terraform environment.

## Evidence

### Screenshot 7 — Healthy Baseline Report

Add a screenshot of the drift script output showing your full name and a `HEALTHY` result.

Add your screenshot here.

---

### Screenshot 8 — Baseline Script Exit Code

Add a screenshot showing the captured script exit code `0`.

Add your screenshot here.

## Questions

### 1. What is the Overall Status of your baseline?

My **real baseline is pending/not established**. The explicit offline clean fixture produces `Overall Status: HEALTHY` and checker exit 0, but that is only a labelled synthetic demonstration, not the Task 4 live baseline.

### 2. Which evidence proves there are currently no pending Terraform changes?

There is no live evidence proving that in this submission. A fresh, authorized plan with detailed exit 0 and validated JSON for the intended workspace would be required. The fixture report's hash proves which synthetic input was evaluated, not deployed alignment.

### 3. Was `reports/tfplan.json` created? Explain why or why not.

No persistent `reports/tfplan.json` was created. Offline runs copy the fixture into a new private scratch directory, then remove it after analysis. A later authorized live run would create temporary plan binary/JSON in ignored private scratch space, never commit raw plans or provider logs. No real plan JSON was collected here.

---

# Task 5 — Create and Run the `/tf-drift-review` Claude Code Skill

## Goal

Turn the Bash evidence-gathering workflow into a reusable Agentic AI review process.

## Evidence

### Screenshot 9 — `/tf-drift-review` Skill Configuration

Add a screenshot of `SKILL.md` showing the frontmatter, allowed tools, and safety rules.

![Screenshot 9 — Skill frontmatter, allowed tools and noWrite safety rules in VS Code](drift-review/screenshots/screenshot-09-skill-configuration.png)

Captured locally on 15 September 2026. This demonstrates the configuration only; actual `/tf-drift-review` execution is pending.

---

### Screenshot 10 — Clean Agentic AI Review

Add a screenshot of `/tf-drift-review` showing the clean `HEALTHY` result.

Add your screenshot here.

## Questions

### 1. Why does this Skill have `Bash`, `Read`, and `Grep`, but not `Write`?

I only want inspection and the audited evidence checker, not source/configuration edits. The noWrite instruction and hook deny Write/Edit and arbitrary commands. Bash itself can write, so the actual allowlist permits only inspection and the checker creating fresh local evidence; tool names alone do not establish read-only behavior.

### 2. Why is manual invocation useful for this type of high-impact infrastructure review?

`disable-model-invocation: true` leaves the decision to start a review with the human. It reduces unintended runs and makes scope and evidence deliberate. The Skill is configured locally but has not actually been invoked in Claude Code.

### 3. Which part of the workflow is deterministic Bash automation?

Argument/dependency checks, evidence collection, jq schema/policy evaluation, detailed-exit handling, sanitized report generation, and exit codes are deterministic automation. Python standard-library helpers handle private files, JSON parsing and CIDRs; hook decisions use an exact allowlist.

### 4. Which part requires Claude's reasoning?

Claude would explain the validated evidence in context, distinguish true drift from configuration intent, assess trade-offs and propose questions or options for human review. That Claude reasoning step is pending; current explanations were drafted with GitHub Copilot and are not claimed as observed Claude output.

### 5. Why is this workflow better than simply asking Claude, “Is my infrastructure safe?”

It ties each conclusion to inspectable evidence, explicit policy and unknowns, preserves a human action boundary, and requires fresh verification. A generic chat answer without provenance or scope cannot prove a resource's current state or authorize a change.

---

# Task 6 — Introduce a Controlled Difference and Detect It

## Goal

Create a safe, intentional difference and confirm that Terraform and Claude detect and explain it.

## Evidence

### Screenshot 11 — Controlled Difference

Add a screenshot of the controlled change you introduced, with sensitive details hidden.

Add your screenshot here.

---

### Screenshot 12 — Detected Difference and Risk Assessment

Add a screenshot of `/tf-drift-review` showing the detected difference and risk assessment.

Add your screenshot here.

---

### Screenshot 13 — Detected Drift Report

Add a screenshot of `drift-detected-report.txt` showing your full name and the `WARN` or `FAIL` result.

Add your screenshot here.

## Questions

### 1. What change did you introduce?

I added a controlled **synthetic fixture** modelling an AWS security-group ingress update that exposes TCP/22 to `0.0.0.0/0`. I did not change a deployed resource or a real Terraform configuration.

### 2. Was it true infrastructure drift or a Terraform configuration change?

Neither occurred operationally. The fixture models a configuration change for local testing. True drift would mean remote managed state diverged outside Terraform; a configuration change would mean changed desired code. An authorized real exercise and its classification remain pending.

### 3. What Terraform plan evidence proves that a change is pending?

Within the synthetic input only, the resource's `change.actions` is `["update"]` and its `after.ingress` includes the public SSH rule. The generated FAIL report records that fixture's hash. No real Terraform plan exists here to prove an actual pending change.

### 4. Was the action an update, deletion, replacement, or security-rule change?

The demonstration is an update containing a security-rule change, not deletion or replacement. Separate synthetic subprocess cases validate deletion and both replacement orders.

### 5. What did Claude recommend?

No Claude recommendation was produced because I have not run `/tf-drift-review`. The local policy finding suggests an authorized human should investigate whether SSH exposure is intended and remove or restrict an unintended rule through the normal change process; that is a proposed next step, not an executed repair.

### 6. Why should you review the recommendation before taking action?

I need to verify real intent, access requirements, unknown values, workspace and operational impact. Neither an AI suggestion nor a fixture report establishes those facts or grants permission to mutate infrastructure.

---

# Task 7 — Add a `PreToolUse` Hook to Block Unsafe Apply Attempts

## Goal

Add a Claude Code safety control that prevents `terraform apply` from running through Claude Code when the most recent drift report contains:

```text
Overall Status: FAIL
```

## Evidence

### Screenshot 14 — `PreToolUse` Safety Hook

Add a screenshot of `.claude/settings.json` showing the `PreToolUse` safety hook.

![Screenshot 14 — Actual PreToolUse command and args configuration in VS Code](drift-review/screenshots/screenshot-14-hook-configuration.png)

Captured locally on 15 September 2026. The configuration is visible, but effective settings loading and actual Claude hook invocation remain unverified.

---

### Screenshot 15 — Blocked Apply Attempt

Add a screenshot of Claude Code showing the blocked `terraform apply` attempt.

Add your screenshot here.

## Questions

### 1. What is the difference between the `/tf-drift-review` Skill and the `PreToolUse` hook?

The manually invoked Skill describes the evidence review and explanation procedure. The hook is a deterministic pre-execution gate for tool requests. I tested hook input/exit behavior using JSON simulation only, not an actual Claude apply attempt.

### 2. Which component performs analysis?

Bash/jq performs deterministic checks; the Skill would guide Claude's contextual interpretation. Only the local deterministic checks and GitHub Copilot-assisted implementation/explanation have been exercised here.

### 3. Which component enforces the safety gate?

The isolated project's `PreToolUse` hook rejects requests outside a finite review allowlist. Apply, destroy and auto-approve are always denied, including when the report is FAIL, missing, stale, malformed, synthetic or HEALTHY. Actual Claude integration remains pending.

### 4. Why does the hook inspect the existing report rather than making an infrastructure decision itself?

It uses the current report for a deterministic denial explanation without starting a plan or inventing context. The report is never a permission token: even a fresh live HEALTHY report cannot override this workflow's unconditional mutation prohibition.

### 5. Why is a deterministic guard useful for high-impact commands?

It makes the permitted command surface small, repeatable and testable rather than trusting model phrasing or a broad shell regex. My hook rejects chaining, substitution, wrappers and environment tricks without executing them. It is not an OS sandbox and cannot control a human terminal or a disabled/misconfigured hook.

---

# Task 8 — Resolve the Difference and Verify the Final State

## Goal

Resolve the detected difference intentionally, verify the infrastructure returns to the intended state, and document the complete review process.

## Evidence

### Screenshot 16 — Human-Reviewed Resolution

Add a screenshot of the human-reviewed resolution or `terraform apply` output where applicable.

Add your screenshot here.

---

### Screenshot 17 — Final Healthy Review

Add a screenshot of the final `/tf-drift-review` showing `HEALTHY`.

Add your screenshot here.

---

### Screenshot 18 — Saved Reports

Add a screenshot of `ls -lah reports` showing both:

- `drift-detected-report.txt`
- `resolved-report.txt`

Add your screenshot here.

---

### Screenshot 19 — Drift Review Summary

Add a screenshot of `drift-review-summary.md` showing all required sections and your full name.

Add your screenshot here.

## Terraform Drift Review Summary

### 1. Change Introduced

Explain the controlled change you introduced.

State whether it was:

- True infrastructure drift, or
- A Terraform configuration change

My completed change is a synthetic fixture modelling public SSH ingress on `aws_security_group.synthetic`. It is neither observed infrastructure drift nor an executed Terraform configuration change. The real controlled-change exercise remains pending. [Full summary](drift-review/drift-review-summary.md).

### 2. Evidence Collected

Describe the Terraform plan evidence and affected resource.

The fixture contains an `update` action and an `after.ingress` rule for TCP/22 from `0.0.0.0/0`. Bash/jq genuinely processed it and generated a sanitized report with my name, time, mode, source SHA256 and finding counts. A second run processed the clean fixture. These are not provider-produced plans or Claude transcripts.

### 3. Risk Assessment

Explain the risk identified by the Bash check and Claude Code.

The Bash policy reports fixture FAIL for unsafe public SSH. Tests also cover destructive actions, IPv4/IPv6 and unknown/malformed evidence. Intentional public HTTP/HTTPS receives WARN for human exception review. Claude Code analysis is pending; GitHub Copilot assisted the local implementation and explanation only.

### 4. Human-Approved Action

Explain the action you reviewed and executed manually.

No infrastructure action was approved or executed. The proposed future human decision is to review a fresh trusted-project plan and remove or restrict an unintended exposure, or justify an intended exception through the normal change process. Running a separate clean fixture is not a human-applied resolution.

### 5. Verification

Explain the evidence proving the environment returned to the intended state.

Local evidence verifies checker behavior: detected fixture exit 2/FAIL, clean fixture exit 0/HEALTHY, and the subprocess tests recorded in [local-validation.json](drift-review/reports/local-validation.json). Nothing here proves the deployed environment returned to its intended state; a real final plan and actual Claude review remain pending.

### 6. Safety Decision

Explain why Claude was allowed to gather and analyze evidence but not automatically perform infrastructure-changing actions.

The implemented boundary separates review from authorization: noWrite instructions, a fixed read-only tool/command surface, and an unconditional mutation-denying hook. A future human-authorized live plan must use a trusted project because providers/data sources execute code. No actual Claude session was granted or exercised in this work.

### 7. Agentic Loop Mapping

Explain how your workflow followed:

```text
Gather --> Analyze --> Human Act --> Verify
```

Locally: explicit fixture input → deterministic Bash/jq findings and assisted explanation → documented proposed human decision, with no infrastructure action → separate clean fixture and regression tests. Operationally, live evidence, actual Claude reasoning, human resolution and post-action verification are all pending; this is a local harness, not a completed live loop.

## Questions

### 1. What action did you execute to resolve the difference?

No actual infrastructure difference was resolved. I ran the checker against a separate clean synthetic fixture to demonstrate its resolved-report path. Human-reviewed operational resolution is pending.

### 2. Did you review `terraform plan` before taking action?

I inspected synthetic plan JSON for local policy testing, not a real Terraform plan, and performed no infrastructure action. Review of an authorized fresh live plan remains pending.

### 3. What evidence proves the environment is now aligned?

None in this submission. The resolved report proves only that the clean fixture passes the limited checks. Real alignment requires fresh trusted-provider plan evidence and the intended workspace/configuration, not the presence of a report filename.

### 4. Why is a second drift review required after the fix?

It verifies the actual resulting state rather than assuming an action succeeded, and can detect remaining changes, new drift or unknowns. It must collect fresh evidence rather than reuse the pre-action report.

### 5. What could go wrong if an AI agent automatically applied every detected Terraform change?

It could delete data, replace critical services, create outages or costs, expose resources, apply to the wrong workspace, or act on stale/incomplete evidence and malicious instructions. Deterministic review plus independent human authorization is safer than treating every difference as a repair instruction.

### 6. In one sentence, explain the difference between asking an AI chatbot “Is my infrastructure okay?” and using this evidence-based Agentic AI workflow.

A generic chatbot answer offers an opinion, while this workflow ties scoped conclusions to inspectable evidence, explicit safety gates, human decisions and fresh verification.

---

# LinkedIn Post — Mandatory

## Goal

Publish a LinkedIn post in your own words describing:

- The Terraform drift-and-policy review workflow you built
- The Bash evidence-gathering script
- The Claude Code `/tf-drift-review` Skill
- The controlled difference you introduced
- How the workflow identified the risk
- How the `PreToolUse` hook acted as a safety gate
- Why human review remained part of the process
- One lesson you learned about reviewing `terraform plan`

Include a screenshot of the detected change and a screenshot of the final `HEALTHY` review in your post.

Suggested tags:

```text
#DMIByPravinMishra #Terraform #AgenticAI #ClaudeCode #DevOps
```

## LinkedIn Evidence

### LinkedIn Post URL

Add your LinkedIn post URL here.

**Pending — not published; no URL is claimed.** The required detected-change and final live HEALTHY screenshots are also pending.

### Draft Only — Local Validation Progress, Not an Assignment-Completion Post

> I built a local, read-only Terraform drift/policy review harness for my DMI assignment with GitHub Copilot assistance. Bash and jq classify explicit synthetic plan JSON, including destructive actions, public IPv4/IPv6 ingress, unknown values and malformed input. A fixture modelling public SSH produces FAIL; a separate clean fixture produces a clearly labelled synthetic HEALTHY result.
>
> I also prepared a manually invoked Claude Code Skill and an isolated PreToolUse hook with a small review-command allowlist. Local JSON-input simulations verify that apply/destroy/auto-approve requests are denied, regardless of report status. I have not run the Skill in Claude, collected a live baseline, deployed the fixture change, or applied a fix.
>
> My lesson: a report filename or a green synthetic result is not infrastructure evidence. Provenance, scope, unknowns, independent human review and fresh post-action verification matter. Live validation, actual Claude screenshots and the final assignment post remain next steps when authorized.
>
> #DMIByPravinMishra #Terraform #AgenticAI #ClaudeCode #DevOps

This is draft text only. It does not fulfill the publication or screenshot requirement and has not been posted.

### Published LinkedIn Post Screenshot — Mandatory

Add a screenshot of the published LinkedIn post here.

---

# Required Assignment Files

Confirm that the following files are included in your GitHub repository:

All paths below exist under [the isolated local drift-review project](drift-review/README.md), not at the repository root. They are branch-only artifacts awaiting integration; both report files are synthetic demonstrations, and their existence does not complete Task 8.

- `CLAUDE.md`
- `AI Assignment/tf-drift-check.sh`
- `.claude/skills/tf-drift-review/SKILL.md`
- `.claude/settings.json` containing the safety hook
- `reports/drift-detected-report.txt`
- `reports/resolved-report.txt`
- `drift-review-summary.md`

---

# Submission Instructions

- Complete Tasks 1–8 in sequence.
- Include Screenshots 1–19 exactly as specified.
- Answer every question under Tasks 1–8 in your own words.
- Complete all seven sections of the Terraform Drift Review Summary.
- Include the GitHub repository/folder URL containing the assignment files.
- Include your full name in the required reports and screenshots.
- Include the LinkedIn post URL and a screenshot of the published LinkedIn post.
- Do not expose access keys, passwords, tokens, account IDs, private keys, Terraform secrets, or other sensitive information.
- Review all screenshots carefully and hide or redact sensitive details where necessary.

---

# Completion Checklist

Checked items mean **local implementation/fixture validation only**, not live infrastructure or Claude-runtime completion. The full Terraform workspace, real plan JSON, operational loop, Claude execution, screenshot-combined requirements and publication remain unchecked. Source hashes and test counts are in the generated local validation record. Synthetic report filenames are fulfilled locally but do not fulfill Tasks 4/8's live evidence.

- [ ] Confirmed a clean Terraform baseline
- [ ] Created the required assignment workspace
- [x] Created or updated `CLAUDE.md`
- [x] Added project context and safety rules
- [x] Created `tf-drift-check.sh`
- [x] Added my full name to the report
- [x] Validated the Bash script
- [x] Made the script executable
- [ ] Used `terraform plan -detailed-exitcode`
- [ ] Used Terraform plan JSON
- [x] Used `jq` to inspect destructive actions
- [x] Used `jq` to inspect unsafe ingress
- [ ] Confirmed the baseline returns `HEALTHY`
- [x] Created `/tf-drift-review`
- [x] Restricted the Skill to appropriate tools
- [ ] Confirmed the Skill remains read-only
- [ ] Confirmed the Skill never runs `terraform apply`
- [ ] Confirmed the Skill never runs `terraform destroy`
- [ ] Introduced a controlled detectable difference
- [ ] Correctly identified whether it was true drift or a configuration change
- [x] Saved `drift-detected-report.txt`
- [x] Added the `PreToolUse` safety hook
- [ ] Verified the hook blocks `terraform apply` when the report is `FAIL`
- [ ] Reviewed the Terraform evidence before resolving the change
- [ ] Performed any infrastructure-changing action manually
- [ ] Ran the drift review again after resolution
- [ ] Confirmed the final status is `HEALTHY`
- [x] Saved `resolved-report.txt`
- [x] Completed `drift-review-summary.md`
- [x] Mapped the workflow to `Gather --> Analyze --> Human Act --> Verify`
- [ ] Included all 19 numbered screenshots
- [x] Answered all required questions
- [ ] Published the required LinkedIn post
- [ ] Added the LinkedIn post URL and screenshot
- [x] Included the GitHub repository/folder URL
- [ ] Confirmed that no sensitive information is exposed

The checked Skill restrictions are configuration/static checks, not a claimed runtime invocation. The mapping documents which loop stages remain pending. Local generated reports are sanitized and secret-canary tests pass. The six attached local screenshots were reviewed before committing; all 19 screenshot and final publication/redaction checklist items remain open because 13 numbered captures and publication evidence are still missing.

---

*This submission is part of the DevOps Micro Internship (DMI) Cohort 3 — Agentic AI Track.*
