from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")


def replace_once(old: str, new: str, label: str):
    global text
    if old in text:
        text = text.replace(old, new, 1)
        return
    if new in text:
        return
    raise SystemExit(f"Trecho não encontrado: {label}")


def insert_after_once(marker: str, addition: str, label: str):
    global text
    target = marker + addition
    if target in text:
        return
    if marker not in text:
        raise SystemExit(f"Marcador não encontrado: {label}")
    text = text.replace(marker, target, 1)


def replace_section(start_marker: str, end_marker: str, replacement: str, label: str):
    global text
    if replacement in text:
        return
    start = text.find(start_marker)
    if start < 0:
        raise SystemExit(f"Início não encontrado: {label}")
    end = text.find(end_marker, start)
    if end < 0:
        raise SystemExit(f"Fim não encontrado: {label}")
    text = text[:start] + replacement + text[end:]


# =========================================================
# FASE 1 — REMOVER REFLOW FORÇADO DA CURA
# =========================================================
insert_after_once(
    ".hp-fill.heal-pulse{animation:hpHealPulse .72s ease-out}\n"
    "@keyframes hpHealPulse{0%{filter:brightness(1);box-shadow:none}35%{filter:brightness(1.75);box-shadow:0 0 8px rgba(90,255,150,.95)}100%{filter:brightness(1);box-shadow:none}}\n",
    ".hp-fill.heal-pulse-alt{animation:hpHealPulseAlt .72s ease-out}\n"
    "@keyframes hpHealPulseAlt{0%{filter:brightness(1);box-shadow:none}35%{filter:brightness(1.75);box-shadow:0 0 8px rgba(90,255,150,.95)}100%{filter:brightness(1);box-shadow:none}}\n",
    "animação alternativa da barra de cura",
)

insert_after_once(
    ".entity-facing.round-heal{\n"
    "  animation:roundHeal .95s ease-out;\n"
    "}\n"
    "@keyframes roundHeal{\n"
    "  0%{filter:none}\n"
    "  25%{filter:brightness(1.55) saturate(1.25) drop-shadow(0 0 4px rgba(90,255,150,.25))}\n"
    "  55%{filter:brightness(1.25) saturate(1.12) drop-shadow(0 0 13px rgba(90,255,150,.85))}\n"
    "  100%{filter:none}\n"
    "}\n",
    ".entity-facing.round-heal-alt{\n"
    "  animation:roundHealAlt .95s ease-out;\n"
    "}\n"
    "@keyframes roundHealAlt{\n"
    "  0%{filter:none}\n"
    "  25%{filter:brightness(1.55) saturate(1.25) drop-shadow(0 0 4px rgba(90,255,150,.25))}\n"
    "  55%{filter:brightness(1.25) saturate(1.12) drop-shadow(0 0 13px rgba(90,255,150,.85))}\n"
    "  100%{filter:none}\n"
    "}\n",
    "animação alternativa de cura do corpo",
)

replace_once(
    """   if((el._lastRegenSerial||0)!==(e.regenSerial||0)){
     el._lastRegenSerial=e.regenSerial||0;
     if(e.regenSerial>0){
       el._facing.classList.remove('round-heal');
       el._hp?.classList.remove('heal-pulse');
       void el._facing.offsetWidth;
       void el._hp?.offsetWidth;
       el._facing.classList.add('round-heal');
       el._hp?.classList.add('heal-pulse');
       setTimeout(()=>{el._facing?.classList.remove('round-heal');el._hp?.classList.remove('heal-pulse')},1000);
     }
   }
""",
    """   if((el._lastRegenSerial||0)!==(e.regenSerial||0)){
     el._lastRegenSerial=e.regenSerial||0;
     if(e.regenSerial>0){
       const alt=((e.regenSerial||0)&1)===0;
       const faceClass=alt?'round-heal-alt':'round-heal';
       const hpClass=alt?'heal-pulse-alt':'heal-pulse';
       const regenToken=(el._regenAnimToken||0)+1;el._regenAnimToken=regenToken;
       el._facing.classList.remove('round-heal','round-heal-alt');
       el._hp?.classList.remove('heal-pulse','heal-pulse-alt');
       el._facing.classList.add(faceClass);
       el._hp?.classList.add(hpClass);
       setTimeout(()=>{
         if(el._regenAnimToken!==regenToken)return;
         el._facing?.classList.remove(faceClass);
         el._hp?.classList.remove(hpClass);
       },1000);
     }
   }
""",
    "cura sem forced reflow",
)


