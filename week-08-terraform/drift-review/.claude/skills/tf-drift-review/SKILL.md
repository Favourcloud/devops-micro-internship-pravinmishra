---
name: tf-drift-review
description: Manually review sanitized Terraform drift and ingress-policy evidence without infrastructure mutation.
disable-model-invocation: true
allowed-tools: Bash Read Grep
---

# Manual read-only Terraform review

**noWrite:** Do not use Write, Edit, file modification tools, delegates, or arbitrary shell commands. Do not modify configuration, fixtures, policy, hooks, or existing evidence. The single evidence-writing exception is the audited checker producing a new report and private scratch data; it never changes infrastructure. `noWrite` is an instruction, not an invented Claude frontmatter option. `allowed-tools` grants tool access; it does not itself make Bash read-only.

1. Read `CLAUDE.md` and `README.md`. Confirm this isolated project is the working directory and the project hook is loaded; stop if that cannot be verified.
2. For the local demonstration use exactly one of the hook's fixed commands:
   - `bash "AI Assignment/tf-drift-check.sh" --fixture fixtures/clean.json --report .review-data/current-report.txt`
   - `bash "AI Assignment/tf-drift-check.sh" --fixture fixtures/detected.json --report .review-data/current-report.txt`
   A human must first create `.review-data/` and archive/remove any old current report outside this workflow. Never overwrite evidence or chain commands.
3. Alternatively inspect `reports/drift-detected-report.txt` or `reports/resolved-report.txt`. These are historical **synthetic fixtures only**, not a live baseline. Do not relabel them as fresh evidence.
4. Explain mode, timestamp, source hash, status, affected policy categories, unknowns, and limits. Cite findings from the report and known synthetic fixture only. FAIL is not permission to repair automatically; WARN is not safe. Missing, malformed, stale, incomplete or unsupported evidence is not approval.
5. Request human review of any recommendation. Never run `terraform apply`, `terraform destroy`, `-auto-approve`, initialization, cloud APIs, or live planning from this Skill. The separate live checker mode requires a trusted project and explicit human authorization and is deliberately absent from this hook's allowlist.
6. After an independently authorized human action, request fresh evidence rather than recycling a prior report. Do not invent a Claude invocation, screenshot, infrastructure change, clean plan, human approval, or publication.

The deterministic checker gathers and classifies evidence. Reasoning explains context and alternatives; it cannot turn synthetic or incomplete evidence into infrastructure assurance. The hook is a local guard, not an OS sandbox or control over human terminals. No real Claude invocation is claimed in this submission.
