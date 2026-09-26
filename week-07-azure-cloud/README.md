# Week 07 — Azure Cloud: verified recovery

On 26 September 2026, the Week 07 deployments were recovered and independently checked. The original 60 missing or 1-pixel image references now resolve to readable evidence, and two additional account views document current Azure access. The seven briefs link the evidence and mark supported technical tasks complete.

| Assignment | Verified result |
|---|---|
| A1 — Account | Portal access and active subscription verified. Historical Free Trial signup, identity/payment/phone verification and agreement acceptance remain unverified. |
| A2 — React | [Original VM app](http://4.223.123.39/), fresh build, Nginx, SSH restriction and nested-route refresh verified. |
| A3 — Network | Three subnet ranges, Nginx VM and public LB tested; the temporary 18-resource exercise was deleted after capture. |
| A4 — Storage | [Mini Finance](https://minifinanceeze20260926.z1.web.core.windows.net/): 32/32 public assets match source bytes. |
| A5 — EpicBook | [Live app](http://20.240.250.186/), private MySQL, cart and synthetic checkout verified through HTTP, browser and independent SQL. |
| A6 — Book Review | [Live app](http://4.225.220.198/), two private web VMs, two private API VMs, private MySQL, Key Vault, monitoring and availability test verified. |
| A7 — Audit | Actual Bedrock Claude plan and two skill runs; a separate Codex operator remediated the unattached-NSG fixture; four final checks pass. Personal learner execution is not claimed. |

Start with the [evidence index and limitations](evidence/2026-09-26/README.md), [62-slot screenshot manifest](evidence/2026-09-26/screenshot-manifest.json), [recovery source](recovery/README.md) and [read-only audit](security-audit/README.md). The [published reflection](../publication-review/published/week-07-blog.md) explains the actual recovery.

Public application endpoints use HTTP. MySQL has private connectivity, certificate-verified TLS and seven-day backups, but is a single instance without database HA. The web availability test succeeded after probe convergence; it does not establish zero interruption during the transition.

Codex performed this recovery under Eze Favour's delegation. Screenshots distinguish native browser/portal views from labelled saved-output viewers. The earlier 1-pixel image audit remains in Git history and publication-review evidence. DMI determines rubric acceptance and scores on its rerun. Attendance was not changed, and no attendance-verification message was sent.
