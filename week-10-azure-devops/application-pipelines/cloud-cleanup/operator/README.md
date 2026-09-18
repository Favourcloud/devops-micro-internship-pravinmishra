# Non-root AWS operator — source and owner handoff

**Offline preparation, not a created user or successful sign-in.** For this bounded single-account lab, use a dedicated MFA-protected IAM user with temporary AWS CLI browser-login credentials. Do not introduce AWS Organizations just to enable SSO. An existing organization-backed Identity Center role remains preferable when already available; an Identity Center account instance does not provide AWS-account access.

The saved Azure DevOps PAT is unrelated and need not be replaced. The existing `GetFederationToken` broker cannot call IAM APIs, regardless of its policy or renewal. Do not broaden that broker, inspect its credentials, run root Terraform, or give root/operator credentials to a hosted runner.

## Exact source scope

[Terraform](aws/main.tf) defines only an IAM user, two customer-managed policies, one optional policy attachment, and a built-in authorization guard. No password/login profile, access key, MFA seed/device, VM, organization, console session or service connection is created. `live_execution_approved`, `bootstrap_access_enabled` and `mfa_enrolled_and_verified` default to **false**. A boundary alone grants no permissions; the identity-policy attachment remains absent until separately enabled after MFA verification.

For one fresh 12-character lowercase hex lease:

| Object | Exact name/purpose |
| --- | --- |
| IAM user | `dmi-w10-bootstrap-<lease>`; no groups, keys or unrelated policy attachments |
| Operator managed policy | `dmi-w10-bootstrap-<lease>`; both the user's permissions boundary and, after verification, its identity policy |
| Runtime boundary managed policy | `dmi-w10-cleanup-boundary-<lease>`; cannot be edited by the operator |
| Later cleanup role, **not created here** | `dmi-w10-cleanup-<lease>`; the [AWS bootstrap](../bootstrap/aws/main.tf) must now receive `runtime_permissions_boundary_arn` |

The operator policy allows metadata reads and management of only the exact cleanup role and approved Entra issuer. Every delegated role-policy/trust/boundary write requires the administrator-owned runtime boundary. The operator cannot remove/edit either boundary, attach arbitrary managed policies, create users/keys, pass or assume roles, or call EC2. **It is an IAM bootstrap identity, not yet a canary-creation or A2 workload operator.** Those additional permissions require a separate reviewed scope; do not discover the gap by attempting a live apply.

The runtime boundary limits even an overly broad role inline policy to regional EC2 metadata, lease-tagged empty-VPC deletion and caller identity. It deliberately has no expiry deny: cleanup retries must remain possible after the creation window ends. The human operator policy, in contrast, explicitly denies operations before `approved_at` and at/after `expires_at`, with no automatic renewal. `GetCallerIdentity` can still identify a principal despite denies; that response never proves permissions.

The operator requires MFA request context; a missing or false `aws:MultiFactorAuthPresent` fails closed. Browser-login MFA-context propagation and actual IAM authorization **have not been tested**. If a real authenticated read is denied, stop and inspect the exact context with the administrator; do not remove the MFA deny, create access keys, or fall back to root. Native mocks cannot establish AWS's effective permissions, SCPs or service behavior.

## Owner checklist before any account change

1. Review the exact account, lease, intended tenant issuer, policies and one fixed lifecycle of **at most 24 hours**, including identity/control-plane teardown and the unchanged combined US$10 planning allowance. No new clock has started in this source delivery. Do not reset the window when logging in, renewing credentials or advancing to A2. Arrange an independently reachable account owner/administrator and a recovery copy of the non-secret object IDs and reviewed source.
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
4. Choose the already-approved administrative route below. Do not supply secret fields or credentials to Terraform. Its inputs are `account_id`, `lease_id`, exact `administrator_arn`, approved `oidc_issuer`, the [approval object](aws/approval.tf), and explicit execution approval. Keep access disabled for initial user setup.
5. The account owner and learner handle console password creation/final password, mandatory-reset requirements, and MFA enrollment **privately in AWS** before permission activation. No password, authorization code, QR code, MFA seed or recovery material belongs in a plan/state file, helper input, screenshot, chat, shared terminal or Git commit. There is no self-service password/MFA-management grant in this policy; the administrator must finish enrollment first. Never disable account password policy or MFA to bypass this gate.

### Route A: an existing authorized non-root administrator

Use the Terraform root with exact verified administrator identity and reviewed state custody. The default local backend is not an independent backup. Protect and escrow state outside the disposable control plane before applying. Review a saved plan: two policies, one user and the authorization guard, **zero permission attachments** initially. Apply only that exact authorized plan. After private console/MFA setup and verification, review a second plan enabling only `bootstrap_access_enabled` with `mfa_enrolled_and_verified = true`, within the unchanged window.

This root rejects root, the federation broker, a different account/operator and self-administration. It cannot manufacture its own administrator. It does not automatically invoke Terraform or obtain credentials.

### Route B: only the account owner has root access

