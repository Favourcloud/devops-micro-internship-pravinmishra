"""Credential-free checks of genuine attached bytes, placement and bounded claims."""
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
EXPECTED = {
    (1, 1): ("assignment-01-screenshot-01-agent-pool.png", "f2a7640a96c5d3a2136ed1ee3882c762863ea189e1063253345552ebada9a128"),
    (1, 7): ("assignment-01-screenshot-07-linux-pipeline-output.png", "956e610d09f104a667dd5e7dad3d41ea09db8d7334d725339df6f63fd8480496"),
    (2, 1): ("assignment-02-screenshot-01-azure-repos.png", "2270ea7c29078822be81fe5ecf2359bc308c38895a9ab4becef04c6fdb77137e"),
}


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = json.loads((WEEK / "evidence/captures-2026-09-19.json").read_text())
        cls.captures = cls.index["captures"]

    def test_allowlisted_schema_and_pending_human_claims(self):
        self.assertEqual(set(self.index), {"schema_version", "status", "snapshot_as_of_utc", "supplements_frozen_source_commit", "numbered_required", "numbered_captured", "numbered_missing", "separate_linkedin_image_captured", "assignment_completion_claimed", "human_visual_review_verified", "captures"})
        self.assertEqual(self.index["schema_version"], 1)
        self.assertEqual(self.index["status"], "partial_captures_review_pending")
        self.assertEqual((self.index["numbered_required"], self.index["numbered_captured"], self.index["numbered_missing"]), (36, 3, 33))
        for flag in ("separate_linkedin_image_captured", "assignment_completion_claimed", "human_visual_review_verified"):
            self.assertIs(self.index[flag], False)
        fields = {"assignment", "slot", "title", "captured_at", "sha256", "bytes", "dimensions", "source_url", "method", "pixels_edited_or_synthesized", "local_ocr_markers_checked", "ocr_sensitive_screen_marker_found", "human_visual_review_verified", "limitations", "path", "brief"}
        for item in self.captures:
            self.assertEqual(set(item), fields)
            for flag in ("pixels_edited_or_synthesized", "ocr_sensitive_screen_marker_found", "human_visual_review_verified"):
                self.assertIs(item[flag], False)
            self.assertTrue(item["limitations"])
            self.assertTrue(item["local_ocr_markers_checked"])

    def test_exact_captures_titles_and_files(self):
        self.assertEqual([(i["assignment"], i["slot"]) for i in self.captures], list(EXPECTED))
        later = json.loads((WEEK / "evidence/static-yaml-2026-09-19.json").read_text())
        fresh = json.loads((WEEK / "evidence/a1-vm-ssh-2026-09-19.json").read_text())
        interactive = json.loads((WEEK / "evidence/a1-interactive-2026-09-19.json").read_text())
        react = json.loads((WEEK / "evidence/react-yaml-2026-09-20.json").read_text())
        expected_files = {v[0] for v in EXPECTED.values()} | {Path(i["path"]).name for i in later["images"]} | {Path(i["path"]).name for i in fresh["captures"]} | {Path(i["path"]).name for i in interactive["captures"]} | {Path(i["path"]).name for i in react["images"]}
        self.assertEqual({p.name for p in (WEEK / "screenshots").glob("*.png")}, expected_files)
        for item in self.captures:
            name, digest = EXPECTED[(item["assignment"], item["slot"])]
            self.assertEqual(item["path"], "screenshots/" + name)
            self.assertEqual(item["sha256"], digest)
            brief = (WEEK / item["brief"]).read_text()
            title = re.search(r"^#{3,4} Screenshot " + str(item["slot"]) + r" — (.+)$", brief, re.M)
            self.assertIsNotNone(title)
            self.assertEqual(title.group(1), item["title"])

    def test_original_png_hash_crc_dimensions_and_complete_structure(self):
        for item in self.captures:
            with self.subTest(path=item["path"]):
                raw = (WEEK / item["path"]).read_bytes()
                self.assertEqual(len(raw), item["bytes"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), item["sha256"])
                self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n")
                offset, chunks = 8, []
                while offset < len(raw):
                    self.assertGreaterEqual(len(raw) - offset, 12)
                    length = struct.unpack_from(">I", raw, offset)[0]
                    end = offset + 12 + length
                    self.assertLessEqual(end, len(raw))
                    kind = raw[offset + 4:offset + 8]
                    payload = raw[offset + 8:offset + 8 + length]
                    crc = struct.unpack_from(">I", raw, offset + 8 + length)[0]
                    self.assertEqual(zlib.crc32(kind + payload) & 0xffffffff, crc)
                    if kind == b"IHDR":
                        self.assertEqual(length, 13)
                        self.assertEqual(list(struct.unpack_from(">II", payload)), item["dimensions"])
                    if kind == b"IEND":
                        self.assertEqual(length, 0)
                    chunks.append(kind)
                    offset = end
                self.assertEqual(chunks[0], b"IHDR")
                self.assertEqual(chunks[-1], b"IEND")
                self.assertEqual(chunks.count(b"IHDR"), 1)
                self.assertEqual(chunks.count(b"IEND"), 1)
                self.assertIn(b"IDAT", chunks)
                self.assertEqual(item["dimensions"], [3584, 2064])

    def test_manifest_matches_index_without_current_online_claim(self):
        manifest = json.loads((WEEK / "self-hosted-agent/evidence/manifest.json").read_text())
        self.assertIs(manifest["live_verified"], False)
        self.assertEqual([s["slot"] for s in manifest["screenshots"] if s["captured"]], list(range(1, 8)))
        for item in self.captures:
            if item["assignment"] == 1:
                slot = manifest["screenshots"][item["slot"] - 1]
                for key in ("path", "sha256", "captured_at"):
                    self.assertEqual(slot[key], item[key])
                self.assertEqual(slot["run_url"], item["source_url"])

    def test_captures_follow_zero_image_snapshot_and_historical_cleanup(self):
        self.assertEqual(self.index["snapshot_as_of_utc"], "2026-09-19T08:15:30Z")
        self.assertEqual(self.index["supplements_frozen_source_commit"], "80c16e402deca4bf0004d32619e6babba3095096")
        snapshot = json.loads((WEEK / "submission/status.json").read_text())
        self.assertEqual(snapshot["screenshots"]["numbered_captured"], 0)
        cutoff = datetime.fromisoformat(self.index["snapshot_as_of_utc"].replace("Z", "+00:00"))
        for item in self.captures:
            self.assertGreater(datetime.fromisoformat(item["captured_at"]), cutoff)
            self.assertEqual(item["captured_at"][:10], "2026-09-19")

    def test_images_are_embedded_under_only_their_exact_requirement(self):
        for brief in WEEK.glob("assignment-*.md"):
            expected = [i for i in self.captures if i["brief"] == brief.name]
            text = brief.read_text()
            later_slot = int(brief.name.startswith("assignment-02-")) + 5 * int(brief.name.startswith("assignment-01-")) + int(brief.name.startswith("assignment-03-"))
            self.assertEqual(text.count("<!-- BEGIN WEEK10 CAPTURE "), len(expected) + later_slot)
            self.assertEqual(text.count("<!-- END WEEK10 CAPTURE "), len(expected) + later_slot)
            for item in expected:
                marker = f"A{item['assignment']}-S{item['slot']}"
                section = re.search(r"^#{3,4} Screenshot " + str(item["slot"]) + r" — [^\n]+\n(.*?)(?=\n---)", text, re.M | re.S)
                self.assertIsNotNone(section)
                block = section.group(1)
                self.assertNotIn("Add your screenshot here.", block)
                self.assertIn("<!-- BEGIN WEEK10 CAPTURE " + marker + " -->", block)
                self.assertIn("<!-- END WEEK10 CAPTURE " + marker + " -->", block)
                self.assertEqual(re.findall(r"!\[[^\]]*\]\(([^)]+)\)", block), [item["path"]])
                if item["assignment"] == 1:
                    self.assertIn("Full-size content/privacy review is user-attested", block)
                    self.assertIn("(evidence/a1-human-review-2026-09-19.json)", block)
                else:
                    self.assertIn("Human visual/privacy review is pending.", block)

    def test_safe_paths_source_urls_and_gallery_links(self):
        for item in self.captures:
            for field in ("path", "brief"):
                path = Path(item[field])
                self.assertFalse(path.is_absolute())
                self.assertNotIn("..", path.parts)
                self.assertTrue((WEEK / path).is_file())
            url = urlsplit(item["source_url"])
            self.assertEqual((url.scheme, url.netloc), ("https", "dev.azure.com"))
            self.assertTrue(url.path.startswith("/aneneeze2021/"))
            self.assertFalse(url.fragment)
            self.assertLessEqual(set(parse_qs(url.query)), {"poolId", "view", "buildId", "path"})
        gallery = WEEK / "evidence/README.md"
        for link in re.findall(r"\]\(([^)]+)\)", gallery.read_text()):
            target = (gallery.parent / link.split("#", 1)[0]).resolve()
            self.assertTrue(target.is_relative_to(WEEK.resolve()))
            self.assertTrue(target.is_file(), link)


if __name__ == "__main__":
    unittest.main()
