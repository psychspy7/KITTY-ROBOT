'use strict';
const $=id=>document.getElementById(id);
const canvas=$('arena'),ctx=canvas.getContext('2d');
const W=900,H=550;
let state=null,tool='target',busy=false,lastEvents='',failed=0,recognition=null;
const colors={bg:'#09131e',grid:'#1b2e43',obs:'#526479',edge:'#6f8ca9',target:'#58e5b1',blue:'#5aaaff'};
function rounded(x,y,w,h,r){ctx.beginPath();ctx.roundRect(x,y,w,h,r)}
function line(x,y,a,b,color,width=1,dash=[]){ctx.beginPath();ctx.setLineDash(dash);ctx.moveTo(x,y);ctx.lineTo(a,b);ctx.strokeStyle=color;ctx.lineWidth=width;ctx.stroke();ctx.setLineDash([])}
function drawArena(){
 ctx.fillStyle=colors.bg;ctx.fillRect(0,0,W,H);
 for(let x=0;x<W;x+=30)line(x,0,x,H,colors.grid,.6);
 for(let y=0;y<H;y+=30)line(0,y,W,y,colors.grid,.6);
 ctx.fillStyle='#56718c';ctx.font='11px monospace';ctx.fillText('VIRTUAL LAB // SENSOR SIMULATION',16,20);
 if(!state){ctx.fillStyle='#91abc3';ctx.font='20px sans-serif';ctx.fillText('Connecting to robot mind...',290,255);return}
 for(const [id,z] of Object.entries(state.zones)){
   ctx.beginPath();ctx.arc(z.x,z.y,15,0,Math.PI*2);ctx.strokeStyle='#294e4e';ctx.lineWidth=1.5;ctx.stroke();
   ctx.beginPath();ctx.arc(z.x,z.y,4,0,Math.PI*2);ctx.fillStyle='#3b9d8b';ctx.fill();
   ctx.fillStyle='#8cb9bb';ctx.font='11px sans-serif';ctx.fillText(z.name,z.x+17,z.y+4);
 }
 for(const o of state.obstacles){
   ctx.fillStyle='#283647';rounded(o.x,o.y,o.w,o.h,6);ctx.fill();
   ctx.strokeStyle='#607186';ctx.lineWidth=1.8;ctx.stroke();
   for(let i=6;i<o.w+o.h;i+=13){ctx.beginPath();ctx.moveTo(Math.max(o.x+3,o.x+i-o.h),Math.max(o.y+3,o.y+o.h-i));ctx.lineTo(Math.min(o.x+o.w-3,o.x+i),Math.min(o.y+o.h-3,o.y+i));ctx.strokeStyle='#344459';ctx.lineWidth=.5;ctx.stroke()}
   ctx.fillStyle='#a2b3c7';ctx.font='10px monospace';ctx.fillText('OBSTACLE',o.x+7,o.y+18);
 }
 if(state.path.length){
  ctx.beginPath();ctx.moveTo(state.pose.x,state.pose.y);
  state.path.forEach(p=>ctx.lineTo(p.x,p.y));
  ctx.strokeStyle='#65a8fe';ctx.setLineDash([6,5]);ctx.lineWidth=3;ctx.stroke();ctx.setLineDash([]);
 }
 if(state.target){
  let t=state.target;
  ctx.beginPath();ctx.arc(t.x,t.y,13,0,Math.PI*2);ctx.strokeStyle=colors.target;ctx.lineWidth=2;ctx.stroke();
  line(t.x-20,t.y,t.x+20,t.y,colors.target,1);line(t.x,t.y-20,t.x,t.y+20,colors.target,1);
  ctx.fillStyle='#72dcbf';ctx.font='bold 11px sans-serif';ctx.fillText(t.name,t.x+20,t.y-10);
 }
 const p=state.pose,a=p.angle;
 // range fan is schematic only, not actual camera vision.
 ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.arc(p.x,p.y,125,a-.6,a+.6);ctx.closePath();ctx.fillStyle='#3b93f015';ctx.fill();ctx.strokeStyle='#427bb73f';ctx.stroke();
 for(const delta of [-.698,0,.698]){
   let read=delta<0?state.sensors.left:delta>0?state.sensors.right:state.sensors.front;
   line(p.x,p.y,p.x+(20+read)*Math.cos(a+delta),p.y+(20+read)*Math.sin(a+delta),'#3a93c899',1,[3,6]);
 }
 ctx.save();ctx.translate(p.x,p.y);ctx.rotate(a);
 ctx.shadowColor='#4ea7ff';ctx.shadowBlur=19;ctx.beginPath();ctx.arc(0,0,20,0,Math.PI*2);ctx.fillStyle='#162f4c';ctx.fill();ctx.shadowBlur=0;
 ctx.strokeStyle=state.safety==='READY'?'#8ec5ff':'#fa6579';ctx.lineWidth=4;ctx.stroke();
 ctx.fillStyle='#bde6ff';ctx.beginPath();ctx.moveTo(25,0);ctx.lineTo(3,-9);ctx.lineTo(3,9);ctx.closePath();ctx.fill();
 ctx.fillStyle='#89bfff';rounded(-12,-13,24,26,5);ctx.fill();ctx.fillStyle='#173356';rounded(-8,-9,16,18,3);ctx.fill();ctx.restore();
 ctx.fillStyle='#a7c6e5';ctx.font='bold 11px sans-serif';ctx.fillText('PROMETHEUS',p.x-31,p.y-32);
 ctx.fillStyle='#526c87';ctx.font='10px monospace';ctx.fillText('X: '+Math.round(p.x)+'  Y: '+Math.round(p.y),W-170,H-15);
}
function safeText(t){return String(t??'')}
function updateUI(s){
 state=s;drawArena();$('modeChip').textContent=s.mode;$('statMode').textContent=s.mode;$('statSafety').textContent=s.safety;
 $('statSafety').style.color=s.safety==='READY'?'#7de9c6':'#ff7d8a';$('statSpeed').innerHTML=String(s.speed)+' <span>u/s</span>';
 $('statDistance').innerHTML=String(s.distance_travelled)+' <span>m*</span>';
 for(const side of ['Front','Left','Right']){let d=s.sensors[side.toLowerCase()];$('sense'+side).textContent=d+' cm';$('bar'+side).style.width=Math.max(0,Math.min(100,d/180*100))+'%';$('bar'+side).style.background=d<26?'#ff6d7e':'linear-gradient(90deg,#3a72ed,#67cfff)'}
 $('mindNote').textContent=s.mind;$('facestate').textContent=s.mode;$('aiState').textContent=s.ai_connected?'MODEL CONFIGURED':'OFFLINE BRAIN';
 $('uptime').textContent=String(Math.floor(s.uptime/60)).padStart(2,'0')+':'+String(s.uptime%60).padStart(2,'0');
 const events=JSON.stringify(s.events);if(events!==lastEvents){lastEvents=events;const container=$('events');container.replaceChildren();s.events.slice().reverse().forEach(e=>{const div=document.createElement('div');div.className='event';const tm=document.createElement('time');tm.textContent=e.time;const kind=document.createElement('b');kind.textContent=e.kind;const content=document.createElement('span');content.textContent=e.text;div.append(tm,kind,content);container.appendChild(div)})}
}
async function poll(){try{let r=await fetch('/api/state',{cache:'no-store'});if(!r.ok)throw Error('Server offline');updateUI(await r.json());$('connLabel').textContent='CONNECTED';failed=0}catch(e){if(++failed===2)$('connLabel').textContent='DISCONNECTED'}finally{setTimeout(poll,150)}}
async function action(action,extra={}){try{let r=await fetch('/api/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action,...extra})});let obj=await r.json();if(obj.state)updateUI(obj.state);if(obj.error)return obj.error;return obj.reply}catch(e){return 'Server is unreachable. Launch main.py on the laptop.'}}
function setTool(t){tool=t;for(const name of ['Target','Obstacle','Select'])$('tool'+name).classList.toggle('active',name.toLowerCase()===t);$('mapHelper').textContent={target:'Click inside the arena to set a destination. The path planner will calculate a route.',obstacle:'Click inside the arena to introduce a new obstacle. Routes will update automatically.',select:'Inspect mode: the next click displays its virtual position.'}[tool]}
$('toolTarget').onclick=()=>setTool('target');$('toolObstacle').onclick=()=>setTool('obstacle');$('toolSelect').onclick=()=>setTool('select');
canvas.addEventListener('click',async e=>{const box=canvas.getBoundingClientRect();const x=(e.clientX-box.left)*W/box.width;const y=(e.clientY-box.top)*H/box.height;if(tool==='target'){let reply=await action('go_to',{x,y});if(reply.includes('cannot')||reply.includes('inside')||reply.includes('Emergency'))addBubble('bot',reply)}else if(tool==='obstacle'){let reply=await action('add_obstacle',{x,y});if(reply.startsWith('Too close'))addBubble('bot',reply)}else $('mapHelper').textContent=`Position: (${x.toFixed(0)}, ${y.toFixed(0)}) virtual coordinates.`});
$('goBtn').onclick=async()=>{const r=await action('go_to_zone',{zone:$('zones').value});addBubble('bot',r)};
for(const b of document.querySelectorAll('[data-direction]'))b.onclick=async()=>action(b.dataset.direction);
$('stopBtn').onclick=async()=>{let r=await action('stop');addBubble('bot',r)};
$('estopBtn').onclick=async()=>{let r=await action('estop');addBubble('bot',r)};
$('releaseBtn').onclick=async()=>{let r=await action('reset_estop');addBubble('bot',r)};
$('resetBtn').onclick=async()=>action('reset_world');$('clearBtn').onclick=async()=>action('clear_obstacles');
document.addEventListener('keydown',e=>{let tag=document.activeElement?.tagName;if(e.ctrlKey||e.altKey||e.metaKey||['INPUT','TEXTAREA','SELECT'].includes(tag))return;let commands={KeyW:'forward',ArrowUp:'forward',KeyS:'backward',ArrowDown:'backward',KeyA:'left',ArrowLeft:'left',KeyD:'right',ArrowRight:'right',Space:'stop'};if(commands[e.code]&&!e.repeat){e.preventDefault();action(commands[e.code])}});
function addBubble(role,text){const node=document.createElement('div');node.className='bubble '+role;if(role==='bot'){let s=document.createElement('span');s.className='speaker';s.textContent='PROMETHEUS MIND';node.appendChild(s)}node.appendChild(document.createTextNode(safeText(text)));$('chatLog').appendChild(node);$('chatLog').scrollTop=$('chatLog').scrollHeight;return node}
function speak(text){if(!$('speakCheck').checked||!('speechSynthesis' in window))return;try{speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(text);u.rate=1.05;u.pitch=.95;speechSynthesis.speak(u)}catch{}}
async function say(text){if(!text.trim()||busy)return;busy=true;$('chatSubmit').disabled=true;addBubble('user',text);$('chatInput').value='';let placeholder=addBubble('bot','Thinking...');try{let r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})});let o=await r.json();placeholder.lastChild.textContent=o.reply||o.error||'Something went wrong';speak(o.reply||'');if(o.state)updateUI(o.state)}catch(e){placeholder.lastChild.textContent='Local server unavailable. Start the Python application.'}finally{busy=false;$('chatSubmit').disabled=false;$('chatLog').scrollTop=$('chatLog').scrollHeight}}
$('chatForm').addEventListener('submit',e=>{e.preventDefault();say($('chatInput').value)});
for(const b of document.querySelectorAll('.suggestion'))b.onclick=()=>say(b.textContent);
$('micBtn').onclick=()=>{const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SpeechRecognition){addBubble('bot','Voice recognition is not supported in this browser. You can type commands instead.');return}if(recognition){recognition.stop();return}recognition=new SpeechRecognition();recognition.lang='en-IN';recognition.interimResults=false;recognition.maxAlternatives=1;$('micBtn').classList.add('active');recognition.onresult=e=>{const txt=e.results[0][0].transcript;say(txt)};recognition.onerror=e=>addBubble('bot','Microphone recognition error: '+e.error+'. Try typed commands.');recognition.onend=()=>{$('micBtn').classList.remove('active');recognition=null};recognition.start()};
drawArena();poll();
