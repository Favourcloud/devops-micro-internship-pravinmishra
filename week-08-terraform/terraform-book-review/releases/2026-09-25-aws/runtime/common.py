#!/usr/bin/env python3
"""Shared non-secret configuration, verified database TLS, and secret handling."""
import json
import os
from pathlib import Path
import re
import ssl
import stat
import subprocess
import urllib.parse

from upstream import digest, https_url

ROOT = Path("/opt/book-review")
CONFIGURATION = ROOT / "configuration"
CA_FILE = Path("/etc/book-review/rds-ca.pem")
SAFE_ENV = {"PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8",
            "AWS_PAGER": "", "AWS_CLI_AUTO_PROMPT": "off", "AWS_MAX_ATTEMPTS": "2"}
IDENTIFIER = re.compile(r"[a-z][a-z0-9_]{0,47}\Z")
DNS = re.compile(r"(?=.{1,253}\Z)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z][a-z0-9-]{1,62}\Z")
ARN = re.compile(r"arn:aws:secretsmanager:([a-z]{2}-[a-z]+-[0-9]):[0-9]{12}:secret:[A-Za-z0-9/_+=.@-]+\Z")


class RuntimeFailure(Exception):
    """Only fixed status codes, never raw SDK/SQL/child exception text, may be logged."""


def hostname(value):
    if not isinstance(value, str) or not DNS.fullmatch(value):
        raise RuntimeFailure("invalid_hostname")
    return value


def origin(value, scheme):
    if not isinstance(value, str):
        raise RuntimeFailure("invalid_origin")
    parsed = urllib.parse.urlsplit(value)
    if (parsed.scheme != scheme or parsed.netloc != parsed.hostname
            or parsed.path or parsed.query or parsed.fragment or parsed.username):
        raise RuntimeFailure("invalid_origin")
    hostname(parsed.hostname)
    return value


def validate_config(config):
    config = dict(config)
    config.setdefault("release_authorized", False)
    if type(config["release_authorized"]) is not bool:
        raise RuntimeFailure("invalid_release_authorization")
    common = {"tier", "region", "public_origin", "internal_url", "db_host", "replica_host", "db_name",
              "release_authorized"}
    artifact_keys = {"runtime_artifact_url", "runtime_artifact_sha256"}
    ca_keys = {"rds_ca_path", "rds_ca_sha256"}
    tier_keys = {
        "web": artifact_keys,
        "app": artifact_keys | ca_keys | {"app_secret_arn", "app_secret_version", "router_secret_arn"},
        "initializer": ca_keys | {"app_secret_arn", "app_secret_version", "master_secret_arn", "master_secret_version"},
    }
    tier = config.get("tier")
    if tier not in tier_keys or set(config) != common | tier_keys[tier]:
        raise RuntimeFailure("invalid_config_keys")
    if not re.fullmatch(r"[a-z]{2}-[a-z]+-[0-9]", config["region"]):
        raise RuntimeFailure("invalid_region")
    origin(config["public_origin"], "https")
    origin(config["internal_url"], "http")
    for key in ("db_host", "replica_host"):
        hostname(config[key])
    if config["db_host"] == config["replica_host"] or not IDENTIFIER.fullmatch(config["db_name"]):
        raise RuntimeFailure("invalid_database")
    if tier != "initializer":
        https_url(config["runtime_artifact_url"])
    if tier != "web" and config["rds_ca_path"] != str(CA_FILE):
        raise RuntimeFailure("invalid_rds_ca_path")
    for key in (key for key in config if key.endswith("_sha256")):
        if not re.fullmatch(r"[0-9a-f]{64}", config[key]):
            raise RuntimeFailure("invalid_artifact_digest")
    for key in (key for key in tier_keys[tier] if key.endswith("_arn")):
        match = ARN.fullmatch(config[key])
        if not match or match[1] != config["region"]:
            raise RuntimeFailure("invalid_secret_arn")
    for key in (key for key in tier_keys[tier] if key.endswith("_secret_version")):
        if not re.fullmatch(r"[A-Za-z0-9-]{32,64}", config[key]):
            raise RuntimeFailure("invalid_secret_version")
    arns = [config[key] for key in tier_keys[tier] if key.endswith("_arn")]
    if len(set(arns)) != len(arns):
        raise RuntimeFailure("secret_identities_must_differ")
    return config


def require_release(config):
    if config.get("release_authorized") is not True:
        raise RuntimeFailure("runtime_release_not_authorized")


def load_config(path=None):
    systemd = path is None
    if path is None:
        credential_dir = os.environ.get("CREDENTIALS_DIRECTORY")
        if not credential_dir:
            raise RuntimeFailure("missing_systemd_config_credential")
        path = Path(credential_dir) / "config"
    file = Path(path)
    credential = (systemd and file.parts[:3] == ("/", "run", "credentials")
                  and len(file.parts) == 5 and file.name == "config"
                  and file.stat().st_uid == 0 and stat.S_IMODE(file.stat().st_mode) == 0o440
                  and all(not parent.is_symlink() and parent.stat().st_uid == 0
                          and not parent.stat().st_mode & 0o022 for parent in file.parents))
    if file.is_symlink() or not file.is_file() or (stat.S_IMODE(file.stat().st_mode) & 0o077 and not credential):
        raise RuntimeFailure("unsafe_config_permissions")
    config = validate_config(json.loads(file.read_text()))
    require_release(config)
    return config


