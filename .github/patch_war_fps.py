from pathlib import Path
import re

path=Path('index.html')
text=path.read_text(encoding='utf-8')
MARKER='WAR FPS SWEEP 2026-09-09'
if MARKER in text:
    print('War FPS patch already applied.')
    raise SystemExit(0)


def replace_once(old,new,label):
    global text
    if old not in text:
        raise SystemExit(f'Trecho não encontrado: {label}')
    text=text.replace(old,new,1)

# =========================================================
# 1) ALVOS: REMOVE ALOCAÇÃO DE ARRAY EM CADA TESTE
# =========================================================
old_target="""function isRealCombatTarget(t){
 // A IA nunca pode selecionar GIFs, poderes, fragmentos ou outros efeitos visuais.
 // Só personagens/unidades reais do combate entram na lista de alvos.
 return !!t && t.alive && ['warrior','king','mage','golem','dragon','enemy'].includes(t.type);
}
"""
new_target="""const REAL_COMBAT_TYPES=new Set(['warrior','king','mage','golem','dragon','enemy']);
// WAR FPS SWEEP 2026-09-09
function isRealCombatTarget(t){
 // Set persistente: evita criar um array novo em cada teste de alvo.
 return !!t && t.alive && REAL_COMBAT_TYPES.has(t.type);
}
"""
replace_once(old_target,new_target,'Set persistente de tipos combatentes')

# Helper sem filter/map temporário para localizar o mais próximo.
anchor="""/* ==================== IA ==================== */
function aiFightAgainstList(e,dt,candidates){
"""
helper="""/* ==================== IA ==================== */
function nearestEngageableCandidate(e,candidates,forcedTeam=null,nonDragonOnly=false){
 let target=null,bestSq=Infinity;
 for(const t of candidates||[]){
   if(!t||!t.alive||t===e)continue;
   if(forcedTeam ? t.team!==forcedTeam : t.team===e.team)continue;
   if(nonDragonOnly&&t.type==='dragon')continue;
   if(!canEngageTarget(e,t))continue;
   const dx=t.x-e.x,dy=t.y-e.y,ds=dx*dx+dy*dy;
   if(ds<bestSq){bestSq=ds;target=t}
 }
 return target;
}
function aiFightAgainstList(e,dt,candidates){
"""
replace_once(anchor,helper,'helper de alvo sem alocação')

# Golem: usa lista já preparada diretamente, sem .filter() duplo.
old_golem_candidates=""" const candidates=(preparedCandidates||state.entities.filter(t=>
   isRealCombatTarget(t) && t!==e &&
   (forcedTeam?t.team===forcedTeam:t.team!==e.team)
 )).filter(t=>canEngageTarget(e,t));
 if(!candidates.length){
   e.moving=false;
   e.target=null;
   e.golemPhase='seek';
   return;
 }

 let target=candidates[0];
 let tdx=target.x-e.x,tdy=target.y-e.y,bestSq=tdx*tdx+tdy*tdy;
 for(let i=1;i<candidates.length;i++){
   const candidate=candidates[i];
   const cdx=candidate.x-e.x,cdy=candidate.y-e.y,ds=cdx*cdx+cdy*cdy;
   if(ds<bestSq){bestSq=ds;target=candidate}
 }

 e.target=target;
"""
new_golem_candidates=""" const candidates=preparedCandidates||state.entities;
 const target=nearestEngageableCandidate(e,candidates,forcedTeam,false);
 if(!target){
   e.moving=false;
   e.target=null;
   e.golemPhase='seek';
   return;
 }

 e.target=target;
"""
replace_once(old_golem_candidates,new_golem_candidates,'Golem sem filtros temporários')

