# Eze Favour — Bedrock enrollment proposal

**DRAFT FOR HUMAN REVIEW — NOT ATTACHED, NOT ENROLLED, NO INFERENCE EXECUTED.**

Prepared on 15 September 2026 from the AWS references below. The existing lab
user's console login now works. This proposal addresses the separate model
enrollment blocker; it is not a Claude review or assignment screenshot.

## Concrete proposed access

Use [haiku-enrollment-policy.json](haiku-enrollment-policy.json) as both the sole
permissions policy and the permissions boundary of a separate, human-operated
identity named `dmi-week8-enrollment`. No identity or policy has been created by
this proposal. Do not attach it to `dmi-week8` or the Claude runtime role. Human
approval must cover identity creation, this exact access scope, and the setup
operator before any AWS access change. The previous permission to use root for
the lab user's own-password fix does not authorize this new setup operation.

The intended model is `anthropic.claude-haiku-4-5-20251001-v1:0`, with enrollment
requests originating in `ap-south-1`. AWS's model card identifies its Marketplace
product as `prod-xdkflymybwmvi`. The runtime's existing global inference profile
is unchanged; its cross-region routing is separate from these enrollment calls.

All grants expire at **2026-09-16 00:45 UTC (01:45 Africa/Lagos)**. This is a fixed
end time, not two hours from attachment. If the draft expires before use, prepare
a newly reviewed window rather than silently extending it. Detach and retire the
temporary identity after the approved enrollment session; that cleanup must also
be reviewed and verified.

| Permission | Actual restriction and limitation |
| --- | --- |
| `bedrock:GetFoundationModel` | Only the public Haiku 4.5 foundation-model ARN in Mumbai. |
| `bedrock:ListFoundationModels`, `bedrock:ListFoundationModelAgreementOffers`, `bedrock:GetFoundationModelAvailability`, `bedrock:GetUseCaseForModelAccess` | Read-only metadata in Mumbai. AWS requires `Resource: "*"` for these actions. They can read more than one model's metadata or the account's submitted use case. Keep returned use-case details private. |
| `bedrock:CreateFoundationModelAgreement` | MFA-authenticated calls in Mumbai before expiry. **AWS does not support a model resource or model-specific condition key for this action. It is an account-level agreement-creation permission.** The statement name does not enforce human approval; the human must review and submit the specific agreement. |
| `aws-marketplace:Subscribe` | Only calls forwarded through Bedrock, with a present product-ID list containing only `prod-xdkflymybwmvi`. `ForAllValues` plus `Null: false` avoids accepting a mixed-product request or a missing key. |
| `aws-marketplace:ViewSubscriptions`, `aws-marketplace:Unsubscribe` | AWS lists both as model-access prerequisites. Allowed only through Bedrock before expiry. **Neither can be product-scoped with `aws-marketplace:ProductId`.** Direct Marketplace calls are not allowed. |

The agreement-creation permission itself is **not guaranteed to be Haiku-only**.
The product condition constrains Marketplace subscription, not every possible
Bedrock agreement operation. Likewise, the service-mediated unsubscription grant
is not a product-specific boundary. These limitations require explicit review;
do not describe the whole policy as fully restricted to a single model.

AWS's own `AmazonBedrockFullAccess` policy uses `aws:CalledViaLast` for Marketplace
operations. This draft uses that pattern without attaching the full-access
policy. The initial preference to omit unsubscription was revised because AWS's
published prerequisites include it. It is listed explicitly above, not hidden
in a wildcard action. No successful enrollment under this narrower draft has
been demonstrated. If AWS requires an additional action, stop and review the
exact denial; do not fall back to full access.

Bedrock entry-point actions require an MFA-authenticated session. Marketplace
forwarded calls use `aws:CalledViaLast` rather than assuming that every original
authentication context key survives the service call. The principal's permitted
Bedrock calls remain MFA-gated. Both paths share the fixed expiry.

No policy statement permits inference, streaming, agreement deletion, use-case
submission, billing changes, IAM administration, role assumption, endpoints,
provisioned throughput, EC2 resources, or Terraform operations. In particular,
`bedrock:DeleteFoundationModelAgreement` is absent. Using this policy as the
boundary is part of the proposal; another attached policy must not be used to
expand the envelope. This is an IAM design review, not proof of effective AWS
authorization or an AWS spending cap.

