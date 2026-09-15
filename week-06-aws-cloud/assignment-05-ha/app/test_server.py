"""Run: python3 -B -m unittest discover -s week-06-aws-cloud/assignment-05-ha/app -v

No database, AWS access, CA bundle, or installed PyMySQL is needed.
"""

import contextlib
import http.client
import io
import json
import pathlib
import socket
import ssl
import sys
import threading
import types
import unittest
from unittest import mock
from urllib.parse import urlencode

try:
    import pymysql
except ModuleNotFoundError:
    sys.modules["pymysql"] = types.SimpleNamespace(connect=mock.Mock())

import server


class ConfigTests(unittest.TestCase):
    def test_environment_contract(self):
        config = server.Config.from_environment({
            "DB_HOST": "test.rds.amazonaws.com", "DB_USER": "app",
            "DB_PASSWORD": "secret", "INSTANCE_ID": "i-example",
        })
        self.assertEqual(config.database, "epicbook")
        self.assertEqual(config.instance_id, "i-example")
        self.assertNotIn("secret", repr(config))

    def test_missing_configuration(self):
        with self.assertRaises(ValueError):
            server.Config.from_environment({})

    def test_default_instance_and_custom_database(self):
        config = server.Config.from_environment({
            "DB_HOST": "db", "DB_USER": "app", "DB_PASSWORD": "password",
            "DB_NAME": "custom",
        })
        self.assertEqual(config.database, "custom")
        self.assertEqual(config.instance_id, "unknown")

    def test_empty_database_is_invalid(self):
        with self.assertRaises(ValueError):
            server.Config.from_environment({
                "DB_HOST": "db", "DB_USER": "app", "DB_PASSWORD": "password",
                "DB_NAME": "",
            })


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.connect = mock.MagicMock()
        self.connection = self.connect.return_value
        self.cursor = self.connection.cursor.return_value.__enter__.return_value
        self.cursor.fetchone.return_value = ("Ssl_cipher", "TLS_AES_256_GCM_SHA384")
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.database = server.Database(
            server.Config("db.rds.amazonaws.com", "app", "secret"),
            connect=self.connect, tls_context=self.context,
        )

    def test_verified_tls_timeouts_and_parameterized_insert(self):
        title = "'); DROP TABLE books; --"
        self.database.add_book(title, "Author")
        options = self.connect.call_args.kwargs
        self.assertEqual(options["host"], "db.rds.amazonaws.com")
        self.assertIs(options["ssl"], self.context)
        self.assertEqual(self.context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(self.context.check_hostname)
        self.assertEqual(self.context.minimum_version, ssl.TLSVersion.TLSv1_2)
        for option in ("connect_timeout", "read_timeout", "write_timeout"):
            self.assertEqual(options[option], 5)
        self.assertTrue(options["autocommit"])
        self.cursor.execute.assert_called_with(
            "INSERT INTO books (title, author) VALUES (%s, %s)", (title, "Author"))
        self.connection.close.assert_called_once()

    def test_ca_bundle_path(self):
        with mock.patch.object(server.ssl, "create_default_context", return_value=self.context) as factory:
            server.Database(server.Config("db", "app", "secret"), connect=self.connect)
        factory.assert_called_once_with(cafile="/etc/ssl/certs/rds-global-bundle.pem")

    def test_no_fallback_without_tls(self):
        for cipher in (None, ("Ssl_cipher", "")):
            with self.subTest(cipher=cipher):
                self.cursor.fetchone.return_value = cipher
                self.cursor.execute.reset_mock()
                with self.assertRaises(server.DatabaseUnavailable):
                    self.database.add_book("title", "author")
                self.cursor.execute.assert_called_once_with("SHOW SESSION STATUS LIKE 'Ssl_cipher'")
        self.assertEqual(self.connection.close.call_count, 2)

    def test_db_errors_are_sanitized_and_connection_closed(self):
        self.cursor.execute.side_effect = RuntimeError("private internal secret")
        with self.assertRaises(server.DatabaseUnavailable) as error:
            self.database.list_books()
        self.assertNotIn("secret", str(error.exception))
        self.connection.close.assert_called_once()

    def test_connect_error_is_sanitized(self):
        self.connect.side_effect = RuntimeError("password=secret")
        with self.assertRaises(server.DatabaseUnavailable) as error:
            self.database.ready()
        self.assertEqual(str(error.exception), "")

    def test_list_is_bounded_and_serializable(self):
        self.cursor.fetchall.return_value = ((5, "Title", "Author"),)
        self.assertEqual(self.database.list_books(), [{"id": 5, "title": "Title", "author": "Author"}])
        self.cursor.execute.assert_called_with(
            "SELECT id, title, author FROM books ORDER BY id DESC LIMIT %s", (100,))

    def test_readiness_query(self):
        self.cursor.fetchall.return_value = ((1,),)
        self.database.ready()
        self.cursor.execute.assert_called_with("SELECT 1", ())
        self.cursor.fetchall.return_value = ()
        with self.assertRaises(server.DatabaseUnavailable):
            self.database.ready()

    def test_schema_retries_and_is_idempotent(self):
        with mock.patch.object(self.database, "execute", side_effect=[
            server.DatabaseUnavailable(), server.DatabaseUnavailable(), None,
        ]) as execute:
            sleep = mock.Mock()
            self.database.initialize(sleep=sleep)
        self.assertEqual(execute.call_count, 3)
        self.assertIn("CREATE TABLE IF NOT EXISTS books", execute.call_args.args[0])
        self.assertEqual(sleep.call_args_list, [mock.call(1), mock.call(2)])

    def test_retry_exhaustion_is_bounded(self):
        with mock.patch.object(self.database, "execute", side_effect=server.DatabaseUnavailable()) as execute:
            sleep = mock.Mock()
            with self.assertRaises(server.DatabaseUnavailable):
                self.database.initialize(sleep=sleep)
        self.assertEqual(execute.call_count, 8)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [1, 2, 4, 8, 10, 10, 10])


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = mock.Mock()
        cls.httpd = server.BookServer(("127.0.0.1", 0), cls.database, "i-test")
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.httpd.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=5)

    def setUp(self):
        self.database.reset_mock(return_value=True, side_effect=True)
        self.database.list_books.return_value = []

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read().decode("utf-8")
        finally:
            connection.close()

    def post(self, fields, headers=None):
        return self.request("POST", "/books", urlencode(fields), headers or {
            "Content-Type": "application/x-www-form-urlencoded",
        })

    def test_health_does_not_touch_db(self):
        self.database.ready.side_effect = server.DatabaseUnavailable()
        status, headers, body = self.request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {"status": "ok", "instance_id": "i-test"})
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(self.database.mock_calls, [])

    def test_readiness_success_and_failure(self):
        status, _, body = self.request("GET", "/ready")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["status"], "ready")
        self.database.ready.side_effect = server.DatabaseUnavailable("secret")
        status, _, body = self.request("GET", "/ready")
        self.assertEqual(status, 503)
        self.assertEqual(json.loads(body)["status"], "unavailable")
        self.assertNotIn("secret", body)

    def test_html_escapes_data_and_has_no_javascript(self):
        self.database.list_books.return_value = [{
            "id": 1, "title": '<script>alert("x")</script>', "author": "A & <B>",
        }]
        status, headers, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("&lt;script&gt;", body)
        self.assertIn("A &amp; &lt;B&gt;", body)
        self.assertNotIn("<script", body)
        self.assertNotIn("javascript:", body)
        self.assertIn('method="post"', body)
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        self.assertIn("&lt;instance&gt;", server.render_page([], "<instance>"))

    def test_api_read(self):
        books = [{"id": 4, "title": "Book", "author": "Author"}]
        self.database.list_books.return_value = books
        status, _, body = self.request("GET", "/api/books")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {"books": books, "instance_id": "i-test"})

    def test_post_redirect_and_unicode(self):
        status, headers, body = self.post({"title": "  Café 📚  ", "author": " Author "})
        self.assertEqual(status, 303)
        self.assertEqual(headers["Location"], "/")
        self.assertEqual(body, "")
        self.database.add_book.assert_called_once_with("Café 📚", "Author")

    def test_maximum_field_length_is_accepted(self):
        self.assertEqual(self.post({"title": "a" * 200, "author": "b" * 200})[0], 303)

    def test_invalid_fields(self):
        for fields in (
            {"title": "", "author": "Author"},
            {"title": "   ", "author": "Author"},
            {"title": "x" * 201, "author": "Author"},
            {"title": "Title", "author": "x" * 201},
            {"title": "Title"},
            {"title": "Title", "author": "Author", "extra": "field"},
            [("title", "one"), ("title", "two")],
            {"title": "bad\x00title", "author": "Author"},
        ):
            with self.subTest(fields=fields):
                self.assertEqual(self.post(fields)[0], 400)
        self.database.add_book.assert_not_called()

    def test_body_limits_and_encoding(self):
        cases = [
            ("a" * 8193, {"Content-Type": "application/x-www-form-urlencoded"}, 413),
            ("{}", {"Content-Type": "application/json"}, 415),
            (b"title=%FF&author=A", {"Content-Type": "application/x-www-form-urlencoded"}, 400),
            (b"title=\xff&author=A", {"Content-Type": "application/x-www-form-urlencoded"}, 400),
            ("x", {"Content-Length": "-1"}, 400),
            ("x", {"Transfer-Encoding": "chunked"}, 400),
        ]
        for body, headers, expected in cases:
            with self.subTest(body=body[:20], headers=headers):
                self.assertEqual(self.request("POST", "/books", body, headers)[0], expected)
        self.database.add_book.assert_not_called()

    def test_duplicate_or_missing_length_rejected(self):
        for lengths in (b"", b"Content-Length: 0\r\nContent-Length: 0\r\n"):
            with socket.create_connection(("127.0.0.1", self.port), timeout=3) as client:
                client.sendall(b"POST /books HTTP/1.0\r\n" + lengths + b"\r\n")
                self.assertIn(b" 400 ", client.recv(4096).split(b"\r\n")[0])

    def test_cross_site_submission_is_rejected(self):
        for headers in ({"Origin": "https://other.example"}, {"Origin": "null"},
                        {"Sec-Fetch-Site": "cross-site"}):
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            self.assertEqual(self.post({"title": "Title", "author": "Author"}, headers)[0], 403)
        self.database.add_book.assert_not_called()

    def test_same_origin_submission_is_allowed(self):
        status, _, _ = self.post({"title": "Title", "author": "Author"}, {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://books.example", "Host": "books.example",
        })
        self.assertEqual(status, 303)

    def test_database_failures_do_not_leak(self):
        self.database.list_books.side_effect = server.DatabaseUnavailable("secret db hostname")
        self.database.add_book.side_effect = server.DatabaseUnavailable("secret db hostname")
        responses = [self.request("GET", "/"), self.request("GET", "/api/books"),
                     self.post({"title": "Title", "author": "Author"})]
        for status, _, body in responses:
            self.assertEqual(status, 503)
            self.assertNotIn("secret", body)

    def test_unknown_path_and_unsupported_method(self):
        self.assertEqual(self.request("GET", "/missing")[0], 404)
        self.assertEqual(self.request("POST", "/missing", "")[0], 404)
        status, _, body = self.request("DELETE", "/books")
        self.assertEqual(status, 501)
        self.assertNotIn("DELETE", body)

    def test_worker_limit_rejects_without_starting_thread(self):
        limited = server.BookServer(("127.0.0.1", 0), self.database, "test", max_workers=1)
        request = mock.Mock()
        limited.workers.acquire()
        try:
            limited.process_request(request, ("127.0.0.1", 1))
            self.assertIn(b"503", request.sendall.call_args.args[0])
            request.close.assert_called_once()
        finally:
            limited.workers.release()
            limited.server_close()


