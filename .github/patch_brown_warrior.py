from pathlib import Path

p=Path('index.html')
t=p.read_text(encoding='utf-8')
MARK='BROWN WARRIOR SYSTEM 2026-09-12'
if MARK in t:
    print('Brown Warrior patch already applied.')
    raise SystemExit(0)

def rep(old,new,label):
    global t
    n=t.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected exactly 1 match, found {n}')
    t=t.replace(old,new,1)

rep('<link rel="prefetch" as="image" href="assets/ui/war-shop/card-dragao-guerreiro.png">','<link rel="prefetch" as="image" href="assets/ui/war-shop/card-dragao-guerreiro.png">\n<link rel="prefetch" as="image" href="assets/ui/war-shop/card-guerreira-marrom.png">','prefetch')

rep('/* ===== MAGO / MAGA GUERREIROS ===== */','''/* ===== GUERREIRA MARROM ===== */
.entity-visual.brown-warrior-visual{width:96px;height:116px}
.entity-visual.brown-warrior-visual .entity-facing{width:96px;height:108px}
.entity-visual.brown-warrior-visual .entity-body{left:-7px;top:-9px;width:110px;height:110px;object-fit:contain}
.entity-visual.brown-warrior-visual .entity-bars{left:15px;top:-5px;width:66px}
.entity-visual.brown-warrior-visual .hp-bg,
.entity-visual.brown-warrior-visual .shield-bg{width:66px}
.entity-visual.brown-warrior-visual .entity-weapon-facing{display:none !important}
.entity-brown-attack,.entity-brown-special{opacity:0}
.brown-warrior-power{position:absolute;object-fit:contain;pointer-events:none;transform-origin:center;will-change:auto}

/* ===== MAGO / MAGA GUERREIROS ===== */''','brown CSS')

rep('.entity-body,.entity-sword,.mage-staff,.mage-hand,.golem-rock-fragment,.mage-power-normal,.mage-power-special,.shop-unit img,.clan-option img{','.entity-body,.entity-sword,.mage-staff,.mage-hand,.golem-rock-fragment,.mage-power-normal,.mage-power-special,.brown-warrior-power,.shop-unit img,.clan-option img{','image rendering selector')

rep('<div class="small">Guerreiro/Guerreira • Rei Guerreiro • Mago/Maga • Golem • Dragão</div>\n        <div class="small">Cinco tropas disponíveis na preparação da guerra.</div>','<div class="small">Guerreiro/Guerreira • Guerreira Marrom • Rei Guerreiro • Mago/Maga • Golem • Dragão</div>\n        <div class="small">Seis tropas disponíveis na preparação da guerra.</div>','clan description')

rep('        <button id="buyKing" class="shop-sprite-card" aria-label="Comprar Rei Guerreiro por 400 gemas" title="Rei Guerreiro — 400 gemas">','''        <button id="buyBrownWarrior" class="shop-sprite-card" aria-label="Comprar Guerreira Marrom por 450 gemas" title="Guerreira Marrom — 450 gemas">
          <img src="assets/ui/war-shop/card-guerreira-marrom.png" alt="Guerreira Marrom" draggable="false" decoding="async">
        </button>
        <button id="buyKing" class="shop-sprite-card" aria-label="Comprar Rei Guerreiro por 400 gemas" title="Rei Guerreiro — 400 gemas">''','shop card')

rep("  // Rei Guerreiro — clã Guerreiros\n  kingIdle:","""  // Guerreira Marrom — clã Guerreiros
  brownIdle:'assets/brown-warrior/guerreira-marrom-parada.gif',
  brownWalk:'assets/brown-warrior/guerreira-marrom-andando.gif',
  brownAttack:'assets/brown-warrior/guerreira-marrom-ataque-normal.gif',
  brownSpecial:'assets/brown-warrior/guerreira-marrom-ataque-especial.gif',
  brownPower:'assets/brown-warrior/poder-especial-guerreira-marrom.gif',

  // Rei Guerreiro — clã Guerreiros
  kingIdle:""",'brown assets')

rep('const WAR_UNIT_COSTS=Object.freeze({warrior:50,king:400,golem:550,mage:550,dragon:450});','/* BROWN WARRIOR SYSTEM 2026-09-12 */\nconst WAR_UNIT_COSTS=Object.freeze({warrior:50,brownWarrior:450,king:400,golem:550,mage:550,dragon:450});','unit costs')

rep('let GOLEM_NORMAL_DURATION=3000;\nlet GOLEM_SPECIAL_DURATION=3300;','''let GOLEM_NORMAL_DURATION=3000;
let GOLEM_SPECIAL_DURATION=3300;
let BROWN_NORMAL_DURATION=1800;
let BROWN_SPECIAL_BODY_DURATION=2200;
let BROWN_POWER_DURATION=2200;
let BROWN_SPECIAL_DURATION=2200;
const BROWN_NORMAL_DAMAGE_1=40;
const BROWN_NORMAL_DAMAGE_2=25;
const BROWN_SPECIAL_DAMAGE=15;
const BROWN_SPECIAL_TICK_MS=500;
const BROWN_SPECIAL_LENGTH=340;
const BROWN_SPECIAL_BEHIND=58;
const BROWN_SPECIAL_HALF_WIDTH=56;''','brown constants')

