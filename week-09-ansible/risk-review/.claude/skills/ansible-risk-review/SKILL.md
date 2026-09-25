---
name: ansible-risk-review
description: Gather a fresh Ansible dry run and explain pending EpicBook changes without applying them.
disable-model-invocation: true
allowed-tools: Read, Bash(./run-review.sh)
---

Read `CLAUDE.md`. Run exactly `./run-review.sh` once, without arguments, shell
operators, environment assignments, background execution or command substitution.
Set the Bash tool timeout to 600000 milliseconds and wait for completion before
interpreting any report. A RUNNING report or a timestamp earlier than this
invocation is not evidence. After completion, read the new report again even if
an earlier report was already read. Never preserve a stale HOLD or LOW result.
The operator supplies the private configuration; never read it or request secrets.
The wrapper runs only `ansible-playbook --check --diff` and returns a sanitized
report. Read `reports/latest.json` if needed.

State the learner name, report timestamp, status, failed/unreachable counts and
deduplicated changed tasks. Analyze exactly four categories: service restarts and
handlers, firewall changes, user/sudo changes, package/file removal. Unmatched
changes require review. ERROR means evidence is not usable. HOLD means do not
apply. LOW means no changes were predicted by supported modules; it does not
prove application health or substitute for the real deployment verification.

Recommend an operator-reviewed next step. Never edit, deploy, remove files,
restart services, run the playbook without check mode, or claim the learner
personally executed an assisted operation.
