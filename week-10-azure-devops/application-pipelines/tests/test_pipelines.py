import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import unittest
from unittest.mock import Mock, mock_open, patch


ROOT = Path(__file__).resolve().parents[1]
WEEK = ROOT.parent
CONTRACT_SPEC = importlib.util.spec_from_file_location("brief_contract", WEEK / "submission/brief_contract.py")
CONTRACT = importlib.util.module_from_spec(CONTRACT_SPEC)
CONTRACT_SPEC.loader.exec_module(CONTRACT)
spec = importlib.util.spec_from_file_location("site_contract", ROOT / "ci/validate_site.py")
site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site)
DATE = "2026-09-17"
STATIC = {"index.html": b"<html><body><h1>Eze Favour</h1><p>Synthetic unit fixture only.</p></body></html>"}
REACT = {
    "index.html": b'<html><body><div id="root"></div><script src="/static/js/main.fixture.js"></script></body></html>',
    "asset-manifest.json": b"{}",
    "static/js/main.fixture.js": b"Opaque synthetic unit fixture, not JavaScript or a build: Eze Favour 2026-09-17",
}


def parse_yaml(name):
    result = subprocess.run(
        ["/usr/bin/ruby", "--disable-gems", "-rpsych", "-rjson", "-e",
         "puts JSON.generate(Psych.safe_load(STDIN.read, [], [], false))"],
        input=(ROOT / name).read_text(), text=True, capture_output=True, check=True, timeout=10,
    )
    return json.loads(result.stdout)


def jobs(pipeline):
    return pipeline.get("jobs", []) + [job for stage in pipeline.get("stages", []) for job in stage["jobs"]]


def steps(pipeline):
    return [step for job in jobs(pipeline) for step in job["steps"]]


