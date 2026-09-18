# Non-root AWS operator — source and owner handoff

## Verified initial creation — 18 September 2026

At **23:03:19 UTC**, the explicitly approved creation-only Terraform operation was verified against frozen source `91787063e1e36bcdd08ab3d1811c50b9c7f73d62`: persistent user **`dmi-week10-operator`**, its operator policy/boundary, and the canary runtime boundary were created. Both live policy documents matched the reviewed templates. Private state and exact recovery metadata were retained; an independent backup is **not** claimed.

The user had **zero attached/inline policies, groups, access keys and MFA devices**, and no console password. At that checkpoint, it was **not yet a usable login**. Private password/MFA enrollment and independent verification must precede any policy attachment. The original privilege deadline remains **19 September 2026, 18:18:03 UTC**; retention does not renew it. No role, issuer, VM or hosted cleanup service was created, and the existing Week08 user was unchanged. These are initial API/state verification results, not ongoing monitoring, browser authentication, assignment completion or screenshot evidence.

## Verified activation — 18 September 2026

At **23:36:43 UTC**, the reviewed policy attachment was applied with Terraform and independently verified against AWS and the existing protected state. The user had **one enrolled MFA device, one attached operator policy, zero access keys, zero inline policies and zero groups**. The console password was configured with no mandatory reset outstanding. Both live policy documents and the permissions boundary still matched frozen source `91787063e1e36bcdd08ab3d1811c50b9c7f73d62`.

The first attachment plan stopped on one unexpected user tag. After explicit owner approval, a separate saved plan removed only that extra setup tag and attached the unchanged policy; the three managed tags were preserved. The rejected plan was not applied. The successful plan SHA-256 was `5d49b1e4b7b4be2ff9f5cda248541fe4170f9aaaf32f6e08ed6cb37a0261147b`. Targeted private-controller tests passed offline with network and filesystem writes denied; these were gate tests, not sign-in evidence.

The original privilege deadline remains **19 September 2026, 18:18:03 UTC**. The root administration window was not extended. No role, issuer, VM or hosted cleanup service was created. **Actual non-root browser/CLI sign-in, MFA request context and Terraform-provider acceptance remain unverified**; attachment alone does not establish effective access. AWS CLI 2.26.1 was rechecked locally and is still below the documented 2.32.0 login prerequisite. This is not assignment completion or screenshot evidence.

The existing state and its backup were verified owner-only (`0600`) within a private directory. Historical creation inputs remain unchanged and describe the inactive phase; a separate private activation override and recovery record describe the active attachment. Preserve all of them. Do not rerun the creation plan or apply its inactive inputs alone. An independent external backup is still **not** claimed. Any later IAM maintenance needs a currently valid, explicitly authorized administration window; it must not renew privileges automatically.

## Source contract

**Persistent identity, expiring permissions.** This source and its tests do not prove live creation or successful sign-in. For this bounded single-account lab, use one dedicated MFA-protected IAM user with temporary AWS CLI browser-login credentials. Retaining the identity and protective policies requires explicit approval; it never renews privileges or extends lab-resource deadlines. Do not introduce AWS Organizations just to enable SSO. An existing organization-backed Identity Center role remains preferable when already available; an Identity Center account instance does not provide AWS-account access.

The saved Azure DevOps PAT is unrelated and need not be replaced. The existing `GetFederationToken` broker cannot call IAM APIs, regardless of its policy or renewal. Do not broaden that broker, inspect its credentials, or give root/operator credentials to a hosted runner. Root is rejected by default; the separately authorized, short-lived exception below applies **only to this IAM identity root**, never to workload or cleanup-control-plane roots.

## Exact source scope

[Terraform](aws/main.tf) defines only an IAM user, two customer-managed policies, one optional policy attachment, and a built-in authorization guard. No password/login profile, access key, MFA seed/device, VM, organization, console session or service connection is created. `live_execution_approved`, `persistent_identity_approved`, `bootstrap_access_enabled` and `mfa_enrolled_and_verified` default to **false**. A boundary alone grants no permissions; the identity-policy attachment remains absent until separately enabled after MFA verification.