rep('let golemAttackAssetsReady=false;\nconst golemGifReadyKeys=new Set();','let golemAttackAssetsReady=false;\nlet brownAttackAssetsReady=false;\nconst golemGifReadyKeys=new Set();\nconst brownGifReadyKeys=new Set();','brown asset ready')

rep("const gifKeys=['golemAttack','golemSpecial','magePower','mageSpecial','femaleMageSpecial','magePowerSpecial','kingSpecial','kingPower','dragonTakeoff','dragonAttack','dragonFireball'];","const gifKeys=['golemAttack','golemSpecial','brownAttack','brownSpecial','brownPower','magePower','mageSpecial','femaleMageSpecial','magePowerSpecial','kingSpecial','kingPower','dragonTakeoff','dragonAttack','dragonFireball'];",'gif preload list')

rep("     if(key==='golemSpecial')GOLEM_SPECIAL_DURATION=validGifDuration(duration,GOLEM_SPECIAL_DURATION);\n     if(key==='kingSpecial')","""     if(key==='golemSpecial')GOLEM_SPECIAL_DURATION=validGifDuration(duration,GOLEM_SPECIAL_DURATION);
     if(key==='brownAttack')BROWN_NORMAL_DURATION=validGifDuration(duration,BROWN_NORMAL_DURATION);
     if(key==='brownSpecial')BROWN_SPECIAL_BODY_DURATION=validGifDuration(duration,BROWN_SPECIAL_BODY_DURATION);
     if(key==='brownPower')BROWN_POWER_DURATION=validGifDuration(duration,BROWN_POWER_DURATION);
     if(key==='kingSpecial')""",'gif duration brown')

rep("""     if(key==='golemAttack'||key==='golemSpecial'){
       golemGifReadyKeys.add(key);
       if(golemGifReadyKeys.size===2)golemAttackAssetsReady=true;
     }""","""     if(key==='golemAttack'||key==='golemSpecial'){
       golemGifReadyKeys.add(key);
       if(golemGifReadyKeys.size===2)golemAttackAssetsReady=true;
     }
     if(key==='brownAttack'||key==='brownSpecial'||key==='brownPower'){
       brownGifReadyKeys.add(key);
       if(brownGifReadyKeys.size===3)brownAttackAssetsReady=true;
     }""",'brown gif ready finally')

rep(' MAGE_SPECIAL_DURATION=Math.max(MAGE_SPECIAL_MALE_DURATION,MAGE_SPECIAL_FEMALE_DURATION,MAGE_POWER_SPECIAL_DURATION);\n KING_SPECIAL_DURATION=Math.max(KING_BODY_SPECIAL_DURATION,KING_POWER_DURATION);',' MAGE_SPECIAL_DURATION=Math.max(MAGE_SPECIAL_MALE_DURATION,MAGE_SPECIAL_FEMALE_DURATION,MAGE_POWER_SPECIAL_DURATION);\n BROWN_SPECIAL_DURATION=Math.max(BROWN_SPECIAL_BODY_DURATION,BROWN_POWER_DURATION);\n KING_SPECIAL_DURATION=Math.max(KING_BODY_SPECIAL_DURATION,KING_POWER_DURATION);','brown special duration')

rep('setTimeout(()=>{golemAttackAssetsReady=true},3500);','setTimeout(()=>{golemAttackAssetsReady=true},3500);\nsetTimeout(()=>{brownAttackAssetsReady=true},3500);','brown ready fallback')

rep("}else if(e.type==='mage'){\n   out.mageAttackKind=e.mageAttackKind??null;","""}else if(e.type==='brownWarrior'){
   out.brownAttackKind=e.brownAttackKind??null;
   out.brownAttackSerial=Number(e.brownAttackSerial)||0;
   out.brownNormalCount=Number(e.brownNormalCount)||0;
   if(e.pendingBrownAttack){
     const p=e.pendingBrownAttack;
     out.pendingBrownAttack={
       kind:p.kind,serial:Number(p.serial)||Number(e.brownAttackSerial)||0,targetId:p.targetId??null,
       originX:Number.isFinite(Number(p.originX))?Number(p.originX):e.x,
       originY:Number.isFinite(Number(p.originY))?Number(p.originY):e.y,
       angle:Number.isFinite(Number(p.angle))?Number(p.angle):0,
       length:Number.isFinite(Number(p.length))?Number(p.length):BROWN_SPECIAL_LENGTH,
       duration:Number(p.duration)||(p.kind==='special'?BROWN_SPECIAL_DURATION:BROWN_NORMAL_DURATION),
       remainingMs:Math.max(0,Number(p.endAt)-now),
       hit1RemainingMs:p.hit1At?Math.max(0,Number(p.hit1At)-now):0,
       hit2RemainingMs:p.hit2At?Math.max(0,Number(p.hit2At)-now):0,
       hit1Done:!!p.hit1Done,hit2Done:!!p.hit2Done
     };
   }
 }else if(e.type==='mage'){
   out.mageAttackKind=e.mageAttackKind??null;""",'brown serialize')

