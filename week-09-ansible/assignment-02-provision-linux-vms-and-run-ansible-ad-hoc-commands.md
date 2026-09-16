# Assignment 02 — Provision Linux VMs with Terraform and Run Ansible Ad-Hoc Commands

Part of the DevOps Micro Internship (DMI) with Agentic AI

**Learner:** Eze Favour. **Choice:** Azure only, four Ubuntu 22.04 VMs (`web1`, `web2`, `app1`, `db1`).

**Submission status: CODE PREPARATION — NOT CLOUD-COMPLETE.** Terraform and local inventory tests are implemented; no real public IPs, apply, SSH, remote ad-hoc results or A2 screenshots are claimed. The coordinator relayed a shared US$5 temporary-cloud budget approval, with at most US$2 for A2+A3. Historical B1s read-only plans proposed 23 creates and no updates/deletes but must not be executed; the approved D2lds_v6 replacement requires a new sealed plan, A5 pilot and exact-plan review before apply. The coordinator selected Azure after the allowed non-root AWS identity lacked EC2 permissions; no escalation was attempted. The historical enrollment expired at `2026-09-16T13:30Z`. Assignment 3 will reuse web1/web2, not add servers.

Copilot assisted implementation, source review, local validation and the technical explanations below. They are not invented learner actions or personal experience. The learner must review the answers and add genuine firsthand reflection after authorized execution. See the [runbook](ansible-adhoc-lab/README.md) and [17-slot screenshot manifest](screenshots/assignment-02-manifest.json). Every screenshot and LinkedIn slot remains pending; original assignment requirements are retained.

---

## Purpose

In this assignment, you will use Terraform to provision three or four Ubuntu Linux Virtual Machines on either Microsoft Azure or Amazon Web Services.

You will configure SSH key-based authentication, organize the servers using a custom Ansible inventory, and run Ansible ad-hoc commands across individual hosts and inventory groups.

---

# Task 1 — Create the Multi-Host Lab Structure

## Goal

Create a separate project directory for the multi-host lab and prepare the Terraform, Ansible, and documentation files.

This project will use the Git repository and Ansible controller prepared in Assignment 01.

### Evidence

#### Screenshot 1 — Terminal showing the complete `ansible-adhoc-lab` project structure

**PENDING — Screenshot 1.** Genuine screenshot not captured; local checks do not substitute for an image. Show the complete reviewed source layout, not private cache/state files. Capture guidance: [manifest slot 1](screenshots/assignment-02-manifest.json).

---

#### Screenshot 2 — Terminal showing `git status --short` with the new project files and updated `.gitignore`

**PENDING — Screenshot 2 (historical evidence not captured).** The initial new files are already committed. Do not reset, untrack or manufacture a dirty status to recreate this moment. An honestly labelled `git show --stat` can provide supplemental history, but does **not** fulfill the requested initial `git status --short` screenshot. Capture guidance: [manifest slot 2](screenshots/assignment-02-manifest.json).

---

### Notes

Created the required Terraform, Ansible, helper, test and README files. Ignore rules are project-local to avoid changing the repository root or Assignment 1. Screenshot capture is still pending.

---

# Task 2 — Create the Terraform Configuration

## Goal

Create the Terraform configuration required to provision three or four Ubuntu Linux VMs on your selected cloud platform.

Complete only one option:

- Option A — Microsoft Azure
- Option B — Amazon Web Services

Do not configure both providers for this assignment.

### Evidence

#### Screenshot 3 — Terraform configuration showing the three or four server roles and the `for_each` or `count` implementation

**PENDING — Screenshot 3.** Genuine screenshot not captured; local checks do not substitute for an image. Show web1, web2, app1, db1 and for_each. Capture guidance: [manifest slot 3](screenshots/assignment-02-manifest.json).

---

#### Screenshot 4 — Terraform configuration showing SSH restricted to the controller IP and HTTP allowed only for web hosts

**PENDING — Screenshot 4.** Genuine screenshot not captured; local checks do not substitute for an image. Show controller /32 SSH, web-only /32 HTTP and explicit deny-all-other inbound. Capture guidance: [manifest slot 4](screenshots/assignment-02-manifest.json).

---

#### Screenshot 5 — Terraform output configuration showing how public IP addresses are associated with the server roles

**PENDING — Screenshot 5.** Genuine screenshot not captured; local checks do not substitute for an image. Show public_ips role mapping and only two web_urls. Capture guidance: [manifest slot 5](screenshots/assignment-02-manifest.json).

---

### Notes