# =========================================================
# FASE 1 — MENOS ESCRITAS DOM REDUNDANTES NAS PEDRAS
# =========================================================
replace_once(
    """function acquireGolemRockNode(){
 let rock=golemRockPool.pop();
 if(!rock){rock=document.createElement('img');rock.className='golem-rock-fragment';rock.src=ASSETS.golemRocks}
 if(!rock.hasAttribute('src'))rock.src=ASSETS.golemRocks;
 if(rock.parentElement!==combatFxLayer)combatFxLayer?.appendChild(rock);
 rock.style.visibility='visible';
 return rock;
}
function recycleGolemRockNode(rock){
 if(!rock)return;
 rock.style.visibility='hidden';
 if(golemRockPool.length<MAX_GOLEM_ROCK_POOL)golemRockPool.push(rock);
 else rock.remove();
}
""",
    """function acquireGolemRockNode(){
 let rock=golemRockPool.pop();
 if(!rock){rock=document.createElement('img');rock.className='golem-rock-fragment';rock.src=ASSETS.golemRocks}
 if(!rock.hasAttribute('src'))rock.src=ASSETS.golemRocks;
 if(rock.parentElement!==combatFxLayer)combatFxLayer?.appendChild(rock);
 if(rock._rockVisible!==true){rock._rockVisible=true;rock.style.visibility='visible'}
 return rock;
}
function recycleGolemRockNode(rock){
 if(!rock)return;
 if(rock._rockVisible!==false){rock._rockVisible=false;rock.style.visibility='hidden'}
 rock._rockPxSize=NaN;
 if(golemRockPool.length<MAX_GOLEM_ROCK_POOL)golemRockPool.push(rock);
 else rock.remove();
}
""",
    "cache visual das pedras",
)

replace_once(
    """   if(!onScreen){
     if(fx.el)fx.el.style.visibility='hidden';
     continue;
   }
   let el=fx.el;
   if(!el){
     el=acquireGolemRockNode();
     fx.el=el;
   }
   el.style.visibility='visible';
   const pxSize=fx.size*zoom;
   el.style.width=pxSize+'px';
   el.style.height=pxSize+'px';
""",
    """   if(!onScreen){
     if(fx.el&&fx.el._rockVisible!==false){fx.el._rockVisible=false;fx.el.style.visibility='hidden'}
     continue;
   }
   let el=fx.el;
   if(!el){
     el=acquireGolemRockNode();
     fx.el=el;
   }else if(el._rockVisible!==true){
     el._rockVisible=true;el.style.visibility='visible';
   }
   const pxSize=fx.size*zoom;
   if(el._rockPxSize!==pxSize){
     el._rockPxSize=pxSize;
     el.style.width=pxSize+'px';
     el.style.height=pxSize+'px';
   }
""",
    "menos estilos repetidos nas pedras",
)


# =========================================================
# FASE 2 — CACHE DE DECISÃO DA IA + GRID REUTILIZÁVEL
# =========================================================
insert_after_once(
    "const WAR_AI_LOCAL_RADIUS=560;\n",
    "const WAR_AI_DECISION_INTERVAL_MS=70;\n",
    "intervalo de decisão da IA",
)

insert_after_once(
    "const warEntityById=new Map();\n",
    """const warCombatGrid=new Map();
const warCandidateCache=new Map();
const warBurningEntities=new Set();
const deadTargetIds=new Set();
""",
    "estruturas reutilizáveis da Guerra",
)

replace_section(
    "function buildWarAIGrid(living){",
    "function nearestEnemyFromWarGrid",
    """function buildWarAIGrid(living){
 const cells=warCombatGrid;cells.clear();
 for(const e of living){
   const cx=Math.floor(e.x/WAR_AI_GRID_CELL),cy=Math.floor(e.y/WAR_AI_GRID_CELL),key=cx+','+cy;
   let bucket=cells.get(key);if(!bucket){bucket=[];cells.set(key,bucket)}bucket.push(e);
 }
 return cells;
}

// Itera somente células que podem conter o efeito. O +1 de margem preserva
// acertos mesmo que as entidades tenham se movido alguns pixels após a grade
// ter sido montada no início do frame; a hitbox final continua exatamente igual.
function forEachWarSpatialCandidate(minX,minY,maxX,maxY,visit){
 if(state.mode!=='war'||state.phase!=='combat'||!warCombatGrid.size){
   for(const t of state.entities)visit(t);
   return;
 }
 const cs=WAR_AI_GRID_CELL;
 const startX=Math.floor(minX/cs)-1,endX=Math.floor(maxX/cs)+1;
 const startY=Math.floor(minY/cs)-1,endY=Math.floor(maxY/cs)+1;
 for(let x=startX;x<=endX;x++)for(let y=startY;y<=endY;y++){
   const bucket=warCombatGrid.get(x+','+y);if(!bucket)continue;
   for(const t of bucket)visit(t);
 }
}

""",
    "grid reutilizável e consulta espacial",
)

