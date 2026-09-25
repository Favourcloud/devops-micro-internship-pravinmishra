#!/usr/bin/env python3
"""Fixed, non-root systemd service definitions. Config is a non-secret systemd credential."""
from common import CONFIGURATION, ROOT

SERVICES = {
    "book-router": ("book-router", "router.py", "", True),
    "book-app": ("book-app", "supervisor.py", "Wants=book-router.service\nAfter=book-router.service\n", False),
    "book-web": ("book-web", "web.py", "", True),
    "book-health": ("book-web", "readiness.py", "After=book-web.service\nWants=book-web.service\n", False),
    "book-initialize": ("book-init", "initialize.py", "", False),
    "book-nginx": ("book-web", None, "After=book-web.service book-health.service\nWants=book-web.service book-health.service\n", True),
}


def unit(name):
    user, script, dependencies, quiet = SERVICES[name]
    command = f"/usr/bin/python3 -B {CONFIGURATION}/{script}"
    extra = ""
    if name == "book-nginx":
        command = f"/usr/sbin/nginx -c {ROOT}/nginx.conf -g 'daemon off;'"
        extra = "AmbientCapabilities=CAP_NET_BIND_SERVICE\nCapabilityBoundingSet=CAP_NET_BIND_SERVICE\n"
    else:
        extra = "CapabilityBoundingSet=\n"
    if name == "book-web":
        extra += f"ReadWritePaths={ROOT}/application/frontend/.next/cache\n"
    one_shot = name == "book-initialize"
    return f"""[Unit]
Description=Book Review {name} (source preparation; future approved operation)
After=network-online.target
Wants=network-online.target
{dependencies}StartLimitIntervalSec=900
StartLimitBurst=3

[Service]
Type={'oneshot' if one_shot else 'simple'}
User={user}
Group={user}
UMask=0077
LoadCredential=config:/etc/book-review/config.json
RuntimeDirectory={name}
RuntimeDirectoryMode=0700
WorkingDirectory={ROOT}
ExecStartPre=/usr/bin/python3 -B {CONFIGURATION}/common.py
ExecStart={command}
Restart={'no' if one_shot else 'on-failure'}
RestartSec=15
TimeoutStartSec=300
TimeoutStopSec=20
KillMode=control-group
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateDevices=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
ProtectClock=yes
ProtectHostname=yes
ProtectProc=invisible
RestrictSUIDSGID=yes
RestrictNamespaces=yes
RestrictRealtime=yes
LockPersonality=yes
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
LimitCORE=0
Environment=PYTHONDONTWRITEBYTECODE=1
Environment=TMPDIR=/run/{name}
StandardOutput={'null' if quiet else 'journal'}
StandardError={'null' if quiet else 'journal'}
{extra}
[Install]
WantedBy=multi-user.target
"""
