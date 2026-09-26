---
name: azure-audit
description: Read-only audit of the Week 07 Azure lab and evidence-grounded explanation.
allowed-tools: Read, Bash(./azure-audit.sh)
---

Run exactly `./azure-audit.sh`, then read `reports/azure-audit-report.json` and explain all four checks.
The script writes only its local report. A nonzero exit is expected for WARN or FAIL; still read the fresh report.
Never execute an Azure create, update, delete, set, deployment, or run-command operation.
Never modify files or invoke another shell command. Never claim missing evidence is a PASS.
Cite actual resource names and values. Distinguish an unattached deliberately configured test NSG from internet exposure of a VM.
Recommend remediation in prose for the operator; do not run it. State that the learner delegated this recovery to Codex.
