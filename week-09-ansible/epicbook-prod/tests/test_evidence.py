import hashlib
import json
from pathlib import Path
import unittest


PROJECT = Path(__file__).resolve().parents[1]
REPOSITORY = PROJECT.parents[1]


class SourceCaptureTests(unittest.TestCase):
    def test_approved_capture_bytes_and_sources_remain_unchanged(self):
        manifest_text = (PROJECT / "evidence/source-captures.json").read_text()
        manifest = json.loads(manifest_text)
        self.assertNotIn("/Users/", manifest_text)
        self.assertEqual(
            {item["slot"] for item in manifest["items"]},
            {"6", "7", "8a", "8b", "8c", "8d", "10a", "10b", "10c", "11"},
        )
        self.assertEqual(len(manifest["items"]), 10)
        for item in manifest["items"]:
            with self.subTest(slot=item["slot"]):
                image = (PROJECT / "evidence" / item["image"]).resolve()
                source = (REPOSITORY / item["source_file"]).resolve()
                self.assertTrue(image.is_relative_to(PROJECT / "evidence/images"))
                self.assertTrue(source.is_relative_to(PROJECT / "ansible"))
                raw = image.read_bytes()
                self.assertTrue(raw.startswith(b"\x89PNG\r\n\x1a\n"))
                self.assertEqual(len(raw), item["image_bytes"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), item["image_sha256"])
                self.assertEqual(
                    hashlib.sha256(source.read_bytes()).hexdigest(),
                    item["source_sha256"],
                )
                self.assertEqual(item["source_commit"], manifest["source_commit"])
                self.assertTrue(item["source_only"])
        evidence = json.loads((PROJECT / "evidence/assignment-05-manifest.json").read_text())
        self.assertEqual(
            {item["number"] for item in evidence["numbered_screenshots"]
             if item["status"] == "captured-source-only"},
            {1, 3, 6, 7, 8, 10, 11},
        )

    def test_infrastructure_captures_and_historical_tree_scope(self):
        text = (PROJECT / "evidence/infrastructure-source-captures.json").read_text()
        self.assertNotIn("/Users/", text)
        manifest = json.loads(text)
        self.assertEqual({item["slot"] for item in manifest["items"]},
                         {"1a", "1b", "1c", "3a", "3b"})
        self.assertEqual(len(manifest["items"]), 5)
        tree = manifest["tree_at_capture"]
        self.assertEqual(tree["tracked_file_count"], 43)
        self.assertEqual(len(tree["source_hashes"]), 43)
        self.assertEqual(tree["source_commit"], "a15fc8c7c728d699fe1a0ae43177b8809f19eba7")
        for relative in tree["source_hashes"]:
            self.assertTrue((REPOSITORY / relative).is_relative_to(PROJECT))
        for item in manifest["items"]:
            with self.subTest(slot=item["slot"]):
                image = (PROJECT / "evidence" / item["image"]).resolve()
                self.assertTrue(image.is_relative_to(PROJECT / "evidence/images"))
                raw = image.read_bytes()
                self.assertTrue(raw.startswith(b"\x89PNG\r\n\x1a\n"))
                self.assertEqual(len(raw), item["image_bytes"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), item["image_sha256"])
                self.assertTrue(item["source_only"])
                if item["source_kind"] == "terraform-source":
                    source = (REPOSITORY / item["source_file"]).resolve()
                    self.assertTrue(source.is_relative_to(PROJECT / "terraform/azure"))
                    self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),
                                     item["source_sha256"])
                else:
                    self.assertEqual(item["source_commit"], tree["source_commit"])


if __name__ == "__main__":
    unittest.main()
