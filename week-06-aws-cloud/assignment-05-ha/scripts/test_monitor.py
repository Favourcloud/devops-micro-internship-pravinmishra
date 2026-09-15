import io
import json
import unittest
from unittest.mock import patch
import urllib.error

import monitor


class Response:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def read(self, _):
        return json.dumps({'status': 'ok'}).encode()


class ProbeTests(unittest.TestCase):
    @patch('monitor.urllib.request.urlopen', return_value=Response())
    def test_success_is_timestamped_database_probe(self, request):
        result = monitor.probe('http://example.test/')
        self.assertTrue(result['ok'])
        self.assertEqual(result['status'], 200)
        self.assertEqual(result['url_path'], '/ready')
        self.assertIn('timestamp', result)
        request.assert_called_once_with('http://example.test/ready', timeout=5)

    @patch('monitor.urllib.request.urlopen', side_effect=urllib.error.HTTPError('http://example.test/ready', 503, 'Unavailable', {}, io.BytesIO()))
    def test_http_failure_is_not_retried_or_hidden(self, request):
        result = monitor.probe('http://example.test')
        self.assertFalse(result['ok'])
        self.assertEqual(result['status'], 503)
        request.assert_called_once()

    @patch('monitor.urllib.request.urlopen', side_effect=TimeoutError('timeout'))
    def test_timeout_is_failed_sample(self, request):
        result = monitor.probe('http://example.test')
        self.assertFalse(result['ok'])
        self.assertIsNone(result['status'])
        request.assert_called_once()

    @patch('monitor.urllib.request.urlopen')
    def test_invalid_json_is_failed_sample(self, request):
        response = Response()
        response.read = lambda _: b'not-json'
        request.return_value = response
        self.assertFalse(monitor.probe('http://example.test')['ok'])


if __name__ == '__main__':
    unittest.main()
