import contextlib
import http.client
import io
import json
import unittest
from unittest.mock import Mock, mock_open, patch
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

    @patch('monitor.urllib.request.urlopen', side_effect=http.client.BadStatusLine('private upstream detail'))
    def test_invalid_http_status_is_failed_sample(self, request):
        result = monitor.probe('http://example.test')
        self.assertFalse(result['ok'])
        self.assertIsNone(result['status'])
        self.assertEqual(result['error'], 'BadStatusLine')
        self.assertNotIn('private', json.dumps(result))
        request.assert_called_once()

    @patch('monitor.urllib.request.urlopen')
    def test_incomplete_http_body_is_failed_sample(self, request):
        response = Response()
        response.read = Mock(side_effect=http.client.IncompleteRead(b'private partial body', 20))
        request.return_value = response
        result = monitor.probe('http://example.test')
        self.assertFalse(result['ok'])
        self.assertIsNone(result['status'])
        self.assertEqual(result['error'], 'IncompleteRead')
        self.assertNotIn('private', json.dumps(result))
        response.read.assert_called_once_with(4096)
        request.assert_called_once()

    def test_protocol_failure_is_recorded_and_next_sample_still_runs(self):
        output = mock_open()
        with patch('sys.argv', ['monitor.py', 'http://example.test', 'unused.jsonl', '--duration', '2']), \
                patch('monitor.urllib.request.urlopen', side_effect=[
                    http.client.BadStatusLine('private upstream detail'), Response(),
                ]) as request, \
                patch('monitor.time.monotonic', side_effect=[0, 0, 0, 0.001, 1, 1, 1.001, 2]), \
                patch('monitor.time.sleep'), \
                patch('monitor.Path.mkdir'), patch('monitor.Path.open', output), \
                patch('monitor.Path.write_text') as summary, \
                contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as result:
                monitor.main()
        self.assertEqual(result.exception.code, 1)
        rows = [json.loads(call.args[0]) for call in output().write.call_args_list]
        self.assertEqual([row['ok'] for row in rows], [False, True])
        self.assertEqual(rows[0]['error'], 'BadStatusLine')
        self.assertEqual(request.call_count, 2)
        report = json.loads(summary.call_args.args[0])
        self.assertEqual((report['samples'], report['failures'], report['successes']), (2, 1, 1))

    @patch('monitor.urllib.request.urlopen')
    def test_invalid_json_is_failed_sample(self, request):
        response = Response()
        response.read = lambda _: b'not-json'
        request.return_value = response
        self.assertFalse(monitor.probe('http://example.test')['ok'])


if __name__ == '__main__':
    unittest.main()
