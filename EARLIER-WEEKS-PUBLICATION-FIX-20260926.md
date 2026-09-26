# Earlier-week publication fixes — 26 September 2026

The three missing publication cells for Weeks 06–07 now contain verified public URLs. These address **70 potential publication points** in the last recorded DMI result; only an external DMI review can award them.

| Submission | Published result | Verification |
|---|---|---|
| Week 06 AWS blog | [High Availability Needs Measurements](https://favourcloud.github.io/devops-micro-internship-pravinmishra/blog/week-06.html) | Anonymous HTTP 200; 653 paragraph words; actual own-badge hyperlink; deployed bytes match source |
| Week 07 Azure blog | [Azure Architecture and the Evidence Needed to Prove It](https://favourcloud.github.io/devops-micro-internship-pravinmishra/blog/week-07.html) | Anonymous HTTP 200; 746 paragraph words; actual own-badge hyperlink; deployed bytes match source; browser layout inspected |
| Week 07 LinkedIn | [Published post](https://www.linkedin.com/posts/eze-favour-52732752_dmibypravinmishra-devops-agenticai-share-7509568835549700096-c4Lf/) | LinkedIn success confirmation, canonical copy-link resolution, matching author/content, four actual mentor profile links, required P.S. and hashtags |

The final writing is in [`publication-review/published/`](publication-review/published/). The AWS article preserves the actual four failed probes, controlled evacuation scope and verified temporary-lab cleanup. The Azure article is an architecture/security reflection with its evidence limitations disclosed. Both identify Codex assistance and avoid unsupported personal-manual or full-deployment claims.

The root README's Weekly Progress table now has a canonical `/posts/` LinkedIn URL and a blog URL for **every week from 00 through 10**. Previously credited Week 00–05 blog links and Week 00–06 LinkedIn links are preserved. All five GitHub Pages articles for Weeks 06–10 were checked together; the three earlier articles are unchanged.

## Evidence correction

The Week 07 inventory previously counted 22 existing files out of 60 screenshot references without establishing image quality. The new dimension audit found that **all 22 are 1 × 1 pixel, 68-byte placeholders**; the other 38 files are absent. A focused search for matching screenshots in the available workspace and Downloads copies found no usable originals. No authentic deployment proof can be inferred from these files.

The [Week 07 README](week-07-azure-cloud/README.md) and A6/A7 briefs now say so. No placeholder was turned into a fabricated capture, and no unsupported technical or manual checkbox was marked complete. Existing assignment marks do not establish technical completeness.

## Attendance and last recorded scores

The public DMI review remains dated **25 September 2026**:

| Week | Recorded score | Missing publication marks addressed here | Attendance still recorded |
|---|---:|---:|---:|
| 04 | 180/190 | None; both publications already credited | 20/30 |
| 05 | 160/170 | None; both publications already credited | 20/30 |
| 06 | 170/210 | Blog: 30 | 20/30 |
| 07 | 160/210 | Blog: 30; LinkedIn: 10 | 20/30 |

The remaining **40 attendance points** come from four uncredited 10-point slots. The public page does not identify the specific slots or establish whether they were missed or recorded incorrectly. A factual verification request has been prepared for the cohort team; no attendance correction, message delivery or new score is claimed in this commit. Only the team can reconcile its attendance source.

## Publication source and receipts

GitHub Pages publishes `dmi-public-articles` at its root. The matching source is in [`docs/`](docs/). [Deployment 36237564719](https://github.com/Favourcloud/devops-micro-internship-pravinmishra/actions/runs/36237564719) succeeded. Future changes must synchronize both sources.

- [Public article checks](publication-review/evidence/2026-09-26-earlier-weeks/pages-public-checks.json)
- [LinkedIn publication and mentor links](publication-review/evidence/2026-09-26-earlier-weeks/linkedin-week07.json)
- [Image dimensions and hashes](publication-review/evidence/2026-09-26-earlier-weeks/week07-image-audit.json)
- [Observed earlier-week DMI breakdown](publication-review/evidence/2026-09-26-earlier-weeks/earlier-dmi-scores.json)

The six retained cloud demonstrations remain running under the learner's existing instruction. This publication fix performs no cloud deployment or cleanup.
