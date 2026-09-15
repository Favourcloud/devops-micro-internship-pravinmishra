#!/usr/bin/env python3
"""Educational book list; run behind Nginx with /usr/bin/python3 server.py.

Runtime dependency: Ubuntu package python3-pymysql. Required environment:
DB_HOST (RDS DNS hostname), DB_USER, DB_PASSWORD. Optional: DB_NAME (epicbook),
INSTANCE_ID (unknown). Install the AWS RDS CA bundle at
/etc/ssl/certs/rds-global-bundle.pem. Never use an IP instead of the RDS hostname.
The database must already exist; this app creates only its books table.
Grant this user CREATE, SELECT and INSERT on that database. Nginx must preserve
the browser's Host header (proxy_set_header Host $http_host) for origin checks;
configure request/body timeouts and rate limits there. Runtime listens only on
127.0.0.1:8000. Startup retries schema creation eight times before exiting 1;
configure systemd restart-on-failure and allow for database startup delays.

List endpoints return the latest 100 books. /health is process-only; /ready
checks MySQL. All database connections require a verified TLS 1.2+ session.
This anonymous educational app has no authentication; restrict write access
at the proxy/network boundary if it is not intended for public submissions.
"""

import html
import json
import os
import socket
import ssl
import sys
import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

import pymysql


CA_BUNDLE = "/etc/ssl/certs/rds-global-bundle.pem"
MAX_FIELD_LENGTH = 200
MAX_BODY_BYTES = 8192
LIST_LIMIT = 100
CREATE_SCHEMA = """
CREATE TABLE IF NOT EXISTS books (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(200) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""


class DatabaseUnavailable(Exception):
    """A database operation failed; details are never exposed to clients."""


@dataclass(frozen=True)
class Config:
    host: str
    user: str
    password: str = field(repr=False)
    database: str = "epicbook"
    instance_id: str = "unknown"

    @classmethod
    def from_environment(cls, environ=None):
        environ = os.environ if environ is None else environ
        required = [environ.get(name, "") for name in
                    ("DB_HOST", "DB_USER", "DB_PASSWORD")]
        if not all(required):
            raise ValueError("Missing database configuration")
        database = environ.get("DB_NAME", "epicbook")
        if not database:
            raise ValueError("Missing database name")
        return cls(*required, database=database,
                   instance_id=environ.get("INSTANCE_ID", "unknown")[:128])


class Database:
    def __init__(self, config, connect=None, tls_context=None):
        self.config = config
        self.connect = pymysql.connect if connect is None else connect
        self.tls = tls_context if tls_context is not None else ssl.create_default_context(
            cafile=CA_BUNDLE
        )
        self.tls.verify_mode = ssl.CERT_REQUIRED
        self.tls.check_hostname = True
        self.tls.minimum_version = ssl.TLSVersion.TLSv1_2

    def execute(self, query, parameters=(), fetch=False):
        connection = None
        try:
            connection = self.connect(
                host=self.config.host, user=self.config.user,
                password=self.config.password, database=self.config.database,
                port=3306, charset="utf8mb4", autocommit=True,
                connect_timeout=5, read_timeout=5, write_timeout=5,
                ssl=self.tls,
            )
            with connection.cursor() as cursor:
                # Some driver/server combinations can otherwise silently skip TLS.
                cursor.execute("SHOW SESSION STATUS LIKE 'Ssl_cipher'")
                cipher = cursor.fetchone()
                if not cipher or not cipher[1]:
                    raise DatabaseUnavailable()
                cursor.execute(query, parameters)
                return cursor.fetchall() if fetch else None
        except Exception:
            raise DatabaseUnavailable() from None
        finally:
            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass

    def initialize(self, attempts=8, sleep=time.sleep):
        for attempt in range(attempts):
            try:
                self.execute(CREATE_SCHEMA)
                return
            except DatabaseUnavailable:
                if attempt == attempts - 1:
                    raise
                sleep(min(2 ** attempt, 10))
        raise DatabaseUnavailable()

    def list_books(self):
        rows = self.execute(
            "SELECT id, title, author FROM books ORDER BY id DESC LIMIT %s",
            (LIST_LIMIT,), fetch=True,
        )
        return [dict(zip(("id", "title", "author"), row)) for row in rows]

    def add_book(self, title, author):
        self.execute("INSERT INTO books (title, author) VALUES (%s, %s)",
                     (title, author))

    def ready(self):
        rows = self.execute("SELECT 1", fetch=True)
        if not rows or rows[0][0] != 1:
            raise DatabaseUnavailable()


def render_page(books, instance_id):
    entries = "".join(
        "<li><strong>" + html.escape(book["title"], quote=True)
        + "</strong> by " + html.escape(book["author"], quote=True) + "</li>"
        for book in books
    ) or "<li>No books yet. Add the first one!</li>"
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>EpicBook · Shared book list</title>
<style>
body {{font-family:system-ui,sans-serif;max-width:48rem;margin:auto;padding:1.5rem;background:#f5f7fa;color:#152536}}
main {{background:white;padding:1.5rem;border-radius:.5rem}}
label {{display:block;margin-top:1rem}} input {{box-sizing:border-box;width:100%;padding:.7rem;font:inherit}}
button {{margin-top:1rem;padding:.7rem 1rem;background:#184b85;color:white;border:0;font:inherit;cursor:pointer}}
li {{margin:.8rem 0;overflow-wrap:anywhere}} footer {{margin-top:2rem;overflow-wrap:anywhere}}
</style></head>
<body><main><h1>EpicBook</h1><p>A shared reading list backed by Amazon RDS.</p>
<form method="post" action="/books" accept-charset="UTF-8">
<label for="title">Title</label><input id="title" name="title" maxlength="200" required>
<label for="author">Author</label><input id="author" name="author" maxlength="200" required>
<button type="submit">Add book</button></form>
<h2>Latest {LIST_LIMIT} books</h2><ul>{entries}</ul>
<footer>Served by instance: {html.escape(instance_id, quote=True)}</footer>
</main></body></html>"""


