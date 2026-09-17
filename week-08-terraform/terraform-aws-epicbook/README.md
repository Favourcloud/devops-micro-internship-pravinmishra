# Week 08 Assignment 4 — EpicBook on modular AWS infrastructure

**Learner:** Eze Favour · **Repository:** Favourcloud/devops-micro-internship-pravinmishra

**OFFLINE PREPARATION ONLY. No AWS resources, live URL, screenshots or LinkedIn post were created.**

[Original assignment, preserved](../assignment-04-deploy-epicbook-application-on-aws-using-terraform.md) ·
[35 pending screenshot slots](evidence/screenshot-manifest.json) · [Local validation record](evidence/local-validation.md)

## Deliverables and interfaces

```text
terraform-aws-epicbook/
├── main.tf / variables.tf / outputs.tf
├── terraform.tfvars.example           # safe template; real terraform.tfvars is private/ignored
├── .terraform.lock.hcl                # AWS 6.64.0; Terraform 1.13.x
├── modules/
│   ├── network/{main,variables,outputs}.tf
│   ├── ec2/{main,variables,outputs}.tf + user_data.sh + runtime.py
│   └── rds/{main,variables,outputs}.tf
├── scripts/                          # offline runner, schema/preflight/cleanup checks
├── tests/                            # native AWS mocks, stdlib/stub tests, original brief
└── evidence/                         # pending manifest; sanitized local check record only
```

There are **12 Terraform source files, 25 resource blocks expanding to 28 managed resource instances**, plus one Ubuntu AMI data lookup. The exact future real plan remains unapproved/unexecuted.

| Module | Proposed resources | Count |
|---|---|---:|
| Network | VPC, 3 subnets, IGW, 2 route tables, 1 internet route, 3 associations, 2 SGs, 3 ingress and 3 egress rules | 19 |
| RDS | DB subnet group, MySQL 8.4 parameter group, single-AZ MySQL instance | 3 |
| EC2 | Ubuntu instance, scoped runtime role, inline policy, instance profile | 4 |
| Root | Secrets Manager secret and write-only secret version | 2 |

Network exports `vpc_id`, `public_subnet_id`, `private_subnet_ids`, `ec2_security_group_id`, `rds_security_group_id`.
Root passes the subnet/SG outputs into EC2/RDS. RDS exports `address` for bootstrap and `endpoint` for the rubric.
EC2 exports `instance_id` and `public_ip`. Root outputs only instance ID, public IP, application URL and RDS endpoint, never passwords, secret ARNs or account identity.

Topology: public HTTP → Nginx:80 → Express:8080 → private RDS:3306. VPC `10.0.0.0/16`, public subnet `10.0.1.0/24`, database subnets `10.0.2.0/24` and `10.0.3.0/24` across two AZs. Only the public route table has `0.0.0.0/0 → IGW`. Both DB subnets explicitly associate with a local-only route table. EC2 alone opts into a public IP. SSH permits only the explicit controller public IPv4 `/32`; 8080 is not exposed by its SG. MySQL ingress references only EC2's SG. EC2 egress is limited to HTTP/HTTPS package/API access and RDS MySQL; Amazon-provided VPC DNS does not need a separate SG rule.

No NAT, load balancer, EIP, replica, Multi-AZ DB, custom KMS key, IAM user/access keys, or broad managed policy is proposed. The 3 IAM and 2 Secrets Manager resources support credential-safe bootstrap, not general administration. The parameter group enforces database TLS. IAM itself has no separate resource charge; Secrets Manager storage/API requests, EC2, 12-GiB gp3 EBS, public IPv4, 20-GiB gp3 RDS, traffic and applicable taxes are billable. There is **no free-tier promise**. EC2 standard CPU credits avoid unlimited-mode surplus charges; small capacity may need a reviewed increase. Obtain current regional rates and a maximum runtime/spend limit before provisioning.

## Credential and runtime design

