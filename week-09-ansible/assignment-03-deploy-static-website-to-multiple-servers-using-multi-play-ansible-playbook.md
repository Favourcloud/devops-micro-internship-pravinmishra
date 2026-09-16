# Assignment 03 — Deploy a Static Website to Multiple Servers Using a Multi-Play Ansible Playbook

Part of the DevOps Micro Internship (DMI) with Agentic AI

---

## Student Details

**Full Name:** Eze Favour

**Cloud Platform Used:** Azure, reusing Assignment 2's web1/web2 (no extra VMs).

**Server 1 URL:** PENDING — no verified deployment/public IP.

**Server 2 URL:** PENDING — no verified deployment/public IP.

**Submission status: CODE PREPARATION — NOT DEPLOYMENT-COMPLETE.** Three plays, source provenance, syntax/lint and loopback-only verification tests are prepared. No managed-host ping, website deployment, remote idempotency, browser screenshots or publication is claimed. The coordinator relayed a shared US$5 temporary-cloud budget approval and at most US$2 for A2+A3; A2's authorized read-only Azure plan succeeded with 23 creates and no updates/deletes, but exact saved-plan approval, capacity and execution window remain gates. The authorized non-root AWS identity lacked EC2 permissions, so the coordinator selected Azure without escalation. The historical enrollment expired at `2026-09-16T13:30Z`.

Copilot assisted implementation, the genuine source download, local checks and these technical explanations. The learner must review the answers and provide firsthand reflection after actual execution. The [11-slot screenshot manifest](screenshots/assignment-03-manifest.json) retains every required screenshot plus LinkedIn; all are pending.

---

## Purpose

In this assignment, you will create a multi-play Ansible playbook to install Nginx, deploy a static website to two Ubuntu servers, and verify that the website is accessible from both servers.

You may use either AWS EC2 instances or Azure Virtual Machines as your managed servers.

---

# Task 1 — Create the Project Structure

## Goal

Create the required folders and files for the Ansible project.

## Evidence

### Screenshot 1 — Terminal or VS Code showing the complete `static-web` project structure

**PENDING — Screenshot 1.** Genuine screenshot not captured; local checks do not substitute for an image. Show complete static-web source structure, not private outputs/caches. Capture guidance: [manifest slot 1](screenshots/assignment-03-manifest.json).

---

# Task 2 — Configure the Ansible Inventory

## Goal

Add both Ubuntu servers to the Ansible inventory.

## Evidence

### Screenshot 2 — Output of `ansible-inventory -i inventory.ini --graph` showing `web1` and `web2`

**PENDING — Screenshot 2.** Genuine screenshot not captured; local checks do not substitute for an image. Show web1/web2 and explicitly label UNCONFIGURED template. After authorization use inventory.local.ini for the real counterpart. Capture guidance: [manifest slot 2](screenshots/assignment-03-manifest.json).

---

## Configuration File

Copy and paste the complete contents of your `inventory.ini` file below:

```ini
# UNCONFIGURED TEMPLATE: .invalid names cannot be managed hosts.
# Render from A2 outputs after approval; never replace this tracked file.
[web]
web1 ansible_host=web1.invalid
web2 ansible_host=web2.invalid

[all:vars]
ansible_user=azureuser
ansible_connection=ssh
ansible_python_interpreter=/usr/bin/python3
lab_inventory_configured=false
ansible_ssh_common_args='-o StrictHostKeyChecking=yes -o ForwardAgent=no'
```

---

# Task 3 — Verify Ansible Connectivity

## Goal

Confirm that the Ansible controller can connect to both servers.

## Evidence

### Screenshot 3 — Ansible ping output showing `SUCCESS` and `pong` for both servers

**PENDING — Screenshot 3.** No authorized completed cloud/SSH/deployment run or genuine screenshot yet; exact plan and execution gates apply. After approval and fingerprint review, show SUCCESS/pong for both real servers. Capture guidance: [manifest slot 3](screenshots/assignment-03-manifest.json).

---

# Task 4 — Download and Personalize the Static Website

## Goal

Download `index.html` to the Ansible controller and personalize the website with your full name.

## Evidence

### Screenshot 4 — Edited `files/index.html` showing the footer line with your full name

**PENDING — Screenshot 4.** Genuine screenshot not captured; local checks do not substitute for an image. Show Eze Favour footer and genuine pinned download provenance; content is not proof of deployment. Capture guidance: [manifest slot 4](screenshots/assignment-03-manifest.json).

