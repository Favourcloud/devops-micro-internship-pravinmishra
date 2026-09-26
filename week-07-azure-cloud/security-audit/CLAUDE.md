# Week 07 Azure security audit — Eze Favour

Audit the Week 07 lab only, using Azure CLI reads: NSG administrative ingress (22/3389), public blob access, VM managed-disk encryption at rest, and MySQL public network access.

The auditor is read-only. Never run mutating az commands. Never invent findings; cite report values. Propose remediation for the operator to review and execute separately. Never print credentials, full subscription/tenant IDs, tokens or connection strings. A missing/failed check is WARN or FAIL, never PASS. Azure platform-managed disk encryption must be distinguished from guest Azure Disk Encryption.

Workflow: plan before writing a script; build and syntax-check it; collect an unchanged baseline; invoke /azure-audit to explain the report; let the operator remediate; capture a fresh second audit. Codex is the authorized operator for this recovery. This must not be described as manual learner work or as a historical run.
