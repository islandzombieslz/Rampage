
/* WATER CLAN COMBAT — authoritative host handles damage, movement and summons. */
const POSEIDON_NORMAL_MS=3070;
const POSEIDON_WAVE_BODY_MS=2550;
const POSEIDON_SUMMON_BODY_MS=2800;
const POSEIDON_WAVE_DELAY_MS=1000;
const POSEIDON_WAVE_DURATION_MS=3040;
const POSEIDON_WAVE_TICK_MS=1000;
const SEAHORSE_NORMAL_MS=1470;
function countLivingWaterSummons(poseidon){
 let count=0;
 for(const t of state.entities){
   if(t.alive&&t.type==='seahorse'&&t.team===poseidon.team&&t.waterSummonerId===poseidon.id)count++;
 }
 return count;
}
function spawnPoseidonSeahorses(e,p){
 const ox=p.originX??e.x,oy=p.originY??e.y,base=(Number(p.serial)||0)*.39;
 for(let i=0;i<3;i++){
   const a=base+i*Math.PI*2/3,r=72+(i%2)*15;
   spawnSeahorse(clamp(ox+Math.cos(a)*r,45,state.world.w-45),
     clamp(oy+Math.sin(a)*r,45,state.world.h-45),e.team,e.color,e.id);
 }
}
function waterWavePosition(p,now){
 const duration=Math.max(1,Number(p.waveDuration)||POSEIDON_WAVE_DURATION_MS);
 const progress=clamp((now-Number(p.waveStartAt||now))/duration,0,1);
 const angle=Number(p.angle)||0;
 const distance=45+300*(1-Math.pow(1-progress,1.45));
 return {progress,angle,x:Number(p.originX)+Math.cos(angle)*distance,y:Number(p.originY)+Math.sin(angle)*distance};
}
function startWaterAttack(e,kind,target=null){
 if(!e?.alive||!(e.type==='poseidon'||e.type==='seahorse')||e.pendingWaterAttack||e.attackCooldown>0||e.knockTime>0)return false;
 if(!isRealCombatTarget(target)||target.team===e.team||!canEngageTarget(e,target))return false;
 const d=dist(e,target),now=performance.now();
 if(kind==='normal'&&d>(e.type==='poseidon'?112:108))return false;
 if(kind==='wave'&&d>365)return false;
 if(e.type==='seahorse'&&kind!=='normal')return false;
 if(e.type==='poseidon'&&kind==='summon'&&countLivingWaterSummons(e)>=3)return false;
 const angle=Math.atan2(target.y-e.y,target.x-e.x);
 e.heading=angle;if(Math.abs(target.x-e.x)>4)e.facing=target.x<e.x?-1:1;
 e.moving=false;e.target=target;e.lastAttackAt=now;e.lastCombatAt=now;
 const duration=kind==='wave'?POSEIDON_WAVE_DELAY_MS+POSEIDON_WAVE_DURATION_MS:
   kind==='summon'?POSEIDON_SUMMON_BODY_MS:e.type==='seahorse'?SEAHORSE_NORMAL_MS:POSEIDON_NORMAL_MS;
 e.waterAttackKind=kind;e.waterAttackSerial=(Number(e.waterAttackSerial)||0)+1;
 e.attackCooldown=duration/1000+.12;
 e.pendingWaterAttack={
   kind,serial:e.waterAttackSerial,targetId:target.id,originX:e.x,originY:e.y,angle,duration,
   startedAt:now,endAt:now+duration,bodyEndAt:now+(kind==='wave'?POSEIDON_WAVE_BODY_MS:duration),
   impactAt:now+Math.round(duration*.52),hit1At:now+440,hit2At:now+1020,
   hit1Done:false,hit2Done:false,impacted:false,summoned:false,
   summonAt:now+1300,waveStartAt:now+POSEIDON_WAVE_DELAY_MS,
   waveDuration:POSEIDON_WAVE_DURATION_MS,nextTickById:{}
 };
 if(kind!=='normal'){
   e.knockTime=0;e.knockVX=0;e.knockVY=0;
   e.poseidonNormalCount=0;e.poseidonSpecialIndex=(Number(e.poseidonSpecialIndex)||0)+1;
   addWarGoalProgress(e.team,'specials');
   if(kind==='wave')addWarGoalProgress(e.team,'ranged');
 }
 return true;
}
function updateWaterAttackState(e,now,dt){
 const p=e.pendingWaterAttack;if(!p)return;
 e.moving=false;
 if(p.kind==='normal'){
   if(e.type==='poseidon'){
     if(!p.impacted&&now>=Number(p.impactAt)){
       p.impacted=true;
       const target=warEntityById.get(p.targetId)||state.entities.find(t=>t.id===p.targetId);
       if(e.alive&&target?.alive&&target.team!==e.team&&canEngageTarget(e,target)&&dist(e,target)<=118)
         applyCombatHit(target,e,e.damage,{knockForce:220,knockTime:.12,tilt:9});
     }
   }else{
     const target=warEntityById.get(p.targetId)||state.entities.find(t=>t.id===p.targetId);
     for(const [at,flag,force] of [[p.hit1At,'hit1Done',255],[p.hit2At,'hit2Done',180]]){
       if(p[flag]||now<Number(at))continue;
       p[flag]=true;
       if(e.alive&&target?.alive&&target.team!==e.team&&canEngageTarget(e,target)&&dist(e,target)<=128)
         applyCombatHit(target,e,e.damage/2,{knockForce:force,knockTime:.12,tilt:9});
     }
   }
 }else if(p.kind==='summon'){
   if(!p.summoned&&now>=Number(p.summonAt)){
     p.summoned=true;if(e.alive)spawnPoseidonSeahorses(e,p);
   }
 }else if(p.kind==='wave'&&now>=Number(p.waveStartAt)&&now<Number(p.endAt)&&e.alive){
   const pos=waterWavePosition(p,now),radius=105,pad=radius+50;
   const ticks=p.nextTickById||(p.nextTickById={});
   forEachWarSpatialCandidate(pos.x-pad,pos.y-pad,pos.x+pad,pos.y+pad,t=>{
     if(!isRealCombatTarget(t)||t.team===e.team||t===e||najaIsUnderground(t))return;
     if(t.type==='poseidon'&&entityHasActiveSpecial(t,now))return;
     if(Math.hypot(t.x-pos.x,t.y-pos.y)>radius+(Number(t.r)||25)*.55)return;
     if(ticks[t.id]===undefined)ticks[t.id]=now;
     if(now>=ticks[t.id]&&ticks[t.id]<p.endAt){
       applyCombatHit(t,e,25,{knockForce:0,knockTime:0,tilt:4,allowFlying:true});
       ticks[t.id]+=POSEIDON_WAVE_TICK_MS;
     }
     const travel=Math.min(95*dt,8);
     t.x+=Math.cos(pos.angle)*travel;t.y+=Math.sin(pos.angle)*travel;
     t.x=clamp(t.x,35,state.world.w-35);t.y=clamp(t.y,35,state.world.h-35);
     t.waveDraggedUntil=now+125;
   });
 }
 if(now>=Number(p.endAt)){
   if(p.kind==='normal'&&e.type==='poseidon')e.poseidonNormalCount=Math.min(4,(Number(e.poseidonNormalCount)||0)+1);
   e.pendingWaterAttack=null;e.waterAttackKind=null;e.target=null;
 }
}
function aiFightPoseidon(e,dt,forcedTeam,preparedCandidates=null){
 if(!e.alive||e.pendingWaterAttack){e.moving=false;return}
 const target=nearestEngageableCandidate(e,preparedCandidates||state.entities,forcedTeam,false);
 if(!target){e.moving=false;e.target=null;return}
 const dx=target.x-e.x,dy=target.y-e.y,d=Math.hypot(dx,dy)||1;
 e.target=target;e.heading=Math.atan2(dy,dx);if(Math.abs(dx)>4)e.facing=dx<0?-1:1;
 if((Number(e.poseidonNormalCount)||0)>=4){
   let kind=(Number(e.poseidonSpecialIndex)||0)%2===0?'wave':'summon';
   if(kind==='summon'&&countLivingWaterSummons(e)>=3)kind='wave';
   if(d<=365&&startWaterAttack(e,kind,target))return;
 }
 if(d<=100){if(startWaterAttack(e,'normal',target))return;e.moving=false}
 else{e.x+=dx/d*e.speed*dt;e.y+=dy/d*e.speed*dt;e.moving=true}
 e.x=clamp(e.x,42,state.world.w-42);e.y=clamp(e.y,42,state.world.h-42);
}
function aiFightSeahorse(e,dt,forcedTeam,preparedCandidates=null){
 if(!e.alive||e.pendingWaterAttack){e.moving=false;return}
 const target=nearestEngageableCandidate(e,preparedCandidates||state.entities,forcedTeam,true);
 if(!target){e.moving=false;e.target=null;return}
 const dx=target.x-e.x,dy=target.y-e.y,d=Math.hypot(dx,dy)||1;
 e.target=target;e.heading=Math.atan2(dy,dx);if(Math.abs(dx)>4)e.facing=dx<0?-1:1;
 if(d<=92){if(startWaterAttack(e,'normal',target))return;e.moving=false}
 else{e.x+=dx/d*e.speed*dt;e.y+=dy/d*e.speed*dt;e.moving=true}
 e.x=clamp(e.x,35,state.world.w-35);e.y=clamp(e.y,35,state.world.h-35);
}
