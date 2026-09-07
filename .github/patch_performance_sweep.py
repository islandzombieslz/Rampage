from pathlib import Path
import re

path=Path('index.html')
text=path.read_text(encoding='utf-8')


def replace_once(old,new,label):
    global text
    count=text.count(old)
    if count!=1:
        raise SystemExit(f'{label}: esperava 1 ocorrencia, encontrei {count}')
    text=text.replace(old,new,1)

# 1) Botao da loja maior, mantendo exatamente o mesmo sprite e hit target.
replace_once('''  width:76px !important;\n  height:76px !important;''','''  width:96px !important;\n  height:96px !important;''','botao loja desktop')
replace_once('''    width:62px !important;\n    height:62px !important;''','''    width:78px !important;\n    height:78px !important;''','botao loja mobile')

# 2) Cache por frame para a regra de Guerreiros no modo Guerra.
# Evita cada Guerreiro percorrer state.entities inteiro uma ou duas vezes por frame.
replace_once('''const WAR_AI_GRID_CELL=220;\nconst WAR_AI_LOCAL_RADIUS=560;''','''const WAR_AI_GRID_CELL=220;\nconst WAR_AI_LOCAL_RADIUS=560;\n// PERFORMANCE SWEEP 2026-09-07: caches de frame sem alterar decisao/alcance da IA.\nconst warFrameEnemiesByTeam=new Map();\nfunction rebuildWarFrameEnemyCache(living){\n const teams=[],seen=new Set();\n warFrameEnemiesByTeam.clear();\n for(const e of living){\n   if(!seen.has(e.team)){seen.add(e.team);teams.push(e.team)}\n }\n for(const team of teams){\n   const all=[],nonDragon=[],dragons=[];\n   for(const t of living){\n     if(t.team===team||!isRealCombatTarget(t))continue;\n     all.push(t);\n     if(t.type==='dragon')dragons.push(t);else nonDragon.push(t);\n   }\n   warFrameEnemiesByTeam.set(team,{all,nonDragon,dragons});\n }\n return teams;\n}''','cache IA guerra')

replace_once('''   const living=state.entities.filter(e=>e.alive);\n   const teams=[...new Set(living.map(e=>e.team))];\n   const combatGrid=buildWarAIGrid(living);''','''   const living=state.entities.filter(e=>e.alive);\n   const teams=rebuildWarFrameEnemyCache(living);\n   const combatGrid=buildWarAIGrid(living);''','updateWar cache times')

replace_once(''' const enemies=state.entities.filter(t=>t.alive&&t.team!==e.team&&isRealCombatTarget(t));\n if(!enemies.length||enemies.some(t=>t.type!=='dragon'))return false;\n\n // Quando só restam Dragões, foge do Dragão voando mais próximo em vez de ficar parado.\n const dragons=enemies.filter(t=>t.type==='dragon');''',''' const cached=warFrameEnemiesByTeam.get(e.team);\n const enemies=cached?.all||state.entities.filter(t=>t.alive&&t.team!==e.team&&isRealCombatTarget(t));\n if(!enemies.length||(cached?cached.nonDragon.length:enemies.some(t=>t.type!=='dragon')))return false;\n\n // Quando só restam Dragões, foge do Dragão mais próximo em vez de ficar parado.\n const dragons=cached?.dragons||enemies.filter(t=>t.type==='dragon');''','fuga guerreiro cache')

replace_once('''   const allEnemies=state.entities.filter(t=>t.alive&&t!==e&&(forcedTeam?t.team===forcedTeam:t.team!==e.team)&&isRealCombatTarget(t));\n   const nonDragonEnemies=allEnemies.filter(t=>t.type!=='dragon');''','''   const cachedEnemies=forcedTeam==null?warFrameEnemiesByTeam.get(e.team):null;\n   const allEnemies=cachedEnemies?.all||state.entities.filter(t=>t.alive&&t!==e&&(forcedTeam?t.team===forcedTeam:t.team!==e.team)&&isRealCombatTarget(t));\n   const nonDragonEnemies=cachedEnemies?.nonDragon||allEnemies.filter(t=>t.type!=='dragon');''','alvos guerreiro cache')

