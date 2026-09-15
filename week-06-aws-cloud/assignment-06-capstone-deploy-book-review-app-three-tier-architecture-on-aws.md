# Assignment 6 — Capstone Assignment — Deploy Book Review App (Three-Tier Architecture) on AWS

Part of the DevOps Micro Internship (DMI) Cohort 3 with Agentic AI

---

## Purpose

This is the most important assignment of the course. You will deploy the Book Review App in a fully production-style three-tier architecture on AWS: a Next.js Web Tier behind Nginx and a public ALB, a private Node.js/Express App Tier behind an internal ALB, and a private Multi-AZ MySQL RDS database with a read replica. You are expected to design, deploy, isolate, debug, and document the result independently.

## Current verification — 15 September 2026

**Status: existing deployment partially verified; no new deployment or remediation performed.** Before rebuilding anything, 18 read-only AWS API queries checked the two named Book Review VPCs. The [timestamped, redacted preflight record](assignment-06-capstone/evidence/preflight-2026-09-15.json) is current API evidence, not a browser test or replacement for the required console screenshots.

| Requirement | Observed now | Remaining work |
| --- | --- | --- |
| Existing capstone location | `bookreview-vpc` in **`eu-north-1`**, `vpc-0f7b4a0baa38141ca` | Reuse this deployment rather than build a duplicate in another region. |
| Six subnets across two AZs | Two Web subnets route to an Internet Gateway; two App subnets route to NAT; two DB subnets have only the VPC-local route. | Capture the route/subnet console views. Names inherited from older work are not reliable tier labels; use IDs and routes. |
| Web and App instances | One running `t3.micro` per tier, both in `eu-north-1a`; the App instance has no public IPv4 or IPv6 address. | Inspect Nginx/Next.js/runtime configuration through approved administrative access. One instance per tier is **not AZ-redundant compute**. |
| Internal ALB and app target | Internal scheme, active, two AZs; `bookreview-app-tg` reports **healthy** on port `3001`, health path `/health`. | Capture the actual response and current application revision. The earlier timeout is no longer observed, but its cause and remediation were not established by this check. |
| Primary database | `bookreview-db` is available, MySQL `8.4.9`, `db.t4g.micro`, **Multi-AZ**, encrypted and **not publicly accessible**, with 20 GB gp2 storage and one-day backup retention. Its attached SG permits MySQL from `SG-App`. | Verify application write/read and persistence; a healthy ALB target alone does not establish database functionality. |
| Public ALB | **Absent from the capstone VPC.** An existing `SG-Public-ALB` is allowed into `SG-Web` on port 80. | Provision the public ALB/listener/web target group through reviewed Terraform, then prove the UI works at its DNS name. |
| Read replica | The primary lists **no read replicas**. | Provision and verify a separate private encrypted read replica; the Multi-AZ standby is not a read replica. |
| Administrative access | The only configured CLI profile is `default`, resolving to **root**. Neither capstone instance appears in the scoped SSM managed-instance query, and neither has an instance profile. | Establish approved non-root deployment access and a safe runtime-inspection path before infrastructure or application changes. Do not open SSH to the world. |

The other `bookreview-vpc` in **`us-east-1`** has no instances, load balancers, target groups, databases or NAT gateways in the scoped queries. That is not an account-wide cleanup claim. The Stockholm VPC also contains an available **`ha-mysql-db`**, which is outside this capstone's change scope. Existing instances, NAT, ALB and databases can continue to incur charges. **No resource was created, changed, stopped or deleted**, and Assignment 4 and the isolated Assignment 5 lab were not altered.

### Application prerequisites checked, not deployed

