DMI Week 07 — Azure architecture and the evidence needed to prove it.

My reflection covers three connected questions:
• How should a request move from a public entry point through web, application and private database tiers?
• Which Azure checks establish network exposure, storage access and encryption settings?
• What evidence supports a claim that a security finding was fixed?

The workflow I am documenting is: collect read-only facts → explain the finding → review a scoped change → verify it with a fresh report. Missing access or missing report data must remain unknown, not become a PASS.

This review also caught an evidence gap: Week 07's 22 existing image files were 1-pixel placeholders, and 38 referenced images were absent. The repository now states that clearly. The article is an architecture and verification reflection; it does not claim a completed live Azure capstone or personal manual remediation.

Codex assisted with the source review and writing. The practical takeaway is to keep a source for each claim: configuration for architecture, probes for reachability, database checks for persistence, and before/after records for remediation.

Article: https://favourcloud.github.io/devops-micro-internship-pravinmishra/blog/week-07.html
Evidence status: https://github.com/Favourcloud/devops-micro-internship-pravinmishra/tree/main/week-07-azure-cloud

Thank you to Pravin Mishra, Anjana Muthunayake, Tanisha Borana and Anuradha Iyer for the programme and mentorship.

P.S. This post is part of the DevOps Micro Internship (DMI) with Agentic AI — Cohort 3 — by Pravin Mishra. My graded progress is public: https://dmi.pravinmishra.com/s/Favourcloud.html · Start your DevOps journey: https://dmi.pravinmishra.com/?utm_source=student&utm_medium=ps-linkedin&utm_campaign=cohort3

#DMIByPravinMishra #DevOps #AgenticAI #Azure #CloudSecurity #LearningInPublic
