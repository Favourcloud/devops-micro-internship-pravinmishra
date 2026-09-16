#!/usr/bin/env python3
"""Fail-closed local validation: isolated environment, existing mirror, AzureRM mocks only."""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TF_FILES = ("main.tf", "variables.tf")
TEST_FILES = ("tests/app.tftest.hcl", "tests/inputs.tftest.hcl")


def guard_project(root):
    for path in root.iterdir():
        name = path.name
        if (
            name.endswith((".tfvars", ".tfvars.json", ".tf.json"))
            or ".auto.tfvars" in name
            or (name.endswith(".tf") and name not in TF_FILES)
            or name.startswith("terraform.tfstate")
            or name.endswith((".tfplan", ".tfplan.json"))
        ):
            raise ValueError("Unexpected live input, state, plan or Terraform override; move it out before offline validation.")
    for name in (*TF_FILES, *TEST_FILES, ".terraform.lock.hcl", "cloud-init.sh"):
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("A required reviewed source file is missing or symlinked.")
    if (root / "tests").is_symlink() or (root / ".private").is_symlink():
        raise ValueError("Refusing a symlinked tests or .private directory.")
    if {p.name for p in (root / "tests").glob("*.tftest.*")} != {Path(p).name for p in TEST_FILES}:
        raise ValueError("Unexpected Terraform test files; review the runner allowlist first.")
    for name in TEST_FILES:
        text = (root / name).read_text(encoding="utf-8")
        if len(re.findall(r'^mock_provider "azurerm"\s*\{', text, re.M)) != 1 or re.search(
            r'^\s*(provider|module|override_provider)\s+|\bproviders\s*=|\balias\s*=', text, re.M
        ):
            raise ValueError("Only the unaliased AzureRM mock is allowed; no live provider or alternate modules.")


def isolated_environment(directory, socket_directory):
    return {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": str(directory),
        "XDG_CONFIG_HOME": str(directory),
        "TMPDIR": str(socket_directory),
        "CHECKPOINT_DISABLE": "1",
        "TF_IN_AUTOMATION": "1",
        "TF_INPUT": "0",
        "TF_CLI_CONFIG_FILE": str(directory / "offline.tfrc"),
        "TF_DATA_DIR": str(directory / "terraform-data"),
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def run_steps(root, terraform, mirror, env):
    steps = [
        ("delivery, runner and stub safeguards", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]),
        ("bootstrap shell syntax", ["/bin/bash", "-n", "cloud-init.sh"]),
        ("Terraform version", [terraform, "version", "-json"]),
        ("terraform fmt", [terraform, "fmt", "-check", "-diff", *TF_FILES, *TEST_FILES]),
        ("terraform init (backend disabled)", [terraform, "init", "-backend=false", "-input=false", "-lockfile=readonly", "-no-color", f"-plugin-dir={mirror}"]),
        ("terraform validate", [terraform, "validate", "-no-color"]),
        ("terraform test (mock only)", [terraform, "test", *(f"-filter={name}" for name in TEST_FILES), "-no-color"]),
    ]
    for label, command in steps:
        result = subprocess.run(command, cwd=root, env=env, text=True, capture_output=True, timeout=300, check=False)
        output = result.stdout + result.stderr
        if result.returncode:
            for value in (str(root), env["HOME"], env["TMPDIR"], str(mirror), str(terraform), str(Path.home())):
                output = output.replace(value, "<local-path>")
            print(f"FAIL {label}\n{output}", file=sys.stderr)
            raise SystemExit(result.returncode)
        print(f"PASS {label}")
        if label == "Terraform version":
            if json.loads(result.stdout)["terraform_version"] != "1.13.5":
                raise ValueError("This reproducible offline runner requires exactly Terraform 1.13.5.")
        if label == "delivery, runner and stub safeguards":
            match = re.search(r"Ran \d+ tests? in .+", output)
            if not match:
                raise ValueError("Python test summary missing.")
            print(match.group(0))
        if label == "terraform test (mock only)":
            match = re.search(r"Success! \d+ passed, 0 failed\.", output)
            if not match:
                raise ValueError("Terraform mock success summary missing.")
            print(match.group(0))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--terraform", required=True, help="Existing trusted Terraform 1.13.5 binary")
    parser.add_argument("--plugin-dir", required=True, type=Path, help="Existing read-only AzureRM 4.47.0 mirror; no downloads")
    args = parser.parse_args()
    try:
        guard_project(ROOT)
        terraform = shutil.which(args.terraform)
        if not terraform:
            raise ValueError("Terraform missing; supply the existing trusted binary.")
        mirror = args.plugin_dir.resolve(strict=True)
        if not mirror.is_dir():
            raise ValueError("Provider mirror is not a directory.")
        os.umask(0o077)
        private = ROOT / ".private"
        private.mkdir(mode=0o700, exist_ok=True)
        private.chmod(0o700)
        # Short Unix socket paths are required on macOS; all other private data stays here.
        with tempfile.TemporaryDirectory(prefix="dmi-a3-", dir="/tmp") as socket_tmp, tempfile.TemporaryDirectory(prefix="offline-", dir=private) as temporary:
            directory = Path(temporary)
            config = "disable_checkpoint = true\nprovider_installation {\n  filesystem_mirror {\n"
            config += f"    path = {json.dumps(str(mirror))}\n"
            config += '    include = ["registry.terraform.io/hashicorp/azurerm"]\n  }\n}\n'
            (directory / "offline.tfrc").write_text(config, encoding="utf-8")
            run_steps(ROOT, terraform, mirror, isolated_environment(directory, socket_tmp))
        print("Offline checks only: no cloud API/authentication, real plan/apply/destroy or screenshots.")
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"Offline validation refused/failed: {type(exc).__name__}. Review local configuration; no later steps ran.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
