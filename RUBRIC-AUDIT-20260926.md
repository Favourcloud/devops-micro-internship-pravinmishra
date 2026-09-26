# DMI submission audit — 26 September 2026

The Week 08–10 submission passes the locally reproducible checks in DMI's [published grading rules](https://dmi.pravinmishra.com/how-it-works.html). Two publication defects were corrected: Week 09/10 LinkedIn links now use their real canonical `/posts/` addresses, and all three weekly blogs have accessible public copies. This record does not replace DMI's external assessment or certify unproved personal/manual requirements.

## Corrections now submitted

| Finding | Correction and verification |
|---|---|
| Week 09/10 LinkedIn links used `/feed/update/`, which does not match the required prefix | Retrieved each existing post's canonical URL through LinkedIn's copy-link action, resolved it, verified author/content, and updated the root progress table and active assignment briefs. [Canonical URLs](publication-review/evidence/2026-09-26/canonical-linkedin.json) |
| Medium articles loaded in the signed-in browser but anonymous requests returned HTTP 403 | Published accessible copies of the existing articles on GitHub Pages and submitted those URLs. Medium originals remain linked from the copies. [Original HTTP checks](publication-review/evidence/2026-09-26/blog-public-http.json), [successful public checks](publication-review/evidence/2026-09-26/pages-public-checks.json) |
| The Week 10 LinkedIn post still described expired AWS access | Updated that existing post with the completed Claude Code/Bedrock baseline, failed run 20 and recovery run 21. Reloaded its canonical URL and verified the update. [Receipt](publication-review/evidence/2026-09-26/linkedin-update-check.json) |
| README statuses were older than recorded DMI results | Marked Weeks 05–08 completed **in DMI** and displayed their existing badges. Week 07 now links its assignment folder. Weeks 09–10 state that submission checks are complete and DMI review is pending. |
| Four checklist items remained open despite existing evidence | Checked Week 08 A4's Terraform installation (v1.13.5), AWS CLI installation (v2.37.2), and installed HashiCorp Terraform extension; checked Week 10 A3's genuine screenshot showing Eze Favour and 2026-09-25. |

## Reproducible checks

The [machine-readable audit](publication-review/evidence/2026-09-26/submission-checks.json) records every expected path, content hash, original-prose count and remaining unchecked item. The comparison uses instructor revision `e979906210d76e22c1711afabc0fb941ae5c1184`.

The dashboard specifically flags Week 09 A5–A6 and Week 10 A2–A5 for template text. All six are included in the passing checks below; their actual deployment and AI-workflow evidence was delivered in earlier merged changes. The current audit also fixes both missing publication cells for each week. Attendance already shows 30 points for each of Weeks 09 and 10 and requires no repository change.

- **17/17 expected assignment files** exist and differ from their upstream templates.
- **17/17** contain none of the published flagged template phrases.
- **17/17** exceed 50 original prose words. The lowest conservative count is **688** after removing code fences, comments, headings, tables and lines identical to the official template.
- **3/3 README progress rows** have one real LinkedIn URL beginning `https://www.linkedin.com/posts/` and one verified public blog URL.
- **3/3 articles** returned HTTP 200 without authentication, contain over 200 paragraph words and link to `https://dmi.pravinmishra.com/s/Favourcloud.html`. Their deployed bytes match the submitted source.

| Week | Public article | Paragraph words | Anonymous HTTP |
|---|---|---:|---:|
| 08 | [Terraform and AWS](https://favourcloud.github.io/devops-micro-internship-pravinmishra/blog/week-08.html) | 964 | 200 |
| 09 | [Ansible deployments](https://favourcloud.github.io/devops-micro-internship-pravinmishra/blog/week-09.html) | 665 | 200 |
| 10 | [Azure DevOps pipelines](https://favourcloud.github.io/devops-micro-internship-pravinmishra/blog/week-10.html) | 769 | 200 |

The articles preserve the original published technical account, source attribution and assistance disclosures. The Week 10 copy was also inspected in the browser for readable layout and rendered links. This audit changes documentation/publication only; prior runtime validation remains in the [delivery record](COMPLETION-STATUS-20260926.md).

## Publication maintenance

The source is in [`docs/`](docs/). GitHub Pages publishes identical static files from the **root of `dmi-public-articles`**, with [successful deployment 36236351166](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/actions/runs/36236351166). This separate branch avoids the unrelated broken `Pravin-Mishra-Portfolio-Template` submodule in the main repository. No new workflow permissions were granted. Future article edits must update both `docs/` and that publication branch, followed by public byte/link checks.

## Items that remain honestly unverified

The exact unchecked statements are listed per assignment in the machine-readable audit. They fall into these groups:

- Required native editor/terminal/address-bar captures and full-name visibility across **every** required capture. Existing genuine screenshots and labeled recorded-output viewers remain distinguished. Missing original views cannot be reconstructed as authentic screenshots.
- Week 09 A3's exact two-host `curl -I` capture: the saved successful check is a URI GET, and that temporary lab has already been removed.
- Learner-personal manual execution, review and exact task sequence. Delegated work is disclosed and cannot establish that the learner personally performed those steps.
- The instructor-supplied Week 10 triage kit was not found in the previously reviewed sources. The functioning original replacement is explicitly identified as a replacement; it cannot truthfully satisfy “supplied files” or “only placeholders changed.”
- Original Azure DevOps PAT scope/expiry certification and blanket privacy assertions covering all historical evidence. The new staged changes receive credential scanning; that does not certify every old image or original credential setting.

These checkboxes remain open rather than misrepresenting completion. Evidence and substitution acceptance are the assessor's decisions. The six retained demos remain running under the learner's instruction.

## Recorded DMI result

The [dashboard receipt](dmi-assessment-20260926.json), observed on 26 September, still records an assessment dated **25 September**:

| Week | Recorded score | Dashboard status |
|---|---:|---|
| 08 | 190/190 | Complete |
| 09 | 110/190 | In progress |
| 10 | 50/170 | In progress |

DMI reports 9/14 completed weeks. Its published rules say completed assignment weeks and verified blogs are locked, while LinkedIn and attendance are recalculated. No rerun control was available on the inspected profile. The fixes must reach graded `main`; only a subsequent DMI assessment can establish changed marks.
