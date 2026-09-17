#!/usr/bin/env python3
"""Validate A1 with a clean environment, isolated data and an AzureRM mock only."""

import argparse
import os
from pathlib import Path
import re
import secrets
import shutil
import string
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--terraform", default="terraform", help="Existing Terraform 1.13.x binary")
    parser.add_argument("--plugin-dir", type=Path, help="Optional existing read-only provider mirror")
    args = parser.parse_args()
    terraform = shutil.which(args.terraform)
    if not terraform:
        parser.error("Terraform is missing; supply the installed binary with --terraform.")
    if args.plugin_dir and not args.plugin_dir.is_dir():
        parser.error("The provider mirror directory does not exist.")
    if any(ROOT.glob("*.auto.tfvars*")) or any(
        (ROOT / name).exists() for name in ("terraform.tfvars", "terraform.tfvars.json", "override.tf", "override.tf.json")
    ) or any(ROOT.glob("*_override.tf*")):
        parser.error("Remove auto-loaded inputs/overrides from this project before isolated offline validation.")

    os.umask(0o077)
    private = ROOT / ".private"
    if private.is_symlink():
        parser.error("Refusing a symlinked .private directory.")
    private.mkdir(mode=0o700, exist_ok=True)
    private.chmod(0o700)

    classes = (string.ascii_lowercase, string.ascii_uppercase, string.digits, "!@#%_-+=")
    alphabet = "".join(classes)
    while True:
        password = "".join(secrets.choice(group) for group in classes)
        password += "".join(secrets.choice(alphabet) for _ in range(28))
        if not any(name in (password * 3).lower() for name in ("dmiuser", "root")):
            break

    # Provider Unix sockets need short paths on macOS, even in long worktree paths.
    with tempfile.TemporaryDirectory(prefix="dmi-a1-", dir="/tmp") as socket_tmp, tempfile.TemporaryDirectory(prefix="offline-env-", dir=private) as temporary:
        isolated = Path(temporary)
        config = isolated / "offline.tfrc"
        config.write_text("disable_checkpoint = true\n", encoding="utf-8")
        env = {
            "PATH": os.environ.get("PATH", os.defpath),
            "HOME": temporary,
            "XDG_CONFIG_HOME": temporary,
            "TMPDIR": socket_tmp,
            "CHECKPOINT_DISABLE": "1",
            "TF_IN_AUTOMATION": "1",
            "TF_INPUT": "0",
            "TF_CLI_CONFIG_FILE": str(config),
            "TF_DATA_DIR": str(private / "offline-data"),
            "TF_VAR_admin_password": password,
            "PYTHONDONTWRITEBYTECODE": "1",
        }

        def check(label, command):
            result = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, check=False)
            if result.returncode:
                diagnostic = result.stdout + result.stderr
                variants = (
                    password, password.lower(), password.upper(), password[:15], password[:16], password[:8],
                    re.sub(r"[0-9]", "x", password), re.sub(r"[^a-zA-Z0-9]", "x", password),
                )
                for value in sorted(variants, key=len, reverse=True):
                    diagnostic = diagnostic.replace(value, "<sensitive>")
                for value in (str(ROOT), temporary, socket_tmp, str(Path.home()), str(args.plugin_dir or ""), terraform):
                    if value:
                        diagnostic = diagnostic.replace(value, "<local-path>")
                print(f"FAIL {label}\n{diagnostic}", file=sys.stderr)
                raise SystemExit(result.returncode)
            print(f"PASS {label}")
            return result.stdout + result.stderr

        check("delivery safeguards", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"])
        check("terraform fmt", [terraform, "fmt", "-check", "-recursive", "-diff"])
        init = [terraform, "init", "-backend=false", "-input=false", "-lockfile=readonly", "-no-color"]
        if args.plugin_dir:
            init.append(f"-plugin-dir={args.plugin_dir.resolve()}")
        check("terraform init (backend disabled)", init)
        check("terraform validate", [terraform, "validate", "-no-color"])
        summary = check("terraform test (AzureRM mock only)", [terraform, "test", "-filter=tests/vm.tftest.hcl", "-no-color"])
        match = re.search(r"Success! \d+ passed, \d+ failed\.", summary)
        if not match:
            raise SystemExit("Mock test success summary missing; inspect the test runner before claiming success.")
        print(match.group(0))
        print("No Azure authentication, cloud deployment, real plan/apply/destroy, or screenshot capture performed.")


if __name__ == "__main__":
    main()
