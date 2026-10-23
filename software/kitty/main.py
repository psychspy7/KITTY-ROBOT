"""Run `python main.py` for the loopback-only KITTY development preview."""
from __future__ import annotations

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from brain import MissionBrain, Observation

STATIC = Path(__file__).resolve().parent / 'static'
SCENARIOS = {
    'centered': (0.0, 1.5, 2.0),
    'left': (-0.7, 1.5, 2.0),
    'right': (0.7, 1.5, 2.0),
    'obstacle': (0.0, 0.1, 2.0),
    'arrived': (0.0, 1.5, 0.3),
    'lost_target': (0.0, 1.5, 2.0),
}


class Runtime:
    def __init__(self):
        self.lock = threading.RLock()
        self.brain = MissionBrain()
        self.scenario = 'centered'
        self.feeding = False
        self.sequence = 0

    def tick(self):
        with self.lock:
            if self.feeding:
                now = time.monotonic()
                self.sequence += 1
                center, front_range, target_range = SCENARIOS[self.scenario]
                self.brain.heartbeat()
                self.brain.observe(Observation(
                    self.sequence, now, now, center,
                    0.0 if self.scenario == 'lost_target' else 0.95,
                    front_range, target_range, 'fixture'))
            self.brain.step()

    def state(self):
        with self.lock:
            return {**self.brain.snapshot(), 'fixture': {
                'running': self.feeding, 'scenario': self.scenario,
                'label': 'DEVELOPER FIXTURE — NO CAMERA OR SENSOR CONNECTED'}}

    def action(self, name, data):
        with self.lock:
            if name == 'run_fixture':
                scenario = data.get('scenario', 'centered')
                if scenario not in SCENARIOS:
                    raise ValueError('Unknown fixture')
                self.scenario, self.feeding = scenario, True
                self.tick()
                self.brain.arm_preview()
            elif name == 'pause_feed':
                self.feeding = False
            elif name == 'resume_feed':
                self.feeding = True
                self.tick()
            elif name == 'arm_preview':
                self.brain.arm_preview()
            elif name == 'disarm':
                self.feeding = False
                self.brain.disarm()
            elif name == 'estop':
                self.brain.estop()
            elif name == 'reset_estop':
                self.feeding = False
                self.brain.reset_estop()
            else:
                raise ValueError('Unknown action')
            return self.state()


class PreviewServer(ThreadingHTTPServer):
    daemon_threads = True

    def service_actions(self):
        self.runtime.tick()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def send(self, data, content_type, status=200):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(data)

    def json(self, data, status=200):
        self.send(json.dumps(data, allow_nan=False).encode(), 'application/json; charset=utf-8', status)

    def do_GET(self):
        route = urlsplit(self.path).path
        if route == '/api/health':
            return self.json({'status': 'ok', 'app': 'kitty-preview', 'hardware': 'disabled_no_transport'})
        if route == '/api/state':
            return self.json(self.server.runtime.state())
        name = {'/': 'index.html', '/face': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css'}.get(route)
        if not name:
            return self.json({'error': 'not found'}, 404)
        content_type = {'html': 'text/html', 'js': 'application/javascript', 'css': 'text/css'}[name.rsplit('.', 1)[1]]
        self.send((STATIC / name).read_bytes(), content_type + '; charset=utf-8')

    def do_POST(self):
        route = urlsplit(self.path).path
        if route not in ('/api/action', '/api/chat'):
            return self.json({'error': 'not found'}, 404)
        if self.headers.get_content_type() != 'application/json':
            return self.json({'error': 'application/json required'}, 415)
        origin = self.headers.get('Origin')
        if origin and origin != f'http://127.0.0.1:{self.server.server_port}':
            return self.json({'error': 'origin not allowed'}, 403)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 4096:
                raise ValueError('Invalid body size')
            def reject_constant(value):
                raise ValueError('Non-finite JSON')
            data = json.loads(self.rfile.read(length), parse_constant=reject_constant)
            if not isinstance(data, dict):
                raise ValueError('Expected an object')
            runtime = self.server.runtime
            if route == '/api/action':
                if not isinstance(data.get('action'), str):
                    raise ValueError('Missing action')
                return self.json({'state': runtime.action(data['action'], data)})
            text = data.get('text')
            if not isinstance(text, str) or len(text) > 700:
                raise ValueError('Text must be at most 700 characters')
            with runtime.lock:
                return self.json({'reply': runtime.brain.chat(text), 'state': runtime.state()})
        except (ValueError, TypeError, UnicodeError):
            self.json({'error': 'Invalid request'}, 400)


def build_server(port=0):
    server = PreviewServer(('127.0.0.1', port), Handler)
    server.runtime = Runtime()
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=0)
    args = parser.parse_args()
    server = build_server(args.port)
    print('KITTY preview — physical output disabled; all inputs are developer fixtures.', flush=True)
    print(f'Local preview address: http://127.0.0.1:{server.server_port}', flush=True)
    print('Face-only layout: append /face. Press Ctrl+C to stop.', flush=True)
    try:
        server.serve_forever(poll_interval=0.05)
    except KeyboardInterrupt:
        pass
    finally:
        server.runtime.brain.disarm()
        server.server_close()


if __name__ == '__main__':
    main()