class BookServer(ThreadingHTTPServer):
    daemon_threads = True
    block_on_close = False
    request_queue_size = 32

    def __init__(self, address, database, instance_id, max_workers=32):
        self.database = database
        self.instance_id = instance_id
        self.workers = threading.BoundedSemaphore(max_workers)
        super().__init__(address, BookHandler)

    def get_request(self):
        request, address = super().get_request()
        request.settimeout(10)
        return request, address

    def process_request(self, request, client_address):
        if not self.workers.acquire(blocking=False):
            try:
                request.sendall(b"HTTP/1.0 503 Service Unavailable\r\n"
                                b"Content-Length: 0\r\nConnection: close\r\n\r\n")
            except OSError:
                pass
            finally:
                self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.workers.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.workers.release()

    def handle_error(self, request, client_address):
        # Do not print tracebacks or request data, which may contain secrets.
        print("Request could not be completed.", file=sys.stderr)


class BookHandler(BaseHTTPRequestHandler):
    server_version = "EpicBook"
    sys_version = ""

    def log_message(self, format, *args):
        pass

    def respond(self, status, body, content_type="text/plain; charset=utf-8", location=None):
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy",
                         "default-src 'none'; style-src 'unsafe-inline'; "
                         "form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.send_header("Connection", "close")
        if location:
            self.send_header("Location", location)
        self.end_headers()
        self.close_connection = True
        if self.command != "HEAD":
            try:
                self.wfile.write(payload)
            except OSError:
                pass

    def send_error(self, code, message=None, explain=None):
        self.respond(code, "Request could not be completed.\n")

    def json_response(self, status, data):
        self.respond(status, json.dumps(data), "application/json; charset=utf-8")

    def do_GET(self):
        try:
            path = urlsplit(self.path).path
        except ValueError:
            self.respond(400, "Invalid request.\n")
            return
        if path == "/health":
            self.json_response(200, {"status": "ok", "instance_id": self.server.instance_id})
            return
        if path not in ("/", "/ready", "/api/books"):
            self.respond(404, "Not found.\n")
            return
        try:
            if path == "/ready":
                self.server.database.ready()
                self.json_response(200, {"status": "ready", "instance_id": self.server.instance_id})
            else:
                books = self.server.database.list_books()
                if path == "/api/books":
                    self.json_response(200, {"books": books, "instance_id": self.server.instance_id})
                else:
                    self.respond(200, render_page(books, self.server.instance_id),
                                 "text/html; charset=utf-8")
        except DatabaseUnavailable:
            if path == "/ready":
                self.json_response(503, {"status": "unavailable", "instance_id": self.server.instance_id})
            else:
                self.respond(503, "Book storage is temporarily unavailable.\n")

    def do_POST(self):
        if self.path != "/books":
            self.respond(404, "Not found.\n")
            return
        origin = self.headers.get("Origin")
        try:
            cross_origin = origin is not None and (
                urlsplit(origin).scheme not in ("http", "https")
                or urlsplit(origin).netloc.lower() != self.headers.get("Host", "").lower()
            )
        except ValueError:
            cross_origin = True
        if cross_origin or self.headers.get("Sec-Fetch-Site") == "cross-site":
            self.respond(403, "Cross-site submissions are not allowed.\n")
            return
        lengths = self.headers.get_all("Content-Length", [])
        if self.headers.get("Transfer-Encoding") is not None or len(lengths) != 1:
            self.respond(400, "A single Content-Length is required.\n")
            return
        if not lengths[0].isascii() or not lengths[0].isdigit():
            self.respond(400, "Invalid Content-Length.\n")
            return
        # Limit digit count before int conversion to avoid unbounded parsing.
        if len(lengths[0]) > 5 or int(lengths[0]) > MAX_BODY_BYTES:
            self.respond(413, "Form is too large.\n")
            return
        length = int(lengths[0])
        if self.headers.get_content_type() != "application/x-www-form-urlencoded":
            self.respond(415, "Expected a URL-encoded form.\n")
            return
        try:
            body = self.rfile.read(length)
            if len(body) != length:
                raise ValueError()
            fields = parse_qs(body.decode("utf-8"), keep_blank_values=True,
                              strict_parsing=True, encoding="utf-8", errors="strict",
                              max_num_fields=2)
            if set(fields) != {"title", "author"}:
                raise ValueError()
            values = [fields[key][0].strip() for key in ("title", "author")]
            if any(not value or len(value) > MAX_FIELD_LENGTH
                   or any(ord(char) < 32 or ord(char) == 127 for char in value)
                   for value in values):
                raise ValueError()
        except (ValueError, UnicodeError):
            self.respond(400, "Provide a title and author of 1–200 characters each.\n")
            return
        except (socket.timeout, OSError):
            self.respond(408, "Request timed out.\n")
            return
        try:
            self.server.database.add_book(*values)
        except DatabaseUnavailable:
            self.respond(503, "Book storage is temporarily unavailable.\n")
            return
        self.respond(303, "", location="/")


def main():
    try:
        config = Config.from_environment()
        database = Database(config)
        database.initialize()
        server = BookServer(("127.0.0.1", 8000), database, config.instance_id)
    except Exception:
        print("Startup failed; check database configuration, TLS trust and connectivity.",
              file=sys.stderr)
        return 1
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