The separately approved one-time account-owner bootstrap is **human-operated**, not root API automation or root Terraform. Limit the exception to the three named IAM objects, their exact reviewed policies/boundary/attachment, and private console/MFA setup and retirement. No EC2, Organizations, unrelated IAM changes or blanket administrator policy is included.

In the owner's private AWS console, create the runtime-boundary policy and operator policy from the reviewed document. Create the exact user with the operator policy as its permissions boundary, **without groups, access keys or an identity-policy attachment**. Complete private console/MFA setup. Only then attach that same operator policy as the identity policy. Do not attach `AdministratorAccess`, `IAMFullAccess`, or an unreviewed replacement policy. Sign out of root before the operator login below. The agent must not drive, capture or read this owner session.

Record this route honestly as an owner-created identity; it is **not Terraform-managed yet**. Do not apply the creation root against it. A separately authorized non-root administrator may later adopt it using exact resource imports and a reviewed no-change plan. The operator itself cannot change/adopt its own administration root. If no such administrator exists, retain owner responsibility for the exact identity's retirement; never expand the operator to make self-administration work. All subsequent cloud workload/control-plane resources remain Terraform-managed.

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

Select only the approved `dmi-w10-bootstrap-<lease>` IAM identity, **never root or another account/role**. Check both account ID and full IAM user ARN against the reviewed document before any Terraform command. The pure `verify_identity` helper can validate allowlisted caller-identity metadata; it explicitly does **not** establish MFA or permissions. A wrong selection requires immediate `w10_aws logout --profile signin` and a fresh correct sign-in, not trying a plan with those credentials.

The pinned provider's direct support for login-session credentials is unverified. AWS documents a `credential_process` bridge for older SDKs. If needed, add a separate `process` profile **only in this isolated config**, using the approved CLI's absolute quoted path:

```ini
[profile process]
region = eu-west-2
credential_process = "/absolute/path/to/approved/aws" configure export-credentials --profile signin --format process
```

Only the SDK may consume that command's credential JSON through its private subprocess pipe; **never run it standalone or print its output**. An eventual separately authorized Terraform invocation must inherit the same isolated config/cache, a cleared credential environment and `AWS_PROFILE=process`; no fallback to HOME, metadata, static keys or the root broker. Actual provider login, an MFA-authenticated metadata read and exact effective permissions remain acceptance gates. Do not use shell tracing, AWS `--debug`, `TF_LOG` or full-environment output.

## Retirement and remaining deployment gates

- Keep an independent administrator/owner available. The operator cannot extend its window, edit its own policy, remove its boundary or retire its user. Expiry denies use but **does not delete IAM objects or prove revocation of every cached session**.
- First retire the owned cleanup role/provider through their reviewed Terraform and verify absence. No other entity may depend on the runtime boundary. Then disable the operator attachment, revoke private console/login access and retire its MFA association through the owner. With credentials/devices handled separately, Route A's administrator destroys only the reviewed identity root. `force_destroy = false` intentionally refuses to sweep unexpected credentials. For Route B, the owner removes only the recorded attachment/user and two policies in the private console, after checking dependencies. Never delete shared objects or force detach unexpected consumers.
- Log out using `w10_aws logout --profile signin`; this clears the local cache but is not server-side revocation. Remove only this invocation's private login directory after any agreed recovery-record retention. Do not delete other sessions, state, credentials or HOME configuration. The owner verifies user/policy absence and records the actual result without secret material.
- Independent cloud control-plane state custody/teardown, actual WIF/AWS exchange, hosted capacity, real canary creation/deletion, and later workload-cleanup permissions still precede A2 VMs. This identity does **not** implement those missing controls or complete an assignment. Screenshots and learner reflections remain pending.

## Validation and public references

Use the [existing credential-free tests and native sandbox runner](../README.md#credential-free-offline-validation). The runner now covers this plan-only root as well as the four existing roots, using the existing AWS/Azure providers, with external network denial and private scratch cleanup. Structural tests are not an IAM simulator; mocked plans are not a live permission/MFA test.

- [AWS CLI browser login, remote-client ARN, cache isolation and credential-process bridge](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html).
- [SignInLocalDevelopmentAccess](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/SignInLocalDevelopmentAccess.html): the source uses its two documented actions, narrowed to this account, region and remote client, rather than attaching the broader AWS-managed policy.
- [IAM permissions-boundary delegation](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html) and [public IAM action metadata](https://servicereference.us-east-1.amazonaws.com/v1/iam/iam.json). The `iam:PermissionsBoundary` condition was verified for every delegated role write; policies themselves were not sent to a service.
- [MFA condition semantics and enrollment caveats](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_examples_aws_my-sec-creds-self-manage.html). Its broad credential-management example is **not** copied into this policy.
- [GetFederationToken restrictions](https://docs.aws.amazon.com/STS/latest/APIReference/API_GetFederationToken.html) and [Identity Center instance differences](https://docs.aws.amazon.com/singlesignon/latest/userguide/identity-center-instances.html).
