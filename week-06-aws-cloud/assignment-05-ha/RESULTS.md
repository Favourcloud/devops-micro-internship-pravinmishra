# Assignment 5 — actual deployment and resilience results

**Run date: 15 September 2026 (UTC).** An isolated Terraform lab was deployed and tested in `us-east-1`. This report makes no grade guarantee and does not claim uninterrupted availability.

## Outcome

| Check | Actual result | Evidence |
| --- | --- | --- |
| HA network | Four subnets across `us-east-1a` and `us-east-1b`; public IGW routes, private NAT routes | [Baseline snapshot](evidence/baseline.json), [rendered architecture capture](evidence/architecture-evidence.png) |
| Security | ALB → web port 80; web → DB port 3306; private DB, encrypted storage, IMDSv2, verified MySQL TLS | Terraform and baseline snapshot |
| Database | MySQL **8.4.9**, Multi-AZ, available, not publicly accessible | Baseline; [later snapshot](evidence/test-a-after.json) explicitly reports primary `us-east-1b`, standby `us-east-1a` |
| Web tier | Two healthy instances in different AZs; ASG **min 2 / desired 2 / max 4** | Baseline, [recovered snapshot](evidence/recovered.json) |
| Application | Real HTML-form insert, then read of that row from two distinct web instances | [Baseline read/write](evidence/read-write-baseline.json), [live app screenshot](evidence/application-live.png), [mobile screenshot](evidence/application-mobile.png) |
| Test A: abrupt termination | Automatic replacement succeeded; **283/287 probes succeeded, 4 failed** | [Action](evidence/experiment.json), [termination state](evidence/terminated-instance.json), [recovery](evidence/test-a-after.json), [all probes](evidence/test-a-probes.jsonl) |
| Test B: web-tier AZ evacuation | Two healthy instances served from `us-east-1b`, then two-AZ distribution restored; **260/260 probes succeeded** | [Evacuated snapshot](evidence/test-b-evacuated.json), [read/write during evacuation](evidence/read-write-evacuated.json), [recovery](evidence/recovered.json), [all probes](evidence/test-b-probes.jsonl) |
| Data persistence | Records written before termination and during evacuation remained readable after restoration | [Persistence result](evidence/persistence-after-recovery.json) |
| Terraform drift | No changes required after restoring defaults, before teardown | Verified with `terraform plan -detailed-exitcode` (exit 0) |
| Local validation | 30 app tests, 12 monitoring/termination-guard tests, 5 mocked Terraform tests passed | Reproducible commands in README |

**Task 8's strict “without interruption” criterion is not met by Test A.** Recovery and redundancy worked, but four failed probes must not be relabeled as zero downtime. Task 9 is a results summary, not a declaration that every requirement passed.

## Test A timeline

- Monitoring: **01:15:26–01:23:15 UTC**, `GET /ready` performing a database query, no retries.
- Termination accepted: **01:19:44 UTC**, instance `i-0c61b083e64f74019` in `us-east-1a`; desired ASG capacity was not decremented.
- Two HTTP **502** responses were observed at **01:19:46** and **01:19:47**. Two probes beginning at **01:19:52** and **01:20:01** timed out after five seconds.
- Replacement `i-0105f6ee8acfed1ff` and surviving `i-0c9ff12b01e5fe629` were observed healthy across two AZs by **01:22:49 UTC**. The recovery snapshot was captured at **01:22:55 UTC**.
- Exact durations are observations, not a contractual recovery-time guarantee. Requests may fail while an abrupt target loss is detected. Planned draining, appropriate health-check tuning and retry/error-budget design are follow-up considerations; none was silently added to hide this run's errors.

An initial AWS FIS template request failed with `SubscriptionRequiredException`. No FIS experiment ran or subscription was enabled. The actual test used a Terraform-triggered, exact-instance EC2 termination after checking VPC, project tag, ASG membership/capacity and both healthy targets. Temporary FIS IAM resources were removed through Terraform.