replace_section(
    "function warCandidatesFor(e,grid,nonDragonOnly=false){",
    "function updateWar(dt){",
    """function warCandidatesFor(e,grid,nonDragonOnly=false,now=performance.now()){
 const cached=warCandidateCache.get(e.id);
 if(cached&&cached.nonDragonOnly===nonDragonOnly&&now<cached.until){
   if(cached.items.length===0)return cached.items;
   for(const t of cached.items){
     if(t.alive&&t!==e&&t.team!==e.team&&(!nonDragonOnly||t.type!=='dragon')&&canEngageTarget(e,t))return cached.items;
   }
 }
 const cs=WAR_AI_GRID_CELL,r=WAR_AI_LOCAL_RADIUS,r2=r*r;
 const minX=Math.floor((e.x-r)/cs),maxX=Math.floor((e.x+r)/cs);
 const minY=Math.floor((e.y-r)/cs),maxY=Math.floor((e.y+r)/cs);
 const local=[];
 for(let x=minX;x<=maxX;x++)for(let y=minY;y<=maxY;y++){
   const bucket=grid.get(x+','+y);if(!bucket)continue;
   for(const t of bucket){
     if(!t.alive||t===e||t.team===e.team||(nonDragonOnly&&t.type==='dragon')||!canEngageTarget(e,t))continue;
     const dx=t.x-e.x,dy=t.y-e.y;if(dx*dx+dy*dy<=r2)local.push(t);
   }
 }
 const nearest=local.length?null:nearestEnemyFromWarGrid(e,grid,nonDragonOnly);
 const result=local.length?local:(nearest?[nearest]:[]);
 warCandidateCache.set(e.id,{nonDragonOnly,until:now+WAR_AI_DECISION_INTERVAL_MS,items:result});
 return result;
}
""",
    "cache de candidatos da IA",
)

replace_once(
    "     aiFight(e,dt,null,warCandidatesFor(e,combatGrid,avoidDragons));",
    "     aiFight(e,dt,null,warCandidatesFor(e,combatGrid,avoidDragons,now));",
    "uso do cache temporal da IA",
)

replace_once(
    "     candidates=preparedCandidates||nonDragonEnemies.filter(t=>canEngageTarget(e,t));",
    "     candidates=(preparedCandidates||nonDragonEnemies).filter(t=>canEngageTarget(e,t));",
    "validação de candidato em cache para guerreiro/rei",
)

replace_once(
    """function setupWarRound(){
 state.entities=[];state.particles=[];state.dragonProjectiles=[];clearEntityVisuals();state.phase='prep';state.prepLeft=15;state.timeLeft=state.warTime;
""",
    """function setupWarRound(){
 state.entities=[];state.particles=[];state.dragonProjectiles=[];
 warCandidateCache.clear();warCombatGrid.clear();warBurningEntities.clear();deadTargetIds.clear();
 clearEntityVisuals();state.phase='prep';state.prepLeft=15;state.timeLeft=state.warTime;
""",
    "limpeza dos caches por rodada",
)


