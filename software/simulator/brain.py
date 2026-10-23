"""Team Prometheus R1 laptop brain: simulation + deterministic safety controller.

No dependencies outside Python's standard library. All dimensions in virtual pixels.
The world map is a simulator privilege, NOT a physical robot sensor capability.
"""
from __future__ import annotations

import heapq
import math
import os
import re
import threading
import time
import urllib.error
import urllib.request
import json
from collections import deque
from dataclasses import dataclass

W, H = 900, 550
ROBOT_R = 20.0
CELL = 18
MAX_SPEED = 85.0
TURN_SPEED = 160.0
MAX_RANGE = 180.0
DEFAULT_OBSTACLES = [
    {'id':'crate-a', 'x':290, 'y':100, 'w':70, 'h':165},
    {'id':'crate-b', 'x':495, 'y':305, 'w':130, 'h':65},
    {'id':'crate-c', 'x':670, 'y':88, 'w':55, 'h':90},
]
ZONES = {
    'home': {'x':102, 'y':420, 'name':'Home base'},
    'presentation': {'x':777, 'y':415, 'name':'Presentation zone'},
    'lab': {'x':762, 'y':115, 'name':'Innovation lab'},
    'charger': {'x':100, 'y':125, 'name':'Charging point'},
}


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def wrap_angle(a):
    return (a + math.pi) % (2*math.pi) - math.pi


def dist(a,b):
    return math.hypot(a[0]-b[0],a[1]-b[1])


def point_to_rect_distance(x,y,o):
    qx=clamp(x,o['x'],o['x']+o['w'])
    qy=clamp(y,o['y'],o['y']+o['h'])
    return math.hypot(x-qx,y-qy)


@dataclass
class Pose:
    x: float = 105.0
    y: float = 415.0
    angle: float = -0.1