---

# Task 5 — Create the Multi-Play Ansible Playbook

## Goal

Create a single Ansible playbook containing separate plays for installation, deployment, and verification.

## Configuration File

Copy and paste the complete contents of your `site.yml` file below:

```yaml
---
- name: Install and start Nginx on the two web hosts
  hosts: web
  gather_facts: false
  become: true
  any_errors_fatal: true
  vars:
    live_execution_approved: false
  pre_tasks:
    - name: Require current approval and a configured two-host inventory before SSH
      ansible.builtin.assert:
        that:
          - live_execution_approved | bool
          - lab_inventory_configured | default(false) | bool
          - groups['web'] | sort == ['web1', 'web2']
          - hostvars[inventory_hostname].ansible_connection == 'ssh'
          - not (hostvars[inventory_hostname].ansible_host | default('') is search('invalid'))
        fail_msg: >-
          Blocked. Obtain current cloud/budget/SSH approval, render the local
          inventory from A2 outputs, and explicitly set live_execution_approved=true.
  tasks:
    - name: Install Nginx with a cached package index
      ansible.builtin.apt:
        name: nginx
        state: present
        update_cache: true
        cache_valid_time: 3600
    - name: Start and enable Nginx
      ansible.builtin.service:
        name: nginx
        state: started
        enabled: true

- name: Deploy the personalized static website
  hosts: web
  gather_facts: false
  become: true
  any_errors_fatal: true
  vars:
    live_execution_approved: false
  pre_tasks:
    - name: Require approval again before deployment
      ansible.builtin.assert:
        that:
          - live_execution_approved | bool
          - lab_inventory_configured | default(false) | bool
          - groups['web'] | sort == ['web1', 'web2']
  tasks:
    - name: Copy the website and its local assets
      ansible.builtin.copy:
        src: "files/{{ item }}"
        dest: "/var/www/html/{{ item }}"
        owner: root
        group: root
        mode: "0644"
      loop:
        - index.html
        - contact.html
        - style.css
      notify: Reload Nginx
  handlers:
    - name: Reload Nginx
      ansible.builtin.service:
        name: nginx
        state: reloaded

- name: Verify both websites from the controller
  hosts: localhost
  connection: local
  gather_facts: false
  become: false
  vars:
    live_execution_approved: false
    ansible_python_interpreter: "{{ ansible_playbook_python }}"
    ansible_remote_tmp: "{{ playbook_dir }}/.ansible/tmp"
  tasks:
    - name: Require approval and complete inventory before controller HTTP requests
      ansible.builtin.assert:
        that:
          - live_execution_approved | bool
          - groups['web'] | default([]) | sort == ['web1', 'web2']
          - hostvars['web1'].lab_inventory_configured | default(false) | bool
          - hostvars['web2'].lab_inventory_configured | default(false) | bool
    - name: Request each deployed home page without proxying or following redirects
      ansible.builtin.uri:
        url: "http://{{ hostvars[item].ansible_host }}/"
        status_code: 200
        return_content: true
        use_proxy: false
        follow_redirects: none
        timeout: 10
      loop: "{{ groups['web'] | sort }}"
      register: website_response
      until: website_response.status | default(0) == 200
      retries: 6
      delay: 5
      when: not ansible_check_mode
    - name: Assert HTTP success and personalized content on each server
      ansible.builtin.assert:
        that:
          - item.status == 200
          - "'Eze Favour' in item.content"
          - "'Week 09 multi-host lab' in item.content"
        success_msg: "{{ item.item }} returned HTTP 200 with Eze Favour and the lab marker."
      loop: "{{ website_response.results | default([]) }}"
      loop_control:
        label: "{{ item.item }}"
      when: not ansible_check_mode
```

---

# Task 6 — Validate the Playbook Syntax

## Goal

Check the playbook for YAML or Ansible syntax errors before running it.

## Evidence

### Screenshot 5 — Successful syntax-check output showing `playbook: site.yml`

**PENDING — Screenshot 5.** Genuine screenshot not captured; local checks do not substitute for an image. Capture real playbook: site.yml output; syntax success is local-only. Capture guidance: [manifest slot 5](screenshots/assignment-03-manifest.json).

---

# Task 7 — Run the Multi-Play Playbook

## Goal

Install Nginx, deploy the website, and verify both servers in one playbook run.

## Evidence

### Screenshot 6 — Play 3 verification showing HTTP `200` for both servers

