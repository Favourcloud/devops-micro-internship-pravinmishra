# Assignment 4 — Deploy Mini Finance Project Using Terraform and Ansible

Part of the DevOps Micro Internship (DMI) Cohort 3 with Agentic AI

---

## Purpose

In this assignment, you will provision an Azure VM with Terraform and use Ansible to automate the install, deploy, and verify workflow for the Mini Finance static website — a clean separation between infrastructure and configuration management.

## Submission status — code preparation only (2026-09-16)

The [Mini Finance project and gated runbook](mini-finance/README.md) contain Azure Terraform, an intentionally unconfigured `inventory.ini`, and three Ansible plays. Local Terraform formatting/init/validation and 10 mocked-plan tests passed; 17 Python contract/preflight tests, Ansible syntax check and offline lint passed. Provider initialization accessed HashiCorp downloads, not Azure resources.

**Not deployed:** the user approved a US$5 combined temporary AWS/Azure lab budget with teardown after evidence; the coordinator allocated A4 at most US$1/two hours. After coordinator authorization, a private read-only live Azure plan from infrastructure commit `835b90b041315c76b10b6984448504b0c0d11fd4` succeeded with **8 creates, 0 updates, 0 deletes** in `uksouth`. Actual key content, controller `/32`, identifiers and full plan/logs remain private. Exact-plan review and live allocation capacity remain gates before apply. No apply/destroy, remote SSH, real Ansible deployment, browser verification, remote idempotence run, screenshot capture or LinkedIn publication was performed. All eight numbered screenshots and the LinkedIn screenshot are explicitly pending in the [assignment-specific manifest](screenshots/assignment-04-manifest.json). Existing coursework evidence is not reused.

GitHub Copilot prepared the code, runbook and local tests under user direction; upstream Mini Finance assets remain attributed to their authors and are not vendored here. Learner-authored firsthand reflection remains pending. The original task goals/questions below are retained.

---

# Task 1 — Set Up Folder Layout

## Goal

Create the `mini-finance` project with separate `terraform/` and `ansible/` subdirectories.

### Evidence

#### Screenshot 1 — Terminal or editor showing the complete `mini-finance` project tree

**Pending.** The project tree is prepared; no screenshot has been captured.

---

# Task 2 — Terraform — Azure VM + NSG (Ports 22/80)

## Goal

Provision an Ubuntu 22.04 Standard_B1s VM with a public IP, SSH key authentication, and an NSG allowing SSH (22) and HTTP (80), and output the public IP.

### Evidence

#### Screenshot 2 — Terminal showing the end of a successful `terraform apply`

**Pending.** Requires an authorized, successful Azure apply; none was performed.

---

#### Screenshot 3 — Terminal showing `terraform output public_ip`

**Pending.** No real Azure VM output exists for this preparation; no example IP is presented as real.

---

#### Screenshot 4 — Terraform code or Azure Portal showing NSG inbound rules for ports 22 and 80

**Pending.** Code restricts SSH to one controller IPv4 `/32`, permits HTTP 80, and denies other inbound traffic; no screenshot or deployed NSG is claimed.

---

# Task 3 — Configure Passwordless SSH

## Goal

Connect to the VM with SSH using the injected key and run `hostname` remotely without a password prompt.

### Evidence

#### Screenshot 5 — Terminal showing the successful passwordless SSH hostname check

**Pending.** Requires the actual VM, the existing user's key and independently verified host key. No remote SSH connection was attempted.

---

# Task 4 — Ansible — Multi-Play: Install → Deploy → Verify

## Goal

Create `ansible/inventory.ini` and a three-play `site.yml` that installs Nginx and Git, clones and deploys the Mini Finance repository to `/var/www/html/` with a reload handler, and verifies HTTP 200 from `localhost`.

### Evidence

#### Screenshot 6 — Editor showing `inventory.ini` and the three plays in `site.yml`

**Pending.** Both files are prepared, but the committed inventory is deliberately empty/fail-closed until real outputs are supplied privately. No screenshot was captured.

