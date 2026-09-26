# Assignment 7 — AI-Assisted Docker Container Hardening Audit

Part of the DevOps Micro Internship (DMI) Cohort 3 with Agentic AI

**Eze Favour · Verified 26 September 2026 · DMI assessment pending**

Actual Claude Code/Bedrock planning and skill runs are recorded. The deliberately weak training copy of the EpicBook backend had 3 PASS / 3 FAIL; after Codex changed its Dockerfile outside Claude and rebuilt it, the audit reported 6 PASS. The hardened public backend was not weakened to create failures. See [operator review and sequence disclosure](hardening-audit/OPERATOR-REVIEW.md): the first script draft predated Claude planning, and learner-personal manual execution is not claimed.

**Evidence method:** Codex executed and documented these exercises under delegation. App screenshots are actual browser captures. Numbered command/editor slots link to labelled browser renderings of saved command output or source, with originals alongside them; they are not represented as live Terminal or VS Code captures. Full-name captions identify the submission without claiming personal learner execution.

---

## Purpose

In this assignment, you will build a read-only Bash script that audits a running Docker container for common hardening gaps — running as root, missing health checks, unpinned image tags, privileged mode, and unnecessary exposed ports — then connect that script to Claude Code as a reusable `/docker-audit` skill. You will run the audit against your production-grade EpicBook stack, fix what it finds by editing the Dockerfile yourself, rebuild the image, and re-run the audit to prove the fix worked. Claude analyzes evidence and recommends a fix; it never edits your Dockerfile or rebuilds the image itself.

---

# Task 1 — Confirm the Running Stack and Create the Workspace

## Goal

Confirm your production-grade EpicBook containers from this week's capstone are currently running, note the exact name of your application container, and set up a project workspace for the audit.

### Evidence

#### Screenshot 1 — `docker ps` showing your running EpicBook application container

[Original record/source](evidence/2026-09-26/a6-final-build.txt) · [Screenshot page 1](screenshots/a6-final-build-p01.png) · [Screenshot page 2](screenshots/a6-final-build-p02.png) · [Screenshot page 3](screenshots/a6-final-build-p03.png) · [Screenshot page 4](screenshots/a6-final-build-p04.png) · [Screenshot page 5](screenshots/a6-final-build-p05.png) · [Screenshot page 6](screenshots/a6-final-build-p06.png). Captured from the labelled saved-output/source viewer.

---

# Task 2 — Create Project Context and Safety Rules in CLAUDE.md

## Goal

Create a `CLAUDE.md` in your workspace that tells Claude this project only ever gathers container evidence and recommends a Dockerfile fix — it must never run `docker build`, `docker rm`, `docker stop`, `docker rmi`, or edit the Dockerfile itself.

### Evidence

#### Screenshot 2 — `CLAUDE.md` open in VS Code showing the project overview, hardening workflow, and safety rules

[Original record/source](hardening-audit/CLAUDE.md) · [Screenshot page 1](screenshots/hardening-audit-CLAUDE_md-p01.png). Captured from the labelled saved-output/source viewer.

---

# Task 3 — Use Agentic AI to Plan Before Writing the Script

## Goal

Ask Claude Code to inspect your running container using only read-only Docker commands and propose a six-check hardening audit plan, without creating or editing any file.

### Evidence

#### Screenshot 3 — Claude's proposed audit plan and read-only inspection

[Original record/source](evidence/2026-09-26/a7-claude-plan.txt) · [Screenshot page 1](screenshots/a7-claude-plan-p01.png) · [Screenshot page 2](screenshots/a7-claude-plan-p02.png) · [Screenshot page 3](screenshots/a7-claude-plan-p03.png) · [Screenshot page 4](screenshots/a7-claude-plan-p04.png) · [Screenshot page 5](screenshots/a7-claude-plan-p05.png). Captured from the labelled saved-output/source viewer.

---

# Task 4 — Build the Docker Hardening Audit Script

## Goal

Write a Bash script that runs `docker inspect` and `docker image inspect` against your target container and checks: the container exists, whether it runs as root, whether a `HEALTHCHECK` is defined, whether the image tag is pinned instead of `:latest`, whether the container runs in privileged mode, and how many ports it exposes. The script must be strictly read-only and must produce a report file with a clear pass/warning/failure summary.

### Evidence

#### Screenshot 4 — Your audit script open in an editor, showing the six check functions

[Original record/source](hardening-audit/docker-audit.sh) · [Screenshot page 1](screenshots/hardening-audit-docker-audit_sh-p01.png) · [Screenshot page 2](screenshots/hardening-audit-docker-audit_sh-p02.png). Captured from the labelled saved-output/source viewer.

---

#### Screenshot 5 — Terminal output of `bash -n` confirming the script has no syntax errors, and `ls -l` showing it is executable

[Original record/source](evidence/2026-09-26/a7-tests.txt) · [Screenshot page 1](screenshots/a7-tests-p01.png). Captured from the labelled saved-output/source viewer.