**PENDING — Screenshot 6.** No authorized completed cloud/SSH/deployment run or genuine screenshot yet; exact plan and execution gates apply. Capture Play 3 successful HTTP 200 and personalized-content assertions for both real web hosts, not loopback tests. Capture guidance: [manifest slot 6](screenshots/assignment-03-manifest.json).

---

### Screenshot 7 — Final play recap showing `unreachable=0` and `failed=0` for `web1`, `web2`, and `localhost`

**PENDING — Screenshot 7.** No authorized completed cloud/SSH/deployment run or genuine screenshot yet; exact plan and execution gates apply. Show genuine recap with unreachable=0 and failed=0 for web1, web2 and localhost. Capture guidance: [manifest slot 7](screenshots/assignment-03-manifest.json).

---

# Task 8 — Verify Idempotency

## Goal

Run the playbook again and confirm that it does not make unnecessary changes.

## Evidence

### Screenshot 8 — Second playbook run showing the play recap with `changed=0`, `unreachable=0`, and `failed=0` for both web servers

**PENDING — Screenshot 8.** No authorized completed cloud/SSH/deployment run or genuine screenshot yet; exact plan and execution gates apply. Show genuine changed=0, unreachable=0, failed=0 for both web hosts; do not alter output. Capture guidance: [manifest slot 8](screenshots/assignment-03-manifest.json).

---

# Task 9 — Test Both Websites Manually

## Goal

Confirm that the static website is accessible from both public IP addresses.

## Evidence

### Screenshot 9 — `curl -I` output showing HTTP `200 OK` from both servers

**PENDING — Screenshot 9.** No authorized completed cloud/SSH/deployment run or genuine screenshot yet; exact plan and execution gates apply. Show HTTP 200 OK from both real endpoints, not fixture addresses. Capture guidance: [manifest slot 9](screenshots/assignment-03-manifest.json).

---

### Screenshot 10 — Browser showing the website from Server 1 with the public IP and your full name visible

**PENDING — Screenshot 10.** No authorized completed cloud/SSH/deployment run or genuine screenshot yet; exact plan and execution gates apply. Show public IP and Eze Favour footer; check CSS and contact/back links. No desktop operation is authorized in code preparation. Capture guidance: [manifest slot 10](screenshots/assignment-03-manifest.json).

---

### Screenshot 11 — Browser showing the website from Server 2 with the public IP and your full name visible

**PENDING — Screenshot 11.** No authorized completed cloud/SSH/deployment run or genuine screenshot yet; exact plan and execution gates apply. Show the second public IP and Eze Favour footer, without broadening controller-only HTTP access. Capture guidance: [manifest slot 11](screenshots/assignment-03-manifest.json).

---

## Website URLs

Add both deployed website URLs below:

```text
Server 1: PENDING — no verified deployment URL.
Server 2: PENDING — no verified deployment URL.
```

---

# Task 10 — Complete the Project README

## Goal

Document how the project works and record what you learned.

## README Content

Copy and paste the complete contents of your `README.md` file below:

````markdown
# Week 09 Assignment 3 — Multi-play static website

**Learner:** Eze Favour. **Platform:** Azure, reusing Assignment 2's `web1` and `web2` Ubuntu 22.04 hosts. **Status:** locally validated code preparation; no remote deployment, URLs, idempotency result, screenshots or LinkedIn post yet.

Copilot assisted the code, source download, technical explanations and local checks. These notes are not a record of learner-operated cloud work. The learner must review them and supply firsthand reflection after genuine execution.

## Files and website source

```text
static-web/
├── .gitignore, .ansible-lint, ansible.cfg
├── inventory.ini                 # safe UNCONFIGURED template
├── site.yml                      # exactly three plays
├── README.md, SOURCE.md
├── files/{index.html,contact.html,style.css}
└── tests/test_site.py
```

The existing course `CodeTrack` website was genuinely downloaded from the learner's GitHub repository at a pinned commit. [SOURCE.md](SOURCE.md) records the exact immutable URLs, original SHA-256 values, verification and reproduction command. `index.html` and the linked contact page use `Eze Favour` and add `Deployed by Eze Favour — Week 09 multi-host lab` to the preserved DMI footer. The stylesheet is unchanged and bundled. No JavaScript, build step or external asset dependency is introduced. The footer is desired artifact content, not a claim of deployment.

## Prerequisites and approval

