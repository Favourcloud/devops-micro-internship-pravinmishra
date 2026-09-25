# Week10 verified evidence — 25 September 2026

Learner: **Eze Favour**. Operator and writing: Codex under delegated authorization. Run URLs below require access to the private Azure DevOps project. Public source and sanitized captures allow independent review without sharing its credentials.

| Assignment | Actual result | Evidence |
|---|---|---|
| A1 self-hosted agent | Official agent5.279.0, Ubuntu, non-root azdoagent,29GB free at check; manual run3 succeeded | [run3](https://dev.azure.com/aneneeze2021/DMI-Week10/_build/results?buildId=3), [capture](w10-a1-run3.png) |
| A2 static AWS site | Manual run13 and automatic CI runs15/17 passed; learner name visible | [CI17](https://dev.azure.com/aneneeze2021/DMI-Week10/_build/results?buildId=17), [site](w10-a2-live.png), http://100.54.219.171 |
| A3 React | Manual run12 and automatic CI16 passed Build/Test/Publish/Deploy, actual Jest tests, native SSH transfer | [CI16](https://dev.azure.com/aneneeze2021/DMI-Week10/_build/results?buildId=16), [capture](w10-a3-ci16.png), [site](w10-a3-live.png), http://20.108.9.183 |
| A4 dual pipelines | Infra apply11 and application14 succeeded; both Ansible hosts changed0 on rerun;19 HTTP/SQL checks passed with verified database TLS | [infra](w10-a4-infra-run11.png), [four outputs](w10-a4-handoff-cropped.png), [app pipeline](w10-a4-app-run14.png), [app](w10-a4-live.png), [saved browser order2](w10-a4-order.png), [API/SQL](a4-checkout-managed-e2e.json), http://51.107.188.80 |
| A5 triage | Baseline HEALTHY0, controlled Build failure18 INCIDENT1, corrected branch run19 HEALTHY0; deployment skipped for the drill branch | [complete report sequence](../../pipeline-triage/change-summary.md) |

## Scope and provenance

Screenshots are real page captures; browser chrome/address bars are not included. The four-output image is a crop of the genuine apply log, with the exact crop recorded in [provenance](handoff-crop-provenance.json). It excludes unrelated resource identifiers, not failed output. Original screenshots from September18–19 remain historical and are not relabeled as this run.

The agent uses a managed identity scoped to the A4 resource group and state account. SSH uses pinned hosts and isolated forwarding/deployment accounts. No AWS credentials were sent to the agent. A4 database traffic is private and TLS-verified. Credentials, private keys, Terraform state and raw private logs remain excluded.

## Remaining rubric limitations

The existing PAT works, but its original creation, exact scopes and expiry are not newly certified. The original supplied A5 kit could not be located; the replacement is openly identified as original. A5's fresh Claude/Bedrock diagnosis could not run after AWS authentication expired. Operator actions were delegated, not performed personally by the learner. Page captures and recorded-output viewers are not substitutes for every exact native-editor/address-bar screenshot requirement. React succeeds with upstream NodeTool@0 deprecation warnings; no build/test failure is hidden. Final grading is pending assessor review.

## Published write-ups

[Medium article](https://medium.com/@rosenaefavour/two-pipelines-one-verified-app-dmi-week-10-with-azure-devops-d6b95cfff40a) · [LinkedIn post](https://www.linkedin.com/feed/update/urn:li:activity:7509319294388944897/). Both were published with an assisted-work disclosure and DMI attribution.

[Published post capture](w10-linkedin-published.png) · [post and attached images](w10-linkedin-media.png).