# =========================================================
# FASE 2 — QUEIMADURA: ATUALIZAR SÓ QUEM ESTÁ QUEIMANDO
# =========================================================
replace_section(
    "          function igniteDragonBurn(target,source){",
    "          function launchDragonFireball",
    """          function igniteDragonBurn(target,source){
           if(!target||!target.alive)return;
           const now=performance.now();
           target.dragonBurnSerial=(target.dragonBurnSerial||0)+1;
           target.dragonBurnStartedAt=now;target.dragonBurnUntil=now+DRAGON_BURN_DURATION_MS;
           target.dragonBurnNextTick=now+DRAGON_BURN_TICK_MS;target.dragonBurnSourceId=source?.id??null;
           target.dragonBurnSourceX=source?.x??target.x;target.dragonBurnSourceY=source?.y??target.y;
           target.dragonBurnFlameCount=2+(target.dragonBurnSerial%2);
           warBurningEntities.add(target);
          }
          function dragonBurnAttacker(target,entityById=warEntityById){
           return entityById.get(target.dragonBurnSourceId)||{id:'dragon-burn',type:'dragon',x:Number(target.dragonBurnSourceX)||target.x,y:Number(target.dragonBurnSourceY)||target.y,heading:0,lastCombatAt:0};
          }
          function updateDragonBurns(now,entityById=warEntityById){
           for(const target of warBurningEntities){
             if(!target.alive||!target.dragonBurnUntil){warBurningEntities.delete(target);continue}
             while(target.alive&&target.dragonBurnNextTick&&now>=target.dragonBurnNextTick&&target.dragonBurnNextTick<=target.dragonBurnUntil){
               const burnSource=dragonBurnAttacker(target,entityById);
               applyCombatHit(target,burnSource,DRAGON_BURN_DAMAGE,{knockForce:0,knockTime:0,tilt:4,allowFlying:burnSource.type==='king'});
               target.dragonBurnNextTick+=DRAGON_BURN_TICK_MS;
             }
             if(now>target.dragonBurnUntil||!target.alive){
               target.dragonBurnUntil=0;target.dragonBurnStartedAt=0;target.dragonBurnNextTick=0;target.dragonBurnSourceId=null;
               warBurningEntities.delete(target);
             }
           }
          }
""",
    "set de queimaduras ativas",
)


# =========================================================
# FASE 2 — MORTE: LIMPAR ALVOS UMA VEZ POR FRAME
# =========================================================
replace_once(
    """ // Ninguém pode continuar \"preso\" a um alvo que já morreu.
 for(const other of state.entities){
   if(other.target===e)other.target=null;
 }
}
""",
    """ // A limpeza é agrupada no fim do frame. Em mortes em área isso evita
 // repetir uma varredura completa de todas as tropas para cada vítima.
 deadTargetIds.add(e.id);
}
""",
    "limpeza agrupada de alvos mortos",
)

replace_once(
    """ }
 separateLivingEntities();
 cleanupDeadEntities(now);
}
""",
    """ }
 if(deadTargetIds.size){
   for(const other of state.entities){
     if(other.target&&deadTargetIds.has(other.target.id))other.target=null;
   }
   deadTargetIds.clear();
 }
 separateLivingEntities();
 cleanupDeadEntities(now);
}
""",
    "flush de alvos mortos no update",
)


# =========================================================
# FASE 2 — PODERES USAM A MESMA GRADE ESPACIAL
# =========================================================
replace_section(
    "function updateMageAttackState(e,now){",
    "function startKingSpecial(e){",
    """function updateMageAttackState(e,now){
 const p=e.pendingMageAttack;if(!p)return;
 if(p.kind==='special'){
   e.moving=false;
   if(!p.impacted && now>=(p.damageAt||p.startedAt||0)){
     p.impacted=true;
     p.hitIds=p.hitIds||{};
     const ox=p.originX,oy=p.originY,r=MAGE_SPECIAL_RADIUS,r2=r*r;

     // Dano: mesmas regras e mesma distância final; só deixamos de testar
     // entidades que estão em células impossíveis de alcançar.
     forEachWarSpatialCandidate(ox-r,oy-r,ox+r,oy+r,t=>{
       if(!t.alive||t===e||t.team===e.team)return;
       const dx=t.x-ox,dy=t.y-oy;if(dx*dx+dy*dy>r2)return;
       if(p.hitIds[t.id])return;p.hitIds[t.id]=true;
       applyCombatHit(t,e,MAGE_SPECIAL_DAMAGE,{knockForce:260,knockTime:.18,tilt:10});
     });

     // Cura mantém exatamente a regra anterior, inclusive o próprio Mago.
     forEachWarSpatialCandidate(ox-r,oy-r,ox+r,oy+r,ally=>{
       if(!ally.alive||ally.team!==e.team)return;
       const dx=ally.x-ox,dy=ally.y-oy;if(dx*dx+dy*dy>r2)return;
       const before=Number(ally.hp)||0;
       ally.hp=Math.min(Number(ally.maxHp)||before,before+MAGE_SPECIAL_HEAL);
       if(ally.hp>before)ally.regenSerial=(ally.regenSerial||0)+1;
     });
   }
 }else if(now>=p.nextTickAt && now>=(p.damageStartAt||0) && now<=(p.damageEndAt||p.endAt)){
   const angle=p.angle??(e.heading||0),length=p.length||245;
   const ox=p.originX??e.x,oy=p.originY??e.y;
   const ax=ox+Math.cos(angle)*32,ay=oy-18,bx=ax+Math.cos(angle)*length,by=ay+Math.sin(angle)*length;
   const fireHalfWidth=22,pad=fireHalfWidth+16;
   forEachWarSpatialCandidate(Math.min(ax,bx)-pad,Math.min(ay,by)-pad,Math.max(ax,bx)+pad,Math.max(ay,by)+pad,t=>{
     if(!t.alive||t===e||t.team===e.team)return;
     const targetBodyRadius=Math.min(16,(t.r||25)*0.5);
     if(distanceToSegment(t.x,t.y,ax,ay,bx,by)<=fireHalfWidth+targetBodyRadius){
       applyCombatHit(t,e,5,{knockForce:90,knockTime:.06,tilt:5});
     }
   });
   p.nextTickAt=now+MAGE_FIRE_TICK;
 }
 if(now>=p.endAt){e.pendingMageAttack=null;e.mageAttackKind=null}
}

""",
    "ataques do Mago com consulta espacial",
)