The human username is stable; the fresh 12-character lowercase hex lease scopes only the current cleanup permissions and runtime boundary:

| Object | Exact name/purpose |
| --- | --- |
| IAM user | `dmi-week10-operator`; persistent, with no groups, keys or unrelated policy attachments |
| Operator managed policy | `dmi-week10-operator`; persistent, both the user's permissions boundary and, after verification, its identity policy |
| Runtime boundary managed policy | `dmi-w10-cleanup-boundary-<lease>`; cannot be edited by the operator |
| Later cleanup role, **not created here** | `dmi-w10-cleanup-<lease>`; the [AWS bootstrap](../bootstrap/aws/main.tf) must now receive `runtime_permissions_boundary_arn` |

The operator policy allows metadata reads and management of only the exact cleanup role and approved Entra issuer. Every delegated role-policy/trust/boundary write requires the administrator-owned runtime boundary. The operator cannot remove/edit either boundary, attach arbitrary managed policies, create users/keys, pass or assume roles, or call EC2. **It is an IAM bootstrap identity, not yet a canary-creation or A2 workload operator.** Those additional permissions require a separate reviewed scope; do not discover the gap by attempting a live apply.

The runtime boundary limits even an overly broad role inline policy to regional EC2 metadata, lease-tagged empty-VPC deletion and caller identity. It deliberately has no expiry deny: cleanup retries must remain possible after the creation window ends. The human operator policy, in contrast, explicitly denies operations before `approved_at` and at/after `expires_at`, with no automatic renewal. `GetCallerIdentity` can still identify a principal despite denies; that response never proves permissions.

The operator requires MFA request context; a missing or false `aws:MultiFactorAuthPresent` fails closed. Browser-login MFA-context propagation and actual IAM authorization **have not been tested**. If a real authenticated read is denied, stop and inspect the exact context with the administrator; do not remove the MFA deny, create access keys, or fall back to root. Native mocks cannot establish AWS's effective permissions, SCPs or service behavior.

## Owner checklist before any account change

1. Review the exact account, lease, intended tenant issuer, policies and one fixed **privileged-access window of at most 24 hours**, with the unchanged combined US$10 planning allowance. Explicitly approve retention of the IAM user and two protective policies separately from permission expiry. The existing lab/control-plane deadlines and independent teardown requirements are unchanged. Neither persistent identity, login, credential renewal nor advancing to A2 starts a new clock. Keep account-owner recovery access and an owner-accessible record of exact IAM object IDs and frozen source; see recovery below.
2. Verify the user/policy/role names and the account-wide OIDC provider are absent. **An existing/shared issuer is a stop**, not an import, retag or replacement opportunity. The scoped tagging permission needed for creation is not proof of ownership and could retag that exact existing issuer. Other administrators must not create/use that issuer or namespace during this lease; the checks are not atomic with outside writers. No issuer-client-list or thumbprint-update permission is granted.
3. Render and inspect a review document using only five non-secret fields. The example below has deliberately fictitious IDs and an **expired** window. It is safe source output, not usable authorization or evidence:

   ```sh
   /usr/bin/env -i PATH=/usr/bin:/bin HOME=/nonexistent \
     /usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)(deny file-write*)(allow file-write-data (literal "/dev/null"))' \
     /usr/bin/python3 -I -B \
     week-10-azure-devops/application-pipelines/cloud-cleanup/operator/review.py \
     week-10-azure-devops/application-pipelines/cloud-cleanup/operator/review.example.json
   ```

   For real review, keep the metadata copy in an invocation-owned ignored `.private/` directory, not alongside the example. Supply only `account_id`, `lease_id`, `oidc_issuer`, `approved_at`, `expires_at`. The helper renders the **same templates Terraform uses**, enforces a maximum 24-hour window and the managed-policy size limit, and performs no authentication or writes. It does not authorize an apply or verify live ownership/MFA. Freeze the final reviewed policies and window before account changes.
