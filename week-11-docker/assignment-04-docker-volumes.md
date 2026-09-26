# Assignment 4 — Docker Volumes

Part of the DevOps Micro Internship (DMI) Cohort 3 with Agentic AI

**Eze Favour · Verified 26 September 2026 · DMI assessment pending**

Nginx log files and their checksums remained after container removal. A named shared volume served the initial message and two updates to a read-only frontend. A write attempt from the reader was rejected, and the last data remained after exercise-container cleanup.

**Evidence method:** Codex executed these exercises under delegation. App screenshots are direct browser captures; source screenshots use the actual Code OSS editor except the explicitly labelled original multistage-Dockerfile source capture in A2. Terminal-review screenshots show the original dated saved command output or source in its integrated terminal, explicitly labelled as a review rather than a new execution. Originals and hashes remain linked. Newly executed A4 updates and A6 live logs are identified separately. No learner-personal execution is claimed.

---

## Purpose

In this assignment, you will learn how Docker Volumes and Bind Mounts provide persistent storage for containers, deploying applications that retain logs and data even after containers are stopped or removed.

---

# Task 1 — Deploy a Standalone Application with Persistent Logs Using Bind Mounts

## Goal

Run an Nginx container (`myweb`) with a Bind Mount from `~/nginx-logs` to `/var/log/nginx`, verify the site loads, confirm logs are written, remove the container, and confirm the logs persist on the host.

### Evidence

#### Screenshot 1 — Output of `docker images`

