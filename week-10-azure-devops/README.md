# Week 10 — Azure DevOps

Learner: **Eze Favour**. Status: **A1–A4 source preparation and partial A1 setup delivered; no assignment is complete**.

## Recorded progress — 18 September 2026

- **A1 source:** [manual verification YAML and runbook](self-hosted-agent/README.md), [key-only Azure Terraform adaptation](self-hosted-agent/azure-vm/README.md), read-only checks and offline tests.
- **A1 setup:** private Azure DevOps project `DMI-Week10`, dedicated pool `DMI-Week10-A1`, and an imported assessment repository exist. Definition **1**, `DMI-Week10-A1-VerifyLinuxAgent`, was saved and read back at revision **4**, using `main`, the exact A1 YAML path and the dedicated default queue. No run was initiated. Exact pipeline-only pool authorization, pool-detail verification and a final source/run-history recheck remain pending; the YAML still requires the runtime `poolName` selection.
- **Temporary Azure labs:** the [first pilot receipt](self-hosted-agent/azure-vm/runtime-2026-09-17.json) remains unchanged. A second, separately authorized lab established trusted SSH, verified Ubuntu 22.04/x86_64 and the non-sudo agent account, and verified the published Microsoft agent 5.279.0 package. It did **not** register an agent or start its service. Empty state and exact resource-group/VM/disk/IP absence were verified at **00:29:30 UTC on 18 September**, before expiry. Both labs were cleaned up; their authorizations are retired and neither supplies a current agent host.
- **A2/A3 source:** [pipeline templates, payload/remote checks and runbook](application-pipelines/README.md); **50 offline tests passed**. No application import, application build/test, deployment or live pipeline success is claimed.
- **A4 source:** [manual handoff validator, inventory formatter and pinned-source review](epicbook/README.md); **36 offline tests passed**. Infrastructure, Ansible and both real pipelines are still to be implemented.

These are recorded operational facts and source-validation results, **not submission screenshots or assignment completion**. Private authentication, keys, state, plans and raw execution records are not published. No new cloud operation is authorized by publishing this source.

| Assignment | Source status | Live gate / next dependency | Numbered screenshots |
| --- | --- | --- | --- |
| [1 — Self-hosted Linux agent](assignment-01-set-up-a-self-hosted-linux-agent-for-azure-devops.md) | [Foundation and VM preparation](self-hosted-agent/README.md); manual definition saved | Finish restricted pool permission; fresh bounded lab and private authentication; registration/service, Online agent and successful manual run | 0/7 |
| [2 — Static website](assignment-02-deploy-a-static-website-to-aws-ec2-using-an-azure-devops-cicd-pipeline.md) | [Static pipeline and validation](application-pipelines/README.md) | A1 readiness; personalized Azure Repos app; non-root AWS identity, Terraform/Ansible target and trusted SSH connection; automatic deployment and grading retention | 0/5 |
| [3 — React CI/CD](assignment-03-automate-react-app-deployment-using-azure-devops-cicd.md) | [Build/Test/Publish/Deploy template](application-pipelines/README.md) | Authorized app personalization/stale-test correction; separate Terraform/Ansible target; actual build/test, artifact deployment and automatic run | 0/6 |
| [4 — EpicBook dual pipelines](assignment-04-automate-epicbook-deployment-with-dual-pipelines.md) | [Handoff checks and source constraints](epicbook/README.md) | Two repositories, Terraform/remote state, two Azure VMs and private MySQL, runtime/TLS/schema review, idempotent Ansible, both pipelines and live handoff | 0/6 |
| [5 — Read-only failure triage](assignment-05-ai-assisted-azure-devops-dual-pipeline-failure-triage.md) | Brief only; no substitute kit | A4's two healthy pipelines, actual instructor-supplied files, separately authorized Claude use, genuine controlled failure/recovery | 0/12 |

There are **36 numbered screenshot slots**, plus A2's separate unnumbered LinkedIn image. All remain pending. Submission capture and social publication still need separate approval. The [A1 evidence manifest](self-hosted-agent/evidence/manifest.json) records seven empty slots, not substitute evidence. Learner reflections and original completion checklists remain unanswered/unchecked.

## Delivery / run sequence

1. Review the credential-free checks for [A1](self-hosted-agent/README.md#offline-validation), [A2/A3](application-pipelines/README.md#offline-checks) and [A4](epicbook/README.md#credential-free-local-tests). Local test success does not establish cloud or agent readiness.
2. Finish A1's saved-definition/pool verification in the approved browser context. Renew the [scoped lab authorization](self-hosted-agent/README.md#1-fresh-authorization-and-vm-choice) before paying for a new host; use fresh invocation records, identity/capacity/price checks and a bounded cleanup window. Never reuse an expired approval or assume an earlier resource exists.
3. Follow A1's human-operated runbook: independently authenticate the new host, verify its account/package, privately enter short-lived authentication, register, install/verify the service, prove Online, then run the exact manual pipeline with `poolName: DMI-Week10-A1`. Never expose a PAT in chat, arguments, environment, logs or screenshots.
4. Deliver A2 and A3 on separately approved targets using their reviewed source and real application tests. A2 requires AWS and an agreed grading window; the temporary Azure-agent allowance does not cover either deployment target.
5. Implement and verify A4's infrastructure and application pipelines, protected state, database and manual handoff before attempting A5 with the real supplied kit. Do not fabricate incidents, reports or recovery.
6. Capture genuine, readable evidence only after approval; review it for secrets, match every original slot, and complete human reflections/publication only when actually performed.

The original briefs remain the source of requirements. A1 contains only a clearly delimited preparation notice; its seven screenshot requirements, eight unchecked checklist entries, and unanswered notes are preserved.
