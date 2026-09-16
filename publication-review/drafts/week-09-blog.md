# Before the Servers: Building an Ansible Workstation I Can Reproduce

**Week 09 Assignment 1 — Ansible | Eze Favour**

The first Ansible assignment in my DevOps Micro Internship was about preparing the controller. It was tempting to treat installation as the whole task, but a usable workstation also needs a known interpreter, consistent configuration, SSH readiness, meaningful checks and documentation that another person can follow.

The completed evidence now contains twelve required screenshots and two supporting interpreter images from genuine Visual Studio Code. This is workstation evidence. The later multi-host and cloud-deployment assignments are still pending.

## Reuse the environment and make its assumptions visible

The controller uses an isolated Python environment and 38 pinned package versions. Project-specific settings keep Ansible configuration, linting and local temporary paths predictable. The tools include Ansible, ansible-lint, yamllint and pre-commit.

Instead of reinstalling a working setup for the screenshots, the existing environment was preserved and checked. VS Code's Python interpreter selection was verified in the actual interface, alongside the required Ansible, YAML and Python extensions.

That matters because an editor can display the correct configuration file while still using a different interpreter. A screenshot of settings and evidence of the selected runtime answer different questions.

## Keep the controller's Git hooks separate

The controller has independent Git metadata and its own real pre-commit hook. This avoids changing hooks shared by other coursework through a Git worktree.

The verification used the actual controller hook, not just a disposable test fixture. The original successful installation receipt was retained rather than reinstalling the hook solely to produce a fresh-looking capture. Historical evidence and fresh checks remain distinguishable.

## SSH readiness has a precise boundary

I privately created and loaded a separate Ed25519 identity. The readiness checks confirmed the key's presence, safe permissions, the agent's matching public identity and the expected effective SSH configuration.

Eight readiness checks passed in the genuine VS Code terminal. That establishes local preparation. It does not prove a connection to a remote cloud server, which belongs to a later assignment. Private key contents and passphrases were excluded from the evidence.

## Test outcomes should say what actually ran

The local verification suite passed 25 checks, including three deliberate rejection cases. Those negative cases matter because validation should reject malformed input as well as accept valid files.

Both the check-mode and normal localhost smoke runs reported four successful tasks, zero changes, zero unreachable hosts and zero failures. The real controller pre-commit checks also passed. Source hashes connect the captured evidence to the reviewed project files.

These are local results. They are not a substitute for future remote Ansible ping checks, deployed website verification or a multi-server idempotency test.

## Capture permission is not control permission

The evidence work exposed another practical distinction: permission to record a window does not automatically allow keyboard or mouse control. The authorized Terminal route could locate the Week 09 VS Code window through native macOS APIs, activate it, open the Command Palette, dismiss it and capture the resulting states.

The Codex execution process did not have equivalent desktop access. Copilot continued the authorized genuine VS Code capture work. Keeping those capabilities separate prevented a successful screenshot from being mistaken for proof that every agent could control the desktop.

## What is complete, and what comes next

The workstation evidence was merged through PR #4. The DMI page still displayed earlier missing-evidence findings during the latest check, so I am not claiming a fresh grading result.

Codex helped prepare the controller; Copilot continued the checks and captures; I handled my SSH key privately. Documenting that division is part of making the work reviewable.

The next assignment will provision and manage several Ubuntu servers. For now, the completed result is a reproducible local controller with a documented checklist, working validation and genuine evidence. That is a foundation I can inspect before adding cloud infrastructure and cost.

## Evidence behind this reflection

- [Workstation assignment and screenshots](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/blob/b9f903148c273aee9dab83aa2080580df6b70373/week-09-ansible/assignment-01-set-up-a-team-ready-ansible-development-workstation.md)
- [Onboarding documentation](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/blob/b9f903148c273aee9dab83aa2080580df6b70373/week-09-ansible/ansible-onboarding/README.md)
- [Merged evidence PR #4](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/pull/4)

This work is part of the [DevOps Micro Internship with Agentic AI — Cohort 3](https://dmi.pravinmishra.com/), led by [Pravin Mishra](https://www.linkedin.com/in/pravin-mishra-aws-trainer/). Thank you to the cohort mentors for the learning framework.

[Follow my graded progress](https://dmi.pravinmishra.com/s/Favourcloud.html).
