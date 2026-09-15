"""Write a synthetic book through the ALB and read it from two web instances."""
import argparse
import datetime
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    url = args.url.rstrip('/')
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    title = 'HA verification ' + timestamp
    data = urllib.parse.urlencode({'title': title, 'author': 'Synthetic lab record'}).encode()
    request = urllib.request.Request(url + '/books', data=data,
                                     headers={'Content-Type': 'application/x-www-form-urlencoded', 'Origin': url})
    with urllib.request.urlopen(request, timeout=15) as response:
        html = response.read().decode()
        assert response.status == 200 and title in html, 'Write/redirect did not render the saved record'
        assert '<script' not in html.lower(), 'Unexpected JavaScript'
    instances = set()
    for _ in range(40):
        with urllib.request.urlopen(url + '/api/books', timeout=15) as response:
            payload = json.load(response)
        assert any(book['title'] == title and book['author'] == 'Synthetic lab record' for book in payload['books']), 'Saved record was not read back'
        instances.add(payload['instance_id'])
        if len(instances) >= 2:
            break
        time.sleep(0.5)
    assert len(instances) >= 2, 'Two different serving instances were not observed'
    with urllib.request.urlopen(url + '/ready', timeout=15) as response:
        ready = json.load(response)
        assert response.status == 200
    report = {'observed_at': timestamp, 'url': url, 'title': title, 'author': 'Synthetic lab record',
              'read_write': 'passed', 'instance_ids': sorted(instances), 'ready_response': ready,
              'note': 'Synthetic form write and database read observed from two distinct web instances.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    args.output.with_suffix('.html').write_text(html)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
