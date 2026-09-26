# Azure Architecture and the Evidence Needed to Prove It: Week 07

Eze Favour · DMI Week 07 · 26 September 2026

My Week 07 reflection focuses on Azure architecture, security boundaries and the evidence needed to support a deployment claim. It was prepared with Codex assistance from the course assignments and a fresh review of my repository. The current Week 07 deployment evidence is incomplete; this is an architecture and verification reflection.

## Follow the request through three tiers

The Azure Book Review assignment separates presentation, application logic and data. A public entry service receives the user's request. The web tier forwards the appropriate request to an internal application endpoint, and the application connects to a private managed database.

That design gives each boundary a purpose. The database does not need direct internet access to serve the application. The backend does not need to expose its management interface publicly to receive traffic from the web tier. Network rules should permit the required source, destination and port for each connection, with administration handled through a controlled path.

A diagram is the beginning of this reasoning. Verification must follow the same path: confirm the public response, confirm the internal health check, exercise a database write, and check that the record survives the expected application lifecycle. A successful page load by itself says little about persistent writes or recovery.

## Similar cloud goals, different controls

AWS and Azure share the goals of network isolation, controlled access and encryption, but their resource models differ. In Azure, a Resource Group organizes the assignment's resources, a VNet and subnets define network placement, and Network Security Groups govern permitted traffic. Managed identities and role assignments help scope access to Azure services. Secrets belong in an approved protected store rather than a repository or screenshot.

Names should not substitute for checks. A resource described as private needs evidence of its effective configuration and reachable path. A storage account needs its public-access policy inspected. A database needs its network setting checked alongside the application's connection behavior. The verification question is always about the resulting access, not merely whether a setting exists somewhere in the portal.

## Design a read-only security review

The Week 07 audit assignment asks for four checks: broadly open administrative ports in NSGs, public blob access, VM disk encryption status, and public network access on Azure Database for MySQL. A useful report records the observed values, the affected resource and a clear PASS, WARN or FAIL explanation.

The workflow separates evidence collection from remediation. A read-only script collects facts; an AI assistant explains their significance; an operator reviews a proposed change; a new report checks the outcome. The saved baseline matters because a clean final report alone cannot establish which issue was found or what changed.

Access failures must also be explicit. If an account cannot read a resource, the report should identify an unknown or failed check. Treating missing data as a healthy result would create false confidence. Similarly, an AI explanation cannot be presented as a live finding unless the underlying report supports it.

## Review the evidence itself

The repository review on 26 September found 60 Week 07 screenshot references. Thirty-eight referenced files were absent. The 22 files that existed were all 1-by-1-pixel images, which provide no readable deployment proof. The earlier count of present files was only an inventory count and did not establish screenshot quality.

This discovery changes what can responsibly be said about the work. The course dashboard has credited the assignment files, but that score cannot certify the missing native views, a live Azure capstone or a completed personal remediation. The repository now records this distinction explicitly. The placeholder image files are not being presented as genuine screenshots in this article.

The next evidence pass needs original configuration views, real command results, application behavior and before-and-after audit records. It should capture the relevant view while keeping credentials and private identifiers out of the published material. Existing deployments from other weeks retain their own dates and provenance.

## A practical standard for the next iteration

For every claim, keep a corresponding source: a configuration export for architecture, a probe for reachability, a database check for persistence and a saved comparison for remediation. This makes the report useful to another engineer and exposes gaps early enough to fix them.

That is the Azure lesson this reflection documents: infrastructure design, security reasoning and evidence quality belong in the same workflow. The remaining Week 07 technical and screenshot requirements stay visible until supported by authentic results.

[Review the Week 07 assignments and evidence status](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/tree/main/week-07-azure-cloud).

This work is part of Pravin Mishra's [DevOps Micro Internship with Agentic AI](https://dmi.pravinmishra.com/), Cohort 3. [Follow my graded DMI progress](https://dmi.pravinmishra.com/s/Favourcloud.html).
