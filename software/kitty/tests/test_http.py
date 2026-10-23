import json
import sys
import threading
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from main import build_server


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.server = build_server(0)
        self.thread = threading.Thread(target=self.server.serve_forever,
                                       kwargs={'poll_interval': 0.02}, daemon=True)
        self.thread.start()
        self.base = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, path, value=None):
        req = Request(self.base + path, data=None if value is None else json.dumps(value).encode(),
                      headers={} if value is None else {'Content-Type': 'application/json'})
        with urlopen(req, timeout=3) as response:
            return json.load(response)

    def action(self, name, **fields):
        return self.request('/api/action', {'action': name, **fields})

    def test_health_and_face_assets_have_explicit_preview_identity(self):
        health = self.request('/api/health')
        self.assertEqual(health['hardware'], 'disabled_no_transport')
        for path in ['/', '/face', '/app.js', '/style.css']:
            with urlopen(self.base + path, timeout=3) as response:
                self.assertEqual(response.status, 200)
                self.assertGreater(len(response.read()), 100)
        self.assertEqual(self.request('/api/state')['mode'], 'DISARMED')

    def test_fixture_approach_pause_fault_and_explicit_rearm(self):
        state = self.action('run_fixture', scenario='centered')['state']
        self.assertEqual(state['mode'], 'APPROACHING')
        self.assertFalse(state['hardware_enabled'])
        self.action('pause_feed')
        time.sleep(0.4)
        self.assertEqual(self.request('/api/state')['mode'], 'FAULT')
        self.action('resume_feed')
        time.sleep(0.04)
        self.assertEqual(self.request('/api/state')['mode'], 'FAULT')
        self.assertEqual(self.action('arm_preview')['state']['mode'], 'APPROACHING')
        self.assertEqual(self.action('estop')['state']['mode'], 'ESTOP')
        self.assertEqual(self.action('run_fixture', scenario='centered')['state']['mode'], 'ESTOP')
        self.assertEqual(self.action('reset_estop')['state']['mode'], 'DISARMED')
        self.assertEqual(self.action('disarm')['state']['command']['linear_m_s'], 0)

    def test_chat_does_not_drive_and_no_hardware_enable_endpoint_exists(self):
        answer = self.request('/api/chat', {'text': 'move forward'})
        self.assertIn('preview', answer['reply'].lower())
        self.assertFalse(answer['state']['armed'])
        with self.assertRaises(HTTPError) as caught:
            self.action('enable_hardware')
        self.assertEqual(caught.exception.code, 400)
        req = Request(self.base + '/api/action', data=b'{"action":"estop"}',
                      headers={'Content-Type': 'text/plain'})
        with self.assertRaises(HTTPError) as caught:
            urlopen(req, timeout=3)
        self.assertEqual(caught.exception.code, 415)


if __name__ == '__main__':
    unittest.main()