class PayloadTests(unittest.TestCase):
    def reject(self, files, kind="static", **kwargs):
        with self.assertRaises(site.InvalidSite):
            site.validate_payload(files, kind, **kwargs)

    def test_static_manifest_matches_real_sha256(self):
        expected = hashlib.sha256(STATIC["index.html"]).hexdigest() + "  index.html\n"
        self.assertEqual(site.validate_payload(STATIC, "static"), expected)

    def test_react_manifest_is_deterministic_and_verifiable(self):
        manifest = site.validate_payload(REACT, "react", DATE)
        files = dict(REACT, **{site.MANIFEST: manifest.encode()})
        self.assertEqual(site.validate_payload(files, "react", DATE, True), manifest)
        self.assertEqual(site.validate_payload(dict(reversed(list(REACT.items()))), "react", DATE), manifest)

    def test_index_is_required(self):
        self.reject({})
        self.reject({"manifest.json": b"{}"}, "react", deployment_date=DATE)

    def test_name_must_be_in_static_body_not_title_comment_or_script(self):
        for html in (
            b"<html><head><title>Eze Favour</title></head><body>Fixture</body></html>",
            b"<html><body><!-- Eze Favour --></body></html>",
            b"<html><body><script>Eze Favour</script></body></html>",
        ):
            with self.subTest(html=html):
                self.reject({"index.html": html})

    def test_static_name_can_span_html_elements(self):
        site.validate_payload({"index.html": b"<html><body>Eze <strong>Favour</strong></body></html>"}, "static")

    def test_static_upstream_inline_script_is_not_an_external_payload_file(self):
        html = STATIC["index.html"].replace(b"</body>", b"<script></script></body>")
        site.validate_payload({"index.html": html}, "static")

    def test_static_external_scripts_and_stylesheets_are_rejected(self):
        for tag in (b'<script src="https://example.invalid/a.js"></script>', b'<link rel="stylesheet" href="a.css">'):
            self.reject({"index.html": STATIC["index.html"].replace(b"</body>", tag + b"</body>")})

    def test_invalid_utf8_and_missing_body_are_rejected(self):
        self.reject({"index.html": b"\xff"})
        self.reject({"index.html": b"Eze Favour"})

    def test_secret_source_map_and_traversal_paths_are_rejected(self):
        for name in (".env", ".git/config", "src/App.js", "node_modules/package.json", "../key", "/index.html", "static/js/main.js.map", "static/../key", "static/js/.secret.js", "static//js/main.js", "static/js/bad\nname.js", "terraform.tfstate"):
            with self.subTest(name=name):
                files = dict(REACT, **{name: b"synthetic forbidden file"})
                self.reject(files, "react", deployment_date=DATE)

    def test_static_cannot_include_other_repository_files(self):
        for name in ("README.md", "azure-pipelines.yml", "ci/validate_site.py", "asset-manifest.json"):
            self.reject(dict(STATIC, **{name: b"synthetic fixture"}))

    def test_react_requires_local_script_and_asset_manifest(self):
        files = dict(REACT)
        del files["asset-manifest.json"]
        self.reject(files, "react", deployment_date=DATE)
        for source in (b"https://example.invalid/main.js", b"/static/js/missing.js", b"/static/media/image.svg", b""):
            files = dict(REACT)
            files["index.html"] = b'<html><body><script src="' + source + b'"></script></body></html>'
            self.reject(files, "react", deployment_date=DATE)

    def test_react_rejects_missing_name_date_and_original_placeholders(self):
        for content in (b"Fixture", b"Eze Favour", b"2026-09-17", b"Eze Favour 2026-09-17 Your Full Name", b"Eze Favour 2026-09-17 DD/MM/YYYY"):
            files = dict(REACT)
            files["static/js/main.fixture.js"] = content
            self.reject(files, "react", deployment_date=DATE)

    def test_real_calendar_date_is_required(self):
        for value in (None, "__set_actual_deployment_date__", "17/09/2026", "2026-02-29", "2026-9-17", "2026-09-17\n"):
            with self.subTest(value=value):
                self.reject(REACT, "react", deployment_date=value)
        site.valid_date("2028-02-29")

    def test_absent_stale_and_tampered_manifests_fail(self):
        self.reject(STATIC, verify_manifest=True)
        manifest = site.validate_payload(STATIC, "static").encode()
        self.reject(dict(STATIC, **{site.MANIFEST: manifest + b"extra\n"}), verify_manifest=True)
        files = dict(STATIC, **{site.MANIFEST: manifest})
        files["index.html"] += b" "
        self.reject(files, verify_manifest=True)

    def test_generating_over_an_existing_manifest_is_rejected(self):
        self.reject(dict(STATIC, **{site.MANIFEST: b"old"}))

    def test_file_count_file_size_and_total_limits(self):
        with patch.object(site, "MAX_FILES", 1):
            self.reject(REACT, "react", deployment_date=DATE)
        with patch.object(site, "MAX_FILE_BYTES", 1):
            self.reject(STATIC)
        with patch.object(site, "MAX_TOTAL_BYTES", 1):
            self.reject(STATIC)

    def test_unknown_kind_is_rejected(self):
        self.reject(STATIC, "unknown")