Selected Azure only at the coordinator's direction. The approved replacement is four **nonzonal Standard_D2lds_v6** Ubuntu 22.04 hosts (eight vCPUs total), explicit NVMe controllers and the pinned Canonical Gen2 image `22.04.202608060`. Managed OS disks remain 32 GiB Standard_LRS; ephemeral local disks are not used for application data. The hosts retain for_each, dedicated networking, controller-only SSH, web-only HTTP, existing public-key authentication and role-keyed outputs. AzureRM stays pinned to 4.47.0. No second cloud provider or extra A3 hosts are configured. A5's pilot and coordinator review of A2's new sealed plan must precede any apply.

---

# Task 3 — Provision the Infrastructure with Terraform

## Goal

Initialize and validate the Terraform configuration, review the execution plan, provision the selected three or four VMs, and retrieve their public IP addresses.

### Evidence

#### Screenshot 6 — Final `terraform apply` output showing `Apply complete`

**PENDING — Screenshot 6.** No authorized completed cloud/SSH/deployment run or genuine screenshot yet; exact plan and execution gates apply. Capture the genuine Apply complete summary only after separate plan/apply approval. Capture guidance: [manifest slot 6](screenshots/assignment-02-manifest.json).

---

#### Screenshot 7 — `terraform output public_ips` showing the role-to-IP mapping for all three or four VMs

**PENDING — Screenshot 7.** No authorized completed cloud/SSH/deployment run or genuine screenshot yet; exact plan and execution gates apply. Show all four role mappings; redact actual public IPs consistently if desired. Capture guidance: [manifest slot 7](screenshots/assignment-02-manifest.json).

---

#### Screenshot 8 — Azure Portal or AWS Management Console showing all three or four VMs in the `Running` state, with their role-based names visible

**PENDING — Screenshot 8.** No authorized completed cloud/SSH/deployment run or genuine screenshot yet; exact plan and execution gates apply. Show all four role-based names and Running status, with subscription/account metadata hidden. Capture guidance: [manifest slot 8](screenshots/assignment-02-manifest.json).

---

### Notes

Backend-disabled init, validate and seven mocked plan tests pass for the revised D2lds_v6/NVMe/pinned-image configuration. The historical B1s read-only plans proposed 23 creates and zero updates/deletes, but are preserved **for evidence only, not execution**. A fresh identity-sealed plan bound to the revised source, a successful A5 pilot and coordinator approval are required before A2 apply. See [sanitized validation](ansible-adhoc-lab/validation.json). No apply, Running-state screenshot or real role-to-IP output is claimed. A2+A5 together would exhaust the reviewed ten-core family/regional quota. A2+A3's two-hour estimate is **US$1.60812 including US$0.50 contingency**, below the US$2 allocation; this is not a guaranteed bill cap.

---

# Task 4 — Verify SSH Key-Based Access

## Goal

Verify that each managed VM can be accessed from the Ansible controller using SSH key-based authentication.

### Evidence

#### Screenshot 9 — Terminal showing successful SSH hostname output from all VMs

**PENDING — Screenshot 9.** No authorized completed cloud/SSH/deployment run or genuine screenshot yet; exact plan and execution gates apply. After authenticated fingerprint review, show actual hostname output from every VM. Capture guidance: [manifest slot 9](screenshots/assignment-02-manifest.json).

---

### Notes

Use the existing loaded SSH identity as azureuser. Before SSH, compare host-key fingerprints from authenticated boot diagnostics against key scans, storing verified entries only in the task-local known_hosts. No global SSH changes or key generation are needed. Live SSH remains pending.

---

# Task 5 — Create the Custom Ansible Inventory

## Goal

Create an Ansible inventory file that groups the managed VMs by role.

The inventory allows Ansible to run commands against all servers, or only specific groups such as `web`, `app`, or `db`.

### Evidence

#### Screenshot 10 — `inventory.ini` showing the `web`, `app`, and `db` groups

**PENDING — Screenshot 10.** Genuine screenshot not captured; local checks do not substitute for an image. Label UNCONFIGURED template explicitly. Once authorized, separately capture the generated inventory.local.ini with real addresses redacted; never replace the tracked template. Capture guidance: [manifest slot 10](screenshots/assignment-02-manifest.json).

---

#### Screenshot 11 — Output of `ansible-inventory -i inventory.ini --graph`

**PENDING — Screenshot 11.** Genuine screenshot not captured; local checks do not substitute for an image. Show web/app/db membership; graph of .invalid template names is not connectivity evidence. Live counterpart uses inventory.local.ini. Capture guidance: [manifest slot 11](screenshots/assignment-02-manifest.json).

---

### Notes

The required inventory.ini exists with web/app/db groups and intentionally unresolvable .invalid names. Its graph was checked locally. Explicit rendering from Terraform public_ips creates ignored inventory.local.ini with mode 0600; only that generated inventory is used for approved live commands. A3 selects the same web1/web2 addresses.

