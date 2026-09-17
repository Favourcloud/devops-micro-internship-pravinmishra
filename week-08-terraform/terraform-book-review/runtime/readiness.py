#!/usr/bin/env python3
"""Loopback Web readiness endpoint: Next and DB-backed internal API must both succeed."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import sys
from common import RuntimeFailure, load_config
from probes import web_ready


def handler(config):
    class ReadinessHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            code = 404
            if self.path == "/healthz":
                try:
                    web_ready(config)
                    code = 200
                except Exception:
                    code = 503
            self.send_response(code)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(b"ready\n" if code == 200 else b"unavailable\n")

        def log_message(self, format, *args):
            pass
    return ReadinessHandler


def main():
    try:
        config = load_config()
        if config["tier"] != "web":
            raise RuntimeFailure("health_wrong_tier")
        server = HTTPServer(("127.0.0.1", 3002), handler(config))
        server.socket.settimeout(5)
        server.serve_forever()
    except Exception:
        print("web_readiness_service_failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
