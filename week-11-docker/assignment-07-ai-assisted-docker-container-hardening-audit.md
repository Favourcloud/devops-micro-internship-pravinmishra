# Assignment 7 — AI-Assisted Docker Container Hardening Audit

Part of the DevOps Micro Internship (DMI) Cohort 3 with Agentic AI

**Eze Favour · Ordered rerun verified 27 September 2026 (Africa/Lagos) · DMI assessment pending**

The fresh ordered rerun completed all seven tasks: live inspection → Claude planning while no audit script existed → script creation and validation → first audit → restricted skill → reviewed operator Dockerfile change and rebuild → second skill. The baseline returned **3 PASS / 3 FAIL** and the rebuilt training container returned **6 PASS / 0 WARN / 0 FAIL**. It was independently observed healthy with UID 1000. Fifteen behavior tests passed. [Chronology and operator review](hardening-audit/ordered-rerun/README.md).

**Evidence method:** The 11 required screenshot slots below now use direct captures of the actual Code OSS editor and its integrated terminal, including live Claude Code/Bedrock tool runs. They are not HTML evidence viewers. Codex performed the work and Dockerfile changes under delegation; no personal learner execution or awarded grade is claimed. The earlier attempt and its disclosed sequence error remain preserved as historical evidence.

---

## Purpose

In this assignment, you will build a read-only Bash script that audits a running Docker container for common hardening gaps — running as root, missing health checks, unpinned image tags, privileged mode, and unnecessary exposed ports — then connect that script to Claude Code as a reusable `/docker-audit` skill. You will run the audit against your production-grade EpicBook stack, fix what it finds by editing the Dockerfile yourself, rebuild the image, and re-run the audit to prove the fix worked. Claude analyzes evidence and recommends a fix; it never edits your Dockerfile or rebuilds the image itself.

---

# Task 1 — Confirm the Running Stack and Create the Workspace

## Goal

Confirm your production-grade EpicBook containers from this week's capstone are currently running, note the exact name of your application container, and set up a project workspace for the audit.

### Evidence

#### Screenshot 1 — `docker ps` showing your running EpicBook application container

[Original record/source](evidence/2026-09-27-ordered-rerun/baseline-setup.txt) · [Direct capture 1](screenshots/ordered-rerun/01-live-docker-ps.png)

---

# Task 2 — Create Project Context and Safety Rules in CLAUDE.md

## Goal

Create a `CLAUDE.md` in your workspace that tells Claude this project only ever gathers container evidence and recommends a Dockerfile fix — it must never run `docker build`, `docker rm`, `docker stop`, `docker rmi`, or edit the Dockerfile itself.

### Evidence

#### Screenshot 2 — `CLAUDE.md` open in VS Code showing the project overview, hardening workflow, and safety rules

[Original record/source](hardening-audit/ordered-rerun/CLAUDE.md) · [Direct capture 1](screenshots/ordered-rerun/02-claude-context.png)

---

# Task 3 — Use Agentic AI to Plan Before Writing the Script

## Goal

Ask Claude Code to inspect your running container using only read-only Docker commands and propose a six-check hardening audit plan, without creating or editing any file.

### Evidence

#### Screenshot 3 — Claude's proposed audit plan and read-only inspection

[Original record/source](evidence/2026-09-27-ordered-rerun/plan-result.json) · [Direct capture 1](screenshots/ordered-rerun/03-plan-start.png) · [Direct capture 2](screenshots/ordered-rerun/03-plan-end.png)

---

# Task 4 — Build the Docker Hardening Audit Script

## Goal

Write a Bash script that runs `docker inspect` and `docker image inspect` against your target container and checks: the container exists, whether it runs as root, whether a `HEALTHCHECK` is defined, whether the image tag is pinned instead of `:latest`, whether the container runs in privileged mode, and how many ports it exposes. The script must be strictly read-only and must produce a report file with a clear pass/warning/failure summary.

### Evidence

#### Screenshot 4 — Your audit script open in an editor, showing the six check functions

[Original record/source](hardening-audit/ordered-rerun/docker-audit.sh) · [Direct capture 1](screenshots/ordered-rerun/04-audit-script-1.png) · [Direct capture 2](screenshots/ordered-rerun/04-audit-script-2.png) · [Direct capture 3](screenshots/ordered-rerun/04-audit-script-3.png) · [Direct capture 4](screenshots/ordered-rerun/04-audit-script-4.png) · [Direct capture 5](screenshots/ordered-rerun/04-audit-script-5.png)

---

#### Screenshot 5 — Terminal output of `bash -n` confirming the script has no syntax errors, and `ls -l` showing it is executable

[Original record/source](evidence/2026-09-27-ordered-rerun/audit-tests.txt) · [Direct capture 1](screenshots/ordered-rerun/05-syntax-and-permissions.png) · [Direct capture 2](screenshots/ordered-rerun/12-behavior-tests.png)

---

# Task 5 — Run the Audit Against Your Current Container

## Goal

Run the script against your running EpicBook container and record the results honestly, even if one or more checks fail — most first-time containers fail at least one (commonly: no `USER` directive, no `HEALTHCHECK`, or a `:latest` tag).

### Evidence

#### Screenshot 6 — Script output showing your Full Name and all six check results

[Original record/source](evidence/2026-09-27-ordered-rerun/baseline-first-report.txt) · [Direct capture 1](screenshots/ordered-rerun/06-baseline-audit.png)

---

# Task 6 — Create and Run the /docker-audit Skill

## Goal

