"""Runtime contracts with explicit fake subprocess, HTTP, DB and Linux process state."""
import ast
import contextlib
import gzip
import io
import json
import os
from pathlib import Path
import re
import shutil
import ssl
import subprocess
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))
import common
import bootstrap
import initialize
import probes
import readiness
import report_replica
import router
import services
import supervisor

# Clearly synthetic inert fixture values; not real secret material or evidence.
SYNTHETIC_APP = {"username": "synthetic_app", "password": "SYNTHETIC_INERT_quoted_'_not_a_password",
                 "jwt_secret": "SYNTHETIC_INERT_NOT_A_SIGNING_KEY_1234567890"}
SYNTHETIC_MASTER = {"username": "synthetic_master", "password": "SYNTHETIC_INERT_MASTER"}


def config(tier="app"):
    value = {"tier": tier, "release_authorized": True, "region": "eu-west-2", "public_origin": "https://books.example.invalid",
             "internal_url": "http://internal.example.invalid", "db_host": "primary.example.invalid",
             "replica_host": "replica.example.invalid", "db_name": "book_review"}
    if tier != "initializer":
        value.update(runtime_artifact_url="https://artifacts.example.invalid/runtime.tar.gz",
                     runtime_artifact_sha256="0" * 64)
    if tier != "web":
        value.update(rds_ca_path="/etc/book-review/rds-ca.pem", rds_ca_sha256="1" * 64)
        value.update(app_secret_arn="arn:aws:secretsmanager:eu-west-2:000000000000:secret:synthetic-app-000000",
                     app_secret_version="00000000-0000-0000-0000-000000000000")
        kind = "master" if tier == "initializer" else "router"
        value[kind + "_secret_arn"] = "arn:aws:secretsmanager:eu-west-2:000000000000:secret:synthetic-" + kind + "-000000"
        if tier == "initializer":
            value["master_secret_version"] = "11111111-1111-1111-1111-111111111111"
    return value


@contextlib.contextmanager
def scratch():
    path = ROOT / "runtime" / (".test-runtime-" + str(os.getpid()))
    path.mkdir(mode=0o700)
    try:
        yield path
    finally:
        shutil.rmtree(path)


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def execute(self, sql, params=None):
        self.sql, self.params = sql, params
        self.connection.events.append((sql, params))
        if self.connection.fail_sql and self.connection.fail_sql in sql:
            raise OSError("SYNTHETIC_SECRET_DATABASE_ERROR")
        if sql.startswith("CREATE USER "):
            self.connection.account_rows = [("%", "ANY")]
        if sql.startswith("GRANT "):
            target = f"`{params[0]}`@`{params[1]}`"
            self.connection.grants = [f"GRANT USAGE ON *.* TO {target}", sql.replace("%s@%s", target)]
    def fetchone(self):
        if "GET_LOCK" in self.sql:
            return (self.connection.acquire_results.pop(0) if self.connection.acquire_results else 1,)
        if "IS_USED_LOCK" in self.sql:
            return (self.connection.owner, 17)
        if "RELEASE_LOCK" in self.sql:
            return (self.connection.release_result,)
        if "@@global.read_only" in self.sql:
            return (self.connection.read_only,)
        if "@@GLOBAL.partial_revokes" in self.sql:
            return (self.connection.partial_revokes,)
        if "CURRENT_USER()" in self.sql:
            return (self.connection.current_user,)
        return (2,)
    def fetchall(self):
        if "FROM mysql.user" in self.sql:
            return self.connection.account_rows
        if self.sql.startswith("SHOW GRANTS"):
            return [(grant,) for grant in self.connection.grants]
        return [(column,) for column in self.connection.columns[self.params[1]]]


class FakeConnection:
    def __init__(self):
        self.events, self.acquire_results = [], [1]
        self.columns = {name: set(columns) for name, columns in supervisor.SCHEMA_COLUMNS.items()}
        self.owner, self.read_only, self.release_result, self.fail_sql = 17, 1, 1, None
        self.account_rows, self.grants, self.partial_revokes = [], [], 0
        self.current_user = SYNTHETIC_APP["username"] + "@%"
    def cursor(self):
        return FakeCursor(self)
    def close(self):
        self.events.append(("CLOSE", None))


class OfflineCase(unittest.TestCase):
    def setUp(self):
        self.addCleanup(mock.patch.stopall)
        mock.patch("socket.socket", side_effect=AssertionError("network forbidden in unit tests")).start()
        mock.patch("subprocess.Popen", side_effect=AssertionError("subprocess forbidden in unit tests")).start()