rep("""     // Estado visual nunca pode sobreviver sozinho sem um ataque pendente real.
     if(!out.pendingGolemAttack)out.golemAttackKind=null;
     if(out.dragonTakeoffRemainingMs!=null){""","""     // Estado visual nunca pode sobreviver sozinho sem um ataque pendente real.
     if(!out.pendingGolemAttack)out.golemAttackKind=null;
     if(out.pendingBrownAttack?.remainingMs!=null){
       const p=out.pendingBrownAttack;
       const serial=Number(p.serial)||Number(out.brownAttackSerial)||0;
       const duration=p.duration||(p.kind==='special'?BROWN_SPECIAL_DURATION:BROWN_NORMAL_DURATION);
       const remaining=Math.max(0,Number(p.remainingMs)||0);
       const oldPending=old?.pendingBrownAttack;
       const sameSerial=!!oldPending&&Number(oldPending.serial)===serial;
       if(remaining<=0){
         out.pendingBrownAttack=null;out.brownAttackKind=null;
       }else if(sameSerial&&Number.isFinite(Number(oldPending.endAt))){
         out.pendingBrownAttack={...p,serial,duration,
           startedAt:Number(oldPending.startedAt)||localNow-Math.max(0,duration-remaining),
           hit1At:p.hit1Done?localNow:Number(oldPending.hit1At)||localNow+Math.max(0,Number(p.hit1RemainingMs)||0),
           hit2At:p.hit2Done?localNow:Number(oldPending.hit2At)||localNow+Math.max(0,Number(p.hit2RemainingMs)||0),
           endAt:Math.min(Number(oldPending.endAt),localNow+remaining),
           nextTickAt:Number(oldPending.nextTickAt)||localNow+BROWN_SPECIAL_TICK_MS
         };
       }else{
         out.pendingBrownAttack={...p,serial,duration,
           startedAt:localNow-Math.max(0,duration-remaining),
           hit1At:localNow+Math.max(0,Number(p.hit1RemainingMs)||0),
           hit2At:localNow+Math.max(0,Number(p.hit2RemainingMs)||0),
           endAt:localNow+remaining,nextTickAt:localNow+BROWN_SPECIAL_TICK_MS
         };
       }
     }
     if(!out.pendingBrownAttack)out.brownAttackKind=null;
     if(out.dragonTakeoffRemainingMs!=null){""",'brown remote')

rep("     if(cmd.type==='buy-warrior')buyForPlayer(p,false);\n     if(cmd.type==='buy-king')","     if(cmd.type==='buy-warrior')buyForPlayer(p,false);\n     if(cmd.type==='buy-brown-warrior')buyBrownWarriorForPlayer(p,false);\n     if(cmd.type==='buy-king')",'brown host command')

rep(' pendingMageAttack:null,mageAttackKind:null,mageAttackSerial:0,mageCycle:0,\n pendingKingSpecial:null',' pendingMageAttack:null,mageAttackKind:null,mageAttackSerial:0,mageCycle:0,\n pendingBrownAttack:null,brownAttackKind:null,brownAttackSerial:0,brownNormalCount:0,\n pendingKingSpecial:null','brown entity base')

rep('function spawnKing(x,y,team,color){',"""function spawnBrownWarrior(x,y,team,color){
 const e=entityBase('brownWarrior',x,y,team,color);
 if(state.mode==='war')e.speed*=WAR_TROOP_SPEED_MULTIPLIER;
 e.hp=e.maxHp=250;
 e.shield=e.maxShield=150;
 e.damage=BROWN_NORMAL_DAMAGE_1;
 e.r=30;
 e.brownNormalCount=0;
 state.entities.push(e);
 return e;
}
function spawnKing(x,y,team,color){""",'brown spawn')

rep("const golemVsWarriorMage=target.type==='golem' && (attacker.type==='warrior' || attacker.type==='king' || attacker.type==='mage');","const golemVsWarriorMage=target.type==='golem' && (attacker.type==='warrior' || attacker.type==='brownWarrior' || attacker.type==='king' || attacker.type==='mage');",'golem resistance')

rep(' e.pendingMageAttack=null;\n e.mageAttackKind=null;\n e.pendingKingSpecial=null;',' e.pendingMageAttack=null;\n e.mageAttackKind=null;\n e.pendingBrownAttack=null;\n e.brownAttackKind=null;\n e.pendingKingSpecial=null;','brown death clear')

rep("const REAL_COMBAT_TYPES=new Set(['warrior','king','mage','golem','dragon','enemy']);","const REAL_COMBAT_TYPES=new Set(['warrior','brownWarrior','king','mage','golem','dragon','enemy']);",'combat types')
rep("if(target.type==='dragon'&&target.dragonFlightState==='flying'&&(attacker.type==='warrior'||attacker.type==='king'))return false;","if(target.type==='dragon'&&target.dragonFlightState==='flying'&&(attacker.type==='warrior'||attacker.type==='brownWarrior'||attacker.type==='king'))return false;",'flying dragon melee restriction')

