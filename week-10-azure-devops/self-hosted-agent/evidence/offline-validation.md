# Offline validation — 2026-09-17

This record covers local source preparation only. It is not an assignment submission, live host inventory, package attestation, Azure pipeline report, or screenshot evidence.

## Environment actually checked

- macOS system `/usr/bin/python3`: Python 3.9.6.
- Existing `/usr/bin/ruby`: Ruby 2.6.10; bundled Psych 3.1.0 YAML parser. PyYAML was absent, so the existing parser is reused; no dependency was installed.
- A sanitized `env -i` invocation with `HOME=/nonexistent`, Python `-I -B`, and `/usr/bin/sandbox-exec` denied a local socket bind with `PermissionError: [Errno 1] Operation not permitted`. The probe intentionally attempted no remote connection.
- The test command also denies `file-write*`; tests use repository reads and in-memory fixtures, not temporary files or HOME configuration.
- Initial worktree disk check: 1.5 GiB available. Deliverables are text-only; no package/provider download or installation occurred.

## Preservation baseline

Base commit: `d7c5fbf15c25edf2cc2d23c07d69796ed4b19212` (fast-forwarded from `376f7a9305884494a7efc36b8f2b22fe1c02348d` before the delivery commit).

[`tests/source-baseline.json`](../tests/source-baseline.json) records SHA-256 and byte lengths of all five original briefs, A1's exact seven screenshot titles and eight unchecked checklist entries, and the root README baseline hash. The preservation contract removes only A1's delimited added notice and reverses only the authorized Week 10 root progress row. No original answer, screenshot placeholder, checklist, task or note was replaced.

A direct heading/list count found numbered screenshot counts **7, 5, 6, 6, 12** and unchecked checklist counts **8, 22, 21, 40, 33** for A1–A5 respectively. A2 additionally has one unnumbered LinkedIn screenshot heading. These counts reflect unfinished requirements, not completed evidence.

## Local test result

**37 tests passed** in **1.551 seconds** under the documented network/file-write-denying sandbox (exit 0, no skipped tests). The exact credential-free command is in the [runbook](../README.md#offline-validation).

Coverage includes strict candidate keys/types, unsupported OS/architecture, root/privileged accounts, disk/Git/command requirements, package URL/release/hash/compatibility fields, duplicate/malformed/oversized input, checksum comparison using synthetic in-memory bytes, CLI error privacy and fail-closed behavior, real Ruby/Psych YAML parsing, manual-only pipeline constraints, no checkout, exact required commands, pending evidence metadata, local links, original brief hashes/counts, and root-row-only preservation. No pipeline script, downloaded package, registration or service command was executed.

`git diff --check` also passed. Direct review of the two existing-file diffs confirmed only the authorized root progress row and A1's delimited notice changed. The new source/runbook/tests were reviewed locally; this is not an independent security audit or a live deployment review.

## Not performed / remaining gates

No AWS, Azure or Azure DevOps control-plane call; credential/PAT creation or reading; SSH; Terraform plan/apply/destroy; provisioning; account/service change; package download/extraction; agent registration; pipeline run; GUI capture; social publication; Docker; paid-model or instructor application activity occurred. Public Microsoft documentation and public Microsoft GitHub release metadata were read to inform the runbook; release metadata is not installation evidence.

Cloud choice, budget/identity/SSH approval, reviewed VM adaptation, runtime package compatibility and checksum verification, dedicated account/pool/PAT, interactive registration/service setup, Online status, actual manual pipeline success, readable secret-free screenshots, learner notes and cleanup remain live gates. A2–A5 remain brief-only. All seven A1 manifest entries remain false/null/pending.
