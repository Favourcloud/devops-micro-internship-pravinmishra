#!/usr/bin/env python3.13
"""Generate sanitized local-only validation evidence; no real Terraform calls."""
import argparse
from datetime import datetime, timezone
from fnmatch import fnmatch
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def is_private_artifact(relative):
    return (any(part in {".review-data", "__pycache__", ".terraform"} or part.startswith(".review-run-")
                for part in relative.parts)
            or any(fnmatch(relative.name, pattern) for pattern in
                   ("*.pyc", "*.tfstate*", "*.tfplan*", "*.binary", "*.log", "*.tfvars", "*.tfvars.json", "crash.*", "tfplan*.json")))


class CountedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subtests = 0

    def addSubTest(self, test, subtest, error):
        self.subtests += 1
        super().addSubTest(test, subtest, error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, help="new report path; parent must exist")
    args = parser.parse_args()
    os.umask(0o077)
    os.chdir(ROOT)
    output = Path(args.report).absolute()
    # Reserve the output exclusively; this also makes the first-run documentation
    # link check possible before the validation record has been filled.
    with output.open("x") as destination:
        syntax = subprocess.run(["/bin/bash", "-n", "AI Assignment/tf-drift-check.sh"], capture_output=True)
        suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py")
        stream = io.StringIO()
        result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=CountedResult).run(suite)
        sources = [path for path in ROOT.rglob("*") if path.is_file()
                   and not is_private_artifact(path.relative_to(ROOT))
                   and path != output and path.relative_to(ROOT).as_posix() != "reports/local-validation.json"]
        sources.append(ROOT.parent / "assignment-06-ai-assisted-terraform-drift-and-policy-review.md")
        hashes = {os.path.relpath(path, ROOT): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(sources)}
        reports = {}
        for filename, expected_status in (("drift-detected-report.txt", "FAIL"), ("resolved-report.txt", "HEALTHY")):
            path = ROOT / "reports" / filename
            text = path.read_text()
            expected_hash = hashlib.sha256((ROOT / "fixtures" / ("detected.json" if expected_status == "FAIL" else "clean.json")).read_bytes()).hexdigest()
            verified = (text.startswith("SYNTHETIC FIXTURE DEMONSTRATION")
                        and "Mode: FIXTURE\n" in text and f"Overall Status: {expected_status}\n" in text
                        and f"Plan SHA256: {expected_hash}\n" in text)
            reports[filename] = {"fixture_only": True, "status": expected_status, "source_hash_matches": verified}
        passed = result.wasSuccessful() and syntax.returncode == 0 and all(item["source_hash_matches"] for item in reports.values())
        manifest = json.loads((ROOT / "screenshots/manifest.json").read_text())
        captured = sorted(item["number"] for item in manifest["screenshots"])
        pending = sorted(set(range(1, 20)) - set(captured))
        evidence = {
            "evidence_class": "OFFLINE REGRESSION AND EVIDENCE-INTEGRITY VALIDATION — DOES NOT RE-RUN CLOUD OR CLAUDE",
            "student": "Eze Favour",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "status": "PASS" if passed else "FAIL",
            "reproduction_command": "python3.13 tests/run_validation.py --report NEW_PATH",
            "equivalent_unittest_command": "python3.13 -m unittest discover -s tests -v",
            "tests_run": result.testsRun, "subtests_run": result.subtests,
            "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped),
            "bash_syntax_command": 'bash -n "AI Assignment/tf-drift-check.sh"',
            "bash_syntax_exit": syntax.returncode,
            "tools": {"python": sys.version.split()[0], "jq": subprocess.check_output(["jq", "--version"], text=True).strip()},
            "fixture_reports": reports,
            "source_file_count": len(hashes), "source_sha256": hashes,
            "source_parity": json.loads((ROOT / "tests/assignment-source.json").read_text()),
            "screenshot_numbers": {"captured": captured, "pending": pending},
            "limitations": [
                "This test run invokes no real Terraform binary; plan/show exit handling uses fake executables in discarded project-local directories.",
                "This test run makes no cloud or Claude API calls. Separate reports/live records contain actual historical operations and failures; integrity checks do not reperform them.",
                "Hook tests use JSON stdin and exit codes only, not a runtime Claude apply attempt.",
                "Earlier Claude failures are preserved separately. Dated clean/risk/final review and native-denial records document later verified runtime events; this offline run does not repeat them.",
                f"{len(captured)} genuine screenshots are recorded; pending numbered slots: {', '.join(map(str, pending)) or 'none'}. LinkedIn publication/URL/screenshot remains pending.",
                "Historical live-preflight.json remains unchanged. Actual scoped creation, unapplied proposal, technical reset and verified cleanup are recorded separately in reports/live/operations.json.",
                "The dated September 16 human record documents the later reject-public-SSH decision. Copilot executed authorized operations; manual human Terraform execution is not claimed.",
                "The September 16 cycle record documents actual final review and verified cleanup. Operator non-attestation flags do not replace separately recorded human/Claude evidence.",
                "HEALTHY means no findings in the stated limited evidence, never global safety or mutation authorization. Both dated labs were deleted; historical reports are not current state.",
                "Hashes identify bytes, not a signed attestation. Raw plans, state, private bindings and logs are excluded."
            ],
        }
        json.dump(evidence, destination, indent=2, ensure_ascii=False)
        destination.write("\n")
    print(f"{evidence['status']}: {result.testsRun} tests, {result.subtests} subtests; bash syntax exit {syntax.returncode}; {len(hashes)} source hashes.")
    if not passed:
        print(stream.getvalue(), file=sys.stderr)
    return 0 if passed else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as error:
        print("Validation could not complete: " + type(error).__name__, file=sys.stderr)
        sys.exit(1)
