# Sanitized local validation — Week 08 Assignment 4

**Learner:** Eze Favour

**Scope:** OFFLINE ONLY — source/mock validation, not runtime evidence.

**All 35 screenshots remain pending.** No browser, IDE or terminal images were generated.

## Reproducible check

From `terraform-aws-epicbook`, supply existing absolute `TERRAFORM_BIN` and
`AWS_PROVIDER_MIRROR` paths privately, then run:

```bash
bash scripts/check-offline.sh
```

The runner has no cloud plan/apply/destroy path. It uses an empty HOME, cleared
AWS environment, disabled metadata/checkpoints, filesystem-only provider mirror,
read-only lock init, short private temporary directories and automatic cleanup.
The preflight refuses real tfvars, overrides, state, private directories and symlinks.
No personal tool paths, raw logs, credentials or account metadata are published here.

## Results

Final completed run (2026-09-17): Terraform **1.13.5**, AWS provider **6.64.0**, macOS darwin_amd64.
The expanded final suite passed **18 native mock runs and 46 standard-library tests**,
with zero failures. Final rerun status: **PASS**.

| Check | Verified result |
|---|---|
| `terraform fmt -check -recursive` | PASS |
| `terraform init -backend=false -lockfile=readonly -input=false` | PASS, existing filesystem mirror; no download or AWS calls |
| `terraform validate` | PASS |
| `terraform providers schema -json` plus `scripts/check-schema.py` | PASS: both credential fields sensitive/write-only; numeric version fields |
| `terraform test -test-directory=tests` | PASS: 18 native mock runs, 0 failed |
| `bash -n` for user data and runner | PASS |
| Python stdlib tests (runtime/privacy/cleanup/preservation suite) | PASS: 46 tests, 0 failed |

The native mock tests check exact subnets, routing, SG restrictions, private TLS RDS,
module wiring, encrypted disk/IMDSv2, user-data references/size, write-only unreadable
values, and positive/negative inputs. Python and shell stubs exercise import ordering,
partial import failure, bounded retries, protected files, cleanup on error, limited
DB grants, catalogue readiness versus default Nginx/failed service/HTTP, isolation,
original assignment and all 35 manifest slots, and exact-ID cleanup-ledger rejection.
A provider mock is not an AWS plan. A SQL/subprocess stub is not MySQL/Node/systemd.

## Source facts and explicit limits

- 12 Terraform source files, 25 resource blocks expanding to 28 proposed instances,
  and one AMI lookup; none were provisioned.
- Instructor main was publicly checked at commit
  `763becebb8d3f5663a76bb30facddc25be63cfd5`; no newer release/tag was available.
  Node artifact checksum and package/lock/config/SQL/route contracts were read,
  not installed or executed locally.
- Password input is ephemeral+sensitive and routed only to write-only RDS/secret
  fields. Username and resource metadata still require confidential state handling.
- The upstream checkout UI deletes carts; it has no order creation route.
  Future cart screenshots/records cannot justify the separate checkout/order check.
- No cloud auth, AWS control-plane call, SSH, actual plan/apply/destroy, billing/IAM
  mutation, real application import/install, live cleanup proof or LinkedIn posting
  was performed. No approval is inferred from this file.
- Live EC2/RDS/software/catalogue/cart/database evidence, public IP URL, all 35
  captures, end-to-end runtime compatibility, fresh permission/budget approval,
  exact-ID destruction and mandatory learner publication are still pending.
