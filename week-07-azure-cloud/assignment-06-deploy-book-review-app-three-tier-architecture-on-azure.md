# Assignment 6 — Capstone: Deploy Book Review App (Three-Tier Architecture) on Azure

Part of the DevOps Micro Internship (DMI) Cohort 3 with Agentic AI

**Verified recovery — 26 September 2026:** this submission now links authentic Azure/app captures and labelled recordings of actual command and Claude results. Codex performed the recovery under Eze Favour’s delegation. [Evidence, limitations and source index](evidence/2026-09-26/README.md).

---

## Purpose

This is the most important assignment of the course. You will deploy the Book Review App in a production-ready, best-practice-compliant three-tier architecture on Azure: separated presentation, application, and database tiers, least-privilege network access, a controlled public entry point, protected secrets, and availability/monitoring evidence.

---

# Task 1 — Design the Azure Three-Tier Architecture

## Goal

Create an architecture diagram and implementation plan identifying the presentation, application, and database components, the chosen Azure services, the public entry point, and the internal traffic paths.

### Evidence

#### Screenshot 1 — Architecture diagram showing the public entry point, three tiers, network boundaries, and traffic flow

![Screenshot 1](screenshots/assignment-06-deploy-book-review-app-three-tier-architecture-on-azure-screencap-1.png)

*Evidence method: labelled saved-output/source viewer, captured in the browser; not a native terminal/editor/portal view. Source: [architecture.svg](recovery/architecture.svg).*

---

#### Screenshot 2 — Written architecture assumptions and selected Azure services

![Screenshot 2](screenshots/assignment-06-deploy-book-review-app-three-tier-architecture-on-azure-screencap-2.png)

*Evidence method: labelled saved-output/source viewer, captured in the browser; not a native terminal/editor/portal view. Source: [architecture-assumptions.txt](evidence/2026-09-26/architecture-assumptions.txt).*

---

# Task 2 — Create the Azure Network Foundation

## Goal

Create a dedicated Resource Group and VNet with separate subnets for the web, application, and database tiers, keeping the application and database tiers without direct public access.

### Evidence

#### Screenshot 3 — Resource Group overview showing the assignment resources

![Screenshot 3](screenshots/assignment-06-deploy-book-review-app-three-tier-architecture-on-azure-screencap-3.png)

*Actual browser capture on 26 September 2026; privacy redactions only where noted in the [manifest](evidence/2026-09-26/screenshot-manifest.json). The browser capture omits address-bar chrome; the verified endpoint is linked in this submission.*

---

#### Screenshot 4 — VNet overview showing the address space and all required subnets

![Screenshot 4](screenshots/assignment-06-deploy-book-review-app-three-tier-architecture-on-azure-screencap-4.png)

*Actual browser capture on 26 September 2026; privacy redactions only where noted in the [manifest](evidence/2026-09-26/screenshot-manifest.json). The browser capture omits address-bar chrome; the verified endpoint is linked in this submission.*

---

#### Screenshot 5 — Route-table or Private DNS evidence where applicable

![Screenshot 5](screenshots/assignment-06-deploy-book-review-app-three-tier-architecture-on-azure-screencap-5.png)

*Evidence method: labelled saved-output/source viewer, captured in the browser; not a native terminal/editor/portal view. Source: [lab-dns.json](evidence/2026-09-26/lab-dns.json).*

---

# Task 3 — Configure Security and Secret Management

## Goal

Apply least-privilege NSG rules so traffic flows Internet → public entry point → web tier → application tier → database tier, and store credentials in Azure Key Vault or another approved secure mechanism.

### Evidence

#### Screenshot 6 — NSG rules proving least-privilege access between the tiers

![Screenshot 6](screenshots/assignment-06-deploy-book-review-app-three-tier-architecture-on-azure-screencap-6.png)

*Evidence method: labelled saved-output/source viewer, captured in the browser; not a native terminal/editor/portal view. Source: [lab-nsg.json](evidence/2026-09-26/lab-nsg.json).*

---

#### Screenshot 7 — Key Vault or approved secret-management configuration (without displaying secret values)

![Screenshot 7](screenshots/assignment-06-deploy-book-review-app-three-tier-architecture-on-azure-screencap-7.png)

*Evidence method: labelled saved-output/source viewer, captured in the browser; not a native terminal/editor/portal view. Source: [lab-keyvault.json](evidence/2026-09-26/lab-keyvault.json).*

---

# Task 4 — Deploy the Presentation (Web) Tier

## Goal

Deploy the Book Review App presentation layer on the approved web-tier compute service, configured to route requests to the internal application-tier endpoint, and not directly exposed except through the public entry service.

### Evidence

#### Screenshot 8 — Web-tier compute overview showing subnet and availability configuration