---

# Task 5 — Run the Audit Against Your Current Container

## Goal

Run the script against your running EpicBook container and record the results honestly, even if one or more checks fail — most first-time containers fail at least one (commonly: no `USER` directive, no `HEALTHCHECK`, or a `:latest` tag).

### Evidence

#### Screenshot 6 — Script output showing your Full Name and all six check results

[Original record/source](evidence/2026-09-26/a7-baseline-report.txt) · [Screenshot page 1](screenshots/a7-baseline-report-p01.png). Captured from the labelled saved-output/source viewer.

---

# Task 6 — Create and Run the /docker-audit Skill

## Goal

Turn the script into a Claude Code skill restricted to read-only tools, and run `/docker-audit` to confirm Claude reads the report, explains each finding with evidence, and recommends a specific Dockerfile fix — without modifying anything itself.

### Evidence

#### Screenshot 7 — `SKILL.md` frontmatter showing the tool restrictions and safety rules

[Original record/source](hardening-audit/.claude/skills/docker-audit/SKILL.md) · [Screenshot page 1](screenshots/hardening-audit-_claude-skills-docker-audit-SKILL_md-p01.png). Captured from the labelled saved-output/source viewer.

---

#### Screenshot 8 — `/docker-audit` output showing the findings and Claude's recommended fix

[Original record/source](evidence/2026-09-26/a7-claude-baseline.txt) · [Screenshot page 1](screenshots/a7-claude-baseline-p01.png) · [Screenshot page 2](screenshots/a7-claude-baseline-p02.png) · [Screenshot page 3](screenshots/a7-claude-baseline-p03.png) · [Screenshot page 4](screenshots/a7-claude-baseline-p04.png) · [Screenshot page 5](screenshots/a7-claude-baseline-p05.png) · [Screenshot page 6](screenshots/a7-claude-baseline-p06.png). Captured from the labelled saved-output/source viewer.

---

# Task 7 — Fix the Findings, Rebuild, and Verify

## Goal

Edit your Dockerfile to apply Claude's recommendation, rebuild the image, recreate the container, and re-run `/docker-audit` to prove the previously failing check now passes.

### Evidence

#### Screenshot 9 — Your edited Dockerfile line(s) showing the fix

[Original record/source](hardening-audit/Dockerfile.hardened) · [Screenshot page 1](screenshots/hardening-audit-Dockerfile_hardened-p01.png). Captured from the labelled saved-output/source viewer.

---

#### Screenshot 10 — `docker build` and `docker run` succeeding with the rebuilt image

[Original record/source](evidence/2026-09-26/a7-operator-remediation.txt) · [Screenshot page 1](screenshots/a7-operator-remediation-p01.png) · [Screenshot page 2](screenshots/a7-operator-remediation-p02.png). Captured from the labelled saved-output/source viewer.

---

#### Screenshot 11 — Second `/docker-audit` run showing the previously failed check now passing

[Original record/source](evidence/2026-09-26/a7-claude-after.txt) · [Screenshot page 1](screenshots/a7-claude-after-p01.png) · [Screenshot page 2](screenshots/a7-claude-after-p02.png) · [Screenshot page 3](screenshots/a7-claude-after-p03.png) · [Screenshot page 4](screenshots/a7-claude-after-p04.png). Captured from the labelled saved-output/source viewer.

---

### Notes

In one paragraph, explain why the `/docker-audit` skill is allowed to gather evidence and recommend a Dockerfile fix, but is never allowed to edit the Dockerfile or rebuild the image itself.

The read-only skill keeps diagnosis separate from operational changes. It gathers Docker metadata, writes a bounded report and recommends a correction, while its command guard prevents builds, removals, stops and Dockerfile edits. Codex, acting under my delegation outside that Claude session, reviewed the findings, corrected inaccurate generic examples, implemented the Node health probe and non-root user, rebuilt, and obtained a fresh audit. This separation makes the evidence and change authority easier to review, but does not eliminate the need to inspect AI recommendations or prove application behavior beyond six configuration checks.

---

# Submission Instructions

Complete all tasks in sequence.

Your submission must include:
- All 11 required screenshots
- Full name must be visible in required screenshots
- Do not expose Docker Hub credentials or cloud account IDs

---

# Completion Checklist

- [x] Task 1: EpicBook container confirmed running (Screenshot 1)
- [x] Task 2: `CLAUDE.md` created with hardening workflow and safety rules (Screenshot 2)
- [x] Task 3: Claude produced a read-only six-check audit plan (Screenshot 3)
- [x] Task 4: Audit script built and validated (Screenshots 4–5)
- [x] Task 5: Script run against the live container, results recorded honestly (Screenshot 6)
- [x] Task 6: `/docker-audit` skill created and run (Screenshots 7–8)
- [x] Task 7: Dockerfile fixed, image rebuilt, and fix verified (Screenshots 9–11)
- [x] Reflection answered (Notes)
- [x] No sensitive data exposed

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

