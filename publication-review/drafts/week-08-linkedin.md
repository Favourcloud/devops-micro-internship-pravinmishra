My DMI Week 08 Terraform capstone now has a working AWS Book Review app with verified HTTPS login, book data and persistent reviews.

The deployment spans two Availability Zones and six subnets: Web and private App tiers, load balancers, private encrypted Multi-AZ MySQL, and a separate read replica. An AWS-provided HTTPS entry point reaches the application through a restricted VPC path.

What the evidence shows:
• API registration/login/review tests passed; anonymous reviews and unsafe book writes were rejected.
• A browser-submitted review survived reload. Independent database checks verified the API review on primary and replica, TLS 1.3 and rejection of incorrect CA/hostname values.
• AWS confirmed a controlled Multi-AZ failover. The API briefly returned 503, then recovered with both reviews intact. The AZ label did not change, so the report preserves that limitation.
• 100 Python tests and 45 Terraform mock tests passed, alongside the separate live checks.

The attached proof also covers EpicBook's browser cart matching its RDS record and the policy-review exercise: a proposed public SSH rule failed policy checks, Claude recommended rejecting it, and a native hook blocked apply. The risky rule never reached AWS. Final review and cleanup were recorded.

Codex performed the approved capstone/cloud/browser operations; Claude Code used Amazon Bedrock for improvements, troubleshooting and named-role reviews. Earlier policy-lab Terraform execution was delegated to Copilot. These are assisted results, not a claim of manual learner execution.

The practical lesson: a successful apply is not the finish line. Test the real request path, verify persistence and recovery, review AI suggestions, and plan cleanup.

Limits remain visible: EpicBook's instructor app has no order-creation endpoint; A6's manual-execution requirement remains open. The capstone stays online at my request until cleanup, with ongoing AWS charges. This is not a whole-week completion claim.

Article: https://medium.com/@rosenaefavour/from-terraform-plans-to-a-working-aws-book-review-app-27a81b45dedb
Demo: https://xdr0flp20e.execute-api.us-east-1.amazonaws.com
Evidence: https://github.com/Favourcloud/devops-micro-internship-pravinmishra

Thank you to Pravin Mishra and the cohort mentors.

P.S. This post is part of the DevOps Micro Internship (DMI) with Agentic AI — Cohort 3 by Pravin Mishra. My graded progress: https://dmi.pravinmishra.com/s/Favourcloud.html
Start your DevOps journey: https://dmi.pravinmishra.com/?utm_source=student&utm_medium=ps-linkedin&utm_campaign=cohort3

#DMIByPravinMishra #DevOps #Terraform #AWS #ClaudeCode #AgenticAI
