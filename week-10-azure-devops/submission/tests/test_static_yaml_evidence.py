"""Read-only checks of the later three-view, single-slot source capture."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import struct
import unittest
from urllib.parse import parse_qs, urlsplit
import zlib

WEEK = Path(__file__).resolve().parents[2]
BRIEF = "assignment-02-deploy-a-static-website-to-aws-ec2-using-an-azure-devops-cicd-pipeline.md"
FILES = [
    ("assignment-02-screenshot-03-part-01-trigger-pool-variables.png", "cf6af1a769c277b996d4bd433fe0d8afe3cd8840bcdd48ef7420f5329fbbb047", 1026424),
    ("assignment-02-screenshot-03-part-02-pipeline-information.png", "26c88232e068b19c63296e4074e20eae420ae4cf941ebfc5a5934007b05ba922", 1166683),
    ("assignment-02-screenshot-03-part-03-ssh-tasks.png", "2261932f69f87e2da777e3f724d0c49f02830572dfa2a781db79add9f4a25f25", 707248),
]


class StaticYamlEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = json.loads((WEEK / "evidence/static-yaml-2026-09-19.json").read_text())
        cls.current = json.loads((WEEK / "evidence/current.json").read_text())

    def test_allowlisted_source_only_schema(self):
        self.assertEqual(set(self.record), {"schema_version", "assignment", "slot", "title", "status", "brief", "source_revision", "evidence_scope", "method", "pixels_edited_or_synthesized", "human_visual_review_verified", "sensitive_screen_marker_found", "live_deployment_verified", "assignment_completion_claimed", "limitations", "images"})
        self.assertEqual(self.record["schema_version"], 1)
        self.assertEqual((self.record["assignment"], self.record["slot"], self.record["title"]), (2, 3, "Azure Pipelines YAML"))
        self.assertEqual(self.record["brief"], BRIEF)
        self.assertEqual(self.record["status"], "captured_review_pending")
        self.assertEqual(self.record["evidence_scope"], "source_only_incomplete_configuration")
        for key in ("pixels_edited_or_synthesized", "human_visual_review_verified", "sensitive_screen_marker_found", "live_deployment_verified", "assignment_completion_claimed"):
            self.assertIs(self.record[key], False)
        self.assertIn("placeholder", " ".join(self.record["limitations"]))
        self.assertIn("not three slots", " ".join(self.record["limitations"]))
        for image in self.record["images"]:
            self.assertEqual(set(image), {"part", "path", "captured_at", "sha256", "bytes", "dimensions", "source_url", "ocr_markers_checked"})

    def test_exact_distinct_original_images(self):
        self.assertEqual(len(self.record["images"]), 3)
        for part, (image, expected) in enumerate(zip(self.record["images"], FILES), 1):
            name, digest, size = expected
            self.assertEqual(image["part"], part)
            self.assertEqual(image["path"], "screenshots/" + name)
            self.assertEqual(image["sha256"], digest)
            self.assertEqual(image["bytes"], size)
            raw = (WEEK / image["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
            self.assertEqual(len(raw), size)
        self.assertEqual(len({i["sha256"] for i in self.record["images"]}), 3)

    def test_png_structure_crc_and_dimensions(self):
        for image in self.record["images"]:
            with self.subTest(part=image["part"]):
                raw = (WEEK / image["path"]).read_bytes()
                self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n")
                offset, kinds = 8, []
                while offset < len(raw):
                    self.assertGreaterEqual(len(raw) - offset, 12)
                    length = struct.unpack_from(">I", raw, offset)[0]
                    end = offset + length + 12
                    self.assertLessEqual(end, len(raw))
                    kind = raw[offset + 4:offset + 8]
                    payload = raw[offset + 8:offset + 8 + length]
                    self.assertEqual(zlib.crc32(kind + payload) & 0xffffffff, struct.unpack_from(">I", raw, offset + 8 + length)[0])
                    if kind == b"IHDR":
                        self.assertEqual(length, 13)
                        self.assertEqual(list(struct.unpack_from(">II", payload)), [3584, 1884])
                    if kind == b"IEND":
                        self.assertEqual(length, 0)
                    kinds.append(kind)
                    offset = end
                self.assertEqual((kinds[0], kinds[-1]), (b"IHDR", b"IEND"))
                self.assertEqual(kinds.count(b"IHDR"), 1)
                self.assertEqual(kinds.count(b"IEND"), 1)
                self.assertIn(b"IDAT", kinds)
                self.assertEqual(image["dimensions"], [3584, 1884])

    def test_source_revision_safe_urls_and_later_timing(self):
        revision = "6b38993a18f75c2588803a42b6e7790c95e95b81"
        self.assertEqual(self.record["source_revision"], revision)
        for image in self.record["images"]:
            path = Path(image["path"])
            self.assertFalse(path.is_absolute())
            self.assertNotIn("..", path.parts)
            self.assertTrue((WEEK / path).is_file())
            url = urlsplit(image["source_url"])
            self.assertEqual((url.scheme, url.netloc, url.path), ("https", "dev.azure.com", "/aneneeze2021/DMI-Week10/_git/Azure-Static-Website"))
            self.assertFalse(url.fragment)
            self.assertEqual(parse_qs(url.query), {"path": ["/azure-pipelines.yml"], "version": ["GC" + revision], "_a": ["contents"]})
            self.assertGreater(datetime.fromisoformat(image["captured_at"]), datetime.fromisoformat("2026-09-19T09:04:28+00:00"))
            self.assertEqual(image["captured_at"][:10], "2026-09-19")

    def test_required_source_sections_are_covered_without_runtime_claims(self):
        markers = {m for i in self.record["images"] for m in i["ocr_markers_checked"]}
        self.assertEqual(markers, {"trigger", "variables", "poolName", "checkout", "Pipeline information", "persistCredentials", "CopyFilesOverSSH", "SSH@", "Verify checksums", "static verify"})
        self.assertIs(self.record["live_deployment_verified"], False)
        self.assertIs(self.record["human_visual_review_verified"], False)
        source = (WEEK / "application-pipelines/static.azure-pipelines.yml").read_text()
        self.assertIn("__set_approved_static_ssh_connection_id__", source)

    def test_three_parts_belong_to_only_one_exact_brief_slot(self):
        text = (WEEK / BRIEF).read_text()
        marker = "A2-S3"
        self.assertEqual(text.count("<!-- BEGIN WEEK10 CAPTURE " + marker + " -->"), 1)
        self.assertEqual(text.count("<!-- END WEEK10 CAPTURE " + marker + " -->"), 1)
        section = re.search(r"^### Screenshot 3 — Azure Pipelines YAML\n(.*?)(?=\n---)", text, re.M | re.S)
        self.assertIsNotNone(section)
        self.assertNotIn("Add your screenshot here.", section.group(1))
        self.assertEqual(re.findall(r"!\[[^\]]*\]\(([^)]+)\)", section.group(1)), [i["path"] for i in self.record["images"]])
        self.assertIn("one numbered slot", section.group(1))
        self.assertIn("unset placeholder", section.group(1))
        self.assertIn("Human visual/privacy review is pending.", section.group(1))
        for brief in WEEK.glob("assignment-*.md"):
            if brief.name != BRIEF:
                self.assertNotIn(marker, brief.read_text())

    def test_cumulative_counts_preserve_original_bundle_and_snapshot(self):
        self.assertEqual(set(self.current), {"schema_version", "status", "numbered_required", "numbered_captured", "numbered_missing", "raw_images", "separate_linkedin_image_captured", "assignment_completion_claimed", "human_visual_review_verified", "captured_slots", "bundles"})
        self.assertEqual((self.current["schema_version"], self.current["status"]), (1, "partial_captures_review_pending"))
        self.assertEqual((self.current["numbered_required"], self.current["numbered_captured"], self.current["numbered_missing"], self.current["raw_images"]), (36, 4, 32, 6))
        self.assertEqual(self.current["captured_slots"], [[1, 1], [1, 7], [2, 1], [2, 3]])
        self.assertEqual(self.current["bundles"], ["captures-2026-09-19.json", "static-yaml-2026-09-19.json"])
        for key in ("separate_linkedin_image_captured", "assignment_completion_claimed", "human_visual_review_verified"):
            self.assertIs(self.current[key], False)
        original = json.loads((WEEK / "evidence/captures-2026-09-19.json").read_text())
        snapshot = json.loads((WEEK / "submission/status.json").read_text())
        self.assertEqual(original["numbered_captured"], 3)
        self.assertEqual(snapshot["screenshots"]["numbered_captured"], 0)
        slots = {(i["assignment"], i["slot"]) for i in original["captures"]} | {(self.record["assignment"], self.record["slot"])}
        self.assertEqual(slots, {tuple(s) for s in self.current["captured_slots"]})
        self.assertEqual(len(original["captures"]) + len(self.record["images"]), self.current["raw_images"])


if __name__ == "__main__":
    unittest.main()