class ConfigAndSecretsTests(OfflineCase):
    def test_valid_tier_schemas(self):
        for tier in ("web", "app", "initializer"):
            self.assertEqual(common.validate_config(config(tier))["tier"], tier)

    def test_json_schema_tier_fields_match_runtime_contract(self):
        schema = json.loads((ROOT / "runtime/config.schema.json").read_text())
        for branch in schema["allOf"]:
            tier = branch["if"]["properties"]["tier"]["const"]
            required = set(schema["required"]) | set(branch["then"]["required"])
            forbidden = {key for clause in branch["then"]["not"]["anyOf"] for key in clause["required"]}
            allowed = set(schema["properties"]) - forbidden
            expected = set(config(tier))
            self.assertEqual(required, expected - {"release_authorized"})
            self.assertEqual(allowed, expected)

    def test_release_authorization_defaults_false_and_requires_boolean(self):
        original = config()
        original.pop("release_authorized")
        validated = common.validate_config(original)
        self.assertIs(validated["release_authorized"], False)
        self.assertNotIn("release_authorized", original)
        for value in ("false", "true", 0, 1, None, [], {}):
            with self.subTest(value=value), self.assertRaises(common.RuntimeFailure):
                common.validate_config(dict(config(), release_authorized=value))
        with self.assertRaisesRegex(common.RuntimeFailure, "runtime_release_not_authorized"):
            common.require_release(validated)

    def test_release_denial_precedes_bootstrap_downloads_and_local_commands(self):
        for tier in ("web", "app", "initializer"):
            with self.subTest(tier=tier), mock.patch.object(bootstrap, "prerequisites") as prereqs, mock.patch.object(bootstrap, "download") as download, mock.patch.object(bootstrap, "run") as run:
                with self.assertRaisesRegex(common.RuntimeFailure, "runtime_release_not_authorized"):
                    bootstrap.bootstrap(dict(config(tier), release_authorized=False))
            prereqs.assert_not_called()
            download.assert_not_called()
            run.assert_not_called()

    def test_release_denial_precedes_secret_database_and_child_operations(self):
        denied = dict(config(), release_authorized=False)
        runner, driver, popen, connector = mock.Mock(), mock.Mock(), mock.Mock(), mock.Mock()
        for operation in (
            lambda: common.fetch_secret(denied, "app", runner),
            lambda: common.connect_db(denied, SYNTHETIC_APP, driver=driver),
            lambda: common.child_environment(denied, SYNTHETIC_APP),
            lambda: supervisor.start_once(denied, SYNTHETIC_APP, connector=connector, popen=popen),
            lambda: initialize.initialize(dict(config("initializer"), release_authorized=False), SYNTHETIC_MASTER, SYNTHETIC_APP, connector),
        ):
            with self.assertRaisesRegex(common.RuntimeFailure, "runtime_release_not_authorized"):
                operation()
        runner.assert_not_called()
        driver.connect.assert_not_called()
        connector.assert_not_called()
        popen.assert_not_called()

    def test_config_loader_blocks_unauthorized_services(self):
        with scratch() as directory:
            target = directory / "config.json"
            for value in (False, None):
                cfg = config()
                if value is None:
                    cfg.pop("release_authorized")
                else:
                    cfg["release_authorized"] = value
                common.private_write(target, json.dumps(cfg))
                with self.assertRaisesRegex(common.RuntimeFailure, "runtime_release_not_authorized"):
                    common.load_config(target)

    def test_config_denies_unsafe_hosts_urls_fields_versions(self):
        changes = [("public_origin", "http://books.example.invalid"),
                   ("public_origin", "https://books.example.invalid/"),
                   ("public_origin", "https://user:pass@books.example.invalid"),
                   ("internal_url", "http://internal.example.invalid:8080"),
                   ("db_host", "127.0.0.1"), ("db_host", "primary.example.invalid\nport=2"),
                   ("db_name", "schema`;DROP DATABASE other;--"),
                   ("replica_host", "primary.example.invalid"),
                   ("runtime_artifact_url", "http://artifacts.example.invalid/source"),
                   ("runtime_artifact_sha256", "wrong"), ("app_secret_version", "AWSCURRENT"),
                   ("app_secret_arn", "arn:aws:secretsmanager:us-east-1:000000000000:secret:wrong-000000"),
                   ("password", "SYNTHETIC_FORBIDDEN_CONFIG_SECRET")]
        for key, value in changes:
            with self.subTest(key=key, value=value), self.assertRaises(Exception):
                common.validate_config(dict(config(), **{key: value}))

    def test_tier_and_secret_identity_isolation(self):
        bad = config("web")
        bad["app_secret_arn"] = config()["app_secret_arn"]
        with self.assertRaises(common.RuntimeFailure):
            common.validate_config(bad)
        bad = config()
        bad["router_secret_arn"] = bad["app_secret_arn"]
        with self.assertRaises(common.RuntimeFailure):
            common.validate_config(bad)

    def test_private_files_and_config_permissions(self):
        with scratch() as directory:
            target = directory / "secret.txt"
            common.private_write(target, "SYNTHETIC_INERT_TEXT")
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            common.private_write(target, "SYNTHETIC_REPLACED")
            self.assertEqual(target.read_text(), "SYNTHETIC_REPLACED")
            (directory / "alias").symlink_to(target)
            with self.assertRaises(OSError):
                common.private_write(directory / "alias", "denied")
            target.write_text(json.dumps(config()))
            self.assertEqual(common.load_config(target), config())
            target.chmod(0o644)
            with self.assertRaises(common.RuntimeFailure):
                common.load_config(target)
            directory.chmod(0o755)
            with self.assertRaises(common.RuntimeFailure):
                common.private_write(target, "denied")

    def test_exact_arn_version_role_environment_and_redaction(self):
        response = {"ARN": config()["app_secret_arn"], "VersionId": config()["app_secret_version"],
                    "SecretString": json.dumps(SYNTHETIC_APP)}
        runner = mock.Mock(return_value=mock.Mock(stdout=json.dumps(response).encode()))
        self.assertEqual(common.fetch_secret(config(), "app", runner), SYNTHETIC_APP)
        args, kwargs = runner.call_args
        self.assertIn(config()["app_secret_arn"], args[0])
        self.assertIn(config()["app_secret_version"], args[0])
        self.assertEqual(kwargs["env"], common.SAFE_ENV)
        self.assertNotIn("AWS_PROFILE", kwargs["env"])
        self.assertNotIn("--endpoint-url", args[0])
        self.assertNotIn(SYNTHETIC_APP["password"], str(args))
        with self.assertRaises(common.RuntimeFailure):
            common.fetch_secret(config("web"), "app", runner)
        with self.assertRaises(common.RuntimeFailure):
            common.fetch_secret(config(), "master", runner)
        runner.side_effect = RuntimeError(SYNTHETIC_APP["password"])
        with self.assertRaisesRegex(common.RuntimeFailure, "^secret_read_failed$") as error:
            common.fetch_secret(config(), "app", runner)
        self.assertNotIn(SYNTHETIC_APP["password"], str(error.exception))

    def test_master_reads_exact_version_and_router_uses_agreed_bundle_keys(self):
        cfg = config("initializer")
        response = {"ARN": cfg["master_secret_arn"], "VersionId": cfg["master_secret_version"],
                    "SecretString": json.dumps(SYNTHETIC_MASTER)}
        runner = mock.Mock(return_value=mock.Mock(stdout=json.dumps(response).encode()))
        self.assertEqual(common.fetch_secret(cfg, "master", runner), SYNTHETIC_MASTER)
        command = runner.call_args.args[0]
        self.assertEqual(command[command.index("--version-id") + 1], cfg["master_secret_version"])
        response["VersionId"] = "22222222-2222-2222-2222-222222222222"
        runner.return_value.stdout = json.dumps(response).encode()
        with self.assertRaisesRegex(common.RuntimeFailure, "secret_read_failed"):
            common.fetch_secret(cfg, "master", runner)
        inert = {"certificate": "SYNTHETIC_INERT_CERT_NOT_PEM", "private_key": "SYNTHETIC_INERT_NOT_A_KEY"}
        runner.return_value.stdout = json.dumps({"ARN": config()["router_secret_arn"], "SecretString": json.dumps(inert)}).encode()
        self.assertEqual(common.fetch_secret(config(), "router", runner), inert)
        self.assertNotIn("--version-id", runner.call_args.args[0])
        old_fields = {"certificate_pem": inert["certificate"], "private_key_pem": inert["private_key"]}
        runner.return_value.stdout = json.dumps({"ARN": config()["router_secret_arn"], "SecretString": json.dumps(old_fields)}).encode()
        with self.assertRaisesRegex(common.RuntimeFailure, "secret_read_failed"):
            common.fetch_secret(config(), "router", runner)

    def test_tier_specific_ca_artifact_and_master_version_contract(self):
        self.assertNotIn("rds_ca_path", config("web"))
        self.assertNotIn("runtime_artifact_url", config("initializer"))
        for cfg in (dict(config(), rds_ca_path="/unexpected/ca.pem"),
                    dict(config(), rds_ca_url="https://example.invalid/ca.pem"),
                    dict(config("web"), rds_ca_path=str(common.CA_FILE)),
                    dict(config("initializer"), master_secret_version="AWSCURRENT"),
                    dict(config(), master_secret_version="0" * 32)):
            with self.assertRaises(common.RuntimeFailure):
                common.validate_config(cfg)
        schema = json.loads((ROOT / "runtime/config.schema.json").read_text())
        self.assertEqual(schema["properties"]["rds_ca_path"]["const"], str(common.CA_FILE))
        self.assertEqual(schema["properties"]["master_secret_version"]["pattern"], r"^[A-Za-z0-9-]{32,64}$")
        self.assertNotIn("rds_ca_url", schema["properties"])

    def test_secret_response_identity_version_and_shape_fail_closed(self):
        base = {"ARN": config()["app_secret_arn"], "VersionId": config()["app_secret_version"],
                "SecretString": json.dumps(SYNTHETIC_APP)}
        for changed in [{"ARN": "wrong"}, {"VersionId": "wrong"}, {"SecretString": "{}"},
                        {"SecretString": json.dumps(dict(SYNTHETIC_APP, jwt_secret="short"))}]:
            runner = mock.Mock(return_value=mock.Mock(stdout=json.dumps(dict(base, **changed)).encode()))
            with self.subTest(changed=changed), self.assertRaises(common.RuntimeFailure):
                common.fetch_secret(config(), "app", runner)

    def test_child_env_only_exact_consumed_keys_no_ambient_credentials(self):
        with mock.patch.dict(os.environ, {"AWS_SECRET_ACCESS_KEY": "SYNTHETIC_DO_NOT_INHERIT", "NODE_OPTIONS": "SYNTHETIC_DENIED"}):
            env = common.child_environment(config(), SYNTHETIC_APP)
        self.assertEqual(env["PORT"], "3001")
        self.assertEqual((env["DB_HOST"], env["DB_PORT"]), ("127.0.0.1", "6446"))
        self.assertEqual(env["JWT_SECRET"], SYNTHETIC_APP["jwt_secret"])
        self.assertEqual(env["DB_PASS"], SYNTHETIC_APP["password"])
        self.assertEqual(env["ALLOWED_ORIGINS"], config()["public_origin"])
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", env)
        self.assertNotIn("NODE_OPTIONS", env)
        web_env = common.child_environment(config("web"))
        self.assertEqual(web_env["NEXT_PUBLIC_API_URL"], config()["public_origin"])
        self.assertFalse(any(key.startswith("DB_") or key.startswith("JWT") for key in web_env))