---

# Task 6 — Run Ansible Ad-Hoc Commands

## Goal

Run Ansible ad-hoc commands from the controller to verify connectivity, check server information, and manage packages and services across inventory groups.

This task proves that the inventory is working and that Ansible can control multiple managed VMs without writing a playbook.

### Evidence

#### Screenshot 12 — Output of `ansible all -i inventory.ini -m ping`

**PENDING — Screenshot 12.** No authorized completed cloud/SSH/deployment run or genuine screenshot yet; exact plan and execution gates apply. Show SUCCESS/pong for all four real managed hosts. Capture guidance: [manifest slot 12](screenshots/assignment-02-manifest.json).

---

#### Screenshot 13 — Output of `ansible all -i inventory.ini -m command -a "uptime"`

**PENDING — Screenshot 13.** No authorized completed cloud/SSH/deployment run or genuine screenshot yet; exact plan and execution gates apply. Show uptime from all four real managed hosts. Capture guidance: [manifest slot 13](screenshots/assignment-02-manifest.json).

---

#### Screenshot 14 — Output of `ansible web -i inventory.ini -m apt -a "name=nginx state=present update_cache=yes" --become`

**PENDING — Screenshot 14.** No authorized completed cloud/SSH/deployment run or genuine screenshot yet; exact plan and execution gates apply. Show actual apt result for web1/web2 with become. Capture guidance: [manifest slot 14](screenshots/assignment-02-manifest.json).

---

#### Screenshot 15 — Output of `ansible web -i inventory.ini -m service -a "name=nginx state=started enabled=yes" --become`

**PENDING — Screenshot 15.** No authorized completed cloud/SSH/deployment run or genuine screenshot yet; exact plan and execution gates apply. Show Nginx started and enabled on both web hosts. Capture guidance: [manifest slot 15](screenshots/assignment-02-manifest.json).

---

#### Screenshot 16 — Output of `ansible all -i inventory.ini -m apt -a "name=htop state=present update_cache=yes" --become`

**PENDING — Screenshot 16.** No authorized completed cloud/SSH/deployment run or genuine screenshot yet; exact plan and execution gates apply. Show actual htop package result for every host with become. Capture guidance: [manifest slot 16](screenshots/assignment-02-manifest.json).

---

#### Screenshot 17 — Output of `ansible web -i inventory.ini -m command -a "systemctl is-active nginx"`

**PENDING — Screenshot 17.** No authorized completed cloud/SSH/deployment run or genuine screenshot yet; exact plan and execution gates apply. Show active from both web hosts. Capture guidance: [manifest slot 17](screenshots/assignment-02-manifest.json).

---

### Notes

The runbook and fixed wrapper include all six required ad-hoc operations with fully qualified builtin modules. Privilege escalation is used only for package/service changes. Tests cover command construction and rejection before execution; no SUCCESS/pong, remote apt/service result or Nginx active result is claimed.

---

# LinkedIn Post Required

## Evidence

#### LinkedIn Post URL

Paste your LinkedIn post URL here:

**PENDING — not published; separate authorization required.**

---

#### Screenshot — Published LinkedIn post

**PENDING — LinkedIn screenshot.** Publication is not authorized and no post exists. Only a genuine separately approved published post may satisfy this slot.

---

# Assignment Questions

Answer the following in your own words:

**1. What is the purpose of an Ansible inventory file?**

An inventory names the managed hosts, associates connection settings with them, and groups them so a command can target all hosts or a role. The tracked inventory here is deliberately unconfigured; only the explicitly generated local inventory contains approved real addresses.

---

**2. What is the difference between the `web`, `app`, and `db` groups in your inventory?**

`web` contains web1 and web2 and receives Nginx/HTTP tasks. `app` contains app1 and `db` contains db1; these are organizational roles only, not evidence that application or database software is installed. All four receive connectivity, uptime and htop checks.

---

**3. What does the Ansible `ping` module verify?**

Ansible ping verifies that the controller can authenticate over the configured SSH transport, run the Python-based module on the host, and receive pong. It is not ICMP ping and does not prove Nginx or HTTP content is healthy.

---

**4. Why do package installation commands require `--become`?**

Installing packages and changing system services need root privileges on Ubuntu. `--become` asks Ansible to escalate the existing SSH user for those tasks instead of connecting as root. Read-only uptime/status tasks do not request escalation.

---

**5. When would you use an ad-hoc command instead of a playbook?**

Use an ad-hoc command for a small, one-off operation such as checking uptime or service status across a group. Use a playbook for a repeatable ordered workflow with multiple tasks, assertions and handlers, as in Assignment 3.

---

