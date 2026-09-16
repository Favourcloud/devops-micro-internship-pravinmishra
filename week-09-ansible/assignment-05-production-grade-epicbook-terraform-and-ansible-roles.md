# Assignment 5 — Production-Grade EpicBook: Terraform + Ansible Roles (Azure or AWS)

Part of the DevOps Micro Internship (DMI) Cohort 3 with Agentic AI

---

## Purpose

In this assignment, you will deploy the EpicBook web application on a cloud VM provisioned with Terraform (Azure or AWS — pick one) and configured through reusable Ansible roles (`common`, `nginx`, `epicbook`) orchestrated by one playbook, using group variables, templates, and handlers, with a verified idempotent second run.

---

## Preparation status — 16 September 2026

Azure code and the `common` → `nginx` → `epicbook` roles are prepared in
[`epicbook-prod`](./epicbook-prod/README.md), with local validation recorded in its
[evidence manifest](./epicbook-prod/evidence/assignment-05-manifest.json).
This is **preparation, not a completed cloud deployment**. The instructor's pinned
EpicBook is a Node/Express/Sequelize/MySQL application, not a static website. The
project includes an opt-in single-VM Node 22/MySQL 8 runtime, secret-safe service
configuration, and guarded SQL initialization; the default deliberately returns
503 until runtime installation is explicitly approved.

Local syntax, lint, mock infrastructure tests and source compatibility checks do
not prove provisioning, SSH, database operation, public HTTP 200 or second-run
idempotency. All **15 numbered screenshots**, the published LinkedIn post and the
video reflection remain pending. Existing tasks and evidence checklist below are
preserved; no learner action or screenshot is fabricated. See the runbook for
remaining approval, compatibility and production-hardening gates.

# Task 1 — Set Up Folder Layout

## Goal

Create the `epicbook-prod` project with `terraform/azure` or `terraform/aws`, `ansible/inventory.ini`, `ansible/site.yml`, `ansible/group_vars/web.yml`, and the `common`, `nginx`, and `epicbook` role directories.

### Evidence

#### Screenshot 1 — Terminal or editor showing the complete `epicbook-prod` project tree

Add your screenshot here.

---

# Task 2 — Terraform (Pick One: Azure or AWS)

## Goal

Provision one secure Ubuntu 22.04 VM with SSH key authentication, inbound SSH (22) and HTTP (80), and `public_ip`/`admin_user` outputs, on your chosen cloud.

### Evidence

#### Screenshot 2 — Terminal showing successful `terraform apply` and `terraform output` with `public_ip` and `admin_user`

Add your screenshot here.

---

#### Screenshot 3 — Terraform code or cloud console showing inbound rules for ports 22 and 80

Add your screenshot here.

---

# Task 3 — Ansible Inventory

## Goal

Create the `[web]` inventory using the Terraform `public_ip` and `admin_user` outputs, and verify passwordless SSH and `ansible ping`.

### Evidence

#### Screenshot 4 — Terminal showing the successful passwordless SSH hostname check

Add your screenshot here.

---

#### Screenshot 5 — Editor or terminal showing `inventory.ini` and a successful Ansible ping

Add your screenshot here.

---

# Task 4 — Create site.yml (Role Orchestration)

## Goal

Create `site.yml` invoking the `common`, `nginx`, and `epicbook` roles in that exact order.

### Evidence

#### Screenshot 6 — Editor showing `ansible/site.yml` with the three roles in the required order

Add your screenshot here.

---

# Task 5 — Role: common

## Goal

Create `roles/common/tasks/main.yml` to update apt, upgrade packages, install baseline packages (`git`, `curl`, `unzip`, `software-properties-common`), with optional SSH hardening applied only after key-based access is confirmed.

### Evidence

#### Screenshot 7 — Editor showing `roles/common/tasks/main.yml`

Add your screenshot here.

---

# Task 6 — Role: nginx

## Goal

Create the `nginx` role to install Nginx, deploy the `epicbook.conf.j2` template to `/etc/nginx/sites-available/epicbook`, enable the site, remove the default site, and reload via handler.

### Evidence

#### Screenshot 8 — Editor showing the Nginx role tasks, handler, and `epicbook.conf.j2` template

Add your screenshot here.

---

#### Screenshot 9 — Terminal showing `/etc/nginx/sites-available/epicbook` and a successful Nginx configuration test

Add your screenshot here.

---

# Task 7 — Role: epicbook

## Goal

