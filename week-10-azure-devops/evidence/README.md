# Genuine screenshot attachments — 19 September 2026

**Six numbered slots have captures (eight original PNGs); 30 numbered slots and A2's separate LinkedIn image remain missing. No assignment is complete. Human visual/privacy review remains pending.** See the [current machine-readable totals](current.json).

The original PNG bytes are embedded immediately below the matching screenshot requirements in the briefs. No pixels were synthesized, edited or used as placeholders. Native Chrome URL/focus checks, local OCR markers, SHA-256 and PNG chunk checks were verified; archive verification is recorded in separate publication receipts. OCR is not exhaustive human visual/privacy review: open each full-size image before submission.

| Assignment and exact slot | Original capture | What it establishes / limitation |
| --- | --- | --- |
| [A1 screenshot 1](../assignment-01-set-up-a-self-hosted-linux-agent-for-azure-devops.md#screenshot-1--azure-devops-agent-pools-page-showing-the-newly-created-pool) | [Dedicated pool](../screenshots/assignment-01-screenshot-01-agent-pool.png) | Retained `DMI-Week10-A1` pool; not a currently Online agent. |
| [A1 screenshot 7](../assignment-01-set-up-a-self-hosted-linux-agent-for-azure-devops.md#screenshot-7--successful-test-pipeline-run-output-in-azure-devops-showing-the-linux-commands) | [Linux pipeline output](../screenshots/assignment-01-screenshot-07-linux-pipeline-output.png) | Historical successful run 1 on 18 September, including Linux, `azdoagent` and disk output. The host was subsequently removed. |
| [A2 screenshot 1](../assignment-02-deploy-a-static-website-to-aws-ec2-using-an-azure-devops-cicd-pipeline.md#screenshot-1--azure-static-website-in-azure-repos) | [Azure Repos files](../screenshots/assignment-02-screenshot-01-azure-repos.png) | Imported repository and files including `index.html`; no deployed website or application pipeline success. |

[Machine-readable provenance](captures-2026-09-19.json) records exact capture times, original hashes, dimensions, source URLs, OCR checks and limitations. Its image paths, and the [A1 manifest](../self-hosted-agent/evidence/manifest.json) paths, are relative to `week-10-azure-devops/`. A captured slot means an image exists, not that a human reviewer has accepted it or an assignment is complete.

## Later A2 YAML source capture — one slot, three views

[A2 screenshot 3](../assignment-02-deploy-a-static-website-to-aws-ec2-using-an-azure-devops-cicd-pipeline.md#screenshot-3--azure-pipelines-yaml) contains original views of the existing, pinned Azure Repos YAML:

1. [Push trigger, pool declaration and variables](../screenshots/assignment-02-screenshot-03-part-01-trigger-pool-variables.png).
2. [Checkout and pipeline information](../screenshots/assignment-02-screenshot-03-part-02-pipeline-information.png).
3. [CopyFilesOverSSH and SSH verification task definitions](../screenshots/assignment-02-screenshot-03-part-03-ssh-tasks.png).

Captured at **09:19–09:26 UTC** using guarded native source navigation and scrolling, without source edits, service connections, builds or deployments. The connection identifier is still a placeholder, and the pool default is not proof of an Online agent. These are **source-only, incomplete-configuration evidence**, not successful task output. [Separate provenance](static-yaml-2026-09-19.json) records hashes, dimensions, capture times and limitations. No pixels were stitched, edited or synthesized. The original three-capture provenance remains an unchanged historical bundle; use `current.json` for cumulative availability.

At the **09:19–09:26 UTC** capture checkpoint, fresh paid-resource approval had not been provided. Subsequent A1 approval is separate from this source-only record. No A1 authorization was replayed, and no AWS/Azure resource, agent, service, pipeline run, social post or paid AI activity was created by this capture pass. A3/A4 LinkedIn images and A5's actual supplied kit, healthy pipelines and authorized triage still need genuine work.

## Historical snapshot versus later evidence

The [submission snapshot](../submission/status.json) and [original handoff](../SUBMISSION.md) describe the zero-image source package verified at **08:15:30 UTC**, before these captures at **08:30–08:33 UTC**. Their historical receipt and test counts are not rewritten as new live proof. This index is the later evidence supplement.

The earlier A1-only approval before 09:00 UTC led to read-only preflight, not provisioning: the expected Azure identity and dedicated Azure DevOps resources were accessible, but the SKU query timed out. No fresh VM, registration, service or pipeline run was created. The ten-minute submission deadline prioritised attaching available genuine evidence rather than fabricating missing live screenshots.

## Local integration validation

On 19 September at **09:01:18 UTC**, **331 local checks passed**: A1 43, Azure adaptation 21, application/source 145, EpicBook 51, cleanup/operator/recovery 58, and submission/evidence 13. Tests used an empty environment, isolated Python without bytecode, denied networking and denied ordinary-file writes (`/dev/null` discard exception only). These checks validate source, exact attachment placement, PNG integrity and original requirement preservation—not live cloud facts or human visual review. No native Terraform suite or application build was rerun.

The later YAML integration passed **338 local checks at 09:30:25 UTC** on the same date, under the same empty-environment/network/write-denied conditions: 43 A1, 21 Azure adaptation, 145 application/source, 51 EpicBook, 58 cleanup/operator/recovery and 20 submission/evidence. Seven added checks cover the new original PNGs, source-only claims, placement and cumulative counts; the earlier 331-test result remains historical. These are not CI or live acceptance results.

## Later A1 VM/SSH capture — two slots

The separately authorized, assistant-operated lab produced original [running Ubuntu VM/public-IP evidence](../screenshots/assignment-01-screenshot-02-running-ubuntu-vm.png) at **19:48 UTC** and [fresh trusted SSH/Ubuntu output](../screenshots/assignment-01-screenshot-03-ssh-ubuntu-details.png) at **19:49 UTC**. They replace only A1-S2 and A1-S3's redundant prompts. [Separate capture provenance](a1-vm-ssh-2026-09-19.json) and the [actual operational receipt](../self-hosted-agent/runtime-2026-09-19.json) record hashes, timing and limits. Native local CPU-only OCR verified the required context and found no sensitive-screen marker; this is not exhaustive human review.

The package passed digest/version/library checks, but registration timed out at the optional TFVC licence prompt **before the PAT was sent**. No new service, Online agent or pipeline run resulted. A corrected attempt was not authorized. The runbook now explains answering **N** for Git-only work, but successful registration recovery is not claimed.

Terraform destruction completed at **20:04:40 UTC**. A strict verifier initially rejected the disk's `ResourceNotFound` wording. After eight network/write-denied parser tests, a read-only recheck verified empty state, exact resource-group/VM/disk/IP absence and zero agents at **20:07:17 UTC**, before expiry. The existing PAT was not changed or revoked; observed Full access metadata is not a least-privilege compliance claim. The 81 prior controller tests and eight parser tests are local invocation checks, not CI or assignment acceptance.

## Still required

- A1 slots **4–6**: successful configuration, running service and Online agent. These require fresh bounded authorization; the VM used for slots 2–3 no longer exists. Least-privilege PAT compliance, private expiry/revocation handling and the learner's own issue/resolution reflection remain pending. Attributed technical notes describe actual trials, not learner reflection.
- A2 slots **2, 4 and 5**, plus its separate LinkedIn image and actual live deployment requirements. Slot 3's source capture does not resolve its unset connection or runtime gates.
- All A3 **6**, A4 **6** and A5 **12** numbered slots and their live prerequisites.
- Human review of all eight images, the original checklists and the learner's own reflections. No checklist item or reflection was completed by attaching images.

All original requirement text is preserved. The six captured slots now replace their redundant screenshot prompts rather than appearing beneath unanswered placeholders. A1's attributed technical notes replace its generic answer prompt while explicitly retaining the missing learner-reflection requirement. The [shared preservation contract](../submission/brief_contract.py) reverses only these allowlisted substitutions and the historical preparation-notice correction to compare against unchanged original hashes. Image bytes, provenance, historical receipts and all unmet requirements remain unchanged. Passing these checks is not an assignment-completion or human-review claim.