replace_section(
    "function updateKingSpecialState(e,now){",
    "function performAttack(e,preparedCandidates=null){",
    """function updateKingSpecialState(e,now){
 const p=e.pendingKingSpecial;if(!p)return;
 e.moving=false;
 if(!p.impacted&&now>=(p.damageAt||p.startedAt||0)){
   p.impacted=true;p.hitIds=p.hitIds||{};
   const ox=p.originX,oy=p.originY,r=KING_SPECIAL_RADIUS,r2=r*r;
   forEachWarSpatialCandidate(ox-r,oy-r,ox+r,oy+r,t=>{
     if(!isRealCombatTarget(t)||t===e||t.team===e.team)return;
     const dx=t.x-ox,dy=t.y-oy;if(dx*dx+dy*dy>r2)return;
     if(p.hitIds[t.id])return;
     p.hitIds[t.id]=true;
     applyCombatHit(t,e,KING_SPECIAL_DAMAGE,{knockForce:260,knockTime:.18,tilt:10,allowFlying:true});
     if(t.alive)igniteDragonBurn(t,e);
   });
 }
 if(now>=p.endAt){
   e.pendingKingSpecial=null;
   e.kingNormalCount=0;
 }
}

""",
    "especial do Rei com consulta espacial",
)

replace_section(
    "function resolveGolemImpact(e,pending){",
    "function updateGolemAttackState(e,now){",
    """function resolveGolemImpact(e,pending){
 if(!pending||pending.impacted)return;
 pending.impacted=true;

 if(pending.kind==='special'){
   spawnGolemRockBurst(e);
   if(!e.alive)return;

   const radius=230,r2=radius*radius;
   forEachWarSpatialCandidate(e.x-radius,e.y-radius,e.x+radius,e.y+radius,t=>{
     if(!isRealCombatTarget(t)||t===e||t.team===e.team)return;
     const dx=t.x-e.x,dy=t.y-e.y;if(dx*dx+dy*dy>r2)return;
     applyCombatHit(t,e,70,{
       knockForce:1120,
       knockTime:.50,
       tilt:34,
       shake:22,
       shakeDuration:.58
     });
   });
 }else{
   if(!e.alive)return;
   const target=warEntityById.get(pending.targetId)||state.entities.find(t=>t.id===pending.targetId&&isRealCombatTarget(t));
   if(target && isRealCombatTarget(target) && target.team!==e.team && dist(e,target)<=112){
     applyCombatHit(target,e,40,{
       knockForce:760,
       knockTime:.40,
       tilt:24,
       shake:13,
       shakeDuration:.42
     });
   }
 }
}

""",
    "impacto do Golem com consulta espacial",
)