[Original record/source](evidence/2026-09-26/a4-bind-mount.txt) · [Terminal page 1](screenshots/terminal-review/a4-bind-mount-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a4-bind-mount-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a4-bind-mount-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a4-bind-mount-terminal-04.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 2 — Output of `docker search nginx`

[Original record/source](evidence/2026-09-26/a4-bind-mount.txt) · [Terminal page 1](screenshots/terminal-review/a4-bind-mount-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a4-bind-mount-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a4-bind-mount-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a4-bind-mount-terminal-04.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 3 — Successful `docker pull nginx` (if applicable)

[Original record/source](evidence/2026-09-26/a4-bind-mount.txt) · [Terminal page 1](screenshots/terminal-review/a4-bind-mount-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a4-bind-mount-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a4-bind-mount-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a4-bind-mount-terminal-04.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 4 — Creation of the `~/nginx-logs` directory

[Original record/source](evidence/2026-09-26/a4-bind-mount.txt) · [Terminal page 1](screenshots/terminal-review/a4-bind-mount-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a4-bind-mount-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a4-bind-mount-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a4-bind-mount-terminal-04.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 5 — Output of `docker run` with the Bind Mount

[Original record/source](evidence/2026-09-26/a4-bind-mount.txt) · [Terminal page 1](screenshots/terminal-review/a4-bind-mount-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a4-bind-mount-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a4-bind-mount-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a4-bind-mount-terminal-04.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 6 — Output of `docker ps` showing the running `myweb` container

[Original record/source](evidence/2026-09-26/a4-bind-mount.txt) · [Terminal page 1](screenshots/terminal-review/a4-bind-mount-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a4-bind-mount-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a4-bind-mount-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a4-bind-mount-terminal-04.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 7 — Browser displaying the Nginx Welcome Page

![Eze Favour — a4-bind-mount-browser](screenshots/a4-bind-mount-browser.png)

---

#### Screenshot 8 — Output of `ls ~/nginx-logs` showing `access.log` and `error.log`

[Original record/source](evidence/2026-09-26/a4-bind-mount.txt) · [Terminal page 1](screenshots/terminal-review/a4-bind-mount-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a4-bind-mount-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a4-bind-mount-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a4-bind-mount-terminal-04.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 9 — Successful removal of the container

[Original record/source](evidence/2026-09-26/a4-bind-removal.txt) · [Terminal page 1](screenshots/terminal-review/a4-bind-removal-terminal-01.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 10 — Output of `ls ~/nginx-logs` confirming the log files remain after the container has been removed

[Original record/source](evidence/2026-09-26/a4-bind-removal.txt) · [Terminal page 1](screenshots/terminal-review/a4-bind-removal-terminal-01.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

# Task 2 — Deploy Two Containers with Persistent Data Using Docker Volumes

## Goal

Create a custom network `mynetwork` and a Docker volume `shared-data`, build and run a `backend` container that writes to the shared volume and a `frontend` container that reads from it, and confirm updates are reflected immediately.

### Evidence

#### Screenshot 1 — Project folder structure

[Original record/source](evidence/2026-09-26/a4-shared-volume.txt) · [Terminal page 1](screenshots/terminal-review/a4-shared-volume-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a4-shared-volume-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a4-shared-volume-terminal-03.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 2 — Output of `docker network create mynetwork`

[Original record/source](evidence/2026-09-26/a4-shared-volume.txt) · [Terminal page 1](screenshots/terminal-review/a4-shared-volume-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a4-shared-volume-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a4-shared-volume-terminal-03.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 3 — Output of `docker volume create shared-data`

[Original record/source](evidence/2026-09-26/a4-shared-volume.txt) · [Terminal page 1](screenshots/terminal-review/a4-shared-volume-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a4-shared-volume-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a4-shared-volume-terminal-03.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 4 — Backend Dockerfile

[Original record/source](evidence/2026-09-26/a4-shared-volume.txt) · [Terminal page 1](screenshots/terminal-review/a4-shared-volume-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a4-shared-volume-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a4-shared-volume-terminal-03.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 5 — Successful backend image build

[Original record/source](evidence/2026-09-26/a4-shared-volume-build-stderr.txt) · [Terminal page 1](screenshots/terminal-review/a4-shared-volume-build-stderr-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a4-shared-volume-build-stderr-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a4-shared-volume-build-stderr-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a4-shared-volume-build-stderr-terminal-04.png) · [Terminal page 5](screenshots/terminal-review/a4-shared-volume-build-stderr-terminal-05.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 6 — Frontend Dockerfile

[Original record/source](evidence/2026-09-26/a4-shared-volume.txt) · [Terminal page 1](screenshots/terminal-review/a4-shared-volume-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a4-shared-volume-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a4-shared-volume-terminal-03.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 7 — Successful frontend image build

[Original record/source](evidence/2026-09-26/a4-shared-volume-build-stderr.txt) · [Terminal page 1](screenshots/terminal-review/a4-shared-volume-build-stderr-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a4-shared-volume-build-stderr-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a4-shared-volume-build-stderr-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a4-shared-volume-build-stderr-terminal-04.png) · [Terminal page 5](screenshots/terminal-review/a4-shared-volume-build-stderr-terminal-05.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 8 — Output of `docker ps` showing both containers

[Original record/source](evidence/2026-09-26/a4-shared-volume.txt) · [Terminal page 1](screenshots/terminal-review/a4-shared-volume-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a4-shared-volume-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a4-shared-volume-terminal-03.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 9 — Successful execution of `docker exec backend curl http://localhost/write`

[Original record/source](evidence/2026-09-26/a4-shared-volume.txt) · [Terminal page 1](screenshots/terminal-review/a4-shared-volume-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a4-shared-volume-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a4-shared-volume-terminal-03.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 10 — Browser displaying "Hello from Backend!"

![Eze Favour — a4-volume-initial](screenshots/a4-volume-initial.png)

---

#### Screenshot 11 — Browser displaying "Test Data 1" after the first update

[Original September 26 record](evidence/2026-09-26/a4-volume-update1.txt) · [Fresh update record](evidence/2026-09-27-ordered-rerun/volume-update1.txt)

![Eze Favour — live shared-volume update 1](screenshots/ordered-rerun/a4-update1-browser.png)

---

#### Screenshot 12 — Browser displaying "Test Data 2 - New Update" after the second update

[Original September 26 record](evidence/2026-09-26/a4-volume-update2.txt) · [Fresh update record](evidence/2026-09-27-ordered-rerun/volume-update2.txt)

![Eze Favour — live shared-volume update 2](screenshots/ordered-rerun/a4-update2-browser.png)

---

# LinkedIn Post (Optional)

## Goal

Create a LinkedIn post covering the assignment, Docker Hub repository, steps performed, and key learning outcomes.

## Evidence

#### LinkedIn Post URL

The weekly post covers this assignment and the EpicBook capstone.

[Published Week 11 LinkedIn post](https://www.linkedin.com/posts/eze-favour-52732752_dmibypravinmishra-docker-devops-share-7509737427876454400-cxc1/) · [receipt](publication/README.md).

---

#### Screenshot — Published LinkedIn post

See [the weekly publication receipt](publication/README.md) and its published-post capture.

---

# Submission Instructions

- Add all required screenshots in your submission
- Full name must be visible in required screenshots
- Do not expose sensitive information

---

# Completion Checklist

- [x] Task 1: Bind-mounted persistent logs verified before and after container removal (Screenshots 1–10)
- [x] Task 2: Docker volume shared between frontend and backend verified (Screenshots 1–12)
- [x] No sensitive information exposed

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

## Recorded evidence gallery

The new browser captures above use a separate `week11-volume-rerun` volume and containers, accessed through an SSH tunnel to a loopback-only listener. The initial message and both updates were actually executed and observed; the original shared volume and public React service were preserved.

![Eze Favour — fresh initial shared-volume message](screenshots/ordered-rerun/a4-initial-browser.png)

### Historical evidence viewer captures

Each figure is captured once and may support multiple related screenshot slots. Page links above identify the same original evidence, not separate repeated executions.

### a4-bind-mount

[Original](evidence/2026-09-26/a4-bind-mount.txt)

![Eze Favour — a4-bind-mount-p01](screenshots/a4-bind-mount-p01.png)

![Eze Favour — a4-bind-mount-p02](screenshots/a4-bind-mount-p02.png)

![Eze Favour — a4-bind-mount-p03](screenshots/a4-bind-mount-p03.png)

![Eze Favour — a4-bind-mount-p04](screenshots/a4-bind-mount-p04.png)

### a4-bind-removal

[Original](evidence/2026-09-26/a4-bind-removal.txt)

![Eze Favour — a4-bind-removal-p01](screenshots/a4-bind-removal-p01.png)

![Eze Favour — a4-bind-removal-p02](screenshots/a4-bind-removal-p02.png)

### a4-shared-volume

[Original](evidence/2026-09-26/a4-shared-volume.txt)

![Eze Favour — a4-shared-volume-p01](screenshots/a4-shared-volume-p01.png)

![Eze Favour — a4-shared-volume-p02](screenshots/a4-shared-volume-p02.png)

![Eze Favour — a4-shared-volume-p03](screenshots/a4-shared-volume-p03.png)

### a4-shared-volume-build-stderr

[Original](evidence/2026-09-26/a4-shared-volume-build-stderr.txt)

![Eze Favour — a4-shared-volume-build-stderr-p01](screenshots/a4-shared-volume-build-stderr-p01.png)

![Eze Favour — a4-shared-volume-build-stderr-p02](screenshots/a4-shared-volume-build-stderr-p02.png)

![Eze Favour — a4-shared-volume-build-stderr-p03](screenshots/a4-shared-volume-build-stderr-p03.png)

![Eze Favour — a4-shared-volume-build-stderr-p04](screenshots/a4-shared-volume-build-stderr-p04.png)

![Eze Favour — a4-shared-volume-build-stderr-p05](screenshots/a4-shared-volume-build-stderr-p05.png)

![Eze Favour — a4-shared-volume-build-stderr-p06](screenshots/a4-shared-volume-build-stderr-p06.png)

### a4-volume-update1

[Original](evidence/2026-09-26/a4-volume-update1.txt)

![Eze Favour — a4-volume-update1-p01](screenshots/a4-volume-update1-p01.png)

### a4-volume-update2

[Original](evidence/2026-09-26/a4-volume-update2.txt)

![Eze Favour — a4-volume-update2-p01](screenshots/a4-volume-update2-p01.png)
