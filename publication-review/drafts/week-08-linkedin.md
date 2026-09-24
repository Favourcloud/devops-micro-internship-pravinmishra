Week 08 Terraform progress: three cloud exercises now have verified deployments, application or VM checks, and complete cleanup.

• Azure VM: 11/11 screenshots; eight resources created and destroyed, with VM-running, image, disk and IP verification.
• AWS VM: 10/10 screenshots; EC2, SSH, Nginx, public HTTP and browser checks passed before teardown.
• React on Azure: 15/15 screenshots; application, assets and routing checked, followed by verified teardown.

Codex performed these approved runs under delegation. The recorded public addresses are retired, and the evidence is merged into the repository.

Assignment 6 adds a different lesson: a valid Terraform plan can still describe an unsafe change. A planning-only input proposed public SSH, the checker returned FAIL, and Claude Code recommended rejecting it. A native PreToolUse hook blocked an actual apply request before Terraform ran. AWS read-back confirmed the public SSH rule was never deployed.

The recorded human decision retained the closed configuration. Copilot performed the final checks and cleanup. Its Terraform execution was delegated; the separate manual learner execution requirement remains open.

The repository includes the detected-change report and final recorded Claude review. Across Week 08, 78/118 screenshot slots are filled. A4's live AWS/RDS run, A5's starter kit and release/deployment work, and personal reflections still need completion. This is a progress update, not a whole-week completion claim.

The takeaway: connect each claim to its evidence—plan, review, decision, runtime result and cleanup.

Thank you to Pravin Mishra, Anjana Muthunayake, Tanisha Borana and Anuradha Iyer for the cohort's guidance.

P.S. This post is part of the DevOps Micro Internship (DMI) with Agentic AI — Cohort 3 — by Pravin Mishra. My graded progress is public: https://dmi.pravinmishra.com/s/Favourcloud.html · Start your DevOps journey: https://dmi.pravinmishra.com/?utm_source=student&utm_medium=ps-linkedin&utm_campaign=cohort3

#DMIByPravinMishra #DevOps #AgenticAI #Terraform #ClaudeCode
