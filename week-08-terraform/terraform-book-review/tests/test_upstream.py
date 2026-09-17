"""Stdlib-only synthetic archive tests. No downloads, installs, source execution or cloud calls."""
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))
import upstream
import artifact


def archive_bytes(entries):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as archive:
        for name, payload, kind in entries:
            member = tarfile.TarInfo(name)
            member.type = kind
            if kind == tarfile.REGTYPE:
                member.size = len(payload)
                archive.addfile(member, io.BytesIO(payload))
            else:
                member.linkname = "outside"
                archive.addfile(member)
    return output.getvalue()


@contextlib.contextmanager
def scratch():
    directory = ROOT / "runtime" / (".test-upstream-" + str(os.getpid()))
    directory.mkdir(mode=0o700)
    try:
        yield directory
    finally:
        shutil.rmtree(directory)


class SourceTests(unittest.TestCase):
    def test_project_runtime_locks_match_exact_pins(self):
        project = json.loads((ROOT / "source-lock.json").read_text())
        runtime = upstream.load_lock()
        self.assertEqual(project, runtime)
        self.assertEqual(runtime["files"]["backend/src/server.js"], "85e5b994746753a903d78ee4b4ab9fc69acb447120b1f84743cff69feb6212c6")
        for path, value in upstream.LOCK_HASHES.items():
            self.assertEqual(project["files"][path], value)
        self.assertFalse(any("node_modules" in p or ".env" in p for p in project["files"]))

    def test_archive_hash_checked_before_parsing(self):
        with self.assertRaises(upstream.VerificationError), mock.patch.object(upstream.tarfile, "open") as parser:
            upstream.verify_source(b"synthetic tampered archive", upstream.load_lock())
        parser.assert_not_called()

    def test_synthetic_archive_selects_only_pinned_files(self):
        entries = [("root/notes.txt", b"synthetic inert input", tarfile.REGTYPE),
                   ("root/backend/.env", b"SYNTHETIC_NOT_A_SECRET", tarfile.REGTYPE),
                   ("root/backend/node_modules/untrusted.txt", b"not selected", tarfile.REGTYPE)]
        for path in upstream.LOCK_HASHES:
            entries.append(("root/" + path, b'{"lockfileVersion":3}', tarfile.REGTYPE))
        data = archive_bytes(entries)
        files = {path.removeprefix("root/"): upstream.digest(payload) for path, payload, _ in entries
                 if path == "root/notes.txt" or "package-lock.json" in path}
        lock = {"archive_size": len(data), "archive_sha256": upstream.digest(data), "root": "root", "files": files}
        selected = upstream.verify_source(data, lock)
        self.assertEqual(set(selected), set(files))
        self.assertNotIn("backend/.env", selected)

    def test_rejects_unsafe_entries_even_when_not_selected(self):
        for name, kind in [("../escape", tarfile.REGTYPE), ("/absolute", tarfile.REGTYPE),
                           ("root/../../escape", tarfile.REGTYPE), ("root//file", tarfile.REGTYPE),
                           ("root/./file", tarfile.REGTYPE), ("root/a\\b", tarfile.REGTYPE),
                           ("root/link", tarfile.SYMTYPE), ("root/hardlink", tarfile.LNKTYPE),
                           ("root/device", tarfile.CHRTYPE), ("root/pipe", tarfile.FIFOTYPE),
                           ("other/notes", tarfile.REGTYPE)]:
            with self.subTest(name=name, kind=kind):
                with tarfile.open(fileobj=io.BytesIO(archive_bytes([(name, b"test", kind)])), mode="r:gz") as archive:
                    with self.assertRaises(upstream.VerificationError):
                        list(upstream.safe_members(archive, strip_root="root"))

    def test_rejects_duplicates_size_count_and_expansion(self):
        inputs = [([("root/a", b"a", tarfile.REGTYPE)] * 2, {}),
                  ([("root/a", b"abcd", tarfile.REGTYPE)], {"max_file": 3}),
                  ([("root/a", b"abcd", tarfile.REGTYPE)], {"max_total": 3}),
                  ([("root/a", b"abcd", tarfile.REGTYPE)], {"max_count": 0})]
        for entries, options in inputs:
            with self.subTest(options=options), tarfile.open(fileobj=io.BytesIO(archive_bytes(entries)), mode="r:gz") as archive:
                with self.assertRaises(upstream.VerificationError):
                    list(upstream.safe_members(archive, **options))

    def test_extraction_refuses_existing_and_symlink_destinations(self):
        with scratch() as directory:
            destination = directory / "output"
            upstream.write_new_tree({"notes.txt": b"synthetic inert text"}, destination)
            self.assertEqual((destination / "notes.txt").read_bytes(), b"synthetic inert text")
            with self.assertRaises(upstream.VerificationError):
                upstream.write_new_tree({}, destination)
            (directory / "alias").symlink_to(destination, target_is_directory=True)
            with self.assertRaises(upstream.VerificationError):
                upstream.write_new_tree({}, directory / "alias" / "nested")

    def test_urls_deny_auth_queries_http_and_redirects(self):
        for url in ["http://example.invalid/a", "https://user:password@example.invalid/a",
                    "https://example.invalid/a?token=synthetic", "https://example.invalid:444/a",
                    "https://example.invalid/a#fragment", "https://example.invalid/a\n"]:
            with self.subTest(url=url), self.assertRaises(upstream.VerificationError):
                upstream.https_url(url)
        with self.assertRaises(upstream.VerificationError):
            upstream.NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.invalid")

    def test_download_bounded_and_proxy_free(self):
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.status, response.read.return_value = 200, b"12345"
        opener = mock.Mock()
        opener.open.return_value = response
        with mock.patch.object(upstream.urllib.request, "build_opener", return_value=opener) as build:
            with self.assertRaises(upstream.VerificationError):
                upstream.download("https://example.invalid/input", 4)
        response.read.assert_called_once_with(5)
        self.assertEqual(build.call_args.args[0].proxies, {})
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 30)


