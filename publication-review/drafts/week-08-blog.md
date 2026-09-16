# A Terraform Review That Stopped Before Public SSH Reached AWS

**Week 08 — Terraform | Eze Favour**

My Week 08 Assignment 6 focused on a small but important question: can an AI-assisted review explain a proposed infrastructure change while a separate control prevents that AI workflow from applying it?

The evidence now includes a real clean baseline, a deliberately risky proposal, actual Claude reviews, a native hook denial, a human resolution decision and verified cleanup. It also includes a limitation worth keeping visible: GitHub Copilot performed the authorized Terraform operations. I did not manually execute Terraform, so the assignment's separate manual-execution requirement remains unmet.

## Keep the experiment small enough to understand

The isolated AWS lab contained one dedicated VPC and one closed, unattached security group. It did not contain application instances, a NAT gateway or a database. Earlier coursework resources were outside the approved scope.

Baseline Terraform plans reported no changes. A Bash/jq checker evaluated the supported ingress and destructive-action evidence and produced a LIVE HEALTHY result. That label described the checks at that point in time. It did not establish global security or authorize a subsequent apply.

## A proposed configuration change is not drift

The risky input was supplied only to planning processes. It proposed a public SSH rule without deploying that rule. The real plan showed one security-group update, and the checker returned FAIL with one unsafe ingress finding. Refresh drift remained zero. Independent AWS read-back still showed zero deployed ingress rules.

This distinction matters. Out-of-band drift means actual infrastructure has diverged from the configuration or recorded state because something changed outside the intended workflow. Here, the configuration proposal itself was risky. Calling it drift would misdescribe what the evidence showed.

## Review and enforcement are different jobs

Claude Code performed genuine clean, risk and final /tf-drift-review invocations using the sanitized context and reports. The risk review recommended: “Do not apply this configuration.” The operator independently checked the exact private plan, rather than treating an AI explanation as a replacement for it.

A separate native PreToolUse test used the fresh FAIL report. It denied an actual apply request before Terraform executed. That event is stronger evidence than merely showing a hook configuration file or running a local simulation: the gate intercepted a real tool request in the review workflow.

The historical synthetic fixtures remain labeled as fixtures. Earlier unsuccessful model attempts remain dated records. Neither was substituted for the successful live cycle.

## Record the human decision accurately

When the first focused question received an unavailable response, no approval was inferred. My later explicit approval chose to reject public SSH and retain the closed configuration.

Copilot then performed the separately authorized checks. Both final plans reported no changes, the checker returned limited-scope HEALTHY with zero findings, and the final Claude review cited the fresh evidence. There was no deployed SSH rule to revoke and no persistent override file to remove.

I owned that resolution decision. Copilot operated Terraform. Keeping those statements separate avoids presenting autonomous execution as a manual action by me.

## Cleanup needs its own evidence

After the final review, separately reviewed deletion plans removed the new security group and then the VPC. Independent checks found empty Terraform states, no lab-tagged resources and absence of both exact resources. The final state of this experiment is a deleted lab, not a still-running HEALTHY environment.

All 19 numbered screenshots are recorded with provenance. Some show recorded native review output in the editor; they are not presented as fresh chat replays. Those evidence labels matter as much as readable images.

My takeaway is to bind every claim to the appropriate record: the plan describes intent, the checker evaluates a defined policy, Claude explains the evidence, the human owns the decision, and independent verification checks the result. None of those steps should silently stand in for another.

## Evidence behind this reflection

- [The current assignment and its remaining rubric limits](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/blob/b9f903148c273aee9dab83aa2080580df6b70373/week-08-terraform/assignment-06-ai-assisted-terraform-drift-and-policy-review.md)
- [The seven-part review summary](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/blob/b9f903148c273aee9dab83aa2080580df6b70373/week-08-terraform/drift-review/drift-review-summary.md)

This work is part of the [DevOps Micro Internship with Agentic AI — Cohort 3](https://dmi.pravinmishra.com/), led by [Pravin Mishra](https://www.linkedin.com/in/pravin-mishra-aws-trainer/). Thank you to the cohort mentors for the learning framework.

[Follow my graded progress](https://dmi.pravinmishra.com/s/Favourcloud.html).