class DeploymentManifestTests(OfflineCase):
    def test_each_tier_contains_complete_local_import_and_template_closure(self):
        runtime = ROOT / "runtime"
        manifest = json.loads((runtime / "deploy-manifest.json").read_text())
        modules = {path.stem: path.name for path in runtime.glob("*.py")}
        templates = {"web": {"nginx.conf.template"}, "app": {"mysqlrouter.conf.template"}, "initializer": set()}
        for tier, tier_files in manifest["tiers"].items():
            selected = manifest["common"] + tier_files
            self.assertEqual(len(selected), len(set(selected)))
            self.assertFalse(set(selected) & set(manifest["repository_only"]))
            self.assertTrue(templates[tier] <= set(selected))
            self.assertIn("source-lock.json", selected)
            for name in selected:
                self.assertTrue((runtime / name).is_file())
                if not name.endswith(".py"):
                    continue
                tree = ast.parse((runtime / name).read_text())
                for node in ast.walk(tree):
                    imports = [entry.name for entry in node.names] if isinstance(node, ast.Import) else []
                    if isinstance(node, ast.ImportFrom) and node.module:
                        imports.append(node.module)
                    for imported in imports:
                        if imported in modules:
                            self.assertIn(modules[imported], selected, (tier, name, imported))

    def test_reference_cloud_config_subsets_fit_compressed_payload_limit(self):
        # A local packaging regression only; the parent must check actual Terraform output.
        runtime = ROOT / "runtime"
        manifest = json.loads((runtime / "deploy-manifest.json").read_text())
        for tier, tier_files in manifest["tiers"].items():
            names = manifest["common"] + tier_files
            files = [(name, (runtime / name).read_text()) for name in names]
            files.append(("verify_upstream.py", (ROOT / "scripts/verify_upstream.py").read_text()))
            entries = [("/opt/book-review/configuration/" + name, text,
                        "0755" if name.endswith((".py", ".sh")) else "0644") for name, text in files]
            cfg = dict(config(tier), release_authorized=False)
            entries.append(("/etc/book-review/config.json", json.dumps(cfg, separators=(",", ":")) + "\n", "0600"))
            payload = "#cloud-config\nwrite_files:\n"
            for path, content, permissions in entries:
                payload += f'- path: {path}\n  owner: root:root\n  permissions: "{permissions}"\n  content: |\n'
                payload += "".join("    " + line + "\n" for line in content.splitlines())
            payload += "runcmd:\n- [/opt/book-review/configuration/bootstrap.sh, /etc/book-review/config.json]\n"
            size = len(gzip.compress(payload.encode(), compresslevel=6, mtime=0))
            self.assertLessEqual(size, 16384, (tier, size))