4. Choose the already-approved administrative route below. Do not supply secret fields or credentials to Terraform. Its inputs are `account_id`, `lease_id`, exact `administrator_arn`, approved `oidc_issuer`, the [privileged-access approval object](aws/approval.tf), and explicit execution and persistent-identity approval. Keep access disabled for initial user setup. A later maintenance window is separate from permission expiry and must not be substituted into the policy's `approval` object.
5. The account owner and learner handle console password creation/final password, mandatory-reset requirements, and MFA enrollment **privately in AWS** before permission activation. No password, authorization code, QR code, MFA seed or recovery material belongs in a plan/state file, helper input, screenshot, chat, shared terminal or Git commit. There is no self-service password/MFA-management grant in this policy; the administrator must finish enrollment first. Never disable account password policy or MFA to bypass this gate.

### Route A: an existing authorized non-root administrator

Use the Terraform root with exact verified administrator identity and reviewed recovery arrangements below. The default local backend is not an independent backup. Protect IAM state locally and retain the exact import IDs and frozen source; an owner-held copy outside this Mac is recommended and must not be claimed unless verified. Review a saved plan: two policies, one user and the authorization guard, **zero permission attachments** initially. Apply only that exact authorized plan. After private console/MFA setup and verification, review a second plan enabling only `bootstrap_access_enabled` with `mfa_enrolled_and_verified = true`, within the unchanged window.

Without a separate root exception, this root rejects root, the federation broker, a different account/operator and self-administration. It cannot manufacture its own administrator. It does not automatically invoke Terraform or obtain credentials.

### Route B: explicitly authorized root IAM bootstrap

An account owner may explicitly authorize a one-time **Terraform-managed IAM bootstrap** when no usable non-root administrator is available. Console sign-in alone is not that authorization, nor proof of the CLI caller. Do not create policies/users manually in the browser or remove the normal identity guards. An existing Week08 user is not permission to repurpose it.

Supply `root_bootstrap_approval = { approved_at = "...Z", expires_at = "...Z" }` with a fresh fixed administration window of **at most one hour**, and the exact account root ARN as `administrator_arn`. Both planning and saved-plan application require a current exception and exact caller/account match. The exception is null by default and cannot authorize a federation-broker session. Administration may occur after privilege expiry so the persistent identity can be maintained without renewing access: keep the policy's original `approval` timestamps unchanged and `bootstrap_access_enabled = false`. Expired/future privileges cannot be activated, even with verified MFA and fresh root approval. This is a Terraform execution guard, **not an IAM restriction or revocation of root credentials**, and never a sandbox for arbitrary root commands.

Freeze and review this root, both policy templates, lockfile and explicit inputs before using the approved local credential mechanism. Do not expose secret values to Terraform variables, command arguments, plan output, logs or the browser. Do not modify the existing STS broker. An initial saved plan must contain exactly the authorization guard, two named policies and one new bounded user, all creates, with **zero policy attachments, groups, passwords, keys, MFA devices or other resources**. Stop on an existing namespace, shared issuer, import, update, replacement or deletion. Protect state and record the exact recovery metadata and frozen source before applying; see recovery below. Local state alone is not independent custody.

IAM-only setup creates no billed compute, storage or hosted runner, so its estimate may truthfully be zero. This does not increase the combined US$10 allowance, approve paid services, or satisfy the later control-plane budget/state/teardown gates. The approved IAM identity/policies persist, but bootstrap privileges still expire at the original fixed deadline. Persistent console credentials may still authenticate; that does not grant AWS API access or extend CLI browser-login authorization after policy expiry.

