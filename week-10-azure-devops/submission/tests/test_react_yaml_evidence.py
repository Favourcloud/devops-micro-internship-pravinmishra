"""Read-only contracts for two genuine editor views, not pipeline execution."""
from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import unittest
from urllib.parse import urlsplit
import zlib


WEEK = Path(__file__).resolve().parents[2]
BRIEF = "assignment-03-automate-react-app-deployment-using-azure-devops-cicd.md"
RECEIPT = "react-yaml-2026-09-20.json"
REVISION = "b84d90ef20b525ce23440796166aeb2bf1f7b2b1"
SOURCE_HASH = "76d71dfba4b9f5772d652722fce9eb9582a724e55490df79d7350c7417fdeb47"
FILES = (
    ("assignment-03-screenshot-02-part-01-trigger-build.png", "0c743760609e71d4dfc3a6da6ae663dcec25c4fa0f213ac33aeead050a617db9", 489868),
    ("assignment-03-screenshot-02-part-02-test-publish-deploy.png", "2bde56853df7a73ab8879199741d0c68e8d26315d54b8c6966118789e18aaa49", 471675),
)
FALSE_FLAGS = {
    "pixels_edited_or_synthesized", "pipeline_source_edited",
    "human_visual_review_verified", "independent_secret_absence_certification",
    "azure_repos_import_verified", "pipeline_definition_created",
    "live_pipeline_run_verified", "live_deployment_verified",
    "assignment_completion_claimed", "pat_value_accessed", "cloud_operations_performed",
}


class ReactYamlEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw_record = (WEEK / "evidence" / RECEIPT).read_text()
        cls.record = json.loads(cls.raw_record)
        cls.brief = (WEEK / BRIEF).read_text()

    def test_allowlisted_metadata_has_no_runtime_or_human_claims(self):
        fields = {
            "schema_version", "assignment", "slot", "title", "status", "brief",
            "source_revision", "source_path", "source_sha256", "source_url",
            "evidence_scope", "method", "local_ocr", "limitations", "images",
        } | FALSE_FLAGS
        self.assertEqual(set(self.record), fields)
        self.assertEqual(self.raw_record, json.dumps(self.record, indent=2) + "\n")
        self.assertEqual(self.record["schema_version"], 1)
        self.assertEqual((self.record["assignment"], self.record["slot"]), (3, 2))
        self.assertEqual(self.record["title"], "Multi-Stage Pipeline YAML")
        self.assertEqual(self.record["brief"], BRIEF)
        self.assertEqual(self.record["status"], "captured_review_pending")
        self.assertEqual(self.record["evidence_scope"], "source_only_incomplete_configuration")
        for flag in FALSE_FLAGS:
            self.assertIs(self.record[flag], False)
        self.assertIn("TextEdit", self.record["method"])
        self.assertIn("read-only", self.record["method"])
        self.assertIn("not successful stage results", " ".join(self.record["limitations"]))
        self.assertEqual(self.record["local_ocr"], {
            "engine": "Apple Vision", "cpu_only_requested": True,
            "network_denied": True, "file_writes_denied": True,
        })

    def test_exact_original_png_hashes_chunks_and_dimensions(self):
        self.assertEqual(len(self.record["images"]), 2)
        for part, (image, (name, digest, size)) in enumerate(zip(self.record["images"], FILES), 1):
            with self.subTest(part=part):
                self.assertEqual(set(image), {
                    "part", "path", "captured_at", "sha256", "bytes", "dimensions",
                    "ocr_markers_checked", "minimum_marker_confidence",
                })
                self.assertEqual(image["part"], part)
                self.assertEqual(image["path"], "screenshots/" + name)
                self.assertEqual((image["sha256"], image["bytes"]), (digest, size))
                raw = (WEEK / image["path"]).read_bytes()
                self.assertEqual((hashlib.sha256(raw).hexdigest(), len(raw)), (digest, size))
                self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n")
                offset, kinds = 8, []
                while offset < len(raw):
                    self.assertGreaterEqual(len(raw) - offset, 12)
                    length = struct.unpack_from(">I", raw, offset)[0]
                    self.assertLessEqual(offset + length + 12, len(raw))
                    kind = raw[offset + 4:offset + 8]
                    payload = raw[offset + 8:offset + 8 + length]
                    crc = struct.unpack_from(">I", raw, offset + 8 + length)[0]
                    self.assertEqual(zlib.crc32(kind + payload) & 0xffffffff, crc)
                    if kind == b"IHDR":
                        self.assertEqual(length, 13)
                        self.assertEqual(struct.unpack_from(">II", payload), (2800, 1840))
                    if kind == b"IEND":
                        self.assertEqual(length, 0)
                    kinds.append(kind)
                    offset += length + 12
                self.assertEqual(offset, len(raw))
                self.assertEqual((kinds[0], kinds[-1]), (b"IHDR", b"IEND"))
                self.assertEqual((kinds.count(b"IHDR"), kinds.count(b"IEND")), (1, 1))
                self.assertIn(b"IDAT", kinds)
                self.assertEqual(image["dimensions"], [2800, 1840])
        self.assertEqual(len({image["sha256"] for image in self.record["images"]}), 2)

    def test_read_only_source_binding_is_not_an_azure_repos_import(self):
        self.assertEqual(self.record["source_revision"], REVISION)
        self.assertEqual(self.record["source_path"], "application-pipelines/react.azure-pipelines.yml")
        self.assertEqual(self.record["source_sha256"], SOURCE_HASH)
        source = (WEEK / self.record["source_path"]).read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(), SOURCE_HASH)
        url = urlsplit(self.record["source_url"])
        self.assertEqual((url.scheme, url.netloc), ("https", "github.com"))
        self.assertEqual(url.path, "/Favourcloud/devops-micro-internship-pravinmishra/blob/" + REVISION + "/week-10-azure-devops/" + self.record["source_path"])
        self.assertFalse(url.query or url.fragment or url.username or url.password)
        self.assertIn(b"__set_actual_deployment_date__", source)
        self.assertIn(b"__set_approved_react_ssh_connection_id__", source)
        self.assertIs(self.record["azure_repos_import_verified"], False)
        self.assertIs(self.record["pipeline_definition_created"], False)

    def test_actual_capture_order_and_required_ocr_markers(self):
        first, second = self.record["images"]
        self.assertEqual(first["ocr_markers_checked"], ["trigger:", "- stage: Build"])
        self.assertEqual(second["ocr_markers_checked"], ["- stage: Test", "- stage: Publish", "- stage: Deploy"])
        times = [datetime.fromisoformat(image["captured_at"]) for image in (first, second)]
        self.assertLess(times[0], times[1])
        for image, timestamp in zip((first, second), times):
            self.assertGreater(timestamp, datetime.fromisoformat("2026-09-20T00:40:38.025+00:00"))
            self.assertEqual(image["captured_at"][:10], "2026-09-20")
            self.assertEqual(image["minimum_marker_confidence"], 1.0)
        self.assertIs(self.record["human_visual_review_verified"], False)

    def test_only_one_exact_slot_is_filled_without_checklist_credit(self):
        section = re.search(r"^### Screenshot 2 — Multi-Stage Pipeline YAML\n(.*?)(?=\n---)", self.brief, re.M | re.S).group(1)
        self.assertEqual(re.findall(r"!\[[^\]]*\]\(([^)]+)\)", section), [image["path"] for image in self.record["images"]])
        self.assertIn("one numbered source slot", section)
        self.assertIn("unset placeholders", section)
        self.assertIn("Human visual/privacy review is pending.", section)
        self.assertIn("No checklist item is completed", section)
        self.assertIn("not successful stage results", section)
        self.assertEqual(self.brief.count("Add your screenshot here."), 5)
        self.assertEqual(len(re.findall(r"(?m)^[-*] \[ \] ", self.brief)), 21)
        self.assertNotRegex(self.brief, r"(?m)^[-*] \[[xX]\] ")
        self.assertEqual(self.brief.count("<!-- BEGIN WEEK10 CAPTURE A3-S2 -->"), 1)
        self.assertEqual(self.brief.count("<!-- END WEEK10 CAPTURE A3-S2 -->"), 1)

    def test_current_counts_and_human_review_remain_partial(self):
        current = json.loads((WEEK / "evidence/current.json").read_text())
        self.assertEqual([current[key] for key in ("numbered_required", "numbered_captured", "numbered_missing", "raw_images")], [36, 10, 26, 13])
        self.assertEqual(current["captured_slots"], [[1, slot] for slot in range(1, 8)] + [[2, 1], [2, 3], [3, 2]])
        self.assertEqual(current["bundles"][-1], RECEIPT)
        self.assertEqual(current["human_review_receipts"], ["a1-human-review-2026-09-19.json"])
        for flag in ("human_visual_review_verified", "assignment_completion_claimed", "separate_linkedin_image_captured"):
            self.assertIs(current[flag], False)
        self.assertEqual(len(list((WEEK / "screenshots").glob("*.png"))), 13)

    def test_unapproved_a3_slots_and_answer_claims_still_fail_closed(self):
        spec = importlib.util.spec_from_file_location("react_brief_contract", WEEK / "submission/brief_contract.py")
        contract = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(contract)
        raw = self.brief.encode()
        for changed in (
            raw.replace(b"A3-S2", b"A3-S3"),
            raw.replace(b"Add your screenshot here.", b"<!-- BEGIN WEEK10 CAPTURE A3-S1 -->\nInvented.\n<!-- END WEEK10 CAPTURE A3-S1 -->", 1),
            re.sub(rb"(?m)^([-*]) \[ \]", rb"\1 [x]", raw, count=1),
        ):
            with self.subTest(length=len(changed)), self.assertRaises(ValueError):
                contract.restore_original_prompts(changed, BRIEF)

    def test_current_docs_identify_the_limited_native_capture(self):
        gallery = (WEEK / "evidence/README.md").read_text()
        overview = (WEEK / "README.md").read_text()
        self.assertIn(RECEIPT, gallery)
        self.assertIn("TextEdit", gallery)
        self.assertIn("26 numbered slots", gallery)
        self.assertIn("thirteen original PNGs", gallery)
        self.assertIn("A3 screenshot 2", overview)
        self.assertIn("26 numbered slots", overview)
        self.assertIn("No assignment is complete", gallery)
        self.assertIn("shared PAT is left unchanged", overview)


if __name__ == "__main__":
    unittest.main()
