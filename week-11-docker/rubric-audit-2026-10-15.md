# Week 11 — reconciliation with the current DMI rubric

Eze Favour · 15 October 2026 · assistance and execution disclosed.

Source: [current instructor template](https://github.com/pravinmishraaws/devops-micro-internship-pravinmishra/tree/9535276e19bec0e2b30ed789d85d4cefe7620732/week-11-docker). The [DMI page](https://dmi.pravinmishra.com/s/Favourcloud.html) last reviewed 14 October reports **110/230**, **3/8 assignment files passing**, credited blog/LinkedIn, and 10 attendance points. That is an external result, not changed by this document.

## Filename repairs

The assignment now contains eight expected documents. Four completed September documents had older names. Their contents and original evidence are retained under the current expected names:

| Old filename | Current expected filename |
|---|---|
| `assignment-04-docker-volumes.md` | `assignment-04-docker-volumes-and-bind-mounts.md` |
| `assignment-05-sharing-the-docker-container-on-docker-hub.md` | `assignment-05-publish-a-docker-container-on-docker-hub.md` |
| `assignment-06-capstone-deploy-a-production-grade-stack-for-the-epicbook.md` | `assignment-07-capstone-deploy-a-production-grade-stack-for-the-epicbook.md` |
| `assignment-07-ai-assisted-docker-container-hardening-audit.md` | `assignment-08-ai-assisted-docker-container-hardening-audit.md` |

Internal Markdown links were updated; dated log/image names still reflect the September assignment numbering. They are historical evidence identifiers.

## Technical and evidence review

| Assignment | Verified evidence and change | Remaining current-template work |
|---|---|---|
| 1–3 | DMI already reports the files passing. Original lab evidence retained. | No new score loss reported for these files; current detailed examples differ in places from the September template. |
| 4 — storage | Existing bind-mount log preservation and shared-volume write/read screenshots retained. | The newer rubric explicitly requires removing **and recreating both** shared-volume app containers and a browser view afterward. The original isolated volume read alone is insufficient for this new slot. |
| 5 — registry | Original public versioned image and second-VM pull/run proof retained; `latest` published and targeted local remove/pull/run verified on 15 October. | Exact current terminal/browser views and assignment-specific post text remain. New local registry evidence, where linked in A5, does not replace fresh VM proof. |
| 6 — Book Review Compose | Newly implemented fork with health-gated MySQL/API/frontend, non-root production images, build-time browser API URL and CORS. 13 local checks pass; real browser review survives down/up. | Public VM deployment and address, the exact Network + Console screenshot, and assignment-specific LinkedIn publication remain pending. |
| 7 — EpicBook capstone | Original September cloud deployment, backup and fault evidence retained. October candidate has an Nginx frontend, backend image comparison, database-aware proxy readiness and a synthetic-row restore drill; 14 HTTP tests and local recovery tests pass. | Candidate rollout and the new 36-slot evidence layout still require cloud access. A local result is not a new cloud verification. |
| 8 — hardening audit | Original ordered Claude/Bedrock run: 3 FAIL to 6 PASS, operator-applied fixes and 15 audit/guard tests. | Reconcile the new 9-slot supplied-skill format, usage/LF check and current production target. The existing training target is explicitly disclosed and not silently relabelled as production. |

Cloud access was unavailable during this revision. The existing demos were not intentionally destroyed. Public deployment and publication requirements remain unchecked where unsupported. Attendance is controlled by DMI's Zoom records; no attendance request was sent.

[October local evidence](evidence/2026-10-15-rubric/) · [September ordered rerun](hardening-audit/ordered-rerun/README.md)