class RobotBrain:
    def __init__(self):
        self.lock = threading.RLock()
        self.pose = Pose()
        self.mode = 'IDLE'
        self.safety = 'READY'
        self.target = None
        self.path = []
        self.obstacles = [dict(x) for x in DEFAULT_OBSTACLES]
        self.events = deque(maxlen=70)
        self.memory = deque(maxlen=12)
        self.distance_travelled = 0
        self.manual = None
        self.manual_until = 0
        self.last_replan = 0
        self._log('SYSTEM', 'Mind initialized. Virtual motors and sensors are online.')
        self._log('SAFETY', 'Software stop, obstacle checks and command timeout armed.')
        self.start_time = time.monotonic()
        self.alive = True

    def _log(self, kind, message):
        self.events.append({'time':time.strftime('%H:%M:%S'), 'kind':kind, 'text':message})

    def _collides(self,x,y, pad=0):
        r=ROBOT_R+pad
        if not (r < x < W-r and r < y < H-r):return True
        return any(point_to_rect_distance(x,y,o)<r for o in self.obstacles)

    def _ray(self,ang):
        # Robot-front surface to obstruction; simulated obstacle map used as a range sensor.
        for d in range(0,int(MAX_RANGE)+1,3):
            x=self.pose.x+(ROBOT_R+d)*math.cos(ang)
            y=self.pose.y+(ROBOT_R+d)*math.sin(ang)
            if x<0 or x>W or y<0 or y>H or any(o['x']<=x<=o['x']+o['w'] and o['y']<=y<=o['y']+o['h'] for o in self.obstacles):
                return float(d)
        return MAX_RANGE

    def _senses(self):
        a=self.pose.angle
        return {'front':round(self._ray(a)), 'left':round(self._ray(a-math.radians(40))), 'right':round(self._ray(a+math.radians(40)))}

    def snapshot(self):
        with self.lock:
            return self._snapshot()

    def _snapshot(self):
        sensors=self._senses()
        return {
          'pose':{'x':round(self.pose.x,1),'y':round(self.pose.y,1),'angle':round(self.pose.angle,3)},
          'mode':self.mode,'safety':self.safety,'sensors':sensors,
          'speed':round(MAX_SPEED if self.mode in ('NAVIGATING','MANUAL_FORWARD','MANUAL_BACKWARD') else 0),
          'target':self.target, 'path':[{'x':round(x,1),'y':round(y,1)} for x,y in self.path],
          'obstacles':[dict(x) for x in self.obstacles], 'zones':ZONES,
          'distance_travelled':round(self.distance_travelled/100,1),
          'uptime':int(time.monotonic()-self.start_time),
          'events':list(self.events)[-16:],
          'mind':self._mind_note(sensors),
          'ai_connected':bool(os.getenv('ROBOT_LLM_KEY','').strip()) or os.getenv('ROBOT_LLM_PROVIDER','').lower()=='ollama',
        }

    def _mind_note(self, sensors):
        if self.safety!='READY': return 'Emergency stop active. All simulated movement disabled until release.'
        if self.mode=='NAVIGATING':
            return f'Following planned route. Forward clearance {sensors["front"]} cm (virtual).'
        if self.mode.startswith('MANUAL'):return 'Direct movement command active with automatic timeout and collision guard.'
        if self.mode=='ARRIVED':return 'Destination reached. Waiting for next instruction.'
        if self.mode=='BLOCKED':return 'No collision-free route found. Waiting for a new destination or obstacle change.'
        return 'Standing by. Try a destination, movement command, or a question.'

    def _astar(self, target):
        # A* with full map knowledge: useful digital twin, not real SLAM.
        nx=math.ceil(W/CELL); ny=math.ceil(H/CELL)
        start=(int(self.pose.x//CELL),int(self.pose.y//CELL))
        goal=(int(target['x']//CELL),int(target['y']//CELL))
        def center(q):return ((q[0]+.5)*CELL,(q[1]+.5)*CELL)
        def valid(q):
            x,y=center(q)
            return 0<=q[0]<nx and 0<=q[1]<ny and not self._collides(x,y,pad=9)
        # Allow the exact start, even if nearby obstacle was dynamically inserted.
        if not valid(goal):return []
        todo=[(0,start)]; cost={start:0.}; came={}
        while todo:
            _,u=heapq.heappop(todo)
            if u==goal:
                route=[goal]
                while route[-1] in came:route.append(came[route[-1]])
                route.reverse()
                points=[center(q) for q in route]
                if len(points)>1:points=points[1:]
                points.append((float(target['x']),float(target['y'])))
                return points
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                v=(u[0]+dx,u[1]+dy)
                if not valid(v):continue
                if dx and dy and (not valid((u[0]+dx,u[1])) or not valid((u[0],u[1]+dy))):continue
                g=cost[u]+(1.4142 if dx and dy else 1)
                if g>=cost.get(v,1e9):continue
                cost[v]=g; came[v]=u
                h=math.hypot(v[0]-goal[0],v[1]-goal[1])
                heapq.heappush(todo,(g+h,v))
        return []

    def navigate(self,x,y, name='Custom target'):
        with self.lock:
            if self.safety!='READY':return 'Emergency stop is active. Release it before navigating.'
            x=float(x); y=float(y)
            if not (0<=x<=W and 0<=y<=H):return 'Target is outside the arena.'
            if self._collides(x,y,pad=9):return 'That destination is inside an obstacle or too close to an edge. Pick a clear area.'
            target={'x':round(x),'y':round(y),'name':name}
            route=self._astar(target)
            if not route:
                self.mode='BLOCKED';self.path=[];self.target=target
                self._log('PLANNER','No safe route found. Refusing to drive.')
                return 'I cannot find a safe path there. Try removing an obstacle or picking another point.'
            self.target=target;self.path=route;self.mode='NAVIGATING';self.manual=None
            self._log('PLAN',f'Route to {name}: {len(route)} waypoints. Starting navigation.')
            return f'Route planned to {name}. I am moving there in the simulator.'

    def action(self, name, **kwargs):
        with self.lock:
            if name=='estop':
                self.safety='EMERGENCY STOP';self.mode='STOPPED';self.manual=None;self.target=None;self.path=[]
                self._log('SAFETY','EMERGENCY STOP: motors disabled. Manual reset required.')
                return 'Emergency stop activated. Simulated motors are disabled.'
            if name=='reset_estop':
                self.safety='READY';self.mode='IDLE';self.manual=None
                self._log('SAFETY','Emergency stop reset. Robot remains stationary.')
                return 'Safety stop released. Robot is stationary and ready.'
            if name=='stop':
                self.mode='IDLE';self.manual=None;self.target=None;self.path=[]
                self._log('CONTROL','Stop command received. Robot stationary.')
                return 'Stopped. Awaiting instructions.'
            if name=='reset_world':
                self.pose=Pose();self.obstacles=[dict(x) for x in DEFAULT_OBSTACLES]
                self.mode='IDLE';self.manual=None;self.target=None;self.path=[];self.safety='READY';self.distance_travelled=0
                self._log('SYSTEM','World reset. Default obstacles restored.')
                return 'Simulation reset to its starting position.'
            if name=='clear_obstacles':
                self.obstacles=[]
                if self.mode=='NAVIGATING' and self.target:self.path=self._astar(self.target)
                self._log('WORLD','All obstacles removed.')
                return 'The test arena is now clear.'
            if name=='add_obstacle':
                x=float(kwargs.get('x',0));y=float(kwargs.get('y',0));w=72;h=52
                x=clamp(x-w/2,12,W-w-12);y=clamp(y-h/2,12,H-h-12)
                new={'id':f'box-{int(time.monotonic()*1000)}','x':round(x),'y':round(y),'w':w,'h':h}
                if point_to_rect_distance(self.pose.x,self.pose.y,new)<ROBOT_R+15:
                    return 'Too close to the robot. Place the obstacle farther away.'
                self.obstacles.append(new)
                if self.mode=='NAVIGATING' and self.target:
                    self.path=self._astar(self.target)
                    if not self.path:self.mode='BLOCKED';self._log('SAFETY','Obstacle appeared; route unavailable. Holding.')
                    else:self._log('PLAN','Obstacle added; recalculated route.')
                else:self._log('WORLD','Obstacle placed in the test arena.')
                return 'Obstacle placed. Navigation replanned if needed.'
            if name=='go_to_zone':
                key=str(kwargs.get('zone','')).lower()
                if key not in ZONES:return 'Unknown zone. Choose home, charger, lab or presentation.'
                p=ZONES[key]
                return self.navigate(p['x'],p['y'],p['name'])
            if name=='go_to':
                try:return self.navigate(kwargs['x'],kwargs['y'])
                except (KeyError,ValueError,TypeError):return 'Invalid coordinates.'
            if name in ('forward','backward','left','right'):
                if self.safety!='READY':return 'Safety stop active; movement command rejected.'
                self.mode={'forward':'MANUAL_FORWARD','backward':'MANUAL_BACKWARD','left':'MANUAL_LEFT','right':'MANUAL_RIGHT'}[name]
                self.manual=name;self.manual_until=time.monotonic()+1.0
                self.target=None;self.path=[]
                self._log('CONTROL',f'{name.title()} requested: one-second bounded pulse.')
                return f'{name.title()} for up to one second, with collision protection.'
            return 'Unknown command.'

    def tick(self,dt):
        with self.lock:
            if self.safety!='READY':return
            dt=clamp(dt,0,0.12)
            if self.manual:
                if time.monotonic()>self.manual_until:
                    self.manual=None;self.mode='IDLE';return
                if self.manual in ('left','right'):
                    self.pose.angle=wrap_angle(self.pose.angle+(1 if self.manual=='right' else -1)*math.radians(TURN_SPEED)*dt)
                    return
                angle=self.pose.angle + (math.pi if self.manual=='backward' else 0)
                self._step_move(angle,MAX_SPEED*dt)
                return
            if self.mode!='NAVIGATING':return
            if not self.path:
                self.mode='ARRIVED';self._log('NAV','Destination reached.')
                return
            next_xy=self.path[0]
            if dist((self.pose.x,self.pose.y),next_xy)<12:
                self.path.pop(0)
                if not self.path:
                    self.mode='ARRIVED';self._log('NAV',f'Arrived at {self.target["name"]}.')
                    return
                next_xy=self.path[0]
            target_ang=math.atan2(next_xy[1]-self.pose.y,next_xy[0]-self.pose.x)
            diff=wrap_angle(target_ang-self.pose.angle)
            max_turn=math.radians(TURN_SPEED)*dt
            self.pose.angle=wrap_angle(self.pose.angle+clamp(diff,-max_turn,max_turn))
            if abs(diff)>0.40:return  # align before driving
            forward_clearance=self._ray(self.pose.angle)
            if forward_clearance<17:
                if time.monotonic()-self.last_replan>0.7:
                    self.last_replan=time.monotonic()
                    self.path=self._astar(self.target)
                    self._log('SAFETY','Forward obstruction. Paused and replanned.')
                    if not self.path:
                        self.mode='BLOCKED';self._log('SAFETY','No safe route available; stopping.')
                return
            self._step_move(self.pose.angle,min(MAX_SPEED*dt,dist((self.pose.x,self.pose.y),next_xy)))

    def _step_move(self,angle,distance):
        # Refuse moves whose swept path would intersect inflated obstacles.
        steps=max(1,int(math.ceil(abs(distance)/3)))
        for i in range(steps):
            x=self.pose.x+distance/steps*math.cos(angle)
            y=self.pose.y+distance/steps*math.sin(angle)
            if self._collides(x,y,pad=4):
                self.mode='BLOCKED';self.manual=None
                self._log('SAFETY','Collision envelope triggered. Movement stopped.')
                return False
            self.pose.x=x;self.pose.y=y;self.distance_travelled+=abs(distance/steps)
        return True

    def chat(self, text):
        s=text.strip()[:700]
        if not s:return 'Say something and I will respond.'
        low=s.lower()
        with self.lock:self.memory.append(('user',s))
        # Commands processed BEFORE optional LLM, so model outputs cannot operate motors.
        commands=[(r'^(release|reset) (the )?(emergency( stop)?|e-?stop|safety( stop)?)[.! ]*$',lambda:self.action('reset_estop')),
                  (r'\b(emergency stop|e-?stop|kill motors)\b',lambda:self.action('estop')),
                  (r'^(stop|halt|freeze|stop moving|stay still)[.! ]*$',lambda:self.action('stop')),
                  (r'\b(reset simulation|reset world)\b',lambda:self.action('reset_world')),
                  (r'\b(clear obstacles|remove obstacles)\b',lambda:self.action('clear_obstacles')),
                  (r'^(go|navigate|move|drive|travel|head)\s+to\s+(the\s+)?(home|charger|charging point|charging station|lab|innovation lab|presentation|presentation zone|home base)\b',self._chat_zone(low)),
                  (r'^(move |drive |go )?(forward|backward|back|left|right)\b',self._chat_direction(low))]
        for pattern, handler in commands:
            if re.search(pattern,low):
                response=handler()
                with self.lock:self.memory.append(('assistant',response))
                return response
        with self.lock:
            snap=self._snapshot()
        if any(t in low for t in ('what do you see','what can you see','look around','obstacle','distance sensor')):
            se=snap['sensors']
            ans=(f'In my simulated arena, I detect {len(snap["obstacles"])} mapped obstacles. '
                 f'Range readings: front {se["front"]}, left {se["left"]}, right {se["right"]} virtual cm. '
                 'This is simulated sensing, not a live camera feed.')
        elif any(t in low for t in ('status','how are you','where are you','position','what are you doing')):
            ans=f"Mode: {snap['mode']}. Safety: {snap['safety']}. Position ({snap['pose']['x']}, {snap['pose']['y']}) in virtual units. {snap['mind']}"
        elif any(t in low for t in ('your name','who made','who built','who created','who are you')):
            ans='I am the prototype robot mind of Team Prometheus, created by KITTY CORP. Currently running on a laptop in simulation — my wheels are entirely imaginary, but my safety checks are real code.'
        elif any(t in low for t in ('what can you do','capabilities','help','commands')):
            ans='I can navigate to Home, Charger, Lab or Presentation, accept one-second movement pulses, avoid mapped obstacles, simulate distance sensing, and explain my decisions. Try “go to the lab”, “what do you see?”, or click a map destination.'
        elif any(t in low for t in ('joke','funny','roast')):
            ans='I asked for artificial intelligence and they gave me a charging cable. At least my career has direction — unlike my first path-planning attempt.'
        elif any(t in low for t in ('hello','hi ','hey','good morning','good evening','namaste')):
            ans='Hello! Team Prometheus reporting. Sensors simulated, enthusiasm genuine. What shall we test?'
        elif os.getenv('ROBOT_LLM_KEY','').strip() or os.getenv('ROBOT_LLM_PROVIDER','').lower()=='ollama':
            ans=self._llm_reply(s,snap)
        else:
            ans=('My offline brain handles commands, sensor status and a few conversations. '
                 'For open-ended intelligent chatting, add ROBOT_LLM_KEY on the laptop server. '
                 'Try “go to the lab” or “what do you see?” for now.')
        with self.lock:self.memory.append(('assistant',ans))
        return ans

    def _chat_zone(self,low):
        def run():
            key=next((k for k, words in [('home',['home','home base']),('charger',['charger','charging point','charging station']),('lab',['lab','innovation lab']),('presentation',['presentation','presentation zone'])] if any(w in low for w in words)),None)
            return self.action('go_to_zone',zone=key)
        return run

    def _chat_direction(self,low):
        def run():
            m=re.search(r'\b(forward|backward|back|left|right)\b',low)
            cmd=m.group(1) if m else 'forward'
            return self.action('backward' if cmd=='back' else cmd)
        return run

    def _llm_reply(self,utterance,snap):
        instructions=(
          'You are the voice/personality of Team Prometheus\' robot prototype, made by KITTY CORP. '
          'Warm, sharp, lightly witty, natural; speak in 1-3 short sentences, no generic robotic filler. '
          'You are in a laptop-only simulation. Never claim actual visual perception, microphone input, real-world navigation, '
          'physical actuator movement, autonomous real-world actions, or uninstalled capabilities. '
          'IMPORTANT: you cannot directly command the robot. Do not invent confirmations that actions happened. '
          'Only the separate validated command controller operates simulated motors. '
          f'Current simulator state: mode={snap["mode"]}, safety={snap["safety"]}, '
          f'front_sensor_virtual={snap["sensors"]["front"]}, x={snap["pose"]["x"]}, y={snap["pose"]["y"]}. '
          'For movement ask the user to say commands such as go to lab or stop.'
        )
        messages=[{'role':role,'content':msg} for role,msg in list(self.memory)[-8:]]
        payload={'model':os.getenv('ROBOT_LLM_MODEL','gpt-4.1-mini'),
                 'instructions':instructions,'input':messages,'max_output_tokens':150,'store':False}
        use_ollama=os.getenv('ROBOT_LLM_PROVIDER','').lower()=='ollama'
        if use_ollama:
            # Ollama is optional and must be started by the user separately.
            data={'model':os.getenv('ROBOT_OLLAMA_MODEL','qwen2.5:1.5b'),
                  'messages':[{'role':'system','content':instructions}]+messages,
                  'stream':False,'options':{'num_predict':160}}
            url='http://127.0.0.1:11434/api/chat'
            headers={'Content-Type':'application/json'}
        else:
            data=payload
            url='https://api.openai.com/v1/responses'
            headers={'Authorization':'Bearer '+os.environ['ROBOT_LLM_KEY'], 'Content-Type':'application/json'}
        req=urllib.request.Request(url,data=json.dumps(data).encode(),headers=headers,method='POST')
        try:
            with urllib.request.urlopen(req,timeout=45 if use_ollama else 18) as resp: obj=json.load(resp)
            if use_ollama:
                return obj.get('message',{}).get('content','').strip() or 'No text response returned.'
            chunks=[]
            for item in obj.get('output',[]):
                if item.get('type')=='message':
                    for piece in item.get('content',[]):
                        if piece.get('type')=='output_text':chunks.append(piece.get('text',''))
            return ' '.join(chunks).strip() or 'No text response returned. Try again.'
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,OSError,ValueError) as e:
            return f'AI model is unavailable ({type(e).__name__}). Offline movement and safety features still work.'


def simulation_loop(brain):
    previous=time.monotonic()
    while brain.alive:
        now=time.monotonic()
        brain.tick(now-previous)
        previous=now
        time.sleep(.05)
