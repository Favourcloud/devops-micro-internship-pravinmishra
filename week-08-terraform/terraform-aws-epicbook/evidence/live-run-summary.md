# Assignment 04 — verified AWS EpicBook run

The approved deployment, browser/cart verification and teardown succeeded on **24 September 2026**. **34/35 numbered screenshot slots now have captures:** the original 19 local images plus 15 new images for slots 20–34. This is **not a complete Assignment 04 submission**: checkout/order behavior, the learner's reflection and mandatory LinkedIn publication remain unfinished, and specific screenshot limitations are disclosed below. All new work was performed by Codex under user delegation.

## Verified infrastructure and runtime

The unchanged project from commit `3bb863a56ceaadb2eacdbef35a25c340b3aa0c57` created **28 resources**. A separate Terraform root imported the existing local SSH public key as **one lab-owned AWS key-pair resource**, for 29 total. The private key never entered Terraform or Git. Both real saved plans, their source/input hashes and the approved account were checked before apply. Terraform 1.13.5 used AWS provider 6.64.0 and the unchanged lock file. The15 copied source/lock/bootstrap files matched their hashes; no upstream JavaScript changed.

| Check | Actual result |
|---|---|
| Network | VPC; public app subnet; two local-only database subnets in us-east-1a/1b |
| EC2 | t3.micro, Canonical Ubuntu 24.04.5 LTS, AMI ami-0045d7fc2ad003464 |
| Storage | Encrypted 12 GiB EC2 gp3 root volume; encrypted 20 GiB RDS gp3 |
| Access | Public HTTP 80; SSH 22 from the controller's single IPv4 only; no public 8080/MySQL ingress |
| Database | MySQL 8.4.11, db.t3.micro, single-AZ, private, available |
| IAM | EC2-only role trust; GetSecretValue scoped to the one actual lab secret |
| Credentials | IMDSv2 required; password/secret contents in write-only fields; absent from user data |
| Bootstrap | cloud-init done, no errors; pinned instructor commit checked |
| Software | Node 22.23.3, npm 10.9.9, Nginx 1.24.0; MySQL client 8.0.46 |
| Database session | TLS_AES_256_GCM_SHA384; 53 authors and 54 books |
| Services | epicbook-config, epicbook and Nginx active; Nginx config valid |
| HTTP | App 8080, Nginx 80 and public catalogue returned 200; real catalogue rendered |
| Destruction |28 application resources and1 public key destroyed; independent checks passed |

The Ubuntu image lookup was deferred in the saved plan. The candidate was rechecked before apply, and the created instance matched it. The actual IAM secret policy and rendered user data were verified privately after allocation. The SSH host key was matched against a fingerprint obtained through authenticated EC2 console output, then used with strict host-key checking. A protected Nginx config required `sudo` for a diagnostic read; no application, IAM, TLS or file-permission relaxation was needed. The original helper's full-host-key wait was replaced locally with verified fingerprint matching. These were verification-tool adjustments, not deployment-source changes.

The public address was **`3.234.183.199`**, now retired following cleanup. Do not treat the old address as a current service. The pinned dependencies remain old upstream versions; successful runtime verification does not certify their security.

## Real browser-to-database evidence

The browser displayed a seeded product and one **Add to Cart** click for **28 Summers**. The captured request was `POST /api/cart`, `bookId=1`, at **2026-09-24T07:23:31.588509+00:00**, and received **HTTP 200**. The cart UI showed one item and total **$28**. The database was empty of carts before the click; afterward the read-only helper returned:

| Record | Values |
|---|---|
| Cart | id 1, quantity 1, price 28.00, createdAt 2026-09-24 07:23:32 UTC |
| Cartbook | CartId 1, BookId 1 |
| Checkout | No rows returned |

The record timestamp is **0.411491 seconds** after the captured browser request. The application's immediate reload evicted the POST response body before retrieval. The request and200 response are preserved; the association is established by the empty baseline, single new cart/join, matching book, quantity, price and server time. No second POST or manual data insertion was used to make the evidence pass.

The instructor app has **no order-creation endpoint**; its checkout action deletes carts. The cart test satisfies the narrower evidence for screenshots 32–33, while the separate checkout/order checklist stays unchecked. A verified instructor fix or separately authorized upstream work is still required.

## Cleanup and cost

- First apply started: **2026-09-24T07:06:00.631780+00:00**.
- All 29 resources created: **2026-09-24T07:14:54.337933+00:00**.
- Cleanup independently verified: **2026-09-24T07:38:57.790892+00:00**.
- Total run window: **32.95 minutes**, within the approved 60 minutes.

Both Terraform destruction plans were inspected for the approved resource addresses and delete/no-op actions, then applied in application-first/key-second order. Both `terraform state list` results were empty. Read-only AWS checks verified all 29 captured managed resources absent or EC2 terminated. Ten recorded child identifiers were also checked, including the root EBS volume and VPC network children; some route-table/security-group IDs overlap managed resources and are **not ten extra distinct Terraform resources**. The secret and version, IAM role/policy/profile, RDS instance/subnet/parameter groups, snapshots/backups and public-key resource were removed. The old local private key remains.

AWS returned its specific `DBInstanceAutomatedBackupNotFound` response for the removed DB's automated backup. The local verifier initially treated that as an error; it was corrected to accept only that documented absence result, and the full check passed. AccessDenied, timeouts and unrecognized errors were not accepted as deletion evidence. The 28-resource application ledger also passed the repository's consistency checker; the key was verified separately. The local fallback observed completed cleanup and is no longer needed.

The base price estimate is **$0.037414/hour**. Applying it conservatively to the entire window gives approximately **$0.0205**, excluding CPU-credit use, requests, bandwidth, billing minimums/rounding and tax. **The actual bill has not been verified.** No free-tier discount is assumed, and this approval does not authorize another run.

## Capture provenance and remaining requirements

Original19 PNGs and historical [provenance](provenance.json) are unchanged. New [live provenance](live-provenance.json) records image hashes, capture times, dimensions, source-log hashes and limitations. Screenshots 20–22,25–30,33–34 show genuine recorded local Terraform/EC2-SSH output replayed in CloudShell with an explicit label. Screenshots 23–24 show live read-only AWS CLI queries executed there. Captures may therefore occur after command execution or cleanup; numbering is rubric order.

Browser screenshots 31–32 show the real app. A temporary, clearly labelled DOM banner supplied Eze Favour, delegation attribution and the current browser URL; it was removed after capture. It is not instructor-app functionality, and browser chrome is not in these captures. Unannotated originals remain private. PNG pixels were not edited or composited. CloudShell captures use a capture-time rectangle that excludes the AWS account header.

Screenshot 22 deliberately redacts the private RDS hostname, so the full endpoint is not visually reproduced. Screenshot 4 remains the original partial Explorer view although private tfvars was created for this run; screenshot 10 remains a partial historical script view. Screenshot 34 shows the equivalent saved-plan destruction workflow (`plan -destroy`, then saved-plan `apply`), with the actual completion messages. These distinctions are retained rather than claiming every visual requirement is fully satisfied.

**Screenshot 35, the LinkedIn URL, learner reflection and checkout/order behavior remain pending.** No social post was published. The last observed DMI score remains70/190; this run does not establish a regrade. Historical offline checks passed 22 Terraform mocks and 65 Python tests before deployment; new evidence checks validate this delivery separately.
