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


def insert_after(anchor,addition,label):
    global t
    if addition in t:
        return
    c=t.count(anchor)
    if c!=1:
        raise SystemExit(f'{label}: expected 1 anchor, found {c}')
    t=t.replace(anchor,anchor+addition,1)


def insert_before(anchor,addition,label):
    global t
    if addition in t:
        return
    c=t.count(anchor)
    if c!=1:
        raise SystemExit(f'{label}: expected 1 anchor, found {c}')
    t=t.replace(anchor,addition+anchor,1)


# ---------- Shop / clan UI ----------
old_shop='''        <button id="buyEgyptNaja" class="shop-sprite-card" aria-label="Comprar Naja do Egito por 550 gemas" title="Naja do Egito — 550 gemas">\n          <img src="assets/egypt/naja/card.png" alt="Naja do Egito" draggable="false" decoding="async">\n        </button>'''
new_shop=old_shop+'''\n        <button id="buyEgyptAnubis" class="shop-sprite-card" aria-label="Comprar Annubis do Egito por 450 gemas" title="Annubis do Egito — 450 gemas">\n          <img src="assets/egypt/anubis/card.png" alt="Annubis do Egito" draggable="false" decoding="async">\n        </button>'''
replace_once(old_shop,new_shop,'Anubis Egypt shop card')
replace_once('Guerreiro/Guerreira do Egito • Mago/Maga do Egito • Naja do Egito','Guerreiro/Guerreira do Egito • Mago/Maga do Egito • Naja do Egito • Annubis','Egypt clan description')

# ---------- CSS: same visual footprint/scale as Golem ----------
css_anchor='''/* ===== GUERREIRA MARROM ===== */'''
old_anubis_css='''/* ===== ANNUBIS DO EGITO ===== */\n.entity-visual.anubis-visual{width:102px;height:130px}\n.entity-visual.anubis-visual .entity-facing{width:102px;height:122px}\n/* O GIF tem bastante transparencia a direita/abaixo. Compensacao visual centraliza o corpo no circulo sem mover hitbox/barras. */\n.entity-visual.anubis-visual .entity-body{left:3px;top:1px;width:120px;height:140px;object-fit:contain}\n.entity-visual.anubis-visual .entity-bars{left:14px;top:-5px;width:74px}\n.entity-visual.anubis-visual .hp-bg,.entity-visual.anubis-visual .shield-bg{width:74px}\n.entity-visual.anubis-visual .entity-weapon-facing{display:none !important}\n.entity-anubis-melee,.entity-anubis-ranged{opacity:0}\n\n'''
anubis_css='''/* ===== ANNUBIS DO EGITO ===== */\n.entity-visual.anubis-visual{width:102px;height:130px}\n.entity-visual.anubis-visual .entity-facing{width:102px;height:122px}\n/* Alinhamento real do Annubis e feito no container externo em syncEntityVisuals(). */\n.entity-visual.anubis-visual .entity-body{left:-9px;top:-12px;width:120px;height:140px;object-fit:contain}\n.entity-visual.anubis-visual .entity-bars{left:14px;top:-5px;width:74px}\n.entity-visual.anubis-visual .hp-bg,.entity-visual.anubis-visual .shield-bg{width:74px}\n.entity-visual.anubis-visual .entity-weapon-facing{display:none !important}\n.entity-anubis-melee,.entity-anubis-ranged{opacity:0}\n\n'''
if anubis_css not in t:
    if old_anubis_css in t:
        replace_once(old_anubis_css,anubis_css,'Anubis internal sprite reset')
    else:
        # Older install without the temporary centering patch.
        legacy='''.entity-visual.anubis-visual .entity-body{left:-9px;top:-12px;width:120px;height:140px;object-fit:contain}'''
        if legacy not in t:
            insert_before(css_anchor,anubis_css,'Anubis CSS')

# The visible placement must be adjusted on the real screen container.
old_render='''   // A Naja precisa de offset no container real do render, nao apenas dentro do PNG/GIF.
   // Assim idle, caminhada, ataques, especiais e barras se movem juntos.
   const renderX=e.type==='naja'?sx+14*zoom:sx;
   const renderY=e.type==='naja'?sy+16*zoom:sy;
   const visualTop=renderY-dragonLift*zoom;'''
new_render='''   // Naja e Annubis usam offset no CONTAINER REAL do render.
   // No Annubis o X acompanha a direcao: o artwork tem margem assimetrica e,
   // ao espelhar, a compensacao tambem precisa espelhar.
   const anubisFace=(e.facing||1)>=0?1:-1;
   const renderX=e.type==='naja'?sx+14*zoom:e.type==='anubis'?sx+(16*anubisFace)*zoom:sx;
   const renderY=e.type==='naja'?sy+16*zoom:e.type==='anubis'?sy+18*zoom:sy;
   const visualTop=renderY-dragonLift*zoom;'''
replace_once(old_render,new_render,'Anubis real render position')

# ---------- Asset map ----------
asset_anchor="""  // Dragão Guerreiro — clã Guerreiros\n  dragonGround:'assets/dragon/dragao-guerreiro-parado.gif',"""
anubis_assets="""  // Annubis do Egito — clã Egito\n  anubisIdle:'assets/egypt/anubis/idle.gif',\n  anubisWalk:'assets/egypt/anubis/walk.gif',\n  anubisMeleeAttack:'assets/egypt/anubis/attack-melee.gif',\n  anubisRangedAttack:'assets/egypt/anubis/attack-ranged.gif',\n  anubisProjectile:'assets/egypt/anubis/projectile.gif',\n\n"""
insert_before(asset_anchor,anubis_assets,'Anubis assets')

