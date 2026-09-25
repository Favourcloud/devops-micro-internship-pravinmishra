# From Terraform Plans to a Working AWS Book Review App

**Eze Favour · DMI Week 08 · 25 September 2026**

A successful Terraform apply is only one part of delivering an application. My Week 08 project now includes a Book Review app on AWS, real login and review tests, private database verification, and a controlled recovery test. The evidence also records where the work falls short of the original rubric.

This was an assisted workflow. Codex performed the authorized cloud operations and browser tests. Claude Code used Amazon Bedrock for Terraform improvements, troubleshooting and reviews. The reflections here were drafted with assistance from the recorded results; they do not claim that I manually executed every command. Claude's named engineer and reviewer configurations ran as main sessions, not delegated subagents.

## The architecture behind the working page

The capstone has six subnets across two Availability Zones, two Web instances, two private Application instances, an internal load balancer and a private, encrypted RDS MySQL database. A managed Multi-AZ standby supports availability; a separate read replica provides a read-only copy. The application uses the primary database. The replica was checked independently, so this is not a claim of application read splitting.

I approved AWS and an AWS-provided HTTPS address. The deployed entry path uses API Gateway, a private VPC link, an internal Network Load Balancer and the assignment's internet-facing Application Load Balancer. Security groups restrict each step to its intended predecessor. The public ALB is not open to arbitrary Internet traffic. Database connections verify the certificate authority and hostname. HTTP between application tiers stays inside the VPC; it is not encrypted on every internal hop.

[Open the Book Review demo](https://xdr0flp20e.execute-api.us-east-1.amazonaws.com).

## The checks that made deployment evidence useful

API tests verified the HTTPS homepage, three seeded books, new account registration, login, review creation and an independent read of the saved review. Negative checks rejected anonymous review creation, invalid login and an upstream book-write route that should not be exposed.

The browser test then logged in, opened a book, submitted another review and reloaded the page. The review remained visible. Independent database checks found the API review on both primary and replica, confirmed the replica was read-only, and negotiated TLS 1.3. Separate wrong-CA and wrong-hostname tests failed as expected.

A controlled RDS reboot with forced failover produced AWS events confirming Multi-AZ failover completion. The API briefly returned 503, then recovered automatically with both test reviews intact. The reported Availability Zone label stayed the same before and after, so the records explicitly avoid claiming an independently observed AZ switch. This was one recovery exercise, not a complete regional resilience or load test.

## Problems that required evidence, not guesses

Several real issues appeared after deployment. Ubuntu's systemd credential files used a protected 0440 mode, while the original guard expected 0600 everywhere. The correction accepts 0440 only in the exact protected systemd credential location; ordinary config files still require 0600. MySQL Router also needed narrowly scoped AppArmor rules for its runtime configuration and RDS CA file. AppArmor remained enforced.

The gateway connection initially failed, leading to the internal NLB entry. A later HTTP 400 had a different cause: API Gateway supplied a zero Content-Length on GET, which strict load-balancer desync handling rejected. The public ALB now uses AWS's defensive mode for this integration. Nginx removes request bodies and Content-Length from permitted read-only routes, while the internal ALB retains strictest handling. These fixes were applied through reviewed Terraform changes and verified after rolling replacement.

The release passed 100 Python tests and 45 Terraform mock tests. Those are useful source checks; the live API, browser and database results establish different facts. Original screenshots and sanitized records are kept with hashes. Some infrastructure screenshots show clearly labeled recorded API/CLI evidence viewers, rather than the AWS Console or a live terminal.

## What the other Week 08 assignments show

The Azure VM, AWS VM and Azure React exercises have verified deployment and teardown records. The EpicBook AWS exercise also has a browser cart action correlated with its RDS record and verified removal of all 29 lab resources. Its instructor application has no order-creation endpoint, so a working cart cannot honestly be described as completed checkout.

The policy-review exercise planned a deliberately unsafe public SSH rule. The checker returned FAIL, Claude recommended rejection, and a native hook blocked the apply attempt. AWS read-back showed that the risky rule was never deployed. Final checks and cleanup were recorded. The rubric's separate manual learner execution requirement remains open.

## The lesson and the next boundary

The most useful lesson from these records is to connect every claim to a specific observation: source validation, reviewed plan, applied infrastructure, application behavior and cleanup are separate steps. AI suggestions also need tests. One earlier archive-handling proposal failed boundary checks and needed an operator correction before it was accepted.

I asked to keep the capstone online until I request cleanup. Its core resources are estimated at about $0.59 per hour, before storage, public IPv4, traffic, requests and taxes. Temporary builder and initializer resources have already been removed. The teardown plan covers the remaining stack, artifacts, image snapshots, secrets and retained backups. This is a learning deployment, not a claim of production readiness or full rubric completion.

[Browse the repository and evidence](https://github.com/Favourcloud/devops-micro-internship-pravinmishra).

This work is part of the [DevOps Micro Internship with Agentic AI — Cohort 3](https://dmi.pravinmishra.com/), led by Pravin Mishra and The CloudAdvisory. Thank you to the cohort mentors for their guidance.

[Follow my graded DMI progress](https://dmi.pravinmishra.com/s/Favourcloud.html).
