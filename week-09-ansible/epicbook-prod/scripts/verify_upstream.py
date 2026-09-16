#!/usr/bin/env python3
"""Probe an already-installed scratch upstream checkout; never start the app or contact MySQL."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

PIN = "763becebb8d3f5663a76bb30facddc25be63cfd5"
NODE_VERSION = "v22.23.2"


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path, help="Disposable clone at the documented revision, after npm ci")
    parser.add_argument("--node", required=True, type=Path)
    args = parser.parse_args()
    source, node = args.source.resolve(), args.node.resolve()
    env = {
        "PATH": f"{node.parent}:/usr/bin:/bin",
        "NODE_ENV": "production",
        "JAWSDB_URL": "mysql://fixture:fixture@127.0.0.1:3306/bookstore",
    }
    version = subprocess.check_output([node, "--version"], env=env, text=True).strip()
    if version != NODE_VERSION:
        raise SystemExit(f"Expected {NODE_VERSION}, received {version}")
    record = json.loads((Path(__file__).resolve().parents[1] / "evidence/upstream-source.json").read_text())
    if record["revision"] != PIN:
        raise SystemExit("Source checksum record does not match the reviewed revision")
    for relative, expected in record["sha256"].items():
        if checksum(source / relative) != expected:
            raise SystemExit(f"Source differs from the reviewed revision: {relative}")
    manifests = [source / "package.json", source / "package-lock.json"]
    before = [checksum(path) for path in manifests]
    subprocess.run([node, "--check", "server.js"], cwd=source, env=env, check=True)
    # An in-memory test harness, not an application patch or a database-backed health check.
    probe = r'''
const names = ["express", "express-handlebars", "sequelize", "mysql2", "accounting", "lodash"];
for (const name of names) require(name);
const db = require("./models");
const engine = require("express-handlebars").create({defaultLayout: "main", layoutsDir: "views/layouts"});
const book = db.Book.build({id: 1, title: "A5_COMPATIBILITY_BOOK", genre: "fixture", price: 12});
engine.renderView("views/index.handlebars", {books: [book], categories: [], cartCount: 0})
  .then(html => {
    if (!html.includes("A5_COMPATIBILITY_BOOK")) throw Error("Sequelize book title did not render");
    console.log(JSON.stringify({imports: names, dialect: db.sequelize.getDialect(), book_title_rendered: true}));
    return db.sequelize.close();
  }).catch(error => { console.error(error.message); process.exitCode = 1; });
'''
    result = subprocess.check_output([node, "-e", probe], cwd=source, env=env, text=True)
    if before != [checksum(path) for path in manifests]:
        raise SystemExit("Upstream manifests changed during the probe")
    print(json.dumps({
        "expected_source_revision": PIN,
        "revision_verification": "All 19 recorded source file checksums matched the reviewed revision",
        "node": version,
        "manifest_sha256": dict(zip([p.name for p in manifests], before)),
        "probe": json.loads(result),
        "database_contacted": False,
        "http_server_started": False,
        "scope": "Local import and template compatibility only, not full runtime verification",
    }, indent=2))


if __name__ == "__main__":
    main()