rep('function distanceToSegment(px,py,ax,ay,bx,by){',"""function brownPowerPosition(p,at=performance.now()){
 const duration=Math.max(1,Number(p.duration)||BROWN_SPECIAL_DURATION);
 const progress=clamp((at-Number(p.startedAt||at))/duration,0,1);
 const travelProgress=1-Math.pow(1-progress,2.35);
 const travel=-BROWN_SPECIAL_BEHIND+((Number(p.length)||BROWN_SPECIAL_LENGTH)+BROWN_SPECIAL_BEHIND)*travelProgress;
 const angle=Number(p.angle)||0;
 return {progress,travel,x:(Number(p.originX)||0)+Math.cos(angle)*travel,y:(Number(p.originY)||0)+Math.sin(angle)*travel};
}

function startBrownWarriorAttack(e,kind,target){
 if(!e?.alive||e.type!=='brownWarrior'||e.pendingBrownAttack||e.attackCooldown>0||e.knockTime>0||!brownAttackAssetsReady)return false;
 if(!isRealCombatTarget(target)||target===e||target.team===e.team||!canEngageTarget(e,target))return false;
 const d=dist(e,target);
 if(kind==='special'){if(d>132)return false}else if(d>108)return false;
 const now=performance.now(),angle=Math.atan2(target.y-e.y,target.x-e.x);
 e.heading=angle;if(Math.abs(target.x-e.x)>4)e.facing=target.x<e.x?-1:1;
 e.moving=false;e.lastAttackAt=now;e.lastCombatAt=now;
 e.brownAttackKind=kind;e.brownAttackSerial=(Number(e.brownAttackSerial)||0)+1;
 const duration=kind==='special'?BROWN_SPECIAL_DURATION:BROWN_NORMAL_DURATION;
 e.attackCooldown=duration/1000+.12;
 if(kind==='special'){
   e.pendingBrownAttack={kind,serial:e.brownAttackSerial,targetId:target.id,originX:e.x,originY:e.y,angle,
     length:BROWN_SPECIAL_LENGTH,duration,startedAt:now,nextTickAt:now+BROWN_SPECIAL_TICK_MS,endAt:now+duration};
   addWarGoalProgress(e.team,'specials');
 }else{
   const hit1Delay=Math.min(duration-260,Math.max(280,duration*.32));
   const hit2Delay=Math.min(duration-120,Math.max(hit1Delay+180,duration*.62));
   e.pendingBrownAttack={kind,serial:e.brownAttackSerial,targetId:target.id,originX:e.x,originY:e.y,angle,duration,startedAt:now,
     hit1At:now+hit1Delay,hit2At:now+hit2Delay,endAt:now+duration,hit1Done:false,hit2Done:false};
 }
 return true;
}

function brownNormalHit(e,p,amount,which){
 if(p[which])return;
 p[which]=true;
 if(!e.alive)return;
 const target=warEntityById.get(p.targetId)||state.entities.find(t=>t.id===p.targetId);
 if(!target?.alive||target===e||target.team===e.team||!canEngageTarget(e,target))return;
 const dx=target.x-e.x,dy=target.y-e.y;
 if(dx*dx+dy*dy>128*128)return;
 applyCombatHit(target,e,amount,{knockForce:which==='hit1Done'?255:180,knockTime:which==='hit1Done'?.14:.10,tilt:which==='hit1Done'?9:7});
}

function applyBrownSpecialTick(e,p,at){
 if(!e.alive)return;
 const pos=brownPowerPosition(p,at),angle=Number(p.angle)||0;
 const behindX=(Number(p.originX)||e.x)-Math.cos(angle)*BROWN_SPECIAL_BEHIND;
 const behindY=(Number(p.originY)||e.y)-Math.sin(angle)*BROWN_SPECIAL_BEHIND;
 const pad=BROWN_SPECIAL_HALF_WIDTH+42;
 const minX=Math.min(behindX,pos.x)-pad,maxX=Math.max(behindX,pos.x)+pad;
 const minY=Math.min(behindY,pos.y)-pad,maxY=Math.max(behindY,pos.y)+pad;
 forEachWarSpatialCandidate(minX,minY,maxX,maxY,target=>{
   if(!isRealCombatTarget(target)||target===e||target.team===e.team)return;
   const body=Math.min(22,(target.r||25)*.62);
   const cdx=target.x-pos.x,cdy=target.y-pos.y;
   const nearCurrent=cdx*cdx+cdy*cdy<=Math.pow(BROWN_SPECIAL_HALF_WIDTH+body+12,2);
   const inTrail=distanceToSegment(target.x,target.y,behindX,behindY,pos.x,pos.y)<=BROWN_SPECIAL_HALF_WIDTH+body;
   if(nearCurrent||inTrail)applyCombatHit(target,e,BROWN_SPECIAL_DAMAGE,{knockForce:0,knockTime:0,tilt:4,allowFlying:true});
 });
}

function updateBrownWarriorAttackState(e,now){
 const p=e.pendingBrownAttack;if(!p)return;
 e.moving=false;
 if(p.kind==='normal'){
   if(!p.hit1Done&&now>=Number(p.hit1At||Infinity))brownNormalHit(e,p,BROWN_NORMAL_DAMAGE_1,'hit1Done');
   if(!p.hit2Done&&now>=Number(p.hit2At||Infinity))brownNormalHit(e,p,BROWN_NORMAL_DAMAGE_2,'hit2Done');
 }else{
   let guard=0;
   while(now>=Number(p.nextTickAt||Infinity)&&Number(p.nextTickAt)<=Number(p.endAt)&&guard<5){
     applyBrownSpecialTick(e,p,Number(p.nextTickAt));
     p.nextTickAt+=BROWN_SPECIAL_TICK_MS;guard++;
   }
 }
 if(now>=Number(p.endAt||0)){
   if(p.kind==='normal')e.brownNormalCount=Math.min(6,(Number(e.brownNormalCount)||0)+1);
   else e.brownNormalCount=0;
   e.pendingBrownAttack=null;e.brownAttackKind=null;e.target=null;
 }
}

function distanceToSegment(px,py,ax,ay,bx,by){""",'brown combat system')