# ---------- Cost / attack constants ----------
desired_costs="const WAR_UNIT_COSTS=Object.freeze({warrior:90,brownWarrior:450,king:500,golem:550,mage:550,dragon:450,naja:550,anubis:450});"
if desired_costs not in t:
    candidates=[
        "const WAR_UNIT_COSTS=Object.freeze({warrior:65,brownWarrior:450,king:400,golem:550,mage:550,dragon:450,naja:550});",
        "const WAR_UNIT_COSTS=Object.freeze({warrior:65,brownWarrior:450,king:400,golem:550,mage:550,dragon:450,naja:550,anubis:450});",
        "const WAR_UNIT_COSTS=Object.freeze({warrior:90,brownWarrior:450,king:500,golem:550,mage:550,dragon:450,naja:550});",
    ]
    found=[x for x in candidates if x in t]
    if len(found)!=1:
        raise SystemExit(f'Anubis cost: expected exactly 1 migration anchor, found {len(found)}')
    t=t.replace(found[0],desired_costs,1)
const_anchor="""const DRAGON_BURN_DURATION_MS=6000;\nconst gifRuntime=new Map();"""
const_new="""const DRAGON_BURN_DURATION_MS=6000;\n\n// ANNUBIS DO EGITO: híbrido terrestre. Corpo a corpo = normal da Guerreira Marrom;\n// disparo = projétil teleguiado do Dragão, +10 de dano e sem queimadura.\nlet ANUBIS_MELEE_DURATION=1800;\nlet ANUBIS_RANGED_DURATION=1800;\nconst ANUBIS_PROJECTILE_DAMAGE=DRAGON_FIREBALL_DAMAGE+10;\nconst ANUBIS_PROJECTILE_SPEED=DRAGON_FIREBALL_SPEED;\nconst gifRuntime=new Map();"""
replace_once(const_anchor,const_new,'Anubis combat constants')
replace_once(
    "let najaAttackAssetsReady=false;\nconst golemGifReadyKeys=new Set();",
    "let najaAttackAssetsReady=false;\nlet anubisAttackAssetsReady=false;\nconst golemGifReadyKeys=new Set();",
    'Anubis asset readiness flag'
)
replace_once(
    "const najaGifReadyKeys=new Set();",
    "const najaGifReadyKeys=new Set();\nconst anubisGifReadyKeys=new Set();",
    'Anubis asset readiness set'
)
replace_once(
    "'kingSpecial','kingPower','dragonTakeoff','dragonAttack','dragonFireball'];",
    "'kingSpecial','kingPower','dragonTakeoff','dragonAttack','dragonFireball','anubisMeleeAttack','anubisRangedAttack'];",
    'Anubis GIF preload keys'
)
insert_after(
    "     if(key==='dragonAttack')DRAGON_ATTACK_VISUAL_MS=validGifDuration(duration,DRAGON_ATTACK_VISUAL_MS);",
    "\n     if(key==='anubisMeleeAttack')ANUBIS_MELEE_DURATION=validGifDuration(duration,ANUBIS_MELEE_DURATION);\n     if(key==='anubisRangedAttack')ANUBIS_RANGED_DURATION=validGifDuration(duration,ANUBIS_RANGED_DURATION);",
    'Anubis GIF durations'
)
insert_after(
    "     if(key==='najaAttack'||key==='najaSpecial'||key==='najaSpecialFinal'){\n       najaGifReadyKeys.add(key);\n       if(najaGifReadyKeys.size===3)najaAttackAssetsReady=true;\n     }",
    "\n     if(key==='anubisMeleeAttack'||key==='anubisRangedAttack'){\n       anubisGifReadyKeys.add(key);\n       if(anubisGifReadyKeys.size===2)anubisAttackAssetsReady=true;\n     }",
    'Anubis GIF readiness'
)
insert_after("setTimeout(()=>{najaAttackAssetsReady=true},4000);","\nsetTimeout(()=>{anubisAttackAssetsReady=true},4000);",'Anubis readiness fallback')

# ---------- Entity state / spawn ----------
replace_once(
    " pendingBrownAttack:null,brownAttackKind:null,brownAttackSerial:0,brownNormalCount:0,\n pendingKingSpecial:null,kingSpecialSerial:0,kingNormalCount:0,",
    " pendingBrownAttack:null,brownAttackKind:null,brownAttackSerial:0,brownNormalCount:0,\n pendingAnubisAttack:null,anubisAttackKind:null,anubisAttackSerial:0,anubisNextShotAt:0,\n pendingKingSpecial:null,kingSpecialSerial:0,kingNormalCount:0,",
    'Anubis entity state'
)
spawn_anchor="""function spawnDragon(x,y,team,color){"""
spawn_anubis="""function spawnAnubis(x,y,team,color){\n const e=entityBase('anubis',x,y,team,color);\n e.clan='egypt';\n // Exatamente a mesma vida, escudo e velocidade-base do Dragão Guerreiro.\n e.hp=e.maxHp=150;e.shield=e.maxShield=50;e.damage=ANUBIS_PROJECTILE_DAMAGE;e.r=34;\n e.speed=state.mode==='war'?110*WAR_TROOP_SPEED_MULTIPLIER:110;\n e.attackCooldown=0;e.anubisAttackSerial=0;e.anubisNextShotAt=0;e.pendingAnubisAttack=null;\n state.entities.push(e);return e;\n}\n\n"""
insert_before(spawn_anchor,spawn_anubis,'spawnAnubis')