## Test B scope and timeline

- Monitoring: **01:23:35–01:30:35 UTC**, 260 successful database-readiness probes, no observed failures.
- Terraform temporarily restricted the ASG subnet selection to AZ B. It did **not** remove an ALB subnet or change RDS.
- At **01:26:33 UTC**, the snapshot showed `i-0c9ff12b01e5fe629` and `i-0d4e5495fb5b81371` in `us-east-1b`; an additional form write/read passed there.
- After restoring default subnet selection, the **01:30:13 UTC** snapshot showed healthy `i-05337f6f87beaee27` in `us-east-1a` and `i-0d4e5495fb5b81371` in `us-east-1b`.
- This was **controlled web-tier AZ evacuation**, not an abrupt AWS AZ outage, network partition or RDS failover exercise. ASG could launch new capacity before removing old capacity. Zero failed samples do not prove that every possible request succeeded.

![Measured failure-test evidence rendered from the recorded AWS CLI responses and probe logs](evidence/availability-evidence.png)

## Evidence integrity

- The architecture and availability screenshots are **rendered AWS CLI evidence**, explicitly labeled as such—not fabricated AWS Console captures. The application images were captured from the live ALB with JavaScript disabled.
- The first RDS snapshot showed `MultiAZ: true` but had not yet populated secondary-AZ metadata. It is preserved unchanged; subsequent snapshots explicitly show the standby AZ.
- Probe logs include failures without retries or filtering. Sampling uses a one-second pause after each request, so it is not precisely one request per second; request duration and timeout extend the spacing.
- Account IDs are redacted from new snapshots and ARN segments. Passwords, private keys and secret values are excluded. Resource IDs remain for traceability.
- Earlier screenshot evidence in the parent assignment remains historical and contains account identifiers; this run does not certify those original images as redacted.

## Teardown and cost

**Teardown verified on 15 September 2026 at 01:40 UTC:** Terraform destroyed all 37 managed lab resources. [Read-only cleanup verification](evidence/cleanup.json) confirms empty Terraform state and no remaining lab resources in the 18 checked categories, including RDS, ALB, ASG, NAT, EIPs, VPC, launch templates, IAM roles/profiles and database logs. The lab's synthetic database records were deleted without a final snapshot. Assignment 4 was excluded: its original EC2 instance is still running in its original VPC and `epicbook-db` remains available, private and single-AZ.

The captured ALB URL is historical evidence and must not be advertised as live after teardown. A rough continuously running cost estimate is $140–$180/month before traffic/tax and account credits; no free-tier or zero-bill guarantee is made. Final charges can lag resource deletion. Existing Assignment 4 resources can still incur charges.

## Remaining submission items

1. Address or explicitly discuss the strict zero-interruption gap in Test A; do not mark that criterion passed from these logs.
2. Confirm the instructor accepts consolidated CLI-derived evidence and SSM instead of an SSH `/32` rule; provide exact console screenshots if the rubric requires them.
3. Redact historical submission images before checking the parent assignment's “No sensitive data exposed” item.
4. Publish the user's own LinkedIn post with the actual results and proof image, then add its real URL. No post has been published by this work.

### LinkedIn draft — not published

> Built and tested a Terraform-managed two-tier AWS lab across two Availability Zones: ALB, a 2/2/4 Auto Scaling Group, private encrypted Multi-AZ MySQL, and a server-rendered application.
>
> Verified real database writes/reads through the ALB. An abrupt instance termination triggered automatic replacement, with four transient failed probes—an important reminder that redundancy does not guarantee zero downtime. Controlled web-tier AZ evacuation and restoration recorded 260 successful probes with no observed failures.
>
> Captured the evidence and tore down the temporary lab to limit costs. Next focus: improve failure handling and validate the strict availability requirement.

Attach `evidence/availability-evidence.png`. Publish this draft only after cleanup is confirmed; do not substitute the old Assignment 6 post or claim a live URL after teardown.
