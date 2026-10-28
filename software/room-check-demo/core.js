/* PROMETHEUS: deterministic SI-unit differential-drive simulator.
   Environment geometry is private to physics + sensing. A* receives an explicitly
   supplied prior map. The local safety controller receives only sampled sensors. */
(function(root,factory){if(typeof module==='object')module.exports=factory();else root.Prometheus=factory();})(typeof globalThis!=='undefined'?globalThis:this,function(){
'use strict';
const C={dt:1/60,width:12,height:7,radius:0.24,wheelBase:0.36,wheelRadius:0.07,maxWheel:0.68,range:4,sensorOffset:0.21,stopDistance:0.36,irRange:0.55,cell:0.25,plannerInflation:0.44};
const wrap=a=>Math.atan2(Math.sin(a),Math.cos(a));
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
function rayRect(x,y,dx,dy,r){let lo=0,hi=C.range;for(const [p,d,min,max] of [[x,dx,r.x,r.x+r.w],[y,dy,r.y,r.y+r.h]]){if(Math.abs(d)<1e-10){if(p<min||p>max)return Infinity;}else{let a=(min-p)/d,b=(max-p)/d;if(a>b)[a,b]=[b,a];lo=Math.max(lo,a);hi=Math.min(hi,b);if(hi<lo)return Infinity;}}return lo;}
function raycast(world,x,y,a,max=C.range){const dx=Math.cos(a),dy=Math.sin(a);let best=max;for(const r of world.obstacles)best=Math.min(best,rayRect(x,y,dx,dy,r));for(const [p,d,edge] of [[x,dx,0],[x,dx,C.width],[y,dy,0],[y,dy,C.height]]){if(Math.abs(d)>1e-10){const t=(edge-p)/d;if(t>=0)best=Math.min(best,t);}}return best;}
function sense(world,p){const fan=(a)=>{let best=C.range;const ox=p.x+Math.cos(a)*C.sensorOffset,oy=p.y+Math.sin(a)*C.sensorOffset;for(const delta of [-6,-3,0,3,6])best=Math.min(best,raycast(world,ox,oy,a+delta*Math.PI/180));return best;};let ir=C.irRange;const ox=p.x+Math.cos(p.theta)*C.sensorOffset,oy=p.y+Math.sin(p.theta)*C.sensorOffset;for(let d=-20;d<=20;d+=5)ir=Math.min(ir,raycast(world,ox,oy,p.theta+d*Math.PI/180,C.irRange));return{front:fan(p.theta),rear:fan(p.theta+Math.PI),ir:ir<0.34,irDistance:ir,valid:true};}
function intersects(world,x,y,r=C.radius){if(x-r<0||y-r<0||x+r>C.width||y+r>C.height)return true;return world.obstacles.some(o=>{const cx=clamp(x,o.x,o.x+o.w),cy=clamp(y,o.y,o.y+o.h);return Math.hypot(cx-x,cy-y)<r;});}
function integrate(p,left,right,dt=C.dt){const v=(left+right)/2,w=(right-left)/C.wheelBase;let x,y;if(Math.abs(w)<1e-10){x=p.x+v*Math.cos(p.theta)*dt;y=p.y+v*Math.sin(p.theta)*dt;}else{x=p.x+v/w*(Math.sin(p.theta+w*dt)-Math.sin(p.theta));y=p.y-v/w*(Math.cos(p.theta+w*dt)-Math.cos(p.theta));}return{x,y,theta:wrap(p.theta+w*dt),leftAngle:(p.leftAngle||0)+left/C.wheelRadius*dt,rightAngle:(p.rightAngle||0)+right/C.wheelRadius*dt};}
function astar(prior,start,goal){const nx=Math.round(C.width/C.cell),ny=Math.round(C.height/C.cell);const cell=p=>[clamp(Math.floor(p.x/C.cell),0,nx-1),clamp(Math.floor(p.y/C.cell),0,ny-1)];const point=([x,y])=>({x:(x+.5)*C.cell,y:(y+.5)*C.cell});const blocked=([x,y])=>{const p=point([x,y]);return intersects(prior,p.x,p.y,C.plannerInflation);};const s=cell(start),g=cell(goal),key=p=>p.join(',');if(blocked(s)||blocked(g))return[];const open=[s],came=new Map(),cost=new Map([[key(s),0]]),closed=new Set();const h=p=>Math.abs(p[0]-g[0])+Math.abs(p[1]-g[1]);while(open.length){open.sort((a,b)=>(cost.get(key(a))+h(a))-(cost.get(key(b))+h(b)));const cur=open.shift(),k=key(cur);if(closed.has(k))continue;if(k===key(g)){const route=[cur];let z=k;while(came.has(z)){const n=came.get(z);route.unshift(n);z=key(n);}return [start,...route.slice(1).map(point),goal];}closed.add(k);for(const [dx,dy]of [[1,0],[0,1],[-1,0],[0,-1]]){const n=[cur[0]+dx,cur[1]+dy],nk=key(n);if(n[0]<0||n[1]<0||n[0]>=nx||n[1]>=ny||blocked(n)||closed.has(nk))continue;const ng=cost.get(k)+1;if(ng<(cost.get(nk)??Infinity)){cost.set(nk,ng);came.set(nk,cur);open.push(n);}}}return[];}
function safety(s,left,right,estop=false){if(estop)return{left:0,right:0,reason:'EMERGENCY STOP'};if(!s.valid||![s.front,s.rear,left,right].every(Number.isFinite)||Math.abs(left)>C.maxWheel||Math.abs(right)>C.maxWheel)return{left:0,right:0,reason:'INVALID INPUT'};const v=(left+right)/2;if(v>0&&(s.front<C.stopDistance||s.ir))return{left:0,right:0,reason:'FRONT BLOCKED'};if(v<0&&s.rear<C.stopDistance)return{left:0,right:0,reason:'REAR BLOCKED'};return{left,right,reason:null};}
const scenarios={
 clear:{name:'Clear path',kind:'navigate',start:{x:1.5,y:3.5,theta:0},goal:{x:9.5,y:3.5},obstacles:[],seconds:20},
 front:{name:'Front obstacle',kind:'avoid',start:{x:1.5,y:3.5,theta:0},goal:{x:10,y:3.5},obstacles:[{x:4.3,y:2.3,w:.65,h:2.4}],seconds:10},
 rear:{name:'Rear obstacle',kind:'reverse',start:{x:4.5,y:3.5,theta:0},goal:null,obstacles:[{x:3.65,y:2.8,w:.5,h:1.4}],seconds:5},
 blocked:{name:'Blocked route',kind:'navigate',start:{x:1.5,y:3.5,theta:0},goal:{x:10.2,y:3.5},obstacles:[{x:5,y:0,w:1,h:4.6},{x:8,y:5.8,w:1.5,h:1.2}],seconds:45},
 turn:{name:'180 degree turn',kind:'turn',start:{x:6,y:3.5,theta:0},goal:null,obstacles:[],seconds:6},
 reverse:{name:'Clear reverse',kind:'reverse',start:{x:7,y:3.5,theta:0},goal:null,obstacles:[],seconds:5},
 sealed:{name:'No available route',kind:'navigate',start:{x:1.5,y:3.5,theta:0},goal:{x:10,y:3.5},obstacles:[{x:5,y:0,w:1,h:7}],seconds:3}
};
class Simulation{
 constructor(id='clear',custom=null){this.id=id;this.config=JSON.parse(JSON.stringify(custom||scenarios[id]));this.world={obstacles:this.config.obstacles};this.prior=JSON.parse(JSON.stringify(this.world));this.pose={...this.config.start,leftAngle:0,rightAngle:0};this.t=0;this.steps=0;this.state='STOP';this.reason='READY';this.estop=false;this.paused=false;this.path=this.config.goal?astar(this.prior,this.pose,this.config.goal):[];this.wp=1;this.targetTheta=null;this.turnComplete=false;this.avoidPhase='drive';this.stopUntil=0;this.collisions=0;this.safetyStops=0;this.distance=0;this.trace=[];this.events=[];this.left=0;this.right=0;this.sensors=sense(this.world,this.pose);this.record();}
 event(type,detail){this.events.push({t:+this.t.toFixed(3),type,detail});}
 command(){const p=this.pose,s=this.sensors,c=this.config;let left=0,right=0,reason='';const turnTo=theta=>{const e=wrap(theta-p.theta);if(Math.abs(e)<0.003){this.turnComplete=true;return[0,0];}const w=clamp(3.2*e,-1.65,1.65);return[-w*C.wheelBase/2,w*C.wheelBase/2];};
 if(c.kind==='turn'){if(this.targetTheta===null)this.targetTheta=wrap(c.start.theta+Math.PI);[left,right]=turnTo(this.targetTheta);reason=this.turnComplete?'TURN COMPLETE':'TURN 180';}
 else if(c.kind==='reverse'){left=right=-0.42;reason='REVERSE REQUEST';}
 else if(c.kind==='avoid'){
 if(this.avoidPhase==='drive'){left=right=.58;reason='FORWARD';if(s.front<C.stopDistance||s.ir){this.avoidPhase='hold';this.stopUntil=this.t+.35;this.event('front_detected',s.front);}}
 if(this.avoidPhase==='hold'){left=right=0;reason='FRONT DETECTED';if(this.t>=this.stopUntil){this.avoidPhase='turn';this.targetTheta=wrap(p.theta+Math.PI);this.event('turn_started',this.targetTheta);}}
 if(this.avoidPhase==='turn'){[left,right]=turnTo(this.targetTheta);reason='AVOIDANCE TURN';if(this.turnComplete){this.avoidPhase='retreat';this.event('turn_complete',p.theta);}}
 if(this.avoidPhase==='retreat'){left=right=.42;reason='CLEAR DIRECTION';}
 }else if(c.kind==='navigate'){
 if(!this.path.length)reason='NO ROUTE';
 else{while(this.wp<this.path.length&&Math.hypot(this.path[this.wp].x-p.x,this.path[this.wp].y-p.y)<.09)this.wp++;if(this.wp>=this.path.length)reason='GOAL REACHED';else{const q=this.path[this.wp],e=wrap(Math.atan2(q.y-p.y,q.x-p.x)-p.theta);if(Math.abs(e)>.10){const w=clamp(e*3.5,-1.8,1.8);left=-w*C.wheelBase/2;right=w*C.wheelBase/2;reason='ALIGN TO ROUTE';}else{const v=.56,w=clamp(e*2,-.4,.4);left=v-w*C.wheelBase/2;right=v+w*C.wheelBase/2;reason='FOLLOW A*';}}}
 }
 return{left,right,reason};}
 step(dt=C.dt){if(this.paused)return this.snapshot();this.sensors=sense(this.world,this.pose);const request=this.command(),safe=safety(this.sensors,request.left,request.right,this.estop);this.left=safe.left;this.right=safe.right;const next=integrate(this.pose,this.left,this.right,dt);if(intersects(this.world,next.x,next.y)){this.left=this.right=0;this.collisions++;this.reason='PHYSICS COLLISION';this.event('collision_guard','privileged physics, not controller');}else{this.distance+=Math.hypot(next.x-this.pose.x,next.y-this.pose.y);this.pose=next;this.reason=safe.reason||request.reason;}if(safe.reason){this.safetyStops++;if(this.trace.at(-1)?.reason!==safe.reason)this.event('safety_stop',safe.reason);}const v=(this.left+this.right)/2,w=(this.right-this.left)/C.wheelBase;this.state=Math.abs(v)<1e-5?(Math.abs(w)<1e-5?'STOP':'TURN'):(v>0?'FORWARD':'REVERSE');this.t+=dt;this.steps++;this.sensors=sense(this.world,this.pose);if(this.steps%2===0)this.record();return this.snapshot();}
 snapshot(){return{t:+this.t.toFixed(4),x:this.pose.x,y:this.pose.y,theta:this.pose.theta,leftAngle:this.pose.leftAngle,rightAngle:this.pose.rightAngle,left:this.left,right:this.right,front:this.sensors.front,rear:this.sensors.rear,ir:this.sensors.ir,state:this.state,reason:this.reason,wp:this.wp};}
 record(){this.trace.push(this.snapshot());}
 run(seconds=this.config.seconds){for(let i=0;i<Math.round(seconds/C.dt);i++)this.step();return this;}
 export(){const trace=this.trace.slice();if(trace.at(-1)?.t!==+this.t.toFixed(4))trace.push(this.snapshot());return{id:this.id,config:this.config,constants:C,path:this.path,trace,events:this.events,metrics:{distance:this.distance,collisions:this.collisions,safetyStops:this.safetyStops,duration:this.t,goalReached:this.config.goal?Math.hypot(this.pose.x-this.config.goal.x,this.pose.y-this.config.goal.y)<.15:null,turnError:this.targetTheta===null?null:Math.abs(wrap(this.targetTheta-this.pose.theta))*180/Math.PI}};}
}
return{C,wrap,sense,raycast,rayRect,intersects,integrate,astar,safety,scenarios,Simulation};
});