# Dragon: seleção sem arrays temporários e distância só uma vez.
old_dragon_candidates="""           const candidates=(preparedCandidates||state.entities.filter(t=>t.alive&&t!==e&&(forcedTeam?t.team===forcedTeam:t.team!==e.team))).filter(t=>canEngageTarget(e,t));
           if(!candidates.length){e.moving=false;e.target=null;return}
           let target=candidates[0],best=dist(e,target);for(let i=1;i<candidates.length;i++){const d=dist(e,candidates[i]);if(d<best){best=d;target=candidates[i]}}
           e.target=target;const dx=target.x-e.x,dy=target.y-e.y,d=Math.hypot(dx,dy)||1;e.heading=Math.atan2(dy,dx);if(Math.abs(dx)>4)e.facing=dx<0?-1:1;
"""
new_dragon_candidates="""           const candidates=preparedCandidates||state.entities;
           const target=nearestEngageableCandidate(e,candidates,forcedTeam,false);
           if(!target){e.moving=false;e.target=null;return}
           e.target=target;const dx=target.x-e.x,dy=target.y-e.y,d=Math.hypot(dx,dy)||1;e.heading=Math.atan2(dy,dx);if(Math.abs(dx)>4)e.facing=dx<0?-1:1;
"""
replace_once(old_dragon_candidates,new_dragon_candidates,'Dragão sem filter/dist repetidos')

# Mage: mesma otimização; contagem do especial continua no loop existente.
old_mage_candidates=""" const candidates=(preparedCandidates||state.entities.filter(t=>t.alive&&t!==e&&(forcedTeam?t.team===forcedTeam:t.team!==e.team))).filter(t=>canEngageTarget(e,t));
 if(!candidates.length){e.moving=false;return}
 let target=candidates[0],best=dist(e,target);for(let i=1;i<candidates.length;i++){const d=dist(e,candidates[i]);if(d<best){best=d;target=candidates[i]}}
 e.target=target;const dx=target.x-e.x,dy=target.y-e.y,d=Math.hypot(dx,dy)||1;e.heading=Math.atan2(dy,dx);if(Math.abs(dx)>4)e.facing=dx<0?-1:1;
"""
new_mage_candidates=""" const candidates=preparedCandidates||state.entities;
 const target=nearestEngageableCandidate(e,candidates,forcedTeam,false);
 if(!target){e.moving=false;e.target=null;return}
 e.target=target;const dx=target.x-e.x,dy=target.y-e.y,d=Math.hypot(dx,dy)||1;e.heading=Math.atan2(dy,dx);if(Math.abs(dx)>4)e.facing=dx<0?-1:1;
"""
replace_once(old_mage_candidates,new_mage_candidates,'Mago sem filter/dist repetidos')

# Guerreiro/Rei: remove sistema de fuga e filtros por frame.
pattern=r"\nfunction tryWarriorFleeFlyingDragon\(e,dt\)\{.*?\n\}\n\nfunction aiFight\(e,dt,forcedTeam,preparedCandidates=null\)\{"
m=re.search(pattern,text,re.S)
if not m:
    raise SystemExit('Função de fuga do Dragão não encontrada')
text=text[:m.start()]+"\nfunction aiFight(e,dt,forcedTeam,preparedCandidates=null){"+text[m.end():]

