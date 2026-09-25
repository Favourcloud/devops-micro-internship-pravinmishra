# Ansible risk review — Eze Favour

Actual Claude Code over AWS Bedrock completed the plan, LOW baseline, HOLD removal drill and LOW recovery on 25 September 2026. Codex operated it under delegated authorization. Claude was restricted to the read-only wrapper; Codex separately applied the reviewed disposable-marker removal. This does not establish the rubric's learner-personally-manual apply requirement.

The four categories are service restarts/handlers, firewall changes, users/sudo, and package/file removal. Structured callback records capture changed tasks, module actions and host recaps without publishing Ansible diffs or secrets. Unknown changed modules fail closed. The Bash wrapper exposes the required check-function array and distinct exit codes.

The original Claude reports predate the managed-MySQL migration. The fresh [post-migration baseline](reports/post-migration-baseline.txt) is a real deterministic check-mode result: LOW, zero changes, zero failures and zero unreachable hosts. AWS authentication expired, so this report is explicitly not a new Claude invocation.

Read [change-summary.md](change-summary.md), the [original Claude evidence](evidence/), [reports](reports/) and [source](ansible-check-review.sh). Private inventory, Vault inputs, raw logs and AWS credentials are excluded. The wrapper requires a task-private operator launcher; it intentionally cannot apply, edit source, change cloud resources or run arbitrary commands.