# =========================================================
# FASE 3 — SNAPSHOT COMPACTO SOMENTE NO MODO GUERRA
# =========================================================
replace_section(
    "function serializeGame(){",
    "function applyRemoteGame(game){",
    """function serializeWarEntityForNetwork(e,now){
 const out={
   id:e.id,type:e.type,x:e.x,y:e.y,team:e.team,color:e.color||'#ffffff',
   hp:Number(e.hp)||0,maxHp:Number(e.maxHp)||0,shield:Number(e.shield)||0,maxShield:Number(e.maxShield)||0,
   alive:!!e.alive,moving:!!e.moving,facing:Number(e.facing)||1,heading:Number(e.heading)||0,
   attackSerial:Number(e.attackSerial)||0,comboStep:Number(e.comboStep)||0,
   hitSerial:Number(e.hitSerial)||0,hitDirX:Number(e.hitDirX)||0,hitDirY:Number(e.hitDirY)||0,hitTilt:Number(e.hitTilt)||13,
   deathStarted:e.deathStarted?1:0,deathDir:Number(e.deathDir)||1,regenSerial:Number(e.regenSerial)||0,
   variant:e.variant||'male',ownerId:e.ownerId??null
 };

 if(e.type==='golem'){
   out.golemAttackKind=e.golemAttackKind??null;
   out.golemAttackSerial=Number(e.golemAttackSerial)||0;
   if(e.pendingGolemAttack){
     const p=e.pendingGolemAttack;
     out.pendingGolemAttack={
       kind:p.kind,reason:p.reason||'normal',serial:Number(p.serial)||Number(e.golemAttackSerial)||0,
       targetId:p.targetId??null,duration:Number(p.duration)||GOLEM_NORMAL_DURATION,
       remainingMs:Math.max(0,Number(p.endAt)-now),
       impactRemainingMs:Math.max(0,Number(p.impactAt)-now),
       impacted:!!p.impacted
     };
   }
 }else if(e.type==='mage'){
   out.mageAttackKind=e.mageAttackKind??null;
   out.mageAttackSerial=Number(e.mageAttackSerial)||0;
   if(e.pendingMageAttack){
     const p=e.pendingMageAttack;
     out.pendingMageAttack={
       kind:p.kind,targetId:p.targetId??null,
       originX:Number.isFinite(Number(p.originX))?Number(p.originX):e.x,
       originY:Number.isFinite(Number(p.originY))?Number(p.originY):e.y,
       angle:Number.isFinite(Number(p.angle))?Number(p.angle):0,
       length:Number.isFinite(Number(p.length))?Number(p.length):245,
       duration:Number(p.duration)||(p.kind==='special'?MAGE_SPECIAL_DURATION:MAGE_NORMAL_DURATION),
       remainingMs:Math.max(0,Number(p.endAt)-now)
     };
   }
 }else if(e.type==='king'){
   out.kingSpecialSerial=Number(e.kingSpecialSerial)||0;
   if(e.pendingKingSpecial){
     const p=e.pendingKingSpecial;
     out.pendingKingSpecial={
       serial:Number(p.serial)||Number(e.kingSpecialSerial)||0,
       duration:Number(p.duration)||KING_SPECIAL_DURATION,
       bodyDuration:Number(p.bodyDuration)||KING_BODY_SPECIAL_DURATION,
       powerDelay:Number(p.powerDelay)||KING_POWER_DELAY_MS,
       originX:Number.isFinite(Number(p.originX))?Number(p.originX):e.x,
       originY:Number.isFinite(Number(p.originY))?Number(p.originY):e.y,
       remainingMs:Math.max(0,Number(p.endAt)-now),
       impactRemainingMs:Math.max(0,Number(p.damageAt)-now),
       impacted:!!p.impacted
     };
   }
 }else if(e.type==='dragon'){
   out.dragonFlightState=e.dragonFlightState||'ground';
   out.dragonTakeoffSerial=Number(e.dragonTakeoffSerial)||0;
   out.dragonAttackSerial=Number(e.dragonAttackSerial)||0;
   if(e.dragonTakeoffEndAt)out.dragonTakeoffRemainingMs=Math.max(0,Number(e.dragonTakeoffEndAt)-now);
   if(e.pendingDragonAttack){
     out.pendingDragonAttack={
       serial:Number(e.pendingDragonAttack.serial)||Number(e.dragonAttackSerial)||0,
       remainingMs:Math.max(0,Number(e.pendingDragonAttack.endAt)-now)
     };
   }
 }

 if(e.dragonBurnUntil){
   out.dragonBurnRemainingMs=Math.max(0,Number(e.dragonBurnUntil)-now);
   out.dragonBurnSerial=Number(e.dragonBurnSerial)||0;
   out.dragonBurnFlameCount=Number(e.dragonBurnFlameCount)||2;
 }

 return out;
}

function serializeGame(){
 const now=performance.now();
 const entities=state.mode==='war'
   ? state.entities.map(e=>serializeWarEntityForNetwork(e,now))
   : state.entities.map(e=>{
       const out={...e,targetId:e.target?.id??e.targetId??null};
       delete out.target;
       if(out.pendingMageAttack){
         out.pendingMageAttack={...out.pendingMageAttack,remainingMs:Math.max(0,out.pendingMageAttack.endAt-now)};
       }
       if(out.pendingKingSpecial){
         out.pendingKingSpecial={
           ...out.pendingKingSpecial,
           remainingMs:Math.max(0,out.pendingKingSpecial.endAt-now),
           impactRemainingMs:Math.max(0,out.pendingKingSpecial.damageAt-now)
         };
       }
       if(out.pendingGolemAttack){
         out.pendingGolemAttack={
           ...out.pendingGolemAttack,
           serial:Number(out.pendingGolemAttack.serial)||Number(out.golemAttackSerial)||0,
           remainingMs:Math.max(0,out.pendingGolemAttack.endAt-now),
           impactRemainingMs:Math.max(0,out.pendingGolemAttack.impactAt-now)
         };
       }
       if(out.dragonTakeoffEndAt){
         out.dragonTakeoffRemainingMs=Math.max(0,out.dragonTakeoffEndAt-now);
         delete out.dragonTakeoffEndAt;
         delete out.dragonTakeoffStartedAt;
       }
       if(out.pendingDragonAttack){
         out.pendingDragonAttack={...out.pendingDragonAttack,remainingMs:Math.max(0,out.pendingDragonAttack.endAt-now)};
       }
       if(out.dragonBurnUntil){
         out.dragonBurnRemainingMs=Math.max(0,out.dragonBurnUntil-now);
         delete out.dragonBurnUntil;
         delete out.dragonBurnStartedAt;
         delete out.dragonBurnNextTick;
       }
       return out;
     });
 const dragonProjectiles=(state.dragonProjectiles||[]).map(p=>({
   id:p.id,x:p.x,y:p.y,vx:p.vx||0,vy:p.vy||0,targetId:p.targetId,
   targetX:p.targetX,targetY:p.targetY,team:p.team,sourceId:p.sourceId,serial:p.serial||0
 }));
 return {seq:++state.netSeq,mode:state.mode,round:state.round,rounds:state.rounds,phase:state.phase,running:state.running,timeLeft:state.timeLeft,prepLeft:state.prepLeft,nextId:state.nextId,players:state.players.map(p=>({...p,local:false})),entities,dragonProjectiles};
}

""",
    "snapshot compacto da Guerra",
)