class DatabaseTests(OfflineCase):
    def test_preinstalled_ca_digest_owner_permissions_and_link_checks(self):
        # Inert bytes and a fake filesystem: no certificate/key generation or host CA reads.
        content = b"SYNTHETIC_CA_DIGEST_FIXTURE_NOT_A_CERTIFICATE"
        cfg = dict(config(), rds_ca_sha256=common.digest(content))
        path = mock.MagicMock()
        path.__str__.return_value = str(common.CA_FILE)
        path.parents = ()
        path.is_symlink.return_value = False
        path.is_file.return_value = True
        metadata = mock.Mock(st_uid=0, st_mode=0o100644, st_size=len(content))
        path.stat.return_value = metadata
        path.open.return_value.__enter__.return_value.read.return_value = content
        with mock.patch.object(common, "Path", return_value=path):
            self.assertEqual(common.verified_ca(cfg), str(common.CA_FILE))
            path.open.return_value.__enter__.return_value.read.assert_called_with(1024 * 1024 + 1)
            with self.assertRaisesRegex(common.RuntimeFailure, "rds_ca_digest_mismatch"):
                common.verified_ca(dict(cfg, rds_ca_sha256="0" * 64))
            for attribute, value in (("st_uid", 1000), ("st_mode", 0o100666), ("st_size", 1024 * 1024 + 1)):
                original = getattr(metadata, attribute)
                setattr(metadata, attribute, value)
                with self.assertRaisesRegex(common.RuntimeFailure, "unsafe_rds_ca_file"):
                    common.verified_ca(cfg)
                setattr(metadata, attribute, original)
            path.is_symlink.return_value = True
            path.stat.reset_mock()
            with self.assertRaisesRegex(common.RuntimeFailure, "unsafe_rds_ca_file"):
                common.verified_ca(cfg)
            path.stat.assert_not_called()

    def test_preinstalled_ca_parent_path_must_be_root_controlled(self):
        for linked, uid, mode in ((True, 0, 0o40755), (False, 1000, 0o40755), (False, 0, 0o40777)):
            path, parent = mock.MagicMock(), mock.MagicMock()
            path.is_symlink.return_value = False
            path.parents = (parent,)
            parent.is_symlink.return_value = linked
            parent.stat.return_value = mock.Mock(st_uid=uid, st_mode=mode)
            with mock.patch.object(common, "Path", return_value=path):
                with self.assertRaisesRegex(common.RuntimeFailure, "unsafe_rds_ca_file"):
                    common.verified_ca(config())
            path.open.assert_not_called()

    def test_bad_ca_blocks_direct_database_connection(self):
        driver = mock.Mock()
        with mock.patch.object(common, "verified_ca", side_effect=common.RuntimeFailure("rds_ca_digest_mismatch")):
            with self.assertRaises(common.RuntimeFailure):
                common.connect_db(config(), SYNTHETIC_APP, driver=driver)
        driver.connect.assert_not_called()

    def test_all_direct_db_paths_require_ca_and_hostname(self):
        for replica, database in [(False, True), (True, True), (False, False)]:
            driver, context = mock.Mock(), mock.Mock()
            with mock.patch.object(common, "verified_ca", return_value=str(common.CA_FILE)), mock.patch.object(common.ssl, "create_default_context", return_value=context) as factory:
                common.connect_db(config(), SYNTHETIC_APP, replica=replica, database=database, driver=driver)
            factory.assert_called_once_with(cafile=str(common.CA_FILE))
            self.assertTrue(context.check_hostname)
            self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
            kwargs = driver.connect.call_args.kwargs
            self.assertIs(kwargs["ssl"], context)
            self.assertTrue(kwargs["ssl_verify_cert"])
            self.assertTrue(kwargs["ssl_verify_identity"])
            self.assertEqual(kwargs["host"], config()["replica_host" if replica else "db_host"])
            self.assertLessEqual(kwargs["read_timeout"], 5)

    def test_initializer_parameterizes_values_and_grants_only_schema(self):
        connection, checked = FakeConnection(), FakeConnection()
        connector = mock.Mock(side_effect=[connection, checked])
        initialize.initialize(config("initializer"), SYNTHETIC_MASTER, SYNTHETIC_APP, connector)
        self.assertEqual(connector.call_args_list, [mock.call(config("initializer"), SYNTHETIC_MASTER, database=False),
                                                   mock.call(config("initializer"), SYNTHETIC_APP)])
        statements = [sql for sql, params in connection.events]
        self.assertTrue(any("CREATE DATABASE IF NOT EXISTS `book_review`" in sql for sql in statements))
        self.assertEqual(sum(sql.startswith("CREATE USER ") for sql in statements), 1)
        self.assertFalse(any(sql.startswith(("ALTER USER", "REVOKE")) for sql in statements))
        self.assertTrue(any("CURRENT_USER()" in sql for sql, _ in checked.events))
        self.assertEqual(checked.events[-1], ("CLOSE", None))
        grant = next(sql for sql in statements if sql.startswith("GRANT"))
        self.assertIn("CREATE, ALTER, DROP, INDEX, REFERENCES", grant)
        self.assertIn(r"ON `book\_review`.* TO %s@%s", grant)
        self.assertNotIn("*.*", grant)
        self.assertFalse(any(sql.startswith("INSERT") for sql in statements))
        self.assertNotIn(SYNTHETIC_APP["password"], "\n".join(statements))
        self.assertEqual(connection.events[-1], ("CLOSE", None))

    def test_initializer_refuses_master_reuse_and_invalid_schema(self):
        connector = mock.Mock()
        for cfg, master in [(config("initializer"), SYNTHETIC_APP), (dict(config("initializer"), db_name="bad`sql"), SYNTHETIC_MASTER)]:
            with self.assertRaises(common.RuntimeFailure):
                initialize.initialize(cfg, master, SYNTHETIC_APP, connector)
        connector.assert_not_called()

    def test_initializer_failure_releases_lock_and_closes(self):
        connection = FakeConnection()
        connection.fail_sql = "GRANT "
        with self.assertRaises(OSError):
            initialize.initialize(config("initializer"), SYNTHETIC_MASTER, SYNTHETIC_APP, lambda *a, **kw: connection)
        self.assertTrue(any("RELEASE_LOCK" in sql for sql, _ in connection.events))
        self.assertEqual(connection.events[-1], ("CLOSE", None))

    def test_replica_explicit_read_only_no_writes_or_rows(self):
        connection, connector = FakeConnection(), mock.Mock()
        connector.return_value = connection
        report_replica.report(config(), SYNTHETIC_APP, connector)
        connector.assert_called_once_with(config(), SYNTHETIC_APP, replica=True)
        statements = [sql for sql, _ in connection.events]
        self.assertIn("START TRANSACTION READ ONLY", statements)
        self.assertIn("ROLLBACK", statements)
        self.assertEqual(sum(sql.startswith("SELECT COUNT(*)") for sql in statements), 3)
        connection.read_only = 0
        with self.assertRaises(common.RuntimeFailure):
            report_replica.report(config(), SYNTHETIC_APP, connector)