rep("if(e.type==='golem'||e.type==='mage')return;","if(e.type==='golem'||e.type==='mage'||e.type==='brownWarrior')return;",'generic attack exclusion')

rep(" else {if(type==='buy-warrior')buyForPlayer(p,false);if(type==='buy-king')buyKingForPlayer(p,false);"," else {if(type==='buy-warrior')buyForPlayer(p,false);if(type==='buy-brown-warrior')buyBrownWarriorForPlayer(p,false);if(type==='buy-king')buyKingForPlayer(p,false);",'brown local purchase request')
rep("$('#buyWarrior').onclick=()=>requestWarPurchase('buy-warrior');\n$('#buyKing')","$('#buyWarrior').onclick=()=>requestWarPurchase('buy-warrior');\n$('#buyBrownWarrior').onclick=()=>requestWarPurchase('buy-brown-warrior');\n$('#buyKing')",'brown shop handler')
rep('function buyKingForPlayer(p,bot){',"""function buyBrownWarriorForPlayer(p,bot){
 const cost=WAR_UNIT_COSTS.brownWarrior;if(p.gems<cost)return false;
 p.gems-=cost;p.troops++;
 const t=p.territory,angle=Math.random()*Math.PI*2,r=Math.random()*88;
 spawnBrownWarrior(t.x+Math.cos(angle)*r,t.y+Math.sin(angle)*r,p.id,p.color);
 return true;
}
function buyKingForPlayer(p,bot){""",'brown buy function')

rep('const out={warrior:0,king:0,mage:0,golem:0,dragon:0};','const out={warrior:0,brownWarrior:0,king:0,mage:0,golem:0,dragon:0};','own composition')
rep('const out={warrior:0,king:0,mage:0,golem:0,dragon:0};','const out={warrior:0,brownWarrior:0,king:0,mage:0,golem:0,dragon:0};','enemy composition')
rep("if(p.gems>=WAR_UNIT_COSTS.warrior)types.push('warrior');\n if(p.gems>=WAR_UNIT_COSTS.king)","if(p.gems>=WAR_UNIT_COSTS.warrior)types.push('warrior');\n if(p.gems>=WAR_UNIT_COSTS.brownWarrior)types.push('brownWarrior');\n if(p.gems>=WAR_UNIT_COSTS.king)",'brown bot affordability')
rep('const enemyTotal=enemy.warrior+enemy.king+enemy.mage+enemy.golem+enemy.dragon;','const enemyTotal=enemy.warrior+enemy.brownWarrior+enemy.king+enemy.mage+enemy.golem+enemy.dragon;','enemy total')
rep('const score={warrior:1,king:1,mage:1,golem:1,dragon:1};','const score={warrior:1,brownWarrior:1,king:1,mage:1,golem:1,dragon:1};','bot score types')
rep('score.warrior+=enemy.mage*1.45+enemy.golem*.12;','score.warrior+=enemy.mage*1.45+enemy.golem*.12;\n score.brownWarrior+=enemy.warrior*.75+enemy.brownWarrior*.55+enemy.king*.70+enemy.mage*1.20+enemy.golem*.45;','brown bot score')
rep('if(enemy.dragon>0){score.warrior*=.10;score.king*=.10}','if(enemy.dragon>0){score.warrior*=.10;score.brownWarrior*=.10;score.king*=.10}','brown dragon bot penalty')
rep("if(type==='king')return buyKingForPlayer(p,true);","if(type==='brownWarrior')return buyBrownWarriorForPlayer(p,true);\n if(type==='king')return buyKingForPlayer(p,true);",'brown bot buy')

rep("const avoidDragons=(e.type==='warrior'||e.type==='king')&&(warFrameEnemiesByTeam.get(e.team)?.nonDragon.length||0)>0;","const avoidDragons=(e.type==='warrior'||e.type==='brownWarrior'||e.type==='king')&&(warFrameEnemiesByTeam.get(e.team)?.nonDragon.length||0)>0;",'brown avoid dragon')

