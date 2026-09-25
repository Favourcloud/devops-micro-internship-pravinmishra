# Capstone Assignment — Deploy the Book Review App Using Terraform and Claude Code Agentic AI

Part of the DevOps Micro Internship (DMI) Cohort 3 with Agentic AI

---

## Student Details

**Full Name:** Eze Favour  
**Cloud Platform:** AWS — selected and approved by Eze Favour; operated by Codex under authorization
**GitHub Repository URL:** https://github.com/Favourcloud/devops-micro-internship-pravinmishra  
**Public Application URL / Load-Balancer DNS:** https://xdr0flp20e.execute-api.us-east-1.amazonaws.com

---

## Purpose

> **25 September deployment status:** The AWS capstone is deployed and its HTTPS API, browser login/review flow, primary/replica persistence and verified database TLS have passed. All 28 numbered image slots now contain original captures. [Deployment source and operation](terraform-book-review/releases/2026-09-25-aws/README.md) are separate from the preserved historical source. [Actual results and capture provenance](terraform-book-review/evidence/deployment-20260925/README.md) identify recorded evidence viewers, original app screenshots and test limitations. Claude Code used Bedrock and named-role main sessions, not delegated subagents. Reflection answers below are explicitly AI-assisted project explanations. Publication and the completed final review are linked below; no whole-week completion or new DMI grade is claimed.

Deploy the Book Review App using Terraform on AWS or Azure in a secure, highly available, production-style three-tier architecture. Use Claude Code, specialized subagents, Terraform MCP, and validation hooks to support the engineering workflow while keeping all infrastructure-changing operations under human control.

---

# Task 0 — Prepare the Project and Agentic AI Environment

## Goal

Prepare the Book Review App project and configure the provided Claude Code Agentic AI starter kit with project context, specialized subagents, Terraform MCP, validation hooks, and safety guardrails.

## Evidence

### Screenshot 1 — Project `CLAUDE.md`

Add a screenshot of the project `CLAUDE.md` showing the three-tier architecture, security boundaries, Terraform requirements, and human-approval rules.

<!-- A5 source capture 1 -->
![Screenshot 1: original local source view](terraform-book-review/evidence/screenshots/screenshot-01-project-context.png)

**Source-only evidence:** Actual CLAUDE.md showing three-tier architecture, security boundaries, Terraform requirements and human-approval rules. Visibly Copilot-authored inactive draft, not the provided kit or Claude execution. Captured source: `23748110108196f26c1394830a48af5317f7ca22`.
<!-- /A5 source capture -->

---

### Screenshot 2 — Terraform Engineer Subagent

Add a screenshot showing the Terraform Engineer subagent configuration.

<!-- A5 source capture 2 -->
![Screenshot 2: original local source view](terraform-book-review/evidence/screenshots/screenshot-02-terraform-engineer-agent.png)

**Source-only evidence:** Inactive Terraform Engineer agent source with inherited model selection and bounded tools. This is configuration text, not an executed agent or Claude-generated work. Captured source: `23748110108196f26c1394830a48af5317f7ca22`.
<!-- /A5 source capture -->

---

### Screenshot 3 — Architecture and Security Reviewer Subagent

Add a screenshot showing the Architecture and Security Reviewer subagent configuration.

<!-- A5 source capture 3 -->
![Screenshot 3: original local source view](terraform-book-review/evidence/screenshots/screenshot-03-architecture-reviewer-agent.png)

**Source-only evidence:** Inactive read-only Architecture/Security Reviewer definition. This shows the bounded reviewer configuration, not a performed Claude architecture or security review. Captured source: `23748110108196f26c1394830a48af5317f7ca22`.
<!-- /A5 source capture -->

---

### Screenshot 4 — Terraform MCP Connection

Add a screenshot showing Terraform MCP connected and available.

<!-- A5 workflow capture 4 -->
![Screenshot 4: genuine live terminal evidence](terraform-book-review/evidence/screenshots/screenshot-04-terraform-mcp.jpg)