# 3) Golem: remove array de objetos + sort criado em todo frame; preserva contagem e alvo mais proximo.
replace_once(''' const nearbySpecial=[];\n for(const candidate of candidates){\n   const ndx=candidate.x-e.x,ndy=candidate.y-e.y,ds=ndx*ndx+ndy*ndy;\n   if(ds<=145*145)nearbySpecial.push({target:candidate,ds});\n }\n nearbySpecial.sort((a,b)=>a.ds-b.ds);\n\n const crowdActive=nearbySpecial.length>=2;''',''' let nearbySpecialTarget=null,nearbySpecialBestSq=Infinity,nearbySpecialCount=0;\n const golemSpecialRadiusSq=145*145;\n for(const candidate of candidates){\n   const ndx=candidate.x-e.x,ndy=candidate.y-e.y,ds=ndx*ndx+ndy*ndy;\n   if(ds<=golemSpecialRadiusSq){\n     nearbySpecialCount++;\n     if(ds<nearbySpecialBestSq){nearbySpecialBestSq=ds;nearbySpecialTarget=candidate}\n   }\n }\n\n const crowdActive=nearbySpecialCount>=2;''','golem crowd sem sort')
replace_once("startGolemAttack(e,'special',nearbySpecial[0].target,'crowd')","startGolemAttack(e,'special',nearbySpecialTarget,'crowd')",'golem alvo crowd')

# 4) Mago: mesma contagem de inimigos na area usando distancia ao quadrado, sem filter+sqrt+array.
replace_once('''   const nearbyForSpecial=candidates.filter(t=>dist(e,t)<=MAGE_SPECIAL_RADIUS).length;''','''   let nearbyForSpecial=0;\n   const mageSpecialRadiusSq=MAGE_SPECIAL_RADIUS*MAGE_SPECIAL_RADIUS;\n   for(const t of candidates){\n     const sdx=t.x-e.x,sdy=t.y-e.y;\n     if(sdx*sdx+sdy*sdy<=mageSpecialRadiusSq)nearbyForSpecial++;\n   }''','mago especial sem alocacao')

# 5) PVE: reutiliza listas de vivos e set de humanos; evita 3 filtros/includes por frame.
replace_once('''function updateOutOfCombatRegen(dt){\n  if(state.mode!=='pve'||state.phase!=='combat')return;\n\n  const now=performance.now();\n  const enemies=state.entities.filter(e=>e.alive&&e.team==='enemy');''','''function updateOutOfCombatRegen(dt,enemies=null){\n  if(state.mode!=='pve'||state.phase!=='combat')return;\n\n  const now=performance.now();\n  enemies=enemies||state.entities.filter(e=>e.alive&&e.team==='enemy');''','regen PVE lista pronta')

replace_once('''function updatePVE(dt){\n const controlledHumans=state.entities.filter(e=>e.alive&&e.team==='players'&&state.players.some(p=>p.id===e.ownerId&&p.human));''','''const pveHumanOwnerIds=new Set();\nconst pveAlivePlayersScratch=[];\nconst pveAliveEnemiesScratch=[];\nconst pveControlledHumansScratch=[];\nfunction updatePVE(dt){\n pveHumanOwnerIds.clear();\n pveAlivePlayersScratch.length=0;pveAliveEnemiesScratch.length=0;pveControlledHumansScratch.length=0;\n for(const p of state.players)if(p.human)pveHumanOwnerIds.add(p.id);\n for(const e of state.entities){\n   if(!e.alive)continue;\n   if(e.team==='players'){\n     pveAlivePlayersScratch.push(e);\n     if(pveHumanOwnerIds.has(e.ownerId))pveControlledHumansScratch.push(e);\n   }else if(e.team==='enemy')pveAliveEnemiesScratch.push(e);\n }\n const controlledHumans=pveControlledHumansScratch;\n const alivePlayersList=pveAlivePlayersScratch;\n const aliveEnemiesList=pveAliveEnemiesScratch;''','PVE scratch lists')