old_ai_block=""" let candidates;
 if((e.type==='warrior'||e.type==='king')&&state.mode==='war'&&state.phase==='combat'){
   // Regra absoluta: enquanto existir QUALQUER tropa inimiga que não seja Dragão,
   // o Guerreiro ignora os Dragões e escolhe apenas entre essas tropas.
   // Não usa o recorte local do grid aqui, evitando conflito entre fuga e aquisição de alvo.
   const cachedEnemies=forcedTeam==null?warFrameEnemiesByTeam.get(e.team):null;
   const allEnemies=cachedEnemies?.all||state.entities.filter(t=>t.alive&&t!==e&&(forcedTeam?t.team===forcedTeam:t.team!==e.team)&&isRealCombatTarget(t));
   const nonDragonEnemies=cachedEnemies?.nonDragon||allEnemies.filter(t=>t.type!=='dragon');
   if(nonDragonEnemies.length){
     candidates=(preparedCandidates||nonDragonEnemies).filter(t=>canEngageTarget(e,t));
   }else{
     if(tryWarriorFleeFlyingDragon(e,dt))return;
     candidates=[];
   }
 }else{
   candidates=(preparedCandidates||state.entities.filter(t=>t.alive&&t!==e&&(forcedTeam?t.team===forcedTeam:t.team!==e.team))).filter(t=>canEngageTarget(e,t));
 }
 if(!candidates.length){e.moving=false;return}
 let target=candidates[0],best=dist(e,target);
 for(let i=1;i<candidates.length;i++){const d=dist(e,candidates[i]);if(d<best){best=d;target=candidates[i]}}
 e.target=target;
"""
new_ai_block=""" const candidates=preparedCandidates||state.entities;
 let nonDragonOnly=false;
 if((e.type==='warrior'||e.type==='king')&&state.mode==='war'&&state.phase==='combat'){
   const cachedEnemies=forcedTeam==null?warFrameEnemiesByTeam.get(e.team):null;
   nonDragonOnly=!!(cachedEnemies?.nonDragon?.length);
 }
 const target=nearestEngageableCandidate(e,candidates,forcedTeam,nonDragonOnly);
 // Sem alvo alcançável (por exemplo, só Dragões voando): fica parado.
 if(!target){e.moving=false;e.target=null;return}
 e.target=target;
"""
replace_once(old_ai_block,new_ai_block,'IA Guerreiro/Rei sem fuga e sem filtros temporários')

# Ataque corpo a corpo: evita Math.hypot para cada candidato.
old_attack=""" const candidates=preparedCandidates||state.entities;
 for(const t of candidates){
   if(t.alive&&t!==e&&t.team!==e.team&&canEngageTarget(e,t)&&dist(e,t)<92)applyCombatHit(t,e,e.damage);
 }
"""
new_attack=""" const candidates=preparedCandidates||state.entities;
 const hitRangeSq=92*92;
 for(const t of candidates){
   if(!t.alive||t===e||t.team===e.team||!canEngageTarget(e,t))continue;
   const dx=t.x-e.x,dy=t.y-e.y;
   if(dx*dx+dy*dy<hitRangeSq)applyCombatHit(t,e,e.damage);
 }
"""
replace_once(old_attack,new_attack,'Ataque melee com distância quadrada')

# =========================================================
# 2) VARREDURA ESPACIAL: NÃO RECONSTRÓI GRID 60x/s
# =========================================================
old_consts="""const WAR_AI_GRID_CELL=220;
const WAR_AI_LOCAL_RADIUS=560;
const WAR_AI_DECISION_INTERVAL_MS=70;
// PERFORMANCE SWEEP 2026-09-07: caches de frame sem alterar decisao/alcance da IA.
const warFrameEnemiesByTeam=new Map();
const warEntityById=new Map();
const warCombatGrid=new Map();
const warCandidateCache=new Map();
const warBurningEntities=new Set();
const deadTargetIds=new Set();
"""
new_consts="""const WAR_AI_GRID_CELL=220;
const WAR_AI_LOCAL_RADIUS=560;
const WAR_AI_DECISION_INTERVAL_MS=90;
const WAR_AI_GRID_REFRESH_MS=90;
const WAR_SEPARATION_INTERVAL_SEC=1/30;
// Grid/varredura de decisão roda ~11x/s; movimento, física, ataques e render continuam por frame.
const warFrameEnemiesByTeam=new Map();
const warEntityById=new Map();
const warCombatGrid=new Map();
const warCandidateCache=new Map();
const warBurningEntities=new Set();
const deadTargetIds=new Set();
const warLivingScratch=[];
let warAIGridBuiltAt=0;
let warSeparationAccumulator=0;
"""
replace_once(old_consts,new_consts,'cadência da varredura da Guerra')

