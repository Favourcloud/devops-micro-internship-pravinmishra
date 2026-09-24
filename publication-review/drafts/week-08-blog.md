# Terraform Across AWS and Azure: What the Deployment Evidence Shows

**Week 08 — Terraform | Eze Favour | 24 September 2026**

Week 08 of the DevOps Micro Internship brings together infrastructure as code, application deployment and AI-assisted change review. The repository now includes four verified deployment-and-cleanup runs across AWS and Azure, plus a separate Terraform policy-review experiment. The remaining capstone work is still in progress.

The useful question throughout this work is simple: what does each piece of evidence actually prove? A valid configuration establishes that Terraform can understand the source. A successful apply shows that resources were created. Application checks establish whether the service works. Cleanup needs its own verification.

Codex performed the approved A1–A4 cloud operations under delegation. GitHub Copilot performed the earlier Assignment 6 Terraform operations, and Claude Code supplied its recorded reviews. These operator details are retained in the evidence; they do not establish manual learner execution.

## Four deployments with verified cleanup

**Assignment 1: Azure virtual machine.** Terraform created eight resources, including a dedicated network, public IP, network interface and Ubuntu VM. Azure CLI reported the VM running, and the recorded image, disk and public IP matched the deployment. All 11 required screenshots are present. Terraform then destroyed the eight resources. Independent Azure checks confirmed the resource group and recorded objects were absent, including the VM's OS disk.

**Assignment 2: AWS virtual machine.** The AWS exercise created 11 Terraform resources. Verification covered EC2 health, SSH access, cloud-init, Nginx, public HTTP and the browser-rendered page. This made the result more useful than an instance status alone: the service was tested through the path a visitor would use. All 10 screenshots are present. Terraform destroyed the lab, and 13 exact-resource checks covered the managed resources and additional children such as the root volume and network interface.

**Assignment 3: React on Azure.** The React exercise created eight resources and checked SSH, cloud-init, Nginx, the HTTP response, application assets and single-page application routing. A browser capture recorded the running instructor application. Its original name and date placeholders were retained. All 15 screenshots are present. Terraform destroyed the lab, followed by Azure absence checks that included the OS disk.

**Assignment 4: EpicBook on AWS with private RDS.** The approved run created 28 application resources and one separately managed public-key resource. EC2 ran Node 22.23.3, and RDS ran MySQL 8.4.11 with encrypted storage and TLS. The database contained 53 authors and 54 books. A real browser added “28 Summers” to the cart; its book ID, quantity, $28 price and request time matched the new Cart and Cartbook records. All 29 resources were destroyed and independently checked in a 32.95-minute window. There are 34/35 captures, with the private RDS hostname redacted and other capture limitations documented. The separate checkout/order requirement remains incomplete.

The public addresses in these records are historical: the labs were removed after verification. A1–A3 are documented in merged GitHub deliveries; the new A4 evidence is prepared for review. Their evidence supports the completed runs, rather than a claim that the applications remain online.

## A plan can describe a change that should be rejected

Assignment 6 examined the decision before deployment. Its isolated AWS lab contained one dedicated VPC and a closed, unattached security group. A clean baseline plan reported no changes.

A deliberately risky input was supplied only to planning. It proposed opening SSH to the public internet. The policy checker returned FAIL with one unsafe ingress finding, while AWS read-back still showed zero deployed ingress rules. This was a proposed configuration change, not out-of-band drift: the risky rule never reached AWS.

Claude Code performed genuine clean, risk and final reviews using sanitized reports. Its risk review recommended: “Do not apply this configuration.” A separate native PreToolUse hook test used the fresh FAIL report and blocked an actual apply request before Terraform executed.

The recorded human decision rejected public SSH and kept the security group closed. Subsequent plans reported no changes, the checker found no issues within its defined scope, and the final Claude review referenced the updated evidence. Authorized cleanup removed the security group and VPC, followed by independent absence checks.

All 19 numbered Assignment 6 images are recorded with provenance. The assignment's separate manual learner execution requirement remains open, even though the delegated review experiment and cleanup are documented.

## What remains before Week 08 is complete

The repository currently contains **93 of 118 numbered screenshot slots**, with 25 missing across Assignments 4 and 5. Screenshot coverage is an inventory measure; it does not replace the underlying tasks.

Assignment 4's deployment and cart/database test are verified, but the pinned instructor app lacks an order-creation endpoint. A successful cart action cannot be described as completed checkout. Its learner reflection, mandatory LinkedIn publication and disclosed visual-evidence limits remain open. The new delivery passed 66 Python checks; the prior 22 Terraform mock runs remain supplementary to the actual cloud results.

Assignment 5 still needs the provided Claude starter kit, a reviewed dependency update, genuine Claude/MCP workflow evidence, deployment verification and the learner's own reflections. The earlier source captures do not establish those results.

The practical lesson from the completed work is to maintain a clear chain from configuration to plan, deployment, application verification and cleanup. Automated checks and AI explanations help review that chain. Precise records make it possible to identify what succeeded, what remains unverified and what must happen next.

## Evidence and course credit

- [Azure VM run and cleanup](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/blob/3029c3664ba94874abf040379afa866ca2f67300/week-08-terraform/terraform-azure-vm/evidence/live-run-summary.md)
- [AWS VM run and cleanup](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/blob/3029c3664ba94874abf040379afa866ca2f67300/week-08-terraform/terraform-aws-vm/evidence/live-run-summary.md)
- [Azure React run and cleanup](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/blob/3029c3664ba94874abf040379afa866ca2f67300/week-08-terraform/terraform-react-azure/evidence/live-run-summary.md)
- [EpicBook AWS/RDS run and cleanup](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/blob/cca663ae93202ffb7e7fa3e39122a495b14ff7b0/week-08-terraform/terraform-aws-epicbook/evidence/live-run-summary.md)
- [Terraform review experiment](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/blob/3029c3664ba94874abf040379afa866ca2f67300/week-08-terraform/drift-review/drift-review-summary.md)
- [Remaining Week 08 requirements](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/blob/cca663ae93202ffb7e7fa3e39122a495b14ff7b0/week-08-terraform/completion-audit.md)

This work is part of the [DevOps Micro Internship with Agentic AI — Cohort 3](https://dmi.pravinmishra.com/), led by [Pravin Mishra](https://www.linkedin.com/in/pravin-mishra-aws-trainer/). Thank you to the cohort mentors for their guidance.

[Follow my graded progress](https://dmi.pravinmishra.com/s/Favourcloud.html).