class ExistingInitializerTests(OfflineCase):
    def existing_account(self):
        connection = FakeConnection()
        connection.account_rows = [("%", "ANY")]
        target = f"`{SYNTHETIC_APP['username']}`@`%`"
        connection.grants = [f"GRANT USAGE ON *.* TO {target}",
                             f"GRANT {initialize.PRIVILEGES}" + r" ON `book\_review`.* TO " + target]
        return connection

    def assert_no_account_or_schema_mutation(self, connection):
        self.assertFalse(any(sql.startswith(("CREATE", "ALTER", "GRANT", "REVOKE", "DROP", "INSERT"))
                             for sql, _ in connection.events))
        self.assertEqual(connection.events[-1], ("CLOSE", None))

    def test_matching_existing_account_is_authenticated_without_mutation(self):
        connection, checked = self.existing_account(), FakeConnection()
        connector = mock.Mock(side_effect=[connection, checked])
        initialize.initialize(config("initializer"), SYNTHETIC_MASTER, SYNTHETIC_APP, connector)
        self.assert_no_account_or_schema_mutation(connection)
        connector.assert_any_call(config("initializer"), SYNTHETIC_APP)
        self.assertEqual(checked.events, [("SELECT CURRENT_USER()", None), ("CLOSE", None)])

    def test_bad_existing_password_or_missing_schema_never_resets_account(self):
        for failure in (OSError("SYNTHETIC_BAD_PASSWORD"), OSError("SYNTHETIC_MISSING_SCHEMA")):
            connection = self.existing_account()
            connector = mock.Mock(side_effect=[connection, failure])
            with self.assertRaisesRegex(common.RuntimeFailure, "account_authentication_or_schema_failed"):
                initialize.initialize(config("initializer"), SYNTHETIC_MASTER, SYNTHETIC_APP, connector)
            self.assert_no_account_or_schema_mutation(connection)
            self.assertTrue(any("RELEASE_LOCK" in sql for sql, _ in connection.events))

    def test_missing_excess_or_wildcard_schema_grants_are_not_repaired(self):
        baseline = self.existing_account().grants
        bad_grants = [baseline[:1], baseline + ["GRANT `extra_role`@`%` TO `synthetic_app`@`%`"],
                      [baseline[0], baseline[1] + " WITH GRANT OPTION"],
                      [baseline[0], baseline[1].replace("SELECT, ", "")],
                      [baseline[0], baseline[1].replace(r"book\_review", "book_review")],
                      [baseline[0], baseline[1].replace(r"`book\_review`.*", "*.*")]]
        for grants in bad_grants:
            connection = self.existing_account()
            connection.grants = grants
            connector = mock.Mock(return_value=connection)
            with self.assertRaisesRegex(common.RuntimeFailure, "account_privileges_mismatch"):
                initialize.initialize(config("initializer"), SYNTHETIC_MASTER, SYNTHETIC_APP, connector)
            self.assert_no_account_or_schema_mutation(connection)
            self.assertEqual(connector.call_count, 1)

    def test_existing_host_and_tls_mismatches_are_not_changed(self):
        for rows in ([("localhost", "ANY")], [("%", "")], [("%", "ANY"), ("localhost", "ANY")]):
            connection = self.existing_account()
            connection.account_rows = rows
            with self.assertRaisesRegex(common.RuntimeFailure, "account_host_or_tls_mismatch"):
                initialize.initialize(config("initializer"), SYNTHETIC_MASTER, SYNTHETIC_APP, lambda *a, **k: connection)
            self.assert_no_account_or_schema_mutation(connection)

    def test_app_authentication_cannot_match_another_host_account(self):
        connection, checked = self.existing_account(), FakeConnection()
        checked.current_user = "synthetic_app@localhost"
        with self.assertRaisesRegex(common.RuntimeFailure, "account_authentication_or_schema_failed"):
            initialize.initialize(config("initializer"), SYNTHETIC_MASTER, SYNTHETIC_APP,
                                  mock.Mock(side_effect=[connection, checked]))
        self.assert_no_account_or_schema_mutation(connection)
        self.assertEqual(checked.events[-1], ("CLOSE", None))

    def test_new_schema_grant_supports_literal_partial_revokes_semantics(self):
        connection, checked = FakeConnection(), FakeConnection()
        connection.partial_revokes = 1
        initialize.initialize(config("initializer"), SYNTHETIC_MASTER, SYNTHETIC_APP,
                              mock.Mock(side_effect=[connection, checked]))
        grant = next(sql for sql, _ in connection.events if sql.startswith("GRANT "))
        self.assertIn("ON `book_review`.*", grant)
        self.assertNotIn(r"book\_review", grant)

    def test_concurrent_account_creation_never_falls_back_to_alter(self):
        connection = FakeConnection()
        connection.fail_sql = "CREATE USER "
        with self.assertRaises(OSError):
            initialize.initialize(config("initializer"), SYNTHETIC_MASTER, SYNTHETIC_APP, lambda *a, **k: connection)
        self.assertFalse(any(sql.startswith(("ALTER", "GRANT", "REVOKE")) for sql, _ in connection.events))
        self.assertEqual(connection.events[-1], ("CLOSE", None))