# ---------- Combat target type ----------
replace_once(
    "const REAL_COMBAT_TYPES=new Set(['warrior','brownWarrior','king','mage','golem','naja','dragon','enemy']);",
    "const REAL_COMBAT_TYPES=new Set(['warrior','brownWarrior','king','mage','golem','naja','anubis','dragon','enemy']);",
    'Anubis combat type'
)

# ---------- Death cleanup ----------
replace_once(
    " e.pendingBrownAttack=null;\n e.brownAttackKind=null;\n e.pendingKingSpecial=null;",
    " e.pendingBrownAttack=null;\n e.brownAttackKind=null;\n e.pendingAnubisAttack=null;\n e.anubisAttackKind=null;\n e.pendingKingSpecial=null;",
    'Anubis death cleanup'
)

# ---------- Anubis attack mechanics ----------
mechanics_anchor="""function distanceToSegment(px,py,ax,ay,bx,by){"""
anubis_mechanics=r'''function launchAnubisProjectile(e,target){
 if(!e?.alive||e.type!=='anubis'||!target?.alive)return false;
 const now=performance.now();
 const angle=Math.atan2(target.y-e.y,target.x-e.x);
 e.heading=angle;if(Math.abs(target.x-e.x)>4)e.facing=target.x<e.x?-1:1;
 const startX=e.x+Math.cos(angle)*40,startY=e.y-14+Math.sin(angle)*16;
 state.dragonProjectiles.push({
   id:'ap_'+(++state.dragonProjectileSeq),kind:'anubis',serial:e.anubisAttackSerial,
   x:startX,y:startY,vx:Math.cos(angle)*ANUBIS_PROJECTILE_SPEED,vy:Math.sin(angle)*ANUBIS_PROJECTILE_SPEED,
   speed:ANUBIS_PROJECTILE_SPEED,damage:ANUBIS_PROJECTILE_DAMAGE,burn:false,
   targetId:target.id,targetX:target.x,targetY:target.y,team:e.team,sourceId:e.id,createdAt:now,expireAt:now+4500
 });
 addWarGoalProgress(e.team,'ranged');
 return true;
}

function startAnubisAttack(e,kind,target){
 if(!e?.alive||e.type!=='anubis'||e.pendingAnubisAttack||e.attackCooldown>0||e.knockTime>0||!anubisAttackAssetsReady)return false;
 if(!isRealCombatTarget(target)||target===e||target.team===e.team||!canEngageTarget(e,target))return false;
 const d=dist(e,target);
 const flyingDragon=target.type==='dragon'&&target.dragonFlightState==='flying';
 if(kind==='melee'&&(d>108||flyingDragon))return false;
 if(kind==='ranged'&&d>310)return false;
 const now=performance.now(),angle=Math.atan2(target.y-e.y,target.x-e.x);
 e.heading=angle;if(Math.abs(target.x-e.x)>4)e.facing=target.x<e.x?-1:1;
 e.moving=false;e.lastAttackAt=now;e.lastCombatAt=now;
 e.anubisAttackKind=kind;e.anubisAttackSerial=(Number(e.anubisAttackSerial)||0)+1;
 if(kind==='melee'){
   const duration=ANUBIS_MELEE_DURATION;
   const hit1Delay=Math.min(duration-260,Math.max(280,duration*.32));
   const hit2Delay=Math.min(duration-120,Math.max(hit1Delay+180,duration*.62));
   e.attackCooldown=duration/1000+.12;
   e.pendingAnubisAttack={kind,serial:e.anubisAttackSerial,targetId:target.id,originX:e.x,originY:e.y,angle,duration,startedAt:now,
     hit1At:now+hit1Delay,hit2At:now+hit2Delay,endAt:now+duration,hit1Done:false,hit2Done:false};
 }else{
   const duration=ANUBIS_RANGED_DURATION;
   e.attackCooldown=Math.max(duration/1000+.12,DRAGON_SHOT_COOLDOWN_MS/1000);
   e.anubisNextShotAt=now+DRAGON_SHOT_COOLDOWN_MS;
   e.pendingAnubisAttack={kind,serial:e.anubisAttackSerial,targetId:target.id,originX:e.x,originY:e.y,angle,duration,startedAt:now,endAt:now+duration};
   launchAnubisProjectile(e,target);
 }
 return true;
}

function updateAnubisAttackState(e,now){
 const p=e.pendingAnubisAttack;if(!p)return;
 e.moving=false;
 if(p.kind==='melee'){
   if(!p.hit1Done&&now>=Number(p.hit1At||Infinity))brownNormalHit(e,p,BROWN_NORMAL_DAMAGE_1,'hit1Done');
   if(!p.hit2Done&&now>=Number(p.hit2At||Infinity))brownNormalHit(e,p,BROWN_NORMAL_DAMAGE_2,'hit2Done');
 }
 if(now>=Number(p.endAt||0)){
   e.pendingAnubisAttack=null;e.anubisAttackKind=null;e.target=null;
 }
}

function aiFightAnubis(e,dt,forcedTeam,preparedCandidates=null){
 if(!e.alive||e.knockTime>0){e.moving=false;return}
 if(e.pendingAnubisAttack){e.moving=false;return}
 const candidates=preparedCandidates||state.entities;
 const target=nearestEngageableCandidate(e,candidates,forcedTeam,false);
 if(!target){e.moving=false;e.target=null;return}
 e.target=target;
 const dx=target.x-e.x,dy=target.y-e.y,d=Math.hypot(dx,dy)||1;
 e.heading=Math.atan2(dy,dx);if(Math.abs(dx)>4)e.facing=dx<0?-1:1;
 const now=performance.now();
 const flyingDragon=target.type==='dragon'&&target.dragonFlightState==='flying';

 // Contra Dragão voando, só usa o projétil; contra tropas terrestres prefere
 // o golpe normal da Guerreira Marrom quando consegue encostar.
 if(flyingDragon){
   if(d<=285&&now>=Number(e.anubisNextShotAt||0)&&startAnubisAttack(e,'ranged',target))return;
   if(d>285){e.x+=dx/d*e.speed*dt;e.y+=dy/d*e.speed*dt;e.moving=true}else e.moving=false;
 }else if(d<=92){
   if(startAnubisAttack(e,'melee',target))return;
   e.moving=false;
 }else if(d<175){
   e.x+=dx/d*e.speed*dt;e.y+=dy/d*e.speed*dt;e.moving=true;
 }else if(d<=285){
   if(now>=Number(e.anubisNextShotAt||0)&&startAnubisAttack(e,'ranged',target))return;
   e.moving=false;
 }else{
   e.x+=dx/d*e.speed*dt;e.y+=dy/d*e.speed*dt;e.moving=true;
 }
 e.x=clamp(e.x,40,state.world.w-40);e.y=clamp(e.y,40,state.world.h-40);
}

'''
insert_before(mechanics_anchor,anubis_mechanics,'Anubis combat mechanics')