replace_once(''' // Arrays de alvo são montados uma única vez por frame.\n const alivePlayersList=state.entities.filter(e=>e.alive&&e.team==='players');\n const aliveEnemiesList=state.entities.filter(e=>e.alive&&e.team==='enemy');\n for(let i=0;i<alivePlayersList.length;i++){\n   const e=alivePlayersList[i];\n   if(!controlledHumans.includes(e))aiFightAgainstList(e,dt,aliveEnemiesList);\n }''',''' // Arrays de alvo ja foram montados no inicio do frame e sao reutilizados.\n for(let i=0;i<alivePlayersList.length;i++){\n   const e=alivePlayersList[i];\n   if(!pveHumanOwnerIds.has(e.ownerId))aiFightAgainstList(e,dt,aliveEnemiesList);\n }''','PVE remove filtros duplicados')
replace_once('updateOutOfCombatRegen(dt);','updateOutOfCombatRegen(dt,aliveEnemiesList);','PVE regen reutiliza inimigos')

# 6) Particulas: atualizacao/remocao in-place, evitando criar novo array em cada frame.
replace_once("function updateParticles(dt){state.particles.forEach(p=>{p.x+=p.vx*dt;p.y+=p.vy*dt;p.life-=dt});state.particles=state.particles.filter(p=>p.life>0)}",'''function updateParticles(dt){\n const list=state.particles;\n for(let i=list.length-1;i>=0;i--){\n   const p=list[i];p.x+=p.vx*dt;p.y+=p.vy*dt;p.life-=dt;\n   if(p.life<=0)list.splice(i,1);\n }\n}''','particulas in-place')

# 7) DOM de render: scratch arrays/sets/maps reutilizados; nenhuma mudanca de resolucao dos GIFs.
replace_once('''const entityLayer=$('#entityLayer');\nconst entityNodes=new Map();\nconst magePowerNodes=new Map();\nconst dragonProjectileNodes=new Map();''','''const entityLayer=$('#entityLayer');\nconst combatFxLayer=$('#combatFxLayer');\nconst entityNodes=new Map();\nconst magePowerNodes=new Map();\nconst dragonProjectileNodes=new Map();\n// Estruturas temporarias reutilizadas pelo render para reduzir GC/jank em batalhas grandes.\nconst renderVisibleEntities=[];\nconst renderVisibleIds=new Set();\nconst renderPresentIds=new Set();\nconst renderPresentMap=new Map();\nconst magePowerActiveIds=new Set();\nconst dragonProjectileActiveIds=new Set();''','scratch render')

replace_once(''' const margin=80;\n const visible=state.entities.filter(e=>(e.alive||e.deathStarted)&&e.x>=left-margin&&e.x<=right+margin&&e.y>=top-margin&&e.y<=bottom+margin);\n visible.forEach(drawEntityMarker);''',''' const margin=80;\n const visible=renderVisibleEntities;visible.length=0;\n for(const e of state.entities){\n   if((e.alive||e.deathStarted)&&e.x>=left-margin&&e.x<=right+margin&&e.y>=top-margin&&e.y<=bottom+margin)visible.push(e);\n }\n for(let i=0;i<visible.length;i++)drawEntityMarker(visible[i]);''','visible render scratch')

replace_once(''' syncEntityVisuals(visible,left,top,zoom,vw,vh);\n syncMagePowerEffects(left,top,zoom);\n syncDragonProjectileEffects(left,top,zoom);''',''' syncEntityVisuals(visible,left,top,zoom,vw,vh);\n syncMagePowerEffects(left,top,zoom,vw,vh);\n syncDragonProjectileEffects(left,top,zoom,vw,vh);''','viewport compartilhado efeitos')

