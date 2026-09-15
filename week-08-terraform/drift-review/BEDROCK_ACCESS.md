# Restore Bedrock access before another live review

**Eze Favour — enrollment is not yet verified. No new inference or deployment is authorized by this runbook.**

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

## Human administrator enrollment step

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

Preserve the existing ledger: the historical test reported **$0.00017**;
the separate additional allowance is **$0.50**, with **$0 reported completed
usage**, **$0.18 reserved for incomplete usage records**, and **$0.32 unreserved**.
The reservation is not a verified charge. This continuation made no new model
call and does not release reservations or increase the allowance.

Present a bounded retry/review budget and obtain the user's confirmation before
the next billable call. Stop on an access failure instead of repeating retries
or switching models. A CLI budget threshold is not an AWS account spending cap.

Use a new private run directory and the reviewed isolated launcher environment.
Retain controlled, byte-identical Skill registration and explicitly selected
nested hook settings. The original launcher's interactive `review` mode alone
does not establish Skill discovery, a bounded budget, or hook enforcement.
Do not rerun it as a shortcut. Verify actual tool and hook events; the original
tool-free `--bare` connection test cannot provide that evidence.

Only after access is verified, obtain fresh approval for a new isolated VPC and
closed, unattached security group and their cleanup. The previous lab is deleted;
old plans and reports cannot serve as a new baseline. Follow the ordered review
loop in the assignment, including a genuine human resolution decision before
the resolution is executed. Screenshots **10, 12, 15, 16 and 17 remain pending**.