rep("function aiFight(e,dt,forcedTeam,preparedCandidates=null){\n if(e.type==='golem')","""function aiFightBrownWarrior(e,dt,forcedTeam,preparedCandidates=null){
 if(!e.alive||e.knockTime>0){e.moving=false;return}
 if(e.pendingBrownAttack){e.moving=false;return}
 const candidates=preparedCandidates||state.entities;
 const target=nearestEngageableCandidate(e,candidates,forcedTeam,false);
 if(!target){e.moving=false;e.target=null;return}
 e.target=target;
 const dx=target.x-e.x,dy=target.y-e.y,d=Math.hypot(dx,dy)||1;
 e.heading=Math.atan2(dy,dx);if(Math.abs(dx)>4)e.facing=dx<0?-1:1;
 if((Number(e.brownNormalCount)||0)>=6){
   if(d<=125&&startBrownWarriorAttack(e,'special',target))return;
   if(d>125){e.x+=dx/d*e.speed*dt;e.y+=dy/d*e.speed*dt;e.moving=true}else e.moving=false;
 }else if(d<=92){
   if(startBrownWarriorAttack(e,'normal',target))return;
   e.moving=false;
 }else{
   e.x+=dx/d*e.speed*dt;e.y+=dy/d*e.speed*dt;e.moving=true;
 }
 e.x=clamp(e.x,35,state.world.w-35);e.y=clamp(e.y,35,state.world.h-35);
}

function aiFight(e,dt,forcedTeam,preparedCandidates=null){
 if(e.type==='brownWarrior'){aiFightBrownWarrior(e,dt,forcedTeam,preparedCandidates);return;}
 if(e.type==='golem')""",'brown AI')

rep("""   if(e.type==='golem' && e.pendingGolemAttack){
     updateGolemAttackState(e,now);
   }""","""   if(e.type==='golem' && e.pendingGolemAttack){
     updateGolemAttackState(e,now);
   }
   if(e.type==='brownWarrior' && e.pendingBrownAttack){
     updateBrownWarriorAttackState(e,now);
   }""",'brown update state')

rep("const buyWarriorPerfEl=$('#buyWarrior'),buyKingPerfEl=$('#buyKing'),buyGolemPerfEl=$('#buyGolem'),buyMagePerfEl=$('#buyMage'),buyDragonPerfEl=$('#buyDragon');","const buyWarriorPerfEl=$('#buyWarrior'),buyBrownWarriorPerfEl=$('#buyBrownWarrior'),buyKingPerfEl=$('#buyKing'),buyGolemPerfEl=$('#buyGolem'),buyMagePerfEl=$('#buyMage'),buyDragonPerfEl=$('#buyDragon');",'brown HUD ref')
rep("perfSetDisabled(buyWarriorPerfEl,state.phase!=='prep'||gems<WAR_UNIT_COSTS.warrior);\n    perfSetDisabled(buyKingPerfEl","perfSetDisabled(buyWarriorPerfEl,state.phase!=='prep'||gems<WAR_UNIT_COSTS.warrior);\n    perfSetDisabled(buyBrownWarriorPerfEl,state.phase!=='prep'||gems<WAR_UNIT_COSTS.brownWarrior);\n    perfSetDisabled(buyKingPerfEl",'brown HUD disable')

rep('const magePowerNodes=new Map();\nconst kingPowerNodes=new Map();','const magePowerNodes=new Map();\nconst brownPowerNodes=new Map();\nconst kingPowerNodes=new Map();','brown power map')
rep('const magePowerActiveIds=new Set();\nconst kingPowerActiveIds=new Set();','const magePowerActiveIds=new Set();\nconst brownPowerActiveIds=new Set();\nconst kingPowerActiveIds=new Set();','brown power active')

