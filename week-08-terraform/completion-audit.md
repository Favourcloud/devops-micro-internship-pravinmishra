# Week 08 Terraform — completion audit

Rubric reviewed on 22 September 2026; Assignment 04 live and Assignment 05 local-source progress updated on 24 September 2026 (Africa/Lagos). Checked against the [published DMI rubric](https://dmi.pravinmishra.com/how-it-works.html#rubric), the [Favourcloud feedback page](https://dmi.pravinmishra.com/s/Favourcloud.html), and the current assignment files. The feedback page was rechecked on 24 September: its displayed review date is 2026-09-23, and Week 08 remains 70/190 with 2/6 assignment files passing. The A2/A3 live deliveries have no observed regrade.

## Current score and remaining points

**25 September workflow follow-up:** the private A5 integration now has a verified Claude Sonnet 4.6 response through Amazon Bedrock, a seven-tool Terraform MCP connection, a model-selected provider lookup and a model-invoked six-stage offline validation pass. Three live terminal captures now fill slots 4, 5 and 17. Agent workflows, post-edit execution and deployment/runtime screenshots remain pending. See the [setup report](terraform-book-review/evidence/bedrock-setup-20260925.md); this fills three screenshot slots and makes no DMI regrade claim.

| Component | Awarded | Available | What remains |
|---|---:|---:|---|
| Six assignment files | 40 | 120 | Last review credited 01 and 06 only. Assignments 02 and 03 now have complete evidence and await review; 04–05 still have placeholders. 80 points remain unawarded. |
| Weekly LinkedIn post | 0 | 10 | Publish the reviewed post and put its full post URL in the root README's Week 08 row. |
| Weekly blog | 0 | 30 | Publish the reviewed article and put its URL in the same row. |
| Attendance | 30 | 30 | Fully credited; no GitHub edit is needed. |
| **Total** | **70** | **190** | **120 points remain.** |

The official score and completion status change only after DMI's next review. Fixing the screenshots directory has no separately published point value. A passing automated file check does not establish that the deployment requirements were completed: assignments 01 and 06 already receive file credit, while their own checklists still disclose unfinished requirements.

## Exact published grading rules

- Keep each file at the exact current template path and filename. All six expected Week 08 files are present.
- An assignment must differ from the untouched template and answer key, contain no template answer/screenshot/URL placeholders, and contain at least 50 words of original prose after the grader removes code, comments, headings and table formatting. It is worth 20 points or zero.
- The LinkedIn URL must be in the root README's Weekly Progress table and begin with `https://www.linkedin.com/posts/`. A profile URL or draft link does not qualify.
- The blog URL must be in that table, load publicly, contain at least 200 words, and contain an actual link to **https://dmi.pravinmishra.com/s/Favourcloud.html**. A mention of DMI or a link to another page does not meet that condition.
- Attendance is recorded by the DMI team, not inferred from GitHub activity.

Placeholder removal must follow completion of the corresponding work. Substituting an unsupported success statement, a local mock result or an unrelated image would not complete the assignment.

## Evidence inventory

These counts come from the numbered screenshot sections in the assignment files, not the number of duplicate image files on disk.

| Assignment | Existing numbered captures | Missing numbered captures | Work still needed |
|---|---:|---|---|
| 01 — Azure VM | 11 / 11 | None | Approved live plan/apply, public IP, Azure CLI VM-running verification and complete teardown captured. Already had automated file credit; technical evidence is complete and merged in PR #52. |
| 02 — AWS VM | 10 / 10 | None | Live plan/apply, EC2/SSH/HTTP/browser checks and complete teardown verified on September 23; delegated execution disclosed. Delivered to main in PR #50; awaiting DMI review. |
| 03 — Azure React | 15 / 15 | None | Approved live plan/apply, strict SSH, cloud-init, Nginx, public HTTP/SPA/assets/browser and complete teardown verified. Delegated execution and unchanged app placeholders disclosed; merged in PR #51. |
| 04 — AWS EpicBook | 34 / 35 | 35 | Deployment, browser/cart-to-RDS checks and full teardown verified. Checkout/order, learner reflection, mandatory publication and disclosed partial screenshot requirements remain. |
| 05 — Book Review capstone | 12 / 28 | 9–13 and 18–28 | AI generation/review/troubleshooting, post-edit execution, deployment and application evidence; 15 personal reflections remain unanswered. |
| 06 — Drift and policy review | 19 / 19 | None | Existing evidence describes delegated Terraform execution; the manual-execution requirement and publication remain open. Already credited by the automated file check. |
| **Total** | **101 / 118** | **17 missing** | An occupied image slot is not necessarily a completed task. |

The [screenshots index](screenshots/README.md) points to each assignment's original images and manifests. Its included Assignment 06 image is a byte-identical copy of an existing capture, not a new result or an additional completed screenshot slot.

## Checks performed on 22 September for earlier work

- The inspected local Week 08 worktrees contain no additional untracked PNG/JPEG evidence beyond the repository's known image paths.
- Local initialization metadata for assignments 01–03 contains no managed resources. The located Assignment 06 current state files are empty; their backups describe the earlier VPC/security-group lab. These files were inspected locally and are not published.
- The public Medium feed for `@rosenaefavour` has six distinct articles through Week 05 and no Week 08 article. This does not rule out an unpublished Medium draft.
- The repository already contains a [Week 08 LinkedIn draft](../publication-review/drafts/week-08-linkedin.md) and [Week 08 blog draft](../publication-review/drafts/week-08-blog.md). They describe the supported Assignment 06 work and disclose its limits. Their existence is not proof of publication.
- No Week 08 LinkedIn post URL is recorded in the progress table. LinkedIn publication has not been independently verified.

## Finish in this order

1. **Assignment 02: AWS VM — live work completed.** The approved September 23 run added 11 resources, passed real EC2/SSH/HTTP/browser checks and destroyed all 11. All 13 exact-ID cleanup checks passed, including the root disk and network interface; state is empty. All ten captures and the [run summary](terraform-aws-vm/evidence/live-run-summary.md) are included. PR #50 is merged to the default branch; await DMI’s next grading run. The operator was Codex under user delegation, not manual learner execution.
2. **Assignment 03: Azure React — live work completed.** All 15 captures are present. The [live run](terraform-react-azure/evidence/live-run-summary.md) added and destroyed eight resources, verified application readiness and browser rendering, and confirmed all eight independently addressable Azure objects absent, including the OS disk. PR #51 is merged. **Assignment 01 is also complete:** all 11 captures, actual VM-running verification, eight resources destroyed and exact Azure cleanup checks are now recorded in its [live summary](terraform-azure-vm/evidence/live-run-summary.md).
3. **Assignment 04: EpicBook — deployment and cleanup verified.** The [live summary](terraform-aws-epicbook/evidence/live-run-summary.md) records 28 application resources plus one separate public-key resource, real Node 22.23.3/MySQL 8.4.11 runtime, a matching browser Cart/Cartbook record and complete teardown in 32.95 minutes. Fifteen new captures fill slots 20–34. The original 19 images and infrastructure source remain unchanged. Checkout/order behavior, learner reflection and LinkedIn publication remain incomplete. The private RDS output and historical partial-view limitations are disclosed; do not mark the whole assignment complete.
4. **Assignment 05: Book Review.** The official kit has now been received from Udemy and compared with our setup; review the [prepared adaptations and integration requirements](terraform-book-review/evidence/starter-kit-review-20260924.md), then complete the actual Claude/MCP workflow, resolve the source/runtime release blockers in the [project README](terraform-book-review/README.md), and run the three-tier lab. Its two NAT gateways, load balancers and multiple database/compute instances require a costed plan before deployment. Drafted technical explanations can support learning, but the personal reflections should describe the learner's actual decisions and experience.
5. **Publish and link the weekly posts.** Review the existing drafts, publish the blog with the correct badge-page backlink and the LinkedIn post with relevant evidence, then enter the final public URLs in the root README's Week 08 row. Posting is a separate external action; a local draft is not a public URL.
6. **Recheck the official feedback after the next grading run.** Keep Week 08 marked In Progress until the corresponding requirements and evidence are complete.

## Immediate repository correction

The week-level `screenshots/` directory contained only `.gitkeep`, while genuine evidence was stored in assignment-specific subdirectories. It now has an index and one clearly identified existing Assignment 06 capture. This makes the available evidence discoverable at the expected week-level location without changing image contents, inventing missing results or altering assignment answers.

## Validation performed on 22 September

The existing offline runners for assignments 02–05 were rerun with Terraform 1.13.5 and the checksum-locked local AWS/AzureRM providers. All four passed their configuration formatting, initialization, validation and mock-test stages. Assignment 03 also passed 56 Python tests; Assignment 04 passed 65 Python tests. These runs did not create cloud resources or replace the missing live evidence.

The copied image's bytes and SHA-256 were checked against its tracked original. The September 22 audit left the assignment documents and Terraform implementations unchanged. The subsequent September 23 A2 work adds genuine evidence, checks verified checklist items and adds the signed Linux provider checksum without changing the infrastructure source.

The default AWS profile and the dedicated `dmi-week8` profile both returned `InvalidClientTokenId` during read-only identity checks. The dedicated profile is configured for `ap-south-1`. Those old credentials are inactive and were not reused. On September 23, the replacement account’s existing CloudShell session supported the approved A2 run. At that September 22 snapshot, Azure subscription metadata listed an enabled subscription but live access had not been verified. The later approved A3 run verified the current Azure identity, access, deployment and cleanup. No cloud deployment was attempted during the September 22 audit. The separately approved September 23 A2 deployment and cleanup are documented above.

## Assignment 02 completion on 23 September

The live run lasted approximately 8 minutes 28 seconds within the approved one-hour window and $1 ceiling. Estimated base usage was below $0.01; the actual bill has not been verified. The retired public IP is recorded as historical evidence only. The six new PNGs have separate capture provenance documenting privacy crops and JPEG-to-PNG conversion; no output text was changed. The four earlier captures, historical validation and original rubric requirements are preserved.

The A2-only snapshot had **47/99** for assignments 01–05 plus 19 for assignment 06, totaling **66/118** and **52 missing**. The updated A3 accounting is recorded below.

## Assignment 03 completion on 24 September (local date)

The approved Azure React run created eight Terraform resources in Sweden Central and verified the actual Ubuntu VM, strict SSH connection, cloud-init readiness, Nginx, public HTTP, SPA routing, assets and browser rendering. It then destroyed all eight resources. Exact Azure reads confirmed seven direct Terraform ARM objects plus the attached OS disk absent; NIC absence independently proves removal of the eighth Terraform resource, the NIC/NSG association. The resource group does not exist and state is empty. See the [live summary](terraform-react-azure/evidence/live-run-summary.md) for UTC timings and cost estimate; the actual bill remains unverified.

The seven new PNGs fill slots 9–15. The original eight images and historical provenance remain byte-for-byte unchanged. Browser evidence is a single native capture with the actual address bar and an adjacent Eze Favour attribution Terminal; the instructor app's name/date placeholders remain unchanged. Codex operated the live run under user delegation. No manual learner execution, new grade or social publication is claimed.

The A3-only snapshot had **54/99** for assignments 01–05 and **73/118** overall, with **45 missing**. Current accounting after A1 is below.

## Assignment 01 completion on 24 September

The separate approved Azure VM exercise now has **11/11** screenshots. Its real plan created eight resources, Azure CLI reported the VM running, and image, disk and public-IP checks passed. Terraform destroyed all eight resources. Eight independent Azure IDs were verified absent (seven direct Terraform ARM objects plus the OS disk), and NIC absence proves association removal. The resource group is absent and state is empty. The [live summary](terraform-azure-vm/evidence/live-run-summary.md) records timing, the retired IP and estimated base usage; the actual bill is unverified.

The six original PNGs and frozen source remain unchanged. Five new native Terminal captures show the actual approved A1 results under Codex delegation. Generated password-bearing private artifacts were removed only after verified teardown; no user credentials were changed or published. A1 already had DMI file credit, so this closes technical evidence gaps without promising additional points.

**A1-completion snapshot: 59/99 for assignments 01–05, plus 19 for Assignment 06 = 78/118 occupied slots, with 40 missing.** Assignments 01–03 now have all required captures and verified cleanup. Assignments 04–05, Assignment 06's manual-execution requirement and both weekly publication links remain open. Last observed DMI score: **70/190**; no new grading result is claimed.


## Earlier default-branch delivery and access snapshot on 24 September

[PR #52](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/pull/52) merged A1's complete runtime evidence. [PR #53](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/pull/53) merged A4's Node maintenance update. Both reviewed source commits are ancestors of inspected main commit `365f2423ed7441530010d744193446b2d9e4a625`. All 11 A1 screenshot hashes and A4's updated source hash were verified on that commit. The numbered-slot count at that snapshot was **78/118**, with **40 missing**; merging existing evidence does not add another capture or establish a new grade.

At that earlier snapshot, browser control returned `Codex auth token is unavailable`; the latest local AWS profile checks returned `InvalidClientTokenId`. A4 had not started then. This access blocker was subsequently resolved using the existing console session and isolated temporary CLI authentication; see the later run below. The completed A1–A3 labs remain cleaned up.

A5's [instructor application](https://github.com/pravinmishraaws/book-review-app/tree/84280063bea7ccd5144dafa2b969ec4e2e69ffbb) still has the same pinned revision. A complete tree lookup found no starter-kit files. The [course repository](https://github.com/pravinmishraaws/devops-micro-internship-pravinmishra) also has no identifiable A5 starter kit; the related [book-review-infra repository](https://github.com/pravinmishraaws/book-review-infra) contains Terraform/Azure pipeline source without Claude/MCP kit files. Relevant local coursework archives contained earlier portfolio-oriented Claude definitions, not a verified A5 kit. The source location was unknown at this snapshot; the later Udemy discovery below resolves that gap. The dependency release gate, real Claude/MCP activity, learner reflections and publication remain open.


## Assignment 04 live run on 24 September

The approved A4 AWS deployment and real application/cart-to-RDS verification succeeded. All 29 resources were destroyed; both Terraform states are empty. Exact AWS checks covered every managed resource, the root disk, recorded network children and retained-backup absence. The 32.95-minute window was within the approved $1/60-minute limit. Estimated base usage for the whole window is $0.0205 before extras; the actual bill is unverified. No cloud resources from this lab remain.

**A4-completion snapshot: 74/99 for assignments 01–05 plus 19 for Assignment 06 = 93/118 occupied slots, with 25 missing.** A4 now has 34/35 captures; its checkout/order, personal reflection and publication requirements remain unfinished. A5 still has 24 missing captures plus its starter-kit/dependency/Claude workflow and personal work. A6's manual learner requirement and both weekly publication URLs remain open. No new DMI grade is claimed.

The [new A4 provenance](terraform-aws-epicbook/evidence/live-provenance.json) explicitly records CloudShell replay of genuine local/SSH output, two live AWS CLI views, browser attribution annotations, the redacted RDS hostname, and correlation of the actual single cart request with its unique database row. These capture limitations do not waive the original rubric.


## Assignment 05 local evidence on 24 September

Five new original browser captures show the unchanged six-subnet source, tier routes/security, Multi-AZ primary, separate read replica and private database configuration. They occupy slots 7, 8, 14, 15 and 16, bringing A5 to **9/28** and the week to **98/118**, with **20 missing**. The original four A5 images and all 59 protected/source files remain byte-identical to the frozen baseline. See [new provenance](terraform-book-review/evidence/local-capture-provenance-20260924.json).

The unchanged protected runner again passed all six stages, including validate/provider-schema and 43 explicit mock plans, using the locked local provider with IP networking denied. The separately captured stage summary is supporting evidence only: Screenshot17's literal Terraform output remains missing. No cloud resources, Claude/MCP workflow, release approval or learner answers were produced. The original 28 screenshot requirements, 15 reflection questions and 55 unchecked checklist entries remain preserved.

[PR #56](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/pull/56) merged the A4 evidence at `74645e14d0c72616b494bdea1a1e29065fdad253`. DMI was refreshed again and still reports **70/190**, last reviewed **2026-09-23**. The instructor university Login link opened a Payhip sign-in form; that observation did not establish the kit's location or a Payhip prerequisite. The later authenticated Udemy discovery below supersedes the access uncertainty. A5's vulnerable upstream release and unprepared runtime/AMI also remain blockers. No new A5 spending is authorized by the completed A4 budget.

## Assignment 05 official kit received and reviewed on 24 September

The enrolled Udemy course provides `book-review-agentic-ai.zip` under **Section 8 → Assignment 37 → Instructions → Download resource files**. The archive passed integrity checks and its six files were compared with the existing A5 setup. The [review](terraform-book-review/evidence/starter-kit-review-20260924.md) records the official source, file hashes, configuration differences and a private inactive candidate. No course files are redistributed, protected project configuration changed, or Claude/MCP/cloud operations performed. The assignment explicitly offers no complete step-by-step implementation; its Instructor example is `N/A`.

Kit discovery and private integration are complete. The 25 September follow-up above verifies the bounded MCP lookup and offline validation through Bedrock. Agent workflows, post-edit validation, dependency/runtime resolution, the costed deployment, learner work and publication remain pending. New live terminal captures show MCP connected, the configured post-edit hook and exact successful Terraform validation output. Screenshot counts are now **A5 12/28; Week 08 101/118**, with **17 missing**. The latest instructor app commit still matches the vulnerable pinned revision; [runtime readiness](terraform-book-review/evidence/runtime-readiness-20260925.json) records the remaining release and deployment inputs. No new grade is claimed.
