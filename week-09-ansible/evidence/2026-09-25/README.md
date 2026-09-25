# Week09 verified evidence — 25 September 2026

Learner: **Eze Favour**. Execution and writing: Codex-assisted under delegated authorization. This index supersedes older pending-runtime statements; original source/capture history is retained. Screenshots are genuine browser views or explicitly labeled renderings of recorded output. Browser page captures omit browser chrome; no address-bar visibility is claimed. Recorded-output views are not live Terminal or VS Code captures.

| Assignment | Verified outcome | Evidence |
|---|---|---|
| A1 workstation | Prior persistent workstation, tools and twelve original captures retained | [original brief](../../assignment-01-set-up-a-team-ready-ansible-development-workstation.md) |
| A2 four VMs | All four running; SSH/cloud-init, ping4/4, uptime, htop and Nginx checks succeeded; all23 resources subsequently removed | [cloud](a2-azure-four-running.png), [ping](a2-ping.txt), [cleanup](a2-cleanup.json) |
| A3 multiple web hosts | Group1 and name corrected, HTTP200 on both hosts, changed0 rerun; hosts retired after proof | [first](a3-web1-home.png), [second](a3-web2-home.png), [contact](a3-contact.png), [deploy](a3-deploy.txt), [unchanged rerun](a3-idempotence.txt) |
| A4 MiniFinance | Live at http://135.116.197.163; successful deploy and changed0 rerun | [app](a4-home.png), [attribution](a4-attribution.png), [deploy](a4-deploy.txt), [rerun](a4-idempotence.txt) |
| A5 EpicBook | Live at http://20.77.180.238; private managed MySQL with verified TLS, PM2 online, prior orders preserved,20 real HTTP/SQL checks, changed0 rerun | [managed app](a5-managed-home.png), [checks](a5-checkout-managed-e2e.json), [deploy](a5-deploy-managed-recap.txt), [rerun](a5-idempotence-managed-recap.txt) |
| A6 risk review | Real Claude/Bedrock plan → LOW → HOLD → operator apply → LOW, plus fresh deterministic post-migration LOW | [reports and explanation](../../risk-review/README.md), [change summary](../../risk-review/change-summary.md) |

## Exact limitations

Azure capacity/subscription restrictions required Standard_F1als_v7 in Sweden Central for MiniFinance instead of B1s. A5's VM remains UK South; its managed MySQL is Sweden Central through private peering and DNS, because UK South provisioning was rejected. No public database endpoint was enabled. The MiniFinance template's balances, names and transactions are sample content, not the learner's financial data. EpicBook orders are synthetic and do not take payment or arrange shipment.

Historical A5 screenshots show an earlier phase and are not presented as the final managed database. The current screenshots do not fill every exact native Terminal/VS Code/address-bar capture slot in the full instructor brief. A6's human-personally-manual requirement is not claimed: Codex applied under delegation. The rubric's strict evidence-format decisions and final score belong to the assessor.

The two A3 IP addresses are historical and no longer owned by this lab. Do not use them as current demo URLs.

## Published write-ups

[Medium article](https://medium.com/@rosenaefavour/from-four-linux-vms-to-a-repeatable-epicbook-deployment-dmi-week-09-f1f1ea25646f) · [LinkedIn post](https://www.linkedin.com/feed/update/urn:li:activity:7509317694291283968/). Both were published with an assisted-work disclosure and DMI attribution.

[Published post capture](w09-linkedin-published.png).
