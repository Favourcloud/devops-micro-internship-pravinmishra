# Week 07 evidence — 26 September 2026

These are new verification results, not reconstructed historical screenshots. Operator: Codex under Eze Favour's delegation. The original 60 screenshot references have been replaced, and two A1 account views added. The [manifest](screenshot-manifest.json) records each slot, dimensions, SHA-256, capture time, method and source. A view is reused where it substantiates multiple requirements.

## Evidence methods

Azure portal and application images are actual browser captures. Account identifiers, private contact details and the operator IP were masked where visible. Browser screenshot tools omit address-bar chrome, so assignment links and API receipts establish the observed endpoint.

Command, SQL, source and Claude evidence is displayed in an explicitly labelled local browser viewer. Where a page exceeded the viewport, actual screenshots were stitched using observed scroll offsets. These are recordings of genuine saved results, **not** native terminal/editor screenshots or proof that the learner typed the commands. Matching complete text/JSON and source files are linked alongside each image. Raw credentials, unredacted portal images, Terraform state and authentication artifacts remain private.

## Verification map

| Claim | Source |
|---|---|
| Azure subscription and React | [Subscription](subscription.json), [VM](react-vm.json), [NSG](react-nsg.json), [build](react-build.txt), [Nginx](react-nginx-config.txt), [SSH](react-ssh-inspection.txt) |
| Network exercise and deletion | [VNet](a3-vnet.json), [LB](a3-lb.json), [VM](a3-vm.json), [cleanup](a3-cleanup.json) |
| Static site integrity | [Source](mini-finance-source.json), [upload](static-upload-manifest.json), [32 public checks](static-public-checks.json) |
| Five VM placements and services | [Compute](lab-vms.json), [NICs](lab-nics.json), [Epic](runtime-epic.json), [web1](runtime-web1.json), [web2](runtime-web2.json), [app1](runtime-app1.json), [app2](runtime-app2.json) |
| Network and database protection | [VNet](lab-vnet.json), [NSGs](lab-nsg.json), [DNS](lab-dns.json), [Key Vault](lab-keyvault.json), [MySQL](lab-mysql.json), [reachability](network-isolation.json) |
| Behavior and persistence | [16 HTTP checks](application-http-checks.json), [independent SQL](independent-sql.json), [browser writes and SQL](browser-sql.json), [Epic schema](schema-epic.json), [Book schema](schema-book.json) |
| Availability and monitoring | [LBs](lab-load-balancers.json), [alert](lab-alerts.json), [metrics](lb-metrics.json), [availability test](availability-test.json) |
| Deployed source | [Comparisons](deployed-source-checks.json), [Book manifest](book-source-manifest.json), [Epic manifest](epic-source-manifest.json) |
| Claude plan before script creation | [Actual plan and tool metadata](audit-plan.result.json) |
| Baseline, separate fix, fresh audit | [Baseline](baseline-azure-audit-report.json), [baseline Claude](audit-baseline.result.json), [operator change](audit-remediation.json), [recovery](recovery-azure-audit-report.json), [recovery Claude](audit-recovery.result.json) |
| Audit validation | [Syntax, executable bit and nine behavioral tests](audit-source-validation.txt) |

The first HTTP run created Book Review review 1 and EpicBook demo order 1. Browser actions subsequently created review 2 and order 2; independent SQL confirmed those exact rows. Both orders were synthetic and took no payment. Test credentials are excluded.

The web test stopped Nginx on web1, waited 25 seconds for probes, then received 12/12 public database-backed responses from web2. Web1 was restored; both nodes appeared in subsequent requests. This does not measure zero-downtime transition, app/database failure or backup restoration. The alert was configured and metrics read; notification delivery is not claimed.

## Fixes discovered during verification

- A separate oneshot secret-fetch service now runs before the API service loads its protected environment file.
- Database user creation quoting was corrected; host-restricted, database-scoped CRUD grants were verified.
- The homepage's duplicated `/api/api/books` path was replaced with the same API service used by login and reviews.
- White text on light cards/forms under dark browser preferences was corrected.
- EpicBook now displays the actual Week 07 verification date.

## Claude provenance and interpretation corrections

Claude Sonnet 4.6 ran through Amazon Bedrock. Reported call costs were $0.0555528 for planning, $0.0976434 for baseline and $0.0960009 for recovery, excluding tax. Both skill runs attempted appended `; echo "EXIT:$?"` syntax, which was denied; the exact allowed script command subsequently executed. The saved runs retain these denials. No cloud mutation was available to the audit skill.

The original plan incorrectly named a default rule `AllowInternetInBound`; the relevant Azure default is `DenyAllInBound`, corrected before implementation. The recovery explanation confused `DeliberateAuditSSHFixture` (the rule) with `week07-unattached-audit-fixture` (the NSG), and said the rule update was the only intervening change; the fifth VM also appeared between runs. The report/API evidence is authoritative. General model comments about encryption compliance are not certified here.

The deliberately broad SSH fixture was **unattached**, with no NIC/subnet associations. Narrowing its source from `0.0.0.0/0` to the controller `/32` demonstrated detection/remediation without exposing a workload. Codex executed the fix separately from the read-only Claude auditor. This does not fulfill a requirement that the learner personally execute it.

## Remaining rubric distinctions

Current active access cannot prove historical Free Trial identity/phone/payment verification or terms acceptance. Those A1 boxes remain open; A7's personal-execution box also remains open. Equivalent available VM sizes and labelled saved-output evidence are disclosed. Public apps use HTTP; MySQL is a single instance with seven-day backups. These are not silently relabelled as production readiness or guaranteed credit.

DMI had credited all seven assignment files at the earlier audit, but only DMI can accept replacements or change scores. Attendance was not modified. The six earlier Week 08–10 demos were preserved.