- `db_username` and `db_password` are sensitive variables in root and RDS. The password is additionally **ephemeral**. AWS 6.64.0's installed schema was locally checked for `password_wo` and `secret_string_wo` with `write_only=true`. Both receive the same supplied password; the secret JSON also carries the username. Shared `credential_version` drives both write-only updates. Merely marking a variable sensitive would **not** remove it from state.
- The username is not ephemeral: the RDS username argument is not write-only and remains in private Terraform state. Resource IDs, secret references and user data also remain in state. Treat state/plans as confidential despite password exclusion. Do not enable `TF_LOG`, shell tracing, SDK debug logs or raw plan/state publication.
- User data includes only nonsecret RDS host, Region, secret reference and rotation counter, plus code. EC2's Terraform-managed role can only `secretsmanager:GetSecretValue` for this one secret. It cannot write secrets, administer RDS, or retrieve other secrets. Default AWS-managed Secrets Manager encryption avoids a new customer key.
- A root-only Python helper retrieves credentials with the instance role through boto3, creates a mode-0600 temporary MySQL option file under `/run`, and removes it even on failure. Both `prepare` and `verify` quote option values and escape backslashes, double quotes and supported control characters using [MySQL option-file syntax](https://docs.oracle.com/cd/E17952_01/mysql-8.4-en/option-files.html); an allowed `#` password character remains literal, not an inline comment. This does not broaden the validated password alphabet. Passwords never appear in argv, user data or error output. MySQL CLI verifies the RDS CA and hostname with `VERIFY_IDENTITY`; the parameter group requires secure transport.
- RDS creates `bookstore`. The helper imports upstream schema → authors → books only into an empty database. It validates populated Author/Book tables; a partial import stops instead of blindly appending or claiming success. No compatibility migration is needed for `Cart.quantity`: the Sequelize model supplies `defaultValue: 1`.
- A separate random `epicbookapp` password is generated on the instance, not in Terraform. This application username is reserved case-insensitively: root and RDS-module inputs reject it as the master username, and runtime secret validation rejects it before any SQL or credential-file creation in either `prepare` or `verify`. The login requires TLS and has SELECT/INSERT/UPDATE/DELETE/CREATE/ALTER/INDEX/REFERENCES only on `bookstore.*`, sufficient for Sequelize's normal sync. No global grant or master credentials go into app config. It does not have DROP, GRANT OPTION or user-administration rights.
- Runtime production JSON is root:epicbook mode 0640 in `/run/epicbook` (directory 0750); upstream `config/config.json` becomes a symlink to it. No upstream JavaScript is edited. Systemd rebuilds the secret-derived config on boot before starting the app, disables app access to EC2 metadata using `IPAddressDeny`, and runs the app as an unprivileged user with read-only source and restrictive systemd settings. Verify that this systemd/eBPF restriction actually works on the authorized host.
- Root credential/config setup has bounded retries and a systemd deadline. The app has bounded restart bursts. Raw app stdout/stderr are suppressed because upstream Sequelize exceptions could expose connection details; controlled SQL diagnostics are provided instead. Temporarily enabling diagnostic logs requires a private, non-recorded session and careful removal/redaction, never screenshotting raw errors.
- On rotation, increment the counter and supply the new password to plan **and** apply. RDS updates immediately before the secret version; EC2 is replaced because user data changes. This deliberately incurs downtime in a disposable single-instance lab. Out-of-band rotation or changing a value without bumping its counter is unsupported.
- This is not a production storefront: HTTP is public, upstream is old and unauthenticated, and lab backups/final snapshots are disabled only with explicit `accept_lab_data_loss=true`. Secrets are force-deleted on destroy. Use synthetic catalogue/cart data only; never payment details or real personal data. Fresh IAM review/permission is required before applying even this narrow role; prior EC2 permission failure is not resolved by the source.

## Verified upstream contract and remaining compatibility gate

Pinned repository: [pravinmishraaws/theepicbook at 763bece](https://github.com/pravinmishraaws/theepicbook/tree/763becebb8d3f5663a76bb30facddc25be63cfd5).
A bounded public lookup found current instructor `main` still at this exact commit, with no releases or tags. This is not a vendored app: source and dependencies are fetched **only during future authorized EC2 bootstrap**.

| Source checked at the pin | Contract / consequence |
|---|---|
| `package.json`, lockfile v3 | Express 4.17.1, Sequelize 6.3.0, mysql2 2.1.0, express-handlebars 5.0.0, Handlebars 4.7.6; npm start is node server.js |
| `server.js`, `models/index.js` | Default PORT 8080; Sequelize sync before listen; production config uses direct JSON fields so TLS options are retained (not the upstream JAWSDB_URL branch) |
| `db/BuyTheBook_Schema.sql`, author/book seeds | `bookstore`, case-sensitive Author/Book/Cart table names; author import must precede books |
| `models/cart.js`, `models/book.js`, `models/checkout.js` | Quantity default 1; `Cartbook` join table; Checkout table model exists |
| `routes/cart-api-routes.js`, `routes/html-routes.js` | POST `/api/cart` creates Cart and adds Book; catalogue GET `/` queries DB; there is **no checkout/order creation endpoint** |
| `public/assets/js/book.js` | Checkout click only issues DELETE `/api/cart/delete`; the server deletes carts and does not send a response. It does **not** create a Checkout record |

The [pinned instructor guide](https://github.com/pravinmishraaws/theepicbook/blob/763becebb8d3f5663a76bb30facddc25be63cfd5/Installation%20%26%20Configuration%20Guide.md) uses obsolete Node 17/MySQL 5.7 and local database commands. This runbook instead targets Ubuntu 24.04 LTS, **Node 22.22.0** (supported 22 LTS line) and **RDS MySQL 8.4 LTS**. Node's Linux x64 tarball is fixed to its published SHA-256 in user data. `npm ci --omit=dev --ignore-scripts --no-audit --no-fund` honors the upstream lock without arbitrary lifecycle scripts. Engine ranges in the inspected packages allow Node 22; that is a source check, **not verified Node 22/MySQL 8.4 runtime compatibility or a vulnerability audit**. Recheck patch/security support, regional MySQL minor availability and exact class orderability at the future gate. No automatic dependency upgrades are claimed.

**Rubric distinction:** screenshots 32–33 allow a cart action and its real Cart/Cartbook records, so that narrower evidence is feasible subject to genuine runtime tests. The separate "checkout or order workflow" checklist remains **pending/blocking**. Do not fabricate an order, manually insert one as browser evidence, call cart deletion a completed checkout, or check the whole assignment complete. A verified instructor fix or explicitly authorized separate upstream work is needed; this repository's no-JavaScript-authoring constraint remains intact.

## Offline validation — safe to run now

Use an already installed Terraform 1.13.5 executable and the already installed AWS 6.64.0 mirror; do not copy/download the large provider. Set these to your existing absolute tool/mirror paths (do not publish personal paths):

```bash
export TERRAFORM_BIN=/absolute/path/to/existing/terraform
export AWS_PROVIDER_MIRROR=/absolute/path/to/existing/provider-mirror-root
bash scripts/check-offline.sh
```

The runner uses a short private `/tmp/dmi-a4-*` socket directory, empty HOME, cleared environment, disabled EC2 metadata/checkpoints, null AWS credential/config files, filesystem-only provider installation without registry fallback and read-only lock initialization. Provider files may be linked read-only from the supplied mirror; no adjacent state/plans/approvals are consulted. Terraform calls are only version, fmt, backend-disabled init, validate, schema and native **mock** tests. `command=plan/apply` inside `.tftest.hcl` applies solely to `mock_provider "aws"`, not to a real cloud plan/apply.

Preflight refuses tfvars, state, override files, initialized `.terraform`, `.private` and symlinks inside the source tree, including broken private symlinks. Do not delete existing live evidence to make the check pass; use a new clean authorized checkout. Scratch cleanup runs on success/failure. A missing tool/provider or any failed check stops execution. The mirror init message "unauthenticated" means this filesystem install did not obtain a fresh registry signature; the committed lock checksums originate from the existing pinned provider lock, not a newly fetched trust assertion.

Mock tests cover topology, private routing/SGs, module wiring, write-only unreadability, sensitive/ephemeral declarations, user-data references/size, storage/IMDS settings and input rejection. Standard-library/stub tests cover SQL ordering, bounded retry/failure, temporary credential cleanup, file permissions, scoped grants, readiness failures/default Nginx rejection, runner isolation, original brief/manifest integrity and exact-ID cleanup-ledger rejection. They **do not execute the real app or prove actual systemd, MySQL, IAM or AWS behavior**.

## Future authorized runbook — STOP until fresh approval

Everything below is an **unexecuted procedure**, not authority to run it. The coordinating parent owns consent, real identity/price review, serialized captures and cleanup. Earlier permission/budget authorizations are retired. No authentication, STS, AWS API, SSH, plan/apply/destroy, provider registration, billing/IAM change or GUI capture is permitted under the offline task.

### Gate 0 — identity, permission, price and ownership

Obtain explicit approval for Region, controller IPv4, two AZs, existing SSH key ownership, exact AMI/class/engine availability, 28-resource scope including IAM/Secrets Manager, maximum spend/runtime, public HTTP risk, no-backup data loss, secret destruction, and the operator/cleanup deadline. Prior identity lacked EC2 permission: an authorized account administrator must review the minimal resource permissions and scoped `iam:PassRole`; do not escalate yourself or substitute administrator policies. Confirm Terraform/AWS CLI/VS Code extension separately for screenshots 1–3; none are currently captured. Generate no new key under this offline task. If no suitable existing key is available, stop for explicit approval of separate key management.

Only after approval, in a private terminal (never record account IDs):

```bash
umask 077
test ! -L .private && mkdir -p -m 700 .private && chmod 700 .private
aws sts get-caller-identity > .private/identity-before.json
aws configure get region
# Operator compares exact account/principal/Region to the fresh approved values.
```

Create `.private` with mode 0700 **before** the redirect, outside any screenshot session. Resolve SDK/provider credentials using the approved method; do not put keys in tfvars or this repository. Check Region AZs, the Canonical Ubuntu 24.04 AMI and MySQL 8.4 class orderability with read-only AWS queries only after this gate. Read-only checks do not authorize changes.

### Tasks 1–6 — private inputs, init, plan review and apply

```bash
umask 077
test ! -L .private && mkdir -p -m 700 .private && chmod 700 .private
cp -i terraform.tfvars.example terraform.tfvars
chmod 600 terraform.tfvars
# Edit nonsecret values: real controller /32, confirmed Region/AZs and existing key name.
# Set accept_lab_data_loss=true only after explicit approval; template false intentionally fails.
set +x
read -r -s -p 'RDS username (private): ' TF_VAR_db_username; printf '\n'
export TF_VAR_db_username
read -r -s -p 'Unique RDS password (private): ' TF_VAR_db_password; printf '\n'
export TF_VAR_db_password
terraform init -lockfile=readonly
terraform fmt -check -recursive
terraform validate
terraform plan -out=.private/create.tfplan
```

Use a private process environment; never `-var=db_password=...`, an inline environment assignment containing a password, shell history, clipboard screenshots, `terraform show -json` on screen, or `terraform output -json` in public evidence. Preserve secret input in the approved password manager, not a file in the worktree. An ephemeral password must be supplied again for saved-plan apply; the runner must keep the **same password and counter** for the approved plan/apply pair.

Stop after plan. Have the human review changes and current price estimate. The plan should propose exactly the 28 managed resources above, approved image/class/Region, no unexpected replacement/deletion, no NAT/LB/Multi-AZ, no public RDS, no SSH `/0`, no broad IAM, no secret in user data. If it differs, stop and revise the source/approval, not the account manually. Capture sanitized screenshots 4–20 in assignment order with Eze Favour visibly identified and all sensitive identifiers redacted.

Only after separate approval of this exact plan:

```bash
terraform apply .private/create.tfplan
terraform output ec2_public_ip
terraform output rds_endpoint
terraform state list > .private/resource-addresses.txt
terraform show -json > .private/state-before-destroy.json
unset TF_VAR_db_password TF_VAR_db_username
```

Private state export is for inventory only; never commit/share it. Create a private ledger with the exact addresses/IDs of all 28 managed resources plus root EBS volume ID, key name (pre-existing, not owned), account/Region, RDS identifier and secret/IAM identifiers. See cleanup below. State/plan files stay private throughout. Screenshots 21–22 must be genuine results, never native mock output.

### Task 7 — live EC2, RDS and host software

Use actual IDs recorded privately, not guessed IDs or tag-only broad queries:

```bash
aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --query 'Reservations[].Instances[].{State:State.Name,PublicIP:PublicIpAddress}'
aws rds describe-db-instances --db-instance-identifier "$DB_ID" --query 'DBInstances[].{Status:DBInstanceStatus,Public:PubliclyAccessible,Engine:Engine,Version:EngineVersion}'
ssh -i /private/path/to/approved-key.pem ubuntu@"$PUBLIC_IP"
# On EC2; do not cat user data, runtime metadata/config, or credential files:
sudo timeout 1800 cloud-init status --wait
node --version; npm --version; git --version; mysql --version; nginx -v
sudo nginx -t
sudo systemctl is-active nginx epicbook-config epicbook
sudo ss -ltnp '( sport = :8080 )'
curl --fail --max-time 10 http://127.0.0.1/ | grep 'Add to Cart'
```

Bootstrapping fetches only the pinned app revision, installs locked dependencies, runs the root config service, then starts app/Nginx. The default Nginx site is removed. Readiness requires active EpicBook and a DB-backed catalogue containing `Add to Cart`, not merely HTTP 200. Confirm `git -C /opt/epicbook rev-parse HEAD` equals the pin. If cloud-init/config/app fail, stop: do not call Nginx's default page success or automatically relax IAM/TLS/SG rules.

### Tasks 8–9 — database initialization and application configuration

RDS Terraform creates `bookstore`. The root helper has already imported the exact three upstream SQL files in order; it must complete before the app starts. Verify without typing a password in argv:

```bash
sudo python3 /usr/local/lib/epicbook/runtime.py verify
# Lists actual tables, Author/Book counts, latest Cart/Cartbook/Checkout rows and TLS cipher.
test -d /opt/epicbook/node_modules && printf 'node_modules exists\n'
cd /opt/epicbook && npm ls --omit=dev --depth=0
sudo nginx -t
sudo systemctl is-active nginx epicbook
sudo ss -ltnp '( sport = :8080 )'
```

The helper's temporary defaults file uses `--defaults-extra-file` as MySQL's first option and is removed afterward. It prints no credentials, host metadata or raw errors. Do not dump config.json to prove connection. Nginx's config can be viewed from `/etc/nginx/sites-available/epicbook`; it contains no database secrets. A read-only config permission check (`sudo stat /run/epicbook/config.json`) is safer than content display. Screenshots 25–30 must show the actual host/software/TLS/tables/dependencies/services. If an import is partial, the helper fails closed; get explicit approval for recovery or Terraform-managed destroy/recreate of this disposable DB. Never truncate/seed over an unexplained partial result, manually alter AWS, or treat the stdlib SQL stubs as import proof.

### Task 10 — actual browser → app → database evidence

Record the actual public IP URL in the brief only after it works. In a real browser, open the public HTTP URL, view a seeded product and click **Add to Cart once** using synthetic lab data. Save genuine screenshot 31 of the catalogue and 32 of the cart action/UI (not CLI mocks). Record the returned POST `/api/cart` JSON ID/book ID and UTC time privately, without exposing personal browser data. The upstream asynchronous `cart.addBook` is not awaited, so allow bounded eventual checking of its join record; persistent missing records are a failure, not permission to manufacture a row.

Run `runtime.py verify` on EC2 immediately afterward; screenshot 33 must show the matching Cart ID, quantity, price/time and `Cartbook` BookId, tied to the same browser action. For unambiguous larger datasets use an approved read-only MySQL session via a protected defaults file, not a password-bearing command. Compare the actual returned ID/time/product to the matching database row; do not accept an unrelated pre-existing row or only a table count. Do this **before** pressing the upstream Checkout button, which deletes carts.

The separate checkout/order requirement remains unresolved by the pinned upstream source. Verify and disclose the actual behavior; no Checkout insertion route exists. Do not tick that checklist item or claim a matching order record. Seek a verified instructor fix or separate explicit scope approval; preserve all assignment requirements meanwhile.

### Task 11 — destroy, exact-ID verification and cost closeout

Schedule cleanup even when runtime tests fail. Reconfirm the same approved account and Region in a private terminal before any destruction. Re-supply the same ephemeral credentials if Terraform asks; never save them in a plan/tfvars. Use only this A4 state, never neighboring coursework state.

```bash
aws sts get-caller-identity > .private/identity-cleanup.json
# Human compares with identity-before and approves the exact destruction plan.
terraform plan -destroy -out=.private/destroy.tfplan
terraform apply .private/destroy.tfplan
terraform state list > .private/remaining-state-addresses.txt
unset TF_VAR_db_password TF_VAR_db_username
```

This is Terraform destroy via a reviewed saved destruction plan. Capture actual successful destruction as screenshot 34; do not call a mock teardown cloud cleanup. Alternatively, after reviewing the destruction plan, the authorized operator may use interactive `terraform destroy` to satisfy the exact command display, reviewing its fresh plan again before confirming. No `-auto-approve`, targeted partial teardown, manual resource deletion or account-wide cleanup.

**Empty state alone is not deletion evidence.** Re-query the captured exact IDs with approved read-only CLI calls; expected NotFound or EC2 terminated is acceptable, but AccessDenied, invalid identity, timeouts, missing CLI and empty unvalidated responses are not. Check all 28 addresses, plus provider-created children/root volume and leftovers:

| Owned resource family | Exact-ID verification after destroy |
|---|---|
| EC2 | `aws ec2 describe-instances --instance-ids "$INSTANCE_ID"`; require terminated/not-found |
| Root EBS (not a separate Terraform resource) | `aws ec2 describe-volumes --volume-ids "$ROOT_VOLUME_ID"`; require expected absence |
| RDS | `aws rds describe-db-instances --db-instance-identifier "$DB_ID"`; require DBInstanceNotFound; use captured DB ID to check `describe-db-snapshots` and `describe-db-instance-automated-backups` for retained backups |
| DB subnet/parameter group | `aws rds describe-db-subnet-groups --db-subnet-group-name "$DB_SUBNET_GROUP"`; `describe-db-parameter-groups --db-parameter-group-name "$DB_PARAMETER_GROUP"` |
| Secret/version | `aws secretsmanager describe-secret --secret-id "$SECRET_ARN"`; expected ResourceNotFound after asynchronous force deletion also covers its version; never retrieve contents for cleanup |
| IAM role, inline policy, profile | `aws iam get-role --role-name "$ROLE"`; `get-role-policy --role-name "$ROLE" --policy-name read-only-this-lab-secret`; `get-instance-profile --instance-profile-name "$PROFILE"`; require NoSuchEntity, not permission failure |
| 3 subnets, 2 SGs, 6 rules, IGW, VPC | `aws ec2 describe-subnets --subnet-ids ...`, `describe-security-groups --group-ids ...`, `describe-security-group-rules --security-group-rule-ids ...`, `describe-internet-gateways --internet-gateway-ids ...`, `describe-vpcs --vpc-ids ...`; supply the exact recorded IDs |
| 2 route tables, 3 associations, internet route | `aws ec2 describe-route-tables --route-table-ids ...`; verify table absence and recorded association/destination identities, not absence of a tag |

Retain command/timestamp/terminal-status provenance privately per recorded address and exact resource ID, including compound IDs for Terraform routes, rules and secret version. Failed or unknown checks block completion; IAM/Secrets Manager consistency may require bounded retries (for example 12 attempts 10 seconds apart) then escalation to the authorized operator, **not** broader permissions or manual deletes. The existing key pair is not lab-owned and must remain untouched.

Optional private ledger consistency check (not an AWS API/deletion proof):

```bash
python3 scripts/check-cleanup.py .private/inventory.json .private/observations.json
```

Inventory shape: `{ "account": "<private approved account>", "region": "<approved region>", "resources": [{"address":"<exact Terraform address>","id":"<exact captured ID>"}] }` with 28 unique rows. Observations repeats account/Region and all rows, adding `status` (`absent`, or `terminated` for EC2 only), `checked_at` and exact read-only `check` command per row, plus `remaining_state_addresses: []`, `attached_ebs_absent: true`, `db_snapshots_absent: true`. Populate only from genuine captured results, never to make the helper pass. Reconcile IAM/secret parent-child compound IDs explicitly. The helper cannot authenticate observations or independently establish resource absence. After deletion, the authorized operator checks delayed billing/cost reporting, confirms no unexpected snapshot/EBS/IP charges remain, then handles private state/credential/evidence retention under the agreed policy. Never delete shared tools/old evidence to save space.

### Task 12 — mandatory learner publication and final submission

All **35** original screenshot slots remain pending. After authorized execution, capture each original requested view in order and label Eze Favour in the required views. Source/config screenshots must still be genuine screenshots, not generated images. Review every image for account IDs, usernames, passwords, key paths, secret ARNs, tokens, private endpoints/metadata and unrelated browser content before publication. Keep raw captures private; publish only human-reviewed sanitized copies with honest annotations. Do not alter command outcomes or fabricate resources.

The learner writes their own reflection based on what actually happened; no automatic autobiographical reflection or grade claim is supplied. Mandatory LinkedIn post must include genuine permitted deployment proof and be reviewer-accessible. The learner reviews and explicitly authorizes publication, posts manually, then supplies the real URL and screenshot 35. Never post automatically, substitute a draft URL or mark the requirement optional. Update the brief/manifest only with actual evidence, preserving originals and separately explaining unresolved checkout behavior. Offline source/tests alone are not a completed Week 08 submission.