old_updatewar=""" }else if(state.phase==='combat'){
   const now=performance.now();
   const entityById=rebuildWarEntityIdMap();
   updateDragonProjectiles(dt,entityById);updateDragonBurns(now,entityById);
   const living=state.entities.filter(e=>e.alive);
   const teams=rebuildWarFrameEnemyCache(living);
   const combatGrid=buildWarAIGrid(living);
   for(const e of living){
     const avoidDragons=(e.type==='warrior'||e.type==='king')&&(warFrameEnemiesByTeam.get(e.team)?.nonDragon.length||0)>0;
     aiFight(e,dt,null,warCandidatesFor(e,combatGrid,avoidDragons,now));
   }
   state.timeLeft-=dt;
   if(teams.length<=1 || state.timeLeft<=0)finishWarRound();
 }
"""
new_updatewar=""" }else if(state.phase==='combat'){
   const now=performance.now();
   const entityById=rebuildWarEntityIdMap();
   updateDragonProjectiles(dt,entityById);updateDragonBurns(now,entityById);

   const living=warLivingScratch;living.length=0;
   for(const entity of state.entities)if(entity.alive)living.push(entity);

   // A grade serve aquisição de alvo e efeitos de área. Não precisa ser remontada
   // em 60/90/120 Hz: em 90 ms uma unidade anda poucos pixels e a margem espacial
   // já cobre esse deslocamento. Movimento/ataque continuam atualizados todo frame.
   if(!warCombatGrid.size||now-warAIGridBuiltAt>=WAR_AI_GRID_REFRESH_MS){
     rebuildWarFrameEnemyCache(living);
     buildWarAIGrid(living);
     warCandidateCache.clear();
     warAIGridBuiltAt=now;
   }

   for(const e of living){
     const avoidDragons=(e.type==='warrior'||e.type==='king')&&(warFrameEnemiesByTeam.get(e.team)?.nonDragon.length||0)>0;
     aiFight(e,dt,null,warCandidatesFor(e,warCombatGrid,avoidDragons,now));
   }
   state.timeLeft-=dt;
   if(warFrameEnemiesByTeam.size<=1 || state.timeLeft<=0)finishWarRound();
 }
"""
replace_once(old_updatewar,new_updatewar,'updateWar com grid desacoplado do FPS')

# Reinicia relógio do grid em toda rodada.
old_setup_clear=""" warCandidateCache.clear();warCombatGrid.clear();warBurningEntities.clear();deadTargetIds.clear();
 clearEntityVisuals();state.phase='prep';state.prepLeft=15;state.timeLeft=state.warTime;
"""
new_setup_clear=""" warCandidateCache.clear();warCombatGrid.clear();warBurningEntities.clear();deadTargetIds.clear();
 warAIGridBuiltAt=0;warSeparationAccumulator=0;
 clearEntityVisuals();state.phase='prep';state.prepLeft=15;state.timeLeft=state.warTime;
"""
replace_once(old_setup_clear,new_setup_clear,'reset dos relógios de performance da rodada')

# Separação/crowd collision a 30 Hz na Guerra; PVE continua por frame.
old_separation=""" separateLivingEntities();
 // Knockback e separação podem empurrar a unidade alguns pixels depois da IA.
 // O clamp final garante que ninguém atravesse visualmente a muralha.
 if(state.mode==='war')constrainWarEntitiesToArena();
"""
new_separation=""" if(state.mode==='war'){
   warSeparationAccumulator+=dt;
   if(warSeparationAccumulator>=WAR_SEPARATION_INTERVAL_SEC){
     warSeparationAccumulator%=WAR_SEPARATION_INTERVAL_SEC;
     separateLivingEntities();
   }
   // Clamp físico continua em TODOS os frames.
   constrainWarEntitiesToArena();
 }else{
   separateLivingEntities();
 }
"""
replace_once(old_separation,new_separation,'separação da Guerra em 30 Hz')

