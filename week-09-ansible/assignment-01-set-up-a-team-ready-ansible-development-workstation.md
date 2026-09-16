# Assignment 01 — Set Up a Team-Ready Ansible Development Workstation

Part of the DevOps Micro Internship (DMI) with Agentic AI

---

## Purpose

In this assignment, you will prepare an isolated and reusable Ansible development workstation.

You will install Ansible and supporting tools inside a Python virtual environment, configure VS Code, prepare SSH access, configure Git and pre-commit hooks, and document the complete setup.

This workstation will be used as the Ansible controller in upcoming assignments.

---

## Current status

**Learner:** Eze Favour

**Status:** In progress — the persistent controller and its own Git hooks are configured. SSH readiness passed in the learner’s real Terminal. Twelve genuine screenshots and interactive editor verification remain pending. Historical local evidence is preserved.

Aligned on 15 September 2026 with the [official brief at revision `9b394ef`](https://github.com/pravinmishraaws/devops-micro-internship-pravinmishra/blob/9b394ef8efecd7db1f582995a03665f6f8afc2a4/week-09-ansible/assignment-01-set-up-a-team-ready-ansible-development-workstation.md). The current brief has eight tasks, twelve screenshots, four questions, and explicit required files; it supersedes the older six-task, ten-screenshot version. The previous implementation, validation results and reflection notes were retained rather than treated as a new completed lab.

The [onboarding README](ansible-onboarding/README.md) contains machine details, a 12-step new-machine checklist, safe setup commands and the exact validation procedure. The [local validation record](ansible-onboarding/evidence/local-validation.json) records actual results and source hashes; it is not a substitute for screenshots or remote access evidence.

| Current task | Local work and remaining evidence |
|---|---|
| 1 — Workspace and Git | The project and [ignore rules](ansible-onboarding/.gitignore) exist; empty `inventories/` and `roles/` directories are tracked for later labs. Submission stays in the existing shared worktree. A separate persistent sparse controller clone inside the ignored Week 09 directory is actually on `main` and owns its `.git` directory; screenshot 1 remains pending. This local branch is separate from GitHub’s graded `main`. |
| 2 — Python/Ansible tools | Project-local Python 3.13 environment and [pinned requirements](ansible-onboarding/requirements.txt) are retained. Screenshot 2 pending. |
| 3 — VS Code | [Workspace settings](ansible-onboarding/.vscode/settings.json), [recommendations](ansible-onboarding/.vscode/extensions.json) and [EditorConfig](ansible-onboarding/.editorconfig) are prepared. The official Visual Studio Code CLI installed Ansible 26.8.2, YAML 1.24.0 and Python 2026.4.0 into an isolated profile. Interactive interpreter verification and screenshots 3–4 remain pending. |
| 4 — Ansible defaults | [Configuration](ansible-onboarding/ansible.cfg), localhost inventory and harmless [smoke playbook](ansible-onboarding/playbooks/smoke.yml) are validated. Screenshots 5–6 pending. The brief supplies no literal configuration block; chosen defaults are documented rather than presented as instructor-supplied values. |
| 5 — SSH readiness | The learner created the separate Ed25519 Week 09 key privately and supplied the Terminal result “Identity added”. Its existence and `600` private-file permissions were checked without reading private-key contents. The [SSH verifier](ansible-onboarding/scripts/verify_ssh.py) subsequently ran in the learner’s loaded Terminal and [all eight readiness checks passed](ansible-onboarding/evidence/ssh-readiness-20260916.json). Screenshot 7 remains pending. Existing keys and known-host records are preserved; no remote login or fingerprint validation is claimed. |
| 6 — Git identity and hooks | The persistent controller has repository-local identity Eze Favour / the verified GitHub noreply address, `init.defaultBranch=main`, and an actual installed `.git/hooks/pre-commit`. [Hook configuration](ansible-onboarding/.pre-commit-config.yaml) remains scoped to this project. Screenshot 8 remains pending. Shared hooks and global Git settings were preserved. |
| 7 — Complete workstation test | Local linters, localhost smoke runs and isolated hooks pass. Real SSH readiness and Git setup are verified separately. Screenshots 9–10 and a combined application-window capture remain pending. |
| 8 — README and checklist | Machine details and a 12-step checklist are documented. Screenshots 11–12 pending. |

**Verified locally on 15 September 2026:** all **25 command checks** met their expected result, including three intentional rejection tests (unknown lint option, malformed YAML and an unqualified Ansible module). Both the installed isolated hook and direct hook runner passed. Check mode and normal mode each reported `ok=4 changed=0 unreachable=0 failed=0`. Ansible loaded the project configuration, and both linters passed with compatible settings.

**Fresh validation on 16 September 2026:** the persistent controller passed all **25 command checks**, including the three intentional rejections, and both real installed controller hooks passed. Check and normal modes each reported `ok=4 changed=0 unreachable=0 failed=0`. [Fresh validation and source hashes](ansible-onboarding/evidence/controller-validation-20260916.json), [actual hook run](ansible-onboarding/evidence/controller-hooks-20260916.json), and [workstation status](ansible-onboarding/evidence/workstation-20260916.json) are recorded separately from the unchanged historical record. The wrappers now keep caches and the localhost module temporary directory inside ignored project folders.

Validated versions: Python **3.13.3**, Ansible **14.4.0** / core **2.21.4**, ansible-lint **26.8.0**, yamllint **1.38.0**, pre-commit **4.6.2**. Installed dependencies match the 38-package lock. The record includes sanitized outputs and SHA-256 hashes; rerun `python scripts/verify.py` from the activated project environment to reproduce it.

No cloud resources or charges were introduced. The learner created the new SSH key privately; existing private keys, private host inventory, global Git settings and shared Git hooks were preserved. Required editor extensions were installed only in an isolated Visual Studio Code profile. No incomplete task below is claimed as submission-complete.

The [screenshot manifest](screenshots/assignment-01-manifest.json) tracks all twelve slots as pending until genuine original images and their provenance exist. Native desktop control is unavailable to this assistant session. Screen Recording has now been verified in the learner’s Terminal, and a user-run helper can capture only the isolated genuine VS Code window. Until original images are captured and reviewed, every slot remains pending; CLI output does not substitute for images.

---

# Task 1 — Create and Initialize the Ansible Workspace

## Goal

Create the assignment workspace, initialize a Git repository, prepare the required directories, and add Git ignore rules for local and sensitive files.

### Evidence

#### Screenshot 1 — Terminal showing the `ansible-onboarding` path, `ls -la` output, and `git status` confirming the Git repository is on the `main` branch

Add your screenshot here.

---

# Task 2 — Create the Virtual Environment and Install Ansible Tools

## Goal

Create an isolated Python virtual environment and install Ansible and the required validation tools without modifying the system Python environment.

### Evidence

#### Screenshot 2 — Terminal showing the active `(.venv)` environment, `which ansible`, `ansible --version`, `ansible-lint --version`, `yamllint --version`, and `pre-commit --version`

Add your screenshot here.

---

# Task 3 — Configure VS Code for Ansible Development

## Goal

Configure Visual Studio Code to use the project’s Python virtual environment and provide validation support for Python, YAML, and Ansible files.

### Evidence

#### Screenshot 3 — VS Code Extensions panel showing the Ansible, YAML, and Python extensions installed

Add your screenshot here.

---

#### Screenshot 4 — VS Code showing `.vscode/settings.json` and `.editorconfig` open side by side, with the required settings clearly visible

Add your screenshot here.

---

# Task 4 — Create the Baseline Ansible Configuration

## Goal

Create a reusable `ansible.cfg` file containing the default settings that will be used in this workspace and upcoming Ansible assignments.

### Evidence

#### Screenshot 5 — `ansible.cfg` open in VS Code or another editor, showing the complete configuration

Add your screenshot here.

---

#### Screenshot 6 — Terminal showing `ansible --version` with the `ansible.cfg` path and the output of `ansible-config dump --only-changed`

Add your screenshot here.

---

# Task 5 — Configure SSH Readiness

## Goal

Prepare SSH key authentication, load the key into the SSH agent, configure reusable SSH client settings, and understand how trusted host fingerprints are stored.

### Evidence

#### Screenshot 7 — Terminal showing `ssh-add -l` with the ED25519 key loaded and the SSH configuration verification output

Add your screenshot here.

---

# Task 6 — Configure Git Identity and Pre-commit Hooks

## Goal

Configure your Git identity and install pre-commit hooks that validate YAML and Ansible files before commits are created.

### Evidence

#### Screenshot 8 — Terminal showing your Git full name, Git email, default branch, successful `pre-commit install` output, and `.git/hooks/pre-commit`

Add your screenshot here.

---

# Task 7 — Test the Complete Workstation Setup

## Goal

Verify that Ansible, the linting tools, Git hooks, SSH agent, and Git ignore rules are working correctly.

### Evidence

#### Screenshot 9 — Terminal showing `pre-commit run --all-files` completing successfully

Add your screenshot here.

---

#### Screenshot 10 — Terminal showing `ansible --version` with the project configuration path and `ssh-add -l` with the ED25519 key loaded

Add your screenshot here.

---

# Task 8 — Create the README and Onboarding Checklist

## Goal

Document the completed Ansible workstation setup and create a reusable checklist for preparing another workstation in the future.

### Evidence

#### Screenshot 11 — Terminal showing the final `ansible-onboarding` project structure

Add your screenshot here.

---

#### Screenshot 12 — VS Code Markdown preview showing your full name, project summary, and part of the “New Machine? Do This” checklist

Add your screenshot here.

---

# Assignment Questions

Answer the following in your own words:

**1. What is one feature that makes your workstation setup team-friendly?**

The tools and their dependencies are pinned in a project-local environment, with consistent editor settings and lint hooks. Another learner can reproduce the same checks without relying on a global Ansible installation.

---

**2. What is one pitfall you avoided while completing the setup?**

A Git worktree can share hooks with its parent repository. The actual controller therefore uses a persistent clone with its own Git metadata. Its real hook installation is separate from the disposable fixture used for intentional failure tests. The smoke playbook is restricted to localhost and does not use privilege escalation or contact a cloud host.

---

**3. Why should Ansible be installed inside a Python virtual environment?**

A project-local virtual environment keeps Ansible and its Python dependencies separate from system Python and other projects. The pinned requirements make the tool versions reproducible for teammates, while updates can be tested in isolation. This setup uses its own `.venv` instead of changing global packages.

---

**4. Why must SSH private keys and `.venv/` remain outside version control?**

An SSH private key can authenticate as its owner, so committing it would expose access and leave recoverable copies in Git history. The `.venv/` directory contains local, platform-dependent packages and executable paths, not portable source. Recreate it from the pinned requirements instead of committing it.

---

## Implementation notes

**Proxy/CA:** no custom corporate proxy or CA configuration was added. If a managed network requires one, use the administrator-approved trust configuration; do not disable certificate or SSH host-key verification.

**AI assistance:** Copilot and Codex helped inspect prior work, prepare configuration and run local checks. Codex prepared the persistent controller; the learner created and loaded the SSH key privately. Claims are tied to the recorded command results. Screenshots, remote access and personal workstation configuration have not been invented or marked complete.

---

# Required Files

Confirm that the following files are included in your assignment workspace:

- [x] `README.md`
- [x] `requirements.txt`
- [x] `.gitignore`
- [x] `.editorconfig`
- [x] `.vscode/settings.json`
- [x] `ansible.cfg`
- [x] `.pre-commit-config.yaml`
- [x] `inventories/`
- [x] `roles/`

---

# Submission Instructions

- Add all required screenshots in your submission.
- Full Name must be visible in required screenshots.
- All screenshots must be readable.
- Answer all assignment questions clearly in your own words.
- Do not expose SSH private-key contents, passwords, access tokens, API keys, credentials, private certificates, or other sensitive information.

---

# Completion Checklist

- [x] Task 1: `ansible-onboarding` workspace created
- [x] Task 1: Actual persistent controller Git repository uses the `main` branch
- [x] Task 1: `.gitignore` created
- [x] Task 2: Python virtual environment created
- [x] Task 2: Virtual environment activated
- [x] Task 2: Ansible installed inside `.venv`
- [x] Task 2: `ansible-lint`, `yamllint`, and `pre-commit` installed
- [x] Task 2: `requirements.txt` created
- [x] Task 3: Required VS Code extensions installed in the isolated genuine VS Code profile
- [ ] Task 3: VS Code uses the Python interpreter from `.venv`
- [x] Task 3: `.vscode/settings.json` created
- [x] Task 3: `.editorconfig` created
- [x] Task 4: `ansible.cfg` created
- [x] Task 4: Ansible loads `ansible.cfg` from the project directory
- [x] Task 5: Separate ED25519 SSH key exists
- [x] Task 5: SSH private-key contents have not been read or exposed
- [x] Task 5: SSH key loaded in the learner’s Terminal; public-key match verified by the helper
- [x] Task 5: `~/.ssh/config` contains the reviewed safe Week 09 alias; effective settings verified
- [x] Task 5: `~/.ssh/known_hosts` exists (existence only; no remote fingerprint verification claimed)
- [x] Task 6: Git identity configured in the persistent controller
- [x] Task 6: Pre-commit hooks installed in the persistent controller’s own Git directory
- [ ] Task 7: `pre-commit run --all-files` completes successfully
- [x] Task 8: `README.md` contains your full name and workstation details
- [x] Task 8: “New Machine? Do This” checklist contains 10–12 items
- [ ] All 12 required screenshots are included
- [x] Assignment questions are answered
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
