#!/usr/bin/env python3
"""Hold one MySQL named lock until this fresh backend has completed upstream startup."""
import hashlib
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from common import ROOT, RuntimeFailure, child_environment, connect_db, fetch_secret, load_config, require_release
from probes import api_ready

SCHEMA_COLUMNS = {
    "Users": {"id", "name", "email", "password", "createdAt", "updatedAt"},
    "Books": {"id", "title", "author", "rating", "createdAt", "updatedAt"},
    "Reviews": {"id", "userId", "bookId", "comment", "rating", "username", "createdAt", "updatedAt"},
}


def process_identity(pid, proc=Path("/proc")):
    return (pid, (proc / str(pid) / "stat").read_text().rsplit(")", 1)[1].split()[19])


def listener_inodes(port, proc=Path("/proc")):
    found = set()
    for protocol in ("tcp", "tcp6"):
        path = proc / "net" / protocol
        if not path.exists():
            continue
        for line in path.read_text().splitlines()[1:]:
            fields = line.split()
            if fields[3] == "0A" and int(fields[1].rsplit(":", 1)[1], 16) == port:
                found.add(fields[9])
    return found


def owns_listener(identity, port=3001, proc=Path("/proc")):
    pid, _ = identity
    if process_identity(pid, proc) != identity:
        return False
    listeners = listener_inodes(port, proc)
    owned = set()
    for fd in (proc / str(pid) / "fd").iterdir():
        try:
            target = os.readlink(fd)
        except FileNotFoundError:
            continue
        if target.startswith("socket:[") and target.endswith("]"):
            owned.add(target[8:-1])
    return bool(listeners) and listeners.issubset(owned) and process_identity(pid, proc) == identity


def lock_name(config):
    return "book-review-start:" + hashlib.sha256(config["db_name"].encode()).hexdigest()[:40]


def scalar(connection, sql, params):
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchone()[0]


def acquire(connection, name, *, clock=time.monotonic):
    deadline = clock() + 60
    while clock() < deadline:
        result = scalar(connection, "SELECT GET_LOCK(%s, %s)", (name, 3))
        if result == 1:
            return
        if result is None:
            break
    raise RuntimeFailure("startup_lock_timeout")


def assert_lock(connection, name):
    with connection.cursor() as cursor:
        cursor.execute("SELECT IS_USED_LOCK(%s), CONNECTION_ID()", (name,))
        owner, connection_id = cursor.fetchone()
    if owner is None or owner != connection_id:
        raise RuntimeFailure("startup_lock_lost")


def assert_schema(connection, database):
    with connection.cursor() as cursor:
        for table, expected in SCHEMA_COLUMNS.items():
            cursor.execute("SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s",
                           (database, table))
            if not expected.issubset({row[0] for row in cursor.fetchall()}):
                raise RuntimeFailure("schema_incomplete")


def barrier(child, identity, connection, config, name):
    assert_lock(connection, name)
    if child.poll() is not None:
        raise RuntimeFailure("backend_exited")
    if not owns_listener(identity):
        return False
    assert_schema(connection, config["db_name"])
    api_ready("http://127.0.0.1:3001", users=True)
    assert_lock(connection, name)
    if child.poll() is not None or not owns_listener(identity):
        raise RuntimeFailure("backend_identity_changed")
    return True


def terminate(child):
    if child is not None and child.poll() is None:
        try:
            os.killpg(child.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                return
            child.wait(timeout=5)


def start_once(config, secret, *, connector=connect_db, popen=subprocess.Popen,
               clock=time.monotonic, sleep=time.sleep):
    require_release(config)
    connection, child, held = None, None, False
    name = lock_name(config)
    try:
        if listener_inodes(3001):
            raise RuntimeFailure("backend_port_already_owned")
        connection = connector(config, secret)
        acquire(connection, name, clock=clock)
        held = True
        assert_lock(connection, name)
        if listener_inodes(3001):
            raise RuntimeFailure("backend_port_race")
        child = popen(["node", "src/server.js"], cwd=ROOT / "application/backend",
                      env=child_environment(config, secret), stdin=subprocess.DEVNULL,
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        identity = process_identity(child.pid)
        deadline = clock() + 180
        while clock() < deadline:
            assert_lock(connection, name)
            if child.poll() is not None:
                raise RuntimeFailure("backend_exited")
            try:
                ready = barrier(child, identity, connection, config, name)
            except (OSError, ValueError):
                ready = False
            if ready:
                if scalar(connection, "SELECT RELEASE_LOCK(%s)", (name,)) != 1:
                    raise RuntimeFailure("startup_lock_release_failed")
                held = False
                connection.close()
                connection = None
                print("backend_startup_verified", flush=True)
                # Continuous read-only DB readiness failure kills Node and lets bounded systemd retry run.
                failures = 0
                while child.poll() is None:
                    sleep(5)
                    try:
                        if not owns_listener(identity):
                            raise RuntimeFailure("backend_identity_changed")
                        api_ready("http://127.0.0.1:3001", users=True)
                        failures = 0
                    except Exception:
                        failures += 1
                        if failures >= 3:
                            raise RuntimeFailure("backend_readiness_lost")
                raise RuntimeFailure("backend_exited")
            sleep(0.5)
        raise RuntimeFailure("backend_startup_timeout")
    finally:
        # Stop the process before relinquishing the startup lock, including timeout/SQL failure.
        terminate(child)
        if connection is not None:
            try:
                if held:
                    scalar(connection, "SELECT RELEASE_LOCK(%s)", (name,))
            finally:
                connection.close()


def main():
    def stop(signum, frame):
        raise RuntimeFailure("service_stopped")
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        config = load_config()
        if config["tier"] != "app":
            raise RuntimeFailure("wrong_tier")
        start_once(config, fetch_secret(config, "app"))
    except BaseException:
        print("backend_service_failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
