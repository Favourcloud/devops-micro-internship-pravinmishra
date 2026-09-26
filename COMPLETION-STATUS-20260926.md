# Weeks 08–10 verified delivery — 26 September 2026

Learner: Eze Favour. Execution and writing: Codex-assisted under explicit delegation. The two technical blockers recorded on 25 September are resolved: Week 08 now has real AWS checkout persistence, and Week 10 has fresh Claude Code/Bedrock triage evidence. This is a delivery record, not a claim of full marks or learner-personal execution.

| Week | Verified delivery | Evidence |
|---|---|---|
| 08 | AWS Book Review capstone with login, reviews, TLS, persistence and failover proof; earlier Terraform lab deployment/cleanup; new AWS EpicBook browser checkout matched to RDS and 22 live checks. | [New AWS checkout and cleanup](week-08-terraform/terraform-aws-epicbook/evidence/2026-09-26/README.md), [capstone release](week-08-terraform/terraform-book-review/evidence/deployment-20260925/README.md) |
| 09 | Four-VM Ansible lab, two-host static deployment and cleanup; retained MiniFinance and managed EpicBook; 20 HTTP/SQL checks; actual Claude risk drill/recovery; Medium and LinkedIn publications. | [Verified results and substitutions](week-09-ansible/evidence/2026-09-25/README.md) |
| 10 | Self-hosted agent; successful manual and automatic static/React pipelines; dual-pipeline EpicBook with 19 HTTP/SQL checks; fresh Claude healthy baseline, failed-run diagnosis and recovery; publications. | [New Claude evidence](week-10-azure-devops/evidence/2026-09-26/README.md), [pipeline and application delivery](week-10-azure-devops/evidence/2026-09-25/README.md) |

## Corrections verified on 26 September

- AWS EpicBook now applies a disclosed patch to the pinned instructor source for signed carts and transactional, replay-safe checkout. Browser order 2, cart 3 and subtotal 32.50 match an independent RDS query. Persistence survived a Node restart. All 15 deployed implementation files match the submitted source.
- EC2 bootstrap is gzip-compressed to stay within its payload limit. RDS master-password validation now enforces the API's 24–41-character range, and its TLS parameter uses AWS's normalized value to avoid recurring drift.
- Claude Code used Amazon Bedrock and the registered `/pipeline-triage` skill. It diagnosed controlled failed run 20 before the operator removed exactly the injected step, then verified recovered run 21. Deployment remained skipped on the isolated drill branch.
- A rejected command exposed a stale-report problem. The guard now requires evidence generated during the current session; that invalid first attempt is excluded. The accepted baseline, incident and recovery all used fresh evidence.

[104 passing local tests](validation-20260926.json) cover the affected implementation and guards. The separate AWS live check result contains 22 HTTP/SQL checks. The Week 08 and Week 10 published articles were updated with these results; [publication update receipts](publication-updates-20260926.json) and existing publication links remain in the [progress table](README.md#weekly-progress).

## Cleanup and retained demonstrations

The temporary Week 08 A4 stack's **28 resources and root EBS disk were removed**. Its Terraform state is empty and the pre-existing shared SSH key remains. Its old IP is retired. The separate AWS Book Review capstone stays online until the learner requests cleanup.

[All six retained homepages returned HTTP 200 after cleanup](final-http-checks-20260926.json):

- [Week 08 AWS Book Review](https://xdr0flp20e.execute-api.us-east-1.amazonaws.com/)
- [Week 09 MiniFinance](http://135.116.197.163/)
- [Week 09 EpicBook](http://20.77.180.238/)
- [Week 10 AWS static](http://100.54.219.171/)
- [Week 10 React](http://20.108.9.183/)
- [Week 10 EpicBook](http://51.107.188.80/)

Retained cloud resources and the build agent continue to incur charges under the existing authorization. Synthetic orders involve no payments or shipments.

## Requirements that still need assessor review

- The instructor-supplied Week 10 triage kit could not be found in the reviewed instructor repositories or local files. The original replacement remains disclosed; it is not labeled as the supplied kit.
- Learner-personally-manual actions, original PAT scope/expiry certification, and missing exact native-editor/terminal/address-bar captures are not manufactured. The numbered evidence maps distinguish genuine page captures, historical material and labeled recorded-output viewers.
- Week 09 location and machine-size substitutions remain documented in its evidence. Credit for substitutions and delegated execution belongs to the assessor.
- [Dashboard observed on 26 September](dmi-assessment-20260926.json): Week 08 **190/190**, Week 09 **110/190**, Week 10 **50/170**; 9/14 weeks marked complete. Its last assessment remains dated **25 September**. The publication URLs and template fixes it reports missing are present on verified remote main. A newer external review is required; successful tests and publication do not establish a perfect grade.

[Previous status, retained as history](COMPLETION-STATUS-20260925.md).