# =========================================================
# 3) CULLING/GIF: HISTERese PARA NÃO PISCAR NAS BORDAS
# =========================================================
old_margin=""" // Apenas marcação simples no canvas. GIF/espada/barras ficam em DOM para os GIFs animarem de verdade.
 const margin=80;
"""
new_margin=""" // Margem maior evita entra/sai do culling durante pan, tremor e limites da arena.
 const margin=170;
"""
replace_once(old_margin,new_margin,'margem estável do culling')

old_visible_fn="""function setEntityNodeVisible(el,visible){
 if(el._nodeVisible===visible)return;
 el._nodeVisible=visible;
 el.style.visibility=visible?'visible':'hidden';
 el.style.opacity=visible?'1':'0';
}
"""
new_visible_fn="""const ENTITY_OFFSCREEN_GIF_GRACE_MS=900;
const ENTITY_NODE_RETENTION_MS=5000;
const ENTITY_MOVE_VISUAL_HOLD_MS=150;
function clearEntityOffscreenSuspend(el){
 if(el?._offscreenGifTimer){clearTimeout(el._offscreenGifTimer);el._offscreenGifTimer=null}
}
function scheduleEntityOffscreenSuspend(el){
 if(!el||el._offscreenGifTimer)return;
 el._offscreenGifTimer=setTimeout(()=>{
   el._offscreenGifTimer=null;
   if(el._nodeVisible===false)suspendEntityLoopGif(el);
 },ENTITY_OFFSCREEN_GIF_GRACE_MS);
}
function entityVisualMoving(el,e,now){
 if(e.moving){el._visualMovingUntil=now+ENTITY_MOVE_VISUAL_HOLD_MS;return true}
 return now<Number(el._visualMovingUntil||0);
}
function setEntityNodeVisible(el,visible){
 if(visible)clearEntityOffscreenSuspend(el);
 if(el._nodeVisible===visible)return;
 el._nodeVisible=visible;
 el.style.visibility=visible?'visible':'hidden';
 el.style.opacity=visible?'1':'0';
}
"""
replace_once(old_visible_fn,new_visible_fn,'histerese do culling de entidade')

# Não descarrega GIF imediatamente quando cruza a borda de tela.
old_offscreen="""     suspendEntityLoopGif(el);
     continue;
   }

   visibleIds.add(e.id);
   el._lastVisibleAt=localNow;
   setEntityNodeVisible(el,true);
"""
new_offscreen="""     scheduleEntityOffscreenSuspend(el);
     continue;
   }

   visibleIds.add(e.id);
   el._lastVisibleAt=localNow;
   setEntityNodeVisible(el,true);
   const visualMoving=entityVisualMoving(el,e,localNow);
"""
replace_once(old_offscreen,new_offscreen,'culling interno sem descarregar instantaneamente')

# Usa pequeno hold visual para idle/walk não oscilar em paredes/clamps.
for old,new,label in [
 ("const desired=attackKind==='special'?'special':attackKind==='normal'?'attack':e.moving?'walk':'idle';","const desired=attackKind==='special'?'special':attackKind==='normal'?'attack':visualMoving?'walk':'idle';",'Golem visual estável'),
 ("const desired=special?'special':e.moving?'walk':'idle';","const desired=special?'special':visualMoving?'walk':'idle';",'Mago visual estável'),
 ("setEntitySpriteState(el,bodySpecial?'special':e.moving?'walk':'idle');","setEntitySpriteState(el,bodySpecial?'special':visualMoving?'walk':'idle');",'Rei visual estável'),
 ("const desired=e.moving?'walk':'idle';\n     setEntitySpriteState(el,desired);","const desired=visualMoving?'walk':'idle';\n     setEntitySpriteState(el,desired);",'Guerreiro visual estável'),
]:
    replace_once(old,new,label)