Turn the script into a Claude Code skill restricted to read-only tools, and run `/docker-audit` to confirm Claude reads the report, explains each finding with evidence, and recommends a specific Dockerfile fix — without modifying anything itself.

### Evidence

#### Screenshot 7 — `SKILL.md` frontmatter showing the tool restrictions and safety rules

[Original record/source](hardening-audit/ordered-rerun/.claude/skills/docker-audit/SKILL.md) · [Direct capture 1](screenshots/ordered-rerun/07-restricted-skill.png)

---

#### Screenshot 8 — `/docker-audit` output showing the findings and Claude's recommended fix

[Original record/source](evidence/2026-09-27-ordered-rerun/baseline-result.json) · [Direct capture 1](screenshots/ordered-rerun/08-skill-findings.png) · [Direct capture 2](screenshots/ordered-rerun/08-skill-recommendations.png)

---

# Task 7 — Fix the Findings, Rebuild, and Verify

## Goal

Edit your Dockerfile to apply Claude's recommendation, rebuild the image, recreate the container, and re-run `/docker-audit` to prove the previously failing check now passes.

### Evidence

#### Screenshot 9 — Your edited Dockerfile line(s) showing the fix

[Original record/source](hardening-audit/ordered-rerun/Dockerfile.hardened) · [Direct capture 1](screenshots/ordered-rerun/09-dockerfile-fix.png)

---

#### Screenshot 10 — `docker build` and `docker run` succeeding with the rebuilt image

[Original record/source](evidence/2026-09-27-ordered-rerun/operator-rebuild.txt) · [Direct capture 1](screenshots/ordered-rerun/10-build-and-run.png)

---

#### Screenshot 11 — Second `/docker-audit` run showing the previously failed check now passing

[Original record/source](evidence/2026-09-27-ordered-rerun/after-result.json) · [Direct capture 1](screenshots/ordered-rerun/11-skill-six-passes.png) · [Direct capture 2](screenshots/ordered-rerun/11-skill-comparison.png)

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

**Assessor review boundary:** the fresh ordered sequence is verified; delegated execution still requires the assessor’s judgment where the rubric expects personal manual work. Configuration audit passes do not establish complete production security.

## Direct evidence gallery

### Screenshot slot 1

[Record or source](evidence/2026-09-27-ordered-rerun/baseline-setup.txt)

![Eze Favour — 01-live-docker-ps](screenshots/ordered-rerun/01-live-docker-ps.png)

### Screenshot slot 2

[Record or source](hardening-audit/ordered-rerun/CLAUDE.md)

![Eze Favour — 02-claude-context](screenshots/ordered-rerun/02-claude-context.png)

### Screenshot slot 3

[Record or source](evidence/2026-09-27-ordered-rerun/plan-result.json)

![Eze Favour — 03-plan-start](screenshots/ordered-rerun/03-plan-start.png)

![Eze Favour — 03-plan-end](screenshots/ordered-rerun/03-plan-end.png)

### Screenshot slot 4

[Record or source](hardening-audit/ordered-rerun/docker-audit.sh)

![Eze Favour — 04-audit-script-1](screenshots/ordered-rerun/04-audit-script-1.png)

![Eze Favour — 04-audit-script-2](screenshots/ordered-rerun/04-audit-script-2.png)

![Eze Favour — 04-audit-script-3](screenshots/ordered-rerun/04-audit-script-3.png)

![Eze Favour — 04-audit-script-4](screenshots/ordered-rerun/04-audit-script-4.png)

![Eze Favour — 04-audit-script-5](screenshots/ordered-rerun/04-audit-script-5.png)

### Screenshot slot 5

[Record or source](evidence/2026-09-27-ordered-rerun/audit-tests.txt)

![Eze Favour — 05-syntax-and-permissions](screenshots/ordered-rerun/05-syntax-and-permissions.png)

![Eze Favour — 12-behavior-tests](screenshots/ordered-rerun/12-behavior-tests.png)

### Screenshot slot 6

[Record or source](evidence/2026-09-27-ordered-rerun/baseline-first-report.txt)

![Eze Favour — 06-baseline-audit](screenshots/ordered-rerun/06-baseline-audit.png)

### Screenshot slot 7

[Record or source](hardening-audit/ordered-rerun/.claude/skills/docker-audit/SKILL.md)

![Eze Favour — 07-restricted-skill](screenshots/ordered-rerun/07-restricted-skill.png)

### Screenshot slot 8

[Record or source](evidence/2026-09-27-ordered-rerun/baseline-result.json)

![Eze Favour — 08-skill-findings](screenshots/ordered-rerun/08-skill-findings.png)

![Eze Favour — 08-skill-recommendations](screenshots/ordered-rerun/08-skill-recommendations.png)

### Screenshot slot 9

[Record or source](hardening-audit/ordered-rerun/Dockerfile.hardened)

![Eze Favour — 09-dockerfile-fix](screenshots/ordered-rerun/09-dockerfile-fix.png)

### Screenshot slot 10

[Record or source](evidence/2026-09-27-ordered-rerun/operator-rebuild.txt)

![Eze Favour — 10-build-and-run](screenshots/ordered-rerun/10-build-and-run.png)

### Screenshot slot 11

[Record or source](evidence/2026-09-27-ordered-rerun/after-result.json)

![Eze Favour — 11-skill-six-passes](screenshots/ordered-rerun/11-skill-six-passes.png)

![Eze Favour — 11-skill-comparison](screenshots/ordered-rerun/11-skill-comparison.png)
