from pathlib import Path

p=Path('index.html')
t=p.read_text(encoding='utf-8')


def replace_once(old,new,label):
    global t
    if new in t:
        return
    c=t.count(old)
    if c!=1:
        raise SystemExit(f'{label}: expected 1 anchor, found {c}')
    t=t.replace(old,new,1)

# Shared snapshot-history interpolation. Remote visuals intentionally render a
# fraction behind the host so ordinary Firebase jitter does not become a pause.
anchor="""function applyRemoteGame(game){
 if(!game||Number(game.seq||0)<=NetworkAdapter.lastRemoteSeq)return;"""
insert="""const REMOTE_WAR_RENDER_DELAY_MS=160;
const REMOTE_WAR_MAX_EXTRAP_MS=85;
const REMOTE_WAR_HISTORY_LIMIT=7;

function appendRemotePositionSample(old,x,y,timestamp){
 const history=Array.isArray(old?.netHistory)?old.netHistory.slice(-(REMOTE_WAR_HISTORY_LIMIT-1)):[];
 const nx=Number(x)||0,ny=Number(y)||0,nt=Number(timestamp)||performance.now();
 const last=history[history.length-1];
 if(last&&Math.abs(Number(last.x)-nx)<.001&&Math.abs(Number(last.y)-ny)<.001&&nt-Number(last.t)<18){
   last.t=nt;
 }else history.push({x:nx,y:ny,t:nt});
 return history.slice(-REMOTE_WAR_HISTORY_LIMIT);
}

function sampleRemotePosition(obj,now,allowExtrapolation=false){
 const history=obj?.netHistory;
 if(!Array.isArray(history)||!history.length)return null;
 const renderAt=now-REMOTE_WAR_RENDER_DELAY_MS;
 if(history.length===1)return {x:Number(history[0].x)||0,y:Number(history[0].y)||0};
 const first=history[0];
 if(renderAt<=Number(first.t))return {x:Number(first.x)||0,y:Number(first.y)||0};
 for(let i=0;i<history.length-1;i++){
   const a=history[i],b=history[i+1],at=Number(a.t)||0,bt=Number(b.t)||at+1;
   if(renderAt<=bt){
     const alpha=clamp((renderAt-at)/Math.max(1,bt-at),0,1);
     return {x:(Number(a.x)||0)+((Number(b.x)||0)-(Number(a.x)||0))*alpha,y:(Number(a.y)||0)+((Number(b.y)||0)-(Number(a.y)||0))*alpha};
   }
 }
 const last=history[history.length-1],prev=history[history.length-2];
 if(!allowExtrapolation)return {x:Number(last.x)||0,y:Number(last.y)||0};
 const gap=Math.max(16,(Number(last.t)||0)-(Number(prev.t)||0));
 const extra=Math.min(REMOTE_WAR_MAX_EXTRAP_MS,Math.max(0,renderAt-(Number(last.t)||0)));
 let vx=((Number(last.x)||0)-(Number(prev.x)||0))/(gap/1000);
 let vy=((Number(last.y)||0)-(Number(prev.y)||0))/(gap/1000);
 const maxSpeed=Math.max(120,(Number(obj?.speed)||DRAGON_FIREBALL_SPEED||120)*1.7);
 const speed=Math.hypot(vx,vy);
 if(speed>maxSpeed&&speed>0){const s=maxSpeed/speed;vx*=s;vy*=s}
 return {x:(Number(last.x)||0)+vx*(extra/1000),y:(Number(last.y)||0)+vy*(extra/1000)};
}

function applyRemoteGame(game){
 if(!game||Number(game.seq||0)<=NetworkAdapter.lastRemoteSeq)return;"""
replace_once(anchor,insert,'remote interpolation helpers')

old_entity="""     const toX=Number(e.x)||0,toY=Number(e.y)||0;
     const out={...e,x:fromX,y:fromY,netFromX:fromX,netFromY:fromY,netToX:toX,netToY:toY,netInterpStartedAt:remoteNow,netInterpDuration:remoteInterpMs,target:null,controlled:e.ownerId===NetworkAdapter.localPlayerId};"""