rep('function syncMagePowerEffects(left,top,zoom,screenW,screenH,cullLeft=left,cullTop=top,cullZoom=zoom){',"""function syncBrownWarriorPowerEffects(left,top,zoom,screenW,screenH,cullLeft=left,cullTop=top,cullZoom=zoom){
 const layer=entityCameraLayer,active=brownPowerActiveIds;active.clear();const now=performance.now();
 for(const e of state.entities){
   const p=e.pendingBrownAttack;
   if(!e.alive||e.type!=='brownWarrior'||!p||p.kind!=='special'||Number(p.endAt||0)<=now)continue;
   const angle=Number(p.angle)||0,ox=Number(p.originX)||e.x,oy=Number(p.originY)||e.y;
   const ex=ox+Math.cos(angle)*(Number(p.length)||BROWN_SPECIAL_LENGTH),ey=oy+Math.sin(angle)*(Number(p.length)||BROWN_SPECIAL_LENGTH);
   const bx=ox-Math.cos(angle)*BROWN_SPECIAL_BEHIND,by=oy-Math.sin(angle)*BROWN_SPECIAL_BEHIND;
   const pad=130*cullZoom;
   const sx1=(bx-cullLeft)*cullZoom,sy1=(by-cullTop)*cullZoom,sx2=(ex-cullLeft)*cullZoom,sy2=(ey-cullTop)*cullZoom;
   const visible=Math.max(sx1,sx2)+pad>=-40&&Math.min(sx1,sx2)-pad<=screenW+40&&Math.max(sy1,sy2)+pad>=-40&&Math.min(sy1,sy2)-pad<=screenH+40;
   if(!visible){
     const old=brownPowerNodes.get(e.id);
     if(old&&(cameraComposite.active||now-Number(old._lastEffectVisibleAt||0)<CAMERA_EFFECT_RETENTION_MS)){active.add(e.id);old.style.visibility='hidden';continue}
     if(old){releaseGifObjectUrl(old);old.remove();brownPowerNodes.delete(e.id)}
     continue;
   }
   active.add(e.id);
   let img=brownPowerNodes.get(e.id);
   if(!img){img=document.createElement('img');img.className='brown-warrior-power';img.draggable=false;img.dataset.serial='-1';layer.appendChild(img);brownPowerNodes.set(e.id,img)}
   img._lastEffectVisibleAt=now;
   const serial=String(p.serial||e.brownAttackSerial||0);
   if(img.dataset.serial!==serial){img.dataset.serial=serial;restartGif(img,'brownPower',serial)}
   const pos=brownPowerPosition(p,now),progress=pos.progress;
   const alpha=Math.min(clamp(progress/.15,0,1),clamp((1-progress)/.22,0,1));
   const sx=(pos.x-left)*zoom,sy=(pos.y-top)*zoom;
   img.style.left=sx+'px';img.style.top=sy+'px';img.style.width=(190*zoom)+'px';img.style.height=(115*zoom)+'px';
   img.style.opacity=String(alpha);img.style.visibility=alpha>.01?'visible':'hidden';
   img.style.transform=`translate(-50%,-50%) rotate(${angle}rad)`;
   img.style.zIndex=String(Math.max(1,70+Math.round(sy)));
 }
 for(const [id,img] of brownPowerNodes)if(!active.has(id)){releaseGifObjectUrl(img);img.remove();brownPowerNodes.delete(id)}
}

function syncMagePowerEffects(left,top,zoom,screenW,screenH,cullLeft=left,cullTop=top,cullZoom=zoom){""",'brown power renderer')

rep(" if(e.type==='golem'){\n   el.classList.add('golem-visual');",""" if(e.type==='brownWarrior'){
   el.classList.add('brown-warrior-visual');
   el.innerHTML=`
     <div class="entity-facing">
       <img class="entity-body entity-idle active-sprite" data-asset-key="brownIdle" src="${ASSETS.brownIdle}" draggable="false" style="opacity:1">
       <img class="entity-body entity-walk" data-asset-key="brownWalk" src="${ASSETS.brownWalk}" draggable="false" style="opacity:0">
       <img class="entity-body entity-brown-attack" data-asset-key="brownAttack" draggable="false" style="opacity:0">
       <img class="entity-body entity-brown-special" data-asset-key="brownSpecial" draggable="false" style="opacity:0">
     </div>
     <div class="entity-weapon-facing"></div>
     <div class="entity-bars">
       <div class="hp-bg"><div class="hp-fill"></div></div>
       <div class="shield-bg"><div class="shield-fill"></div></div>
     </div>`;
 }else if(e.type==='golem'){
   el.classList.add('golem-visual');""",'brown entity DOM')

rep(" el._golemAttack=el.querySelector('.entity-golem-attack');\n el._golemSpecial=el.querySelector('.entity-golem-special');"," el._brownAttack=el.querySelector('.entity-brown-attack');\n el._brownSpecial=el.querySelector('.entity-brown-special');\n el._golemAttack=el.querySelector('.entity-golem-attack');\n el._golemSpecial=el.querySelector('.entity-golem-special');",'brown DOM refs')
rep(" el.dataset.golemAttackSerial='-1';\n el.dataset.golemRockSerial='-1';"," el.dataset.golemAttackSerial='-1';\n el.dataset.golemRockSerial='-1';\n el.dataset.brownAttackSerial='-1';",'brown dataset serial')
rep("if(e.type==='golem')el._gifKeys={idle:'golemIdle',walk:'golemWalk',attack:'golemAttack',special:'golemSpecial'};","if(e.type==='brownWarrior')el._gifKeys={idle:'brownIdle',walk:'brownWalk',attack:'brownAttack',special:'brownSpecial'};\n else if(e.type==='golem')el._gifKeys={idle:'golemIdle',walk:'golemWalk',attack:'golemAttack',special:'golemSpecial'};",'brown gif keys')
rep('[el._idle,el._walk,el._golemAttack,el._golemSpecial,el._mageSpecial','[el._idle,el._walk,el._brownAttack,el._brownSpecial,el._golemAttack,el._golemSpecial,el._mageSpecial','brown diagnostics')
rep("const transientState=img===el._golemAttack?'attack':\n         (img===el._golemSpecial||img===el._mageSpecial","const transientState=(img===el._golemAttack||img===el._brownAttack)?'attack':\n         (img===el._golemSpecial||img===el._brownSpecial||img===el._mageSpecial",'brown transient retry')