class SupervisorTests(OfflineCase):
    def test_schema_and_ownership_before_all_api_readiness_and_release(self):
        connection, child = FakeConnection(), mock.Mock()
        child.poll.return_value = None
        with mock.patch.object(supervisor, "owns_listener", return_value=True) as owns, mock.patch.object(supervisor, "api_ready") as ready:
            self.assertTrue(supervisor.barrier(child, (42, "100"), connection, config(), "lock"))
        ready.assert_called_once_with("http://127.0.0.1:3001", users=True)
        self.assertEqual(owns.call_count, 2)
        tables = {params[1] for sql, params in connection.events if "information_schema" in sql}
        self.assertEqual(tables, {"Users", "Books", "Reviews"})
        self.assertEqual(sum("IS_USED_LOCK" in sql for sql, _ in connection.events), 2)
        self.assertFalse(any("RELEASE_LOCK" in sql for sql, _ in connection.events))

    def test_unowned_stale_port_cannot_satisfy_barrier(self):
        child = mock.Mock()
        child.poll.return_value = None
        with mock.patch.object(supervisor, "owns_listener", return_value=False), mock.patch.object(supervisor, "api_ready") as probe:
            self.assertFalse(supervisor.barrier(child, (42, "100"), FakeConnection(), config(), "lock"))
        probe.assert_not_called()

    def test_missing_users_or_reviews_schema_blocks_books_success(self):
        child = mock.Mock()
        child.poll.return_value = None
        for table in ("Users", "Reviews"):
            connection = FakeConnection()
            connection.columns[table] = set()
            with mock.patch.object(supervisor, "owns_listener", return_value=True), mock.patch.object(supervisor, "api_ready") as probe:
                with self.assertRaisesRegex(common.RuntimeFailure, "schema_incomplete"):
                    supervisor.barrier(child, (42, "100"), connection, config(), "lock")
            probe.assert_not_called()

    def test_lock_loss_or_pid_change_fails_barrier(self):
        child = mock.Mock()
        child.poll.return_value = None
        connection = FakeConnection()
        connection.owner = None
        with self.assertRaisesRegex(common.RuntimeFailure, "startup_lock_lost"):
            supervisor.barrier(child, (42, "100"), connection, config(), "lock")
        with mock.patch.object(supervisor, "owns_listener", side_effect=[True, False]), mock.patch.object(supervisor, "api_ready"):
            with self.assertRaisesRegex(common.RuntimeFailure, "backend_identity_changed"):
                supervisor.barrier(child, (42, "100"), FakeConnection(), config(), "lock")

    def test_linux_pid_start_ticks_and_all_listener_inode_ownership(self):
        with scratch() as directory:
            (directory / "net").mkdir()
            (directory / "42/fd").mkdir(parents=True)
            stat_file = directory / "42/stat"
            stat_file.write_text("42 (node (worker)) " + " ".join(["S"] + ["0"] * 18 + ["100"]))
            (directory / "net/tcp").write_text("header\n 0: 00000000:0BB9 00000000:0000 0A 0:0 0:0 0 0 0 700 1\n")
            (directory / "42/fd/3").symlink_to("socket:[700]")
            self.assertEqual(supervisor.process_identity(42, directory), (42, "100"))
            self.assertTrue(supervisor.owns_listener((42, "100"), proc=directory))
            self.assertFalse(supervisor.owns_listener((42, "old"), proc=directory))
            (directory / "net/tcp6").write_text("header\n 0: 00000000:0BB9 00000000:0000 0A 0:0 0:0 0 0 0 701 1\n")
            self.assertFalse(supervisor.owns_listener((42, "100"), proc=directory))

    def test_acquire_is_bounded_and_parameterized(self):
        connection = FakeConnection()
        connection.acquire_results = [0, 1]
        supervisor.acquire(connection, "synthetic-lock", clock=lambda: 0)
        self.assertEqual(connection.events, [("SELECT GET_LOCK(%s, %s)", ("synthetic-lock", 3))] * 2)
        connection.acquire_results = [0]
        with self.assertRaisesRegex(common.RuntimeFailure, "startup_lock_timeout"):
            supervisor.acquire(connection, "lock", clock=mock.Mock(side_effect=[0, 1, 61]))

    def test_all_nodes_and_initializer_share_schema_lock(self):
        self.assertEqual(supervisor.lock_name(config()), supervisor.lock_name(config("initializer")))
        changed = dict(config(), db_host="failover.example.invalid")
        self.assertEqual(supervisor.lock_name(config()), supervisor.lock_name(changed))
        self.assertLessEqual(len(supervisor.lock_name(config())), 64)

    def test_port_conflict_never_starts_child_or_opens_database(self):
        connector, popen = mock.Mock(), mock.Mock()
        with mock.patch.object(supervisor, "listener_inodes", return_value={"unrelated"}):
            with self.assertRaisesRegex(common.RuntimeFailure, "backend_port_already_owned"):
                supervisor.start_once(config(), SYNTHETIC_APP, connector=connector, popen=popen)
        connector.assert_not_called()
        popen.assert_not_called()

    def test_success_releases_only_after_barrier_and_suppresses_child_output(self):
        connection, child = FakeConnection(), mock.Mock(pid=42)
        child.poll.side_effect = [None, 1]
        popen = mock.Mock(return_value=child)
        def barrier(*args):
            self.assertFalse(any("RELEASE_LOCK" in sql for sql, _ in connection.events))
            connection.events.append(("BARRIER", None))
            return True
        with mock.patch.object(supervisor, "listener_inodes", return_value=set()), mock.patch.object(supervisor, "process_identity", return_value=(42, "100")), mock.patch.object(supervisor, "barrier", side_effect=barrier), mock.patch.object(supervisor, "terminate"), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(common.RuntimeFailure, "backend_exited"):
                supervisor.start_once(config(), SYNTHETIC_APP, connector=lambda *a: connection, popen=popen, clock=lambda: 0)
        statements = [sql for sql, _ in connection.events]
        self.assertLess(statements.index("BARRIER"), statements.index("SELECT RELEASE_LOCK(%s)"))
        self.assertEqual(popen.call_args.args[0], ["node", "src/server.js"])
        self.assertEqual(popen.call_args.kwargs["stdout"], subprocess.DEVNULL)
        self.assertEqual(popen.call_args.kwargs["stderr"], subprocess.DEVNULL)
        self.assertTrue(popen.call_args.kwargs["start_new_session"])

    def test_failure_stops_child_before_lock_release_and_close(self):
        connection, child = FakeConnection(), mock.Mock(pid=42)
        child.poll.return_value = None
        with mock.patch.object(supervisor, "listener_inodes", return_value=set()), mock.patch.object(supervisor, "process_identity", return_value=(42, "100")), mock.patch.object(supervisor, "barrier", side_effect=common.RuntimeFailure("schema_incomplete")), mock.patch.object(supervisor, "terminate", side_effect=lambda p: connection.events.append(("TERMINATE", None))):
            with self.assertRaises(common.RuntimeFailure):
                supervisor.start_once(config(), SYNTHETIC_APP, connector=lambda *a: connection, popen=lambda *a, **k: child, clock=lambda: 0)
        statements = [sql for sql, _ in connection.events]
        self.assertLess(statements.index("TERMINATE"), statements.index("SELECT RELEASE_LOCK(%s)"))
        self.assertEqual(statements[-1], "CLOSE")

    def test_lost_db_session_after_spawn_stops_child_without_reconnecting(self):
        connection, child = FakeConnection(), mock.Mock(pid=42)
        connector = mock.Mock(return_value=connection)
        def spawn(*args, **kwargs):
            connection.fail_sql = "IS_USED_LOCK"
            return child
        with mock.patch.object(supervisor, "listener_inodes", return_value=set()), mock.patch.object(supervisor, "process_identity", return_value=(42, "100")), mock.patch.object(supervisor, "terminate") as stop:
            with self.assertRaises(OSError):
                supervisor.start_once(config(), SYNTHETIC_APP, connector=connector, popen=spawn, clock=lambda: 0)
        stop.assert_called_once_with(child)
        connector.assert_called_once()
        self.assertEqual(connection.events[-1], ("CLOSE", None))

    def test_release_failure_terminates_before_closing(self):
        connection, child = FakeConnection(), mock.Mock(pid=42)
        child.poll.return_value = None
        connection.release_result = 0
        with mock.patch.object(supervisor, "listener_inodes", return_value=set()), mock.patch.object(supervisor, "process_identity", return_value=(42, "100")), mock.patch.object(supervisor, "barrier", return_value=True), mock.patch.object(supervisor, "terminate") as stop:
            with self.assertRaisesRegex(common.RuntimeFailure, "startup_lock_release_failed"):
                supervisor.start_once(config(), SYNTHETIC_APP, connector=lambda *a: connection, popen=lambda *a, **k: child, clock=lambda: 0)
        stop.assert_called_once_with(child)
        self.assertEqual(connection.events[-1], ("CLOSE", None))

    def test_continued_readiness_failures_terminate_running_child(self):
        connection, child = FakeConnection(), mock.Mock(pid=42)
        child.poll.return_value = None
        sleep = mock.Mock()
        with mock.patch.object(supervisor, "listener_inodes", return_value=set()), mock.patch.object(supervisor, "process_identity", return_value=(42, "100")), mock.patch.object(supervisor, "barrier", return_value=True), mock.patch.object(supervisor, "owns_listener", return_value=True), mock.patch.object(supervisor, "api_ready", side_effect=OSError("synthetic database unavailable")) as probe, mock.patch.object(supervisor, "terminate") as stop, contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(common.RuntimeFailure, "backend_readiness_lost"):
                supervisor.start_once(config(), SYNTHETIC_APP, connector=lambda *a: connection, popen=lambda *a, **k: child, clock=lambda: 0, sleep=sleep)
        self.assertEqual(probe.call_count, 3)
        self.assertEqual(sleep.call_args_list, [mock.call(5)] * 3)
        stop.assert_called_once_with(child)

    def test_main_sanitizes_untrusted_failures(self):
        output = io.StringIO()
        with mock.patch.object(supervisor.signal, "signal"), mock.patch.object(supervisor, "load_config", side_effect=RuntimeError(SYNTHETIC_APP["password"])), contextlib.redirect_stderr(output):
            self.assertEqual(supervisor.main(), 1)
        self.assertEqual(output.getvalue(), "backend_service_failed\n")

    def test_startup_timeout_terminates_and_closes(self):
        connection, child = FakeConnection(), mock.Mock(pid=42)
        with mock.patch.object(supervisor, "listener_inodes", return_value=set()), mock.patch.object(supervisor, "process_identity", return_value=(42, "100")), mock.patch.object(supervisor, "terminate") as stop:
            with self.assertRaisesRegex(common.RuntimeFailure, "backend_startup_timeout"):
                supervisor.start_once(config(), SYNTHETIC_APP, connector=lambda *a: connection, popen=lambda *a, **k: child,
                                      clock=mock.Mock(side_effect=[0, 1, 2, 200]))
        stop.assert_called_once_with(child)
        self.assertEqual(connection.events[-1], ("CLOSE", None))

    def test_terminate_targets_only_child_process_group_with_bounded_escalation(self):
        child = mock.Mock(pid=42)
        child.poll.return_value = None
        child.wait.side_effect = [subprocess.TimeoutExpired("synthetic-child", 10), 0]
        with mock.patch.object(supervisor.os, "killpg") as kill:
            supervisor.terminate(child)
        self.assertEqual([call.args[0] for call in kill.call_args_list], [42, 42])
        self.assertEqual(child.wait.call_args_list, [mock.call(timeout=10), mock.call(timeout=5)])