# Generic attack path must not also attack Anubis.
replace_once(
    " if(e.type==='golem'||e.type==='naja'||e.type==='mage'||e.type==='brownWarrior')return;",
    " if(e.type==='golem'||e.type==='naja'||e.type==='mage'||e.type==='brownWarrior'||e.type==='anubis')return;",
    'Anubis generic attack exclusion'
)

# ---------- Dragon projectile generalized for Dragon + Anubis ----------
replace_once(
    "state.dragonProjectiles.push({id:'df_'+(++state.dragonProjectileSeq),serial:e.dragonAttackSerial,x:startX,y:startY,vx:Math.cos(angle)*DRAGON_FIREBALL_SPEED,vy:Math.sin(angle)*DRAGON_FIREBALL_SPEED,targetId:target.id,targetX:target.x,targetY:target.y,team:e.team,sourceId:e.id,createdAt:now,expireAt:now+4500});",
    "state.dragonProjectiles.push({id:'df_'+(++state.dragonProjectileSeq),kind:'dragon',serial:e.dragonAttackSerial,x:startX,y:startY,vx:Math.cos(angle)*DRAGON_FIREBALL_SPEED,vy:Math.sin(angle)*DRAGON_FIREBALL_SPEED,speed:DRAGON_FIREBALL_SPEED,damage:DRAGON_FIREBALL_DAMAGE,burn:true,targetId:target.id,targetX:target.x,targetY:target.y,team:e.team,sourceId:e.id,createdAt:now,expireAt:now+4500});",
    'Dragon projectile metadata'
)
replace_once(
    "const dx=tx-p.x,dy=ty-p.y,d=Math.hypot(dx,dy)||1,step=DRAGON_FIREBALL_SPEED*dt;\n             p.vx=dx/d*DRAGON_FIREBALL_SPEED;p.vy=dy/d*DRAGON_FIREBALL_SPEED;",
    "const projectileSpeed=Number(p.speed)||DRAGON_FIREBALL_SPEED;\n             const dx=tx-p.x,dy=ty-p.y,d=Math.hypot(dx,dy)||1,step=projectileSpeed*dt;\n             p.vx=dx/d*projectileSpeed;p.vy=dy/d*projectileSpeed;",
    'Generic projectile speed'
)
replace_once(
    "const source=entityById.get(p.sourceId)||{id:p.sourceId,type:'dragon',x:p.x,y:p.y,heading:0,lastCombatAt:0};\n                 applyCombatHit(target,source,DRAGON_FIREBALL_DAMAGE,{knockForce:105,knockTime:.06,tilt:6});\n                 if(target.alive)igniteDragonBurn(target,source);",
    "const projectileType=p.kind==='anubis'?'anubis':'dragon';\n                 const source=entityById.get(p.sourceId)||{id:p.sourceId,type:projectileType,team:p.team,x:p.x,y:p.y,heading:0,lastCombatAt:0};\n                 const impactDamage=Number.isFinite(Number(p.damage))?Number(p.damage):DRAGON_FIREBALL_DAMAGE;\n                 applyCombatHit(target,source,impactDamage,{knockForce:105,knockTime:.06,tilt:6,allowFlying:true});\n                 if(p.burn!==false&&target.alive)igniteDragonBurn(target,source);",
    'Anubis projectile impact without burn'
)

