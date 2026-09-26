# Assignment 2 — Deploy a React App on an Azure VM (Ubuntu + Nginx)

Part of the DevOps Micro Internship (DMI) Cohort 3 with Agentic AI

**Verified recovery — 26 September 2026:** this submission now links authentic Azure/app captures and labelled recordings of actual command and Claude results. Codex performed the recovery under Eze Favour’s delegation. [Evidence, limitations and source index](evidence/2026-09-26/README.md).

---

## Purpose

In this assignment, you will provision a secure Ubuntu virtual machine in Microsoft Azure, build the `my-react-app` React application, and serve the production static build through Nginx. You will validate the deployment from the VM's public IP.

---

# Task 1 — Create a Resource Group

## Goal

Create the Azure Resource Group `react-app-rg` in a region close to you.

### Evidence

#### Screenshot 1 — Resource Group overview showing the name and region

![Screenshot 1](screenshots/assignment-02-deploy-a-react-app-on-an-azure-vm-screencap-1.png)

*Actual browser capture on 26 September 2026; privacy redactions only where noted in the [manifest](evidence/2026-09-26/screenshot-manifest.json). The browser capture omits address-bar chrome; the verified endpoint is linked in this submission.*

---

# Task 2 — Provision Ubuntu VM (20.04) with Correct Networking

## Goal

Create an Ubuntu 20.04 LTS VM (size B1s) with a Network Security Group allowing SSH (22, restricted to your IP where possible) and HTTP (80).

### Evidence

#### Screenshot 2 — Azure VM overview page showing the VM name, Resource Group, and region

![Screenshot 2](screenshots/assignment-02-deploy-a-react-app-on-an-azure-vm-screencap-2.png)

*Actual browser capture on 26 September 2026; privacy redactions only where noted in the [manifest](evidence/2026-09-26/screenshot-manifest.json). The browser capture omits address-bar chrome; the verified endpoint is linked in this submission.*

---

#### Screenshot 3 — Network Security Group inbound rules showing ports 22 and 80 allowed

![Screenshot 3](screenshots/assignment-02-deploy-a-react-app-on-an-azure-vm-screencap-3.png)

*Actual browser capture on 26 September 2026; privacy redactions only where noted in the [manifest](evidence/2026-09-26/screenshot-manifest.json). The browser capture omits address-bar chrome; the verified endpoint is linked in this submission.*

---

# Task 3 — SSH into the Azure VM

## Goal

Connect to the VM over SSH and confirm the Linux prompt is visible.

### Evidence

#### Screenshot 4 — Terminal showing a successful SSH login with the prompt visible

![Screenshot 4](screenshots/assignment-02-deploy-a-react-app-on-an-azure-vm-screencap-4.png)

*Evidence method: labelled saved-output/source viewer, captured in the browser; not a native terminal/editor/portal view. Source: [react-ssh-inspection.txt](evidence/2026-09-26/react-ssh-inspection.txt).*

---

# Task 4 — Update OS and Install Prerequisites (Git, Node.js, npm)

## Goal

Update Ubuntu and install Git, Node.js, and npm.

### Evidence

#### Screenshot 5 — Terminal output showing `node -v` and `npm -v`

![Screenshot 5](screenshots/assignment-02-deploy-a-react-app-on-an-azure-vm-screencap-5.png)

*Evidence method: labelled saved-output/source viewer, captured in the browser; not a native terminal/editor/portal view. Source: [react-ssh-inspection.txt](evidence/2026-09-26/react-ssh-inspection.txt).*

---

# Task 5 — Clone and Build the React App

## Goal

Clone `my-react-app`, install dependencies, and run `npm run build` to produce the `build/` directory.

### Evidence

#### Screenshot 6 — Terminal showing successful `npm run build` completion and `ls -la build` output

![Screenshot 6](screenshots/assignment-02-deploy-a-react-app-on-an-azure-vm-screencap-6.png)

*Evidence method: labelled saved-output/source viewer, captured in the browser; not a native terminal/editor/portal view. Source: [react-build.txt](evidence/2026-09-26/react-build.txt).*

---

# Task 6 — Install and Configure Nginx to Serve the React Build

## Goal

Install Nginx and configure it to serve the `build/` directory with `try_files $uri /index.html;` for SPA routing support.

### Evidence

#### Screenshot 7 — Successful `sudo nginx -t` output

![Screenshot 7](screenshots/assignment-02-deploy-a-react-app-on-an-azure-vm-screencap-7.png)

*Evidence method: labelled saved-output/source viewer, captured in the browser; not a native terminal/editor/portal view. Source: [react-nginx-config.txt](evidence/2026-09-26/react-nginx-config.txt).*

---

#### Screenshot 8 — Nginx configuration snippet showing the build root and `try_files` directive

![Screenshot 8](screenshots/assignment-02-deploy-a-react-app-on-an-azure-vm-screencap-8.png)

*Evidence method: labelled saved-output/source viewer, captured in the browser; not a native terminal/editor/portal view. Source: [react-nginx-config.txt](evidence/2026-09-26/react-nginx-config.txt).*

---

# Task 7 — Test the Deployment (Public IP)

## Goal

Confirm the React app loads through the VM's public IP, navigation works, and a nested route still works after a page refresh.

### Evidence

#### Screenshot 9 — Browser showing the React app with the public IP visible in the address bar

![Screenshot 9](screenshots/assignment-02-deploy-a-react-app-on-an-azure-vm-screencap-9.png)

*Actual browser capture on 26 September 2026; privacy redactions only where noted in the [manifest](evidence/2026-09-26/screenshot-manifest.json). The browser capture omits address-bar chrome; the verified endpoint is linked in this submission.*

---

# Task 8 — Basic Hardening (Recommended)

## Goal

Restrict the SSH Network Security Group rule to your IP if not already restricted, and confirm the firewall does not block port 80.

### Evidence

#### Screenshot 10 (optional) — Network Security Group rule showing SSH restricted to your IP

![Screenshot 10](screenshots/assignment-02-deploy-a-react-app-on-an-azure-vm-screencap-10.png)

*Actual browser capture on 26 September 2026; privacy redactions only where noted in the [manifest](evidence/2026-09-26/screenshot-manifest.json). The browser capture omits address-bar chrome; the verified endpoint is linked in this submission.*

---

## Verified implementation notes

Live app: [React on the original Azure VM](http://4.223.123.39/). [Nested route refresh](http://4.223.123.39/dashboard) also succeeded. The recovered VM uses Ubuntu 20.04 and Standard_F1als_v7, rather than the suggested B1s. Node 20.20.2, npm 10.8.2 and Git 2.25.1 were observed. A fresh production build passed in a separate directory; the existing served build and original displayed deployment date were preserved. SSH is restricted to the current operator /32.

![Actual nested-route refresh](screenshots/react-route-refresh-20260926.png)

# Submission Instructions

- Add all required screenshots in your submission
- Do not expose SSH private keys, passwords, or Azure account information

---

# Completion Checklist

- [x] Task 1: Resource Group created (Screenshot 1)
- [x] Task 2: Ubuntu VM provisioned with correct NSG rules (Screenshots 2 & 3)
- [x] Task 3: SSH access verified (Screenshot 4)
- [x] Task 4: Git, Node.js, and npm installed (Screenshot 5)
- [x] Task 5: React app built successfully (Screenshot 6)
- [x] Task 6: Nginx configured with SPA routing support (Screenshots 7 & 8)
- [x] Task 7: App verified via the VM public IP, including route refresh (Screenshot 9)
- [x] Task 8: SSH hardening applied (Screenshot 10, optional)
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

