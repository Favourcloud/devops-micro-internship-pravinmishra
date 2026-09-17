#!/usr/bin/env python3
"""Run Next's unchanged production server (not a static export) on loopback only."""
import os
import shutil
import sys
from common import ROOT, SAFE_ENV, RuntimeFailure, child_environment, load_config


def main():
    try:
        config = load_config()
        if config["tier"] != "web":
            raise RuntimeFailure("web_wrong_tier")
        executable = shutil.which("node", path=SAFE_ENV["PATH"])
        if not executable:
            raise RuntimeFailure("node_missing")
        os.chdir(ROOT / "application/frontend")
        os.execve(executable, [executable, "node_modules/next/dist/bin/next", "start", "--hostname", "127.0.0.1", "--port", "3000"],
                  child_environment(config))
    except Exception:
        print("web_service_failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
