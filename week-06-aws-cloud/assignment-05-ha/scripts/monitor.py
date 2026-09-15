"""Timestamped, no-retry HTTP probes; HTTP/protocol errors remain failed samples."""
import argparse
import datetime
import http.client
import json
from pathlib import Path
import time
import urllib.error
import urllib.request


def probe(url):
    started = time.monotonic()
    row = {'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'url_path': '/ready'}
    try:
        with urllib.request.urlopen(url.rstrip('/') + '/ready', timeout=5) as response:
            row['status'] = response.status
            row['response'] = json.loads(response.read(4096))
        row['ok'] = row['status'] == 200
    except urllib.error.HTTPError as error:
        row.update(status=error.code, ok=False, error='HTTPError')
    except (OSError, ValueError, http.client.HTTPException) as error:
        row.update(status=None, ok=False, error=type(error).__name__)
    row['duration_ms'] = round((time.monotonic() - started) * 1000, 1)
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url')
    parser.add_argument('output', type=Path)
    parser.add_argument('--duration', type=int, default=1800)
    parser.add_argument('--interval', type=float, default=1)
    parser.add_argument('--stop-file', type=Path)
    args = parser.parse_args()
    if args.duration <= 0 or args.interval <= 0:
        parser.error('duration and interval must be positive')
    if args.stop_file and args.stop_file.exists():
        parser.error('Remove the old stop file before starting a new monitor')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + args.duration
    samples = failures = 0
    with args.output.open('x', buffering=1) as output:
        while time.monotonic() < deadline:
            if args.stop_file and args.stop_file.exists():
                break
            row = probe(args.url)
            output.write(json.dumps(row) + '\n')
            samples += 1
            failures += not row['ok']
            time.sleep(args.interval)
    summary = {'samples': samples, 'failures': failures, 'successes': samples - failures,
               'note': 'Finite sampled database-readiness observations, not a guarantee of uninterrupted availability.'}
    args.output.with_suffix('.summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary))
    raise SystemExit(1 if failures or samples == 0 else 0)


if __name__ == '__main__':
    main()
