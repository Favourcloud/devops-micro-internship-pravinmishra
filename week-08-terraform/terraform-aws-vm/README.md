# Week 08 Assignment 2 — AWS public-network VM

**Learner:** Eze Favour · **Fork:** [Favourcloud/devops-micro-internship-pravinmishra](https://github.com/Favourcloud/devops-micro-internship-pravinmishra)

**Live AWS lifecycle completed and cleaned up — 10 of 10 genuine captures included.** On 23 September 2026, the approved lab created 11 resources, passed AWS/SSH/HTTP/browser verification, and destroyed all 11. Exact-ID checks also confirmed the root EBS volume and primary ENI were gone; Terraform state was empty. The [run summary](evidence/live-run-summary.md) and [live provenance](evidence/live-capture-provenance.json) record the results. Codex operated the live run under user delegation, not manual learner execution. No new grade or personal reflection is claimed.

## Evidence available

| Slot | Genuine original | What it establishes |
| --- | --- | --- |
| 1 | [AWS CLI version](evidence/screenshot-01-aws-cli-version.png) | Local installed CLI version, not account access |
| 2 | [AWS provider and VPC source](evidence/screenshot-02-aws-provider-vpc-source.png) | Actual `main.tf` in VS Code; AMI block folded in the editor without changing HCL |
| 3 | [EC2 and public-IP output source](evidence/screenshot-03-ec2-public-ip-source.png) | Configuration source, not a real instance or public-IP result |
| 4 | [Normal local-backend Terraform init](evidence/screenshot-04-terraform-init.png) | Successful local initialization, not an AWS plan/deployment |
| 5 | [real Terraform plan](evidence/screenshot-05-terraform-plan.png) | Real saved plan: 11 add |
| 6 | [successful Terraform apply](evidence/screenshot-06-terraform-apply.png) | Real apply: 11 added |
| 7 | [actual EC2 public IP output](evidence/screenshot-07-public-ip-output.png) | Actual temporary public IP, now retired |
| 8 | [running EC2 instance and matching public IP](evidence/screenshot-08-ec2-running.png) | Running instance, healthy checks and matching IP |
| 9 | [live Nginx page in the browser](evidence/screenshot-09-nginx-browser.png) | Actual Nginx page loaded during the run |
| 10 | [Terraform destroy and exact cleanup checks](evidence/screenshot-10-terraform-destroy.png) | 11 destroyed, 13 exact-ID cleanup checks, empty state |

The [sanitized provenance](evidence/capture-provenance.json) records capture times, original SHA-256 hashes, operator and scope. All four original PNG byte streams are unchanged. The operator was **GitHub Copilot under user delegation, not manual learner execution**. Their seven recorded source hashes describe capture head `ded8bf1b44fe0e76fb0d9a36b40d795aab46e4b4`. For the live run, only the provider lock gained the verified Linux package checksum; the other six files remain unchanged.

Screenshot 4 records actual `terraform init -input=false -lockfile=readonly`, including successful **local** backend configuration targeting `.private/terraform.tfstate`, using only the existing AWS 6.64.0 filesystem provider mirror. The capture session verified the `env -i` startup guard, empty authentication files, metadata disabled, and no managed resource state. This is different from the earlier runner's `init -backend=false`; neither is cloud execution or permission to deploy. The private receipt, raw logs, OCR, workstation tool paths and provider data are not submission artifacts.

Current delivery validation passed **46 Python tests and 25 Terraform mock runs**, plus formatting, initialization, validation and shell syntax checks; see [live validation](evidence/live-validation.json). Historical configuration validation remains **25 native mock runs and 28 Python tests** at the source head. The earlier evidence-only delivery checks remain recorded in [historical local validation](evidence/local-validation.json); its native mock tests were not re-executed at that September 17 integration. The current September 23 run also checks the Linux lock addition without cloud access. To repeat only the focused delivery tests from this project directory, without Terraform/provider execution:

```bash
python3 -B -m unittest discover -s tests -p 'test_evidence_delivery.py' -v
```

## Topology and scope

| Component | Configuration |
| --- | --- |
| VPC | `10.0.0.0/16`, DNS support and hostnames enabled |
| Public subnet | `10.0.1.0/24`; explicit route table association, IPv4 default route to IGW |
| Private subnet | `10.0.2.0/24`; explicit separate route table, local VPC route only |
| Instance | One public EC2, Canonical Ubuntu 24.04 LTS x86_64; explicit public IPv4 on this instance only |
| SSH | TCP 22 from the controller's current IPv4 `/32`; existing external Ed25519 public key imported as a Terraform-managed lab key pair |
| HTTP | Public TCP 80, required by this lab; no TLS or sensitive content |
| Egress | TCP 80/443 for Ubuntu packages; Amazon-provided VPC DNS is not filtered by security groups |
| Hardening | IMDSv2 required, metadata hop limit 1, metadata tags disabled, encrypted 8 GiB gp3 root deleted on termination, standard CPU credits |
| Bootstrap | Retried package installation, real Nginx config/service checks, named static page and local HTTP check |

Expected fresh live plan: **11 managed resources**, plus **one AMI data lookup**:
VPC (1), subnets (2), IGW (1), route tables (2), associations (2), security group (1), key pair (1), EC2 (1). The root EBS volume and primary network interface are created with EC2, not independent Terraform resources. AWS also creates the VPC's default components. No NAT gateway, Elastic IP, load balancer, RDS, IAM role or private-subnet workload is requested.

A subnet is public because of its route to the IGW, not its name. The instance additionally needs a public IP and permitted traffic. The private subnet has neither a default Internet route nor automatic public addresses; it cannot download packages via a NAT because none is present. The explicit private association avoids inheriting a later-modified main route table. All infrastructure changes, including teardown, must go through Terraform.

## Inputs and outputs

| Input | Requirement |
| --- | --- |
| `aws_region` | Required, no default; approved commercial AWS Region name. Validation checks syntax, not live service availability. |
| `ssh_cidr` | Required IPv4 `/32`; world-open, wider, IPv6, malformed, private, shared, loopback, link-local and multicast inputs are rejected. Reconfirm that it is the controller's actual routable address, not a documentation/test or other special-use address. |
| `ssh_public_key` | Required single-line OpenSSH **Ed25519 public key content**, not a file path; optionally followed by a comment. Terraform checks its shape, not cryptographic usability. Verify the existing `.pub` file and its matching private key separately. |
| `instance_type` | `t3.micro` default; `t3.small` alternative. Both x86_64. Never assume free-tier eligibility or capacity. |
| `name_prefix` | `dmi-w08-a2` default; 3–32 lowercase letters/digits/hyphens starting with a letter. Use an approved distinctive lab label. |

The [safe example](terraform.tfvars.example) deliberately has an invalid SSH placeholder. Test-only `198.51.100.0/24` addresses, zero IDs, and the zero-payload public key in the mock fixture are synthetic documentation data, never operational inputs. No private key is generated or committed. The key pair is a new AWS object with a generated suffix, so deleting it does not delete the user's local key files or a pre-existing AWS key pair.

Outputs: `public_ip`, `instance_id`, `website_url`, `ssh_username` (`ubuntu`), `ami_id`. The public IP is ephemeral and may change after stop/start or replacement. AMI discovery is pinned to Canonical's **public publisher** ID `099720109477`, not a learner account. The `most_recent` lookup may select a new image later; review and record the exact `ami_id` in every fresh plan. Provider checksum locking does not pin an AMI. Bootstrap changes intentionally replace the instance.

## Optional offline checks — no cloud permission needed

Prerequisites: installed Terraform **1.13.x** (tested with 1.13.5), Bash, Python 3, and an existing AWS **6.64.0** provider filesystem mirror for your Terraform platform. No installs are performed by these checks. `.terraform.lock.hcl` retains published package checksums; an unpacked local mirror can report `unauthenticated`, so trust must come from the existing reviewed lockfile and trusted mirror provenance. Do not bypass a checksum mismatch or silently upgrade providers.

From this directory:

```bash
export TERRAFORM_BIN=/absolute/path/to/existing/terraform
export AWS_PROVIDER_MIRROR=/absolute/path/to/existing/provider-mirror
bash scripts/check-offline.sh
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
```

The mirror root contains `registry.terraform.io/hashicorp/aws/6.64.0/<platform>/`. Reuse it read-only; do not copy the large binary. The runner creates a private `0700` `/tmp/dmi-a2.*` directory for HOME, provider data, and short macOS plugin sockets; clears inherited AWS/ARM/Terraform variables via `env -i`; disables metadata discovery/checkpoints; uses empty credential/config files; and allows only the filesystem mirror, with **no direct registry fallback**. It removes only its own temporary directory on exit.

Commands inside the runner: `fmt -check -recursive`, `init -backend=false -lockfile=readonly`, `validate`, native `test`, and `bash -n`. Every `.tftest.hcl` uses `mock_provider "aws"`. Its `command = apply` applies only an in-memory mock graph, not AWS resources. It does not run real `terraform plan`, `apply`, or `destroy`. Python tests mock subprocess responses for the cleanup helper; they never execute AWS or the bootstrap. See [local validation](evidence/local-validation.json) for actual results and limits. These checks do not prove EC2 permissions, capacity, AMI availability, cloud-init execution, Nginx availability, billing, or cleanup.

Rubric protection compares ordered requirements and source metadata, not a permanent document prefix: genuine answers, checkbox updates and future images remain possible. Do not edit protected source requirements merely to make a test pass.

## Runbook for future authorized lab runs

The September 23 approval was used for the completed, cleaned lab recorded above: one hour maximum, $1 ceiling, 11 resources in the replacement account and `us-east-1`. The instructions below remain a reusable runbook for a future run. Any new deployment needs its own account/Region, access, reviewed plan, budget and cleanup window; do not replay the retired plan. Existing CloudShell temporary credentials were sufficient for the completed run, with no new IAM identity or access keys.

Costs may include EC2 time, EBS, public IPv4 and data transfer. `standard` CPU credits avoids opting into unlimited-credit billing, but this lab is **not guaranteed free**. Do not deploy if cleanup cannot be authorized and performed within the approved window. Genuine screenshots are owned by the coordinating capture session, not synthesized by this code.

### Task 0: controlled environment and inputs

Only after fresh approval, start a clean shell from this directory. Do not inherit unrelated AWS/ARM/TF variables or existing credentials. Set up only the newly approved authentication process inside the private HOME/config below. This runbook intentionally does not automate login or identity disclosure. The coordinator must confirm the same identity privately before plan, apply, and teardown; never screenshot account IDs or credential output.

```bash
umask 077
mkdir -p .private/home .private/terraform-data
chmod 700 .private .private/home .private/terraform-data
PROJECT_DIR="$(pwd)"
env -i HOME="$PROJECT_DIR/.private/home" PATH="$PATH" TERM="${TERM:-xterm}" \
  AWS_CONFIG_FILE="$PROJECT_DIR/.private/aws-config" \
  AWS_SHARED_CREDENTIALS_FILE="$PROJECT_DIR/.private/aws-credentials" \
  AWS_EC2_METADATA_DISABLED=true CHECKPOINT_DISABLE=1 \
  bash --noprofile --norc
```

In that clean authorized shell (all subsequent live snippets use it):

```bash
set -euo pipefail
umask 077
export TF_DATA_DIR="$PWD/.private/terraform-data"
export TMPDIR="$(mktemp -d /tmp/dmi-a2-live.XXXXXX)"
export AWS_PAGER=""
export TF_IN_AUTOMATION=1
printf 'Eze Favour | Week 08 Assignment 2\n'
terraform version
aws --version
cp terraform.tfvars.example .private/lab.tfvars
```

Edit `.private/lab.tfvars` with the approved Region and controller's current public IPv4 `/32`. Do not use the mock addresses. Set `AWS_REGION` to **the exact same approved Region** for all verification commands. Set `SSH_PUBLIC_KEY_FILE` and `SSH_PRIVATE_KEY_FILE` to the existing matching files **outside the repository**, using absolute paths. Never paste their contents into screenshots or upload a `.pem` file. Restrict the private key to owner access. Inspect `ssh-keygen -lf "$SSH_PUBLIC_KEY_FILE"` locally; this is not proof the private key is available. Do not generate replacement keys in this repository.

```bash
# Set these variables to approved values before running these lines.
: "${AWS_REGION:?Set the approved Region matching .private/lab.tfvars}"
: "${SSH_PUBLIC_KEY_FILE:?Set the existing absolute .pub path outside the repository}"
: "${SSH_PRIVATE_KEY_FILE:?Set the existing matching private-key path outside the repository}"
ssh-keygen -lf "$SSH_PUBLIC_KEY_FILE"
export TF_VAR_ssh_public_key="$(cat "$SSH_PUBLIC_KEY_FILE")"
```

The sensitive flag redacts the public key from usual CLI output, not from state. Keep all state, plans, inventory, credentials, logs and known-host data under ignored `.private/` (`0700`, files `0600`). Never commit raw `terraform show -json` output. The only committed inputs are the safe example.

### Tasks 1–2: inspect configuration and initialize

Local prerequisite/source screenshots 1–3 are already included with Eze Favour visible. They show the CLI version and actual provider/VPC and EC2/public-IP output **source**, not a deployed system. Refresh them only if relevant source/tool context changes; never capture input files, credentials, account IDs or private keys. For the later newly authorized workspace, inspect the configuration and initialize as needed:

```bash
terraform fmt -check -recursive
terraform init -lockfile=readonly
terraform validate
```

This normal init establishes the local backend at `.private/terraform.tfstate`; it is separate from temporary offline `-backend=false` initialization. Screenshot 4 already records a genuine normal local-backend init with empty authentication and no managed resource state. Initialization is **not** a live deployment or account-access verification. If changing Terraform platform requires a new provider package, obtain it only through the approved installation process and verify against the lockfile.

### Task 3: plan, review, apply

```bash
terraform plan -var-file=.private/lab.tfvars -out=.private/lab.tfplan
terraform show -no-color .private/lab.tfplan
```

Review **11 to add, 0 to change, 0 to destroy** for a fresh isolated lab, exact Region/AMI/type/CIDRs/controller ingress, cost and deadline. Existing resources or another count require investigation, not blind approval. Capture screenshot 5 showing the actual plan summary, without the controller's IP or public-key detail. Stop for explicit approval of this saved plan. Plan files can contain sensitive values; never upload them. A stale plan or input/AMI change requires a new plan and review.

```bash
# Run only after approval of this exact saved plan.
terraform apply .private/lab.tfplan
terraform output public_ip
terraform output instance_id
terraform output website_url
IP="$(terraform output -raw public_ip)"
INSTANCE_ID="$(terraform output -raw instance_id)"
terraform show -json | python3 scripts/check-cleanup.py capture \
  --region "$AWS_REGION" > .private/inventory.json
chmod 600 .private/inventory.json
```

Capture screenshots 6–7. Record the **real** IP in the original assignment only after approved verification. The inventory captures all 11 managed resource IDs plus the attached root volume and primary ENI, not raw state or credentials. Keep it private and intact for exact cleanup. Successful apply does not imply cloud-init or Nginx succeeded. If apply is partial/failed, preserve its state and privately inventory the resources that actually exist; the helper deliberately rejects incomplete inventories. Stop normal evidence capture and use the authorized Terraform recovery/cleanup process—never delete state to hide a failure.

### Task 4: running state, matching IP, SSH and Nginx

All CLI reads and SSH below also require the current authorization:

```bash
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$AWS_REGION"
aws ec2 wait instance-status-ok --instance-ids "$INSTANCE_ID" --region "$AWS_REGION"
aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --region "$AWS_REGION" \
  --query 'Reservations[].Instances[].{InstanceId:InstanceId,State:State.Name,PublicIp:PublicIpAddress}' \
  --output table --no-cli-pager
AWS_IP="$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --region "$AWS_REGION" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text --no-cli-pager)"
test "$IP" = "$AWS_IP"
```

Capture screenshot 8 showing the ID, `running`, and matching IP, with Eze Favour visible. Verify the new host's SSH fingerprint using an independently trusted, authorized source (for example the EC2 console's system log); do not blindly accept it or disable host-key checking. Then:

```bash
ssh -o StrictHostKeyChecking=ask -o UserKnownHostsFile="$PWD/.private/known_hosts" \
  -i "$SSH_PRIVATE_KEY_FILE" "ubuntu@$IP" \
  'sudo cloud-init status --wait && sudo nginx -t && systemctl is-active nginx && curl --fail --silent --show-error http://127.0.0.1/'
curl --fail --silent --show-error --connect-timeout 10 --max-time 30 "http://$IP/" \
  | grep -F 'Nginx — Week 08 Assignment 2'
```

Open `http://<real-public-ip>/` in the browser and capture screenshot 9 with the address bar and Eze Favour page visible. A local mock or preview is not acceptable replacement evidence. If startup fails, inspect approved `cloud-init`/Nginx logs privately; never claim success or fix infrastructure outside Terraform. A controller IP change requires updating the `/32` input and reviewing a new Terraform plan, not opening SSH to the world.

### Task 5: destroy and exact cleanup verification

Before the deadline, reconfirm the **original account identity and Region**, same workspace/backend, and the valid saved inventory. Terraform empty state alone is insufficient. Wrong-account reads can report not-found; the helper does not validate account identity and must not be used as a substitute for the coordinator's private identity check.

```bash
terraform plan -destroy -var-file=.private/lab.tfvars
# Review destruction of this lab only; do not pass -auto-approve.
terraform destroy -var-file=.private/lab.tfvars
terraform state list > .private/remaining-state.txt
test ! -s .private/remaining-state.txt
python3 scripts/check-cleanup.py verify --inventory .private/inventory.json \
  --region "$AWS_REGION" --authorized-live-check
```