**Verified scope:** Actual Claude Code /mcp view shows Terraform connected with seven tools. This is configuration evidence from a live local PTY; AWS credentials were disabled and no model call was made. Operator: Codex under user delegation; no manual learner execution claimed. [Capture provenance](terraform-book-review/evidence/workflow-capture-provenance-20260925.json).
<!-- /A5 workflow capture -->

---

### Screenshot 5 — Validation Hooks

Add a screenshot showing the configured Claude Code validation hooks.

<!-- A5 workflow capture 5 -->
![Screenshot 5: genuine live terminal evidence](terraform-book-review/evidence/screenshots/screenshot-05-validation-hooks.jpg)

**Verified scope:** Actual Claude Code hook details show PostToolUse for Edit|Write invoking the protected post_tool_validate.py command. This proves configuration, not an executed post-edit validation event. Operator: Codex under user delegation; no manual learner execution claimed. [Capture provenance](terraform-book-review/evidence/workflow-capture-provenance-20260925.json).
<!-- /A5 workflow capture -->

---

# Task 1 — Design the Three-Tier Architecture

## Goal

Design the required secure, highly available three-tier architecture and create an architecture diagram before building the infrastructure.

The diagram must show:

- VPC or VNet
- Availability Zones or equivalent availability locations
- Six subnets
- Internet connectivity
- NAT or outbound design
- Public load balancer
- Web Tier
- Internal load balancer
- Application Tier
- Managed MySQL
- Read replica
- Main traffic flow

## Architecture Diagram

