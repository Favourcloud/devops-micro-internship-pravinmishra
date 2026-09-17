#!/usr/bin/env python3
"""Read-only probes. No redirects, ambient proxies, credentials or response logging."""
import json
import urllib.error
import urllib.request

from common import RuntimeFailure
from upstream import NoRedirect


def request(url, *, body=None, expected=200, json_response=True):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    headers = {"Accept": "application/json", "Connection": "close"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                                 headers=headers)
    try:
        response = opener.open(req, timeout=2)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        data = response.read(2 * 1024 * 1024 + 1)
        if response.code != expected or len(data) > 2 * 1024 * 1024:
            raise RuntimeFailure("probe_failed")
    return json.loads(data) if json_response else data


def api_ready(base, *, users=False):
    books = request(base + "/api/books")
    if not isinstance(books, list) or any(not isinstance(book, dict) or type(book.get("id")) is not int for book in books):
        raise RuntimeFailure("books_probe_shape")
    book_id = books[0]["id"] if books else 0
    reviews = request(base + f"/api/reviews/{book_id}")
    if not isinstance(reviews, list):
        raise RuntimeFailure("reviews_probe_shape")
    if users:
        # Exercises User.findOne without creating a user or claiming a successful login.
        result = request(base + "/api/users/login", body={"email": "readiness-probe@invalid.invalid", "password": ""}, expected=400)
        if result != {"message": "Invalid email or password"}:
            raise RuntimeFailure("users_probe_failed")


def web_ready(config):
    request("http://127.0.0.1:3000/", json_response=False)
    api_ready(config["internal_url"])