**6. What is one challenge you faced while setting up SSH or inventory, and how did you fix it?**

**Firsthand SSH/inventory reflection: PENDING learner input after authorized execution.** No remote SSH issue has been observed here. A real local engineering issue was preventing sample inventory from being mistaken for live hosts; the solution uses .invalid templates, explicit output validation, exclusive mode-0600 rendering and approval tests. This is an AI-assisted implementation note, not an invented learner experience.

---

# Required Files

Confirm that the following files are included in your assignment workspace:

- [x] `ansible-adhoc-lab/README.md`
- [x] `ansible-adhoc-lab/terraform/providers.tf`
- [x] `ansible-adhoc-lab/terraform/main.tf`
- [x] `ansible-adhoc-lab/terraform/variables.tf`
- [x] `ansible-adhoc-lab/terraform/outputs.tf`
- [x] `ansible-adhoc-lab/ansible/inventory.ini`
- [x] Updated `.gitignore`

---

# Submission Instructions

- Add all required screenshots from the tasks.
- Full Name must be visible in required screenshots.
- Mention whether you used Azure or AWS.
- Mention whether you used the three-VM option or four-VM option.
- Add the public IP addresses of the VMs, redacted if preferred.
- Add your `inventory.ini` proof.
- Add a short explanation of what you learned.
- Answer all assignment questions clearly in your own words.
- Add your LinkedIn post URL.
- Do not expose SSH private keys, Terraform state files, cloud credentials, passwords, access keys, secret keys, account IDs, or subscription IDs.

---

# Completion Checklist

Checked items below describe **source implementation/local validation only**, not deployed state. Template inventory checks are not SSH proof. Remote execution, screenshots, learner-owned answers and publication remain incomplete.

- [x] Task 1: `ansible-adhoc-lab` project structure created
- [x] Task 1: `.gitignore` updated for Terraform files
- [x] Task 2: Terraform configuration created
- [x] Task 2: Server roles defined for either three or four VMs
- [x] Task 2: `count` or `for_each` used
- [x] Task 2: SSH restricted to the controller public IP
- [x] Task 2: HTTP allowed only for web hosts
- [x] Task 2: Terraform output maps roles to public IPs
- [x] Task 3: Terraform initialized successfully
- [x] Task 3: Terraform configuration validated
- [ ] Task 3: Terraform apply completed successfully
- [ ] Task 3: All selected VMs are running
- [ ] Task 4: SSH key-based access works for every VM
- [x] Task 5: `inventory.ini` contains `web`, `app`, and `db` groups
- [x] Task 5: `ansible-inventory -i inventory.ini --graph` shows the correct groups
- [ ] Task 6: `ansible all -i inventory.ini -m ping` returns `SUCCESS`
- [ ] Task 6: Ad-hoc commands run successfully
- [ ] Task 6: `--become` was used for package and service tasks
- [ ] Task 6: Nginx is active on the `web` group
- [ ] Screenshots 1–17 are included
- [ ] Assignment questions are answered
- [ ] LinkedIn post published
- [ ] LinkedIn post URL added
- [ ] No sensitive information is exposed

---

## About DMI & CloudAdvisory

DevOps Micro Internship (DMI) is a project-based DevOps program run by Pravin Mishra and The CloudAdvisory, focused on real-world execution, systems thinking, and career readiness.

It helps learners build strong DevOps foundations with hands-on experience.

---

## Resources

- DMI Official Website: [https://dmi.pravinmishra.com?utm_source=github&utm_medium=readme](https://dmi.pravinmishra.com?utm_source=github&utm_medium=readme)
- University: [https://university.pravinmishra.com?utm_source=github&utm_medium=readme](https://university.pravinmishra.com?utm_source=github&utm_medium=readme)
- Discord Community: [https://discord.pravinmishra.com?utm_source=github&utm_medium=readme](https://discord.pravinmishra.com?utm_source=github&utm_medium=readme)
- Blog: [https://dmi.pravinmishra.com/blog?utm_source=github&utm_medium=readme](https://dmi.pravinmishra.com/blog?utm_source=github&utm_medium=readme)
- YouTube Playlist: [https://www.youtube.com/playlist?list=PLFeSNDtI4Cho](https://www.youtube.com/playlist?list=PLFeSNDtI4Cho)
- Pravin Mishra LinkedIn: [https://www.linkedin.com/in/pravin-mishra-aws-trainer/](https://www.linkedin.com/in/pravin-mishra-aws-trainer/)
- CloudAdvisory LinkedIn: [https://www.linkedin.com/company/thecloudadvisory/](https://www.linkedin.com/company/thecloudadvisory/)

---

*This submission is part of DevOps Micro Internship (DMI) — Agentic AI Track.*