The [completed source architecture diagram](terraform-book-review/README.md#architecture-created-before-infrastructure-source) was written before infrastructure source. It shows the two-AZ/six-subnet VPC, IGW and per-AZ NAT, public and internal load balancers, Web/App tiers, Multi-AZ MySQL and a separate read replica. It remains the original design artifact. The [release architecture](terraform-book-review/releases/2026-09-25-aws/README.md#architecture) adds the deployed API Gateway/VPC-link/NLB entry path; [live evidence](terraform-book-review/evidence/deployment-20260925/README.md) verifies the resources separately.

---

# Task 2 — Build the Terraform Networking and Security Layers

## Goal

Create the modular Terraform project and implement the network and security layers across the required public and private subnets.

## Evidence

### Screenshot 6 — Modular Terraform Project Structure

Add a screenshot showing the modular Terraform project structure.

<!-- A5 source capture 6 -->
![Screenshot 6: original local source view](terraform-book-review/evidence/screenshots/screenshot-06-modular-project-structure.png)

**Source-only evidence:** Genuine Explorer view showing all nine actual module directories. Twelve is the root module-call count, not the directory count; this is source structure, not deployed infrastructure. Captured source: `23748110108196f26c1394830a48af5317f7ca22`.

Original native window frame initially captured while framing network source. Accepted once for slot 6 after OCR confirmed all nine module folders. Pixels are unchanged; this frame is NOT counted as slot 7.
<!-- /A5 source capture -->

---

### Screenshot 7 — Six-Subnet Architecture

Add a screenshot showing the six-subnet architecture across two availability locations.

<!-- A5 source capture 7 -->
![Screenshot 7: original browser source view](terraform-book-review/evidence/screenshots/screenshot-07-local-evidence.png)

**Source-only evidence:** Two validated availability zones and three tiers produce six subnets. This source has not been deployed. Captured source: `23748110108196f26c1394830a48af5317f7ca22`. Operator: Codex under user delegation. This is an original screenshot of a locally prepared file viewer, not a cloud console or deployed-resource proof.
<!-- /A5 source capture -->

---

### Screenshot 8 — Public and Private Tier Separation

Add a screenshot showing the public and private tier separation, including routing and security boundaries.

<!-- A5 source capture 8 -->
![Screenshot 8: original browser source view](terraform-book-review/evidence/screenshots/screenshot-08-local-evidence.png)

**Source-only evidence:** Source routing: Web uses the internet gateway; App uses its same-AZ NAT; DB has local routes only. The security-group chain restricts traffic to the preceding tier. These are configuration views. Captured source: `23748110108196f26c1394830a48af5317f7ca22`. Operator: Codex under user delegation. This is an original screenshot of a locally prepared file viewer, not a cloud console or deployed-resource proof.
<!-- /A5 source capture -->

---

# Task 3 — Build the Load-Balancing and Compute Layers

## Goal

Deploy the public and internal load balancers and the Web and Application compute resources required by the Book Review App.

## Evidence

### Screenshot 9 — Web and Application Compute

Add a screenshot showing the Web and Application compute resources in their required subnets.

![Screenshot 9 — Eze Favour](terraform-book-review/evidence/deployment-20260925/screenshots/screenshot-09-recorded-final.png)

**Verified scope:** Original browser capture of labeled recorded AWS/API/CLI evidence; not the AWS Console or a live terminal. Operator: Codex under Eze Favour’s authorization. [Provenance](terraform-book-review/evidence/deployment-20260925/capture-provenance.json).

---

### Screenshot 10 — Public Load Balancer

Add a screenshot showing the internet-facing public load balancer.

![Screenshot 10 — Eze Favour](terraform-book-review/evidence/deployment-20260925/screenshots/screenshot-10-recorded-final.png)

**Verified scope:** Original browser capture of labeled recorded AWS/API/CLI evidence; not the AWS Console or a live terminal. Operator: Codex under Eze Favour’s authorization. [Provenance](terraform-book-review/evidence/deployment-20260925/capture-provenance.json).

---

### Screenshot 11 — Internal Load Balancer

Add a screenshot showing the private internal load balancer.

![Screenshot 11 — Eze Favour](terraform-book-review/evidence/deployment-20260925/screenshots/screenshot-11-recorded-final.png)

**Verified scope:** Original browser capture of labeled recorded AWS/API/CLI evidence; not the AWS Console or a live terminal. Operator: Codex under Eze Favour’s authorization. [Provenance](terraform-book-review/evidence/deployment-20260925/capture-provenance.json).

---

### Screenshot 12 — Healthy Targets

Add a screenshot showing healthy target groups or backend pools.

![Screenshot 12 — Eze Favour](terraform-book-review/evidence/deployment-20260925/screenshots/screenshot-12-recorded-final.png)

**Verified scope:** Original browser capture of labeled recorded AWS/API/CLI evidence; not the AWS Console or a live terminal. Operator: Codex under Eze Favour’s authorization. [Provenance](terraform-book-review/evidence/deployment-20260925/capture-provenance.json).

---

# Task 4 — Build the Managed MySQL Database Layer

## Goal

Deploy a private, highly available managed MySQL database with a read replica and restrict database connectivity to the Application Tier.

## Evidence

### Screenshot 13 — Managed MySQL Database

Add a screenshot showing the managed MySQL database deployment.

![Screenshot 13 — Eze Favour](terraform-book-review/evidence/deployment-20260925/screenshots/screenshot-13-recorded-final.png)

**Verified scope:** Original browser capture of labeled recorded AWS/API/CLI evidence; not the AWS Console or a live terminal. Operator: Codex under Eze Favour’s authorization. [Provenance](terraform-book-review/evidence/deployment-20260925/capture-provenance.json).

---

### Screenshot 14 — High Availability

Add a screenshot showing the Multi-AZ or high-availability configuration.

<!-- A5 source capture 14 -->
![Screenshot 14: original browser source view](terraform-book-review/evidence/screenshots/screenshot-14-local-evidence.png)

**Source-only evidence:** The primary database is configured with multi_az = true. This shows the configured intent, not a provisioned standby or failover test. Captured source: `23748110108196f26c1394830a48af5317f7ca22`. Operator: Codex under user delegation. This is an original screenshot of a locally prepared file viewer, not a cloud console or deployed-resource proof.
<!-- /A5 source capture -->

---

### Screenshot 15 — Read Replica

Add a screenshot showing the read replica configuration.

<!-- A5 source capture 15 -->
![Screenshot 15: original browser source view](terraform-book-review/evidence/screenshots/screenshot-15-local-evidence.png)

**Source-only evidence:** The separate replica points to the primary ARN. Its multi_az = false is distinct from the primary standby. No replication or live database connection is demonstrated. Captured source: `23748110108196f26c1394830a48af5317f7ca22`. Operator: Codex under user delegation. This is an original screenshot of a locally prepared file viewer, not a cloud console or deployed-resource proof.
<!-- /A5 source capture -->

---

### Screenshot 16 — Private Database Access

Add a screenshot showing that the database is private and accepts MySQL traffic only from the Application Tier.

<!-- A5 source capture 16 -->
![Screenshot 16: original browser source view](terraform-book-review/evidence/screenshots/screenshot-16-local-evidence.png)

**Source-only evidence:** The only database ingress edge uses the App security group on TCP 3306. Both database instances are private. Live connectivity remains unverified. Captured source: `23748110108196f26c1394830a48af5317f7ca22`. Operator: Codex under user delegation. This is an original screenshot of a locally prepared file viewer, not a cloud console or deployed-resource proof.
<!-- /A5 source capture -->

---

# Task 5 — Validate, Review, and Apply the Terraform Configuration

## Goal

Validate the Terraform configuration, review the execution plan using both Agentic AI and human judgment, and apply the infrastructure changes only after all required checks pass.

## Evidence

### Screenshot 17 — Terraform Validation

Add a screenshot showing successful `terraform validate` output.

<!-- A5 workflow capture 17 -->
![Screenshot 17: genuine live terminal evidence](terraform-book-review/evidence/screenshots/screenshot-17-terraform-validation.jpg)

**Verified scope:** Actual Terraform validate stdout reads “Success! The configuration is valid.” All six offline stages passed with IP networking denied, empty cloud credential files and the locked local provider. No real cloud plan or apply occurred. Operator: Codex under user delegation; no manual learner execution claimed. [Capture provenance](terraform-book-review/evidence/workflow-capture-provenance-20260925.json).
<!-- /A5 workflow capture -->

---

### Screenshot 18 — Terraform Plan

Add a screenshot showing the Terraform plan output.

![Screenshot 18 — Eze Favour](terraform-book-review/evidence/deployment-20260925/screenshots/screenshot-18-recorded-evidence.png)

**Verified scope:** Original browser capture of the reviewed initial deployment plan; historical plan evidence, not the final reconciliation. Operator: Codex under Eze Favour’s authorization. [Provenance](terraform-book-review/evidence/deployment-20260925/capture-provenance.json).

---

### Screenshot 19 — Terraform Apply

Add a screenshot showing successful `terraform apply` completion.

![Screenshot 19 — Eze Favour](terraform-book-review/evidence/deployment-20260925/screenshots/screenshot-19-recorded-final.png)

**Verified scope:** Original browser capture of labeled recorded AWS/API/CLI evidence; not the AWS Console or a live terminal; records the two initial deployment phases, with later corrective applies described in the release report. Operator: Codex under Eze Favour’s authorization. [Provenance](terraform-book-review/evidence/deployment-20260925/capture-provenance.json).

---

# Task 6 — Deploy and Configure the Book Review Application

## Goal

Deploy and configure the Book Review App across the Web, Application, and Database tiers and verify the complete application functionality.

## Evidence

### Screenshot 20 — Homepage

Add a screenshot showing the Book Review App homepage through the public endpoint.

![Screenshot 20 — Eze Favour](terraform-book-review/evidence/deployment-20260925/screenshots/screenshot-20-https-homepage-light-mode.png)

**Verified scope:** Original deployed-app browser capture. Operator: Codex under Eze Favour’s authorization. Light color mode was temporarily emulated for this test; no screenshot pixels or application source were altered. [Provenance](terraform-book-review/evidence/deployment-20260925/capture-provenance.json).

---

### Screenshot 21 — Login or Authentication

Add a screenshot showing successful login or authentication.

![Screenshot 21 — Eze Favour](terraform-book-review/evidence/deployment-20260925/screenshots/screenshot-21-authenticated-light-mode.png)

**Verified scope:** Original deployed-app browser capture. Operator: Codex under Eze Favour’s authorization. Light color mode was temporarily emulated for this test; no screenshot pixels or application source were altered. [Provenance](terraform-book-review/evidence/deployment-20260925/capture-provenance.json).

---

### Screenshot 22 — Book Data

Add a screenshot showing the book listing or book details.

![Screenshot 22 — Eze Favour](terraform-book-review/evidence/deployment-20260925/screenshots/screenshot-22-book-details.png)

**Verified scope:** Original deployed-app browser capture. Operator: Codex under Eze Favour’s authorization. [Provenance](terraform-book-review/evidence/deployment-20260925/capture-provenance.json).

---

### Screenshot 23 — Review Functionality

Add a screenshot showing the review functionality working successfully.

![Screenshot 23 — Eze Favour](terraform-book-review/evidence/deployment-20260925/screenshots/screenshot-23-review-after-reload.png)

**Verified scope:** Original deployed-app browser capture. Operator: Codex under Eze Favour’s authorization. [Provenance](terraform-book-review/evidence/deployment-20260925/capture-provenance.json).

---

### Screenshot 24 — Backend or API Evidence

Add a screenshot showing that the backend or API is working successfully.

![Screenshot 24 — Eze Favour](terraform-book-review/evidence/deployment-20260925/screenshots/screenshot-24-recorded-final.png)

**Verified scope:** Original browser capture of labeled recorded AWS/API/CLI evidence; not the AWS Console or a live terminal. Operator: Codex under Eze Favour’s authorization. [Provenance](terraform-book-review/evidence/deployment-20260925/capture-provenance.json).

---

### Screenshot 25 — Database Reads and Writes

Add a screenshot showing successful database reads and writes.

![Screenshot 25 — Eze Favour](terraform-book-review/evidence/deployment-20260925/screenshots/screenshot-25-recorded-final.png)

**Verified scope:** Original browser capture of labeled recorded AWS/API/CLI evidence; not the AWS Console or a live terminal. Operator: Codex under Eze Favour’s authorization. [Provenance](terraform-book-review/evidence/deployment-20260925/capture-provenance.json).

## Public Application URL

**Public Application URL / DNS:** Add the working public application URL or load-balancer DNS here

---

# Task 7 — Demonstrate the Agentic AI Workflow

## Goal

Demonstrate how Claude Code assisted with Terraform generation, architecture and security review, and evidence-based troubleshooting while infrastructure-changing decisions remained under human control.

You do not need to submit your complete Claude Code conversation history. Include only focused evidence.

## Evidence

### Screenshot 26 — AI-Assisted Terraform Generation

Add a screenshot showing one useful example of AI-assisted Terraform generation or improvement.

<!-- A5 AI capture 26 -->
Recorded actual Claude Code Read/Edit output improved Terraform hostname limits. PostToolUse passed; 13 independent Terraform boundary tests passed. The session hit its budget limit before a final summary. This is a saved-output view, not a live terminal or deployment.

![Recorded actual AI workflow for slot 26](terraform-book-review/evidence/screenshots/screenshot-26-ai-terraform.jpg)

[Capture provenance](terraform-book-review/evidence/ai-capture-provenance-20260925.json) · [Findings and corrections](terraform-book-review/evidence/ai-workflow-20260925.md)
<!-- /A5 AI capture -->

---

### Screenshot 27 — Architecture or Security Review

Add a screenshot showing one structured architecture or security review result.

<!-- A5 AI capture 27 -->
Selected exact PASS/WARN/FAIL findings from the recorded Bedrock reviewer response, with operator follow-up. The 1,024-token response was truncated and then stopped at its CLI budget; it is a partial source review, not final architecture approval.

![Recorded actual AI workflow for slot 27](terraform-book-review/evidence/screenshots/screenshot-27-ai-review.jpg)

[Capture provenance](terraform-book-review/evidence/ai-capture-provenance-20260925.json) · [Findings and corrections](terraform-book-review/evidence/ai-workflow-20260925.md)
<!-- /A5 AI capture -->

---

### Screenshot 28 — AI-Assisted Troubleshooting

Add a screenshot showing one AI-assisted troubleshooting interaction based on collected evidence.

<!-- A5 AI capture 28 -->
Recorded Claude diagnosis of the verified archive failure and explicit operator correction. The first attempt made no edit; the second model patch failed raw-path tests and rejected the root directory. The corrected candidate passed 12 existing and seven new archive checks. Saved-output view; no deployment.

![Recorded actual AI workflow for slot 28](terraform-book-review/evidence/screenshots/screenshot-28-ai-troubleshooting.jpg)

[Capture provenance](terraform-book-review/evidence/ai-capture-provenance-20260925.json) · [Findings and corrections](terraform-book-review/evidence/ai-workflow-20260925.md)
<!-- /A5 AI capture -->

---

# Task 8 — Complete the Final Architecture Review

## Goal

Review the completed infrastructure against the original capstone requirements and resolve significant architecture, security, reliability, and cost issues.

Confirm that the final review covers:

- Tier separation
- Availability
- Public exposure
- Routing
- Security rules
- Load balancing
- Database privacy
- Secrets
- Terraform quality
- Module structure
- Reliability
- Obvious cost risks

Use Screenshot 27 as the focused evidence for the structured architecture or security review.

---

**Completed final review:** [Original Bedrock response](terraform-book-review/evidence/deployment-20260925/bedrock-final-architecture-review.result.json), [independent corrections](terraform-book-review/evidence/deployment-20260925/final-review-followup.md), and [original supplemental screenshot](terraform-book-review/evidence/deployment-20260925/screenshots/final-architecture-review.png). The named reviewer main session completed with PASS/WARN and no FAIL findings. Its opinion is not a guarantee or a full-rubric completion claim.

# Task 9 — Answer the Reflection Questions

## Goal

Reflect on the architecture, Terraform implementation, and Agentic AI workflow. Answer each question briefly in your own words.

**AI-assisted reflection disclosure:** Eze Favour authorized these explanations to be drafted from verified work. Codex operated the cloud/browser tests; Claude Code supplied the recorded Bedrock reviews and changes. These answers explain project decisions and results, without claiming personal manual execution. Learner review is still needed before treating the wording as firsthand understanding.


## Architecture

### 1. Why did you separate the Web, Application, and Database tiers?

Separating Web, Application and Database tiers gives each layer a clear responsibility and a smaller set of permitted connections. A request must pass through the intended load balancers and security groups instead of reaching the database directly.

### 2. Why is the Application Tier private?

The backend handles authentication and database operations. Keeping it in private subnets prevents direct Internet access; only the internal load balancer can reach its application port.

### 3. Why is MySQL private?

MySQL stores user and review data. Both RDS instances are private, encrypted, and reachable on TCP 3306 only through the Application security group. Database connections require TLS, including verification of the RDS hostname.

### 4. Why are multiple Availability Zones used?

Web and App capacity is distributed across two AZs, with a NAT gateway per AZ and a Multi-AZ database. This reduces dependence on one location. AWS confirmed the controlled Multi-AZ failover and the API recovered with saved reviews intact. The unchanged AZ label and transient 503 are recorded limitations; a diagram alone cannot prove availability.

### 5. What is the difference between Multi-AZ/high availability and a read replica?

The primary's standby supports managed failover. The separate asynchronous read replica supports read-only reporting and can lag. The original app still uses the primary; a separate proof path checks the replica.

## Terraform

### 6. How did you divide your Terraform into modules?

Networking, security, load balancing, compute, database, identities, secrets, observability and initialization have separate modules. The release adds a gateway module for an AWS-provided HTTPS address. Reusing compute and identity modules keeps the two tiers consistent.

### 7. How do the modules communicate through variables and outputs?

Modules accept inputs and return explicit outputs. For example, network subnet IDs feed compute and database modules, security-group IDs feed load balancers and instances, and the database endpoints feed runtime configuration. Secret values use ephemeral and write-only Terraform inputs.

### 8. What did you specifically check in `terraform plan`?

The real plan review is recorded separately with the exact resource changes. The checks cover region, AZs, subnet placement, exposure, storage encryption, instance sizes, secret handling, deletion protection and recurring cost. A successful mock plan is only an earlier source-validation step.

## Agentic AI

### 9. What was the purpose of `CLAUDE.md`?

It gives Claude the project architecture, boundaries, Terraform conventions and approval rules. It helps keep suggestions aligned with the assignment, but it does not replace independent review or enforce security by itself.

### 10. What work did the Terraform Engineer subagent perform?

Claude Code used the named engineer configuration to improve hostname validation. The recorded edit triggered the post-tool hook and passed independent boundary tests. These were named-role main sessions, not delegated subagent execution; that distinction is retained in the evidence.

### 11. What did the Architecture and Security Reviewer identify?

The reviewer raised private-link ingress, trusted HTTPS metadata, direct-ALB bypass, health-check behavior and cost/cleanup concerns. Its throttling concern was checked against the configuration: the HTTP API stage already limited traffic to 50 requests per second with burst 100.

### 12. Why did you use Terraform MCP instead of relying only on Claude's existing Terraform knowledge?

The connected Terraform MCP server provided a model-selected provider lookup. This gave the workflow access to provider documentation instead of relying entirely on model memory. The resulting configuration was still checked against the pinned provider and tested.

### 13. What was the purpose of your validation hooks?

The hooks run protected checks after source edits and block unsafe tool requests. The validator checks formatting, initialization, validation, provider schema and mock plans without cloud networking. Hook success does not prove a deployment or a working application.

### 14. Describe one real issue Claude helped you troubleshoot.

Claude helped diagnose rejection of an upstream source archive. Its proposed patch still failed path tests and rejected the root directory, so the operator corrected it. The candidate then passed the existing and new archive checks.

### 15. Describe one recommendation you reviewed, modified, or rejected instead of accepting blindly.

The suggested switch to liveness-only health checks was not accepted automatically. Database-backed readiness is intentional because the application must serve useful requests, not merely keep a process running. The actual forced-failover test recovered automatically with saved reviews intact; readiness was retained. This was a bounded recovery test, not a full availability guarantee.

---

# Task 10 — Publish the Mandatory LinkedIn Post

## Goal

Publish a LinkedIn post describing the capstone, the technical work completed, the Agentic AI workflow, and the lessons learned.

Write the post in your own words, include at least one project image or other proof, and ensure that it can be viewed by the submission reviewer.

## LinkedIn Post URL

**LinkedIn Post URL:** https://www.linkedin.com/posts/eze-favour-52732752_dmibypravinmishra-devops-terraform-ugcPost-7509164778045595649-LVlQ/

---

# Submission Instructions

- Complete Tasks 0–10 in sequence.
- Include all Screenshots 1–28 exactly as specified.
- Ensure that your full name is visible in the required screenshots.
- Include the selected cloud platform.
- Include the completed architecture diagram.
- Include the modular Terraform project structure.
- Include the working public application URL or public load-balancer DNS.
- Include all required Agentic AI workflow evidence.
- Answer all 15 reflection questions briefly in your own words.
- Include the published LinkedIn post URL.
- Do not expose cloud credentials, database passwords, SSH private keys, JWT secrets, access tokens, account IDs, Terraform state containing sensitive values, or other confidential information.
- Review all screenshots and project files carefully before submitting through GitHub.

---

# Completion Checklist

- [x] Selected AWS or Azure
- [x] Added and reviewed the Agentic AI starter files
- [x] Configured `CLAUDE.md`
- [x] Configured the Terraform Engineer subagent
- [x] Configured the Architecture and Security Reviewer subagent
- [x] Connected Terraform MCP
- [x] Configured validation hooks and safety guardrails
- [x] Created the architecture diagram
- [x] Created the six-subnet design
- [x] Configured public Web Tier routing
- [x] Kept the Application Tier private
- [x] Kept the Database Tier private
- [x] Configured tier-specific Security Groups or NSGs
- [x] Restricted backend port `3001`
- [x] Restricted MySQL port `3306` to the Application Tier
- [x] Created the public load balancer
- [x] Created the internal load balancer
- [x] Configured listeners and health checks
- [x] Deployed the Web Tier compute resources
- [x] Deployed the private Application Tier compute resources
- [x] Provisioned private managed MySQL
- [x] Configured Multi-AZ or high availability
- [x] Configured a read replica
- [x] Created the modular Terraform project
- [x] Used variables, outputs, and module dependencies
- [x] Used current Terraform documentation through MCP
- [x] Used hooks for deterministic validation
- [x] Completed `terraform fmt`
- [x] Completed `terraform validate`
- [x] Reviewed `terraform plan`
- [x] Completed the Terraform Engineer review
- [x] Completed the Architecture and Security review
- [x] Applied the infrastructure only after human approval
- [x] Deployed and configured the backend
- [x] Deployed and configured the frontend
- [x] Configured Nginx where required
- [x] Configured the internal backend endpoint
- [x] Configured the public frontend endpoint
- [x] Verified the homepage
- [x] Verified login or authentication
- [x] Verified book data
- [x] Verified review functionality
- [x] Verified the backend API
- [x] Verified database reads and writes
- [x] Verified healthy load-balancer targets
- [x] Included AI-assisted Terraform generation evidence
- [x] Included one architecture or security review
- [x] Included one AI-assisted troubleshooting example
- [x] Completed the final architecture review
- [x] Answered all 15 reflection questions
- [x] Published the mandatory LinkedIn post
- [x] Added the LinkedIn post URL
- [x] Captured all 28 required screenshots
- [ ] Confirmed that my full name is visible in the required screenshots
- [x] Checked that no secrets or sensitive information are exposed

---

## About DMI & CloudAdvisory

DevOps Micro Internship (DMI) is a project-based DevOps program run by Pravin Mishra (The CloudAdvisory), focused on real-world execution, systems thinking, and career readiness.

It helps learners build strong DevOps foundations through hands-on experience.

---

## Resources

- Book Review App Repository: [https://github.com/pravinmishraaws/book-review-app](https://github.com/pravinmishraaws/book-review-app)
- DMI Official Website: [https://dmi.pravinmishra.com](https://dmi.pravinmishra.com)
- University: [https://university.pravinmishra.com](https://university.pravinmishra.com)
- Discord Community: [https://discord.pravinmishra.com](https://discord.pravinmishra.com)
- Blog: [https://dmi.pravinmishra.com/blog](https://dmi.pravinmishra.com/blog)
- YouTube Playlist: [https://www.youtube.com/playlist?list=PLFeSNDtI4Cho](https://www.youtube.com/playlist?list=PLFeSNDtI4Cho)
- Pravin Mishra on LinkedIn: [https://www.linkedin.com/in/pravin-mishra-aws-trainer/](https://www.linkedin.com/in/pravin-mishra-aws-trainer/)
- CloudAdvisory on LinkedIn: [https://www.linkedin.com/company/thecloudadvisory/](https://www.linkedin.com/company/thecloudadvisory/)

---

*This submission is part of the DevOps Micro Internship (DMI) Cohort 3 — Agentic AI Track.*