![Screenshot 8](screenshots/assignment-06-deploy-book-review-app-three-tier-architecture-on-azure-screencap-8.png)

*Evidence method: labelled saved-output/source viewer, captured in the browser; not a native terminal/editor/portal view. Source: [lab-vms.json](evidence/2026-09-26/lab-vms.json).*

---

#### Screenshot 9 — Terminal or service output proving the presentation layer is running

![Screenshot 9](screenshots/assignment-06-deploy-book-review-app-three-tier-architecture-on-azure-screencap-9.png)

*Evidence method: labelled saved-output/source viewer, captured in the browser; not a native terminal/editor/portal view. Source: [runtime-web1.json](evidence/2026-09-26/runtime-web1.json), [runtime-web2.json](evidence/2026-09-26/runtime-web2.json).*

---

# Task 5 — Deploy the Business (Application) Tier

## Goal

Deploy the Book Review App backend privately in the application subnet, configured to use the private database endpoint and secured environment values, reachable only through its internal endpoint.

### Evidence

#### Screenshot 10 — Application-tier compute overview showing private subnet placement

![Screenshot 10](screenshots/assignment-06-deploy-book-review-app-three-tier-architecture-on-azure-screencap-10.png)

*Evidence method: labelled saved-output/source viewer, captured in the browser; not a native terminal/editor/portal view. Source: [lab-vms.json](evidence/2026-09-26/lab-vms.json).*

---

#### Screenshot 11 — Backend process, service, or listening-port evidence

![Screenshot 11](screenshots/assignment-06-deploy-book-review-app-three-tier-architecture-on-azure-screencap-11.png)

*Evidence method: labelled saved-output/source viewer, captured in the browser; not a native terminal/editor/portal view. Source: [runtime-app1.json](evidence/2026-09-26/runtime-app1.json), [runtime-app2.json](evidence/2026-09-26/runtime-app2.json).*

---

#### Screenshot 12 — Internal health-check or API response (without exposing secrets)

![Screenshot 12](screenshots/assignment-06-deploy-book-review-app-three-tier-architecture-on-azure-screencap-12.png)

*Evidence method: labelled saved-output/source viewer, captured in the browser; not a native terminal/editor/portal view. Source: [runtime-app1.json](evidence/2026-09-26/runtime-app1.json), [runtime-app2.json](evidence/2026-09-26/runtime-app2.json).*

---

# Task 6 — Deploy the Managed Database Tier

## Goal

Create a private Azure managed database (public access disabled), with availability/backup/retention settings, the Book Review App schema imported, and access restricted to the application tier only.

### Evidence

#### Screenshot 13 — Database overview showing private connectivity and public access disabled

![Screenshot 13](screenshots/assignment-06-deploy-book-review-app-three-tier-architecture-on-azure-screencap-13.png)

*Actual browser capture on 26 September 2026; privacy redactions only where noted in the [manifest](evidence/2026-09-26/screenshot-manifest.json). The browser capture omits address-bar chrome; the verified endpoint is linked in this submission.*

---

#### Screenshot 14 — Availability, backup, and retention configuration

![Screenshot 14](screenshots/assignment-06-deploy-book-review-app-three-tier-architecture-on-azure-screencap-14.png)

*Evidence method: labelled saved-output/source viewer, captured in the browser; not a native terminal/editor/portal view. Source: [lab-mysql.json](evidence/2026-09-26/lab-mysql.json).*

---

#### Screenshot 15 — Successful schema or connectivity verification (without exposing credentials)

![Screenshot 15](screenshots/assignment-06-deploy-book-review-app-three-tier-architecture-on-azure-screencap-15.png)

*Evidence method: labelled saved-output/source viewer, captured in the browser; not a native terminal/editor/portal view. Source: [schema-book.json](evidence/2026-09-26/schema-book.json), [independent-sql.json](evidence/2026-09-26/independent-sql.json).*

---

# Task 7 — Configure Traffic Management, Availability, and Monitoring

## Goal

Configure the approved public entry service with health probes and backend pools, internal routing for the application tier where required, and enable Azure Monitor/diagnostics/logs/alerts for the key resources.

### Evidence

#### Screenshot 16 — Public entry service showing listener, frontend endpoint, and healthy web targets

![Screenshot 16](screenshots/assignment-06-deploy-book-review-app-three-tier-architecture-on-azure-screencap-16.png)

*Evidence method: labelled saved-output/source viewer, captured in the browser; not a native terminal/editor/portal view. Source: [lab-load-balancers.json](evidence/2026-09-26/lab-load-balancers.json).*

---

#### Screenshot 17 — Internal application-tier load-balancing or routing configuration where applicable