class ArtifactTests(unittest.TestCase):
    def test_release_gate_precedes_runtime_artifact_installation(self):
        with mock.patch.object(artifact, "verify_artifact") as verify, mock.patch.object(artifact, "write_new_tree") as write:
            with self.assertRaisesRegex(Exception, "runtime_release_not_authorized"):
                artifact.install_artifact(b"synthetic inert archive", {"release_authorized": False}, "unused", {})
        verify.assert_not_called()
        write.assert_not_called()

    def test_artifact_digest_checked_first(self):
        with self.assertRaises(Exception), mock.patch.object(artifact.tarfile, "open") as parser:
            artifact.verify_artifact(b"synthetic", {"runtime_artifact_sha256": "0" * 64})
        parser.assert_not_called()

    def test_allowed_source_and_generated_paths(self):
        lock = upstream.load_lock()
        self.assertTrue(artifact.permitted("frontend/.next/BUILD_ID", lock))
        self.assertTrue(artifact.permitted("backend/src/server.js", lock))
        for name in ["backend/.env", "backend/node_modules/a/.env.local", "frontend/.npmrc",
                     "backend/src/unreviewed.txt", "frontend/.next/.aws/credentials"]:
            self.assertFalse(artifact.permitted(name, lock))

    def test_manifest_complete_unchanged_and_origin_bound(self):
        # The minimal synthetic bundle contains no JavaScript source, only inert marker bytes.
        files = {"notes.txt": b"synthetic source", "frontend/.next/BUILD_ID": b"synthetic build",
                 "frontend/.next/required-server-files.json": b'{"config":{}}',
                 "frontend/node_modules/next/dist/bin/next": b"inert marker",
                 "backend/node_modules/sequelize/package.json": b"{}",
                 "backend/node_modules/mysql2/package.json": b"{}"}
        lock = {"files": {"notes.txt": upstream.digest(files["notes.txt"])}}
        manifest = {"schema_version": 1, "commit": upstream.COMMIT, "platform": "ubuntu-24.04-linux-amd64",
                    "public_origin": "https://books.example.invalid", "versions": {"node": "22.0.0"},
                    "files": {p: upstream.digest(v) for p, v in files.items()}}
        def bundle():
            entries = [(p, v, tarfile.REGTYPE) for p, v in files.items()]
            entries.append(("artifact-manifest.json", json.dumps(manifest).encode(), tarfile.REGTYPE))
            return archive_bytes(entries)
        def verify(data):
            return artifact.verify_artifact(data, {"runtime_artifact_sha256": upstream.digest(data),
                       "public_origin": "https://books.example.invalid"}, versions={"node": "22.0.0"})
        with mock.patch.object(artifact, "load_lock", return_value=lock):
            self.assertEqual(verify(bundle()), files)
            for key, value in [("commit", "wrong"), ("public_origin", "http://wrong.invalid"),
                               ("platform", "macos"), ("versions", {})]:
                old, manifest[key] = manifest[key], value
                with self.subTest(key=key), self.assertRaises(Exception):
                    verify(bundle())
                manifest[key] = old
            files["notes.txt"] = b"changed synthetic source"
            manifest["files"]["notes.txt"] = upstream.digest(files["notes.txt"])
            with self.assertRaisesRegex(Exception, "upstream_was_modified"):
                verify(bundle())


if __name__ == "__main__":
    unittest.main()