---

#### Screenshot 7 — Terminal showing `ansible-playbook -i inventory.ini site.yml` with HTTP 200, assertion OK, and no failures

**Pending.** Local syntax/lint and no-SSH negative tests are not a real deployment, HTTP 200, successful remote recap or idempotence result.

---

# Task 5 — Test End-to-End Functionality

## Goal

Confirm the Mini Finance site is publicly accessible and correctly served by Nginx.

### Evidence

#### Screenshot 8 — Browser showing the Mini Finance site loaded from `http://<public_ip>` with the URL visible

**Pending.** No deployed public URL or browser verification exists for this preparation.

---

### Notes

Describe an issue you faced and how you fixed it, and what you learned.

**Learner reflection pending.** No firsthand deployment challenge, fix or learning experience is claimed.

**Locally evidenced AI-assisted preparation note:** read-only public upstream inspection found tracked `js/.DS_Store`, documentation and `git_tracking_summary.txt`. The prepared deployment exports only explicit web assets from pinned revision `296334fc27de87bdfcafdad041e41573d8815700`, keeps the Git checkout outside `/var/www/html`, rejects hidden/symlinked assets and denies dot paths in Nginx. Offline tests check these safeguards; live behavior remains unverified. This engineering note does not replace the learner's own reflection after authorized work.

---

# LinkedIn Post (Required)

## Goal

Publish a LinkedIn post about the Terraform + Ansible deployment, mentioning the Azure VM, secure networking, passwordless SSH, Nginx deployment, and HTTP verification, with one challenge you faced and how you fixed it, and one real-world example of this workflow.

## Evidence

#### LinkedIn Post URL

Paste your LinkedIn post URL here:

**Pending — not published.** No LinkedIn URL has been fabricated or submitted.

---

#### Screenshot — Published LinkedIn post showing the text and at least one image or proof

**Pending.** Publication and an authentic screenshot remain manual learner actions after real deployment evidence is available.

---

# Submission Instructions

- Add all required screenshots in your submission
- The `mini-finance` project tree and `inventory.ini` may have the final IP octet masked
- Do not expose private keys or other secrets

---

# Completion Checklist

- [ ] Task 1: `mini-finance` project structure created (Screenshot 1)
- [ ] Task 2: Azure VM and NSG provisioned with Terraform (Screenshots 2–4)
- [ ] Task 3: Passwordless SSH verified (Screenshot 5)
- [ ] Task 4: Ansible install/deploy/verify plays run successfully (Screenshots 6–7)
- [ ] Task 5: Site verified in the browser (Screenshot 8)
- [ ] Reflection notes written (Notes)
- [ ] LinkedIn post published and URL submitted
- [ ] No sensitive data exposed

---

## 📌 About DMI & CloudAdvisory

DevOps Micro Internship (DMI) is a project-based DevOps program run by Pravin Mishra (The CloudAdvisory) focused on real-world execution, systems thinking, and career readiness.

It helps learners build strong DevOps foundations with hands-on experience.

---

## 📌 Resources

- 🌐 DMI Official Website: https://dmi.pravinmishra.com?utm_source=github&utm_medium=readme  
- 🎓 University: https://university.pravinmishra.com?utm_source=github&utm_medium=readme  
- 💬 Discord Community: https://discord.pravinmishra.com?utm_source=github&utm_medium=readme  
- 📝 Blog: https://dmi.pravinmishra.com/blog?utm_source=github&utm_medium=readme  
- ▶️ YouTube Playlist: https://www.youtube.com/playlist?list=PLFeSNDtI4Cho  
- 🔗 Pravin Mishra (LinkedIn): https://www.linkedin.com/in/pravin-mishra-aws-trainer/  
- 🏢 CloudAdvisory (LinkedIn): https://www.linkedin.com/company/thecloudadvisory/

---

*This submission is part of DevOps Micro Internship (DMI) Cohort 3 — Agentic AI Track.*