# ---------- AI dispatch / per-frame state ----------
replace_once(
    " if(e.type==='naja'){aiFightNaja(e,dt,forcedTeam,preparedCandidates);return;}\n if(e.type==='golem')",
    " if(e.type==='naja'){aiFightNaja(e,dt,forcedTeam,preparedCandidates);return;}\n if(e.type==='anubis'){aiFightAnubis(e,dt,forcedTeam,preparedCandidates);return;}\n if(e.type==='golem')",
    'Anubis AI dispatch'
)
replace_once(
    "   if(e.type==='brownWarrior' && e.pendingBrownAttack){\n     updateBrownWarriorAttackState(e,now);\n   }\n   if(e.type==='mage'",
    "   if(e.type==='brownWarrior' && e.pendingBrownAttack){\n     updateBrownWarriorAttackState(e,now);\n   }\n   if(e.type==='anubis' && e.pendingAnubisAttack){\n     updateAnubisAttackState(e,now);\n   }\n   if(e.type==='mage'",
    'Anubis update state'
)

# ---------- Network entity serialization ----------
serialize_anchor=""" }else if(e.type==='mage'){\n   out.mageAttackKind=e.mageAttackKind??null;"""
anubis_serialize=r''' }else if(e.type==='anubis'){
   out.anubisAttackKind=e.anubisAttackKind??null;
   out.anubisAttackSerial=Number(e.anubisAttackSerial)||0;
   if(e.pendingAnubisAttack){
     const p=e.pendingAnubisAttack;
     out.pendingAnubisAttack={
       kind:p.kind,serial:Number(p.serial)||Number(e.anubisAttackSerial)||0,targetId:p.targetId??null,
       originX:Number.isFinite(Number(p.originX))?Number(p.originX):e.x,
       originY:Number.isFinite(Number(p.originY))?Number(p.originY):e.y,
       angle:Number.isFinite(Number(p.angle))?Number(p.angle):0,
       duration:Number(p.duration)||(p.kind==='melee'?ANUBIS_MELEE_DURATION:ANUBIS_RANGED_DURATION),
       remainingMs:Math.max(0,Number(p.endAt)-now),
       hit1RemainingMs:p.hit1At?Math.max(0,Number(p.hit1At)-now):0,
       hit2RemainingMs:p.hit2At?Math.max(0,Number(p.hit2At)-now):0,
       hit1Done:!!p.hit1Done,hit2Done:!!p.hit2Done
     };
   }
'''
insert_before(serialize_anchor,anubis_serialize,'Anubis network serialization')

# Projectile metadata over the network.
replace_once(
    "   targetX:p.targetX,targetY:p.targetY,team:p.team,sourceId:p.sourceId,serial:p.serial||0\n }));",
    "   targetX:p.targetX,targetY:p.targetY,team:p.team,sourceId:p.sourceId,serial:p.serial||0,\n   kind:p.kind||'dragon',damage:Number(p.damage)||DRAGON_FIREBALL_DAMAGE,burn:p.burn!==false,speed:Number(p.speed)||DRAGON_FIREBALL_SPEED\n }));",
    'Projectile network metadata'
)

# Rebuild Anubis attack timers on non-host clients.
remote_anchor="""     if(!out.pendingBrownAttack)out.brownAttackKind=null;\n     if(out.dragonTakeoffRemainingMs!=null){"""
remote_anubis=r'''     if(out.pendingAnubisAttack?.remainingMs!=null){
       const p=out.pendingAnubisAttack;
       const serial=Number(p.serial)||Number(out.anubisAttackSerial)||0;
       const duration=Number(p.duration)||(p.kind==='melee'?ANUBIS_MELEE_DURATION:ANUBIS_RANGED_DURATION);
       const remaining=Math.max(0,Number(p.remainingMs)||0);
       const oldPending=old?.pendingAnubisAttack;
       const sameSerial=!!oldPending&&Number(oldPending.serial)===serial&&oldPending.kind===p.kind;
       if(remaining<=0){
         out.pendingAnubisAttack=null;out.anubisAttackKind=null;
       }else if(sameSerial&&Number.isFinite(Number(oldPending.endAt))){
         const rebuilt={...p,serial,duration,
           startedAt:Number(oldPending.startedAt)||localNow-Math.max(0,duration-remaining),
           endAt:Math.min(Number(oldPending.endAt),localNow+remaining)
         };
         if(p.kind==='melee'){
           rebuilt.hit1At=p.hit1Done?localNow:(Number(oldPending.hit1At)||localNow+Math.max(0,Number(p.hit1RemainingMs)||0));
           rebuilt.hit2At=p.hit2Done?localNow:(Number(oldPending.hit2At)||localNow+Math.max(0,Number(p.hit2RemainingMs)||0));
           rebuilt.hit1Done=!!(oldPending.hit1Done||p.hit1Done);rebuilt.hit2Done=!!(oldPending.hit2Done||p.hit2Done);
         }
         out.pendingAnubisAttack=rebuilt;
       }else{
         const rebuilt={...p,serial,duration,startedAt:localNow-Math.max(0,duration-remaining),endAt:localNow+remaining};
         if(p.kind==='melee'){
           rebuilt.hit1At=localNow+Math.max(0,Number(p.hit1RemainingMs)||0);
           rebuilt.hit2At=localNow+Math.max(0,Number(p.hit2RemainingMs)||0);
         }
         out.pendingAnubisAttack=rebuilt;
       }
     }
     if(!out.pendingAnubisAttack)out.anubisAttackKind=null;
'''
insert_before(remote_anchor,remote_anubis,'Anubis remote attack reconstruction')