old_final_cull="""   if(!visibleIds.has(id)||!presentIds.has(id)){
     setEntityNodeVisible(el,false);
     suspendEntityLoopGif(el);
     const entity=presentMap.get(id);
     const transient=entity && (entity.deathStarted||entity.pendingGolemAttack||entity.pendingMageAttack||entity.pendingKingSpecial||entity.pendingDragonAttack||entity.dragonFlightState==='takeoff');
     const lastSeen=Number(el._lastVisibleAt||0);
     if(entity && !transient && localNow-lastSeen>1400){
       clearEntityLoopSuspendTimers(el);
       el.querySelectorAll('img').forEach(releaseGifObjectUrl);
       el.remove();
       entityNodes.delete(id);
     }
   }
"""
new_final_cull="""   if(!visibleIds.has(id)||!presentIds.has(id)){
     setEntityNodeVisible(el,false);
     scheduleEntityOffscreenSuspend(el);
     const entity=presentMap.get(id);
     const transient=entity && (entity.deathStarted||entity.pendingGolemAttack||entity.pendingMageAttack||entity.pendingKingSpecial||entity.pendingDragonAttack||entity.dragonFlightState==='takeoff');
     const lastSeen=Number(el._lastVisibleAt||0);
     if(entity && !transient && localNow-lastSeen>ENTITY_NODE_RETENTION_MS){
       clearEntityOffscreenSuspend(el);
       clearEntityLoopSuspendTimers(el);
       el.querySelectorAll('img').forEach(releaseGifObjectUrl);
       el.remove();
       entityNodes.delete(id);
     }
   }
"""
replace_once(old_final_cull,new_final_cull,'retenção de nó sem thrash na borda')

old_clear_node=""" for(const el of entityNodes.values()){
   clearEntityLoopSuspendTimers(el);
   el.querySelectorAll('img').forEach(releaseGifObjectUrl);
 }
"""
new_clear_node=""" for(const el of entityNodes.values()){
   clearEntityOffscreenSuspend(el);
   clearEntityLoopSuspendTimers(el);
   el.querySelectorAll('img').forEach(releaseGifObjectUrl);
 }
"""
replace_once(old_clear_node,new_clear_node,'limpeza timer offscreen')

# Canvas: remove save/restore por unidade mantendo a mesma elipse/cores.
old_marker="""function drawEntityMarker(e){
 // No PVE a identificação agora é feita por contorno/silhueta no próprio sprite.
 if(state.mode==='pve'||!e.alive)return;
 ctx.save();
 ctx.strokeStyle=e.color;ctx.lineWidth=(e.controlled?3:2)/state.camera.zoom;
 ctx.globalAlpha=e.controlled?.95:.58;
 ctx.beginPath();ctx.ellipse(e.x,e.y+31,27,9,0,0,Math.PI*2);ctx.stroke();
 ctx.restore();
}
"""
new_marker="""function drawEntityMarker(e){
 if(state.mode==='pve'||!e.alive)return;
 ctx.strokeStyle=e.color;ctx.lineWidth=(e.controlled?3:2)/state.camera.zoom;
 ctx.globalAlpha=e.controlled?.95:.58;
 ctx.beginPath();ctx.ellipse(e.x,e.y+31,27,9,0,0,Math.PI*2);ctx.stroke();
 ctx.globalAlpha=1;
}
"""
replace_once(old_marker,new_marker,'marcador canvas sem save/restore')

# =========================================================
# 4) FIREBASE: MENOS TRABALHO LOCAL NO HOST
# =========================================================
old_sub="""        const unsubscribe=F.onValue(F.ref(F.firebaseDb,`rooms/${code}/${key}`),s=>{this.roomCache[key]=s.exists()?s.val():null;syncFirebaseRoom(this.roomCache)});
"""
new_sub="""        const unsubscribe=F.onValue(F.ref(F.firebaseDb,`rooms/${code}/${key}`),s=>{
          this.roomCache[key]=s.exists()?s.val():null;
          // O host acabou de gerar esse snapshot; processá-lo outra vez localmente
          // só repete trabalho de sala/DOM sem mudar a autoridade do jogo.
          if(key==='game'&&this.isHost)return;
          syncFirebaseRoom(this.roomCache);
        });
"""
replace_once(old_sub,new_sub,'ignora eco do snapshot no host')