Use the existing Assignment 1 Ansible controller (validated with Python 3.13.3, Ansible 14.4.0/core 2.21.4 and ansible-lint 26.8.0). Do not recreate its environment, keys or agent. Reuse the four-host [A2 Terraform lab](../ansible-adhoc-lab/README.md); A3 creates **no extra infrastructure**. Standard Ubuntu Nginx's default site serves `/var/www/html`. This playbook is for the dedicated fresh lab, not arbitrary production servers with custom Nginx configuration.

The coordinator has a user-approved combined temporary-cloud budget and an A2+A3 allocation of at most US$2 and two hours after apply. Azure replaces the initial AWS choice because the non-root AWS identity lacks EC2 permissions. A2's explicitly authorized read-only Azure plan succeeded with 23 creates and no updates/deletes; exact saved-plan approval, actual capacity and the execution window remain pending. Expired AWS enrollment is not reused. Do not provision, SSH, run package/service tasks or contact managed HTTP endpoints until authorized. Verify both hosts' fingerprints against authenticated Azure boot diagnostics and store matching keys only in A2's `.local/known_hosts`; the configuration preserves strict checking with no global known-hosts fallback. Current `.invalid` inventory names are intentionally not real endpoints.

A2's renderer creates ignored, mode-0600 `inventory.local.ini` explicitly from real Terraform output after approval. Its `--web-only` option selects the same `web1` and `web2`; never invent IPs or replace tracked `inventory.ini`. No private-key path or credentials are committed. The existing SSH key/agent must already be selected. Approval assertions run before remote modules because fact gathering is off. Each play defaults `live_execution_approved` to false; only an authorized operator may explicitly override it. These are workflow safeguards, not a substitute for authorization.

## The three plays

1. **Install:** target `web`, require approval/configured inventory, install Nginx with `apt state=present` and a 3600-second cache validity, then start and enable the service with privilege escalation.
2. **Deploy:** target only `web`, recheck approval and copy the three static files to `/var/www/html` with root ownership and mode `0644`. A change notifies `Reload Nginx`, which runs once per host at the end of that play. Copying unchanged content does not notify it. Reload is included as the assignment's handler example; changing static content normally does not itself require an Nginx reload.
3. **Verify:** run on `localhost` without escalation using the controller Python. For each web host, `uri` requests its HTTP root directly (no proxy/redirect), requires HTTP 200 and returns content. Assertions require both `Eze Favour` and the unique lab marker, so Nginx's default welcome page cannot pass. Retry handles a short startup delay, not a replacement for troubleshooting. Check mode deliberately skips HTTP validation and is not deployment evidence.

Splitting these concerns makes a failure easier to locate. `copy` stages the reviewed, personalized controller artifact without requiring Git or outbound repository access on managed hosts. Terraform is responsible for infrastructure; Ansible handles packages/content/service state.

## Safe local validation

From `static-web/`, with the existing controller environment on `PATH`:

```bash
export PYTHONDONTWRITEBYTECODE=1
export ANSIBLE_HOME="$PWD/.ansible" ANSIBLE_LOCAL_TEMP="$PWD/.ansible/tmp"
export XDG_CACHE_HOME="$PWD/.cache"
ansible-inventory -i inventory.ini --graph
ansible-playbook -i inventory.ini site.yml --list-hosts
ansible-playbook -i inventory.ini site.yml --syntax-check
ansible-lint --offline --nocolor site.yml
python -m unittest discover -s tests -v
```

SSH multiplexing is disabled with `ControlMaster=no` and `ControlPath=none`, avoiding Unix control-socket path limits in deep worktrees while retaining strict task-local host-key verification. A2's `tests/test_ssh_configuration.py` covers both configurations with real, no-network OpenSSH configuration/socket checks.

The graph shows two unconfigured names; syntax/lint do not SSH. The tests verify source hashes and all relative links, module/handler structure and approval refusal before an SSH sentinel could run. A positive preflight test confirms that an approved, configured SSH inventory reaches a deliberately failing SSH stub, while a local-connection inventory is refused before package tasks; the stub never contacts a host. They execute **only a temporary copy of Play 3** against a loopback HTTP fixture, checking success plus wrong content, missing marker, HTTP 503 and redirect rejection. Temporary inventory values and reduced retry delays are test-only. This proves controller-side logic, **not** reachability or deployment of two cloud servers. No install/deploy module is executed by these tests. Keep the pinned source Git commit available (a shallow clone may need that commit fetched explicitly).

## Approved live execution — pending

