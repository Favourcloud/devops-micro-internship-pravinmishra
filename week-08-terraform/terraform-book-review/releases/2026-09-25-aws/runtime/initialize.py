#!/usr/bin/env python3
"""Explicit optional one-shot schema/account setup, never application evidence rows."""
import sys

from common import IDENTIFIER, RuntimeFailure, connect_db, fetch_secret, load_config, require_release
from supervisor import acquire, assert_lock, lock_name, scalar

PRIVILEGES = "SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, INDEX, REFERENCES"


def account_rows(connection, username):
    with connection.cursor() as cursor:
        cursor.execute("SELECT Host, ssl_type FROM mysql.user WHERE User=%s LIMIT 2", (username,))
        return cursor.fetchall()


def verify_account(connection, config, app, grant_schema, connector):
    if list(account_rows(connection, app["username"])) != [("%", "ANY")]:
        raise RuntimeFailure("account_host_or_tls_mismatch")
    with connection.cursor() as cursor:
        cursor.execute("SHOW GRANTS FOR %s@%s", (app["username"], "%"))
        grants = [row[0] for row in cursor.fetchall()]
    target = f"`{app['username']}`@`%`"
    usage = f"GRANT USAGE ON *.* TO {target}"
    suffix = f" ON `{grant_schema}`.* TO {target}"
    schema_grants = [line for line in grants if line.startswith("GRANT ") and line.endswith(suffix)]
    if (len(grants) != 2 or grants.count(usage) != 1 or len(schema_grants) != 1
            or set(schema_grants[0][6:-len(suffix)].split(", ")) != set(PRIVILEGES.split(", "))):
        raise RuntimeFailure("account_privileges_mismatch")
    checked = None
    try:
        checked = connector(config, app)
        if scalar(checked, "SELECT CURRENT_USER()", None) != app["username"] + "@%":
            raise RuntimeFailure("account_identity_mismatch")
    except Exception:
        raise RuntimeFailure("account_authentication_or_schema_failed") from None
    finally:
        if checked is not None:
            checked.close()


def initialize(config, master, app, connector=connect_db):
    require_release(config)
    if config["tier"] != "initializer" or master["username"] == app["username"]:
        raise RuntimeFailure("initializer_identity_invalid")
    name = config["db_name"]
    if not IDENTIFIER.fullmatch(name):
        raise RuntimeFailure("database_identifier_invalid")
    connection = connector(config, master, database=False)
    held = False
    try:
        acquire(connection, lock_name(config))
        held = True
        partial_revokes = scalar(connection, "SELECT @@GLOBAL.partial_revokes", None)
        if partial_revokes not in (0, 1):
            raise RuntimeFailure("unsupported_grant_semantics")
        grant_schema = name if partial_revokes else name.replace("_", "\\_")
        existing = account_rows(connection, app["username"])
        assert_lock(connection, lock_name(config))
        if not existing:
            with connection.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                cursor.execute("CREATE USER %s@%s IDENTIFIED BY %s REQUIRE SSL",
                               (app["username"], "%", app["password"]))
                cursor.execute(f"GRANT {PRIVILEGES} ON `{grant_schema}`.* TO %s@%s", (app["username"], "%"))
        verify_account(connection, config, app, grant_schema, connector)
        assert_lock(connection, lock_name(config))
        if scalar(connection, "SELECT RELEASE_LOCK(%s)", (lock_name(config),)) != 1:
            raise RuntimeFailure("initializer_lock_release_failed")
        held = False
    finally:
        try:
            if held:
                scalar(connection, "SELECT RELEASE_LOCK(%s)", (lock_name(config),))
        finally:
            connection.close()


def main():
    try:
        config = load_config()
        initialize(config, fetch_secret(config, "master"), fetch_secret(config, "app"))
        print("schema_account_setup_complete_no_evidence_created")
        return 0
    except Exception:
        print("schema_account_setup_failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
