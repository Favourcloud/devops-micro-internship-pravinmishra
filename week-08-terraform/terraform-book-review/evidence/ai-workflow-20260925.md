# Recorded AI workflow and dependency candidate — 25 September 2026

A5 now has **15/28 screenshot slots**, including recorded AI improvement, review and troubleshooting in slots 26–28. These are original browser captures of clearly labeled saved-output pages, not a live terminal. The actual CLI response text, generated diffs and errors are preserved in [sanitized results](ai-workflow-results-20260925.json); [provenance](ai-capture-provenance-20260925.json) records their hashes. Codex operated under user delegation. No manual learner execution, deployment, final architecture approval or new grade is claimed.

## Verified work and corrections

- **Terraform improvement:** Claude's `terraform-engineer` role performed native Read then Edit to restrict hostname labels to 63 characters and full hostnames to 253. Native PostToolUse ran the protected six-stage offline Terraform validator successfully. Independent tests of the actual HCL declaration passed all 13 valid/invalid boundary cases. The CLI stopped at its budget before writing a final summary; the edit and hook had completed.
- **Structured review:** the `architecture-security-reviewer` main session produced PASS/WARN/FAIL findings on routing, security-group chains, database privacy, HA and cost. It reached 1,024 output tokens and then its budget limit, cutting off the final recommended-check list. The captured partial review meets the focused screenshot criterion; it does not close Task 8's final review. Operator inspection confirmed all three secret variables are already sensitive and ephemeral. Hostname validation rejects the auth-token/URL inputs the reviewer speculated about. Those are resolved source checks, not deployed proof.
- **Troubleshooting:** the exact pinned source archive failed on four tracked but unselected symlinks in `backend/node_modules/.bin`. The first model attempt had no native Read and its Edit failed; no source changed. The second added an exact allowlist, but failed two existing raw-path tests and incorrectly rejected the root directory. Codex restored the original raw-path checks and root-directory handling, retained the exact source-root/path/target/type/zero-size allowlist, and preserved duplicate/count/size/hash checks. All12 existing and seven new archive tests passed, including verification of all 35 selected files in the actual archive. No link or bundled dependency was extracted. Terraform hook success alone did not establish Python correctness.

Both named roles were invoked as main CLI sessions. No delegated subagent execution is claimed. The paid starter kit remains private. The original public runtime, Terraform, hooks, runner, locks, agent templates and trust seals remain unchanged; reviewed local changes are supplied as [candidate patches](candidates/README.md).

## Dependency remediation

The [complete audit/build record](dependency-candidate-20260925.json) and [candidate lockfiles](candidates/dependencies) document a separate candidate derived from pinned upstream commit `84280063bea7ccd5144dafa2b969ec4e2e69ffbb`. Of 35 verified selected files, only the four package manifests/locks changed; all 31 other application/configuration/assets remain byte-identical.

| Audit snapshot | Original | Candidate |
|---|---:|---:|
| Frontend | 16: 2 critical, 9 high, 3 moderate, 2 low | 0 known findings |
| Backend | 11: 7 high, 4 moderate | 0 known findings |

Next and eslint-config-next moved to 15.5.26; dependencies were updated within declared major ranges. A scoped Next→PostCSS 8.5.23 override fixes the remaining PostCSS advisories. A Sequelize→uuid 11.1.1 override removes the remaining backend advisory while retaining Sequelize 6. The uuid override crosses a major; seven offline package compatibility checks passed, including CommonJS v1/v4 resolution, UUIDV4 model defaults, SQL generation, mysql2 load, bcrypt, JWT and Express APIs. No database connection was attempted.

Both `npm ci` runs used `--ignore-scripts`. The Next production build, lint/type check and seven-page generation succeeded in the pinned official Node 22 image with `--network none`, on Linux x64. The build uses `https://book-review.invalid`; it is **not a deployable artifact**. The Debian container does not establish a reviewed Ubuntu 24.04 AMI. npm also reported deprecated/unsupported eslint 9.39.5 and dottie 2.0.7. A zero registry-audit count does not prove application security or runtime compatibility.

## Budget

Additional approved Bedrock allowance: **$0.50**. Cumulative regional estimate: **$0.452212365**, including the earlier MCP/offline workflow and all four new attempts; approximately **$0.0478** remains before taxes/final AWS billing. No more model calls were made. The CLI budget is checked after responses and was exceeded within individual sessions; it is not an AWS billing cap. Budget-stop records had incomplete `usage` fields, so accounting uses the greater cumulative model/CLI regional estimate. See [cost record](ai-workflow-cost-20260925.json). This is separate from the initial approximately $0.44 setup usage.

## Remaining release and assignment work

The vulnerable frozen source lock is still the release baseline. The clean dependency candidate must be integrated into a newly reviewed source/build identity and runtime verifier; changing dependency files alone cannot satisfy the unchanged-source artifact contract. `runtime_release_authorized` remains false.

Still required: supported Ubuntu AMI, authorized HTTPS hostname/certificate, production origin-bound artifact, CA/secret-version/Router TLS inputs, reviewed costed plan and deployment budget, actual cloud/runtime/browser/HA/replica/cleanup evidence, final review, all 15 learner reflections, and mandatory publication. Thirteen A5 images remain missing: 9–13 and 18–25. Week 08 totals **104/118** occupied slots, **14 missing**. Last observed DMI score remains 70/190, with no regrade claimed.
