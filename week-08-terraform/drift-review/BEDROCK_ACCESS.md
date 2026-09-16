# Bedrock enrollment and review continuation

**Eze Favour — enrollment and later clean/risk/final native Claude reviews verified on 16 September 2026.** The [current-cycle record](reports/live/cycle-20260916.json) documents the subsequent human decision and verified cleanup. This access runbook preserves the earlier troubleshooting and authorization boundaries; it is not an instruction to repeat enrollment or model calls.

The [sanitized continuation record](reports/continuation-20260916.json) verifies
private MFA authentication, user-triggered local SDK acceptance at **13:26:22 UTC**,
and independent readiness at **13:27:31 UTC**: agreement `AVAILABLE`, authorization
`AUTHORIZED`, entitlement `AVAILABLE`, region `AVAILABLE`. No model call was used
to establish that readiness. The [dated setup record](enrollment-proposal/SETUP-20260916.md)
contains the full timeline and completion boundaries.

The temporary session expired at **13:29 UTC** and the unchanged permission
window at **13:30 UTC (14:30 Lagos)**. Do not reuse or silently renew them, repeat
the completed acceptance, or treat expiry as proof of identity/key removal.
The separate restricted runtime profile is not the enrollment profile.
The user separately approved up to **$0.32 within the existing $0.50 allowance**
for global Haiku reviews and the safe hook demonstration; the **$0.18 unknown-usage
reservation is preserved**. This runbook grants no additional approval.

The historical connection test succeeded, but subsequent Claude reviews failed
with Marketplace enrollment authorization errors. Those facts are compatible:
[AWS documents temporary invocation success during automatic enrollment](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html),
followed by `AccessDeniedException` when prerequisites are missing. The error
alone does not identify whether the missing prerequisite is enrollment,
Anthropic first-use information, payment eligibility, or an organization rule.

## Verified continuation preflight

Read-only checks on 15 September 2026 found:

- The expected branch was clean at `aa3cc73615d4550d0f3627689953f92c1aa3f0c1`.
- The standard AWS configuration listed only `default` and `dmi-week8`.
- An identity-only check classified `default` as root. No administrative
  operation was performed using it.
- `dmi-week8` authenticated as a non-root IAM user, but its read-only request to
  list attached IAM policies returned `AccessDenied`. No administrator profile
  was verified. The user reported an available administrator profile; its exact
  local profile name or separate configuration still needs clarification.
- Installed AWS CLI was **2.26.1**. AWS documents **2.27.42 or later** for the
  model-agreement and availability commands below. An unsupported-command error
  from the older CLI is not evidence of denied model access.

The restricted Bedrock runtime role must keep its existing boundary. It needs
no Marketplace subscription permission after an authorized administrator has
enabled the chosen model for the account. Do not attach an administrator or
Marketplace policy to the runtime role, bypass an organization restriction,
restart OmniRoute, or enable the legacy root/personal Claude settings.

## Historical administrator enrollment procedure

**Reference only: acceptance is now complete. Do not repeat it or use the expired
session.** The actual user-triggered SDK acceptance and read-only verification
supersede the earlier handoff below; no new administrator session is needed merely
to repeat this evidence.

Use an authorized **non-root administrator**, in a separate console session or
explicitly named local profile. The user handles login, MFA, payment details and
terms acceptance. Do not copy credentials, account identifiers, offer tokens or
billing information into reports, model prompts or screenshots.

1. Confirm the intended account privately and verify that the identity is not
   root. A modern CLI can print only the root check, without an account ID:

   ```bash
   aws --profile ADMIN_PROFILE --region ap-south-1 sts get-caller-identity \
     --query "ends_with(Arn, ':root')" --output text
   ```

   Stop if this returns `True` or fails. `False` verifies only a non-root
   identity; it does not prove enrollment permissions.
2. Select **Claude Haiku 4.5**, model
   `anthropic.claude-haiku-4-5-20251001-v1:0`, in the Mumbai Bedrock model catalog.
   Keep the existing global inference profile and provider choice.
3. Check whether the Anthropic first-use submission is already accepted. The
   educational project form was submitted earlier; do not invent or resubmit
   organization information without a demonstrated need.
4. Privately verify the model's Marketplace enrollment and account payment
   eligibility. If enrollment is missing, the administrator reviews the actual
   offer and applicable terms and completes the one-time agreement. The user
   accepts the terms and supplies any billing details. Do not deploy a
   Marketplace endpoint or purchase provisioned throughput.
5. Using a supported CLI or SDK under that administrator identity, inspect
   availability without invoking the model:

   ```bash
   aws --profile ADMIN_PROFILE --region ap-south-1 \
     bedrock get-foundation-model-availability \
     --model-id anthropic.claude-haiku-4-5-20251001-v1:0 \
     --query '{agreement:agreementAvailability.status,authorization:authorizationStatus,entitlement:entitlementAvailability,region:regionAvailability}' \
     --output json
   ```

   Expected readiness fields are `AVAILABLE`, `AUTHORIZED`, `AVAILABLE` and
   `AVAILABLE`, respectively. If the call is denied, stop and have the
   administrator resolve the stated permission or organization restriction.
   Do not infer payment status from a generic authorization error. Share only
   these readiness fields and the model name when reporting progress.

AWS's documented programmatic enrollment sequence is
`ListFoundationModelAgreementOffers`, the Anthropic first-use submission when
needed, `CreateFoundationModelAgreement`, and
`GetFoundationModelAvailability`. Agreement creation and terms acceptance belong
to the authorized human administrator; they are not read-only diagnostic steps.

## Resume only after readiness and budget confirmation

Preserve the existing ledger: the historical test reported **$0.00017**.
At the review approval, the separate **$0.50** allowance had **$0 reported
completed usage**, **$0.18 reserved for incomplete records**, and **$0.32 unreserved**.
After the subsequent bounded reviews and native controls, reported additional
usage is **$0.141731**; including the unchanged reservation, **$0.321731** is
accounted and **$0.178269** remains. The reservation is not a verified charge or
an account billing audit. No further model call is needed.

The user confirmed the bounded **$0.32 remaining review allowance at
2026-09-16T13:30:22.429Z**. Record usage atomically, reserve before invocation,
and block concurrent or unreconciled runs before the next billable call. Do not
release the historical $0.18 reservation without reconciliation. Stop on an
access failure instead of repeating retries or switching models. A CLI budget
threshold is not an AWS account spending cap.

Use a new private run directory and the reviewed isolated launcher environment.
Retain controlled, byte-identical Skill registration and explicitly selected
nested hook settings. The original launcher's interactive `review` mode alone
does not establish Skill discovery, a bounded budget, or hook enforcement.
Do not rerun it as a shortcut. Verify actual tool and hook events; the original
tool-free `--bare` connection test cannot provide that evidence.

The separately approved new isolated VPC/closed-SG cycle subsequently completed:
actual clean/risk reviews, fresh-FAIL native denial, the user's reject-public-SSH
decision, fresh final evidence and a genuine final Claude review. Copilot—not a
manually operating human—executed the authorized operations. SG-then-VPC cleanup
was independently verified at **2026-09-16T16:01:58Z**. Both dated labs are deleted;
old plans/reports are historical, not a current baseline. The enrollment permission
expiry was not extended. [Screenshot provenance](screenshots/manifest.json) and the
[assignment](../assignment-06-ai-assisted-terraform-drift-and-policy-review.md)
track actual capture completion and remaining publication/manual-execution limits.