**Assessor review boundary:** functional workflow verified; first-draft sequence and personally manual execution are disclosed exceptions, not checked-off claims. Configuration audit passes do not establish complete production security.

## Recorded evidence gallery

Each figure is captured once and may support multiple related screenshot slots. Page links above identify the same original evidence, not separate repeated executions.

### a6-final-build

[Original](evidence/2026-09-26/a6-final-build.txt)

![Eze Favour — a6-final-build-p01](screenshots/a6-final-build-p01.png)

![Eze Favour — a6-final-build-p02](screenshots/a6-final-build-p02.png)

![Eze Favour — a6-final-build-p03](screenshots/a6-final-build-p03.png)

![Eze Favour — a6-final-build-p04](screenshots/a6-final-build-p04.png)

![Eze Favour — a6-final-build-p05](screenshots/a6-final-build-p05.png)

![Eze Favour — a6-final-build-p06](screenshots/a6-final-build-p06.png)

### hardening-audit-CLAUDE_md

[Original](hardening-audit/CLAUDE.md)

![Eze Favour — hardening-audit-CLAUDE_md-p01](screenshots/hardening-audit-CLAUDE_md-p01.png)

### a7-claude-plan

[Original](evidence/2026-09-26/a7-claude-plan.txt)

![Eze Favour — a7-claude-plan-p01](screenshots/a7-claude-plan-p01.png)

![Eze Favour — a7-claude-plan-p02](screenshots/a7-claude-plan-p02.png)

![Eze Favour — a7-claude-plan-p03](screenshots/a7-claude-plan-p03.png)

![Eze Favour — a7-claude-plan-p04](screenshots/a7-claude-plan-p04.png)

![Eze Favour — a7-claude-plan-p05](screenshots/a7-claude-plan-p05.png)

### hardening-audit-docker-audit_sh

[Original](hardening-audit/docker-audit.sh)

![Eze Favour — hardening-audit-docker-audit_sh-p01](screenshots/hardening-audit-docker-audit_sh-p01.png)

![Eze Favour — hardening-audit-docker-audit_sh-p02](screenshots/hardening-audit-docker-audit_sh-p02.png)

### a7-tests

[Original](evidence/2026-09-26/a7-tests.txt)

![Eze Favour — a7-tests-p01](screenshots/a7-tests-p01.png)

### a7-baseline-report

[Original](evidence/2026-09-26/a7-baseline-report.txt)

![Eze Favour — a7-baseline-report-p01](screenshots/a7-baseline-report-p01.png)

### hardening-audit-_claude-skills-docker-audit-SKILL_md

[Original](hardening-audit/.claude/skills/docker-audit/SKILL.md)

![Eze Favour — hardening-audit-_claude-skills-docker-audit-SKILL_md-p01](screenshots/hardening-audit-_claude-skills-docker-audit-SKILL_md-p01.png)

### a7-claude-baseline

[Original](evidence/2026-09-26/a7-claude-baseline.txt)

![Eze Favour — a7-claude-baseline-p01](screenshots/a7-claude-baseline-p01.png)

![Eze Favour — a7-claude-baseline-p02](screenshots/a7-claude-baseline-p02.png)

![Eze Favour — a7-claude-baseline-p03](screenshots/a7-claude-baseline-p03.png)

![Eze Favour — a7-claude-baseline-p04](screenshots/a7-claude-baseline-p04.png)

![Eze Favour — a7-claude-baseline-p05](screenshots/a7-claude-baseline-p05.png)

![Eze Favour — a7-claude-baseline-p06](screenshots/a7-claude-baseline-p06.png)

### hardening-audit-Dockerfile_hardened

[Original](hardening-audit/Dockerfile.hardened)

![Eze Favour — hardening-audit-Dockerfile_hardened-p01](screenshots/hardening-audit-Dockerfile_hardened-p01.png)

### a7-operator-remediation

[Original](evidence/2026-09-26/a7-operator-remediation.txt)

![Eze Favour — a7-operator-remediation-p01](screenshots/a7-operator-remediation-p01.png)

![Eze Favour — a7-operator-remediation-p02](screenshots/a7-operator-remediation-p02.png)

### a7-claude-after

[Original](evidence/2026-09-26/a7-claude-after.txt)

![Eze Favour — a7-claude-after-p01](screenshots/a7-claude-after-p01.png)

![Eze Favour — a7-claude-after-p02](screenshots/a7-claude-after-p02.png)

![Eze Favour — a7-claude-after-p03](screenshots/a7-claude-after-p03.png)

![Eze Favour — a7-claude-after-p04](screenshots/a7-claude-after-p04.png)


The final public backend also passed all six checks and was running and healthy: [separate live audit](evidence/2026-09-26/a7-public-stack-audit.txt).
