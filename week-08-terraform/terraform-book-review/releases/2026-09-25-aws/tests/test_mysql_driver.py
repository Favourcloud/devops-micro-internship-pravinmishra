"""Pinned PyMySQL executes against memory-only protocol transports, never a DB/socket."""
import importlib.metadata
import inspect
import io
from pathlib import Path
import ssl
import struct
import sys
import unittest
from unittest import mock

import pymysql
from pymysql.constants import CLIENT

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))
import common
import initialize
import report_replica
import supervisor

CONFIG = {"release_authorized": True, "db_host": "primary.example.invalid",
          "replica_host": "replica.example.invalid", "db_name": "synthetic_books",
          "rds_ca_path": str(common.CA_FILE)}
APP = {"username": "synthetic_app", "password": "SYNTHETIC_INERT_APP_NOT_A_SECRET"}
MASTER = {"username": "synthetic_master", "password": "SYNTHETIC_INERT_MASTER_NOT_A_SECRET"}


def packet(payload, sequence):
    return len(payload).to_bytes(3, "little") + bytes([sequence]) + payload


def greeting(tls):
    capabilities = CLIENT.PROTOCOL_41 | CLIENT.SECURE_CONNECTION | CLIENT.PLUGIN_AUTH | CLIENT.CONNECT_WITH_DB
    if tls:
        capabilities |= CLIENT.SSL
    payload = (b"\x0a8.4.0-synthetic\x00" + struct.pack("<I", 17) + b"12345678\x00"
               + struct.pack("<HBHHB", capabilities & 0xffff, 45, 2, capabilities >> 16, 21)
               + b"\x00" * 10 + b"abcdefghijkl\x00mysql_native_password\x00")
    return packet(payload, 0)


class MemoryTransport:
    def __init__(self, incoming):
        self.incoming = io.BytesIO(incoming)
        self.writes = []
        self.closed = False

    def makefile(self, mode):
        return self.incoming

    def settimeout(self, value):
        pass

    def sendall(self, value):
        self.writes.append(value)

    def close(self):
        self.closed = True


