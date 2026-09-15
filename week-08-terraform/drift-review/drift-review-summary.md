# Terraform Drift Review Summary

**Full name: Eze Favour**

**Status: branch-only local implementation; synthetic demonstrations, not deployed-infrastructure evidence.**

## 1. Change Introduced

I used an explicit synthetic plan fixture that adds a security-group ingress update allowing TCP/22 from `0.0.0.0/0`. The clean fixture has no inbound rules. This is **neither observed true infrastructure drift nor an executed Terraform configuration change**: it models a possible configuration change without deploying it. No real baseline or provider authorization was available. [Fixtures and policy](README.md#fixtures-scope-and-policy) explain the assumptions.

## 2. Evidence Collected

The Bash checker genuinely processed [detected.json](fixtures/detected.json) and [clean.json](fixtures/clean.json) offline using jq and the standard-library evidence helper. The fictional affected resource is `aws_security_group.synthetic`, with an `update` action and a public ingress rule in the detected fixture. The resulting [detected report](reports/drift-detected-report.txt) and [resolved report](reports/resolved-report.txt) record my name, UTC time, mode, input hash and counts. [Local validation](reports/local-validation.json) records the executed test suite/source hashes. These are not a real `terraform plan` or Claude transcript.

## 3. Risk Assessment

The deterministic check reports fixture **FAIL** because unrestricted public SSH is outside the policy. Deletes and both replacement orders also fail in tests. Intentional public TCP/80 or TCP/443 remains **WARN**, requiring a human exception decision, never blanket approval. Unknown or unsupported evidence cannot return unconditional HEALTHY. GitHub Copilot assisted implementation and this explanation; **Claude Code has not run**, so there is no observed Claude recommendation to quote.

## 4. Human-Approved Action

No infrastructure action was performed or approved here. The proposed future action is for an authorized human to inspect a fresh trusted-project plan and determine whether to remove/restrict an unintended rule or explicitly approve an intended exception through the normal change process. I separately evaluated the clean fixture as a synthetic resolution demonstration; I did not apply a fix, edit a live Terraform configuration, or claim provider verification.

## 5. Verification

The checker returns **2 / FAIL** for the public-SSH fixture and **0 / HEALTHY** for the clean fixture, with unmistakable synthetic banners. The latter means only that the fixture has no pending changes/findings in the supported scope. Subprocess tests cover policy decisions, malformed/unknown data, missing tools, no-overwrite behavior, filename quoting, secret redaction, fake Terraform detailed exits and command constraints, and JSON-only hook simulations. A real post-action plan, final Claude review and screenshots are **pending**; there is no evidence proving the deployed environment is aligned.

## 6. Safety Decision

AI may explain evidence but must not mutate infrastructure. The manual Skill declares noWrite with Bash/Read/Grep only, and the isolated hook permits only fixed review commands. It blocks all apply/destroy/auto-approve requests regardless of report status. Tests simulate these requests as JSON and never run them. Human-authorized live planning is a separate trusted-project boundary because Terraform providers/data sources execute code; the hook is not a sandbox or control over human actions. Raw plan/log data remains private and ignored; sanitized reports never authorize mutation.

## 7. Agentic Loop Mapping

| Stage | Actually completed locally | Still pending operationally |
| --- | --- | --- |
| Gather | Explicit synthetic fixture JSON copied into a fresh private workspace | Authorized clean baseline and live plan/show evidence |
| Analyze | Deterministic Bash/jq checks; GitHub Copilot-assisted explanation and tests | Actual manual `/tf-drift-review` reasoning and screenshots |
| Human Act | Proposed decision documented; no infrastructure action | Independent human review and authorized resolution |
| Verify | Separate clean fixture check and passing local validation | Fresh real final plan and Claude review showing intended alignment |

This is a tested local harness for **Gather → Analyze → Human Act → Verify**, not a completed live agentic loop. Six genuine local editor/terminal screenshots (3, 4, 5, 6, 9 and 14) are attached to the submission with [capture provenance](screenshots/manifest.json). They show actual source/configuration and Bash validation, not live infrastructure or Claude execution. The other 13 numbered screenshots and publication evidence remain pending; no LinkedIn post or URL has been created.