def private_write(path, content):
    path = Path(path)
    parent = path.parent
    if (parent.is_symlink() or not parent.is_dir()
            or stat.S_IMODE(parent.stat().st_mode) != 0o700
            or parent.stat().st_uid != os.geteuid()):
        raise RuntimeFailure("unsafe_runtime_directory")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as handle:
        os.fchmod(handle.fileno(), 0o600)
        handle.write(content)


def fetch_secret(config, kind, runner=subprocess.run):
    require_release(config)
    key = kind + "_secret_arn"
    allowed = {"app": {"app", "router"}, "initializer": {"app", "master"}, "web": set()}
    if kind not in allowed[config["tier"]]:
        raise RuntimeFailure("secret_scope_denied")
    command = ["aws", "secretsmanager", "get-secret-value", "--region", config["region"],
               "--secret-id", config[key], "--output", "json", "--no-cli-pager",
               "--cli-connect-timeout", "5", "--cli-read-timeout", "10"]
    version = config[kind + "_secret_version"] if kind in ("app", "master") else None
    if version is not None:
        command += ["--version-id", version]
    try:
        result = runner(command, env=SAFE_ENV, capture_output=True, timeout=25, check=True)
        if len(result.stdout) > 131072:
            raise RuntimeFailure("secret_response_oversized")
        response = json.loads(result.stdout)
        if response.get("ARN") != config[key]:
            raise RuntimeFailure("secret_identity_mismatch")
        if version is not None and response.get("VersionId") != version:
            raise RuntimeFailure("secret_version_mismatch")
        value = json.loads(response["SecretString"])
        required = {"app": {"username", "password", "jwt_secret"},
                    "master": {"username", "password"}, "router": {"certificate", "private_key"}}[kind]
        if not isinstance(value, dict) or set(value) != required:
            raise RuntimeFailure("secret_shape_invalid")
        if any(not isinstance(v, str) or not v or "\x00" in v for v in value.values()):
            raise RuntimeFailure("secret_value_invalid")
        if kind in ("app", "master"):
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,31}", value["username"]):
                raise RuntimeFailure("secret_username_invalid")
        if kind == "app" and len(value["jwt_secret"].encode()) < 32:
            raise RuntimeFailure("jwt_too_short")
        return value
    except Exception:
        raise RuntimeFailure("secret_read_failed") from None


def verified_ca(config):
    if config.get("rds_ca_path") != str(CA_FILE):
        raise RuntimeFailure("invalid_rds_ca_path")
    path = Path(config["rds_ca_path"])
    if path.is_symlink():
        raise RuntimeFailure("unsafe_rds_ca_file")
    for parent in path.parents:
        if parent.is_symlink() or parent.stat().st_uid != 0 or parent.stat().st_mode & 0o022:
            raise RuntimeFailure("unsafe_rds_ca_file")
    metadata = path.stat()
    if (not path.is_file() or metadata.st_uid != 0
            or metadata.st_mode & 0o022 or metadata.st_size > 1024 * 1024):
        raise RuntimeFailure("unsafe_rds_ca_file")
    with path.open("rb") as handle:
        content = handle.read(1024 * 1024 + 1)
    if len(content) > 1024 * 1024 or digest(content) != config["rds_ca_sha256"]:
        raise RuntimeFailure("rds_ca_digest_mismatch")
    return str(path)


def connect_db(config, secret, *, replica=False, database=True, driver=None):
    require_release(config)
    if driver is None:
        import pymysql as driver
    context = ssl.create_default_context(cafile=verified_ca(config))
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    class RequiredTLSConnection(driver.connections.Connection):
        def _require_tls(self):
            if (not self._secure or not isinstance(self._sock, ssl.SSLSocket)
                    or self._sock.context is not self.ctx
                    or self._sock.server_hostname != self.host or not self._sock.cipher()):
                raise RuntimeFailure("database_tls_not_negotiated")

        def _request_authentication(self):
            if (not self.ssl or not isinstance(self.ctx, ssl.SSLContext)
                    or self.ctx.verify_mode != ssl.CERT_REQUIRED or not self.ctx.check_hostname
                    or not self.server_capabilities & driver.constants.CLIENT.SSL):
                raise RuntimeFailure("database_verified_tls_required")
            super()._request_authentication()
            self._require_tls()

        def _execute_command(self, command, sql):
            self._require_tls()
            return super()._execute_command(command, sql)

    return RequiredTLSConnection(host=config["replica_host" if replica else "db_host"], port=3306,
                          user=secret["username"], password=secret["password"],
                          database=config["db_name"] if database else None,
                          ssl=context,
                          connect_timeout=5, read_timeout=5, write_timeout=5,
                          autocommit=True, charset="utf8mb4")


def child_environment(config, secret=None):
    require_release(config)
    env = {"PATH": SAFE_ENV["PATH"], "LANG": "C.UTF-8", "NODE_ENV": "production",
           "NEXT_TELEMETRY_DISABLED": "1", "HOME": "/nonexistent"}
    if secret:
        env.update(PORT="3001", DB_HOST="127.0.0.1", DB_PORT="6446", DB_NAME=config["db_name"],
                   DB_USER=secret["username"], DB_PASS=secret["password"], JWT_SECRET=secret["jwt_secret"],
                   ALLOWED_ORIGINS=config["public_origin"], TMPDIR="/run/book-app")
    else:
        env.update(NEXT_PUBLIC_API_URL=config["public_origin"], TMPDIR="/run/book-web")
    return env


if __name__ == "__main__":
    try:
        load_config()
    except Exception:
        raise SystemExit("runtime_release_gate_failed") from None
