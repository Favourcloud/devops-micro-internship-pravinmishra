import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import Mock, mock_open, patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("static_personalization", ROOT / "ci/personalize_static.py")
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
FIXTURE = b'<html><body><header>Fixture\n        </header><script>Opaque fixture bytes, not executable code.</script></body></html>'


class StaticPersonalizationTests(unittest.TestCase):
    def personalize_fixture(self, content=FIXTURE):
        with patch.object(helper, "SOURCE_SHA256", hashlib.sha256(content).hexdigest()):
            return helper.personalize(content)

    def test_public_source_pin_matches_reviewed_coordinates(self):
        source = json.loads((ROOT / "sources.json").read_text())["sources"]["static"]
        self.assertEqual(helper.SOURCE_SHA256, source["index_html_sha256"])

    def test_only_the_name_paragraph_is_added(self):
        result = self.personalize_fixture()
        self.assertEqual(result.count(helper.INSERTION), 1)
        self.assertEqual(result.replace(helper.INSERTION, b"", 1), FIXTURE)
        self.assertIn(b"<strong>Eze Favour</strong>", result)
        self.assertIn(b"<script>Opaque fixture bytes, not executable code.</script>", result)

    def test_unreviewed_or_already_personalized_input_is_rejected(self):
        with self.assertRaises(helper.InvalidSource):
            helper.personalize(FIXTURE)
        with patch.object(helper, "SOURCE_SHA256", hashlib.sha256(FIXTURE).hexdigest()):
            with self.assertRaises(helper.InvalidSource):
                helper.personalize(self.personalize_fixture())

    def test_missing_or_duplicate_header_boundary_is_rejected(self):
        for content in (FIXTURE.replace(helper.MARKER, b""), FIXTURE + helper.MARKER):
            with self.subTest(content=content):
                with self.assertRaises(helper.InvalidSource):
                    self.personalize_fixture(content)

    def test_wrong_type_and_oversized_input_are_rejected(self):
        for content in (None, "not bytes", b"x" * (helper.MAX_BYTES + 1)):
            with self.subTest(kind=type(content).__name__):
                with self.assertRaises(helper.InvalidSource):
                    helper.personalize(content)

    def source_path(self):
        path = Mock()
        path.is_symlink.return_value = False
        path.is_file.return_value = True
        path.stat.return_value.st_size = len(FIXTURE)
        path.open = mock_open(read_data=FIXTURE)
        return path

    def test_file_is_opened_read_only_with_a_size_bound(self):
        path = self.source_path()
        self.assertEqual(helper.read_source(path), FIXTURE)
        path.open.assert_called_once_with("rb")
        path.open().read.assert_called_once_with(helper.MAX_BYTES + 1)

    def test_symlink_special_and_oversized_files_are_not_opened(self):
        for kind in ("symlink", "special", "oversized"):
            path = self.source_path()
            if kind == "symlink":
                path.is_symlink.return_value = True
            elif kind == "special":
                path.is_file.return_value = False
            else:
                path.stat.return_value.st_size = helper.MAX_BYTES + 1
            with self.subTest(kind=kind):
                with self.assertRaises(helper.InvalidSource):
                    helper.read_source(path)
                path.open.assert_not_called()

    def test_cli_emits_only_reviewed_html_to_stdout(self):
        output = Mock(buffer=io.BytesIO())
        with patch.object(helper, "read_source", return_value=FIXTURE), \
                patch.object(helper, "SOURCE_SHA256", hashlib.sha256(FIXTURE).hexdigest()), \
                patch.object(helper.sys, "stdout", output):
            self.assertEqual(helper.main(["synthetic-fixture.html"]), 0)
        self.assertEqual(output.buffer.getvalue(), self.personalize_fixture())

    def test_cli_rejection_does_not_echo_input_or_path(self):
        result = subprocess.run(
            ["/usr/bin/python3", "-I", "-B", str(ROOT / "ci/personalize_static.py"), str(ROOT / "tests/__absent_upstream__")],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertNotIn(str(ROOT), result.stderr)
        self.assertIn("no input contents or paths were logged", result.stderr)


if __name__ == "__main__":
    unittest.main()