class ReadOnlyFilesystemTests(unittest.TestCase):
    def filesystem(self, name="index.html", content=None):
        content = STATIC["index.html"] if content is None else content
        root = Mock()
        root.is_symlink.return_value = False
        root.is_dir.return_value = True
        child = Mock()
        child.is_symlink.return_value = False
        child.is_dir.return_value = False
        child.is_file.return_value = True
        child.relative_to.return_value.as_posix.return_value = name
        child.stat.return_value.st_size = len(content)
        child.open = mock_open(read_data=content)
        root.rglob.return_value = [child]
        return root, child

    def test_regular_file_is_opened_read_only(self):
        root, child = self.filesystem()
        self.assertEqual(site.read_payload(root, "static"), STATIC)
        child.open.assert_called_once_with("rb")

    def test_symlink_root_is_rejected_before_traversal(self):
        root, child = self.filesystem()
        root.is_symlink.return_value = True
        with self.assertRaises(site.InvalidSite):
            site.read_payload(root, "static")
        root.rglob.assert_not_called()

    def test_symlink_file_is_never_opened(self):
        root, child = self.filesystem()
        child.is_symlink.return_value = True
        with self.assertRaises(site.InvalidSite):
            site.read_payload(root, "static")
        child.open.assert_not_called()

    def test_forbidden_file_is_rejected_before_reading_its_contents(self):
        root, child = self.filesystem(".env")
        with self.assertRaises(site.InvalidSite):
            site.read_payload(root, "static")
        child.open.assert_not_called()

    def test_special_file_is_never_opened(self):
        root, child = self.filesystem()
        child.is_file.return_value = False
        with self.assertRaises(site.InvalidSite):
            site.read_payload(root, "static")
        child.open.assert_not_called()

    def test_forbidden_directory_is_not_an_accepted_empty_payload_entry(self):
        root, child = self.filesystem("node_modules")
        child.is_dir.return_value = True
        with self.assertRaises(site.InvalidSite):
            site.read_payload(root, "react")
        child.open.assert_not_called()

    def test_oversized_file_is_not_opened(self):
        root, child = self.filesystem()
        child.stat.return_value.st_size = site.MAX_FILE_BYTES + 1
        with self.assertRaises(site.InvalidSite):
            site.read_payload(root, "static")
        child.open.assert_not_called()

    def test_growing_file_is_bounded_and_rejected(self):
        root, child = self.filesystem(content=b"0123456789")
        child.stat.return_value.st_size = 1
        with patch.object(site, "MAX_FILE_BYTES", 5):
            with self.assertRaises(site.InvalidSite):
                site.read_payload(root, "static")
        child.open().read.assert_called_once_with(6)

    def test_cli_rejects_without_dumping_files_or_paths(self):
        result = subprocess.run(
            ["/usr/bin/python3", "-I", "-B", str(ROOT / "ci/validate_site.py"), "static", str(ROOT / "tests/__absent_payload__")],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertNotIn(str(ROOT), result.stderr)
        self.assertIn("no contents were logged", result.stderr)


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.static = parse_yaml("static.azure-pipelines.yml")
        cls.react = parse_yaml("react.azure-pipelines.yml")

    def test_required_push_triggers_and_no_pr_trigger(self):
        self.assertEqual(self.static["trigger"]["branches"]["include"], ["*"])
        self.assertEqual(self.react["trigger"]["branches"]["include"], ["main"])
        for pipeline in (self.static, self.react):
            self.assertEqual(pipeline["pr"], "none")
            self.assertNotIn("schedules", pipeline)
            self.assertNotIn("resources", pipeline)

    def test_runtime_linux_pool_not_a_hosted_image(self):
        for pipeline in (self.static, self.react):
            self.assertEqual(pipeline["pool"], {"name": "${{ parameters.poolName }}", "demands": ["Agent.OS -equals Linux"]})
            self.assertEqual(pipeline["parameters"][0]["default"], "DMI-Week10-A1")
            self.assertNotIn("vmImage", pipeline["pool"])

    def test_bounded_clean_jobs_and_no_retained_checkout_credentials(self):
        for pipeline in (self.static, self.react):
            for job in jobs(pipeline):
                self.assertLessEqual(job["timeoutInMinutes"], 20)
                self.assertEqual(job["workspace"], {"clean": "all"})
                checkout = job["steps"][0]
                self.assertEqual(checkout, {"checkout": "self", "clean": True, "persistCredentials": False})
                self.assertNotIn("continueOnError", job)

    def test_unconfigured_connections_and_date_are_not_claimed_ready(self):
        for pipeline in (self.static, self.react):
            self.assertTrue(pipeline["variables"]["sshServiceConnection"].startswith("__set_approved_"))
            self.assertEqual(pipeline["variables"]["learnerName"], "Eze Favour")
            self.assertEqual(pipeline["variables"]["targetFolder"], "/var/www/html")
        self.assertEqual(self.react["variables"]["deploymentDate"], "__set_actual_deployment_date__")

    def test_static_stages_only_reviewed_html_then_manifests(self):
        sequence = self.static["jobs"][0]["steps"]
        self.assertIn('test ! -L index.html', sequence[1]["bash"])
        self.assertIn('cp -- index.html "$SITE_ROOT/index.html"', sequence[1]["bash"])
        self.assertIn("--verify-manifest", sequence[1]["bash"])
        native = [step for step in sequence if "task" in step]
        self.assertEqual([step["task"] for step in native], ["SSH@0", "CopyFilesOverSSH@0", "SSH@0"])
        self.assertEqual(native[0]["inputs"]["args"], "static preflight")
        self.assertEqual(native[-1]["inputs"]["args"], "static verify")
        self.assertIn("PullRequest", self.static["jobs"][0]["condition"])

    def test_four_stages_depend_on_success_in_order(self):
        stages = self.react["stages"]
        self.assertEqual([stage["stage"] for stage in stages], ["Build", "Test", "Publish", "Deploy"])
        for previous, stage in zip(stages, stages[1:]):
            self.assertEqual(stage["dependsOn"], previous["stage"])
            self.assertIn("succeeded()", stage["condition"])
        self.assertIn("PullRequest", stages[0]["condition"])
        self.assertIn("refs/heads/main", stages[-1]["condition"])

    def test_all_jest_tests_are_run_without_starter_filter_or_success_bypass(self):
        script = self.react["stages"][1]["jobs"][0]["steps"][-1]
        self.assertIn("npm exec --offline --ignore-scripts -- react-scripts test --watchAll=false --runInBand", script["bash"])
        self.assertEqual(script["env"]["CI"], "true")
        self.assertNotIn("react-scripts test tests", script["bash"])
        for forbidden in ("passWithNoTests", "continueOnError", "|| true", "testPathIgnorePatterns"):
            self.assertNotIn(forbidden, (ROOT / "react.azure-pipelines.yml").read_text())

    def test_locked_install_and_same_real_node_pin_in_build_and_test(self):
        self.assertEqual(self.react["variables"]["nodeVersion"], "22.23.2")
        node_steps = [step for step in steps(self.react) if step.get("task") == "NodeTool@0"]
        self.assertEqual(len(node_steps), 2)
        for step in node_steps:
            self.assertEqual(step["inputs"], {"versionSpec": "$(nodeVersion)", "checkLatest": False})
        build = next(step for step in self.react["stages"][0]["jobs"][0]["steps"] if "npm ci" in step.get("bash", ""))
        self.assertEqual(build["env"]["GENERATE_SOURCEMAP"], "false")
        self.assertIn("npm ci --ignore-scripts --no-audit --no-fund", build["bash"])
        self.assertIn("npm --ignore-scripts run build", build["bash"])

    def test_artifacts_are_current_run_and_production_only(self):
        publish = [step["inputs"] for step in steps(self.react) if step.get("task") == "PublishPipelineArtifact@1"]
        download = [step["inputs"] for step in steps(self.react) if step.get("task") == "DownloadPipelineArtifact@2"]
        self.assertEqual([item["artifact"] for item in publish], ["candidate-site", "site-build"])
        self.assertEqual([item["artifactName"] for item in download], ["candidate-site", "site-build"])
        self.assertTrue(all(item["buildType"] == "current" for item in download))
        self.assertEqual(publish[0]["targetPath"], "$(Build.SourcesDirectory)/build")
        self.assertEqual(publish[1]["targetPath"], download[0]["targetPath"])
        self.assertEqual(download[1]["targetPath"], "$(Pipeline.Workspace)/site-build")
        for stage in self.react["stages"][2:]:
            self.assertTrue(any("--verify-manifest" in step.get("bash", "") for step in stage["jobs"][0]["steps"]))

    def test_copy_and_ssh_are_fail_closed_and_never_clean_the_entire_target(self):
        for pipeline in (self.static, self.react):
            for step in steps(pipeline):
                self.assertNotIn("continueOnError", step)
                if step.get("task") == "CopyFilesOverSSH@0":
                    inputs = step["inputs"]
                    self.assertFalse(inputs["cleanTargetFolder"])
                    self.assertTrue(inputs["failOnEmptySource"])
                    self.assertNotEqual(inputs["sourceFolder"], "$(Build.SourcesDirectory)")
                if step.get("task") == "SSH@0":
                    inputs = step["inputs"]
                    self.assertTrue(inputs["failOnStdErr"])
                    self.assertFalse(inputs["enableRemoteVsoCommands"])
                    self.assertEqual(inputs["scriptPath"], "$(Build.SourcesDirectory)/ci/verify_remote.sh")
                    self.assertEqual(inputs["runOptions"], "script")
                    self.assertIn(inputs["args"], {"static preflight", "static verify", "react preflight", "react verify"})

    def test_every_bash_fragment_parses_without_execution(self):
        scripts = [(ROOT / "ci/verify_remote.sh").read_text()]
        for pipeline in (self.static, self.react):
            scripts.extend(step["bash"] for step in steps(pipeline) if "bash" in step)
        for script in scripts:
            result = subprocess.run(["/bin/bash", "--noprofile", "--norc", "-n"], input=script, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)


STUBS = r'''
id() { if [[ "$1" == -u ]]; then printf '%s\n' "${FAKE_UID:-1001}"; else printf '%s\n' "${FAKE_USER:-week10deploy}"; fi; }
stat() {
  if [[ "$3" == /var/www ]]; then printf '%s\n' "${FAKE_PARENT_OWNER:-0:0:755}";
  elif [[ "$2" == '%s' ]]; then printf '%s\n' "${FAKE_MARKER_SIZE:-10}";
  else printf '%s\n' "${FAKE_MARKER_OWNER:-0:0:644}"; fi
}
cat() { if [[ "${2:-}" == /var/www/.dmi-week10-target ]]; then printf '%s\n' "${FAKE_TARGET:-week10-a2}"; else /bin/cat "$@"; fi; }
systemctl() { return "${FAKE_NGINX_EXIT:-0}"; }
test() {
  if [[ "${1:-}" == '!' ]]; then shift; if test "$@"; then return 1; else return 0; fi; fi
  case "${1:-}" in
    -L) [[ "${FAKE_SYMLINK:-0}" == 1 ]] ;;
    -e) [[ "${FAKE_RAW_SOURCE:-0}" == 1 ]] ;;
    -w) [[ "${FAKE_NOT_WRITABLE:-0}" == 0 ]] ;;
    -f) [[ "${FAKE_MARKER_SPECIAL:-0}" == 0 ]] ;;
    -d|-r|-s) return 0 ;;
    *) builtin test "$@" ;;
  esac
}
cd() { [[ "$1" == '--' && "$2" == '/var/www/html' ]]; }
sha256sum() {
  if [[ "${1:-}" == --strict ]]; then
    [[ "${FAKE_MANIFEST_BAD:-0}" == 0 ]] || return 1
    printf '%s\n' 'index.html: OK'
  elif [[ "${1:-}" == index.html ]]; then
    printf '%s\n' 'fixture-hash  index.html'
  else
    cat >/dev/null
    printf '%s  -\n' "${FAKE_HTTP_HASH:-fixture-hash}"
  fi
}
curl() {
  printf 'STUB_CURL %s\n' "${*: -1}" >&2
  [[ "${FAKE_CURL_FAIL:-0}" == 0 ]] || return 22
  if [[ " $* " == *' --write-out '* ]]; then printf '%s' "${FAKE_MISSING_STATUS:-404}"; else printf '%s' 'Synthetic unit fixture, not an HTTP response'; fi
}
find() {
  if [[ "$1" == /var/www/html ]]; then
    [[ "${FAKE_FIND_FAIL:-0}" == 0 ]] || return 1
    printf '%s' "${FAKE_UNSAFE_ENTRY:-}";
  else printf '%s\n' 'index.html' 'dmi-site.sha256' 'static'; fi
}
'''


class RemoteVerifierStubTests(unittest.TestCase):
    def run_stub(self, kind="static", phase="verify", **environment):
        env = {"PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "FAKE_TARGET": "week10-a3" if kind == "react" else "week10-a2"}
        env.update(environment)
        return subprocess.run(
            ["/bin/bash", "--noprofile", "--norc", "-s", "--", kind, phase],
            input=STUBS + (ROOT / "ci/verify_remote.sh").read_text(), env=env,
            capture_output=True, text=True, timeout=10,
        )

    def test_preflight_uses_no_http_or_checksum_operations(self):
        result = self.run_stub(phase="preflight")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("STUB_CURL", result.stderr)
        self.assertNotIn("index.html: OK", result.stdout)

    def test_preflight_does_not_claim_a_full_privilege_audit(self):
        result = self.run_stub(phase="preflight")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("non-root deployment account verified", result.stdout)
        self.assertNotIn("unprivileged deployment account verified", result.stdout)
        self.assertIn("not its full privilege set", (ROOT / "README.md").read_text())

    def test_static_stub_success_is_only_local_http_verification(self):
        result = self.run_stub()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Eze Favour", result.stdout)
        self.assertEqual(result.stderr.count("STUB_CURL"), 1)
        self.assertIn("http://127.0.0.1/", result.stderr)

    def test_react_stub_checks_spa_and_missing_static_asset(self):
        result = self.run_stub("react")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("/dmi-week10-route-check", result.stderr)
        self.assertIn("/static/dmi-week10-missing.js", result.stderr)
        self.assertEqual(result.stderr.count("STUB_CURL"), 3)

    def test_root_wrong_user_target_owner_and_unsafe_root_fail_before_http(self):
        for changes in (
            {"FAKE_UID": "0"}, {"FAKE_USER": "labadmin"}, {"FAKE_TARGET": "week10-a3"},
            {"FAKE_MARKER_OWNER": "1001:1001:644"}, {"FAKE_MARKER_OWNER": "0:0:666"},
            {"FAKE_SYMLINK": "1"}, {"FAKE_RAW_SOURCE": "1"}, {"FAKE_NOT_WRITABLE": "1"}, {"FAKE_NGINX_EXIT": "3"},
            {"FAKE_PARENT_OWNER": "1001:1001:755"}, {"FAKE_MARKER_SIZE": "11"}, {"FAKE_MARKER_SPECIAL": "1"},
            {"FAKE_TARGET": "week10-a2\nweek10-a3"}, {"FAKE_UNSAFE_ENTRY": "/var/www/html/unsafe-symlink-or-fifo"},
            {"FAKE_FIND_FAIL": "1"},
        ):
            with self.subTest(changes=changes):
                result = self.run_stub(**changes)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("STUB_CURL", result.stderr)
                self.assertNotIn("HTTP verified", result.stdout)

    def test_manifest_http_failure_wrong_content_and_fake_404_fail(self):
        for changes in ({"FAKE_MANIFEST_BAD": "1"}, {"FAKE_CURL_FAIL": "1"}, {"FAKE_HTTP_HASH": "wrong"}, {"FAKE_MISSING_STATUS": "200"}):
            with self.subTest(changes=changes):
                result = self.run_stub("react", **changes)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("HTTP verified", result.stdout)

    def test_unknown_mode_or_phase_is_rejected(self):
        self.assertNotEqual(self.run_stub("unknown").returncode, 0)
        self.assertNotEqual(self.run_stub(phase="unknown").returncode, 0)


class PreservationAndPolicyTests(unittest.TestCase):
    def test_original_requirement_bytes_survive_reviewed_answers(self):
        baseline = json.loads((WEEK / "self-hosted-agent/tests/source-baseline.json").read_text())
        for name, expected in baseline["briefs"].items():
            raw = (WEEK / name).read_bytes()
            raw = CONTRACT.restore_original_prompts(raw, name)
            if name.startswith("assignment-01-"):
                raw, count = re.subn(rb"<!-- BEGIN WEEK10 A1 OFFLINE PREPARATION -->\n.*?<!-- END WEEK10 A1 OFFLINE PREPARATION -->\n\n", b"", raw, flags=re.S)
                self.assertEqual(count, 1)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), expected["sha256"])

    def test_metadata_records_no_live_success_or_synthetic_evidence(self):
        data = json.loads((ROOT / "sources.json").read_text())
        for field in ("live_verified", "applications_imported", "application_builds_run", "application_tests_run"):
            self.assertIs(data[field], False)
        self.assertEqual(data["evidence"]["captured"], 0)
        self.assertEqual(data["evidence"]["successful_run_urls"], [])
        self.assertEqual(data["evidence"]["website_urls"], [])
        self.assertEqual(data["evidence"]["static_numbered_slots"], 5)
        self.assertEqual(data["evidence"]["react_numbered_slots"], 6)
        self.assertEqual(data["sources"]["react"]["package_test_script"], "react-scripts test tests")
        self.assertTrue(data["sources"]["static"]["has_upstream_inline_script"])
        self.assertEqual(data["node"]["version"], "22.23.2")
        self.assertFalse(data["node"]["package_downloaded"])

    def test_no_javascript_images_state_or_packages_added(self):
        banned = {".js", ".jsx", ".ts", ".tsx", ".png", ".jpg", ".gif", ".zip", ".gz", ".tfstate"}
        self.assertFalse([path for path in ROOT.rglob("*") if path.suffix in banned])

    def test_validator_has_no_network_execution_or_write_api(self):
        tree = ast.parse((ROOT / "ci/validate_site.py").read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.assertTrue(all(item.name in {"argparse", "hashlib", "re", "sys"} for item in node.names))
            elif isinstance(node, ast.ImportFrom):
                self.assertIn(node.module, {"datetime", "html.parser", "pathlib"})
            elif isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
                self.assertNotIn(name, {"exec", "eval", "system", "popen", "run", "write_text", "write_bytes", "unlink", "mkdir"})
                if name == "open":
                    self.assertEqual(ast.literal_eval(node.args[0]), "rb")

    def test_remote_script_is_verification_not_provisioning(self):
        text = (ROOT / "ci/verify_remote.sh").read_text()
        for forbidden in ("sudo", "chmod", "chown", "apt ", "systemctl start", "systemctl restart", "terraform", "az ", "aws ", "--token", "set -x", "rm -"):
            self.assertNotIn(forbidden, text)
        self.assertIn("--noproxy '*'", text)
        self.assertIn("sha256sum --strict --check", text)
        self.assertNotIn("https://", text)

    def test_runbook_preserves_material_live_and_human_gates(self):
        text = (ROOT / "README.md").read_text()
        for phrase in ("Neither assignment is complete", "no-JavaScript-edit boundary", "not a reported test execution", "same run", "no sudo", "not SSH host authentication", "not atomic", "actual supplied kit", "live proof remain pending"):
            self.assertIn(phrase.lower(), text.lower())
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if not target.startswith(("https://", "http://", "#")):
                self.assertTrue((ROOT / target.split("#")[0]).exists(), target)


if __name__ == "__main__":
    unittest.main()
