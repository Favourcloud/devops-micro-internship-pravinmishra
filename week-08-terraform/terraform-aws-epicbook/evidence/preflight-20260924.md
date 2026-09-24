# Assignment 04 — preflight on 24 September 2026

Codex performed this preparation under user delegation. No live deployment or manual learner execution is claimed. The existing 19 screenshots remain unchanged; slots 20–35 remain pending.

## Current source

The bootstrap now pins **Node 22.23.3** and the Linux x64 archive SHA-256 from the [official checksum file](https://nodejs.org/dist/v22.23.3/SHASUMS256.txt). The [official release index](https://nodejs.org/dist/index.json) identifies Node 22.22.2, 22.23.0 and 22.23.2 as security releases newer than the previous 22.22.0 pin. The [source-update record](runtime-update-20260924.json) records both source hashes and the exact replacement. No application dependency upgrade or vulnerability audit is claimed.

The 21 other implementation/test files in the historical source manifest, all 19 PNGs, original capture metadata and rubric requirements remain unchanged. Screenshot 10 shows the earlier script. Tests reconstruct its original source hash by reversing only the version/checksum replacement; an unrelated edit still fails preservation checks.

## Local validation

The unchanged baseline passed **22 Terraform mock runs and 65 Python checks**, plus formatting, isolated initialization, validation, write-only schema checks and shell syntax checks. This was a fresh local run using Terraform 1.13.5 and the existing AWS 6.64.0 mirror. It did not make authenticated AWS calls or create resources.

The updated source also passed **22 Terraform mock runs and 65 Python checks**, plus formatting, isolated initialization, validation, write-only schema checks and shell syntax checks. The original PNGs, historical metadata and 21 unchanged source files passed integrity checks. No successful runtime result is inferred from mock tests.

## Remaining work

The instructor repository still points to [763bece](https://github.com/pravinmishraaws/theepicbook/tree/763becebb8d3f5663a76bb30facddc25be63cfd5), with no newer tagged release. The existing cart route can support screenshots 32–33 if verified in a real run. There is still no checkout/order creation endpoint; the separate order-workflow checklist remains incomplete.

Browser automation returned `Codex auth token is unavailable`; the four local AWS profiles returned `InvalidClientTokenId`. Therefore the replacement account could not be reverified, and no real plan, key-pair inventory, current RDS orderability query or deployment was attempted. Existing A1–A3 teardown is unaffected.

The planned topology remains 28 managed resources: 19 network, three RDS, four EC2/IAM and two Secrets Manager resources. Before a real plan, confirm the active account, two AZs, controller address, usable existing key pair, current AMI/MySQL/class availability and regional pricing. Then review the actual resource changes and full lifecycle cost, including cleanup. No A4 spending approval is inferred from the completed A2 run.

The LinkedIn screenshot and publication require a real authorized post. This preparation fills no new screenshot slot, changes no DMI score, and does not complete A4.
