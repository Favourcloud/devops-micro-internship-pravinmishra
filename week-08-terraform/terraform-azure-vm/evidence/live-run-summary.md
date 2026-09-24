# Assignment 01 — verified Azure VM run

**Eze Favour — 11/11 required screenshots captured.** Codex performed the approved 24 September 2026 Azure run under user delegation; this is not manual learner execution. The [assignment](../../assignment-01-create-an-azure-virtual-machine-using-terraform.md) now includes the five missing runtime captures. Its six historical local images, frozen source and historical validation records remain unchanged.

## Deployment and verification

The reviewed saved plan created **eight Terraform resources** in **Azure subscription 1 / Sweden Central**: a dedicated resource group, virtual network, subnet, NSG, Standard public IPv4, NIC, NIC/NSG association and Ubuntu VM. Terraform 1.13.5 and AzureRM 4.47.0 used unchanged source and lock files. The existing Azure CLI login was reused and its identity/subscription verified; a new login command is not claimed.

The VM was **Standard_D2als_v6**, 2 vCPU / 4 GiB, with Ubuntu 22.04 Gen2 image **22.04.202608060** and a **30 GiB Standard LRS** OS disk. Password authentication met the rubric. Its new random password was supplied through the process environment, never displayed or committed. SSH was permitted only from the controller IPv4 `/32`; other inbound traffic was denied. No new IAM, application installation or SSH session was needed.

| Required output | Actual result |
|---|---|
| Terraform plan | 8 create, 0 update, 0 delete |
| Terraform apply | 8 added, 0 changed, 0 destroyed |
| Public IPv4 | `135.116.195.137` — **retired after verified cleanup** |
| Azure CLI | `dmi-w08-a1-20260924-vm` reported **VM running** and provisioning succeeded |
| Image and disk | Exact image version and Standard LRS disk checked through Azure |
| Terraform destroy | **8 destroyed**; empty state and Azure absence checks passed |

## Cleanup and costs

Apply began at **2026-09-24T00:34:03.972223+00:00** and completed at **2026-09-24T00:38:07.204342+00:00**. Cleanup was independently verified at **2026-09-24T00:48:37.287720+00:00**. The complete window was **14.56 minutes**, within the approved one hour; fallback cleanup was armed at 45 minutes and exited after verified teardown.

Eight exact Azure IDs were confirmed absent: **seven direct Terraform ARM objects**, including the resource group and VM, plus the VM's **OS disk**. The eighth Terraform resource was the NIC/NSG association; NIC absence independently proves removal of that association. The resource-group existence check returned false and Terraform state was empty. This count is eight exact-ID checks, not nine.

At the recent official **$0.093104/hour** base estimate, charging the entire window gives approximately **$0.0226**, before disk operations, bandwidth and taxes. A new pricing refresh returned HTTP 429, so the earlier same-session official response was used. **The actual bill is unverified.** The approved ceiling was $1. No resources from this A1 lab remain and this completed window does not authorize another run.

After verified cleanup, this run's generated password-bearing plans, JSON copies and state backup were removed. The final empty state, sanitized review, cleanup inventory and evidence receipts remain private. Existing user authentication and other assignments' private state were untouched.

## Evidence and validation

The five new PNGs are genuine native Terminal window captures of the real saved plan and selected CLI outputs; output was not fabricated or pixel-edited. Every image was visually reviewed. Slots 7–9 were recaptured in a smaller window after apply for readability; the plan screenshot still shows the original saved plan. [Live provenance](live-provenance.json) records UTC timestamps, original hashes and verification scope. The [manifest](manifest.json) keeps its six historical capture entries and historical validation sections separate from this run.

Preflight passed **15 Python checks and 31 Terraform mock runs**, plus formatting, initialization and validation. The final evidence integration passed **18 focused Python checks**; [live-validation.json](live-validation.json) records the result, source/image preservation and independent week-wide slot/link checks. DMI's last observed Week 08 score remains **70/190**; A1 already had automated file credit, so no score increase is promised by this technical completion.