# ---------- Online command handling ----------
insert_after(
    "     if(clan==='egypt'&&cmd.type==='buy-egypt-naja')buyEgyptNajaForPlayer(p,false);",
    "\n     if(clan==='egypt'&&cmd.type==='buy-egypt-anubis')buyEgyptAnubisForPlayer(p,false);",
    'Anubis host command'
)

# ---------- Purchase / shop handlers ----------
replace_once(
    "const allowed=clan==='egypt'?new Set(['buy-egypt-warrior','buy-egypt-mage','buy-egypt-naja']):",
    "const allowed=clan==='egypt'?new Set(['buy-egypt-warrior','buy-egypt-mage','buy-egypt-naja','buy-egypt-anubis']):",
    'Anubis purchase allowance'
)
insert_after(
    "   if(type==='buy-egypt-naja')buyEgyptNajaForPlayer(p,false);",
    "\n   if(type==='buy-egypt-anubis')buyEgyptAnubisForPlayer(p,false);",
    'Anubis local purchase dispatch'
)
insert_after(
    "$('#buyEgyptNaja').onclick=()=>requestWarPurchase('buy-egypt-naja');",
    "\n$('#buyEgyptAnubis').onclick=()=>requestWarPurchase('buy-egypt-anubis');",
    'Anubis shop click'
)
buy_anchor="""function buyDragonForPlayer(p,bot){"""
buy_anubis="""function buyEgyptAnubisForPlayer(p,bot){\n if(normalizeClan(p.clan)!=='egypt')return false;\n const cost=WAR_UNIT_COSTS.anubis;if(p.gems<cost)return false;p.gems-=cost;p.troops++;\n const t=p.territory,angle=Math.random()*Math.PI*2,r=Math.random()*82;\n spawnAnubis(t.x+Math.cos(angle)*r,t.y+Math.sin(angle)*r,p.id,p.color);\n return true;\n}\n"""
insert_before(buy_anchor,buy_anubis,'Anubis buy function')

# ---------- Bot composition ----------
replace_once(
    "const out={warrior:0,brownWarrior:0,king:0,mage:0,golem:0,dragon:0,naja:0};",
    "const out={warrior:0,brownWarrior:0,king:0,mage:0,golem:0,dragon:0,naja:0,anubis:0};",
    'Anubis own composition'
)
# There are two identical composition declarations; replace the remaining one.
replace_once(
    "const out={warrior:0,brownWarrior:0,king:0,mage:0,golem:0,dragon:0,naja:0};",
    "const out={warrior:0,brownWarrior:0,king:0,mage:0,golem:0,dragon:0,naja:0,anubis:0};",
    'Anubis enemy composition'
)
insert_after("   if(p.gems>=WAR_UNIT_COSTS.naja)types.push('naja');","\n   if(p.gems>=WAR_UNIT_COSTS.anubis)types.push('anubis');",'Anubis bot affordability')
replace_once(
    "const enemyTotal=enemy.warrior+enemy.brownWarrior+enemy.king+enemy.mage+enemy.golem+enemy.dragon+enemy.naja;",
    "const enemyTotal=enemy.warrior+enemy.brownWarrior+enemy.king+enemy.mage+enemy.golem+enemy.dragon+enemy.naja+enemy.anubis;",
    'Anubis enemy total'
)
replace_once(
    "const score={warrior:1,brownWarrior:1,king:1,mage:1,golem:1,dragon:1,naja:1};",
    "const score={warrior:1,brownWarrior:1,king:1,mage:1,golem:1,dragon:1,naja:1,anubis:1};",
    'Anubis bot score'
)
insert_after(
    " score.naja+=(enemy.warrior+enemy.brownWarrior+enemy.king)*1.30+enemy.mage*.55+enemy.golem*.35+enemy.naja*.45;",
    "\n score.anubis+=enemy.dragon*1.75+enemy.golem*1.15+enemy.mage*.70+(enemy.warrior+enemy.brownWarrior+enemy.king)*.65+enemy.anubis*.45;",
    'Anubis bot matchup score'
)
insert_after("   if(type==='naja')return buyEgyptNajaForPlayer(p,true);","\n   if(type==='anubis')return buyEgyptAnubisForPlayer(p,true);",'Anubis bot purchase')

