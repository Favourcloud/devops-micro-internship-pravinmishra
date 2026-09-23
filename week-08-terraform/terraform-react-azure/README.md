# Week 08 Assignment 3 — Azure React deployment and evidence

**Learner:** Eze Favour

**Repository:** [Favourcloud/devops-micro-internship-pravinmishra](https://github.com/Favourcloud/devops-micro-internship-pravinmishra)

**Status:** live deployment, runtime verification and teardown completed; **15/15 screenshots** captured. The [live run summary](evidence/live-run-summary.md) records the approved 24 September 2026 local-date run (23 September UTC), and [live provenance](evidence/live-provenance.json) preserves its timings, original image hashes and cleanup results.

The [original assignment](../assignment-03-deploy-a-react-application-on-azure-virtual-machine-using-terraform.md) retains every rubric heading, requirement and checklist item. The [manifest](evidence/manifest.json) records current completion separately from the unchanged historical local evidence and validation below. Codex performed the live work under user delegation. Public IP `4.225.168.0` is **retired after verified cleanup**. The instructor application's name/date placeholders remain unchanged; learner identity appears in the authentic Terminal alongside the browser. No new DMI grade is claimed.

## Genuine local evidence — slots 1–8

These eight original PNGs were captured in a genuine isolated VS Code window on **2026-09-17 UTC**, labelled **Eze Favour — Week 08 Assignment 3**, and operated by **GitHub Copilot under user delegation, not manually by the learner**. They are unaltered window captures, not mock output, reconstructed screenshots or composites. The [sanitized provenance](evidence/provenance.json) records each original SHA-256, capture time, operator and local-only scope without private workstation paths, process/window IDs, account IDs or raw logs. The parent reviewed capture privacy; integration verifies the original bytes and PNG metadata guards.

| Slot | Original capture | What it establishes |
|---|---|---|
| 1 | [Terraform version](evidence/screenshots/screenshot-01-terraform-version.png) | Installed local Terraform 1.13.5, darwin_amd64. |
| 2 | [Azure CLI version](evidence/screenshots/screenshot-02-azure-cli-version.png) | Installed local Azure CLI 2.89.1; no login or Azure API action. |
| 3 | [Terraform extension](evidence/screenshots/screenshot-03-vscode-terraform-extension.png) | Installed HashiCorp Terraform extension in VS Code. |
| 4 | [Provider, RG and NSG source](evidence/screenshots/screenshot-04-provider-resource-group-nsg-source.png) | Native split view of unchanged provider/RG/SSH/HTTP source, not deployed resources. |
| 5 | [VM and custom data source](evidence/screenshots/screenshot-05-linux-vm-custom-data-source.png) | Unchanged Linux VM and `custom_data` configuration, not VM creation. |
| 6 | [Completed cloud-init source](evidence/screenshots/screenshot-06-completed-cloud-init-source.png) | Native split view of build/Nginx excerpts and the complete main workflow, not the whole file or execution. |
| 7 | [Public IP output source](evidence/screenshots/screenshot-07-public-ip-output-source.png) | Output block only, not an allocated address or live output. |
| 8 | [Normal local initialization](evidence/screenshots/screenshot-08-terraform-init.png) | Actual successful `terraform init -input=false -lockfile=readonly` with a local backend. |

Slot 8 is **normal local-backend initialization**, distinct from the earlier backend-disabled validation: Terraform 1.13.5 and AzureRM 4.47.0 were reused through a filesystem-only mirror in an `env -i` environment with empty Azure configuration and a passed startup guard. The configured backend target is `.private/terraform.tfstate`; the capture receipt confirms **no managed-resource state**. No provider download, Azure authentication, live plan/apply/destroy or cloud API action occurred. Tools already installed on the workstation were verified, not claimed as newly installed for the capture.

Captured source is frozen at **`3a0eea8f2dc9c62d28e511155065e6e145a3555b`**. All eight receipt-listed HCL/lock/bootstrap/example/runner/mock file hashes remain unchanged. Slot 6 does not display the entire script; the complete [tracked cloud-init.sh](cloud-init.sh) is the source deliverable. Its visible literal `/tmp/dmi-react.XXXXXXXX` is a public script template, not a private capture path. Existing ignored 0700 private capture directories and 0600 capture files are retained; their contents are not published or required to be absent.

## Files and architecture

- [main.tf](main.tf): provider, private local backend, eight resources and outputs.
- [variables.tf](variables.tf): explicit location/SKU/controller/key inputs and validation.
- [cloud-init.sh](cloud-init.sh): pinned, unprivileged application build and Nginx setup.
- [terraform.tfvars.example](terraform.tfvars.example): deliberately invalid replacement placeholders, not usable live inputs.
- [tests](tests): native AzureRM mocks, offline runner, stubbed bootstrap tests, ordered rubric/privacy guards.

Expected **8 managed resources**: resource group, VNet, subnet, NSG, Standard static IPv4 public IP, NIC, NIC/NSG association and Linux VM. NSG rules are inline, not extra Terraform resources. The managed 32 GiB Standard LRS OS disk is created with the VM; it incurs cost even though it is not a separate Terraform resource address. Azure platform-managed storage encryption applies by default, and the provider explicitly deletes the OS disk with the VM. No customer-managed key vault, host-encryption feature registration, separate storage account, NAT gateway, database, Bastion, load balancer, monitoring workspace or optional paid service is added.

The NIC's NSG permits controller IPv4 `/32` → TCP 22 and public → TCP 80. Priority 200 denies all remaining inbound traffic, including Azure's default VNet/load-balancer allows. VM creation depends on NSG association. Normal outbound access is needed for signed Ubuntu packages, the pinned Node release, GitHub and npm. HTTP is intentionally unencrypted for this temporary rubric exercise: no credentials or sensitive content belong on the site. The Standard public IP gives the VM explicit outbound connectivity; no assumption of default outbound access is needed.

## Input interface

| Variable | Default | Constraint / responsibility |
|---|---|---|
| `project_name` | `dmi-w08-a3` | Unique disposable prefix, 3–30 lowercase characters; do not reuse an existing RG. |
| `location` | **none** | Approved Azure region code; syntax alone does not prove availability. |
| `vm_size` | **none** | Approved `Standard_` x86-64 SKU; check RAM, regional capacity, quota and price. Prefer at least 2 vCPU / 4 GiB for CRA, subject to approval. ARM SKUs are not supported by this bootstrap. |
| `controller_ipv4_cidr` | **none** | Actual current public controller IPv4 `/32`, never `*` or `/0`. Private/loopback/link-local/shared/multicast addresses are rejected. TEST-NET ranges exist only in mocks. |
| `admin_username` | `dmiuser` | Non-reserved Linux login; cannot collide with the separate build user. |
| `admin_ssh_public_key` | **none** | Existing **Ed25519 public key**, a single OpenSSH line without newline; optional single-token comment. Other algorithms intentionally fail. |

Only key authentication is configured; no password is required by A3. Terraform validates the Ed25519 wire header and 32-byte length, and AzureRM validates the key object. The public test vector comes from RFC 8032 §7.1 test 1: it is public-only and must **never** be used for a real VM. Supply a personally controlled matching public key, keep its private counterpart outside the repository, and do not generate or commit a private key here. The public-key variable is sensitive to reduce accidental identity disclosure, but it still appears in private state.

Outputs: `public_ip_address`, `resource_group_name`, `vm_name`. An IP output or successful Terraform apply says nothing about application readiness; cloud-init is asynchronous.

## Pinned dependency provenance

Reviewed public upstream at commit [`f1b1aff14fe15c5bde092067c93a307fa3d97982`](https://github.com/pravinmishraaws/my-react-app/tree/f1b1aff14fe15c5bde092067c93a307fa3d97982):

- [README](https://github.com/pravinmishraaws/my-react-app/blob/f1b1aff14fe15c5bde092067c93a307fa3d97982/README.md) describes Nginx, npm and the `build/` directory.
- [package.json](https://github.com/pravinmishraaws/my-react-app/blob/f1b1aff14fe15c5bde092067c93a307fa3d97982/package.json) uses React/React DOM 19.0.0 and `react-scripts` 5.0.1 (`node >=14`). `npm run build` runs `react-scripts build`.
- [package-lock.json](https://github.com/pravinmishraaws/my-react-app/blob/f1b1aff14fe15c5bde092067c93a307fa3d97982/package-lock.json) is lockfile v3, with webpack 5.98.0, TypeScript 4.9.5 and 1,344 package records including the root. All resolved package URLs use the public npm registry. SHA-256: `287a9d37c611438b6c4ed0979fbf45128bda5dc3ff5175683c74941ba0440257`.
- Node **22.23.2 LTS**, bundled npm **10.9.8**, is supported at preparation time. See the [official release schedule](https://nodejs.org/en/about/previous-releases) before a future deployment; do not blindly use Node 17, the workstation's unsupported Node 23, or Ubuntu's older default Node package.
- The VM's official `node-v22.23.2-linux-x64.tar.xz` SHA-256 is `d60acfe00a2932254bb0ad20e01b0d74397a0875595de719654b214f4b03f307`. The separate local-build `darwin-x64` archive SHA-256 is `96dff79f4e19a78715da559ec7cac2028f4985a175ea0c3454625a269c21deb7`. Both pins were read from the release's [official HTTPS checksums](https://nodejs.org/dist/v22.23.2/SHASUMS256.txt). Checksums are verified before extraction. This is pinned HTTPS/checksum provenance, **not** a claim that a release signature was independently verified.

The instructor README requests changing `src/App.js` for name/date. This submission deliberately does **not** do so: the repository's no-JavaScript-change constraint takes precedence. Upstream was fetched unchanged into the temporary VM (and an isolated temporary local validation directory); no application JS is copied into this Git submission. The live browser evidence shows Eze Favour in an authentic Terminal alongside Chrome; the actual address bar is visible. The page's existing instructor/template text is not represented as personalized learner content. Do not edit pixels or invent a browser screenshot to resolve this limitation.

### Bootstrap behavior

Ubuntu **24.04 LTS x86-64** (`Canonical:ubuntu-24_04-lts:server:latest`) is configured. The image version tracks Ubuntu's patched image stream, not an immutable OS image; record the actually resolved version privately at an authorized run. Node and application pins are immutable, while signed Ubuntu packages follow the image's trusted apt repositories. Reassess support and dependency risks before future use.

The script exits on errors, uses three bounded retries for package/download/fetch/install steps, apt lock/network timeouts and GNU `timeout` deadlines. It installs only required packages through Ubuntu's signed package channel and downloads Node directly from the pinned release—no mutable `curl | bash` installer. Git commit and lockfile digest are verified before dependency installation. `npm ci --ignore-scripts --no-audit --no-fund` and the explicit production build run as a separate unprivileged `dmi-react-build` user with an empty environment and isolated Git/npm configuration. No dependency upgrades, global npm installs, JavaScript patches, legacy OpenSSL flags or lockfile rewrites are used.

Nginx serves only `build/`, uses SPA fallback for routes and real 404s for missing static assets. Sources, dependencies and configuration are outside the web root. A readiness marker at `/var/lib/dmi-react/deployment-ready` is written atomically **only after** successful build/output/source-integrity checks, `nginx -t`, service activation and active status, byte-for-byte localhost index/SPA response checks and a JavaScript asset response check. Old markers are removed at startup/error. This proves local checks inside that VM, not external browser reachability. Custom data contains no credentials; nevertheless Azure/cloud-init and Terraform retain copies, so never add secrets. Failure logs are private troubleshooting material, not publishable evidence.

## Offline validation (safe now)

Prerequisites: existing Python 3, Bash, Terraform **1.13.5** and a trusted read-only filesystem mirror containing **AzureRM 4.47.0** for this host. The checked-in Terraform lock originated from the reviewed A1 source commit `dbdab95b21f517cfe0751d07e667001c0fb6a775`; its package hashes are checked by init against the already installed mirror. No provider download, neighboring state/configuration, credentials or earlier approval is reused. Provider hashes do not imply a newly verified signature.

From this directory, supply your explicitly approved existing binary/mirror paths privately:

```bash
python3 tests/run_offline.py --terraform "$TERRAFORM_BIN" --plugin-dir "$AZURERM_MIRROR"
```

The runner refuses live/auto-loaded tfvars, extra Terraform/override/test files and symlinked private/source directories **before** spawning validation. It creates a fresh 0700 `.private/offline-*` environment and provider data directory, uses a filesystem-only provider install configuration, drops inherited credentials/CLI overrides, and cleans its own temporary files. Short `/tmp/dmi-a3-*` directories hold provider Unix sockets to avoid macOS path limits; they are also cleaned. No neighboring cache is written. The exact validation sequence is:

1. Python delivery/runner guards and stubbed shell tests.
2. `bash -n cloud-init.sh`.
3. Terraform 1.13.5 version check.
4. `terraform fmt -check -diff main.tf variables.tf tests/app.tftest.hcl tests/inputs.tftest.hcl`.
5. `terraform init -backend=false -input=false -lockfile=readonly -no-color -plugin-dir=...`.
6. `terraform validate -no-color`.
7. `terraform test -filter=tests/app.tftest.hcl -filter=tests/inputs.tftest.hcl -no-color`.

All Terraform test runs use `mock_provider "azurerm"`. The test DSL's `command = plan/apply` is an in-memory mock operation, **not** a real plan/apply. Failures stop later steps and propagate a nonzero status. No raw logs, state or input files are published. Ordered rubric tests permit answers/evidence to be added while protecting the original instructions; evidence guards verify the eight supplied originals and keep the seven cloud slots pending.

### Verified local application build, separate from deployment

An isolated **macOS x86-64** build using the checksum-verified Node 22.23.2/npm 10.9.8 archive genuinely ran `npm ci --ignore-scripts --no-audit --no-fund --fetch-timeout=60000 --fetch-retries=2` and `npm run build` at the pinned commit. npm installed 1,343 packages; CRA reported **Compiled successfully** and produced `build/index.html`, JS and CSS assets. Tracked upstream files remained unchanged. Installation plus compilation took approximately 37 seconds. Temporary Node, dependencies/cache, source and outputs were cleaned; no global packages were installed.

The build emitted legacy-dependency deprecation and stale Browserslist database warnings. Those were not concealed or fixed by mutating the locked instructor app. npm audit was not run; build success is not a vulnerability assessment. This actual local compilation does **not** verify Ubuntu package installation, Linux runtime, cloud-init, Nginx, Azure capacity, public HTTP, SSH, browser behavior or cloud cleanup. Stubbed shell tests establish orchestration/error-path behavior only. At source commit `3a0eea8f2dc9c62d28e511155065e6e145a3555b`, the offline suite passed **35 native Terraform mock runs and 46 Python tests**, plus shell syntax, formatting, backend-disabled initialization and Terraform validation. The 46 Python tests included 21 stubbed bootstrap tests (with additional stage/guard subcases), 10 runner tests and 15 delivery/rubric/privacy tests. These are historical source-validation results, not a rerun during evidence integration. The build and mocks do not fill screenshot slots; the eight supplied originals are separate evidence.

### Focused evidence integration checks

From this directory, run only the delivery and capture checks without Terraform, cloud commands, bootstrap execution or package installation:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_[de]*.py'
```

**Historical local evidence integration result: 25 focused Python tests passed** — 15 delivery checks and 10 capture/provenance checks, with per-image/file subcases. These checks cover the ordered original rubric and all 15 titles, eight original PNG hashes/structure and relative links, sanitized metadata, UTC times and operator attribution, frozen source hashes, local initialization limits, pending cloud evidence and retained ignored private artifacts. The command was run with an empty inherited environment and bytecode writes disabled. Historical 46-Python/35-mock/build results are kept separate; the mock suite and application build were not rerun for this evidence-only update.

The current live evidence update passed **28 focused Python checks** (15 delivery and 13 capture/provenance tests), recorded separately in [live-validation.json](evidence/live-validation.json). All 15 PNGs, eight frozen source files, original provenance and historical manifest sections were verified; the new Markdown links resolve. Historical validation records above are unchanged.

## Runbook for future deployments

The following commands are for future deployments, not additional execution evidence. The completed run above used its own explicit approval. A new lab needs a fresh reviewed plan, current identity/permission checks, a budget and a cleanup deadline; the completed one-hour window does not carry forward. **Stop at any unavailable budget, identity, permission, capacity or approval gate.**

### 1. Obtain fresh permission, identity and cost approval

Record privately the approving person, timestamp, exact tenant/subscription, approved region, x86-64 SKU, maximum spend/currency, maximum duration and cleanup deadline. Price the VM runtime, managed OS disk, Standard public IPv4, bandwidth and any taxes. Stopped/deallocated VMs can still incur disk/IP costs; budgets are alerts, not hard spend caps. There is **no free-tier or no-cost promise**. Keep enough approved budget and permission to inspect/delete partial failed deployments.

Only after explicit authorization, use an approved Azure CLI installation and `az login` if necessary. Privately confirm the signed-in identity and correct subscription (`az account show`), selecting only the authorized subscription. Keep tenant/account/subscription IDs and tokens out of screenshots, logs, shell history and Git. Check effective resource-group/Compute/Network create/read/delete permissions; subscription-level RG creation is required for this topology. Terraform sets `resource_provider_registrations = "none"`: verify required providers are already registered; missing registration or permission is a stop condition, not permission to register providers, expand IAM, increase quota or change billing.

Check regional VM/image/SKU availability, x86-64 support, quota, capacity and current pricing, and ensure a unique new RG name. Confirm that the caller can delete the VM's OS disk and every network resource. Do not reuse a shared RG or import another assignment's resources. Confirm the actual public controller IPv4 using an approved method; changes require a reviewed Terraform input/plan change, never broadening SSH manually. Select an existing personally controlled public key, not the known mock key.

### 2. Prepare private inputs and initialize

Use a fresh reviewed shell: no inherited `TF_CLI_ARGS*`, `TF_VAR_*`, backend overrides, auto-loaded tfvars or unrelated Terraform files. Confirm the repository's reviewed revision. Keep all live data ignored with restrictive permissions:

```bash
set -euo pipefail
umask 077
test ! -L .private
mkdir -p .private
chmod 700 .private
export TF_DATA_DIR="$PWD/.private/live-data"
cp terraform.tfvars.example .private/run.tfvars
chmod 600 .private/run.tfvars
```

Privately edit the example replacements with approved inputs (including the public key line only). Never paste private keys or credentials. Avoid printing this file. Authenticate using the authorized Azure CLI context or separately approved secret mechanism; subscription selection must be explicit and private. Set `ARM_SUBSCRIPTION_ID` privately if required by AzureRM 4.x, without publishing its value. Validate public key ownership and format with your existing SSH tooling, not key generation in this project.

```bash
terraform init -input=false -lockfile=readonly
terraform validate
terraform plan -input=false -var-file=.private/run.tfvars -out=.private/reviewed.tfplan
```

Review the private plan and permitted identity/region/SKU/cost again before applying. A pristine deployment should show **8 to add, 0 to change, 0 to destroy**. Explain any difference before continuing. Inspect NSG source/destination/priority, VM image, disk deletion, SSH authentication, exact `custom_data`, provider registration setting and all resource names. An apply creates billable resources. Capture rubric screenshot 9 only from the genuine approved plan, with sensitive identifiers hidden by framing—not by inventing output.

### 3. Apply and record outputs, only within approval

```bash
terraform apply -input=false .private/reviewed.tfplan
terraform output -raw public_ip_address
terraform output -raw resource_group_name
terraform output -raw vm_name
```

Use the reviewed saved plan, not `-auto-approve` or a new unchecked plan. Record the actual IP in the assignment after success, preserving the pending status if it fails. Do not publish full state, `terraform show -json`, raw apply logs or subscription IDs. Keep the live local state and backups protected until cleanup is verified; never use another worktree's state.

### 4. Verify cloud-init, service, SSH and browser

Only after authorized remote execution and controller access checks, connect with your existing private key through your approved SSH configuration. Verify the server host key via an approved independent channel; never disable host-key checking. Supply the real outputs privately, rather than the TEST-NET fixtures:

```bash
ssh -i "$EXISTING_PRIVATE_KEY_PATH" "$ADMIN_USERNAME@$VM_PUBLIC_IP"
# Inside the authorized VM:
sudo cloud-init status --wait
sudo cat /var/lib/dmi-react/deployment-ready
sudo nginx -t
systemctl is-enabled nginx
systemctl is-active nginx
systemctl status nginx --no-pager
curl --fail --silent --show-error http://127.0.0.1/ -o /tmp/react-index-check.html
```

`cloud-init status --wait` must finish successfully, not merely return an IP from Azure. Confirm the readiness marker's exact upstream commit/Node/lock digest and current boot timing. Inspect `/var/log/cloud-init-output.log` and `journalctl -u nginx --no-pager` privately on failure; no marker means no successful deployment claim. Do not work around missing packages/build errors by editing JavaScript, relaxing NSG rules or running manual cloud configuration. Diagnose first, revise reviewed Terraform/bootstrap if needed, and obtain approval for any rebuild/replacement and additional cost.

After the parent authorizes GUI evidence, browse to the **real** `http://<VM-public-IP>/` and a client route, checking the page plus loaded JS/CSS. Screenshot 14 must show the true public IP in the address bar and authentic Eze Favour identity elsewhere on screen. A localhost curl or static HTML response cannot substitute for the real browser verification. Avoid sensitive neighboring windows. Preserve each of the 15 slots until its genuine evidence exists; do not repurpose mock output or local compilation as cloud screenshots.

### 5. Destroy and verify exact cleanup

Cleanup remains required even after a failed/partial apply. Use the same private state, approved subscription and input file. Privately save the real RG name **before** destroy, since Terraform outputs will disappear:

```bash
RG_NAME=$(terraform output -raw resource_group_name)
terraform plan -destroy -input=false -var-file=.private/run.tfvars -out=.private/destroy.tfplan
```

Review that only these assignment resources and the managed OS disk are being removed. Under the fresh cleanup authorization, either apply that reviewed saved destroy plan (`terraform apply -input=false .private/destroy.tfplan`) or use interactive `terraform destroy -var-file=.private/run.tfvars` and review its current plan before confirming. The latter matches screenshot 15's requested command; do not run both unnecessarily. On any failure, keep state and inspect privately—do not discard state or silently abandon resources.

Then perform the approved read-only checks:

```bash
terraform state list
az group exists --name "$RG_NAME" --output tsv
az resource list --resource-group "$RG_NAME" --output table
```

Expected results: **empty Terraform state**, Azure RG existence **false**, and resource listing reporting RG-not-found (or empty), not an authorization/network error. Independently check for the VM, attached OS disk, public IP, NIC, NSG, subnet and VNet; the destroyed unique RG must not contain any remaining resources. Confirm no detached OS disk or public IP from a partial run remains under the assignment names/tags. Resolve uncertainties with the owner within budget; use Terraform for infrastructure remediation, not ad-hoc cloud deletions. Check billing/resource inventory after its normal reporting delay; a destroy message does not prove zero charges. Only then record genuine cleanup evidence, replace pending manifest entries and review private-state retention/deletion under the owner's policy. Never delete old worktrees, histories, other assignments, tools or evidence as part of this cleanup.

## References

- [AzureRM 4.47.0 Linux VM](https://registry.terraform.io/providers/hashicorp/azurerm/4.47.0/docs/resources/linux_virtual_machine)
- [AzureRM 4.47.0 provider configuration](https://registry.terraform.io/providers/hashicorp/azurerm/4.47.0/docs)
- [AzureRM public IP](https://registry.terraform.io/providers/hashicorp/azurerm/4.47.0/docs/resources/public_ip)
- [AzureRM NSG](https://registry.terraform.io/providers/hashicorp/azurerm/4.47.0/docs/resources/network_security_group)
- [Terraform provider mocks](https://developer.hashicorp.com/terraform/language/tests/mocking)
- [RFC 8032 public test vectors](https://www.rfc-editor.org/rfc/rfc8032#section-7.1)