replace_once('''function syncMagePowerEffects(left,top,zoom){\n const layer=$('#combatFxLayer'),active=new Set(),now=performance.now();\n const {w:screenW,h:screenH}=gameViewportSize();''','''function syncMagePowerEffects(left,top,zoom,screenW,screenH){\n const layer=combatFxLayer,active=magePowerActiveIds;active.clear();const now=performance.now();''','sync mage scratch')

replace_once('''function syncDragonProjectileEffects(left,top,zoom){\n           const layer=$('#combatFxLayer'),active=new Set();const {w:screenW,h:screenH}=gameViewportSize();''','''function syncDragonProjectileEffects(left,top,zoom,screenW,screenH){\n           const layer=combatFxLayer,active=dragonProjectileActiveIds;active.clear();''','sync dragon scratch')

replace_once('''function syncEntityVisuals(visible,left,top,zoom,screenW,screenH){\n const visibleIds=new Set();\n const presentIds=new Set(state.entities.filter(e=>e.alive||e.deathStarted).map(e=>e.id));\n const localNow=performance.now();''','''function syncEntityVisuals(visible,left,top,zoom,screenW,screenH){\n const visibleIds=renderVisibleIds;visibleIds.clear();\n const presentIds=renderPresentIds;presentIds.clear();\n const presentMap=renderPresentMap;presentMap.clear();\n for(const entity of state.entities){\n   presentMap.set(entity.id,entity);\n   if(entity.alive||entity.deathStarted)presentIds.add(entity.id);\n }\n const localNow=performance.now();''','sync entities scratch')

replace_once('''   el.style.left=sx+'px';\n   el.style.top=(sy-dragonLift*zoom)+'px';''','''   const visualTop=sy-dragonLift*zoom;\n   if(el._screenX!==sx){el._screenX=sx;el.style.left=sx+'px'}\n   if(el._screenY!==visualTop){el._screenY=visualTop;el.style.top=visualTop+'px'}''','cache posicao DOM')
replace_once("   el.style.zIndex=String((e.type==='dragon'&&e.dragonFlightState==='flying'?900:100)+Math.round(sy));",'''   const visualZ=(e.type==='dragon'&&e.dragonFlightState==='flying'?900:100)+Math.round(sy);\n   if(el._visualZ!==visualZ){el._visualZ=visualZ;el.style.zIndex=String(visualZ)}''','cache zIndex')

replace_once(''' const presentMap=new Map(state.entities.map(e=>[e.id,e]));\n for(const [id,el] of entityNodes){''',''' for(const [id,el] of entityNodes){''','remove presentMap frame allocation')

replace_once(" const fx=$('#combatFxLayer');if(fx)fx.innerHTML='';", " if(combatFxLayer)combatFxLayer.innerHTML='';", 'clear FX cache')

# 8) HUD/mensagem: nao escreve os mesmos valores no DOM 10x/s ou string vazia 60x/s.
replace_once("let last=performance.now(), messageUntil=0;\nfunction flash(text,secs=.8){$('#centerMessage').textContent=text;messageUntil=performance.now()+secs*1000}",'''let last=performance.now(), messageUntil=0;\nconst centerMessagePerfEl=$('#centerMessage');\nconst gameScreenPerfEl=$('#gameScreen');\nconst hudMainPerfEl=$('#hudMain'),hudSubPerfEl=$('#hudSub'),timerPerfEl=$('#timer'),aliveCountPerfEl=$('#aliveCount');\nconst buyWarriorPerfEl=$('#buyWarrior'),buyGolemPerfEl=$('#buyGolem'),buyMagePerfEl=$('#buyMage'),buyDragonPerfEl=$('#buyDragon');\nfunction perfSetText(el,value){if(el&&el.textContent!==value)el.textContent=value}\nfunction perfSetDisabled(el,value){value=!!value;if(el&&el.disabled!==value)el.disabled=value}\nfunction flash(text,secs=.8){perfSetText(centerMessagePerfEl,text);messageUntil=performance.now()+secs*1000}''','cache HUD refs')

