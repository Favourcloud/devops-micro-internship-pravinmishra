#!/usr/bin/env python3
"""Run local onboarding checks without installing hooks in the shared repository."""

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone


PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[1]
RELATIVE_PROJECT = PROJECT.relative_to(REPO)
VENV = PROJECT / ".venv"
IGNORED = {".venv", ".ansible", ".cache", "__pycache__", "evidence"}
ENV = os.environ.copy()
# Keep the verification local even when invoked from a shell used for remote labs.
for name in list(ENV):
    if name.startswith(("ANSIBLE_", "GIT_")) or name == "PRE_COMMIT_HOME":
        del ENV[name]
ENV.update(
    PATH=f"{VENV / 'bin'}{os.pathsep}{ENV['PATH']}",
    ANSIBLE_CONFIG=str(PROJECT / "ansible.cfg"),
    ANSIBLE_NOCOLOR="1",
    PRE_COMMIT_COLOR="never",
)
RESULTS = []


def sanitize(text):
    for path, token in ((PROJECT, "{PROJECT}"), (REPO, "{REPOSITORY}"), (Path.home(), "{HOME}")):
        text = text.replace(str(path), token)
    return text


def run(name, command, *, cwd=PROJECT, env=None, expect=0):
    result = subprocess.run(
        command, cwd=cwd, env=env or ENV, capture_output=True, text=True, timeout=240, check=False
    )
    output = sanitize(result.stdout + result.stderr)
    RESULTS.append(
        {
            "name": name,
            "command": sanitize(" ".join(str(arg) for arg in command)),
            "exit_code": result.returncode,
            "expected_exit_code": expect,
            "output": output,
        }
    )
    print(f"{name}: exit {result.returncode}", flush=True)
    if result.returncode != expect:
        raise RuntimeError(f"{name} failed:\n{output}")
    return output


def check_recap(output):
    if not re.search(r"localhost\s+:\s+ok=4\s+changed=0\s+unreachable=0\s+failed=0", output):
        raise RuntimeError("The smoke test did not produce the expected clean localhost recap")


def verify_hooks(scratch):
    fixture = scratch / "repository"
    destination = fixture / RELATIVE_PROJECT
    shutil.copytree(PROJECT, destination, ignore=shutil.ignore_patterns(*IGNORED))
    fixture_env = ENV | {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "ANSIBLE_CONFIG": str(destination / "ansible.cfg"),
        "PRE_COMMIT_HOME": str(scratch / "pre-commit-cache"),
    }
    run(
        "isolated git init",
        ["git", "init", "--quiet", "--initial-branch=main", "--template="],
        cwd=fixture,
        env=fixture_env,
    )
    run("isolated git add", ["git", "add", "."], cwd=fixture, env=fixture_env)
    (destination / ".venv").symlink_to(VENV, target_is_directory=True)
    pre_commit = [str(VENV / "bin/pre-commit")]
    config = str(RELATIVE_PROJECT / ".pre-commit-config.yaml")
    run("isolated hook install", pre_commit + ["install", "--config", config], cwd=fixture, env=fixture_env)
    if not (fixture / ".git/hooks/pre-commit").is_file():
        raise RuntimeError("The isolated hook was not installed")
    command = pre_commit + ["run", "--config", config, "--all-files"]
    passing = run("isolated hooks pass", command, cwd=fixture, env=fixture_env)
    for hook in ("Week 09 yamllint", "Week 09 ansible-lint"):
        if not re.search(re.escape(hook) + r"\.+Passed", passing):
            raise RuntimeError(f"{hook} did not run and pass")

    run(
        "installed hook execution",
        [str(fixture / ".git/hooks/pre-commit")],
        cwd=fixture,
        env=fixture_env,
    )
    bad_yaml = destination / "playbooks/invalid.yml"
    bad_yaml.write_text("---\nbroken: [\n", encoding="utf-8")
    rejected = run("isolated malformed YAML rejected", command, cwd=fixture, env=fixture_env, expect=1)
    if "syntax error" not in rejected:
        raise RuntimeError("The negative YAML test failed for an unexpected reason")
    bad_yaml.unlink()
    smoke = destination / "playbooks/smoke.yml"
    good_smoke = smoke.read_text(encoding="utf-8")
    smoke.write_text(good_smoke.replace("ansible.builtin.ping:", "ping:"), encoding="utf-8")
    rejected = run(
        "isolated non-FQCN module rejected",
        pre_commit + ["run", "onboarding-ansible-lint", "--config", config, "--all-files"],
        cwd=fixture,
        env=fixture_env,
        expect=1,
    )
    if "fqcn[action-core]" not in rejected:
        raise RuntimeError("The negative Ansible test failed for an unexpected reason")
    smoke.write_text(good_smoke, encoding="utf-8")
    run("isolated hooks restored", command, cwd=fixture, env=fixture_env)


