# Assignment 03 — verified Azure React run

Eze Favour's approved Azure lab completed on **24 September 2026 (Africa/Lagos)**, with execution and cleanup on **23 September UTC**. **All 15 numbered screenshots are present.** Codex performed this run under user delegation; no manual learner execution is claimed. The original eight local captures and their [historical provenance](provenance.json) remain unchanged. The seven new captures have separate [live provenance](live-provenance.json).

## Deployment and verification

The reviewed saved plan created **8 Terraform resources** in Azure subscription 1 / Sweden Central: a dedicated resource group, VNet, subnet, NSG, Standard public IPv4, NIC, NIC/NSG association and Linux VM. The VM was **Standard_D2als_v6 (2 vCPU, 4 GiB)**, running Ubuntu 24.04 image **24.04.202609040**, with a 32 GiB Standard LRS OS disk. Terraform 1.13.5 and signed AzureRM 4.47.0 used the unchanged Terraform, bootstrap and lock files. Public TCP 80 and SSH from the controller IPv4 `/32` were the only allowed inbound traffic.

| Result | Verified observation |
|---|---|
| Plan | 8 create, 0 update, 0 delete; exact saved plan applied |
| Apply | 8 added, 0 changed, 0 destroyed |
| Public IP | `4.225.168.0` — **retired after verified cleanup**, not a current endpoint |
| SSH | Authenticated connection with strict host-key checking; host key obtained through authenticated Azure VM Run Command |
| Bootstrap | cloud-init done; readiness marker matched pinned upstream commit, Node 22.23.2 and lock digest |
| Nginx | Active, enabled, valid configuration |
| Public application | HTTP 200; SPA fallback matches index; real JS and CSS assets returned |
| Browser | React page rendered in Chrome Guest and Codex in-app browser; native capture includes the actual IP address bar |
| Destroy | 8 resources destroyed; empty Terraform state and exact Azure absence checks passed |

The browser still displays the instructor application's **Your Full Name** and **DD/MM/YYYY** placeholders because its JavaScript was kept unchanged. Eze Favour appears in the authentic Terminal alongside the browser. Screenshot 14 is a **single native screen-region capture**, not a composite or pixel-edited image. Terminal evidence shows selected genuine saved-plan/CLI output or recorded genuine SSH output; capture timestamps can therefore follow execution timestamps. Slot 9 was recaptured from the same saved plan to include the proposed resource list.

## Cleanup and cost

- Apply started: **2026-09-23T23:28:20.682110+00:00**.
- Apply completed: **2026-09-23T23:31:25.014012+00:00**.
- Cleanup verified: **2026-09-23T23:47:27.581636+00:00**.
- Total window: **19.11 minutes**, within the approved one hour. The fallback watchdog observed completed cleanup and stopped.

Eight independent Azure IDs were checked absent: the **seven direct ARM objects** managed by Terraform (RG, VM, VNet, subnet, NSG, public IP and NIC), plus the VM's **OS disk**. The eighth Terraform resource is the NIC/NSG association; NIC absence proves its removal. These are **eight exact-ID reads**, not nine. The resource-group existence check returned false and Terraform state was empty. Private state and backups were retained.

The published base estimate was **$0.093104/hour**; applying that rate conservatively to the entire 19.11-minute window gives approximately **$0.0297**, before disk operations, bandwidth and taxes. **The actual bill has not been verified.** The approved spending ceiling was $1. No resources from this lab remain; the completed window does not authorize another deployment.

## Evidence and validation

The [assignment document](../../assignment-03-deploy-a-react-application-on-azure-virtual-machine-using-terraform.md) links each screenshot under its original rubric heading. The [manifest](manifest.json) separates current completion from historical source validation and local-capture integration. Private account identifiers, controller address, credentials, raw logs, binary plans and state are excluded.

Before deployment, the unchanged implementation passed **56 Python tests and 35 Terraform mock runs**, formatting, shell syntax, initialization and validation. Those checks are supplementary; the runtime results above come from real Azure, SSH, HTTP and browser verification. All **28 focused delivery and provenance checks passed** for this evidence update, as recorded in [live-validation.json](live-validation.json). DMI's last observed Week 08 score remains **70/190**, with no regrade of this result observed.