Capture screenshot 10 from genuine successful `terraform destroy` output, not the mock teardown. The helper uses only exact-ID read operations and checks all 11 resource addresses plus root EBS and primary ENI. It requires the recorded Region, accepts the EC2 `terminated` state (AWS may retain terminated records), and requires absence for the remaining objects. Only the matching AWS not-found error counts as absence: `AccessDenied`, expired credentials, wrong response shapes, transient errors and remaining resources **fail**. Retry eventual-consistency checks only within the approved window. It neither destroys resources nor grants itself authorization; the flag records an operator decision, not a technical permission grant.

If any check fails, preserve private state/inventory and escalate to the coordinator for authorized Terraform cleanup. Do not declare zero resources/cost, delete state, change IAM, or manually remove AWS resources. Check the billing view later through an approved process because billing can lag; absence checks are not a zero-bill guarantee. After verified cleanup, unset `TF_VAR_ssh_public_key` and authentication variables, close the authorized shell, and remove only its unique temporary socket directory. Retain private state/backups according to the approved retention policy; they are not submission artifacts.

## Evidence and handoff

The [manifest](evidence/manifest.json) maps exactly ten numbered slots to the original rubric. Each capture must be genuine, readable, current, and show Eze Favour/name or username. Screen only the necessary output; exclude credentials, account IDs, private keys and controller identity details. Authorized instance public-IP evidence is required by the assignment; no real IP is fabricated here.

All ten slots are linked in the assignment and manifest. The first four originals and their September 16–17 provenance are preserved. Slots 5–10 record the approved September 23 live run and teardown, with separate provenance documenting the crops and JPEG-to-PNG conversion. The actual public-IP field and runtime checks now reflect genuine verification. Every original heading, task, question and checklist item is preserved. Week 08 remains in progress because the other assignments and publications have outstanding requirements; see the [completion audit](../completion-audit.md).

## Official references

- [Terraform AWS provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS VPC resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc)
- [AWS subnet resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/subnet)
- [AWS route table resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route_table)
- [AWS EC2 instance resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/instance)
- [AWS key pair resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/key_pair)
- [Canonical Ubuntu AMI discovery](https://documentation.ubuntu.com/aws/aws-how-to/instances/find-ubuntu-images/)
- [Terraform mock-provider tests](https://developer.hashicorp.com/terraform/language/tests/mocking)

External references are documentation pointers, not claims of live URL or AWS verification during offline preparation.
