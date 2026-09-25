# Read-only pipeline triage

This is an original Codex-assisted implementation of the published Week10 A5 workflow. It is **not claimed to be the supplied instructor kit**: neither the pinned DMI repository nor the instructor's Agentic DevOps repository contained those supplied files. The supplied-kit-only rubric item remains unresolved until those originals can be compared.

`pipeline-triage.sh` runs a fixed four-category check-function array after `fetch.py` makes bounded authenticated GET requests for both pipelines' completed-run metadata, timeline records and actual failed-step logs. Raw logs and the PAT stay out of saved reports. `classify.py` returns 0 for HEALTHY, 1 for INCIDENT and 2 for incomplete/unreliable evidence. Failed or canceled unmatched runs fail closed as unclassified INCIDENT.

The operator creates ignored `.private/config.json` with `infrastructure_id`, `application_id`, and `application_branch` (`refs/heads/main` or `refs/heads/triage-safe-drill`), and supplies `AZDO_READ_PAT` through a protected wrapper. Never put the PAT in source, command arguments, screenshots or reports. Written instructions supplement the separate mandatory tool guard.
