# Reliability results

| Test | Observed result |
|---|---|
| Catalogue through split UI/API/MySQL | 200 and nine displayed books |
| Cart + synthetic checkout | Browser order 2, cart 4, subtotal 32.50; independent SQL matches |
| Independent clients | Signed cart remains isolated |
| Foreign Origin | 403 |
| Invalid/missing book | 400 / 404 |
| Secret/source paths | 403 / 404 |
| Backend stopped | Frontend 503 with retry message; cart is not cleared |
| Database stopped | Frontend 503; backend health 503 |
| Services restored | Four Compose services healthy, catalogue available |
| Cold snapshot clone | Catalogue/cart/order counts and order rows match |
| Docker audit training baseline | Three PASS and three FAIL |
| Operator remediation | Six PASS; effective UID 1000; healthy runtime |

[HTTP/SQL tests](../../evidence/2026-09-26/a6-http-tests.json), [backend fault](../../evidence/2026-09-26/a6-backend-fault.txt), [database fault](../../evidence/2026-09-26/a6-database-fault.txt), [restore](../../evidence/2026-09-26/a6-snapshot-restore.txt) and [audit runtime](../../evidence/2026-09-26/a7-final-live-inspection.txt) retain actual results. The public screenshots show the live UI and its error page, not simulated renderings.

These tests deliberately introduce downtime and prove controlled recovery, not zero-downtime availability or HA. The audited weak container was an isolated training baseline with no published port. It was not substituted for the public hardened backend. Codex performed the operator actions under the learner's authorization; the evidence does not claim personal learner execution.