# ---------- Rendering: node, GIF states, scale ----------
node_anchor=""" }else if(e.type==='mage'){\n   el.classList.add('mage-visual');"""
anubis_node=r''' }else if(e.type==='anubis'){
   el.classList.add('anubis-visual','egypt-unit');
   el.innerHTML=`
     <div class="entity-facing">
       <img class="entity-body entity-idle active-sprite" data-asset-key="anubisIdle" src="${ASSETS.anubisIdle}" draggable="false" style="opacity:1">
       <img class="entity-body entity-walk" data-asset-key="anubisWalk" src="${ASSETS.anubisWalk}" draggable="false" style="opacity:0">
       <img class="entity-body entity-anubis-melee" data-asset-key="anubisMeleeAttack" draggable="false" style="opacity:0">
       <img class="entity-body entity-anubis-ranged" data-asset-key="anubisRangedAttack" draggable="false" style="opacity:0">
     </div>
     <div class="entity-weapon-facing"></div>
     <div class="entity-bars">
       <div class="hp-bg"><div class="hp-fill"></div></div>
       <div class="shield-bg"><div class="shield-fill"></div></div>
     </div>`;
'''
insert_before(node_anchor,anubis_node,'Anubis entity DOM')
insert_after(" el._najaSpecialFinal=el.querySelector('.entity-naja-special-final');","\n el._anubisMelee=el.querySelector('.entity-anubis-melee');\n el._anubisRanged=el.querySelector('.entity-anubis-ranged');",'Anubis DOM references')
insert_after(" el.dataset.najaEmergeSerial='-1';","\n el.dataset.anubisAttackSerial='-1';",'Anubis render serial')
insert_after(
    " else if(e.type==='naja')el._gifKeys={idle:'najaIdle',walk:'najaWalk',attack:'najaAttack',special:'najaSpecial',emerge:'najaSpecialFinal'};",
    "\n else if(e.type==='anubis')el._gifKeys={idle:'anubisIdle',walk:'anubisWalk',attack:'anubisMeleeAttack',anubisRanged:'anubisRangedAttack'};",
    'Anubis GIF map'
)
replace_once(
    "[el._idle,el._walk,el._brownAttack,el._brownSpecial,el._golemAttack,el._golemSpecial,el._najaAttack,el._najaSpecial,el._najaSpecialFinal,el._mageSpecial,el._kingSpecial,el._kingPower,el._dragonGround,el._dragonTakeoff,el._dragonFly,el._dragonAttack]",
    "[el._idle,el._walk,el._brownAttack,el._brownSpecial,el._golemAttack,el._golemSpecial,el._najaAttack,el._najaSpecial,el._najaSpecialFinal,el._anubisMelee,el._anubisRanged,el._mageSpecial,el._kingSpecial,el._kingPower,el._dragonGround,el._dragonTakeoff,el._dragonFly,el._dragonAttack]",
    'Anubis asset error handling list'
)
replace_once(
    "const transientState=(img===el._golemAttack||img===el._brownAttack||img===el._najaAttack)?'attack':",
    "const transientState=(img===el._golemAttack||img===el._brownAttack||img===el._najaAttack||img===el._anubisMelee)?'attack':\n         (img===el._anubisRanged?'anubisRanged':",
    'Anubis transient state start'
)
# Close the parenthesis added above at the end of the transient ternary.
replace_once(
    "(img===el._najaSpecialFinal?'emerge':(img===el._golemSpecial||img===el._najaSpecial||img===el._brownSpecial||img===el._mageSpecial||img===el._kingSpecial||img===el._kingPower?'special':(img===el._dragonTakeoff?'takeoff':img===el._dragonAttack?'dragonAttack':null)));",
    "(img===el._najaSpecialFinal?'emerge':(img===el._golemSpecial||img===el._najaSpecial||img===el._brownSpecial||img===el._mageSpecial||img===el._kingSpecial||img===el._kingPower?'special':(img===el._dragonTakeoff?'takeoff':img===el._dragonAttack?'dragonAttack':null))));",
    'Anubis transient state close'
)
replace_once(
    "[el._idle,'idle'],[el._walk,'walk'],[el._brownAttack,'attack'],[el._golemAttack,'attack'],[el._najaAttack,'attack'],",
    "[el._idle,'idle'],[el._walk,'walk'],[el._brownAttack,'attack'],[el._golemAttack,'attack'],[el._najaAttack,'attack'],[el._anubisMelee,'attack'],[el._anubisRanged,'anubisRanged'],",
    'Anubis sprite states'
)
replace_once(
    "if(previous==='attack'&&desired!=='attack'){stopGif(el._brownAttack);stopGif(el._golemAttack);stopGif(el._najaAttack)}",
    "if(previous==='attack'&&desired!=='attack'){stopGif(el._brownAttack);stopGif(el._golemAttack);stopGif(el._najaAttack);stopGif(el._anubisMelee)}\n   if(previous==='anubisRanged'&&desired!=='anubisRanged')stopGif(el._anubisRanged);",
    'Anubis GIF stop states'
)
replace_once(
    "const typeScale=e.type==='golem'?1.34:e.type==='naja'?1.75:",
    "const typeScale=e.type==='golem'?1.34:e.type==='anubis'?1.34:e.type==='naja'?1.75:",
    'Anubis Golem visual scale'
)
# Offscreen attack reset.
insert_before(
    "     }else if(e.type==='golem'&&!activeGolemPending(e,localNow)&&",
    "     }else if(e.type==='anubis'&&!(e.pendingAnubisAttack&&e.pendingAnubisAttack.endAt>localNow)&&\n        (el.dataset.anim==='attack'||el.dataset.anim==='anubisRanged')){\n       setEntitySpriteState(el,e.moving?'walk':'idle');\n",
    'Anubis offscreen reset'
)
# Active Anubis animation branch.
render_anchor="""   }else if(e.type==='golem'){\n     const pending=activeGolemPending(e,localNow);"""
anubis_render=r'''   }else if(e.type==='anubis'){
     const p=e.pendingAnubisAttack;
     const active=!!p&&Number(p.endAt)>localNow;
     const desired=active?(p.kind==='ranged'?'anubisRanged':'attack'):(visualMoving?'walk':'idle');
     setEntitySpriteState(el,desired);
     const serial=Number(p?.serial||e.anubisAttackSerial)||0;
     if(active&&serial>0&&el.dataset.anubisAttackSerial!==String(serial)){
       el.dataset.anubisAttackSerial=String(serial);
       if(p.kind==='ranged')restartGif(el._anubisRanged,'anubisRangedAttack',serial);
       else restartGif(el._anubisMelee,'anubisMeleeAttack',serial);
     }
'''
insert_before(render_anchor,anubis_render,'Anubis render state')
replace_once(
    "entity.pendingBrownAttack||entity.pendingGolemAttack||entity.pendingNajaAttack||entity.pendingMageAttack",
    "entity.pendingBrownAttack||entity.pendingGolemAttack||entity.pendingNajaAttack||entity.pendingAnubisAttack||entity.pendingMageAttack",
    'Anubis DOM retention'
)