rep("if(stateName==='attack')return el._golemAttack;\n if(stateName==='special')return el._golemSpecial||el._mageSpecial||el._kingSpecial;","if(stateName==='attack')return el._brownAttack||el._golemAttack;\n if(stateName==='special')return el._brownSpecial||el._golemSpecial||el._mageSpecial||el._kingSpecial;",'brown state sprite lookup')
rep("   [el._idle,'idle'],[el._walk,'walk'],[el._golemAttack,'attack'],\n   [el._golemSpecial,'special'],[el._mageSpecial,'special'],","   [el._idle,'idle'],[el._walk,'walk'],[el._brownAttack,'attack'],[el._golemAttack,'attack'],\n   [el._brownSpecial,'special'],[el._golemSpecial,'special'],[el._mageSpecial,'special'],",'brown sprite list')
rep("if(previous==='attack'&&desired!=='attack')stopGif(el._golemAttack);","if(previous==='attack'&&desired!=='attack'){stopGif(el._brownAttack);stopGif(el._golemAttack)}",'brown stop attack')
rep("     stopGif(el._golemSpecial);\n     stopGif(el._mageSpecial);","     stopGif(el._brownSpecial);\n     stopGif(el._golemSpecial);\n     stopGif(el._mageSpecial);",'brown stop special')

rep("     if(e.type==='golem'&&!activeGolemPending(e,localNow)&&","     if(e.type==='brownWarrior'&&!(e.pendingBrownAttack&&e.pendingBrownAttack.endAt>localNow)&&\n        (el.dataset.anim==='attack'||el.dataset.anim==='special')){\n       setEntitySpriteState(el,e.moving?'walk':'idle');\n     }else if(e.type==='golem'&&!activeGolemPending(e,localNow)&&",'brown offscreen visual cleanup')
rep("const typeScale=e.type==='golem'?1.34:e.type==='mage'?0.96:e.type==='dragon'?1.16:e.type==='king'?0.96:1;","const typeScale=e.type==='golem'?1.34:e.type==='brownWarrior'?1.04:e.type==='mage'?0.96:e.type==='dragon'?1.16:e.type==='king'?0.96:1;",'brown visual scale')
rep("   if(e.type==='golem'){\n     const pending=activeGolemPending(e,localNow);","""   if(e.type==='brownWarrior'){
     const p=e.pendingBrownAttack;
     const active=!!p&&Number(p.endAt)>localNow;
     const kind=active?p.kind:null;
     const specialBody=kind==='special'&&localNow<(Number(p.startedAt)||localNow)+Math.max(250,BROWN_SPECIAL_BODY_DURATION-45);
     const desired=specialBody?'special':kind==='normal'?'attack':visualMoving?'walk':'idle';
     setEntitySpriteState(el,desired);
     const serial=Number(p?.serial||e.brownAttackSerial)||0;
     if(active&&serial>0&&el.dataset.brownAttackSerial!==String(serial)){
       el.dataset.brownAttackSerial=String(serial);
       if(kind==='special'&&specialBody)restartGif(el._brownSpecial,'brownSpecial',serial);
       else if(kind==='normal')restartGif(el._brownAttack,'brownAttack',serial);
     }
   }else if(e.type==='golem'){
     const pending=activeGolemPending(e,localNow);""",'brown visual state')
rep("const transient=entity && (entity.deathStarted||entity.pendingGolemAttack||entity.pendingMageAttack||entity.pendingKingSpecial||entity.pendingDragonAttack||entity.dragonFlightState==='takeoff');","const transient=entity && (entity.deathStarted||entity.pendingBrownAttack||entity.pendingGolemAttack||entity.pendingMageAttack||entity.pendingKingSpecial||entity.pendingDragonAttack||entity.dragonFlightState==='takeoff');",'brown transient retention')

rep('for(const img of magePowerNodes.values())releaseGifObjectUrl(img);\n for(const img of kingPowerNodes.values())','for(const img of magePowerNodes.values())releaseGifObjectUrl(img);\n for(const img of brownPowerNodes.values())releaseGifObjectUrl(img);\n for(const img of kingPowerNodes.values())','brown power clear release')
rep(' magePowerNodes.clear();\n kingPowerNodes.clear();',' magePowerNodes.clear();\n brownPowerNodes.clear();\n kingPowerNodes.clear();','brown power clear map')
rep('syncEntityVisuals(visible,domCamera.left,domCamera.top,domCamera.zoom,vw,vh,left,top,zoom);\n syncKingPowerEffects','syncEntityVisuals(visible,domCamera.left,domCamera.top,domCamera.zoom,vw,vh,left,top,zoom);\n syncBrownWarriorPowerEffects(domCamera.left,domCamera.top,domCamera.zoom,vw,vh,left,top,zoom);\n syncKingPowerEffects','brown power draw call')

p.write_text(t,encoding='utf-8')
print('Brown Warrior patch applied successfully.')
