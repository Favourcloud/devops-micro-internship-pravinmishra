"""Local HTTP draining tests; no database or AWS access is required."""

import contextlib
import http.client
import json
import pathlib
import select
import signal
import subprocess
import sys
import threading
import types
import unittest
from unittest import mock

try:
    import pymysql
except ModuleNotFoundError:
    sys.modules["pymysql"] = types.SimpleNamespace(connect=mock.Mock())

import server


class ShutdownTests(unittest.TestCase):
    @contextlib.contextmanager
    def running_server(self, drain_timeout=1):
        database = mock.Mock()
        entered = threading.Event()
        release = threading.Event()

        def ready():
            entered.set()
            release.wait(5)

        database.ready.side_effect = ready
        httpd = server.BookServer(("127.0.0.1", 0), database, "i-test",
                                  max_workers=1, drain_timeout=drain_timeout)
        thread = threading.Thread(target=httpd.serve_forever,
                                  kwargs={"poll_interval": 0.01}, daemon=True)
        thread.start()
        connection = http.client.HTTPConnection(*httpd.server_address, timeout=3)
        try:
            yield httpd, database, connection, entered, release
        finally:
            release.set()
            connection.close()
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=3)

    def close_in_thread(self, httpd):
        closed = threading.Event()

        def close():
            httpd.server_close()
            closed.set()

        thread = threading.Thread(target=close, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 3)
        return closed

    def test_shutdown_drains_in_flight_response(self):
        with self.running_server() as (httpd, _, connection, entered, release):
            connection.request("GET", "/ready")
            self.assertTrue(entered.wait(3))
            httpd.shutdown()
            closed = self.close_in_thread(httpd)
            self.assertFalse(closed.wait(0.05))
            release.set()
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertEqual(json.loads(response.read())["status"], "ready")
            self.assertTrue(closed.wait(3))

    def test_shutdown_drain_budget_is_bounded(self):
        with self.running_server(drain_timeout=0.05) as (httpd, _, connection, entered, release):
            connection.request("GET", "/ready")
            self.assertTrue(entered.wait(3))
            httpd.shutdown()
            closed = self.close_in_thread(httpd)
            self.assertTrue(closed.wait(1), "Shutdown waited past its drain budget")
            self.assertFalse(release.is_set())
            release.set()
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            response.read()

    def test_shutdown_rejects_new_work(self):
        with self.running_server() as (httpd, database, _, _, _):
            httpd.shutdown()
            request = mock.Mock()
            httpd.process_request(request, ("127.0.0.1", 1))
            self.assertIn(b"503 Service Unavailable", request.sendall.call_args.args[0])
            request.close.assert_called_once()
            database.ready.assert_not_called()

    def test_thread_start_failure_releases_capacity_and_drain_tracking(self):
        with self.running_server(drain_timeout=1) as (httpd, _, _, _, _):
            with mock.patch.object(server.ThreadingHTTPServer, "process_request",
                                   side_effect=RuntimeError("Cannot start worker")):
                with self.assertRaises(RuntimeError):
                    httpd.process_request(mock.Mock(), ("127.0.0.1", 1))
            self.assertTrue(httpd.workers.acquire(blocking=False))
            httpd.workers.release()
            httpd.shutdown()
            self.assertTrue(self.close_in_thread(httpd).wait(0.5))

    def test_sigterm_drains_in_flight_http_response_and_exits_cleanly(self):
        program = '''
import sys
import types
sys.path.insert(0, sys.argv[1])
sys.modules["pymysql"] = types.SimpleNamespace(connect=None)
import server

class LocalDatabase:
    def __init__(self, config):
        pass
    def initialize(self):
        pass
    def ready(self):
        print("REQUEST_STARTED", flush=True)
        sys.stdin.readline()

class LocalServer(server.BookServer):
    def __init__(self, address, database, instance_id):
        super().__init__(("127.0.0.1", 0), database, instance_id)
        print(self.server_address[1], flush=True)
    def server_close(self):
        print("CLOSING", flush=True)
        super().server_close()

server.Config.from_environment = lambda: server.Config("local", "app", "unused")
server.Database = LocalDatabase
server.BookServer = LocalServer
sys.exit(server.main())
'''
        process = subprocess.Popen(
            [sys.executable, "-B", "-u", "-c", program, str(pathlib.Path(__file__).parent)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True,
        )
        connection = None

        def output_line():
            self.assertTrue(select.select([process.stdout], [], [], 3)[0],
                            "Local subprocess did not respond")
            return process.stdout.readline().strip()

        try:
            port = int(output_line())
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
            connection.request("GET", "/ready")
            self.assertEqual(output_line(), "REQUEST_STARTED")
            process.send_signal(signal.SIGTERM)
            self.assertEqual(output_line(), "CLOSING")
            self.assertIsNone(process.poll(), "Process exited before draining its request")
            process.send_signal(signal.SIGTERM)
            process.stdin.write("complete request\n")
            process.stdin.flush()
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertEqual(json.loads(response.read())["status"], "ready")
            self.assertEqual(process.wait(timeout=3), 0)
            self.assertEqual(process.stderr.read(), "")
        finally:
            if connection is not None:
                connection.close()
            if process.poll() is None:
                process.kill()
            process.wait(timeout=3)
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()


if __name__ == "__main__":
    unittest.main()
