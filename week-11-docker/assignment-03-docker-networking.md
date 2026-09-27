# Assignment 3 — Docker Networking

Part of the DevOps Micro Internship (DMI) Cohort 3 with Agentic AI

**Eze Favour · Verified 26 September 2026 · DMI assessment pending**

All four network exercises ran on the dedicated labs VM. The custom bridge used container-name DNS. The three-tier app inserted and retrieved a MongoDB document; frontend-to-database name resolution was blocked. MongoDB 8.0 initially failed on the host kernel; the working exercise used MongoDB 7.0. Temporary networking containers were removed before restoring React on port 80.

**Evidence method:** Codex executed these exercises under delegation. App screenshots are direct browser captures; source screenshots use the actual Code OSS editor except the explicitly labelled original multistage-Dockerfile source capture in A2. Terminal-review screenshots show the original dated saved command output or source in its integrated terminal, explicitly labelled as a review rather than a new execution. Originals and hashes remain linked. Newly executed A4 updates and A6 live logs are identified separately. No learner-personal execution is claimed.

---

## Purpose

In this assignment, you will explore Docker network types and deploy applications using different networking modes: the default bridge network, a custom bridge network for microservices, multiple networks for a multi-tier architecture, and host networking.

---

# Task 1 — Deploy a Standalone Application Using Docker Bridge Network

## Goal

List Docker networks, verify/pull the Nginx image, run an Nginx container (`myweb`) on the default bridge network with port 80 mapped, and verify it's reachable from a browser via the VM's public IP.

### Evidence

#### Screenshot 1 — Output of `docker network ls`