# ---------- Projectile render asset selection ----------
replace_once("function acquireDragonProjectileNode(layer){","function acquireDragonProjectileNode(layer,assetKey='dragonFireball'){",'Dynamic projectile function signature')
replace_once(
    "   img.dataset.assetKey='dragonFireball';\n }\n if(img._poolGifSuspendTimer){clearTimeout(img._poolGifSuspendTimer);img._poolGifSuspendTimer=null}\n if(!img.hasAttribute('src'))img.src=ASSETS.dragonFireball;",
    "   img.dataset.assetKey=assetKey;\n }\n if(img._poolGifSuspendTimer){clearTimeout(img._poolGifSuspendTimer);img._poolGifSuspendTimer=null}\n if(img.dataset.assetKey!==assetKey){stopGif(img);img.dataset.assetKey=assetKey}\n if(!img.hasAttribute('src'))img.src=ASSETS[assetKey];",
    'Dynamic projectile asset acquisition'
)
replace_once(
    "active.add(p.id);let img=dragonProjectileNodes.get(p.id);\n             if(!img){img=acquireDragonProjectileNode(layer);dragonProjectileNodes.set(p.id,img)}",
    "active.add(p.id);let img=dragonProjectileNodes.get(p.id);\n             const projectileAssetKey=p.kind==='anubis'?'anubisProjectile':'dragonFireball';\n             if(!img){img=acquireDragonProjectileNode(layer,projectileAssetKey);dragonProjectileNodes.set(p.id,img)}\n             else if(img.dataset.assetKey!==projectileAssetKey){stopGif(img);img.dataset.assetKey=projectileAssetKey;img.src=ASSETS[projectileAssetKey]}",
    'Anubis projectile visual asset'
)

# ---------- HUD / button cache ----------
replace_once(
    "buyEgyptMagePerfEl=$('#buyEgyptMage'),buyEgyptNajaPerfEl=$('#buyEgyptNaja');",
    "buyEgyptMagePerfEl=$('#buyEgyptMage'),buyEgyptNajaPerfEl=$('#buyEgyptNaja'),buyEgyptAnubisPerfEl=$('#buyEgyptAnubis');",
    'Anubis HUD button cache'
)
insert_after(
    "    perfSetDisabled(buyEgyptNajaPerfEl,state.phase!=='prep'||gems<WAR_UNIT_COSTS.naja);",
    "\n    perfSetDisabled(buyEgyptAnubisPerfEl,state.phase!=='prep'||gems<WAR_UNIT_COSTS.anubis);",
    'Anubis HUD affordability'
)

# ---------- Bot score/purchases and command types are already above ----------

p.write_text(t,encoding='utf-8')

required=[
    'id="buyEgyptAnubis"',
    'assets/egypt/anubis/card.png',
    "anubisIdle:'assets/egypt/anubis/idle.gif'",
    "anubisProjectile:'assets/egypt/anubis/projectile.gif'",
    'anubis:450',
    'const ANUBIS_PROJECTILE_DAMAGE=DRAGON_FIREBALL_DAMAGE+10;',
    "function spawnAnubis(",
    "e.hp=e.maxHp=150;e.shield=e.maxShield=50;e.damage=ANUBIS_PROJECTILE_DAMAGE;e.r=34;",
    "e.speed=state.mode==='war'?110*WAR_TROOP_SPEED_MULTIPLIER:110;",
    "function startAnubisAttack(",
    "function aiFightAnubis(",
    "function launchAnubisProjectile(",
    "kind:'anubis'",
    'burn:false',
    "if(p.burn!==false&&target.alive)igniteDragonBurn(target,source);",
    "BROWN_NORMAL_DAMAGE_1",
    "BROWN_NORMAL_DAMAGE_2",
    "pendingAnubisAttack",
    "buy-egypt-anubis",
    "function buyEgyptAnubisForPlayer(",
    "e.type==='anubis'?1.34",
    "entity-anubis-melee",
    "entity-anubis-ranged",
    "p.kind==='anubis'?'anubisProjectile':'dragonFireball'",
    "buyEgyptAnubisPerfEl",
]
missing=[x for x in required if x not in t]
if missing:
    raise SystemExit('Missing Anubis integration markers: '+repr(missing))

if t.count('id="buyEgyptAnubis"')!=1:
    raise SystemExit('Duplicate Anubis shop card')
if t.count('function spawnAnubis(')!=1 or t.count('function aiFightAnubis(')!=1:
    raise SystemExit('Duplicate Anubis logic')

print('Egypt Annubis integration applied.')