def main():
    run("dependency consistency", [str(VENV / "bin/python"), "-m", "pip", "check"])
    frozen = run("dependency lock match", [str(VENV / "bin/python"), "-m", "pip", "freeze"])
    if frozen.strip() != (PROJECT / "requirements.txt").read_text(encoding="utf-8").strip():
        raise RuntimeError("Installed dependencies differ from requirements.txt")
    for tool in ("python", "ansible", "ansible-lint", "yamllint", "pre-commit"):
        run(f"{tool} version", [str(VENV / f"bin/{tool}"), "--version"])
    config = run("project configuration", ["ansible-config", "dump", "--only-changed"])
    if "CONFIG_FILE() = {PROJECT}/ansible.cfg" not in config:
        raise RuntimeError("Ansible did not load the project configuration")
    if not re.search(r"^HOST_KEY_CHECKING\([^\n]+\) = True$", config, re.MULTILINE):
        raise RuntimeError("SSH host-key checking must remain enabled")
    inventory = run("local inventory", ["ansible-inventory", "--list"])
    hosts = json.loads(inventory)["_meta"]["hostvars"]
    if set(hosts) != {"localhost"} or hosts["localhost"]["ansible_connection"] != "local":
        raise RuntimeError("Only localhost using a local connection is allowed")
    run("shell syntax", ["bash", "-n", "scripts/lint.sh"])
    run("unknown lint option rejected", ["bash", "scripts/lint.sh", "unknown"], expect=2)
    run("yamllint", ["bash", "scripts/lint.sh", "yamllint"])
    lint_output = run("ansible-lint", ["bash", "scripts/lint.sh", "ansible-lint"])
    if "incompatible custom yamllint configuration" in lint_output:
        raise RuntimeError("yamllint settings must agree with ansible-lint")
    playbook = ["ansible-playbook", "playbooks/smoke.yml"]
    run("playbook syntax", playbook + ["--syntax-check"])
    run("playbook target list", playbook + ["--list-hosts"])
    check_recap(run("playbook check mode", playbook + ["--check"]))
    check_recap(run("playbook normal mode", playbook))
    for filename in ("settings.json", "extensions.json"):
        json.loads((PROJECT / ".vscode" / filename).read_text(encoding="utf-8"))
    scratch_parent = REPO / ".tools"
    scratch_parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="w9-validation-", dir=scratch_parent) as scratch:
        verify_hooks(Path(scratch))
    sources = {
        str(path.relative_to(PROJECT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(PROJECT.rglob("*"))
        if path.is_file() and not set(path.relative_to(PROJECT).parts).intersection(IGNORED)
    }
    evidence = {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "learner": "Eze Favour",
        "scope": "Week 09 Assignment 1: local workstation validation only",
        "machine": {"system": os.uname().sysname, "architecture": os.uname().machine},
        "status": "Local checks passed; complete assignment evidence remains pending",
        "no_cloud_operations": True,
        "no_remote_ssh_test": True,
        "no_global_git_or_ssh_changes": True,
        "hook_installation_scope": "Disposable isolated Git fixture only; removed after validation",
        "screenshots_created": 0,
        "remaining": [
            "Ten genuine assignment screenshots",
            "VS Code extension installation and interactive workspace verification",
            "Approved SSH key/agent/host configuration and evidence",
            "Personal Git default-branch/signing policy and actual clone hook setup",
        ],
        "checks": RESULTS,
        "source_sha256": sources,
    }
    target = PROJECT / "evidence/local-validation.json"
    target.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {len(RESULTS)} command checks; evidence/local-validation.json written")


if __name__ == "__main__":
    main()