First complete A2's approved Terraform apply, fingerprint review, SSH checks and explicit rendering of `static-web/inventory.local.ini`. Keep A2's full local role/IP mapping in `ansible-adhoc-lab/.local/public-ips.json`. From `static-web/`:

```bash
# LIVE WORK ONLY AFTER the coordinator's access/plan/time-window approval.
ansible-inventory -i inventory.local.ini --graph
ansible web -i inventory.local.ini -m ansible.builtin.ping
ansible-playbook -i inventory.local.ini site.yml --syntax-check
mkdir -p .local
set -o pipefail
ansible-playbook -i inventory.local.ini site.yml \
  -e '{"live_execution_approved": true}' | tee .local/first-run.log
# Inspect real Play 3 results and recap before continuing.
ansible-playbook -i inventory.local.ini site.yml \
  -e '{"live_execution_approved": true}' | tee .local/second-run.log
```

Run the second pass immediately with no edits and within the apt cache window. Expected first recap: `unreachable=0` and `failed=0` for web1, web2 and localhost; both controller HTTP/content assertions pass. Expected second recap: also `changed=0` for both web hosts, with no handler executed. These are **expected acceptance criteria**, not recorded outputs. Later package-index refreshes or deliberate content edits may legitimately change state. A2 may already have installed Nginx, so A3's first installation play can legitimately report no changes. Do not edit output to manufacture idempotency.

After the playbook succeeds, validate manually from the approved controller:

```bash
# Read the actual URLs from A2's private local outputs; do not paste them into Git.
python -c 'import json; d=json.load(open("../ansible-adhoc-lab/.local/public-ips.json")); print("Server 1: http://"+d["web1"]); print("Server 2: http://"+d["web2"])'
# Set these shell variables to the real reviewed output values, not placeholders.
# WEB1_IP and WEB2_IP must already be set in this authorized shell.
curl --fail --silent --show-error --noproxy '*' --head "http://${WEB1_IP:?set actual web1 IP}/"
curl --fail --silent --show-error --noproxy '*' --head "http://${WEB2_IP:?set actual web2 IP}/"
```

Open each actual URL in the controller's browser; verify the footer, CSS and contact/back links. HTTP access is restricted to the controller /32, so another viewer will not reach the site. Capture the public IP/full name in genuine browser windows only after privacy review. Do not broaden the Terraform-managed NSGs for a screenshot. If the controller IP changes, update it through Terraform after a fresh authorized plan.

The [A3 manifest](../screenshots/assignment-03-manifest.json) preserves all 11 numbered slots plus the LinkedIn slot. Every slot remains pending. Syntax checks or loopback screenshots do not satisfy cloud screenshots. Do not publish a LinkedIn post without separate approval. Real URLs and published-post links remain pending; redact public IPs in submitted evidence if preferred and never show account IDs, credentials, keys, state or private paths.

## Troubleshooting, learning and cleanup

No managed-host issue has been observed because remote execution has not occurred. During preparation, tests intentionally confirmed that a default Nginx page with HTTP 200 is insufficient: the personalized content assertion rejects it. A shared-disk shortage was resolved by removing only this task's redundant tool/provider copies and reusing verified existing executables; no learner action is invented. These are local engineering notes, not firsthand deployment reflections.

For future authorized runs: SSH denial means review the existing identity, verified fingerprint, controller /32 and instance readiness; do not disable verification. Apt locks can mean Ubuntu initialization is unfinished; wait rather than killing package managers. HTTP failure requires inspecting the Nginx service/default-site configuration, copied files and Terraform-managed web-only rule. If a second run changes files, compare source bytes and destination ownership/mode before claiming idempotency.

After **both A2 and A3** evidence sets are saved, follow A2's exact-state reviewed Terraform destroy workflow within the approved deadline. A3 does not have separate infrastructure to destroy. Confirm no lab resources/volumes remain, keep sanitized cleanup evidence, and retire obsolete local inventories only afterward. All actual cleanup and cloud completion claims remain pending.
````

---

# LinkedIn Post Required

## Evidence

### LinkedIn Post URL

Paste your LinkedIn post URL here:

**PENDING — not published; separate authorization required.**

---

### Screenshot — Published LinkedIn post

**PENDING — LinkedIn screenshot.** Publication is not authorized and no post exists. Only a genuine separately approved published post may satisfy this slot.

---

# Assignment Questions

Answer the following in your own words:

**1. What issue did you face while completing this assignment, and how did you fix it?**