The course links to [the instructor's Book Review repository](https://github.com/pravinmishraaws/book-review-app), inspected at revision `84280063bea7ccd5144dafa2b969ec4e2e69ffbb`. This is a reference revision, **not a verified revision of the running servers**. No upstream JavaScript, committed `.env`, or vendored `node_modules` was copied into this repository; no application dependencies were installed.

- The [reference backend](https://github.com/pravinmishraaws/book-review-app/blob/84280063bea7ccd5144dafa2b969ec4e2e69ffbb/backend/src/server.js) defaults to port **5000**, while this ALB targets **3001**. Confirm the live `PORT` and listening address rather than replacing the currently healthy process blindly. That source file does not declare `/health`; inspect the deployed implementation before changing its health check.
- The [frontend API client](https://github.com/pravinmishraaws/book-review-app/blob/84280063bea7ccd5144dafa2b969ec4e2e69ffbb/frontend/src/services/api.js) uses `NEXT_PUBLIC_API_URL` and appends `/users`, `/books` and `/reviews`; the backend mounts them below `/api`. A candidate same-origin setup is a **build-time `/api` base** with Nginx forwarding `/api/...` unchanged to the internal ALB. Validate this end to end; do not put a private ALB hostname in browser-facing configuration or silently trust the conflicting upstream comment about `/api`.
- The [database configuration](https://github.com/pravinmishraaws/book-review-app/blob/84280063bea7ccd5144dafa2b969ec4e2e69ffbb/backend/src/config/db.js) uses `DB_HOST`, `DB_NAME`, `DB_PASS`, `DB_PORT` and `DB_USER`. Do not publish their live values. It does not configure a Sequelize replication pool: creating a replica alone does not route application reads to it.
- The reference backend invokes schema synchronization with `alter: true` during startup. Review schema/data impact before restarting with a different revision. Review dependency support/security and configuration before public exposure; no production-readiness or security certification is claimed.

### Proposed additions and approval gates

The [Stockholm pricing record](assignment-06-capstone/evidence/incremental-cost-estimate.json) models **only** one new public ALB, a one-LCU allowance, two new public IPv4 addresses, and a private `db.t4g.micro` read replica with 20 GB gp2 storage:

| Proposed addition | Normalized monthly USD (730 hours) |
| --- | ---: |
| Public ALB | 17.48 |
| One used-LCU allowance | 5.55 |
| Two public IPv4 addresses | 7.30 |
| Single-AZ read-replica compute | 11.68 |
| Read-replica storage | 2.40 |
| **Incremental subtotal, calculated before rounding** | **44.40** |

The normalized four-hour equivalent is about **$0.24**, **not** a guaranteed bill or the cost of the whole lab. Existing resources, variable usage, billing minimums, taxes, additional compute and cleanup delays are excluded. Rounded rows can differ from the subtotal by one cent. A **$5 allowance for new additions is proposed, not approved or enforced**. The earlier Assignment 5 retest proposal does not authorize this spend; no timer or budget alarm was installed.

**Next execution steps, still pending:**

1. Establish approved non-root AWS access, an authorized way to inspect the existing web/app hosts, and explicit approval of spend, exact scope and cleanup/retention intent.
2. Capture the installed source revision, Nginx routing, process ports, health response and redacted configuration evidence. Confirm browser API routing and database access before overwriting any healthy service.
3. Author and validate a dedicated **new-additions-only Terraform state** for the missing public entry and replica. Reference the existing VPC/subnets/instances/internal ALB/primary read-only; do not import shared resources into a state that will later be destroyed wholesale. No new Terraform configuration or cloud plan has been executed in this preflight.
4. Review the proposed plan, then apply only after approval. Prove public web-target health, UI login/CRUD using synthetic data, primary persistence, and the available replica's source relationship/private settings/replication. Do not claim application read splitting unless separately configured and tested.
5. Capture genuine, redacted console and browser proof under the learner's identity, update the historical sections below, and verify the existing LinkedIn post rather than publishing a duplicate.
6. For an approved short run, abort testing without a stable baseline by 60 minutes and start removing only new additions by 120 minutes, with a four-hour cleanup target. Continue supervised cleanup if needed; preserve the primary, shared VPC, `ha-mysql-db`, Assignment 4 and all pre-existing resources. Retain state and report residual resources honestly.

## Evidence audit — 13 September 2026 (historical screenshots)

The assessment below records what the original screenshots proved at that time. The current API verification above supersedes their app-target and primary-database uncertainty, but does not manufacture missing UI/replica screenshots or a remediation history.

**Status: partial deployment with an unresolved application target-health failure in the submitted captures.** This audit describes historical evidence, not the current AWS environment. The web and app instances are running, and the Book Review RDS instance explicitly shows **Publicly accessible: No**. However, the app target on port `3001` is **Unhealthy — Request timed out**. No submitted capture establishes a working public ALB endpoint, the Book Review UI, Multi-AZ RDS configuration, or an available read replica.

The earlier screenshot mapping mislabeled an internal ALB as the public entry point, a security-group inventory as the app UI, and an unrelated RDS inventory as a LinkedIn post. The sections below correct those mappings and identify the remaining proof.

---

# Task 1 — Architecture Diagram

## Goal

Create an architecture diagram showing the custom VPC (10.0.0.0/16), the six subnets across two Availability Zones (two public Web Tier, two private App Tier, two private Database Tier), the public ALB, Web Tier EC2/Nginx, internal ALB, private App Tier EC2, private Multi-AZ RDS with its read replica, and the permitted traffic flow.

### Evidence

#### Diagram image or link

**Intended architecture.** This diagram documents the required design; it is not proof that every component was deployed or healthy. Only one web instance and one app instance appear in the submitted evidence, and the internal ALB scheme and database replication settings still need verification.

```mermaid
flowchart TB
    clients[Internet clients] -->|HTTP 80| publicalb
    subgraph vpc["Custom VPC: 10.0.0.0/16 — target design"]
        publicalb["Public ALB across both Web subnets"]
        internalalb["Internal ALB across both App subnets"]
        subgraph aza["Availability Zone A: eu-north-1a"]
            weba["Public Web subnet A: EC2 / Nginx / Next.js"]
            appa["Private App subnet A: EC2 / Node.js / Express"]
            dba["Private DB subnet A: RDS MySQL primary"]
        end
        subgraph azb["Availability Zone B: eu-north-1b"]
            webb["Public Web subnet B: Web tier capacity"]
            appb["Private App subnet B: App tier capacity"]
            dbb["Private DB subnet B: RDS Multi-AZ standby"]
            replica["Private DB subnet B: separate RDS read replica"]
        end
        publicalb -->|HTTP 80| weba
        publicalb -->|HTTP 80| webb
        weba -->|TCP 3001| internalalb
        webb -->|TCP 3001| internalalb
        internalalb -->|TCP 3001| appa
        internalalb -->|TCP 3001| appb
        appa -->|MySQL 3306 via primary endpoint| dba
        appb -->|MySQL 3306 via primary endpoint| dba
        dba -. synchronous Multi-AZ standby replication .-> dbb
        dba -. asynchronous read-replica replication .-> replica
    end
```

The standby and read replica are **separate database resources with different roles**: Multi-AZ provides failover, while a read replica supports read scaling and is not the Multi-AZ standby. Their placement is illustrative and can change. The replica needs its own endpoint and must be configured separately if the application is to use it for reads.

Intended security-group flow: internet to public ALB on port 80; public ALB group to Web group on port 80; Web group to internal ALB group on port 3001; internal ALB group to App group on port 3001; App group to DB group on port 3306. Restrict administrative access separately. Web subnets need Internet Gateway routing; App and DB subnets must not have direct Internet Gateway routes or public addresses. NAT may supply outbound access for private app bootstrap without exposing inbound access. These routing and attachment settings remain evidence requirements.

---

# Task 2 — AWS Region & Services Used

## Goal

Record the AWS Region used and list every AWS service used across networking, compute, load balancing, security, and the database.

### Notes

**Region:**

**Europe (Stockholm), `eu-north-1`.** The EC2 hostnames, RDS endpoint, target AZ, and DB subnet-group ARN identify this region. The DB subnet group lists `eu-north-1a` and `eu-north-1b`.

---

**Services:**

| Service/component | Evidence status |
| --- | --- |
| Amazon VPC and subnets | `bookreview-vpc` (`vpc-0f7b4a0baa38141ca`), web/app subnet attachments, and two DB subnets appear in console captures. The six-subnet inventory, VPC CIDR, and routes are not captured together. |
| Amazon EC2 | Running `bookreview-web-1` and `bookreview-app-server-a` instances are shown. |
| VPC security groups | Web inbound rules, an internal-ALB group's inbound rule, and a group inventory are shown. Full App/DB rules and final ALB attachments are not shown. |
| Elastic Load Balancing | `bookreview-internal-alb` listener forwards to `bookreview-app-tg`; the app target times out. Public ALB details and the internal ALB's **Scheme** field are missing. |
| Amazon RDS for MySQL | `bookreview-db`, its non-public setting, and a DB subnet group across two AZs are shown. A read-replica creation form is present, but completed replica creation and Multi-AZ configuration are unproven. |
| Internet Gateway, NAT Gateway, route tables | Described in the intended design and submitted post; deployment configuration is not established by these captures. |
| Nginx, Next.js, Node.js/Express | Required application software, not separate AWS services. Installation, service health, and end-to-end operation need runtime evidence. |

---

# Task 3 — Public Entry Point

## Goal

Confirm the Book Review App loads through the public ALB DNS name.

### Evidence

#### Public ALB DNS

**Still incomplete.** The 15 September API preflight found no public ALB in the capstone VPC. After an approved Terraform deployment, supply the Book Review public ALB's DNS name and a browser capture showing the application at that URL. Also capture its **Internet-facing** scheme, **Active** status, listener forwarding, and healthy web targets. An EC2 public IP or the ALB from the separate two-tier assignment is not this capstone's public ALB endpoint.

---

# Task 4 — Evidence Screenshots

These are the **historical captures** audited on 13 September. The current API record above establishes additional facts, but these images have not been replaced with new console or browser proof.

## Goal

Capture visual proof of every tier and load balancer.

### Evidence

#### Web EC2

![Running Book Review web EC2 instance and web security-group rules](screenshots/01_Web_EC2.png)

The capture shows `bookreview-web-1` running with public IPv4 `51.21.245.114` and private IPv4 `10.0.1.133`. HTTP ingress references the public-ALB security group, while SSH is scoped to one IPv4 address. This does not prove that Nginx/Next.js is serving the application.

---

#### App EC2

![Running Book Review app EC2 instance with no public address and passing EC2 status checks](screenshots/02_App_EC2.png)

The capture shows `bookreview-app-server-a` running at private IPv4 `10.0.3.203`, with no public IPv4 or IPv6 address displayed. EC2 system, instance, and EBS checks pass. Those checks do not establish that the Node.js process responds on port 3001.

---

#### Public ALB / app entry point

**Missing.** The previously linked image is the internal ALB listener, now correctly placed below. Capture the public ALB and its healthy web targets, and record the verified DNS name in Task 3.

---

#### Internal ALB

![Book Review internal ALB listener forwarding to the app target group](screenshots/03_Internal_ALB.png)

The listener forwards to `bookreview-app-tg`. Its existence does not prove that the target is healthy or that the ALB has the required internal scheme.

![Book Review app target unhealthy on port 3001 with Request timed out](screenshots/04_App_Target_Health_UNHEALTHY.png)

One target is registered in `eu-north-1a` on port `3001`, with **Unhealthy — Request timed out**. No after-fix healthy capture is available.

![Internal ALB security group permits port 3001 from a web security-group reference](screenshots/05_Internal_ALB_SG.png)

This shows an intended rule permitting the web security group to reach port `3001`; the capture does not verify the group's attachment to the internal ALB or the App group's inbound rules.

---

#### RDS + replica

![Book Review MySQL RDS connectivity settings with Publicly accessible set to No](screenshots/06_BookReview_RDS.png)

The capture shows `bookreview-db`, MySQL port `3306`, `bookreview-db-subnet-group`, `SG-DB`, and **Publicly accessible: No**. This is positive evidence for the database's public-access setting. It does not show **Multi-AZ = Yes** or application persistence.

![Book Review DB subnet group containing private-a and private-b subnets across two AZs](screenshots/09_RDS_Subnet_Group.png)

The subnet group spans `eu-north-1a` (`10.0.5.0/24`) and `eu-north-1b` (`10.0.6.0/24`). Two subnet-group AZs do not prove that the database itself has Multi-AZ enabled; subnet route tables are also not shown.

![RDS read-replica creation form with no completed-replica status](screenshots/08_Read_Replica_Creation.png)

This form does not prove that a replica was created. Supply the available replica's identifier, source relationship, endpoint, and private-access setting, plus the primary's Multi-AZ configuration. The separate `07_RDS_Databases_List.png` shows EpicBook/HA databases rather than a completed Book Review replica, so it is not used as capstone replica evidence.

---

#### App UI proof

**Missing.** Supply a Book Review browser page at the public ALB URL and evidence of an application write followed by a read of the stored record.

#### Supporting security-group inventory

![Security-group inventory including Book Review web, app, and ALB groups](screenshots/10_Security_Groups.png)

This is a group inventory, not an application UI capture. Names and rule counts do not establish least-privilege rules or correct resource attachments.

---

# Task 5 — Summary

## Goal

Summarize what worked in the final deployment, the issues encountered and how each was fixed, and the tools or sources used to research and debug.

### Notes

**What worked:**

The historical captures establish running Web and App EC2 instances, passing EC2 checks on the app instance, an ALB listener forwarding to an app target group, and a MySQL RDS instance configured without public accessibility. A DB subnet group spans two AZs. They do **not** establish a successful end-to-end three-tier deployment: the app target is unhealthy, and public-entry/UI/database-operation evidence is missing.

---

**Issues + fixes:**

| Observed issue | Verified fix/status | Next verification |
| --- | --- | --- |
| Historical `bookreview-app-tg` target on port 3001 reports **Request timed out** | The 15 September API check reports **healthy**. No remediation was performed during that check; the earlier cause/fix is still unknown. | Capture current healthy target status and inspect the deployed health implementation. Do not claim a particular timeout fix without logs or a recorded change. |
| Public ALB and app UI evidence were mapped to unrelated panels | Screenshot labels corrected in this documentation audit. | Capture the actual public ALB and UI, then verify application read/write. |
| RDS/replica claims exceeded the screenshots | Public-access evidence is now distinguished from unverified Multi-AZ and replica claims. | Capture primary Multi-AZ configuration and an available replica linked to that primary. |

The diagnostic steps above are recommendations, not commands already executed or proven remediations. Passing EC2 checks alone does not resolve an application target timeout.

---

**Tools/sources used:**

The review used the submitted AWS Management Console screenshots: EC2 summaries/status checks, ALB listener and target-health panels, security-group rules, RDS connectivity, and the DB subnet group. Local OCR and small visual previews were used to check the mappings. The submitted LinkedIn screenshot describes the project and mentions the internal-ALB timeout. No application/Nginx logs, successful remediation output, or cited research/debugging references were supplied, so their use and results are not asserted here.

---

# LinkedIn Post (Required)

## Goal

Publish a LinkedIn post sharing the capstone deployment, including the public ALB DNS (or a redacted screenshot), three to five lines on what you built and why it is production-style, and one proof screenshot.

## Evidence

#### LinkedIn Post URL

Submitted link: [LinkedIn capstone short link](https://lnkd.in/p/eCyHf-sv).

A matching-topic post screenshot is available below. The short link resolves to [this LinkedIn destination](https://www.linkedin.com/posts/eze-favour-52732752_aws-devops-cloudcomputing-share-7499769495050276864-lRs_/), but retrieval returned generic LinkedIn sign-up content rather than the post, so its live content could not be verified. The captured portion of the post does not establish the required public ALB URL or attached deployment proof. Keep the publication requirement open until those details are verified.

---


#### Screenshot of LinkedIn post

![Eze Favour LinkedIn post describing the three-tier Book Review capstone and an internal ALB timeout](image-1.png)

---

# Submission Instructions

- Add all required screenshots and links in your submission
- Do not expose passwords, RDS credentials, connection strings, private keys, or account IDs

Existing source captures contain account IDs in console fields/ARNs. They were not altered in this documentation audit. Prepare redacted copies before checking the no-sensitive-data item.

---

# Completion Checklist

- [x] Task 1: Intended architecture diagram completed; deployment proof remains separate
- [x] Task 2: AWS Region and services documented, with evidence limits stated
- [ ] Task 3: Public ALB DNS confirmed working
- [ ] Task 4: All six evidence screenshots captured (Web Tier, App Tier, both ALBs, RDS + replica, app UI)
- [x] Task 5: Evidence-based deployment summary completed; timeout remediation history remains unverified
- [x] Current deployment rechecked read-only; internal app target healthy and primary Multi-AZ verified ([record](assignment-06-capstone/evidence/preflight-2026-09-15.json))
- [ ] Missing public ALB and private read replica provisioned and verified
- [ ] Non-root deployment access, runtime access and incremental spending approved
- [ ] LinkedIn post published and URL submitted
- [x] Existing App Tier and primary Database Tier confirmed not publicly accessible by current API configuration (not a security certification; replica still absent)
- [ ] No sensitive data exposed (historical screenshots and Git history still require review/redaction)

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
