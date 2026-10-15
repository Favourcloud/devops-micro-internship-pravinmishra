# 15 October 2026 — current rubric reconciliation

Eze Favour · DMI Week 11 · Codex execution under learner authorization.

These are **local Docker Desktop** builds and exercises. They do not establish a new AWS deployment. September cloud evidence stays in its original dated folders. The active DMI template at review time was commit `9535276e19bec0e2b30ed789d85d4cefe7620732`.

- [Book Review integration report](bookreview-tests.json): 13 checks passed, including login, creation/read of a review, CORS preflight and refused origin, private MySQL and down/up persistence.
- [Book Review execution log](bookreview-tests.log) and [final frontend build](bookreview-build-final.log).
- [EpicBook HTTP checks](capstone-http-tests.json): 14 checks passed, including catalogue, signed cart, checkout, session isolation and refused sensitive paths.
- [EpicBook recovery drill](capstone-recovery-tests.log): a dedicated synthetic probe was backed up, deleted, restored, and preserved across down/up; backend/database failures returned unavailable responses and then recovered. Existing application records were not intentionally deleted.
- [Backend image comparison](capstone-image-sizes.json): baseline 1,708,635,557 bytes, optimized 380,178,260 bytes, **77.75% smaller**. The comparison-only image was removed after recording its digest/size to recover local disk space. Source and build output remain reproducible.

Cloud deployment, current cloud-console captures, remaining exact screenshot requirements and assignment-specific publication are not inferred from these local results. See [the current rubric audit](../../rubric-audit-2026-10-15.md).
