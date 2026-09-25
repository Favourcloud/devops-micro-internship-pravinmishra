#!/usr/bin/env python3
"""Configure verified-TLS MySQL Router."""
import os
from pathlib import Path
import shutil
import ssl
import sys
from common import CONFIGURATION, SAFE_ENV, RuntimeFailure, fetch_secret, load_config, private_write, verified_ca


def configure_apparmor(write, run):
    profile = Path('/etc/apparmor.d/usr.bin.mysqlrouter')
    text = profile.read_text()
    rules = '  owner /run/book-router/** rw,\n  /etc/book-review/rds-ca.pem r,\n'
    if rules not in text:
        if not text.rstrip().endswith('}'):
            raise RuntimeFailure('router_apparmor_profile_invalid')
        write(profile, text.rstrip()[:-1] + rules + '}\n')
    run(['/usr/sbin/apparmor_parser', '-r', str(profile)])


def render(config):
    return (CONFIGURATION / "mysqlrouter.conf.template").read_text().replace("@@DB_HOST@@", config["db_host"])


def main():
    try:
        config = load_config()
        if config["tier"] != "app":
            raise RuntimeFailure("router_wrong_tier")
        verified_ca(config)
        secret = fetch_secret(config, "router")
        directory = Path("/run/book-router")
        private_write(directory / "certificate.pem", secret["certificate"])
        private_write(directory / "private-key.pem", secret["private_key"])
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(directory / "certificate.pem", directory / "private-key.pem", password=lambda: "")
        private_write(directory / "router.conf", render(config))
        executable = shutil.which("mysqlrouter", path=SAFE_ENV["PATH"])
        if not executable:
            raise RuntimeFailure("router_missing")
        os.execve(executable, [executable, "--config", str(directory / "router.conf")],
                  dict(SAFE_ENV, HOME="/nonexistent", TMPDIR=str(directory)))
    except Exception:
        print("router_service_failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    if sys.argv[1:] == ['--configure-apparmor']:
        if os.geteuid() != 0:
            raise SystemExit('router_apparmor_requires_root')
        from bootstrap import root_write, run
        configure_apparmor(root_write, run)
    else:
        sys.exit(main())
