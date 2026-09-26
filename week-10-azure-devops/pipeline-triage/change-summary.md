> **26 September update:** the AWS authentication blocker is resolved. A fresh Claude/Bedrock baseline → incident20 → recovery21 sequence is documented [here](../evidence/2026-09-26/README.md). The account below preserves the earlier deterministic drill as history.

# Controlled pipeline failure and recovery

Full Name: Eze Favour. Operator: Codex. Date: 25 September 2026.

The read-only baseline selected infrastructure run11 and application run14, both successful: HEALTHY, exit0. The operator then created `triage-safe-drill` from verified main and inserted one Build step printing `DMI_CONTROLLED_FAILURE: missing demo build input`, then exiting1. Run18 failed before deployment. The triage tool fetched real timeline/failed-step logs and reported APPLICATION / INCIDENT, exit1. The saved report preceded the fix.

The operator removed exactly that injected step on the temporary branch. Run19 succeeded in Build, while Deploy was skipped by the independent main-only condition. The second read-only triage returned HEALTHY, exit0. Main and the live app were unchanged by the drill.

This is an original replacement triage implementation: no supplied kit was found in the pinned instructor repository, the linked Agentic DevOps repository or the task-local files. It is not represented as the supplied kit. AWS authentication expired before the Week10 Claude diagnosis could run. The deterministic report and Codex explanation are not Claude output; the Claude skill execution criterion remains unverified.

Reports: [baseline](reports/baseline-report.txt), [incident](reports/incident-failure-report.txt), [recovery](reports/recovery-report.txt). The corresponding JSON files retain sanitized pipeline metadata and classifications; raw credential-bearing logs are not published.
