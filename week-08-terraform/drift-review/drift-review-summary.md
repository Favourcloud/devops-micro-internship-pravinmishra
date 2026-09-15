# Terraform Drift Review Summary

**Full name: Eze Favour — 15 September 2026**

**Status: genuine Terraform evidence and verified cleanup; Claude runtime/complete rubric sequence still pending.**

## 1. Change Introduced

A temporary configuration input proposed public TCP/22 on one isolated, unattached security group. The [example](terraform/public-ssh-proposal.tfvars.example) matched the task-local input used for real planning. This was an **UNAPPLIED configuration change, not out-of-band drift**. The risky rule was never deployed. Earlier synthetic fixtures remain unchanged.

## 2. Evidence Collected

Actual refreshed plans established both roots' clean baseline. Live checker reports show [baseline HEALTHY](reports/live/baseline-report.txt), [proposal FAIL](reports/live/drift-detected-report.txt), and [technical reset HEALTHY](reports/live/resolved-report.txt), with UTC times, plan hashes and Terraform exits 0/2/0. The proposal had one SG update, one unsafe ingress finding and zero refresh drift. [Operational record](reports/live/operations.json) links real execution, inventory, validation and cleanup; raw plans/identifiers stay private.

## 3. Risk Assessment

Public SSH fails the deterministic ingress policy. AWS read-back confirmed the deployed group still had zero ingress after planning. Claude produced **no successful review**: Skill discovery was fixed, but inference failed AWS Marketplace authorization. The earlier $0.00017 tool-free connection is not review evidence. [Actual runtime status](reports/live/claude-runtime.json) separates facts from pending work; these explanations are Copilot-assisted, not Claude recommendations.

## 4. Human-Approved Action

The user authorized isolated provisioning and cleanup beforehand; **Copilot executed Terraform**, not the human or Claude. Copilot removed the temporary override for cleanup safety and deleted only the new SG/VPC under that existing authorization. The user confirmed the technical findings but explicitly stated that [human resolution approval remains PENDING](reports/live/human-resolution.json). General continuation permission is not resolution approval; autonomous cleanup does not complete this requirement.

## 5. Verification

Before deletion, a fresh real plan/checker returned 0/HEALTHY after override removal. At **18:25:59Z**, cleanup verification found both Terraform states empty, zero lab-tagged VPCs/SGs, and both exact created-resource lookups `NotFound`. Both reviewed deletion applies exited 0; both Terraform roots pass fmt/validate. These dated results do not describe a currently deployed lab. [Offline tests](reports/local-validation.json) are separate from live evidence; final Claude review remains pending.

## 6. Safety Decision

The manual noWrite Skill may inspect only named sanitized live reports; its hook always denies apply, destroy and auto-approve. Local JSON-input tests cover enforcement, but **runtime hook loading/denial is not verified**. No risky apply, IAM expansion, earlier-coursework mutation, proxy restart or publication occurred. Raw evidence is excluded; screenshot editor views of sanitized exports are labeled, never passed off as live terminal sessions.

## 7. Agentic Loop Mapping

| Stage | Verified work | Remaining rubric gap |
| --- | --- | --- |
| Gather | Real clean baseline and unapplied proposal plans | Fresh baseline needed if the lab is recreated |
| Analyze | Actual Bash/jq HEALTHY → FAIL → HEALTHY | Actual Claude clean/risk/final reviews |
| Human Act | Prior provisioning/cleanup approval; Copilot-executed operations | Genuine human resolution approval; no manual-human apply claimed |
| Verify | No-change technical reset, real deletion, empty state/inventory | Actual Claude hook denial and final review |

[Screenshot provenance](screenshots/manifest.json) distinguishes source views, actual terminal listings and sanitized historical exports. Claude-dependent slots **10, 12, 15 and 17**, human-resolution slot **16**, and LinkedIn publication remain pending. This is substantial verified progress, **not a claim that the full rubric passed**.
