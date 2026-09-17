# Week 10 — Azure DevOps

Learner: **Eze Favour**. Status: **A1 foundation and temporary Azure VM pilot delivered; no assignment is complete**.
A separately authorized 2026-09-17 pilot provisioned an isolated VM and verified its deletion, disk/IP/resource-group absence and empty Terraform state before the approved deadline. [Actual run details](self-hosted-agent/azure-vm/README.md) distinguish VM provisioning from the still-unverified SSH host, PAT/pool, agent, pipeline, screenshots and learner reflections. **No Week 10 VM remains from this pilot.**

| Assignment | Source status | Live gate / next dependency | Numbered screenshots |
| --- | --- | --- | --- |
| [1 — Self-hosted Linux agent](assignment-01-set-up-a-self-hosted-linux-agent-for-azure-devops.md) | [Foundation](self-hosted-agent/README.md) plus [tested key-only Terraform and cleaned VM pilot](self-hosted-agent/azure-vm/README.md) | Fresh lab window, authenticated host fingerprint/SSH, organization and private PAT/pool handoff, registration/service, Online agent and successful manual run | 0/7 |
| [2 — Static website](assignment-02-deploy-a-static-website-to-aws-ec2-using-an-azure-devops-cicd-pipeline.md) | Brief only | A1 readiness; Azure Repos, approved AWS host and SSH CI/CD setup | 0/5 |
| [3 — React CI/CD](assignment-03-automate-react-app-deployment-using-azure-devops-cicd.md) | Brief only | A1 readiness; approved Build/Test/Publish/Deploy workflow and target | 0/6 |
| [4 — EpicBook dual pipelines](assignment-04-automate-epicbook-deployment-with-dual-pipelines.md) | Brief only | Two external repositories, private MySQL, remote Terraform state and manual infrastructure-to-app handoff | 0/6 |
| [5 — Read-only failure triage](assignment-05-ai-assisted-azure-devops-dual-pipeline-failure-triage.md) | Brief only | A4's two healthy pipelines and the actual supplied failure kit; no invented incidents | 0/12 |

There are **36 numbered screenshot slots**, plus A2's separate unnumbered LinkedIn image. All remain pending. Social publication and GUI capture are not authorized. The [A1 evidence manifest](self-hosted-agent/evidence/manifest.json) records seven empty slots, not substitute evidence.

## Delivery / run sequence

1. Review A1's [offline scope and local test command](self-hosted-agent/README.md#offline-validation). Local tests do not establish cloud or agent readiness.
2. Review the [VM pilot's outcome and remaining gates](self-hosted-agent/azure-vm/README.md), then renew the [scoped authorization](self-hosted-agent/README.md#1-fresh-authorization-and-vm-choice). Do not assume any earlier resource still exists.
3. Only after fresh approval, a human follows the A1 runbook: dedicated pool and short-lived PAT, isolated Ubuntu account, verified package, interactive registration, service verification, and manual pipeline.
4. Capture genuine evidence only after separate capture approval; review for secrets and match it to each original slot. Leave checkboxes and notes unanswered until the learner actually completes them.
5. Prepare A2/A3 next; prepare A4's two pipelines before attempting A5. This delivery implements none of A2–A5.

The original briefs remain the source of requirements. A1 contains only a clearly delimited preparation notice; its seven screenshot requirements, eight unchecked checklist entries, and unanswered notes are preserved.