old_push=""" if(NetworkAdapter.online&&NetworkAdapter.isHost&&NetworkAdapter.roomStatus==='playing'&&gameScreenPerfEl.style.display!=='none'&&now-NetworkAdapter.lastStateAt>=100&&!NetworkAdapter.pushing){
   NetworkAdapter.lastStateAt=now;NetworkAdapter.pushing=true;
   NetworkAdapter.pushState(serializeGame()).catch(console.error).finally(()=>NetworkAdapter.pushing=false);
 }
"""
new_push=""" const networkPushInterval=state.mode==='war'?125:100;
 if(NetworkAdapter.online&&NetworkAdapter.isHost&&NetworkAdapter.roomStatus==='playing'&&gameScreenPerfEl.style.display!=='none'&&now-NetworkAdapter.lastStateAt>=networkPushInterval&&!NetworkAdapter.pushing){
   NetworkAdapter.lastStateAt=now;NetworkAdapter.pushing=true;
   NetworkAdapter.pushState(serializeGame()).catch(console.error).finally(()=>NetworkAdapter.pushing=false);
 }
"""
replace_once(old_push,new_push,'cadência de snapshot da Guerra')

checks=[
 MARKER,
 "const REAL_COMBAT_TYPES=new Set",
 "function nearestEngageableCandidate",
 "const WAR_AI_DECISION_INTERVAL_MS=90;",
 "const WAR_AI_GRID_REFRESH_MS=90;",
 "const WAR_SEPARATION_INTERVAL_SEC=1/30;",
 "const warLivingScratch=[];",
 "if(!warCombatGrid.size||now-warAIGridBuiltAt>=WAR_AI_GRID_REFRESH_MS)",
 "warCandidateCache.clear();",
 "warSeparationAccumulator+=dt;",
 "const margin=170;",
 "const ENTITY_OFFSCREEN_GIF_GRACE_MS=900;",
 "const ENTITY_NODE_RETENTION_MS=5000;",
 "function scheduleEntityOffscreenSuspend(el)",
 "const visualMoving=entityVisualMoving(el,e,localNow);",
 "scheduleEntityOffscreenSuspend(el);",
 "if(key==='game'&&this.isHost)return;",
 "const networkPushInterval=state.mode==='war'?125:100;",
 "const hitRangeSq=92*92;",
]
for marker in checks:
    if marker not in text:
        raise SystemExit(f'Validação FPS falhou: {marker}')

for forbidden in [
    'function tryWarriorFleeFlyingDragon',
    'if(tryWarriorFleeFlyingDragon(e,dt))return;',
    "['warrior','king','mage','golem','dragon','enemy'].includes(t.type)",
    "const living=state.entities.filter(e=>e.alive);\n   const teams=rebuildWarFrameEnemyCache(living);\n   const combatGrid=buildWarAIGrid(living);",
    'localNow-lastSeen>1400',
]:
    if forbidden in text:
        raise SystemExit(f'Comportamento antigo ainda presente: {forbidden}')

# Garantias de mecânica/visual importantes.
for marker in [
    "state.world.w=1850;state.world.h=1542;",
    "const WAR_ARENA_INSET={left:270,right:270,top:275,bottom:245};",
    "restartGif(el._golemSpecial,'golemSpecial'",
    "restartGif(el._kingSpecial,'kingSpecial'",
    "restartGif(el._dragonAttack,'dragonAttack'",
    "if(state.mode==='war')",
    "world:{w:state.world.w,h:state.world.h}",
]:
    if marker not in text:
        raise SystemExit(f'Garantia preservada ausente: {marker}')

path.write_text(text,encoding='utf-8')
print('War FPS sweep aplicado: IA/varredura/culling/rede otimizados; fuga do Dragão removida.')
