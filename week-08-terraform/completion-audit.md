# Week 08 Terraform — completion audit

Rubric reviewed on 22 September 2026; Assignment 02 progress updated on 23 September 2026. Checked against the [published DMI rubric](https://dmi.pravinmishra.com/how-it-works.html#rubric), the [Favourcloud feedback page](https://dmi.pravinmishra.com/s/Favourcloud.html), and the current assignment files. The feedback page was rechecked on 23 September: its displayed review date is 2026-09-23, and Week 08 remains 70/190 with 2/6 assignment files passing. This A2 delivery has not yet been graded.

## Current score and remaining points

| Component | Awarded | Available | What remains |
|---|---:|---:|---|
| Six assignment files | 40 | 120 | Last review credited 01 and 06 only. Assignment 02 now has complete evidence and awaits review; 03–05 still have placeholders. 80 points remain unawarded. |
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
| 01 — Azure VM | 6 / 11 | 7–11 | Real plan/apply, allocated IP, Azure verification and teardown. Already credited by the automated file check. |
| 02 — AWS VM | 10 / 10 | None | Live plan/apply, EC2/SSH/HTTP/browser checks and complete teardown verified on September 23; delegated execution disclosed. Ready for grading after delivery to the default branch. |
| 03 — Azure React | 8 / 15 | 9–15 | Real plan/apply, public IP, VM/SSH/application verification and teardown. |
| 04 — AWS EpicBook | 19 / 35 | 20–35 | Plan/apply/outputs, EC2/RDS checks, database initialization, application/cart-to-database evidence, teardown and publication. |
| 05 — Book Review capstone | 4 / 28 | 4–5 and 7–28 | Remaining architecture/validation images, actual Claude/MCP workflow, deployment and application evidence; 15 personal reflections remain unanswered. |
| 06 — Drift and policy review | 19 / 19 | None | Existing evidence describes delegated Terraform execution; the manual-execution requirement and publication remain open. Already credited by the automated file check. |
| **Total** | **66 / 118** | **52 missing** | An occupied image slot is not necessarily a completed task. |

The [screenshots index](screenshots/README.md) points to each assignment's original images and manifests. Its included Assignment 06 image is a byte-identical copy of an existing capture, not a new result or an additional completed screenshot slot.

## Checks performed on 22 September for earlier work

- The inspected local Week 08 worktrees contain no additional untracked PNG/JPEG evidence beyond the repository's known image paths.
- Local initialization metadata for assignments 01–03 contains no managed resources. The located Assignment 06 current state files are empty; their backups describe the earlier VPC/security-group lab. These files were inspected locally and are not published.
- The public Medium feed for `@rosenaefavour` has six distinct articles through Week 05 and no Week 08 article. This does not rule out an unpublished Medium draft.
- The repository already contains a [Week 08 LinkedIn draft](../publication-review/drafts/week-08-linkedin.md) and [Week 08 blog draft](../publication-review/drafts/week-08-blog.md). They describe the supported Assignment 06 work and disclose its limits. Their existence is not proof of publication.
- No Week 08 LinkedIn post URL is recorded in the progress table. LinkedIn publication has not been independently verified.

## Finish in this order

1. **Assignment 02: AWS VM — live work completed.** The approved September 23 run added 11 resources, passed real EC2/SSH/HTTP/browser checks and destroyed all 11. All 13 exact-ID cleanup checks passed, including the root disk and network interface; state is empty. All ten captures and the [run summary](terraform-aws-vm/evidence/live-run-summary.md) are included. Deliver the reviewed changes to the default branch and await DMI’s next grading run. The operator was Codex under user delegation, not manual learner execution.
2. **Assignment 03: Azure React.** Follow the [runbook](terraform-react-azure/README.md) for the eight-resource Azure lab. Capture real application readiness separately from a successful Terraform apply, then verify cleanup. Complete Assignment 01's remaining Azure VM evidence during its own distinct exercise.
3. **Assignment 04: EpicBook.** Follow the [runbook](terraform-aws-epicbook/README.md). The prepared design includes 28 managed resource instances and an RDS database. Resolve the documented upstream checkout/order limitation before marking that checklist item complete; the current upstream supports cart evidence but not a completed checkout/order record.
4. **Assignment 05: Book Review.** Obtain or identify the required instructor starter kit, complete the actual Claude/MCP workflow, verify the source/runtime release blockers in the [project README](terraform-book-review/README.md), and run the three-tier lab. Its two NAT gateways, load balancers and multiple database/compute instances require a costed plan before deployment. Drafted technical explanations can support learning, but the personal reflections should describe the learner's actual decisions and experience.
5. **Publish and link the weekly posts.** Review the existing drafts, publish the blog with the correct badge-page backlink and the LinkedIn post with relevant evidence, then enter the final public URLs in the root README's Week 08 row. Posting is a separate external action; a local draft is not a public URL.
6. **Recheck the official feedback after the next grading run.** Keep Week 08 marked In Progress until the corresponding requirements and evidence are complete.

## Immediate repository correction

The week-level `screenshots/` directory contained only `.gitkeep`, while genuine evidence was stored in assignment-specific subdirectories. It now has an index and one clearly identified existing Assignment 06 capture. This makes the available evidence discoverable at the expected week-level location without changing image contents, inventing missing results or altering assignment answers.

## Validation performed on 22 September

The existing offline runners for assignments 02–05 were rerun with Terraform 1.13.5 and the checksum-locked local AWS/AzureRM providers. All four passed their configuration formatting, initialization, validation and mock-test stages. Assignment 03 also passed 56 Python tests; Assignment 04 passed 65 Python tests. These runs did not create cloud resources or replace the missing live evidence.

The copied image's bytes and SHA-256 were checked against its tracked original. The September 22 audit left the assignment documents and Terraform implementations unchanged. The subsequent September 23 A2 work adds genuine evidence, checks verified checklist items and adds the signed Linux provider checksum without changing the infrastructure source.

The default AWS profile and the dedicated `dmi-week8` profile both returned `InvalidClientTokenId` during read-only identity checks. The dedicated profile is configured for `ap-south-1`. Those old credentials are inactive and were not reused. On September 23, the replacement account’s existing CloudShell session supported the approved A2 run. Azure subscription metadata lists an enabled subscription; live Azure access has not been verified. No cloud deployment was attempted during the September 22 audit. The separately approved September 23 A2 deployment and cleanup are documented above.

## Assignment 02 completion on 23 September

The live run lasted approximately 8 minutes 28 seconds within the approved one-hour window and $1 ceiling. Estimated base usage was below $0.01; the actual bill has not been verified. The retired public IP is recorded as historical evidence only. The six new PNGs have separate capture provenance documenting privacy crops and JPEG-to-PNG conversion; no output text was changed. The four earlier captures, historical validation and original rubric requirements are preserved.

Current image accounting is **47/99** for assignments 01–05 plus 19 for assignment 06, totaling **66/118** and **52 missing**. The last observed official score remains **70/190**; no regrade has been observed. Assignment 01’s live work, assignments 03–05, assignment 06’s manual-execution requirement, and the weekly publications remain open.
