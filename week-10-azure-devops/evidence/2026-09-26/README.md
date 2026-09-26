# Week 10 — fresh Claude/Bedrock triage, 26 September 2026

Eze Favour’s delegated operator restored the previously authorized AWS session. Claude Code used Amazon Bedrock (`us.anthropic.claude-sonnet-4-6`) and the registered `/pipeline-triage` skill with a guarded, read-only evidence wrapper.

| Phase | Actual evidence | Claude response |
|---|---|---|
| Baseline | Infra11 and app14 on main, HEALTHY | [fresh baseline](claude-baseline.json) |
| Incident | Infra11 healthy; application20 failed before deployment on triage-safe-drill, APPLICATION/INCIDENT | [diagnosis before the fix](claude-incident.json), [real run](failure-run20.png) |
| Recovery | Operator removed exactly the injected failing step; application21 Build succeeded and Deploy stayed skipped, HEALTHY | [fresh recovery](claude-recovery.json), [real run](recovery-run21.png) |

[Saved baseline, incident and recovery reports](../../pipeline-triage/reports/2026-09-26/). The operator copied the incident report before changing the drill branch. Main and the live application were untouched. Claude made no edits or deployment calls. The private gather configuration was reset to main after saving the drill evidence.

An initial attempt added `2>&1`; the exact-command guard rejected it, but Claude read a stale report. That attempt is excluded from accepted evidence. The guard now requires this session’s `DMI_TRIAGE_NOT_BEFORE` timestamp and rejects stale, missing or RUNNING evidence. Seven classifier/guard tests pass, including stale-report and forbidden-redirection regressions. All three accepted sessions ran the exact wrapper and read newly generated reports. The total reported Bedrock cost for the four attempts was about $0.24 before taxes.

These are actual Claude responses and genuine browser page captures, which omit browser chrome. The original replacement kit and delegated operator work remain disclosed; this does not manufacture instructor-supplied files, learner-personal actions or missing native screenshots.

Labeled recorded-output captures: [baseline](claude-baseline-view.png), [incident](claude-incident-view.png), [recovery](claude-recovery-view.png). These display the actual saved Claude response, not a reconstructed terminal.

[Updated numbered Assignment 5 evidence map](screenshot-map.md).
