# Reviewed local candidates — not a release

These files preserve the frozen evidence baseline while making the tested corrections reviewable. Apply each patch only to a fresh copy of the current Book Review project (`patch -p0 < upstream.patch`, then the hostname patch). Do not apply the model's rejected diff from the transcript. The final upstream patch includes Codex corrections after failed model regressions; the hostname patch is Claude's accepted edit.

- `upstream.patch`: exact pinned-source excluded-link handling; strict artifact link rejection and original raw-path guards remain.
- `hostname.patch`: DNS label/full-hostname bounds.
- `test_archive_candidate.py`: seven adversarial/real-archive checks. Set `A5_CANDIDATE_PROJECT` to the patched copy and `A5_SOURCE_ARCHIVE` to the verified pinned archive, then run this test and the copy's existing `tests/test_upstream.py`. Expected: 7+12 passing tests.
- `hostname-boundaries.tftest.hcl`: 13 tests for a temporary provider-free Terraform module containing only the patched `public_hostname` declaration. The exact successful outputs are in `hostname-validation.json`. Run init with backend disabled, then Terraform test with networking denied.
- `dependencies/{frontend,backend}/{package.json,package-lock.json}`: updated manifests/locks for a separate 35-file verified application copy. Do not overwrite the frozen source lock or claim that the unchanged-source verifier accepts these files.
- `backend-compatibility-check.cjs`: copy into the candidate backend after `npm ci --ignore-scripts`; run under Node 22 with network disabled. It tests package APIs and generates SQL without connecting to MySQL.

The candidate is not a deployment artifact or release authorization. Full provenance, exact container image, audit snapshots, versions, hashes and limitations are in the parent dependency-candidate report. The private starter kit, credentials, node_modules and generated build are not included.
