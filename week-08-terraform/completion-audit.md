# Week 08 completion audit — 25 September 2026

The last directly observed [DMI feedback](https://dmi.pravinmishra.com/s/Favourcloud.html) is **110/190**, with **4/6 assignment files passing**. The site says “Last checked: 2026-09-24.” It flagged A4/A5 template placeholders and missing weekly LinkedIn/blog URLs. The new evidence and publication links address those file/submission gaps; no regrade has yet been observed.

| Grading component | Last awarded | Available | Current delivery |
|---|---:|---:|---|
| Six assignment files | 80 | 120 | All six retained at exact paths. A4's publication slot and A5's 13 missing captures/15 explanations are now supplied with provenance and limitations. |
| LinkedIn | 0 | 10 | Public `/posts/` URL in the root Weekly Progress row; five project proof images and actual publication captures. |
| Blog | 0 | 30 | Published Medium article, 911-word draft, and exact clickable learner DMI profile backlink verified in the published page. |
| Attendance | 30 | 30 | Already credited by DMI. |
| **Total** | **110** | **190** | **80 points remain unawarded until the next DMI review.** |

The grading rules award file credit for changed submissions at the required paths, sufficient original prose and absence of template placeholders. That automated check is distinct from proving every technical or manual requirement. Publication credit requires the actual URLs in the root table; a draft or profile URL is insufficient.

## Verified work and evidence inventory

| Assignment | Numbered image slots | Verified work | Remaining limits |
|---|---:|---|---|
| A1 Azure VM | 11/11 | Approved deployment, VM-running/image/disk/IP checks, complete exact-resource teardown; merged PR52 | Delegated operator disclosure |
| A2 AWS VM | 10/10 | EC2/SSH/cloud-init/Nginx/HTTP/browser verification, 11-resource destroy and 13 exact-ID checks; merged PR50 | Delegated operator disclosure |
| A3 Azure React | 15/15 | App/assets/SPA/browser checks, 8-resource destroy and independent absence checks; merged PR51 | Unchanged instructor name/date placeholders; delegated operation |
| A4 EpicBook AWS | 35/35 | Real browser cart matched RDS; all 29 lab resources destroyed; mandatory LinkedIn post and original post-gallery capture | Instructor app lacks order-creation endpoint; no checkout claim. Historical partial/redacted captures remain disclosed. Assisted publication is not firsthand manual execution. |
| A5 Book Review | 28/28 | Live HTTPS app, API auth/review/persistence, browser review/reload, primary/replica TLS and persistence, controlled RDS failover/recovery, completed Bedrock review, 15 assisted project explanations and publication | Infrastructure captures are labeled recorded API/CLI viewers, not AWS Console views. Earlier source captures remain historical. Named roles ran as main sessions, not delegated subagents. Personal wording/manual requirements remain for learner review. |
| A6 Policy review | 19/19 | Unsafe public SSH proposal rejected; native hook blocked apply; AWS read-back, final Claude review and cleanup; detected/final proof now published | The explicit manual learner Terraform execution requirement remains unfulfilled. |
| **Total** | **118/118** | All numbered slots occupied with original captures | Image count does not establish a full-rubric pass. |

[Published article/post and original publication captures](publication/README.md) · [A5 deployment report](terraform-book-review/evidence/deployment-20260925/README.md) · [A5 released source](terraform-book-review/releases/2026-09-25-aws/README.md).

## What changed in the capstone

The deployed path is browser HTTPS → API Gateway → private VPC link → internal NLB → required internet-facing ALB → Web → internal ALB → private App → private MySQL. The entry security groups do not admit arbitrary Internet ingress. The six-subnet/two-AZ design, Multi-AZ primary and separate read replica remain. HTTP inside the VPC is not TLS on every hop; database connections verify CA and hostname.

Actual tests passed registration/login, book reads, review writes and independent persistence, while rejecting anonymous review creation, invalid login and unsafe book writes. Original CUA screenshots show the browser flow. Database probes verified TLS 1.3, read-only replica behavior and failure for wrong CA/hostname. The RDS event stream confirms forced failover completion; a sampled 503 was followed by automatic recovery with both reviews intact. The AZ label did not change, so an independent AZ-switch claim is explicitly withheld.

100 exported Python tests and 45 IP-denied Terraform mock tests passed. Both final non-targeted real Terraform plans showed no changes. Claude's final named-role review completed with no FAIL findings; its overstatements are corrected in a separate operator follow-up. AI review is not a security certification.

## Remaining completion boundaries

1. **DMI regrade:** Wait for the next review run and verify its actual result. Do not replace 110/190 with an expected score.
2. **Learner requirements:** Review the assisted explanations and perform any manual activity the rubric explicitly requires. Tool-operated work cannot truthfully satisfy A6's manual-execution checkbox.
3. **Instructor application mismatch:** A4's source has no order-creation endpoint. A working cart/database record is verified; completed checkout is not. This requires instructor interpretation or a separately agreed app extension.
4. **Evidence interpretation:** Recorded API/CLI viewers, historical source views, original A4 redaction/partial-view limitations and named-role main sessions are clearly identified for the reviewer.
5. **Ongoing deployment:** At the user's explicit request, A5 stays online until cleanup is requested. No automatic teardown is scheduled. Core resources cost about $0.59/hour before extras; temporary builder and initializer are removed. The task-scoped cleanup plan includes remaining infrastructure, artifacts, images/snapshots, secrets and backups.

The original source and earlier manifests remain preserved. Historical tests now explicitly target archived dated briefs; the separate current-submission checks verify that screenshot requirements, all 15 A5 questions, checklist text, immutable evidence and real publication links are retained. This prevents a historical preparation snapshot from being misrepresented as the current deployed state.