new_entity="""     const toX=Number(e.x)||0,toY=Number(e.y)||0;
     const netHistory=appendRemotePositionSample(old,toX,toY,remoteNow);
     const out={...e,x:fromX,y:fromY,netFromX:fromX,netFromY:fromY,netToX:toX,netToY:toY,netInterpStartedAt:remoteNow,netInterpDuration:remoteInterpMs,netHistory,target:null,controlled:e.ownerId===NetworkAdapter.localPlayerId};"""
replace_once(old_entity,new_entity,'entity history')

old_teleport="""       if(becameTeleported){out.x=Number(e.x);out.y=Number(e.y);out.netFromX=Number(e.x);out.netFromY=Number(e.y);out.netToX=Number(e.x);out.netToY=Number(e.y);out.netInterpStartedAt=remoteNow;out.netInterpDuration=1}"""
new_teleport="""       if(becameTeleported){
         const tx=Number(e.x)||0,ty=Number(e.y)||0;
         out.x=tx;out.y=ty;out.netFromX=tx;out.netFromY=ty;out.netToX=tx;out.netToY=ty;out.netInterpStartedAt=remoteNow;out.netInterpDuration=1;
         out.netHistory=[{x:tx,y:ty,t:remoteNow-1},{x:tx,y:ty,t:remoteNow}];
       }"""
replace_once(old_teleport,new_teleport,'Naja teleport history reset')

old_projectiles=""" if(Array.isArray(game.dragonProjectiles)){
   // Fireballs are visually simulated every frame on clients. The host remains
   // authoritative; each snapshot only corrects their path smoothly.
   const previousProjectiles=new Map((state.dragonProjectiles||[]).map(p=>[p.id,p]));
   state.dragonProjectiles=game.dragonProjectiles.map(p=>{
     const old=previousProjectiles.get(p.id),authX=Number(p.x)||0,authY=Number(p.y)||0;
     return {...p,x:old?.x??authX,y:old?.y??authY,netTargetX:authX,netTargetY:authY};
   });
 }"""
new_projectiles=""" if(Array.isArray(game.dragonProjectiles)){
   // Fireballs use the SAME delayed timeline as remote troops. This keeps a
   // projectile and its target visually in the same moment instead of letting
   // the fireball run ahead of an interpolated unit.
   const previousProjectiles=new Map((state.dragonProjectiles||[]).map(p=>[p.id,p]));
   const incomingIds=new Set();
   const nextProjectiles=game.dragonProjectiles.map(p=>{
     incomingIds.add(p.id);
     const old=previousProjectiles.get(p.id),authX=Number(p.x)||0,authY=Number(p.y)||0;
     const netHistory=appendRemotePositionSample(old,authX,authY,remoteNow);
     return {...p,x:old?.x??authX,y:old?.y??authY,netAuthX:authX,netAuthY:authY,netHistory,netRemovedAt:0};
   });
   // When the host removes a projectile because it hit, keep its VISUAL copy
   // only long enough for the interpolation buffer to reach that same instant.
   // A final sample at the authoritative target position makes the fireball
   // visibly arrive at the unit instead of crossing it and flying away.
   for(const old of previousProjectiles.values()){
     if(incomingIds.has(old.id))continue;
     const removedAt=Number(old.netRemovedAt)||remoteNow;
     if(remoteNow-removedAt>REMOTE_WAR_RENDER_DELAY_MS+REMOTE_WAR_MAX_EXTRAP_MS+40)continue;
     let history=old.netHistory;
     if(!old.netRemovedAt){
       const targetSnapshot=Array.isArray(game.entities)?game.entities.find(e=>e.id===old.targetId):null;
       const finalX=targetSnapshot&&Number.isFinite(Number(targetSnapshot.x))?Number(targetSnapshot.x):(Number(old.netAuthX)||Number(old.x)||0);
       const finalY=targetSnapshot&&Number.isFinite(Number(targetSnapshot.y))?Number(targetSnapshot.y):(Number(old.netAuthY)||Number(old.y)||0);
       history=appendRemotePositionSample(old,finalX,finalY,removedAt);
     }
     nextProjectiles.push({...old,netHistory:history,netRemovedAt:removedAt});
   }
   state.dragonProjectiles=nextProjectiles;
 }"""
replace_once(old_projectiles,new_projectiles,'projectile buffered lifecycle')