class ActualDriverTests(unittest.TestCase):
    def setUp(self):
        self.assertEqual(importlib.metadata.version("PyMySQL"), "1.1.1",
                         "Install the exact tests/requirements.txt wheel; never skip these tests")
        self.addCleanup(mock.patch.stopall)
        mock.patch("socket.socket", side_effect=AssertionError("network forbidden")).start()
        mock.patch("socket.create_connection", side_effect=AssertionError("network forbidden")).start()
        mock.patch("subprocess.Popen", side_effect=AssertionError("processes forbidden")).start()

    def connection(self, secret=APP, *, replica=False, database=True):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        replacement = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        with mock.patch.object(common, "verified_ca", return_value=str(common.CA_FILE)), \
                mock.patch.object(common.ssl, "create_default_context", side_effect=[context, replacement]) as factory, \
                mock.patch.object(pymysql.connections.Connection, "connect") as connect:
            connection = common.connect_db(CONFIG, secret, replica=replica, database=database)
        factory.assert_called_once_with(cafile=str(common.CA_FILE))
        connect.assert_called_once_with()
        self.assertIsInstance(connection, pymysql.connections.Connection)
        self.assertIs(connection.ctx, context)
        self.assertTrue(connection.ctx.check_hostname)
        self.assertEqual(connection.ctx.verify_mode, ssl.CERT_REQUIRED)
        self.assertEqual(connection.ctx.get_ca_certs(), [])
        self.addCleanup(connection._force_close)
        return connection, context

    def tls_transport(self, connection, context, incoming=b""):
        transport = mock.Mock(spec=ssl.SSLSocket)
        transport.context = context
        transport.server_hostname = connection.host
        transport.cipher.return_value = ("TLS_AES_256_GCM_SHA384", "TLSv1.3", 256)
        transport.makefile.return_value = io.BytesIO(incoming)
        return transport

    def test_actual_constructor_keeps_exact_context_for_every_direct_identity_and_host(self):
        for secret, replica, database in ((MASTER, False, False), (APP, False, True), (APP, True, True)):
            with self.subTest(identity=secret["username"], replica=replica, database=database):
                connection, _ = self.connection(secret, replica=replica, database=database)
                self.assertEqual(connection.host, CONFIG["replica_host" if replica else "db_host"])
                self.assertEqual(connection.db, CONFIG["db_name"] if database else None)
                self.assertEqual(connection.user, secret["username"])
                self.assertTrue(connection.client_flag & CLIENT.SSL)

    def test_actual_deferred_constructor_retains_verified_context_without_connecting(self):
        first, context = self.connection()
        deferred = type(first)(user=APP["username"], password=APP["password"],
                               host=CONFIG["db_host"], ssl=context, defer_connect=True)
        self.addCleanup(deferred._force_close)
        self.assertIsNone(deferred._sock)
        self.assertIs(deferred.ctx, context)
        self.assertTrue(deferred.ctx.check_hostname)
        self.assertEqual(deferred.ctx.verify_mode, ssl.CERT_REQUIRED)

    def test_no_ssl_greeting_writes_zero_authentication_bytes_even_after_previous_secure_session(self):
        for secret, replica, database in ((MASTER, False, False), (APP, False, True), (APP, True, True)):
            for previously_secure in (False, True):
                with self.subTest(identity=secret["username"], replica=replica, stale=previously_secure):
                    connection, _ = self.connection(secret, replica=replica, database=database)
                    connection._secure = previously_secure
                    transport = MemoryTransport(greeting(False))
                    with self.assertRaisesRegex(common.RuntimeFailure, "database_verified_tls_required"):
                        connection.connect(sock=transport)
                    self.assertFalse(connection.server_capabilities & CLIENT.SSL)
                    self.assertEqual(transport.writes, [])
                    self.assertTrue(transport.closed)

    def test_unadapted_pinned_driver_control_writes_authentication_without_ssl(self):
        connection = pymysql.connections.Connection(user=APP["username"], password=APP["password"],
                      host=CONFIG["db_host"], ssl=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT), defer_connect=True)
        self.addCleanup(connection._force_close)
        transport = MemoryTransport(greeting(False))
        with self.assertRaises(pymysql.err.OperationalError):
            connection.connect(sock=transport)
        self.assertEqual(len(transport.writes), 1)
        self.assertIn(APP["username"].encode(), transport.writes[0])

    def test_missing_or_weakened_context_rejected_before_authentication(self):
        for mode in ("ssl_disabled", "no_hostname", "no_verification", "not_context"):
            with self.subTest(mode=mode):
                connection, context = self.connection()
                if mode == "ssl_disabled":
                    connection.ssl = False
                elif mode == "not_context":
                    connection.ctx = {}
                else:
                    context.check_hostname = False
                    if mode == "no_verification":
                        context.verify_mode = ssl.CERT_NONE
                transport = MemoryTransport(greeting(True))
                with self.assertRaisesRegex(common.RuntimeFailure, "database_verified_tls_required"):
                    connection.connect(sock=transport)
                self.assertEqual(transport.writes, [])

    def test_certificate_failure_allows_only_non_authenticating_ssl_request(self):
        connection, context = self.connection(MASTER, database=False)
        transport = MemoryTransport(greeting(True))
        with mock.patch.object(context, "wrap_socket", side_effect=ssl.SSLCertVerificationError("synthetic rejection")) as wrap:
            with self.assertRaises(pymysql.err.OperationalError):
                connection.connect(sock=transport)
        wrap.assert_called_once_with(transport, server_hostname=CONFIG["db_host"])
        self.assertEqual(len(transport.writes), 1)
        self.assertEqual(len(transport.writes[0][4:]), 32)
        self.assertNotIn(MASTER["username"].encode(), transport.writes[0])
        self.assertNotIn(MASTER["password"].encode(), transport.writes[0])

    def test_actual_authentication_and_initial_sql_follow_tls_wrap_on_memory_transport(self):
        connection, context = self.connection()
        raw = MemoryTransport(greeting(True))
        ok = b"\x00\x00\x00\x02\x00\x00\x00"
        tls = self.tls_transport(connection, context, packet(ok, 3) + packet(ok, 1))
        with mock.patch.object(context, "wrap_socket", return_value=tls) as wrap:
            connection.connect(sock=raw)
        wrap.assert_called_once_with(raw, server_hostname=CONFIG["db_host"])
        self.assertEqual(len(raw.writes), 1)
        self.assertEqual(len(raw.writes[0][4:]), 32)
        self.assertNotIn(APP["username"].encode(), raw.writes[0])
        writes = [call.args[0] for call in tls.sendall.call_args_list]
        self.assertEqual(len(writes), 2)
        self.assertIn(APP["username"].encode(), writes[0])
        self.assertIn(b"SET NAMES utf8mb4", writes[1])
        self.assertIs(connection._sock, tls)

    def test_no_negotiated_tls_blocks_initial_sql_even_if_authentication_returns(self):
        connection, _ = self.connection()
        raw = MemoryTransport(greeting(True))
        with mock.patch.object(pymysql.connections.Connection, "_request_authentication"):
            with self.assertRaisesRegex(common.RuntimeFailure, "database_tls_not_negotiated"):
                connection.connect(sock=raw)
        self.assertEqual(raw.writes, [])

    def test_every_sql_command_rechecks_negotiated_tls_not_only_cached_secure_flag(self):
        for failure in ("raw_socket", "no_cipher", "other_context", "wrong_hostname", "not_secure"):
            with self.subTest(failure=failure):
                connection, context = self.connection()
                tls = self.tls_transport(connection, context)
                connection._sock, connection._secure = tls, True
                if failure == "raw_socket":
                    connection._sock = MemoryTransport(b"")
                elif failure == "no_cipher":
                    tls.cipher.return_value = None
                elif failure == "other_context":
                    tls.context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                elif failure == "wrong_hostname":
                    tls.server_hostname = CONFIG["replica_host"]
                else:
                    connection._secure = False
                with self.assertRaisesRegex(common.RuntimeFailure, "database_tls_not_negotiated"):
                    connection.cursor().execute("SELECT 1")
                tls.sendall.assert_not_called()

    def test_master_initializer_app_lock_schema_and_replica_share_hardened_connector(self):
        for function in (initialize.initialize, supervisor.start_once, report_replica.report):
            self.assertIs(inspect.signature(function).parameters["connector"].default, common.connect_db)
        self.assertIn("checked = connector(config, app)", inspect.getsource(initialize.verify_account))


if __name__ == "__main__":
    unittest.main()