![Screenshot 17](screenshots/assignment-06-deploy-book-review-app-three-tier-architecture-on-azure-screencap-17.png)

*Evidence method: labelled saved-output/source viewer, captured in the browser; not a native terminal/editor/portal view. Source: [lab-load-balancers.json](evidence/2026-09-26/lab-load-balancers.json).*

---

#### Screenshot 18 — Azure Monitor, diagnostic settings, logs, metrics, or alert evidence

![Screenshot 18](screenshots/assignment-06-deploy-book-review-app-three-tier-architecture-on-azure-screencap-18.png)

*Evidence method: labelled saved-output/source viewer, captured in the browser; not a native terminal/editor/portal view. Source: [lab-alerts.json](evidence/2026-09-26/lab-alerts.json), [lb-metrics.json](evidence/2026-09-26/lb-metrics.json).*

---

# Task 8 — Validate the Production-Style Deployment

## Goal

Confirm the Book Review App works end to end through the public endpoint, with at least one database read and one write, confirm private tiers are not internet-reachable, and complete a safe availability test.

### Evidence

#### Screenshot 19 — Browser showing the Book Review App through the public endpoint

![Screenshot 19](screenshots/assignment-06-deploy-book-review-app-three-tier-architecture-on-azure-screencap-19.png)

*Actual browser capture on 26 September 2026; privacy redactions only where noted in the [manifest](evidence/2026-09-26/screenshot-manifest.json). The browser capture omits address-bar chrome; the verified endpoint is linked in this submission.*

---

#### Screenshot 20 — Proof of successful database-backed read and write operations

![Screenshot 20](screenshots/assignment-06-deploy-book-review-app-three-tier-architecture-on-azure-screencap-20.png)

*Actual browser capture on 26 September 2026; privacy redactions only where noted in the [manifest](evidence/2026-09-26/screenshot-manifest.json). The browser capture omits address-bar chrome; the verified endpoint is linked in this submission.*

---

#### Screenshot 21 — Evidence that private tiers are not publicly accessible

![Screenshot 21](screenshots/assignment-06-deploy-book-review-app-three-tier-architecture-on-azure-screencap-21.png)

*Evidence method: labelled saved-output/source viewer, captured in the browser; not a native terminal/editor/portal view. Source: [network-isolation.json](evidence/2026-09-26/network-isolation.json).*

---

#### Screenshot 22 — Availability-test and healthy-target evidence

![Screenshot 22](screenshots/assignment-06-deploy-book-review-app-three-tier-architecture-on-azure-screencap-22.png)

*Evidence method: labelled saved-output/source viewer, captured in the browser; not a native terminal/editor/portal view. Source: [availability-test.json](evidence/2026-09-26/availability-test.json).*

---

#### Public Endpoint

[Book Review — verified live HTTP lab](http://4.225.220.198/)

---

### Notes

The recovered deployment has two private web VMs and two private API VMs across zones 1 and 2, public/internal load balancers, Key Vault managed-identity reads and a private MySQL server. Browser login, review submission and reload succeeded; an independent SQL query confirmed review 2. Backend CRUD-only credentials verify MySQL TLS certificates. The web subnet could not reach MySQL directly, while the app subnet could. The separate EpicBook VM is allowed to reach its own database on the same server from one exact private IP.

The availability test stopped Nginx on web1, waited 25 seconds for probes, then received 12/12 database-backed responses from web2. Web1 was restored and both nodes were observed again. An Azure Monitor health alert is enabled, with actual metric samples retained. The deployment uses HTTP at the public entry and a single MySQL instance with seven-day backups; it is a production-style learning lab, not a claim of complete production readiness, database HA, zero transition downtime or tested backup restoration.

Browser verification caught and fixed a duplicated `/api` prefix and unreadable dark-mode text. The API tests alone had not revealed those frontend defects. Codex performed the operations and prepared this reflection under delegation.

---

# Submission Instructions

- Add all required screenshots and links in your submission
- Do not expose passwords, keys, connection strings, or subscription IDs

---

# Completion Checklist

- [x] Task 1: Architecture diagram and assumptions documented (Screenshots 1–2)
- [x] Task 2: Network foundation created with isolated tiers (Screenshots 3–5)
- [x] Task 3: Least-privilege security and secret management configured (Screenshots 6–7)
- [x] Task 4: Presentation tier deployed (Screenshots 8–9)
- [x] Task 5: Application tier deployed privately (Screenshots 10–12)
- [x] Task 6: Managed database tier deployed privately (Screenshots 13–15)
- [x] Task 7: Public entry, internal routing, and monitoring configured (Screenshots 16–18)
- [x] Task 8: End-to-end validation and availability test completed (Screenshots 19–22, Public Endpoint, Notes)
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