Private console-password and MFA setup remain with the account owner/learner. The initial identity is **not a usable login or an authorized operator** merely because it exists. Only after independent MFA verification may a second reviewed Terraform plan attach the same bounded policy, using `bootstrap_access_enabled = true` and `mfa_enrolled_and_verified = true`. Root cannot bypass that gate. A later root operation needs fresh explicit authorization if its one-hour exception has expired, without changing the original privilege expiry. Never attach `AdministratorAccess`, `IAMFullAccess`, or an unreviewed replacement policy. Sign out of root before operator login. Do not drive, capture or read password/MFA pages.

## Private browser sign-in — human only, not executed by tests

Local offline observation for this delivery: AWS CLI **2.26.1** is installed. AWS documents **2.32.0 or newer** for `aws login`. **Stop until an approved CLI upgrade or an already compliant operator machine is available.** No installer/package was downloaded or run. Do not overwrite a shared installation or inspect existing HOME profiles/caches.

Run the following only in your private local terminal, not an agent tool/shared canvas/logged pipeline. Replace the CLI placeholder with the approved executable's absolute path. The isolated directory contains sensitive login caches; keep it private and never read/paste its files. The authorization URL/code remains between the browser and this terminal, never chat.

```sh
set +x
umask 077
AWS_CLI='/absolute/path/to/approved/aws'
private_root="$PWD/week-10-azure-devops/application-pipelines/cloud-cleanup/operator/aws/.private"
mkdir -p "$private_root"
login_dir="$(mktemp -d "$private_root/login.XXXXXXXX")"
w10_aws() {
  /usr/bin/env -i PATH=/usr/bin:/bin HOME="$login_dir" \
    AWS_CONFIG_FILE="$login_dir/config" AWS_SHARED_CREDENTIALS_FILE=/dev/null \
    AWS_LOGIN_CACHE_DIRECTORY="$login_dir/cache" AWS_EC2_METADATA_DISABLED=true \
    AWS_REGION=eu-west-2 AWS_DEFAULT_REGION=eu-west-2 AWS_PAGER='' \
    "$AWS_CLI" "$@"
}
w10_aws --version
# STOP if the version is older than 2.32.0; do not continue to login.
w10_aws login --profile signin --region eu-west-2 --remote
w10_aws sts get-caller-identity --profile signin --region eu-west-2
```

Select only the approved `dmi-week10-operator` IAM identity, **never root or another account/role**. Check both account ID and full IAM user ARN against the reviewed document before any Terraform command. The pure `verify_identity` helper can validate allowlisted caller-identity metadata; it explicitly does **not** establish MFA or permissions. A wrong selection requires immediate `w10_aws logout --profile signin` and a fresh correct sign-in, not trying a plan with those credentials.

The pinned provider's direct support for login-session credentials is unverified. AWS documents a `credential_process` bridge for older SDKs. If needed, add a separate `process` profile **only in this isolated config**, using the approved CLI's absolute quoted path:

```ini
[profile process]
region = eu-west-2
credential_process = "/absolute/path/to/approved/aws" configure export-credentials --profile signin --format process
```

Only the SDK may consume that command's credential JSON through its private subprocess pipe; **never run it standalone or print its output**. An eventual separately authorized Terraform invocation must inherit the same isolated config/cache, a cleared credential environment and `AWS_PROFILE=process`; no fallback to HOME, metadata, static keys or the root broker. Actual provider login, an MFA-authenticated metadata read and exact effective permissions remain acceptance gates. Do not use shell tracing, AWS `--debug`, `TF_LOG` or full-environment output.

## Persistent identity, recovery and retirement

