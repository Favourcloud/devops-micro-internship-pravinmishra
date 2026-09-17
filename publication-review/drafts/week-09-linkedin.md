Before managing several servers with Ansible, I wanted a controller whose setup could be checked and reproduced.

My Week 09 Assignment 1 workstation is now documented with 12 required screenshots and two supporting interpreter images from genuine Visual Studio Code.

The project uses an isolated Python environment with 38 pinned packages, project-specific Ansible configuration, YAML and Ansible linting, and real pre-commit hooks. VS Code is configured to use the project interpreter and the Ansible, YAML and Python extensions.

I created and loaded a separate Ed25519 key privately. Eight SSH-readiness checks passed; these establish local readiness, not a successful remote server login.

The local verification suite passed 25 checks, including three deliberate rejection cases. Both check mode and the normal localhost smoke run reported four successful tasks, zero changes, zero unreachable hosts and zero failures. The actual controller's pre-commit checks also passed.

One practical lesson was that Git worktrees can share hooks. The controller therefore has independent Git metadata, keeping its hooks separate from other coursework. Another was that permission to record a window does not itself provide permission to control it: capture and keyboard delivery were verified separately.

Codex helped prepare the controller, and Copilot continued the checks and genuine VS Code captures. The existing environment and SSH identity were preserved. The evidence is merged through PR #4; a new DMI grading result is not yet verified.

This completes the workstation assignment. The multi-server and deployment labs remain ahead, and no cloud deployment is claimed here.

Thank you to Pravin Mishra, Anjana Muthunayake, Tanisha Borana and Anuradha Iyer for the cohort's guidance.

P.S. This post is part of the DevOps Micro Internship (DMI) with Agentic AI — Cohort 3 — by Pravin Mishra. My graded progress is public: https://dmi.pravinmishra.com/s/Favourcloud.html · Start your DevOps journey: https://dmi.pravinmishra.com/?utm_source=student&utm_medium=ps-linkedin&utm_campaign=cohort3

#DMIByPravinMishra #DevOps #AgenticAI #Ansible