class StartupTests(unittest.TestCase):
    def test_main_initializes_before_serving_on_loopback(self):
        config = server.Config("db", "app", "secret", instance_id="i-test")
        with mock.patch.object(server.Config, "from_environment", return_value=config), \
                mock.patch.object(server, "Database") as database, \
                mock.patch.object(server, "BookServer") as httpd:
            httpd.return_value.serve_forever.side_effect = KeyboardInterrupt()
            self.assertEqual(server.main(), 0)
            database.return_value.initialize.assert_called_once()
            httpd.assert_called_once_with(("127.0.0.1", 8000), database.return_value, "i-test")
            httpd.return_value.server_close.assert_called_once()

    def test_failed_startup_does_not_print_secret(self):
        output = io.StringIO()
        with mock.patch.object(server.Config, "from_environment", side_effect=ValueError("secret")), \
                contextlib.redirect_stderr(output):
            self.assertEqual(server.main(), 1)
        self.assertNotIn("secret", output.getvalue())
        self.assertNotIn("Traceback", output.getvalue())

    def test_server_is_safe_for_terraform_templatefile(self):
        source = pathlib.Path(server.__file__).read_text()
        self.assertNotIn("${", source)
        self.assertNotIn("%{", source)


if __name__ == "__main__":
    unittest.main()
