# Read-only Azure security audit

`azure-audit.sh` runs four Azure CLI read checks and writes local JSON/text reports through `analyze.py`: internet-wide administrative ingress, public blob access, managed-disk encryption at rest and MySQL public networking. No cloud mutation is present. Missing resources/failed reads cannot silently pass.

Validate with `bash -n azure-audit.sh` and `python3 -m unittest -v test_analyze.py`. Authenticate Azure CLI to the authorized lab subscription, then run `./azure-audit.sh`. Reports default to `reports/`; `DMI_AUDIT_OUTPUT` selects another private directory. Exit codes: 0 PASS, 1 FAIL, 2 WARN.

`CLAUDE.md` provides context. `.claude/skills/azure-audit/SKILL.md` permits Read and the exact script command, without Write. Actual Bedrock Claude planning and baseline/recovery runs, permission denials and interpretation corrections are preserved in the [dated evidence](../evidence/2026-09-26/README.md).

These configuration checks do not establish all effective routes, guest disk encryption, total cloud security or production compliance. Public static-website serving is distinct from anonymous blob access. The SSH fixture was unattached and exposed no VM. The separate Codex operator performed remediation under delegation; personal learner execution is not claimed.
