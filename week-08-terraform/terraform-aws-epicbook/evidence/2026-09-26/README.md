# AWS EpicBook checkout verified — 26 September 2026

**Learner: Eze Favour. Operator: Codex under delegated authorization.** The AWS authentication blocker is resolved. A fresh EC2/RDS deployment now proves the previously missing checkout/order behavior.

- The browser saved **order2** for **cart3**, and an independent TLS-verified RDS query found that same order with subtotal **32.50**: [browser capture](aws-order2.png), [matching database record](browser-order-rds.json), [labeled record viewer](aws-rds-proof-view.png).
- **22 actual HTTP/SQL checks passed**, including separate signed carts, cross-origin rejection, replay-safe order creation, decimal money storage and persistence after restarting the Node application: [complete result](checkout-e2e.json).
- Cloud-init, Nginx and application services, encrypted private RDS, mandatory TLS and runtime-secret file permissions were verified: [control plane](control-plane.json), [runtime](runtime.json), [services](services.txt), [catalogue](aws-home.png).
- All 15 deployed implementation files match the public source: [source hashes](deployed-source.json).
- The exact **28-resource** temporary stack and root EBS volume were removed after proof. The existing shared AWS key and all previously retained demos remain: [cleanup verification](cleanup.json).

The recorded URL `http://100.53.229.121/` is **retired**; do not treat it as a current demo. The separate AWS Book Review capstone remains available at https://xdr0flp20e.execute-api.us-east-1.amazonaws.com/ as requested.

## Reproducible corrections

The pinned instructor commit remains `763becebb8d3f5663a76bb30facddc25be63cfd5`. The [disclosed checkout patch](../../modules/ec2/demo-checkout.patch), adapted from the already-tested Week09 implementation, adds signed cart membership and transactional, replay-safe demo checkout. It also labels the page with the learner, week and date. No payment or shipment occurs.

EC2 user data is gzip-compressed to fit AWS’s 16 KiB limit. A random session secret is generated on the instance and stored in a root-only persistent file; it is not present in Terraform inputs/state or the bootstrap payload. The app retains its limited database login, verified TLS and metadata-access restriction.

The first RDS create attempt rejected a 48-character master password because this API permits at most 41. Validation now enforces 24–41 characters, tested at both boundaries, and the retry used a new 36-character random password. RDS normalizes its TLS switch to `1`; Terraform now uses that representation to avoid recurring `ON`/`1` changes. [Actual apply summary](apply-summary.txt).

## Validation and evidence scope

24 Terraform mock tests, 67 Python/offline/evidence checks, and 6 signed-cart tests passed. Historical screenshot/source tests bind their original Git revision; they do not require the repaired source to be identical to an earlier deployment. [Offline test log](offline-tests.txt), [signed-cart log](signed-cart-tests.txt), [patch verification](patch-validation.json).

Images are genuine browser page captures or explicitly labeled recorded-output viewers. They do not include browser chrome or manufacture learner-personal/native-terminal actions. Original September24 evidence is retained as history. The published Week08 write-up remains linked from the root progress table.