old_loop=""" if(NetworkAdapter.online&&!NetworkAdapter.isHost){
   const clientNow=performance.now();
   for(const e of state.entities){
     if(e.netToX==null)continue;
     const duration=Math.max(1,Number(e.netInterpDuration)||120);
     const alpha=clamp((clientNow-(Number(e.netInterpStartedAt)||clientNow))/duration,0,1);
     // Linear on purpose: no overshoot, spring or predicted knockback correction.
     e.x=(Number(e.netFromX)||0)+((Number(e.netToX)||0)-(Number(e.netFromX)||0))*alpha;
     e.y=(Number(e.netFromY)||0)+((Number(e.netToY)||0)-(Number(e.netFromY)||0))*alpha;
   }
   // Projectiles keep moving at render FPS between Firebase updates. The target
   // authority is advanced by the same velocity and the visible projectile converges
   // slowly to it, so a correction never looks like a teleport backwards.
   const projectileStep=Math.min(dt,.034),projectileSmooth=1-Math.exp(-9*dt);
   for(const p of state.dragonProjectiles||[]){
     const vx=Number(p.vx)||0,vy=Number(p.vy)||0;
     p.x=(Number(p.x)||0)+vx*projectileStep;p.y=(Number(p.y)||0)+vy*projectileStep;
     p.netTargetX=(Number(p.netTargetX)||0)+vx*projectileStep;p.netTargetY=(Number(p.netTargetY)||0)+vy*projectileStep;
     const dx=p.netTargetX-p.x,dy=p.netTargetY-p.y;
     if(dx*dx+dy*dy>240*240){p.x=p.netTargetX;p.y=p.netTargetY}
     else{p.x+=dx*projectileSmooth;p.y+=dy*projectileSmooth}
   }
 }"""
new_loop=""" if(NetworkAdapter.online&&!NetworkAdapter.isHost){
   const clientNow=performance.now();
   for(const e of state.entities){
     // Walking units are rendered from a short authoritative history buffer.
     // This is true snapshot interpolation: Firebase arrival jitter no longer
     // restarts a tween or creates a tiny stop on every packet.
     const buffered=sampleRemotePosition(e,clientNow,!!e.moving&&Number(e.knockTime||0)<=0);
     if(buffered){e.x=buffered.x;e.y=buffered.y;continue}
     if(e.netToX==null)continue;
     const duration=Math.max(1,Number(e.netInterpDuration)||120);
     const alpha=clamp((clientNow-(Number(e.netInterpStartedAt)||clientNow))/duration,0,1);
     e.x=(Number(e.netFromX)||0)+((Number(e.netToX)||0)-(Number(e.netFromX)||0))*alpha;
     e.y=(Number(e.netFromY)||0)+((Number(e.netToY)||0)-(Number(e.netFromY)||0))*alpha;
   }
   const projectiles=state.dragonProjectiles||[];
   for(let i=projectiles.length-1;i>=0;i--){
     const p=projectiles[i];
     if(p.netRemovedAt&&clientNow>=Number(p.netRemovedAt)+REMOTE_WAR_RENDER_DELAY_MS){projectiles.splice(i,1);continue}
     const buffered=sampleRemotePosition(p,clientNow,!p.netRemovedAt);
     if(buffered){p.x=buffered.x;p.y=buffered.y}
   }
 }"""
replace_once(old_loop,new_loop,'client buffered interpolation loop')

p.write_text(t,encoding='utf-8')

required=[
 'const REMOTE_WAR_RENDER_DELAY_MS=160;',
 'function appendRemotePositionSample(',
 'function sampleRemotePosition(',
 'const netHistory=appendRemotePositionSample(old,toX,toY,remoteNow);',
 'nextProjectiles.push({...old,netHistory:history,netRemovedAt:removedAt});',
 'clientNow>=Number(p.netRemovedAt)+REMOTE_WAR_RENDER_DELAY_MS',
 'out.netHistory=[{x:tx,y:ty,t:remoteNow-1},{x:tx,y:ty,t:remoteNow}];'
]
missing=[x for x in required if x not in t]
if missing: raise SystemExit('Missing remote smoothing markers: '+repr(missing))
if 'Projectiles keep moving at render FPS between Firebase updates.' in t:
 raise SystemExit('Old projectile forward simulation remains')
print('Buffered remote movement/projectile smoothing applied.')
