# Week 11 submission review — 26 September 2026

All seven assignment files now contain source, recorded results and mapped screenshot links. The public blog and 10-line LinkedIn post are published and in the root progress table. [Open the submission](week-11-docker/).

| Requirement | Evidence |
|---|---|
| VM, cloud-init, static website | A1: Ubuntu EC2, Docker install log, image/container output and original browser capture |
| React single/multi-stage | A2: both Dockerfiles and browser runs, 854,614,809 → 94,232,874 bytes, eight-line analysis |
| Docker networking | A3: all four network modes, custom DNS, MongoDB insert/read, host cleanup |
| Persistent storage | A4: bind logs survive removal; shared named volume initial message and two updates |
| Docker Hub | A5: authenticated login, tag/push, public repository, digest pull/run on a different VM |
| EpicBook capstone | A6: ten named docs including diagram, split services, proxy/CORS, health, real restore, JSON logs, cloud/browser/SQL, dependency faults and runbook |
| Claude audit | A7: real Bedrock plan and skill; isolated baseline 3 failures → 6 passes; final public backend also 6 passes; eight behavior tests |
| Publication | Public article with own DMI link; canonical LinkedIn `/posts/` URL, image, credit and disclosure |

## Honest limits

Codex executed the work under learner delegation. Command/editor screenshot slots use labelled browser renderings of actual saved output or source, rather than pretending to be live Terminal/VS Code screenshots. Original sources and records accompany every such figure. The audit's first script draft predated Claude planning, and personally manual learner editing is not claimed. These remain assessor decisions even though the functional workflow is verified.

The cloud app is a single-host teaching deployment. CloudFront serves HTTPS to the viewer, but its origin hop is HTTP. No real payment is taken. The optional CI/CD task was not selected; teardown is deferred under the learner's instruction to keep the demos online until cleanup is requested. Earlier demos were left intact. There is no claim of perfect production security, an automatically accepted submission, or a new DMI score.

[Machine-readable final checks](week-11-docker/evidence/final-validation.json) · [Evidence index](week-11-docker/evidence/README.md) · [Publication receipt](week-11-docker/publication/README.md).