[Original record/source](evidence/2026-09-26/a3-default-bridge.txt) · [Terminal page 1](screenshots/terminal-review/a3-default-bridge-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-default-bridge-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-default-bridge-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-default-bridge-terminal-04.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 2 — Output of `docker images`

[Original record/source](evidence/2026-09-26/a3-default-bridge.txt) · [Terminal page 1](screenshots/terminal-review/a3-default-bridge-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-default-bridge-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-default-bridge-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-default-bridge-terminal-04.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 3 — Output of `docker search nginx`

[Original record/source](evidence/2026-09-26/a3-default-bridge.txt) · [Terminal page 1](screenshots/terminal-review/a3-default-bridge-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-default-bridge-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-default-bridge-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-default-bridge-terminal-04.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 4 — Successful `docker pull nginx` (if applicable)

[Original record/source](evidence/2026-09-26/a3-default-bridge.txt) · [Terminal page 1](screenshots/terminal-review/a3-default-bridge-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-default-bridge-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-default-bridge-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-default-bridge-terminal-04.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 5 — Output of `docker ps` showing the running `myweb` container

[Original record/source](evidence/2026-09-26/a3-default-bridge.txt) · [Terminal page 1](screenshots/terminal-review/a3-default-bridge-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-default-bridge-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-default-bridge-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-default-bridge-terminal-04.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 6 — Browser displaying the Nginx Welcome Page using the Public IP address

![Eze Favour — a3-default-bridge-browser](screenshots/a3-default-bridge-browser.png)

---

# Task 2 — Connect Multiple Containers Using a Custom Bridge Network

## Goal

Create a custom bridge network `mynetwork`, build and run a Node/Express `frontend` container and an Nginx `backend` container on it, and verify they can communicate by container name.

### Evidence

#### Screenshot 1 — Output of `docker network create mynetwork`

[Original record/source](evidence/2026-09-26/a3-custom-bridge.txt) · [Terminal page 1](screenshots/terminal-review/a3-custom-bridge-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-custom-bridge-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-custom-bridge-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-custom-bridge-terminal-04.png) · [Terminal page 5](screenshots/terminal-review/a3-custom-bridge-terminal-05.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 2 — Output of `docker network ls`

[Original record/source](evidence/2026-09-26/a3-custom-bridge.txt) · [Terminal page 1](screenshots/terminal-review/a3-custom-bridge-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-custom-bridge-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-custom-bridge-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-custom-bridge-terminal-04.png) · [Terminal page 5](screenshots/terminal-review/a3-custom-bridge-terminal-05.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 3 — Frontend Dockerfile

[Original record/source](evidence/2026-09-26/a3-custom-bridge.txt) · [Terminal page 1](screenshots/terminal-review/a3-custom-bridge-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-custom-bridge-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-custom-bridge-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-custom-bridge-terminal-04.png) · [Terminal page 5](screenshots/terminal-review/a3-custom-bridge-terminal-05.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 4 — Successful `docker build` for the frontend

[Original record/source](evidence/2026-09-26/a3-custom-bridge-build-stderr.txt) · [Terminal page 1](screenshots/terminal-review/a3-custom-bridge-build-stderr-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-custom-bridge-build-stderr-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-custom-bridge-build-stderr-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-custom-bridge-build-stderr-terminal-04.png) · [Terminal page 5](screenshots/terminal-review/a3-custom-bridge-build-stderr-terminal-05.png) · [Terminal page 6](screenshots/terminal-review/a3-custom-bridge-build-stderr-terminal-06.png) · [Terminal page 7](screenshots/terminal-review/a3-custom-bridge-build-stderr-terminal-07.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 5 — Output of `docker ps` showing the frontend container

[Original record/source](evidence/2026-09-26/a3-custom-bridge.txt) · [Terminal page 1](screenshots/terminal-review/a3-custom-bridge-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-custom-bridge-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-custom-bridge-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-custom-bridge-terminal-04.png) · [Terminal page 5](screenshots/terminal-review/a3-custom-bridge-terminal-05.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 6 — Output of `docker ps` showing both frontend and backend containers

[Original record/source](evidence/2026-09-26/a3-custom-bridge.txt) · [Terminal page 1](screenshots/terminal-review/a3-custom-bridge-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-custom-bridge-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-custom-bridge-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-custom-bridge-terminal-04.png) · [Terminal page 5](screenshots/terminal-review/a3-custom-bridge-terminal-05.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 7 — Output of `docker network inspect mynetwork`

[Original record/source](evidence/2026-09-26/a3-custom-bridge.txt) · [Terminal page 1](screenshots/terminal-review/a3-custom-bridge-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-custom-bridge-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-custom-bridge-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-custom-bridge-terminal-04.png) · [Terminal page 5](screenshots/terminal-review/a3-custom-bridge-terminal-05.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 8 — Successful `curl http://<Public-IP>` showing "Hello from Frontend"

[Original record/source](evidence/2026-09-26/a3-custom-bridge.txt) · [Terminal page 1](screenshots/terminal-review/a3-custom-bridge-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-custom-bridge-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-custom-bridge-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-custom-bridge-terminal-04.png) · [Terminal page 5](screenshots/terminal-review/a3-custom-bridge-terminal-05.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 9 — Successful `curl backend` output from the frontend container showing the Nginx Welcome Page

[Original record/source](evidence/2026-09-26/a3-custom-bridge.txt) · [Terminal page 1](screenshots/terminal-review/a3-custom-bridge-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-custom-bridge-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-custom-bridge-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-custom-bridge-terminal-04.png) · [Terminal page 5](screenshots/terminal-review/a3-custom-bridge-terminal-05.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

# Task 3 — Deploy a Multi-Tier Application Using Multiple Docker Networks

## Goal

Build a three-tier app (frontend, backend, MongoDB) across `backend-network` (backend ↔ database) and `frontend-network` (frontend ↔ backend), and verify data flows end to end.

### Evidence

#### Screenshot 1 — Creation of `backend-network`

[Original record/source](evidence/2026-09-26/a3-multiple-networks.txt) · [Terminal page 1](screenshots/terminal-review/a3-multiple-networks-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-multiple-networks-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-multiple-networks-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-multiple-networks-terminal-04.png) · [Terminal page 5](screenshots/terminal-review/a3-multiple-networks-terminal-05.png) · [Terminal page 6](screenshots/terminal-review/a3-multiple-networks-terminal-06.png) · [Terminal page 7](screenshots/terminal-review/a3-multiple-networks-terminal-07.png) · [Terminal page 8](screenshots/terminal-review/a3-multiple-networks-terminal-08.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 2 — Creation of `frontend-network`

[Original record/source](evidence/2026-09-26/a3-multiple-networks.txt) · [Terminal page 1](screenshots/terminal-review/a3-multiple-networks-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-multiple-networks-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-multiple-networks-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-multiple-networks-terminal-04.png) · [Terminal page 5](screenshots/terminal-review/a3-multiple-networks-terminal-05.png) · [Terminal page 6](screenshots/terminal-review/a3-multiple-networks-terminal-06.png) · [Terminal page 7](screenshots/terminal-review/a3-multiple-networks-terminal-07.png) · [Terminal page 8](screenshots/terminal-review/a3-multiple-networks-terminal-08.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 3 — Project folder structure

[Original record/source](evidence/2026-09-26/a3-multiple-networks.txt) · [Terminal page 1](screenshots/terminal-review/a3-multiple-networks-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-multiple-networks-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-multiple-networks-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-multiple-networks-terminal-04.png) · [Terminal page 5](screenshots/terminal-review/a3-multiple-networks-terminal-05.png) · [Terminal page 6](screenshots/terminal-review/a3-multiple-networks-terminal-06.png) · [Terminal page 7](screenshots/terminal-review/a3-multiple-networks-terminal-07.png) · [Terminal page 8](screenshots/terminal-review/a3-multiple-networks-terminal-08.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 4 — Database Dockerfile

[Original record/source](evidence/2026-09-26/a3-multiple-networks.txt) · [Terminal page 1](screenshots/terminal-review/a3-multiple-networks-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-multiple-networks-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-multiple-networks-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-multiple-networks-terminal-04.png) · [Terminal page 5](screenshots/terminal-review/a3-multiple-networks-terminal-05.png) · [Terminal page 6](screenshots/terminal-review/a3-multiple-networks-terminal-06.png) · [Terminal page 7](screenshots/terminal-review/a3-multiple-networks-terminal-07.png) · [Terminal page 8](screenshots/terminal-review/a3-multiple-networks-terminal-08.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 5 — Backend Dockerfile

[Original record/source](evidence/2026-09-26/a3-multiple-networks.txt) · [Terminal page 1](screenshots/terminal-review/a3-multiple-networks-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-multiple-networks-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-multiple-networks-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-multiple-networks-terminal-04.png) · [Terminal page 5](screenshots/terminal-review/a3-multiple-networks-terminal-05.png) · [Terminal page 6](screenshots/terminal-review/a3-multiple-networks-terminal-06.png) · [Terminal page 7](screenshots/terminal-review/a3-multiple-networks-terminal-07.png) · [Terminal page 8](screenshots/terminal-review/a3-multiple-networks-terminal-08.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 6 — Frontend Dockerfile

[Original record/source](evidence/2026-09-26/a3-multiple-networks.txt) · [Terminal page 1](screenshots/terminal-review/a3-multiple-networks-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-multiple-networks-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-multiple-networks-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-multiple-networks-terminal-04.png) · [Terminal page 5](screenshots/terminal-review/a3-multiple-networks-terminal-05.png) · [Terminal page 6](screenshots/terminal-review/a3-multiple-networks-terminal-06.png) · [Terminal page 7](screenshots/terminal-review/a3-multiple-networks-terminal-07.png) · [Terminal page 8](screenshots/terminal-review/a3-multiple-networks-terminal-08.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 7 — Successful Docker image builds (database, backend, frontend)

[Original record/source](evidence/2026-09-26/a3-multiple-networks-build-stderr.txt) · [Terminal page 1](screenshots/terminal-review/a3-multiple-networks-build-stderr-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-multiple-networks-build-stderr-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-multiple-networks-build-stderr-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-multiple-networks-build-stderr-terminal-04.png) · [Terminal page 5](screenshots/terminal-review/a3-multiple-networks-build-stderr-terminal-05.png) · [Terminal page 6](screenshots/terminal-review/a3-multiple-networks-build-stderr-terminal-06.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 8 — Running containers (`docker ps`)

[Original record/source](evidence/2026-09-26/a3-multiple-networks.txt) · [Terminal page 1](screenshots/terminal-review/a3-multiple-networks-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-multiple-networks-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-multiple-networks-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-multiple-networks-terminal-04.png) · [Terminal page 5](screenshots/terminal-review/a3-multiple-networks-terminal-05.png) · [Terminal page 6](screenshots/terminal-review/a3-multiple-networks-terminal-06.png) · [Terminal page 7](screenshots/terminal-review/a3-multiple-networks-terminal-07.png) · [Terminal page 8](screenshots/terminal-review/a3-multiple-networks-terminal-08.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 9 — Output of `docker network inspect backend-network`

[Original record/source](evidence/2026-09-26/a3-multiple-networks.txt) · [Terminal page 1](screenshots/terminal-review/a3-multiple-networks-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-multiple-networks-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-multiple-networks-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-multiple-networks-terminal-04.png) · [Terminal page 5](screenshots/terminal-review/a3-multiple-networks-terminal-05.png) · [Terminal page 6](screenshots/terminal-review/a3-multiple-networks-terminal-06.png) · [Terminal page 7](screenshots/terminal-review/a3-multiple-networks-terminal-07.png) · [Terminal page 8](screenshots/terminal-review/a3-multiple-networks-terminal-08.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 10 — Output of `docker network inspect frontend-network`

[Original record/source](evidence/2026-09-26/a3-multiple-networks.txt) · [Terminal page 1](screenshots/terminal-review/a3-multiple-networks-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-multiple-networks-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-multiple-networks-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-multiple-networks-terminal-04.png) · [Terminal page 5](screenshots/terminal-review/a3-multiple-networks-terminal-05.png) · [Terminal page 6](screenshots/terminal-review/a3-multiple-networks-terminal-06.png) · [Terminal page 7](screenshots/terminal-review/a3-multiple-networks-terminal-07.png) · [Terminal page 8](screenshots/terminal-review/a3-multiple-networks-terminal-08.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 11 — Browser showing the frontend application

![Eze Favour — a3-multitier-browser](screenshots/a3-multitier-browser.png)

---

#### Screenshot 12 — Successful `curl api` from the frontend container

[Original record/source](evidence/2026-09-26/a3-multiple-networks.txt) · [Terminal page 1](screenshots/terminal-review/a3-multiple-networks-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-multiple-networks-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-multiple-networks-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-multiple-networks-terminal-04.png) · [Terminal page 5](screenshots/terminal-review/a3-multiple-networks-terminal-05.png) · [Terminal page 6](screenshots/terminal-review/a3-multiple-networks-terminal-06.png) · [Terminal page 7](screenshots/terminal-review/a3-multiple-networks-terminal-07.png) · [Terminal page 8](screenshots/terminal-review/a3-multiple-networks-terminal-08.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 13 — MongoDB connection using `mongosh`

[Original record/source](evidence/2026-09-26/a3-multiple-networks.txt) · [Terminal page 1](screenshots/terminal-review/a3-multiple-networks-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-multiple-networks-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-multiple-networks-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-multiple-networks-terminal-04.png) · [Terminal page 5](screenshots/terminal-review/a3-multiple-networks-terminal-05.png) · [Terminal page 6](screenshots/terminal-review/a3-multiple-networks-terminal-06.png) · [Terminal page 7](screenshots/terminal-review/a3-multiple-networks-terminal-07.png) · [Terminal page 8](screenshots/terminal-review/a3-multiple-networks-terminal-08.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 14 — Successful document insertion

[Original record/source](evidence/2026-09-26/a3-multiple-networks.txt) · [Terminal page 1](screenshots/terminal-review/a3-multiple-networks-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-multiple-networks-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-multiple-networks-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-multiple-networks-terminal-04.png) · [Terminal page 5](screenshots/terminal-review/a3-multiple-networks-terminal-05.png) · [Terminal page 6](screenshots/terminal-review/a3-multiple-networks-terminal-06.png) · [Terminal page 7](screenshots/terminal-review/a3-multiple-networks-terminal-07.png) · [Terminal page 8](screenshots/terminal-review/a3-multiple-networks-terminal-08.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 15 — Successful retrieval of the inserted document

[Original record/source](evidence/2026-09-26/a3-multiple-networks.txt) · [Terminal page 1](screenshots/terminal-review/a3-multiple-networks-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-multiple-networks-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-multiple-networks-terminal-03.png) · [Terminal page 4](screenshots/terminal-review/a3-multiple-networks-terminal-04.png) · [Terminal page 5](screenshots/terminal-review/a3-multiple-networks-terminal-05.png) · [Terminal page 6](screenshots/terminal-review/a3-multiple-networks-terminal-06.png) · [Terminal page 7](screenshots/terminal-review/a3-multiple-networks-terminal-07.png) · [Terminal page 8](screenshots/terminal-review/a3-multiple-networks-terminal-08.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

# Task 4 — Deploy an Application Using Docker Host Network Mode

## Goal

Deploy an Nginx container (`fastapp`) using Host Network Mode and verify it's reachable without explicit port mapping, then confirm the `NetworkMode` and clean up.

### Evidence

#### Screenshot 1 — Output of `docker run --network host`

[Original record/source](evidence/2026-09-26/a3-host-network.txt) · [Terminal page 1](screenshots/terminal-review/a3-host-network-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-host-network-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-host-network-terminal-03.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 2 — Output of `docker ps` showing the running `fastapp` container

[Original record/source](evidence/2026-09-26/a3-host-network.txt) · [Terminal page 1](screenshots/terminal-review/a3-host-network-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-host-network-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-host-network-terminal-03.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 3 — Browser or terminal displaying the Nginx Welcome Page

[Original record/source](evidence/2026-09-26/a3-host-network.txt) · [Terminal page 1](screenshots/terminal-review/a3-host-network-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-host-network-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-host-network-terminal-03.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 4 — Output of `docker inspect fastapp | grep "NetworkMode"`

[Original record/source](evidence/2026-09-26/a3-host-network.txt) · [Terminal page 1](screenshots/terminal-review/a3-host-network-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-host-network-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-host-network-terminal-03.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

#### Screenshot 5 — Successful cleanup showing `docker stop fastapp` and `docker rm fastapp`

[Original record/source](evidence/2026-09-26/a3-host-network.txt) · [Terminal page 1](screenshots/terminal-review/a3-host-network-terminal-01.png) · [Terminal page 2](screenshots/terminal-review/a3-host-network-terminal-02.png) · [Terminal page 3](screenshots/terminal-review/a3-host-network-terminal-03.png). Direct Code OSS terminal capture while reviewing this dated original log; not a new execution.

---

# LinkedIn Post (Optional)

## Goal

Create a LinkedIn post covering the assignment objective, networking modes explored, key learning outcomes, and a short reflection on Docker networking concepts.

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

- [x] Task 1: Standalone app on default bridge network deployed and verified (Screenshots 1–6)
- [x] Task 2: Custom bridge network with frontend/backend communication verified (Screenshots 1–9)
- [x] Task 3: Multi-tier app across two networks deployed and verified end to end (Screenshots 1–15)
- [x] Task 4: Host network mode deployment verified and cleaned up (Screenshots 1–5)
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

Each figure is captured once and may support multiple related screenshot slots. Page links above identify the same original evidence, not separate repeated executions.

### a3-default-bridge

[Original](evidence/2026-09-26/a3-default-bridge.txt)

![Eze Favour — a3-default-bridge-p01](screenshots/a3-default-bridge-p01.png)

![Eze Favour — a3-default-bridge-p02](screenshots/a3-default-bridge-p02.png)

![Eze Favour — a3-default-bridge-p03](screenshots/a3-default-bridge-p03.png)

![Eze Favour — a3-default-bridge-p04](screenshots/a3-default-bridge-p04.png)

### a3-custom-bridge

[Original](evidence/2026-09-26/a3-custom-bridge.txt)

![Eze Favour — a3-custom-bridge-p01](screenshots/a3-custom-bridge-p01.png)

![Eze Favour — a3-custom-bridge-p02](screenshots/a3-custom-bridge-p02.png)

![Eze Favour — a3-custom-bridge-p03](screenshots/a3-custom-bridge-p03.png)

![Eze Favour — a3-custom-bridge-p04](screenshots/a3-custom-bridge-p04.png)

![Eze Favour — a3-custom-bridge-p05](screenshots/a3-custom-bridge-p05.png)

### a3-custom-bridge-build-stderr

[Original](evidence/2026-09-26/a3-custom-bridge-build-stderr.txt)

![Eze Favour — a3-custom-bridge-build-stderr-p01](screenshots/a3-custom-bridge-build-stderr-p01.png)

![Eze Favour — a3-custom-bridge-build-stderr-p02](screenshots/a3-custom-bridge-build-stderr-p02.png)

![Eze Favour — a3-custom-bridge-build-stderr-p03](screenshots/a3-custom-bridge-build-stderr-p03.png)

![Eze Favour — a3-custom-bridge-build-stderr-p04](screenshots/a3-custom-bridge-build-stderr-p04.png)

![Eze Favour — a3-custom-bridge-build-stderr-p05](screenshots/a3-custom-bridge-build-stderr-p05.png)

![Eze Favour — a3-custom-bridge-build-stderr-p06](screenshots/a3-custom-bridge-build-stderr-p06.png)

![Eze Favour — a3-custom-bridge-build-stderr-p07](screenshots/a3-custom-bridge-build-stderr-p07.png)

![Eze Favour — a3-custom-bridge-build-stderr-p08](screenshots/a3-custom-bridge-build-stderr-p08.png)

![Eze Favour — a3-custom-bridge-build-stderr-p09](screenshots/a3-custom-bridge-build-stderr-p09.png)

### a3-multiple-networks

[Original](evidence/2026-09-26/a3-multiple-networks.txt)

![Eze Favour — a3-multiple-networks-p01](screenshots/a3-multiple-networks-p01.png)

![Eze Favour — a3-multiple-networks-p02](screenshots/a3-multiple-networks-p02.png)

![Eze Favour — a3-multiple-networks-p03](screenshots/a3-multiple-networks-p03.png)

![Eze Favour — a3-multiple-networks-p04](screenshots/a3-multiple-networks-p04.png)

![Eze Favour — a3-multiple-networks-p05](screenshots/a3-multiple-networks-p05.png)

![Eze Favour — a3-multiple-networks-p06](screenshots/a3-multiple-networks-p06.png)

![Eze Favour — a3-multiple-networks-p07](screenshots/a3-multiple-networks-p07.png)

![Eze Favour — a3-multiple-networks-p08](screenshots/a3-multiple-networks-p08.png)

![Eze Favour — a3-multiple-networks-p09](screenshots/a3-multiple-networks-p09.png)

### a3-multiple-networks-build-stderr

[Original](evidence/2026-09-26/a3-multiple-networks-build-stderr.txt)

![Eze Favour — a3-multiple-networks-build-stderr-p01](screenshots/a3-multiple-networks-build-stderr-p01.png)

![Eze Favour — a3-multiple-networks-build-stderr-p02](screenshots/a3-multiple-networks-build-stderr-p02.png)

![Eze Favour — a3-multiple-networks-build-stderr-p03](screenshots/a3-multiple-networks-build-stderr-p03.png)

![Eze Favour — a3-multiple-networks-build-stderr-p04](screenshots/a3-multiple-networks-build-stderr-p04.png)

![Eze Favour — a3-multiple-networks-build-stderr-p05](screenshots/a3-multiple-networks-build-stderr-p05.png)

![Eze Favour — a3-multiple-networks-build-stderr-p06](screenshots/a3-multiple-networks-build-stderr-p06.png)

![Eze Favour — a3-multiple-networks-build-stderr-p07](screenshots/a3-multiple-networks-build-stderr-p07.png)

### a3-host-network

[Original](evidence/2026-09-26/a3-host-network.txt)

![Eze Favour — a3-host-network-p01](screenshots/a3-host-network-p01.png)

![Eze Favour — a3-host-network-p02](screenshots/a3-host-network-p02.png)

![Eze Favour — a3-host-network-p03](screenshots/a3-host-network-p03.png)
