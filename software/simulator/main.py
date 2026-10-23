"""Start with: python main.py  (Python 3.10+, no pip install needed)"""
import json
import os
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from brain import RobotBrain, simulation_loop

ROOT=Path(__file__).resolve().parent
BRAIN=RobotBrain()

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        if not self.path.startswith('/api/state'):
            print('[local]',format % args)

    def _json(self, value, code=200):
        data=json.dumps(value,ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Length',str(len(data)))
        self.end_headers();self.wfile.write(data)

    def do_GET(self):
        route=urlsplit(self.path).path
        if route=='/api/state':return self._json(BRAIN.snapshot())
        if route=='/api/health':return self._json({'status':'ok','brain':'Team Prometheus R1H1','hardware':'simulated'})
        if route in ('/','/index.html','/style.css','/app.js'):
            name={'/':'index.html','/index.html':'index.html','/style.css':'style.css','/app.js':'app.js'}[route]
            p=ROOT/'static'/name
            if not p.is_file():return self._json({'error':'missing asset'},404)
            data=p.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type',{'html':'text/html; charset=utf-8','css':'text/css; charset=utf-8','js':'application/javascript; charset=utf-8'}[p.suffix[1:]])
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Length',str(len(data)))
            self.end_headers();self.wfile.write(data)
            return
        self._json({'error':'not found'},404)

    def do_POST(self):
        route=urlsplit(self.path).path
        if route not in ('/api/chat','/api/action'):return self._json({'error':'not found'},404)
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length>4096 or length<=0:return self._json({'error':'Invalid request size'},400)
            data=json.loads(self.rfile.read(length))
            if not isinstance(data,dict):return self._json({'error':'Invalid JSON object'},400)
            if route=='/api/chat':
                msg=str(data.get('text',''))
                if len(msg)>1000:return self._json({'error':'Message too long'},400)
                reply=BRAIN.chat(msg)
            else:
                cmd=data.get('action')
                if not isinstance(cmd,str):return self._json({'error':'Missing action'},400)
                reply=BRAIN.action(cmd,**{k:v for k,v in data.items() if k!='action'})
            self._json({'reply':reply,'state':BRAIN.snapshot()})
        except (ValueError,TypeError,KeyError):self._json({'error':'Bad request'},400)
        except Exception as e:
            print('[server error]',repr(e))
            self._json({'error':'Internal server error'},500)


def main():
    print('\n   TEAM PROMETHEUS | ROBOT MIND R1\n   Laptop simulation — motors are NOT physically connected\n')
    thread=threading.Thread(target=simulation_loop,args=(BRAIN,),daemon=True)
    thread.start()
    port=int(os.getenv('ROBOT_PORT','0'))
    # Localhost binding is intentional: browser dashboard is not exposed to the network.
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    addr=f'http://127.0.0.1:{server.server_address[1]}'
    print(f'Open in your laptop browser: {addr}')
    print('Press Ctrl+C in this terminal to stop.\n')
    if os.getenv('ROBOT_NO_BROWSER')!='1':
        threading.Timer(0.8,lambda:webbrowser.open(addr)).start()
    try:server.serve_forever(poll_interval=.1)
    except KeyboardInterrupt:print('\nStopping Team Prometheus Robot Mind...')
    finally:BRAIN.alive=False;server.server_close()

if __name__=='__main__':main()
