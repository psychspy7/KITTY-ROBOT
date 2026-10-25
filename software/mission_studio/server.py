"""Optional loopback studio server. No hardware transport or model downloads."""
from __future__ import annotations
import argparse,hmac,json,math,re,secrets,threading,webbrowser
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request,urlopen
INTENTS={'explain','stop','hello','goal_alpha','goal_beta','radar','dance','future'}
MAX_BODY=16000
def model_reply(model,text,prompt,observation):
    system=prompt[:7000]+'\nMANDATORY RUNTIME: all observations are simulated; no hardware outputs. Return JSON {"reply":"...","intent":"explain|stop|hello|goal_alpha|goal_beta|radar|dance|future"}. Never clear a stop latch.'
    body={'model':model,'stream':False,'format':'json','messages':[{'role':'system','content':system},{'role':'user','content':json.dumps({'message':text,'simulator_observation':observation})}],'options':{'temperature':.35,'num_predict':200}}
    request=Request('http://127.0.0.1:11434/api/chat',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')
    with urlopen(request,timeout=13) as response:raw=response.read(65537)
    if len(raw)>65536:raise ValueError('Model response too large')
    data=json.loads(raw);content=data.get('message',{}).get('content','');result=json.loads(content)
    if not isinstance(result,dict) or result.get('intent') not in INTENTS or not isinstance(result.get('reply'),str) or not 1<=len(result['reply'])<=1200:raise ValueError('Model returned unsupported text or intent')
    return {'intent':result['intent'],'reply':result['reply'],'source':'Ollama / '+model}
def create_server(directory,model=None,port=0):
    root=Path(directory).resolve();token=secrets.token_hex(24);model_slot=threading.BoundedSemaphore(1)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def allowed(self):return self.headers.get('Host') in [f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}']
        def reply(self,status,data,kind='application/json; charset=utf-8'):
            raw=json.dumps(data).encode() if not isinstance(data,bytes) else data
            self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"default-src 'self' data: blob:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; media-src 'self' blob:; frame-ancestors 'none'");self.end_headers()
            try:self.wfile.write(raw)
            except (BrokenPipeError,ConnectionResetError):pass
        def do_GET(self):
            if not self.allowed():return self.reply(403,{'error':'Use the printed loopback URL'})
            if self.path=='/api/info':return self.reply(200,{'service':'prometheus-mission-studio','model':model,'token':token,'physical_outputs':False})
            if self.path in ['/','/PROMETHEUS-MISSION-STUDIO.html']:
                p=root/'PROMETHEUS-MISSION-STUDIO.html'
                if not p.is_file():return self.reply(404,{'error':'Build the studio HTML into this folder first'})
                return self.reply(200,p.read_bytes(),'text/html; charset=utf-8')
            return self.reply(404,{'error':'Not found'})
        def do_POST(self):
            origin='http://'+self.headers.get('Host','');given=self.headers.get('X-Studio-Token','')
            if not self.allowed() or self.path!='/api/brain' or self.headers.get('Origin')!=origin or not re.fullmatch(r'[0-9a-f]{48}',given) or not hmac.compare_digest(given,token):return self.reply(403,{'error':'Use the current local studio session'})
            if not model:return self.reply(409,{'error':'No local model configured; use offline demo rules'})
            length=self.headers.get('Content-Length','')
            if not length.isdigit() or not 0<int(length)<=MAX_BODY or self.headers.get('Transfer-Encoding'):return self.reply(413,{'error':'Invalid request size'})
            if self.headers.get_content_type()!='application/json':return self.reply(415,{'error':'JSON required'})
            try:
                self.connection.settimeout(2);data=json.loads(self.rfile.read(int(length)));
                if not isinstance(data,dict):raise ValueError('JSON object required')
                text=data.get('text');prompt=data.get('prompt');obs=data.get('observation')
                if not isinstance(text,str) or not 1<=len(text)<=1500 or not isinstance(prompt,str) or len(prompt)>7000 or not isinstance(obs,dict) or obs.get('prototype') is not True:raise ValueError('Invalid simulator request')
                for key in ['front_m','rear_m']:
                    value=obs.get(key)
                    if value is not None and (isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=4):raise ValueError('Invalid simulated range')
                safe={'mode':str(obs.get('mode',''))[:40],'reason':str(obs.get('reason',''))[:240],'front_m':obs.get('front_m'),'rear_m':obs.get('rear_m'),'prototype':True}
                sim_time=obs.get('sim_time_s')
                if sim_time is not None and (isinstance(sim_time,bool) or not isinstance(sim_time,(int,float)) or not math.isfinite(sim_time) or sim_time<0):raise ValueError('Invalid simulator time')
                marker=obs.get('marker')
                if marker is not None:
                    if not isinstance(marker,dict) or not isinstance(marker.get('valid'),bool):raise ValueError('Invalid marker snapshot')
                    age=marker.get('age_s');box=marker.get('box')
                    if age is not None and (isinstance(age,bool) or not isinstance(age,(int,float)) or not math.isfinite(age) or age<0):raise ValueError('Invalid marker age')
                    if box is not None:
                        if not isinstance(box,dict):raise ValueError('Invalid marker box')
                        for key,limit in [('x',320),('y',180),('w',320),('h',180)]:
                            v=box.get(key)
                            if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=limit:raise ValueError('Invalid marker box')
                        if box['x']+box['w']>320 or box['y']+box['h']>180:raise ValueError('Marker box outside image')
                        box={k:box[k] for k in ['x','y','w','h']}
                    safe['marker']={'valid':marker['valid'],'age_s':age,'box':box,'source':'snapshot of virtual RGB colour tracker, not general recognition'}
                safe['sim_time_s']=sim_time
                if not model_slot.acquire(blocking=False):return self.reply(503,{'error':'Local model busy; stop remains local'})
                try:result=model_reply(model,text,prompt,safe)
                finally:model_slot.release()
                return self.reply(200,result)
            except (ValueError,TypeError,UnicodeError,json.JSONDecodeError) as e:return self.reply(400,{'error':str(e)[:180]})
            except Exception:return self.reply(502,{'error':'Configured local model unavailable or timed out; offline simulation is independent'})
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler);server.daemon_threads=True;return server
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--directory',type=Path,default=Path(__file__).resolve().parent);ap.add_argument('--model',help='Already installed Ollama model; no download is performed');ap.add_argument('--port',type=int,default=0);ap.add_argument('--no-browser',action='store_true');a=ap.parse_args()
    if a.model and not re.fullmatch(r'[a-zA-Z0-9._:/-]{1,100}',a.model):ap.error('Invalid installed-model name')
    server=create_server(a.directory,a.model,a.port);url=f'http://127.0.0.1:{server.server_port}/';print('PROMETHEUS Mission Studio: '+url,flush=True);print('Simulation only. Local model: '+(a.model or 'offline rules'),flush=True)
    if not a.no_browser:threading.Timer(.7,lambda:webbrowser.open(url)).start()
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()