- Keep account-owner recovery access. The operator cannot extend its window, edit its own policy, remove its boundary or retire its user. Expiry denies use but **does not delete IAM objects or prove revocation of every cached session**. The IAM user and two policies have `prevent_destroy = true`; this is a Terraform guard, not protection against console/API deletion. Retaining them is not retaining administrator access.
- Retire any separately owned cleanup role/provider and lab resources through their reviewed Terraform by their original deadlines. The runtime boundary is retained but grants nothing on its own. Changing a lease can replace that named boundary; the destruction guard intentionally blocks blind rotation. Never detach unexpected consumers or reuse a shared namespace.
- Disable the operator attachment through a reviewed Terraform plan when bootstrap work finishes. For non-root maintenance after the original grant expires, supply a separate `administration_approval` window of at most one hour. Root instead needs a fresh `root_bootstrap_approval`; never supply both. Keep `bootstrap_access_enabled = false` and the original privilege timestamps. Maintenance approval must not renew the policy. MFA and a current privilege window are both required for activation; granting a later window needs separate explicit authorization.
- Preserve private state, exact inputs and the frozen source revision. This root stores IAM metadata, **not passwords, keys or MFA material**. For initial inactive creation, recovery IDs are `dmi-week10-operator` for `aws_iam_user.operator`, `arn:aws:iam::<account>:policy/dmi-week10-operator` for `aws_iam_policy.operator`, and `arn:aws:iam::<account>:policy/dmi-w10-cleanup-boundary-<lease>` for `aws_iam_policy.runtime_boundary`. An independently authorized account owner can import those exact objects into protected replacement state using the frozen configuration and a fresh maintenance window, then review a plan with zero AWS changes; the local authorization guard may be recreated. Check actual attachments first: if activation occurred, stop for a reviewed attachment/state-recovery plan rather than treating the identity as inactive. Never reset an expired privilege timestamp just to make recovery pass. An owner-held recovery copy outside this Mac is recommended; a local file is not proof of independent backup. This IAM-only recovery route does **not** satisfy cloud control-plane state/teardown gates.
- Permanent identity retirement requires separate explicit owner authorization, dependency review and a reviewed source change removing only the relevant destruction guards. Handle console credentials/MFA privately, then use a deletion-only Terraform plan. `force_destroy = false` refuses to sweep unexpected credentials. Creation preconditions are not destroy authorization: independently verify the caller and exact deletion scope. No automatic identity deletion or credential retirement is claimed.
- Log out using `w10_aws logout --profile signin`; this clears the local cache but is not server-side revocation. Remove only this invocation's private login directory after agreed recovery-record retention. Do not delete other sessions, state, credentials or HOME configuration.
- Independent cloud control-plane state custody/teardown, actual WIF/AWS exchange, hosted capacity, real canary creation/deletion, and later workload-cleanup permissions still precede A2 VMs. This identity does **not** implement those missing controls or complete an assignment. Screenshots and learner reflections remain pending.

## Validation and public references

Use the [existing credential-free tests and native sandbox runner](../README.md#credential-free-offline-validation). The runner now covers this plan-only root as well as the four existing roots, using the existing AWS/Azure providers, with external network denial and private scratch cleanup. A built-in-only regression also saves an unexpired root plan, waits for its synthetic approval to expire, and verifies that applying it fails without creating even the local guard resource. No AWS provider or credentials are used for that regression. Structural tests are not an IAM simulator; mocked plans are not a live permission/MFA test.

- [IAM service cost information](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html): IAM/STS identities are offered at no additional charge; other services and paid Access Analyzer features are not covered by a zero identity-only estimate.
- [AWS CLI browser login, remote-client ARN, cache isolation and credential-process bridge](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html).
- [SignInLocalDevelopmentAccess](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/SignInLocalDevelopmentAccess.html): the source uses its two documented actions, narrowed to this account, region and remote client, rather than attaching the broader AWS-managed policy.
- [IAM permissions-boundary delegation](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html) and [public IAM action metadata](https://servicereference.us-east-1.amazonaws.com/v1/iam/iam.json). The `iam:PermissionsBoundary` condition was verified for every delegated role write; policies themselves were not sent to a service.
- [MFA condition semantics and enrollment caveats](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_examples_aws_my-sec-creds-self-manage.html). Its broad credential-management example is **not** copied into this policy.
- [GetFederationToken restrictions](https://docs.aws.amazon.com/STS/latest/APIReference/API_GetFederationToken.html) and [Identity Center instance differences](https://docs.aws.amazon.com/singlesignon/latest/userguide/identity-center-instances.html).
