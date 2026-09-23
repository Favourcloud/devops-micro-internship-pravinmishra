# Assignment 2 — verified AWS run, 23 September 2026

Eze Favour’s temporary AWS VM lab completed its real Terraform lifecycle in `us-east-1`. Codex operated the session under the user’s explicit approval; this is not manual learner execution. All **10 of 10** numbered evidence slots are filled. The four earlier local originals and their historical provenance remain unchanged, while six new captures document this live run. No new DMI grade or personal reflection is claimed.

## Execution and verification

The reviewed source was commit `40771b24f19ea79a0fe5061790f2c0836e71d770`. Terraform 1.13.5 and AWS provider 6.64.0 ran in CloudShell using the existing replacement-account root console session’s temporary credentials. The account identity was checked privately before plan, apply and teardown. No AWS access keys or IAM users were created. The local HashiCorp Terraform extension was installed in Visual Studio Code as version 2.40.0; new extensions are enabled by default.

The provider lock required its signed Linux package’s unpacked checksum. Running `terraform providers lock -platform=linux_amd64` added only `h1:2fTLxzUDmp/KVIHbIeLTB4bIzWHx8E6Dw+1ALLUi+Yw=`. The version and every previous checksum were retained. Terraform validation then succeeded. The infrastructure and bootstrap source were unchanged.

| Event | Verified result |
|---|---|
| Saved plan | 11 add, 0 change, 0 destroy; exact digest recorded in provenance |
| Apply started | 22:41:43 UTC |
| Apply and inventory complete | 22:42:20 UTC; 11 added, 0 changed, 0 destroyed |
| EC2 | `i-05972a6598e2eb990`, Ubuntu 24.04 AMI `ami-0045d7fc2ad003464`, `t3.micro` |
| Runtime checks | AWS reported `running`, system and instance health `ok`; AWS instance/IP matched Terraform |
| HTTP and browser | Expected Nginx page and Eze Favour’s name at the recorded public IP |
| SSH | Strict host checking after matching AWS console system-log fingerprint; cloud-init `done`, Nginx syntax valid and service `active`, localhost HTTP passed |
| Teardown | Reviewed 0 add/0 change/11 destroy; actual `terraform destroy` reported all 11 destroyed |
| Cleanup complete | 22:50:11 UTC; all 13 exact-ID checks passed and state empty |

The temporary public IP was `3.80.169.89`, with browser URL `http://3.80.169.89/`. **This address was retired after teardown and is not a current endpoint.** The browser screenshot captures page content without the address bar; the selected tab URL was checked separately, and independent HTTP and SSH checks corroborated the page.

The approved scope allowed public TCP 80 and SSH only from the controller’s current IPv4 `/32`, using a dedicated local key outside the repository. The instance required IMDSv2 and used an encrypted 8 GiB gp3 root disk and standard CPU credits. The private subnet had no Internet default route. No NAT gateway, load balancer or database was created.

## Cleanup, cost and evidence handling

The lab ran for approximately 8 minutes 28 seconds, within the approved one-hour window and $1 ceiling. The base estimate was about $0.0163/hour before credits, putting this run’s base estimate below $0.01; data transfer is additional and the actual bill has not been verified. The fallback cleanup timer was stopped after successful teardown.

The existing cleanup helper verified all 11 managed object IDs plus the root EBS volume and primary network interface. EC2 was absent/terminated; the other resources were absent. Empty Terraform state was checked in addition to those AWS reads. Private state, backups, inputs and logs remain in the private workspace for recovery/audit and are not committed.

See [manifest](manifest.json) for all ten images and [live provenance](live-capture-provenance.json) for timestamps, source/image hashes and structured results. [Earlier capture provenance](capture-provenance.json) and [earlier validation](local-validation.json) describe September 16–17 only. Their old pending flags remain historical facts.

The browser capture tool returned JPEG originals. Slots 5–8 and 10 were cropped from 1280×720 to 1280×630 at `(0,55)` to omit AWS account navigation/footer, then converted to PNG. Slot 9 was converted to PNG without cropping. No terminal output or page content was edited or reconstructed. All six public images were visually inspected for readability, learner identification and sensitive information.