**Firsthand deployment reflection: PENDING learner input.** No managed deployment has occurred. A real local test issue was distinguishing a successful HTTP status from correct content: loopback tests showed that HTTP 200 with the wrong/default page must fail, so verification requires both Eze Favour and the unique lab marker. Shared disk pressure was handled by removing only task-owned duplicate tool artifacts and reusing verified existing executables. These are AI-assisted preparation notes.

---

**2. What did you learn from this assignment?**

Technical takeaway prepared for learner review: Terraform creates the hosts/network, inventory selects the same two web hosts, and Ansible converges package, service and file state before checking HTTP from the controller. Local tests are useful but cannot demonstrate cloud reachability or genuine second-run idempotency. Personal learning reflection remains pending actual learner execution.

---

**3. Why is it useful to split installation, deployment, and verification into separate plays?**

Separate install, deploy and verify plays make target hosts, escalation and failures explicit. Installation prepares Nginx; deployment copies reviewed files and notifies its handler only on changes; verification runs on localhost without remote privilege escalation and checks what the controller can actually access.

---

**4. What is one benefit of using the Ansible `copy` module instead of cloning the website directly from Git on every managed server?**

`copy` distributes the reviewed, personalized controller files identically to both hosts, compares content for changes and sets ownership/mode. Managed hosts need neither Git nor direct repository access, and a moving upstream branch cannot silently change their content during deployment.

---

**5. What does idempotency mean in this assignment?**

Idempotency means rerunning the same playbook against already-correct hosts makes no unnecessary changes. An immediate unchanged second run should show changed=0, unreachable=0 and failed=0 for web1/web2, with no reload handler. apt cache refreshes after the cache window or real source changes can legitimately report changes. Actual remote confirmation is pending, not inferred from syntax/mock tests.

---

**6. What does the Ansible `uri` module verify in Play 3?**

The uri task makes controller-originated HTTP requests to both host addresses, requires status 200, returns the response body and refuses redirects/proxies. Follow-up assertions require Eze Favour and Week 09 multi-host lab, so a default Nginx page is rejected even if its status is 200. These checks are skipped in check mode; only an approved real run proves the deployed endpoints.

---

# Required Files

Confirm that the following files are included in your assignment folder:

- [x] `inventory.ini`
- [x] `site.yml`
- [x] `files/index.html`
- [x] `README.md`

---

# Submission Instructions

- Add all required screenshots in the correct order.
- Full Name must be visible in required screenshots.
- Include both deployed website URLs.
- Paste `inventory.ini`, `site.yml`, and `README.md` as editable text.
- Answer all assignment questions clearly in your own words.
- Add your LinkedIn post URL.
- Do not expose SSH private keys, passwords, cloud account IDs, or other sensitive information.

---

# Completion Checklist

Checked items below describe **source implementation/local validation only**, not deployed state. Template inventory checks are not SSH proof. Remote execution, screenshots, learner-owned answers and publication remain incomplete.

- [x] Task 1: `static-web` folder structure is complete
- [x] Task 2: Both servers are listed under the `[web]` group in `inventory.ini`
- [x] Task 2: Inventory graph shows `web1` and `web2`
- [ ] Task 3: Ansible ping returns `SUCCESS` and `pong` for both servers
- [x] Task 4: `files/index.html` contains your full name
- [x] Task 5: `site.yml` contains three separate plays
- [x] Task 5: Play 1 installs, starts, and enables Nginx
- [x] Task 5: Play 2 deploys `index.html` using the `copy` module
- [x] Task 5: Nginx reload handler is included
- [x] Task 5: Play 3 verifies both web servers from the controller
- [x] Task 6: Playbook syntax check passes
- [ ] Task 7: First playbook run completes with `unreachable=0` and `failed=0`
- [ ] Task 7: URI verification returns HTTP `200` for both servers
- [ ] Task 8: Second playbook run demonstrates idempotency
- [ ] Task 8: Second run shows `changed=0` for both web servers
- [ ] Task 9: Both `curl -I` commands return HTTP `200 OK`
- [ ] Task 9: Website loads from Server 1
- [ ] Task 9: Website loads from Server 2
- [ ] Task 9: Full name is visible on both deployed websites
- [x] Task 10: `README.md` contains all required explanations
- [ ] Screenshots 1–11 are included
- [x] `inventory.ini`, `site.yml`, and `README.md` are pasted as editable text
- [ ] Both website URLs are included
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