replace_once("if(NetworkAdapter.online&&NetworkAdapter.isHost&&NetworkAdapter.roomStatus==='playing'&&$('#gameScreen').style.display!=='none'&&now-NetworkAdapter.lastStateAt>=100&&!NetworkAdapter.pushing){", "if(NetworkAdapter.online&&NetworkAdapter.isHost&&NetworkAdapter.roomStatus==='playing'&&gameScreenPerfEl.style.display!=='none'&&now-NetworkAdapter.lastStateAt>=100&&!NetworkAdapter.pushing){", 'loop gameScreen cache')
replace_once(" if(performance.now()>messageUntil)$('#centerMessage').textContent='';", " if(now>messageUntil&&centerMessagePerfEl.textContent)centerMessagePerfEl.textContent='';", 'mensagem sem write por frame')

hud_pattern=re.compile(r'''function updateHUD\(\)\{.*?\n\}\nfunction finishGame\(msg\)\{''',re.S)
hud_match=hud_pattern.search(text)
if not hud_match:
    raise SystemExit('bloco updateHUD nao encontrado')
new_hud='''function updateHUD(){\n if(gameScreenPerfEl.style.display==='none')return;\n if(state.mode==='pve'){\n    let p=0,en=0;\n    for(const e of state.entities){\n      if(!e.alive)continue;\n      if(e.team==='players')p++;else if(e.team==='enemy')en++;\n    }\n    perfSetText(hudMainPerfEl,`${state.round}/${state.rounds}`);\n    perfSetText(aliveCountPerfEl,`💀 ${en}\\n⚔️ ${p}`);\n    perfSetText(hudSubPerfEl,'');\n    perfSetText(timerPerfEl,fmt(state.timeLeft));\n  } else {\n    const me=localPlayer(),gems=me?.gems??0;\n    perfSetText(hudMainPerfEl,`${state.round}/${state.rounds}`);\n    perfSetText(hudSubPerfEl,`💎 ${gems}`);\n    perfSetText(timerPerfEl,state.phase==='prep'?fmt(state.prepLeft):fmt(state.timeLeft));\n    perfSetText(aliveCountPerfEl,'');\n    perfSetDisabled(buyWarriorPerfEl,state.phase!=='prep'||gems<75);\n    perfSetDisabled(buyGolemPerfEl,state.phase!=='prep'||gems<350);\n    perfSetDisabled(buyMagePerfEl,state.phase!=='prep'||gems<550);\n    perfSetDisabled(buyDragonPerfEl,state.phase!=='prep'||gems<350);\n  }\n}\nfunction finishGame(msg){'''
text=text[:hud_match.start()]+new_hud+text[hud_match.end():]

# 9) Isolamento de pintura da camada de efeitos, sem mudar tamanho/qualidade das imagens.
replace_once('''</style>''','''\n/* PERFORMANCE SWEEP: limita invalidacoes de layout/pintura dos efeitos de combate. */\n#combatFxLayer{contain:layout paint style}\n</style>''','contain FX')

# Garantias finais: nenhuma URL/asset de GIF ou mecanica-chave foi removida.
required=[
 'PERFORMANCE SWEEP 2026-09-07',
 'warFrameEnemiesByTeam',
 'renderVisibleEntities',
 'magePowerActiveIds',
 'dragonProjectileActiveIds',
 'width:96px !important',
 'width:78px !important',
 "$('#buyWarrior').onclick=()=>requestWarPurchase('buy-warrior');",
 "$('#buyGolem').onclick=()=>requestWarPurchase('buy-golem');",
 "$('#buyMage').onclick=()=>requestWarPurchase('buy-mage');",
 "$('#buyDragon').onclick=()=>requestWarPurchase('buy-dragon');",
 'REMOTE WAR ROUND TRANSITION SYNC',
 'scaleY(-1)',
 'assets/dragon/dragao-guerreiro-voando.gif',
 'assets/warrior/guerreiro-parado.gif',
]
for marker in required:
    if marker not in text:
        raise SystemExit('marcador final ausente: '+marker)

path.write_text(text,encoding='utf-8')
