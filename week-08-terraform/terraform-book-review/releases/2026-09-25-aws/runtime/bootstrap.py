#!/usr/bin/env python3
"""Verify the image and artifact; configure services."""
import grp
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import pwd
import re
import shutil
import ssl
import stat
import subprocess
import sys

from artifact import MAX_ARCHIVE, MAX_EXPANDED, install_artifact
from common import CONFIGURATION, ROOT, SAFE_ENV, RuntimeFailure, load_config, require_release, verified_ca
from services import SERVICES, unit
from upstream import download


def run(command):
    timeout = 330 if command[:1] == ["systemctl"] else 30
    return subprocess.run(command, env=SAFE_ENV, check=True, capture_output=True, timeout=timeout)


def runtime_versions():
    commands = {"node": ["node", "--version"], "npm": ["npm", "--version"],
                "nginx": ["/usr/sbin/nginx", "-v"], "mysqlrouter": ["mysqlrouter", "--version"],
                "awscli": ["aws", "--version"]}
    patterns = {"node": r"v(22\.[0-9]+\.[0-9]+)", "npm": r"(10\.[0-9]+\.[0-9]+)",
                "nginx": r"nginx/([0-9]+\.[0-9]+\.[0-9]+)",
                "mysqlrouter": r"(?:Ver|version)\s+(8\.4\.[0-9]+)",
                "awscli": r"aws-cli/(2\.[0-9]+\.[0-9]+)"}
    versions = {}
    for tool, command in commands.items():
        result = run(command)
        match = re.search(patterns[tool], (result.stdout + result.stderr).decode())
        if not match:
            raise RuntimeFailure("unsupported_runtime_version")
        versions[tool] = match[1]
    if tuple(map(int, versions["nginx"].split("."))) < (1, 24, 0):
        raise RuntimeFailure("unsupported_nginx")
    versions["python"] = platform.python_version()
    versions["PyMySQL"] = importlib.metadata.version("PyMySQL")
    if not versions["python"].startswith("3.12.") or versions["PyMySQL"] != "1.1.1":
        raise RuntimeFailure("unsupported_python_dependencies")
    return versions


def prerequisites():
    if os.geteuid() != 0 or platform.system() != "Linux" or platform.machine() != "x86_64":
        raise RuntimeFailure("unsupported_runtime_platform")
    release = dict(line.split("=", 1) for line in Path("/etc/os-release").read_text().splitlines() if "=" in line)
    if release.get("ID", "").strip('"') != "ubuntu" or release.get("VERSION_ID", "").strip('"') != "24.04":
        raise RuntimeFailure("unsupported_os")
    if run(["findmnt", "-n", "-o", "FSTYPE", "/run"]).stdout.strip() != b"tmpfs":
        raise RuntimeFailure("runtime_directory_not_ram_backed")
    if not Path("/run/systemd/system").is_dir():
        raise RuntimeFailure("systemd_required")
    if any(path.is_symlink() or path.stat().st_uid != 0 or stat.S_IMODE(path.stat().st_mode) & 0o022
           for path in [CONFIGURATION, *CONFIGURATION.rglob("*")]):
        raise RuntimeFailure("configuration_not_root_controlled")
    return runtime_versions()


def ensure_user(name):
    try:
        account = pwd.getpwnam(name)
    except KeyError:
        run(["/usr/sbin/useradd", "--system", "--user-group", "--home-dir", "/nonexistent", "--shell", "/usr/sbin/nologin", name])
        account = pwd.getpwnam(name)
    if (account.pw_uid == 0 or account.pw_gid == 0 or grp.getgrgid(account.pw_gid).gr_name != name
            or account.pw_shell != "/usr/sbin/nologin" or account.pw_dir != "/nonexistent"):
        raise RuntimeFailure("unsafe_existing_service_identity")
    return account


def root_write(path, text, mode=0o644):
    path = Path(path)
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise RuntimeFailure("configuration_symlink_denied")
    with path.open("w") as handle:
        handle.write(text)
    path.chmod(mode)


def render_nginx(config):
    text = (CONFIGURATION / "nginx.conf.template").read_text()
    for key, value in {"PUBLIC_HOST": config["public_origin"].removeprefix("https://"),
                       "INTERNAL_URL": config["internal_url"],
                       "INTERNAL_HOST": config["internal_url"].removeprefix("http://")}.items():
        text = text.replace("@@" + key + "@@", value)
    return text


def bootstrap(config):
    require_release(config)
    versions = prerequisites()
    if (ROOT.is_symlink() or ROOT.stat().st_uid != 0 or ROOT.stat().st_mode & 0o022
            or any(parent.is_symlink() for parent in ROOT.parents)):
        raise RuntimeFailure("unsafe_installation_root")
    selected = {"web": ["book-web", "book-health", "book-nginx"],
                "app": ["book-router", "book-app"], "initializer": ["book-initialize"]}[config["tier"]]
    accounts = {name: ensure_user(name) for name in {SERVICES[service][0] for service in selected}}
    if len({account.pw_uid for account in accounts.values()}) != len(accounts):
        raise RuntimeFailure("service_identity_collision")
    if config["tier"] in ("app", "initializer"):
        ssl.create_default_context(cafile=verified_ca(config))
    if config["tier"] == "app":
        run(['/usr/bin/python3', '-B', str(CONFIGURATION / 'router.py'), '--configure-apparmor'])
    if config["tier"] != "initializer":
        if shutil.disk_usage(ROOT).free < MAX_EXPANDED + MAX_ARCHIVE + 512 * 1024 * 1024:
            raise RuntimeFailure("runtime_disk_safety_floor")
        artifact = download(config["runtime_artifact_url"], MAX_ARCHIVE)
        destination = ROOT / "application"
        install_artifact(artifact, config, destination, versions)
        for directory in [destination, *(p for p in destination.rglob("*") if p.is_dir())]:
            directory.chmod(0o755)
        if config["tier"] == "web":
            if "nameserver 127.0.0.53" not in Path("/etc/resolv.conf").read_text():
                raise RuntimeFailure("systemd_dns_stub_required")
            cache = destination / "frontend/.next/cache"
            cache.mkdir(exist_ok=True)
            for path in [cache, *cache.rglob("*")]:
                os.chown(path, accounts["book-web"].pw_uid, accounts["book-web"].pw_gid)
            root_write(ROOT / "nginx.conf", render_nginx(config))
            # Use only our dedicated non-root service, not an AMI's default public site.
            run(["systemctl", "disable", "--now", "nginx.service"])
    for name in selected:
        root_write(Path("/etc/systemd/system") / (name + ".service"), unit(name))
    run(["systemctl", "daemon-reload"])
    for name in selected:
        run(["systemctl", "enable", "--now", name + ".service"])
    root_write(ROOT / "installation.json", json.dumps({"status": "configured_not_cloud_verified",
               "tier": config["tier"], "runtime_artifact_sha256": config.get("runtime_artifact_sha256"),
               "versions": versions}, sort_keys=True) + "\n")


def main():
    try:
        if len(sys.argv) != 2 or sys.argv[1] != "/etc/book-review/config.json":
            raise RuntimeFailure("config_path_denied")
        bootstrap(load_config(sys.argv[1]))
        print("runtime_configured_readiness_not_yet_verified")
        return 0
    except Exception:
        print("runtime_bootstrap_failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
