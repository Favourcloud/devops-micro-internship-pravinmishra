#!/usr/bin/env python3
"""Rebuild the verified instructor source plus the disclosed demo checkout patch."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parent
UPSTREAM = 'https://github.com/pravinmishraaws/theepicbook.git'


def build(output):
    lock = json.loads((ROOT / 'source-lock.json').read_text())
    patch = (ROOT / 'demo-checkout.patch').read_bytes()
    assert hashlib.sha256(patch).hexdigest() == lock['release_id']
    with tempfile.TemporaryDirectory(prefix='epicbook-build-') as tmp:
        source = Path(tmp) / 'source'
        subprocess.run(['git', 'clone', '--quiet', '--no-checkout', UPSTREAM, str(source)], check=True)
        subprocess.run(['git', 'checkout', '--quiet', '--detach', lock['upstream']], cwd=source, check=True)
        subprocess.run(['git', 'apply', '--check', '-'], input=patch, cwd=source, check=True)
        subprocess.run(['git', 'apply', '-'], input=patch, cwd=source, check=True)
        files = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=source).decode().split('\0')
        files = sorted(set(filter(None, files)))
        actual = {name: hashlib.sha256((source / name).read_bytes()).hexdigest() for name in files}
        assert actual == lock['files'], 'Release source differs from reviewed checksums'
        payload = {name: (source / name).read_bytes() for name in files}
        payload['RELEASE.json'] = (json.dumps({'upstream': lock['upstream'], 'release_id': lock['release_id']}, sort_keys=True) + '\n').encode()
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('wb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode='w', format=tarfile.PAX_FORMAT) as archive:
                for name, data in sorted(payload.items()):
                    info = tarfile.TarInfo(name)
                    info.size = len(data)
                    info.mode = 0o644
                    archive.addfile(info, io.BytesIO(data))
    return {'release_id': lock['release_id'], 'archive': str(output.resolve()), 'archive_sha256': hashlib.sha256(output.read_bytes()).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.output), indent=2))
