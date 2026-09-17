A Terraform plan can be accurate and still describe a change that should not be applied.

For Week 08 Assignment 6 of DMI, I built a bounded Terraform review workflow with GitHub Copilot assistance: real plan evidence, a Bash/jq policy checker, a Claude Code /tf-drift-review Skill, and a PreToolUse safety gate.

The isolated lab contained one dedicated VPC and a closed, unattached security group. Copilot performed the separately authorized Terraform operations.

An input supplied only to planning proposed public SSH. The checker returned FAIL with one proposed update and one unsafe ingress finding. AWS read-back still showed zero deployed ingress rules. This was an unapplied configuration change, not out-of-band drift.

The genuine Claude review recommended: “Do not apply this configuration.” A separate native hook test with the fresh FAIL report blocked an actual apply request before Terraform ran.

After reviewing the proposal, I approved rejecting public SSH and keeping the group closed. Copilot ran the final checks: no-change plans, a limited-scope HEALTHY report, and a genuine final Claude review. Authorized cleanup then removed only the new lab, with empty-state and resource-absence checks.

The lesson: keep evidence, recommendations, decisions and execution distinct. A HEALTHY report is not permission to change infrastructure. I owned the resolution decision; I did not manually execute Terraform, so that separate rubric requirement remains open.

The two attached captures show the detected report and the final recorded Claude review before cleanup. All 19 numbered assignment images are recorded with provenance; this post describes Assignment 6 progress, not completion of the whole Terraform week.

Thank you to Pravin Mishra, Anjana Muthunayake, Tanisha Borana and Anuradha Iyer for the cohort's guidance.

P.S. This post is part of the DevOps Micro Internship (DMI) with Agentic AI — Cohort 3 — by Pravin Mishra. My graded progress is public: https://dmi.pravinmishra.com/s/Favourcloud.html · Start your DevOps journey: https://dmi.pravinmishra.com/?utm_source=student&utm_medium=ps-linkedin&utm_campaign=cohort3

#DMIByPravinMishra #DevOps #AgenticAI #Terraform #ClaudeCode
