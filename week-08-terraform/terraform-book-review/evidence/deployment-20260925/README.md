# Verified AWS capstone — 25 September 2026

**Eze Favour** · [Live HTTPS demo](https://xdr0flp20e.execute-api.us-east-1.amazonaws.com) · [Released source and architecture](../../releases/2026-09-25-aws/README.md)

The Book Review application is deployed and its API/browser/database tests pass. Codex performed authorized cloud and browser operations. Claude Code used Amazon Bedrock for the separately recorded improvements, troubleshooting and named-role reviews. Manual learner execution and delegated subagents are not claimed.

## Actual verification

| Check | Observed result | Original record |
|---|---|---|
| Infrastructure | Four t3.large Web/App nodes in two AZs; three load balancers active; all five targets healthy; private encrypted Multi-AZ primary and separate read replica | [AWS API evidence](live-evidence.json) |
| HTTPS/API | Homepage 200, catalogue, registration 201, login 200, review POST 201 followed by independent GET; anonymous review 401, book write 405, invalid login 400 | [API result](api-e2e-result.json) |
| Browser | Login as isolated Eze Favour test user, book details, review submission, reload and retained authenticated session | [Browser result](browser-e2e-result.json) |
| Database | New API review present on primary and replica; TLS 1.3 with CA/hostname verification; secure transport required; replica read-only; wrong CA and hostname rejected | [Database result](database-evidence.json) |
| Recovery | AWS events confirm forced Multi-AZ failover; one sampled 503 then automatic HTTP 200 recovery with both saved reviews; no manual reset | [Recovery record](recovery-evidence.json) |
| Direct ALB bypass | Both direct requests, including spoofed origin headers, failed to connect from outside the VPC | [Recovery record](recovery-evidence.json) |
| Source tests | 100 exported Python tests; 45 Terraform mock tests with IP networking denied | [Python result](final-python-tests.json), [actual Terraform output](terraform-mock-tests.md) |
| Final reconciliation | Non-targeted main and prerequisite plans report no changes | [Plan result](reconciliation-evidence.json) |
| Final AI review | Completed named reviewer main session: no tool calls, PASS with warnings, no FAIL findings; operator corrections retained | [Original response](bedrock-final-architecture-review.result.json), [corrections](final-review-followup.md) |

The API-created review was ID 3. A separate browser-submitted review was ID 4. The initial database evidence was recorded before the browser submission and therefore reports three total reviews; the later recovery record independently retrieves both new review IDs. The read replica is a separate reporting path; the application uses the primary.

RDS events span roughly 35 seconds between failover start and completion. Our sampled API returned 503 once and 200 again about 42 seconds after the request. This does not establish a precise outage duration or availability SLO. The database's reported AZ label stayed the same; we do not claim an independently observed AZ switch. This was one failover test, not an entire AZ outage or sustained load test.

## Deployment and fixes

Initial deployment applied 51 resources followed by a fresh reviewed 35-resource plan. Subsequent reviewed applies persisted runtime fixes, removed the completed initializer's five resources, added the internal NLB entry, and corrected gateway/read-only request compatibility. All four ASG refreshes completed successfully. The two initial-phase apply screenshots are historical records of those phases, not a claim that no later changes occurred.

The corrections address real failures: protected Ubuntu systemd 0440 credentials, Nginx's long hostname map and journald stderr handling, Router AppArmor runtime access, the API VPC-link connection failure, and zero-length GET handling. The public ALB uses AWS defensive desync mode in API mode; the internal ALB retains strictest. Nginx strips bodies/Content-Length for permitted read-only routes. See [HTTP rejection evidence](gateway-http400-root-cause.json) and [final normalization plan review](web-readonly-normalization-plan-review.json).

The API entry uses private SG boundaries. Browser HTTPS terminates at API Gateway; subsequent HTTP remains inside the VPC. Database connections verify TLS CA and hostname. The application is a learning deployment with a fixed four-node baseline, not a production-readiness or automatic scaling claim. The upstream dark-mode catalogue has low title contrast; homepage captures use disclosed temporary light-mode emulation. No screenshot pixels or application source were altered to hide it.

## Original screenshots and provenance

[Current 28-slot manifest](submission-manifest.json) joins the preserved earlier images with this delivery. [Capture provenance](capture-provenance.json) records original image hashes, timestamps, browser settings and source-record hashes. The source snapshots are immutable copies of the exact records rendered at capture time. Later AWS inventory can differ after rolling replacement without changing what those historical images prove.

| Assignment slot | Capture |
|---|---|
| 9 — Compute | [Recorded AWS API view](screenshots/screenshot-09-recorded-final.png) |
| 10 — Public ALB | [Recorded AWS API view](screenshots/screenshot-10-recorded-final.png) |
| 11 — Internal load balancers | [Recorded AWS API view](screenshots/screenshot-11-recorded-final.png) |
| 12 — Healthy targets | [Recorded AWS API view](screenshots/screenshot-12-recorded-final.png) |
| 13 — RDS | [Recorded AWS API view](screenshots/screenshot-13-recorded-final.png) |
| 18 — Initial plan | [Historical reviewed-plan view](screenshots/screenshot-18-recorded-evidence.png) |
| 19 — Initial applies | [Recorded real CLI results](screenshots/screenshot-19-recorded-final.png) |
| 20 — Homepage | [Actual HTTPS app](screenshots/screenshot-20-https-homepage-light-mode.png) |
| 21 — Authentication | [Actual authenticated app](screenshots/screenshot-21-authenticated-light-mode.png) |
| 22 — Book details | [Actual book page](screenshots/screenshot-22-book-details.png) |
| 23 — Review | [Actual review after reload](screenshots/screenshot-23-review-after-reload.png) |
| 24 — API | [Recorded real API tests](screenshots/screenshot-24-recorded-final.png) |
| 25 — Database | [Recorded real TLS/SQL results](screenshots/screenshot-25-recorded-final.png) |

Infrastructure/API/CLI screenshots are clearly labeled recorded evidence viewers, not AWS Console or live-terminal images. That distinction is retained for rubric review. Original earlier slots 1–8, 14–17 and 26–28 remain in the parent evidence directory. The completed final review adds [supplemental original evidence](screenshots/final-architecture-review.png) without replacing the older partial-review image.

## Cost, retention and privacy

Eze Favour explicitly requested that the capstone remain online until cleanup is requested. No automatic teardown is scheduled. Core resources are estimated at $0.5873/hour ($14.10/day), before storage, public IPv4, traffic, requests, LCU charges and taxes. This is not the actual bill. The temporary builder and initializer, including the initializer identity/log resources, are removed.

[Operations and cleanup](../../releases/2026-09-25-aws/runtime/OPERATIONS.md) cover the remaining main stack, prerequisites, artifact bucket/distribution, AMI/snapshots, secrets and retained backups. Cleanup must remain task-scoped. Public evidence excludes credentials, account IDs, state, saved plans, private test accounts and raw access logs.

The reflection answers are AI-assisted project explanations under user authorization, not proof of the learner's own words or manual execution. A complete numbered-image inventory does not waive such rubric requirements.