class HttpAndServiceTests(OfflineCase):
    def test_api_health_uses_books_reviews_and_read_only_invalid_login(self):
        responses = [[{"id": 7}], [], {"message": "Invalid email or password"}]
        with mock.patch.object(probes, "request", side_effect=responses) as request:
            probes.api_ready("http://127.0.0.1:3001", users=True)
        self.assertEqual([call.args[0] for call in request.call_args_list], [
            "http://127.0.0.1:3001/api/books", "http://127.0.0.1:3001/api/reviews/7",
            "http://127.0.0.1:3001/api/users/login"])
        self.assertEqual(request.call_args_list[2].kwargs["expected"], 400)
        self.assertEqual(request.call_args_list[2].kwargs["body"]["password"], "")

    def test_web_health_checks_both_tiers_and_propagates_failure(self):
        with mock.patch.object(probes, "request") as request, mock.patch.object(probes, "api_ready") as api:
            probes.web_ready(config("web"))
        request.assert_called_once_with("http://127.0.0.1:3000/", json_response=False)
        api.assert_called_once_with(config()["internal_url"])
        with mock.patch.object(probes, "request"), mock.patch.object(probes, "api_ready", side_effect=OSError("synthetic")):
            with self.assertRaises(OSError):
                probes.web_ready(config("web"))

    def test_readiness_returns_503_not_false_health_and_hides_errors(self):
        cls = readiness.handler(config("web"))
        handler = object.__new__(cls)
        handler.path, handler.wfile = "/healthz", io.BytesIO()
        handler.send_response, handler.send_header, handler.end_headers = mock.Mock(), mock.Mock(), mock.Mock()
        with mock.patch.object(readiness, "web_ready", side_effect=RuntimeError("SYNTHETIC_PRIVATE_ERROR")):
            handler.do_GET()
        handler.send_response.assert_called_once_with(503)
        self.assertEqual(handler.wfile.getvalue(), b"unavailable\n")

    def test_nginx_method_route_matrix_is_derived_from_template(self):
        text = (ROOT / "runtime/nginx.conf.template").read_text()
        routes = re.findall(r"location ~ (\S+) \{\n(.*?)(?=\n        \})", text, flags=re.S)
        def route(path, method):
            for pattern, block in routes:
                if re.search(pattern, path):
                    if "!= POST" in block and method != "POST":
                        return 405
                    if "^(GET|HEAD)$" in block and method not in ("GET", "HEAD"):
                        return 405
                    return 200
            return 404
        for prefix in ("", "/api"):
            for path in ("/books", "/books/1", "/books/1/"):
                self.assertEqual(route(prefix + path, "GET"), 200)
                self.assertEqual(route(prefix + path, "POST"), 405)
                self.assertEqual(route(prefix + path, "DELETE"), 405)
            for path in ("/users/login", "/users/register", "/reviews"):
                self.assertEqual(route(prefix + path, "POST"), 200)
                self.assertEqual(route(prefix + path, "GET"), 405)
            self.assertEqual(route(prefix + "/reviews/2", "GET"), 200)
            self.assertEqual(route(prefix + "/reviews/2", "POST"), 405)
        mapping = re.search(r"~\^/\(\?:api/\)\?\(\?<api_suffix>.*?\$ /api/\$api_suffix;", text).group(0)
        pattern = mapping.split(" /api/")[0][1:].replace("(?<api_suffix>", "(?P<api_suffix>")
        for path in ("/books", "/api/books", "/reviews/1", "/api/reviews/1"):
            canonical = "/api/" + re.match(pattern, path).group("api_suffix")
            self.assertEqual(canonical.count("/api/"), 1)
        self.assertEqual(text.count("proxy_set_header Authorization $http_authorization;"), 1)
        self.assertIn("error_page 500 502 503 504 =503", text)
        self.assertIn("proxy_set_header Cookie \"\";", text)
        self.assertIn("if ($approved_origin = 0) { return 421; }", text)

    def test_nginx_blocks_image_optimization_and_all_non_api_writes(self):
        text = (ROOT / "runtime/nginx.conf.template").read_text()
        self.assertIn("location ^~ /_next/image { return 404; }", text)
        blocks = re.findall(r"location ([^{]+)\{\n(.*?)(?=\n        \})", text, flags=re.S)
        writable = []
        for selector, block in blocks:
            if "proxy_pass" not in block:
                continue
            if "if ($request_method != POST) { return 405; }" in block:
                writable.append(selector.strip())
            else:
                self.assertIn("if ($request_method !~ ^(GET|HEAD)$) { return 405; }", block, selector)
        self.assertEqual(writable, [r"~ ^/(?:api/)?users/(?:register|login)/?$", r"~ ^/(?:api/)?reviews/?$"])
        self.assertIn("server actions are not used", (ROOT / "runtime/OPERATIONS.md").read_text())

    def test_rendered_nginx_has_only_approved_destinations_and_no_unused_tokens(self):
        with mock.patch.object(bootstrap, "CONFIGURATION", ROOT / "runtime"):
            text = bootstrap.render_nginx(config("web"))
        self.assertNotIn("@@", text)
        self.assertIn('set $internal_origin "http://internal.example.invalid";', text)
        self.assertIn('"books.example.invalid|https" 1;', text)
        self.assertIn("resolver 127.0.0.53 valid=30s ipv6=off", text)

    def test_router_verifies_identity_both_tls_legs_and_loopback(self):
        with mock.patch.object(router, "CONFIGURATION", ROOT / "runtime"):
            text = router.render(config())
        for fragment in ["bind_address = 127.0.0.1", "bind_port = 6446", "destinations = primary.example.invalid:3306",
                         "client_ssl_mode = REQUIRED", "server_ssl_mode = REQUIRED", "server_ssl_verify = VERIFY_IDENTITY",
                         "server_ssl_ca = /etc/book-review/rds-ca.pem"]:
            self.assertIn(fragment, text)
        self.assertNotIn("PASSTHROUGH", text)
        self.assertNotIn("@@", text)

    def test_systemd_nonroot_secrets_runtime_and_bounded_restarts(self):
        for name in services.SERVICES:
            text = services.unit(name)
            self.assertIn("User=book-", text)
            self.assertIn("RuntimeDirectoryMode=0700", text)
            self.assertIn("LoadCredential=config:/etc/book-review/config.json", text)
            self.assertIn("ExecStartPre=/usr/bin/python3 -B /opt/book-review/configuration/common.py", text)
            self.assertIn("NoNewPrivileges=yes", text)
            self.assertIn("ProtectSystem=strict", text)
            self.assertIn("LimitCORE=0", text)
            self.assertNotIn("SYNTHETIC", text)
            self.assertNotIn("EnvironmentFile", text)
        self.assertIn("StartLimitBurst=3", services.unit("book-app"))
        self.assertIn("StartLimitIntervalSec=900", services.unit("book-app"))
        self.assertIn("Restart=no", services.unit("book-initialize"))
        self.assertIn("Type=oneshot", services.unit("book-initialize"))
        self.assertIn("StandardError=null", services.unit("book-router"))
        self.assertIn("StandardError=null", services.unit("book-web"))
        self.assertIn("CAP_NET_BIND_SERVICE", services.unit("book-nginx"))

    def test_runtime_version_checks_use_explicit_fake_commands(self):
        outputs = {"node": b"v22.18.0", "npm": b"10.9.3", "nginx": b"nginx/1.24.0",
                   "mysqlrouter": b"MySQL Router Ver 8.4.6", "aws": b"aws-cli/2.27.0"}
        with mock.patch.object(bootstrap, "run", side_effect=lambda command: mock.Mock(stdout=outputs[command[0]], stderr=b"")), mock.patch.object(bootstrap.platform, "python_version", return_value="3.12.3"), mock.patch.object(bootstrap.importlib.metadata, "version", return_value="1.1.1"):
            versions = bootstrap.runtime_versions()
            self.assertEqual(versions["node"], "22.18.0")
            outputs["node"] = b"v23.11.0"
            with self.assertRaises(common.RuntimeFailure):
                bootstrap.runtime_versions()

    def test_ram_backed_runtime_is_mandatory(self):
        with mock.patch.object(bootstrap.os, "geteuid", return_value=0), mock.patch.object(bootstrap.platform, "system", return_value="Linux"), mock.patch.object(bootstrap.platform, "machine", return_value="x86_64"), mock.patch.object(Path, "read_text", return_value='ID=ubuntu\nVERSION_ID="24.04"'), mock.patch.object(bootstrap, "run", return_value=mock.Mock(stdout=b"ext4\n")):
            with self.assertRaisesRegex(common.RuntimeFailure, "runtime_directory_not_ram_backed"):
                bootstrap.prerequisites()

    def test_deploy_manifest_import_closure_and_complete_file_classification(self):
        import ast
        directory = ROOT / "runtime"
        manifest = json.loads((directory / "deploy-manifest.json").read_text())
        local_modules = {path.stem for path in directory.glob("*.py")}
        classified = set(manifest["repository_only"]) | set(manifest["common"])
        for tier, extra in manifest["tiers"].items():
            selected = set(manifest["common"] + extra)
            classified.update(selected)
            for name in selected:
                self.assertTrue((directory / name).is_file(), name)
                if not name.endswith(".py"):
                    continue
                tree = ast.parse((directory / name).read_text())
                imported = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
                for module in imported & local_modules:
                    self.assertIn(module + ".py", selected, (tier, name, module))
        actual = {path.name for path in directory.iterdir() if path.is_file()}
        self.assertEqual(classified, actual)
        self.assertIn("mysqlrouter.conf.template", manifest["tiers"]["app"])
        self.assertIn("nginx.conf.template", manifest["tiers"]["web"])

    def test_bootstrap_wrong_platform_has_no_side_effects(self):
        with mock.patch.object(bootstrap.os, "geteuid", return_value=0), mock.patch.object(bootstrap.platform, "system", return_value="Darwin"), mock.patch.object(bootstrap, "run") as run:
            with self.assertRaises(common.RuntimeFailure):
                bootstrap.prerequisites()
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
