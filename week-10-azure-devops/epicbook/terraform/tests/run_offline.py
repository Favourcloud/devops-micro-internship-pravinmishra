"""macOS-only native checks: existing tools, synthetic plans and private scratch."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

SOURCE = Path(__file__).resolve().parents[1]


def source_files(root):
    files = sorted([*root.glob("*.tf"), *root.glob("*.tf.json"), root / ".terraform.lock.hcl",
                    *root.glob("tests/*.tftest.hcl")])
    if not all(path.is_file() and not path.is_symlink() for path in files):
        raise ValueError("Expected regular source files and a reviewed provider lock.")
    fixtures = list(root.glob("tests/*.tftest.hcl"))
    if not fixtures or list(root.glob("tests/*.tftest.json")):
        raise ValueError("Expected HCL mock fixtures only.")
    for path in fixtures:
        text = path.read_text()
        runs = re.findall(r'^run "[a-z0-9_]+"', text, re.M)
        commands = re.findall(r'\bcommand\s*=\s*(\w+)', text)
        if not runs or commands != ["plan"] * len(runs) or 'mock_provider "azurerm"' not in text:
            raise ValueError("Each native fixture must use mocked Azure and explicit plan-only runs.")
    return files


def profile_for(scratch):
    return ('(version 1)(allow default)(deny network*)(allow network* (local unix-socket))'
            '(deny file-write*)(allow file-write* (subpath ' + json.dumps(str(scratch)) + '))'
            '(allow file-write-data (literal "/dev/null"))')


def environment_for(scratch):
    return {"PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "TMPDIR": str(scratch),
            "TF_CLI_CONFIG_FILE": "/dev/null", "TF_DATA_DIR": str(scratch / "data"),
            "CHECKPOINT_DISABLE": "1", "TF_IN_AUTOMATION": "1", "TF_INPUT": "0"}


def check(terraform, plugins):
    if sys.platform != "darwin" or not Path("/usr/bin/sandbox-exec").is_file():
        raise ValueError("This runner requires macOS sandbox-exec; it never falls back to unrestricted execution.")
    if not terraform.is_file() or not plugins.is_dir():
        raise ValueError("Provide the existing Terraform executable and installed provider mirror; no downloads are performed.")
    files = source_files(SOURCE)
    hashes = {str(path.relative_to(SOURCE)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    # A short path is necessary for the provider's Unix-domain RPC socket.
    with tempfile.TemporaryDirectory(prefix="w10-a4-", dir="/private/tmp") as directory:
        scratch = Path(directory)
        root = scratch / "root"
        (root / "tests").mkdir(parents=True, mode=0o700)
        for path in files:
            shutil.copyfile(path, root / path.relative_to(SOURCE))

        def run(arguments):
            result = subprocess.run(["/usr/bin/sandbox-exec", "-p", profile_for(scratch),
                                     str(terraform), *arguments], cwd=root, env=environment_for(scratch),
                                    text=True, capture_output=True, timeout=240)
            if result.returncode:
                for line in result.stdout.splitlines():
                    if line.startswith("{"):
                        event = json.loads(line)
                        if event.get("type") == "diagnostic":
                            diagnostic = event["diagnostic"]
                            print(diagnostic.get("summary", "Native check failed"), file=sys.stderr)
                            print(diagnostic.get("detail", "")[:2000], file=sys.stderr)
                raise ValueError("Native offline check failed: " + arguments[0] + ". " + result.stderr[:2000])
            return result.stdout

        run(["init", "-backend=false", "-get=false", "-lockfile=readonly", "-input=false", "-no-color",
             "-plugin-dir=" + str(plugins)])
        run(["fmt", "-check", "-recursive"])
        validation = json.loads(run(["validate", "-json"]))
        if not validation.get("valid"):
            raise ValueError("Terraform configuration did not validate.")
        events = [json.loads(line) for line in run(["test", "-no-color", "-json"]).splitlines()
                  if line.startswith("{")]
        summaries = [event["test_summary"] for event in events if event.get("type") == "test_summary"]
        if len(summaries) != 1 or summaries[0].get("status") != "pass" or summaries[0].get("skipped"):
            raise ValueError("Every mock run must pass; skipped runs are not success.")
        result = {"schema_version": 1, "source_sha256": hashes, "terraform_validation": validation,
                  "mock_tests": summaries[0], "external_network_denied": True,
                  "local_unix_rpc_allowed": True, "credential_environment_inherited": False,
                  "backend_initialized": False, "cloud_resources_created": False}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--terraform", type=Path, required=True)
    parser.add_argument("--plugin-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = check(args.terraform.resolve(), args.plugin_dir.resolve())
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        print(str(error)[:2000], file=sys.stderr)
        print("Offline checks failed. No unrestricted retry was made.", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
