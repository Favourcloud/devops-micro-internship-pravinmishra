#!/usr/bin/env python3
"""Future human-approved, verified-TLS read-only replica check; no row values printed."""
import sys
from common import RuntimeFailure, connect_db, fetch_secret, load_config


def report(config, secret, connector=connect_db):
    if config["tier"] != "app":
        raise RuntimeFailure("replica_probe_wrong_tier")
    connection = connector(config, secret, replica=True)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT @@global.read_only")
            if cursor.fetchone()[0] != 1:
                raise RuntimeFailure("replica_not_read_only")
            cursor.execute("SET SESSION TRANSACTION READ ONLY")
            cursor.execute("START TRANSACTION READ ONLY")
            for table in ("Users", "Books", "Reviews"):
                cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                cursor.fetchone()
            cursor.execute("ROLLBACK")
    finally:
        connection.close()


def main():
    try:
        config = load_config()
        report(config, fetch_secret(config, "app"))
        print("replica_read_only_probe_passed_not_replication_lag_evidence")
        return 0
    except Exception:
        print("replica_read_only_probe_failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