## Human setup and enrollment sequence

1. Review and approve the scope above, including the account-level agreement
   action and service-mediated unsubscription prerequisite. Use a separate
   authorized setup operator; the current lab user cannot administer IAM.
2. If approved, create the dedicated identity, attach the reviewed policy as its
   permissions policy and boundary, and verify the attachments. Configure its
   authentication and MFA privately. This policy does not grant self-service IAM
   credential administration. The human setup operator must complete that setup;
   do not create a forced-password-reset loop or extract any credentials.
3. Establish a non-root, MFA-authenticated local session for that identity using
   authorized access. No access key, password, token, QR code or cookie belongs
   in chat, source control, screenshots or model prompts. Credential setup is a
   separate human action; this draft does not generate keys or assume that a
   configured profile exists. Ordinary long-lived access keys without an MFA
   session will not satisfy this policy.
4. Use a supported official CLI or SDK. The last verified AWS CLI was 2.26.1;
   AWS requires 2.27.42 or newer for these agreement commands. No CLI upgrade has
   been performed by this draft. This API-based route does not grant CloudShell
   permissions or use a playground invocation to trigger enrollment.
5. Verify non-root identity locally without printing identifiers. Read
   `GetUseCaseForModelAccess`, `ListFoundationModelAgreementOffers` and
   `GetFoundationModelAvailability` for the intended model. No inference is
   needed. Keep raw responses and offer tokens private. Do not re-submit the
   earlier educational use-case form unless a verified missing requirement
   justifies a separately approved submission.
6. If enrollment already exists, do not create another agreement. If it is
   missing, the human reviews the actual offer, pricing and legal terms and
   submits `CreateFoundationModelAgreement` for Haiku 4.5 with the verified offer
   token. This can establish an account-wide agreement and is not a read-only
   operation. The policy is not itself permission for the agent to accept terms.
7. Verify availability without inference. Expected fields are agreement
   `AVAILABLE`, authorization `AUTHORIZED`, entitlement `AVAILABLE`, and region
   `AVAILABLE`. Report only those status fields and the model name. An error is
   a blocker, not proof that a larger permission set is necessary.
8. Review and remove the temporary enrollment access; verify removal. Retain the
   existing Bedrock runtime role for inference. Obtain the user's fresh bounded
   model-budget approval before any Claude call, then fresh provisioning/cleanup
   approval before creating another Terraform lab.

## Billing and remaining gates

The console previously showed the Free account plan. AWS says this plan excludes
**certain** Marketplace offers that can incur charges; this does not establish
whether this particular Haiku agreement is eligible. The human must check the
actual offer and account payment eligibility privately. No account upgrade,
payment detail, purchase, subscription or terms acceptance has occurred here.
Do not upgrade the plan automatically to diagnose a generic access error.

The earlier reported connection cost remains $0.00017. The separate $0.50
allowance still has $0 reported completed usage, $0.18 reserved for incomplete
usage records (not confirmed charges), and $0.32 unreserved. This proposal makes
no model call, changes no ledger entry, and authorizes no additional spending.

The five assignment slots 10, 12, 15, 16 and 17 remain pending. Existing genuine
images and historical synthetic/live reports are unchanged. No new screenshot,
human resolution approval, Claude review, hook event or deployment is claimed.

## Verification and references

JSON parsing and local checks can establish draft structure, exact allowed
actions, expiry/MFA/service conditions, and preservation of the current worktree
evidence. They do not prove AWS policy evaluation, Marketplace enrollment, or
Claude access. No IAM policy simulator or Access Analyzer result is claimed.

- [AWS model-access prerequisites and manual agreement sequence](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html)
- [Claude Haiku 4.5 model card and product ID](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-anthropic-claude-haiku-4-5.html)
- [Bedrock service authorization reference](https://docs.aws.amazon.com/service-authorization/latest/reference/list_bedrock.html)
- [Marketplace service authorization reference](https://docs.aws.amazon.com/service-authorization/latest/reference/list_marketplace-agreement.html)
- [AWS's service-mediated Marketplace policy pattern](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/AmazonBedrockFullAccess.html)
- [Free and Paid account-plan limitations](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html)
- [Existing access runbook and budget gate](../BEDROCK_ACCESS.md)