# =========================================================
# VALIDAÇÕES LOCAIS DO PATCHER
# =========================================================
required = [
    "FIREBASE RTDB, HOST AUTORITATIVO",
    "WAR PERFORMANCE 2026-09-08",
    "REMOTE WAR ROUND TRANSITION SYNC",
    "serializeWarEntityForNetwork",
    "WAR_AI_DECISION_INTERVAL_MS=70",
    "forEachWarSpatialCandidate",
    "warBurningEntities",
    "deadTargetIds",
    "round-heal-alt",
    "heal-pulse-alt",
    "now-NetworkAdapter.lastStateAt>=100",
    "e.hp=e.maxHp=200;",
    "e.shield=e.maxShield=200;",
    "e.damage=25;",
    "kingNormalCount)||0)>=6",
]
for marker in required:
    if marker not in text:
        raise SystemExit(f"Validação ausente: {marker}")

regen_start = text.index("if((el._lastRegenSerial||0)!==(e.regenSerial||0))")
regen_end = text.index("if(e.type==='golem')", regen_start)
if "offsetWidth" in text[regen_start:regen_end]:
    raise SystemExit("A cura ainda contém forced reflow")

# Fase 4 explicitamente fora do escopo: nenhuma URL de asset ou formato é alterado.
if ".webp" in text[text.index("const ASSETS = {"):text.index("const state = {")]:
    raise SystemExit("Fase 4 detectada indevidamente")

path.write_text(text, encoding="utf-8")
print("Fases 1, 2 e 3 aplicadas com sucesso.")