Create the `epicbook` role to clone the repository to `{{ app_dest }}`, set ownership/permissions using group variables, and notify the Nginx reload handler on change.

### Evidence

#### Screenshot 10 — Editor showing `roles/epicbook/tasks/main.yml`

Add your screenshot here.

---

# Task 8 — Group Variables

## Goal

Define `app_repo`, `app_dest`, `app_user`, and `app_group` in `ansible/group_vars/web.yml`.

### Evidence

#### Screenshot 11 — Editor showing `ansible/group_vars/web.yml`

Add your screenshot here.

---

# Task 9 — Run the Playbook

## Goal

Run `ansible-playbook -i inventory.ini site.yml` and confirm `common` → `nginx` → `epicbook` all complete with `failed=0`.

### Evidence

#### Screenshot 12 — Terminal showing the role-based Ansible run and final recap with `failed=0`

Add your screenshot here.

---

# Task 10 — Verify

## Goal

Confirm the EpicBook site loads with HTTP 200, inspect the Nginx configuration, and rerun the playbook to confirm the second run is mostly OK/UNCHANGED with `failed=0`.

### Evidence

#### Screenshot 13 — Browser showing the EpicBook site with the public IP visible

Add your screenshot here.

---

#### Screenshot 14 — Terminal showing HTTP 200 and the Nginx site-file snippet

Add your screenshot here.

---

#### Screenshot 15 — Terminal showing the idempotent second Ansible run with mostly OK/UNCHANGED and `failed=0`

Add your screenshot here.

---

### Notes

Describe an issue you faced and how you fixed it, what you learned, any security issues you identified, and your production remediation plan.

Preparation notes (AI-assisted; not a claim of firsthand learner deployment):

- Source inspection found that the referenced EpicBook uses server-rendered
  Handlebars, Sequelize, MySQL and port 8080. Serving its checkout as a static web
  root would neither run the application nor safely protect its configuration.
  The prepared role keeps source outside Nginx's document root and uses a reverse
  proxy only when runtime installation is explicitly enabled.
- Local validation encountered shared-disk exhaustion while extracting tools.
  Only disposable task-owned downloads were removed; the existing provider cache
  was reused read-only and the successful checks were rerun. Ansible's local RPC
  server also failed with a long macOS temporary path; short, uniquely allocated
  temporary paths fixed the guard tests without changing the controller.
- Runtime verification and the learner's own challenge/fix reflection are still
  pending. The runbook records remaining risks: HTTP without TLS, aging upstream
  dependencies, database privileges needed by automatic schema synchronization,
  same-VM failure coupling, backups, and unverified live idempotency. These must
  not be described as resolved production concerns.
- GitHub Copilot assisted source research, code preparation and local tests.
  This does not substitute for genuine Claude Code evidence or a human-applied
  change in Assignment 6.

---

# LinkedIn Post (Required)

## Goal

Publish a LinkedIn post describing the Terraform + Ansible roles deployment (cloud chosen, role structure, Nginx deployment, idempotency result), and add a 4–6 line video reflection covering one challenge/fix, security issues observed, and your production remediation plan.

## Evidence

#### LinkedIn Post URL

Paste your LinkedIn post URL here:

`Add your URL here`

---

#### Screenshot — Published LinkedIn post

Add your screenshot here.

---

#### Video reflection screenshot

Add your screenshot here.

---

# Submission Instructions

- Add all required screenshots in your submission
- Do not expose private keys, credentials, tokens, or unrestricted management access

---

# Completion Checklist

- [ ] Task 1: `epicbook-prod` project and role structure created (Screenshot 1)
- [ ] Task 2: Cloud VM provisioned with Terraform (Screenshots 2–3)
- [ ] Task 3: Passwordless SSH and Ansible ping verified (Screenshots 4–5)
- [ ] Task 4: `site.yml` orchestrates roles in common → nginx → epicbook order (Screenshot 6)
- [ ] Task 5: `common` role created (Screenshot 7)
- [ ] Task 6: `nginx` role, template, and handler created (Screenshots 8–9)
- [ ] Task 7: `epicbook` role created (Screenshot 10)
- [ ] Task 8: Group variables defined (Screenshot 11)
- [ ] Task 9: Playbook run successfully with `failed=0` (Screenshot 12)
- [ ] Task 10: Site verified and idempotent rerun confirmed (Screenshots 13–15)
- [ ] Reflection and security remediation notes written (Notes)
- [ ] LinkedIn post and video reflection submitted
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
