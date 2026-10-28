/* Supported-command SOFTWARE demo. No physical I/O, speech model or device control. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory(require('./core.js'));else root.KittyCommandDemo=factory(root.Prometheus);})(typeof globalThis!=='undefined'?globalThis:this,function(P){
'use strict';
class CompanionDemo{
 constructor(){this.world={obstacles:[{x:5,y:0,w:1,h:4.6},{x:8,y:5.8,w:1.5,h:1.2}]};this.reset();}
 reset(){this.pose={x:1.5,y:3.5,theta:0,leftAngle:0,rightAngle:0};this.time=0;this.phase='IDLE';this.path=[];this.wp=1;this.goal=null;this.events=[];this.trace=[];this.alertAt=null;this.beep=false;this.left=this.right=0;this.distance=0;this.collisions=0;this.record();}
 event(type,detail){this.events.push({t:this.time,type,detail});}
 submit(text){const command=String(text).toLowerCase().replace(/[^a-z\s]/g,'').trim().replace(/^kitty\s*/,'');
  if(command==='stop'){this.phase='STOPPED';this.left=this.right=0;this.event('command_stop','Local supported STOP intent');return true;}
  if(!/^(?:check|scan) (?:the )?room$/.test(command))return false;
  this.goal={x:10.2,y:3.5};this.path=[{x:this.pose.x,y:this.pose.y},this.goal];this.wp=1;this.phase='SCAN';this.event('command_accepted',{command:text,intent:'CHECK_ROOM',goal_source:'internal fixture for supported task; no user-selected destination'});return true;
 }
 step(dt=1/60){const sensors=P.sense(this.world,this.pose);let left=0,right=0;
  if(this.phase==='SCAN'&&this.time>=.7)this.phase='FOLLOW_COMMAND';
  if(this.phase==='FOLLOW_COMMAND'&&(sensors.front<.70||sensors.ir)){this.phase='OBSTACLE_WARNING';this.alertAt=this.time;this.event('obstacle_detected',sensors.front);this.event('buzzer_warning','Virtual buzzer precedes detour');}
  if(this.phase==='OBSTACLE_WARNING'&&this.time-this.alertAt>=.55){this.path=P.astar(this.world,this.pose,this.goal);this.wp=1;this.phase=this.path.length?'DETOUR':'NO_ROUTE';this.event('detour_planned',{nodes:this.path.length,map:'supplied obstacle geometry for this software test, not SLAM'});}
  if(['FOLLOW_COMMAND','DETOUR'].includes(this.phase)){
   while(this.wp<this.path.length&&Math.hypot(this.path[this.wp].x-this.pose.x,this.path[this.wp].y-this.pose.y)<.09)this.wp++;
   if(this.wp>=this.path.length){this.phase='TASK_COMPLETE';this.event('task_complete','Supported CHECK_ROOM route finished');}
   else{const q=this.path[this.wp],error=P.wrap(Math.atan2(q.y-this.pose.y,q.x-this.pose.x)-this.pose.theta);if(Math.abs(error)>.10){const w=Math.max(-1.7,Math.min(1.7,error*3.5));left=-w*P.C.wheelBase/2;right=w*P.C.wheelBase/2;}else{const w=Math.max(-.4,Math.min(.4,error*2));left=.5-w*P.C.wheelBase/2;right=.5+w*P.C.wheelBase/2;}}
  }
  const safe=P.safety(sensors,left,right);this.left=safe.left;this.right=safe.right;const next=P.integrate(this.pose,this.left,this.right,dt);
  if(P.intersects(this.world,next.x,next.y)){this.collisions++;this.left=this.right=0;this.phase='COLLISION_GUARD';}else{this.distance+=Math.hypot(next.x-this.pose.x,next.y-this.pose.y);this.pose=next;}
  this.beep=this.alertAt!==null&&this.time-this.alertAt<.55&&Math.floor((this.time-this.alertAt)*9)%2===0;
  this.time+=dt;return this.snapshot();
 }
 snapshot(){const s=P.sense(this.world,this.pose);return{t:this.time,x:this.pose.x,y:this.pose.y,theta:this.pose.theta,leftAngle:this.pose.leftAngle,rightAngle:this.pose.rightAngle,left:this.left,right:this.right,front:s.front,rear:s.rear,ir:s.ir,beep:this.beep,state:Math.abs(this.left+this.right)>.00001?'FORWARD':Math.abs(this.left-this.right)>.00001?'TURN':'STOP',reason:this.phase};}
 record(){this.trace.push(this.snapshot());}
 export(){return{id:'command',config:{goal:this.goal,obstacles:this.world.obstacles},trace:this.trace,path:this.path,events:this.events,metrics:{distance:this.distance,collisions:this.collisions,taskComplete:this.phase==='TASK_COMPLETE'},command:'KITTY, check the room'};}
}
return{CompanionDemo};
});

