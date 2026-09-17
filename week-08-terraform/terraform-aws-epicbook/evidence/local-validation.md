# Sanitized local validation — Week 08 Assignment 4

**Learner:** Eze Favour

**Scope:** OFFLINE ONLY — local source/capture/mock validation, not runtime evidence.

**19 original local PNGs (slots 1–19) are present; slots 20–35 remain pending.**
The [manifest](screenshot-manifest.json) preserves all original titles in order.
[Sanitized provenance](provenance.json) records original hashes, actual capture timestamps,
Copilot operation under delegation, and the frozen source head:
`7c0005592f167730edb0ec3f56bf29324af6a031`.
All 22 frozen implementation/test hashes remain unchanged. `tests/test_evidence.py`
is the sole delivery-test exception; its original hash is retained in provenance.
No manual learner execution or final review clearance is claimed.

## Historical frozen-source check

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

## Historical results — not rerun for evidence integration

Frozen-source run (2026-09-17): Terraform **1.13.5**, AWS provider **6.64.0**, macOS darwin_amd64.
The credential-fix suite passed **22 native mock runs and 52 standard-library tests**,
with zero failures, and the parent independently verified that result. Historical status: **PASS**.
This evidence-only change does not relabel that count as a current full-suite run.

| Check | Verified result |
|---|---|
| `terraform fmt -check -recursive` | PASS |
| `terraform init -backend=false -lockfile=readonly -input=false` | PASS, existing filesystem mirror; no download or AWS calls |
| `terraform validate` | PASS |
| `terraform providers schema -json` plus `scripts/check-schema.py` | PASS: both credential fields sensitive/write-only; numeric version fields |
| `terraform test -test-directory=tests` | PASS: 22 native mock runs, 0 failed |
| `bash -n` for user data and runner | PASS |
| Python stdlib tests (runtime/privacy/cleanup/preservation suite) | PASS: 52 tests, 0 failed |

The native mock tests check exact subnets, routing, SG restrictions, private TLS RDS,
module wiring, encrypted disk/IMDSv2, user-data references/size, write-only unreadable
values, and positive/negative inputs. Python and shell stubs exercise import ordering,
partial import failure, bounded retries, protected files, cleanup on error, limited
DB grants, catalogue readiness versus default Nginx/failed service/HTTP, isolation,
original assignment and all 35 manifest slots, and exact-ID cleanup-ledger rejection.
A provider mock is not an AWS plan. A SQL/subprocess stub is not MySQL/Node/systemd.

Credential regressions reproduced the previous helper's missing username guard and
unquoted `#` password truncation using synthetic inputs only. Root and direct RDS-module
mock tests now reject the application username as the master; runtime tests reject
case variants before any SQL or credential-file creation in both `prepare` and `verify`.
A distinct master and an allowed `#` password are accepted. Both orchestration paths
preserve that password in protected temporary option files and remove those files.
Serializer fixtures cover quoted comment characters, double quotes, backslashes,
spaces and supported control escapes without broadening the allowed password alphabet.
The test parser is a small independent model checked against the public
[MySQL 8.4 option-file rules](https://docs.oracle.com/cd/E17952_01/mysql-8.4-en/option-files.html)
and [8.4.0 parser implementation](https://github.com/mysql/mysql-server/blob/mysql-8.4.0/mysys/my_default.cc),
not execution of a real MySQL parser, client or server.

## Genuine parent local captures and commands

The parent verified the handoff on 2026-09-17. All 19 PNGs are original native macOS
VS Code window captures, **3584 × 2000**, totaling **10,553,523 bytes**. Integration
copied the bytes unchanged; no crop, composite, overlay, pixel edit or new GUI occurred.
The parent reviewed privacy before handoff; focused integration tests check metadata
and integrity, not independent visual verification. No private sidecars, raw OCR,
window identifiers, process identifiers or personal filesystem paths are published.
Actual timestamps are retained; slot order is not a chronological execution claim.

| Captured local command | Parent-verified result |
|---|---|
| `terraform init -input=false -lockfile=readonly` | PASS; normal init, credential-free, existing read-only filesystem-only AWS 6.64.0 mirror, startup guard passed |
| `terraform validate` | PASS; separately executed, not a live plan/apply |

The source uses the **implicit default local backend**, not a backend at
`.private/terraform.tfstate`. No backend metadata `.tfstate` or managed state at the
root/default or `.private` path was created. A future default managed-state path is
`terraform.tfstate` unless deliberately overridden for an authorized operation.
`TF_DATA_DIR` controls metadata only, **not the managed-state path**. The captured
normal init is distinct from the historical runner's backend-disabled init above.
No remote backend or AWS call was involved.

Slot 4 proves source directories and `terraform.tfvars.example` only; real private
`terraform.tfvars` is not created and remains gated. Slot 10 shows native split-editor
excerpts at lines **21–47 and 83–117**, with word-wrap, not the whole script or executed
bootstrap. Slots 11/13/15 are native split editors, not synthetic composites.
Slots 8/11/14/17 show output source expressions, not actual resource values.

## Focused evidence-only verification

From `terraform-aws-epicbook`:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_evidence.py -v
```

Result (2026-09-17): **PASS — 18 focused standard-library tests, 0 failures**.
`git diff --check` also passed. These checks cover original brief line order,
all 35 exact titles, 19 local/16 pending slots, links, private-metadata
exclusion, PNG signature/chunk CRCs/decoded scanlines, original SHA-256 hashes and
all 22 frozen source hashes. No unchanged Terraform mock suite or runtime test is
rerun, and ignored private artifacts are preserved. Independent evidence-integration
verification remains pending.

The parent separately confirmed targeted independent re-review of
`86210c7b1436b6bbe7d0b2bb61f45b5b4c2618fe..7c0005592f167730edb0ec3f56bf29324af6a031`:
no significant issues found in the reviewed credential fixes/regressions; both the
reserved-username collision and MySQL option-quoting findings are resolved at that
source head. This does not claim evidence-integration, live-runtime or submission clearance.

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
- Live EC2/RDS/software/catalogue/cart/database evidence, public IP URL, slots 20–35,
  end-to-end runtime compatibility, fresh permission/budget approval, private tfvars,
  exact-ID destruction, learner reflection and mandatory LinkedIn publication are
  still pending. The full deployment/cleanup/order checklist remains unchecked.
