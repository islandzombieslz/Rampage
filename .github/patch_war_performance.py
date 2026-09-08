from pathlib import Path

path = Path('index.html')
text = path.read_text(encoding='utf-8')


def replace_once(old, new, label):
    global text
    if old in text:
        text = text.replace(old, new, 1)
        return
    if new in text:
        return
    raise SystemExit(f'Trecho não encontrado: {label}')


def insert_after_once(marker, addition, label):
    global text
    target = marker + addition
    if target in text:
        return
    if marker not in text:
        raise SystemExit(f'Marcador não encontrado: {label}')
    text = text.replace(marker, target, 1)


# =========================================================
# TAMANHO VISUAL — SOMENTE REI E MAGOS
# =========================================================
# Guerreiro, Golem e Dragão permanecem exatamente com a escala atual.
# Rei e Mago recuam um pouco de 1.08 para 0.96.
replace_once(
    "const typeScale=e.type==='golem'?1.34:e.type==='mage'?1.08:e.type==='dragon'?1.16:e.type==='king'?1.08:1;",
    "const typeScale=e.type==='golem'?1.34:e.type==='mage'?.96:e.type==='dragon'?1.16:e.type==='king'?.96:1;",
    'escala visual de Rei/Mago',
)

# O GIF especial do corpo do Rei estava muito maior que idle/walk. Mantemos
# uma pequena folga para compensar transparência do asset, mas sem parecer outra escala.
replace_once(
    """.entity-visual.king-visual .entity-king-special{
  width:205px !important;height:238px !important;
  left:-34px !important;top:-50px !important;object-fit:contain !important;
}""",
    """.entity-visual.king-visual .entity-king-special{
  width:156px !important;height:184px !important;
  left:-9px !important;top:-20px !important;object-fit:contain !important;
}""",
    'proporção do special.gif do Rei',
)


# =========================================================
# PERFORMANCE 2 — EVITAR CAMADAS GPU DESNECESSÁRIAS
# =========================================================
# will-change em dezenas de projéteis/fragmentos força o navegador a promover
# muitos elementos para camadas compostas. Isso consome muita GPU/memória em celular.
replace_once(
    ".golem-rock-fragment{\n  position:absolute;\n  object-fit:contain;\n  transform-origin:center;\n  pointer-events:none;\n  will-change:transform,opacity;\n}",
    ".golem-rock-fragment{\n  position:absolute;\n  object-fit:contain;\n  transform-origin:center;\n  pointer-events:none;\n}",
    'will-change dos fragmentos do Golem',
)
replace_once(
    ".dragon-fireball-projectile{position:absolute;width:48px;height:48px;object-fit:contain;pointer-events:none;transform-origin:center;z-index:12;will-change:transform,left,top}",
    ".dragon-fireball-projectile{position:absolute;width:48px;height:48px;object-fit:contain;pointer-events:none;transform-origin:center;z-index:12}",
    'will-change das bolas de fogo',
)


# =========================================================
# PERFORMANCE 3 — REINICIAR ANIMAÇÕES SEM FORCED REFLOW
# =========================================================
# Cada golpe usava offsetWidth para reiniciar CSS animation. Com várias tropas
# isso força layout síncrono repetidas vezes no mesmo frame. Criamos nomes de
# animação alternativos visualmente idênticos e alternamos pelo serial do golpe.
insert_after_once(
    """@keyframes swordStrike{
  /* Guarda: cabo fixo na barriga, ponta apontada para cima */
  0%{
    transform:rotate(18deg);
  }

  /* Preparação: a PONTA recua para trás/acima.
     O cabo praticamente não muda de lugar porque é o pivô. */
  18%{
    transform:rotate(-48deg);
  }

  /* Corte: a ponta atravessa rapidamente a frente do personagem */
  54%{
    transform:rotate(112deg);
  }

  /* Pequeno overshoot natural */
  68%{
    transform:rotate(96deg);
  }

  /* Recuperação */
  100%{
    transform:rotate(18deg);
  }
}
""",
    """.entity-sword.attacking-alt{animation:swordStrikeAlt .30s cubic-bezier(.18,.75,.25,1)}
@keyframes swordStrikeAlt{
  0%{transform:rotate(18deg)}
  18%{transform:rotate(-48deg)}
  54%{transform:rotate(112deg)}
  68%{transform:rotate(96deg)}
  100%{transform:rotate(18deg)}
}
""",
    'animação alternativa do primeiro golpe',
)
insert_after_once(
    """@keyframes swordStrike2{
  0%{transform:rotate(18deg)}
  18%{transform:rotate(108deg)}
  54%{transform:rotate(-58deg)}
  68%{transform:rotate(-42deg)}
  100%{transform:rotate(18deg)}
}
""",
    """.entity-sword.attacking2-alt{animation:swordStrike2Alt .30s cubic-bezier(.18,.75,.25,1)}
@keyframes swordStrike2Alt{
  0%{transform:rotate(18deg)}
  18%{transform:rotate(108deg)}
  54%{transform:rotate(-58deg)}
  68%{transform:rotate(-42deg)}
  100%{transform:rotate(18deg)}
}
""",
    'animação alternativa do segundo golpe',
)
insert_after_once(
    """@keyframes slashWind2{
  0%,22%{opacity:0;transform:rotate(105deg) scale(.45)}
  38%{opacity:.25;transform:rotate(65deg) scale(.72)}
  56%{opacity:.95;transform:rotate(-12deg) scale(1.05)}
  76%{opacity:.48;transform:rotate(-62deg) scale(1.18)}
  100%{opacity:0;transform:rotate(-92deg) scale(1.28)}
}
""",
    """.entity-slash.attacking2-alt{animation:slashWind2Alt .30s ease-out}
@keyframes slashWind2Alt{
  0%,22%{opacity:0;transform:rotate(105deg) scale(.45)}
  38%{opacity:.25;transform:rotate(65deg) scale(.72)}
  56%{opacity:.95;transform:rotate(-12deg) scale(1.05)}
  76%{opacity:.48;transform:rotate(-62deg) scale(1.18)}
  100%{opacity:0;transform:rotate(-92deg) scale(1.28)}
}
""",
    'rastro alternativo do segundo golpe',
)
insert_after_once(
    """@keyframes slashWind{
  0%,22%{
    opacity:0;
    transform:rotate(-85deg) scale(.45);
  }
  38%{
    opacity:.25;
    transform:rotate(-35deg) scale(.72);
  }
  56%{
    opacity:.95;
    transform:rotate(38deg) scale(1.05);
  }
  76%{
    opacity:.48;
    transform:rotate(84deg) scale(1.18);
  }
  100%{
    opacity:0;
    transform:rotate(110deg) scale(1.28);
  }
}
""",
    """.entity-slash.attacking-alt{animation:slashWindAlt .30s ease-out}
@keyframes slashWindAlt{
  0%,22%{opacity:0;transform:rotate(-85deg) scale(.45)}
  38%{opacity:.25;transform:rotate(-35deg) scale(.72)}
  56%{opacity:.95;transform:rotate(38deg) scale(1.05)}
  76%{opacity:.48;transform:rotate(84deg) scale(1.18)}
  100%{opacity:0;transform:rotate(110deg) scale(1.28)}
}
""",
    'rastro alternativo do primeiro golpe',
)

# Reação de dano também forçava offsetWidth em cada hit.
insert_after_once(
    """@keyframes hitTilt{
  0%{transform:scaleX(var(--face)) rotate(0deg)}
  38%{transform:scaleX(var(--face)) rotate(var(--impact-tilt,12deg))}
  100%{transform:scaleX(var(--face)) rotate(0deg)}
}
""",
    """.entity-facing.hit-react-alt{
  animation:
    hitTiltAlt .20s cubic-bezier(.18,.72,.2,1),
    hitFlashAlt .17s steps(1,end);
}
@keyframes hitFlashAlt{
  0%,72%{filter:sepia(.92) saturate(9) hue-rotate(318deg) brightness(.90) contrast(1.08)}
  73%,100%{filter:none}
}
@keyframes hitTiltAlt{
  0%{transform:scaleX(var(--face)) rotate(0deg)}
  38%{transform:scaleX(var(--face)) rotate(var(--impact-tilt,12deg))}
  100%{transform:scaleX(var(--face)) rotate(0deg)}
}
""",
    'reação alternativa de hit',
)

old_hit_render = """   if((el._lastHitSerial||0)!==(e.hitSerial||0)){
     el._lastHitSerial=e.hitSerial||0;
     const tilt=((e.hitDirX||0)>=0?1:-1)*(e.hitTilt||13);
     el._facing.style.setProperty('--impact-tilt',tilt+'deg');
     el._facing.classList.remove('hit-react');
     void el._facing.offsetWidth;
     el._facing.classList.add('hit-react');
     setTimeout(()=>el._facing?.classList.remove('hit-react'),210);
   }
"""
new_hit_render = """   if((el._lastHitSerial||0)!==(e.hitSerial||0)){
     el._lastHitSerial=e.hitSerial||0;
     const tilt=((e.hitDirX||0)>=0?1:-1)*(e.hitTilt||13);
     el._facing.style.setProperty('--impact-tilt',tilt+'deg');
     const hitClass=((e.hitSerial||0)&1)?'hit-react':'hit-react-alt';
     const hitToken=(el._hitAnimToken||0)+1;el._hitAnimToken=hitToken;
     el._facing.classList.remove('hit-react','hit-react-alt');
     el._facing.classList.add(hitClass);
     setTimeout(()=>{
       if(el._hitAnimToken===hitToken)el._facing?.classList.remove(hitClass);
     },210);
   }
"""
replace_once(old_hit_render, new_hit_render, 'hit sem forced reflow')
replace_once(
    "     el._facing.classList.remove('hit-react');\n",
    "     el._facing.classList.remove('hit-react','hit-react-alt');\n",
    'limpeza de hit na morte',
)

old_attack_restart = """   if(el.dataset.attackSerial!==String(e.attackSerial)){
     el.dataset.attackSerial=String(e.attackSerial);
     if((e.type==='warrior'||e.type==='king') && e.attackSerial>0&&!e.deathStarted&&!e.pendingKingSpecial && el._sword && el._slash){
       el._sword.classList.remove('attacking','attacking2');
       el._slash.classList.remove('attacking','attacking2');
       void el._sword.offsetWidth;
       void el._slash.offsetWidth;
       const attackClass=e.comboStep===2?'attacking2':'attacking';
       el._sword.classList.add(attackClass);
       el._slash.classList.add(attackClass);
     }
   }
"""
new_attack_restart = """   if(el.dataset.attackSerial!==String(e.attackSerial)){
     el.dataset.attackSerial=String(e.attackSerial);
     if((e.type==='warrior'||e.type==='king') && e.attackSerial>0&&!e.deathStarted&&!e.pendingKingSpecial && el._sword && el._slash){
       el._sword.classList.remove('attacking','attacking-alt','attacking2','attacking2-alt');
       el._slash.classList.remove('attacking','attacking-alt','attacking2','attacking2-alt');
       const alt=((e.attackSerial||0)&1)===0;
       const attackClass=e.comboStep===2?(alt?'attacking2-alt':'attacking2'):(alt?'attacking-alt':'attacking');
       el._sword.classList.add(attackClass);
       el._slash.classList.add(attackClass);
     }
   }
"""
replace_once(old_attack_restart, new_attack_restart, 'ataques sem forced reflow')


# =========================================================
# PERFORMANCE 4 — MAPA DE ENTIDADES PARA PROJÉTEIS/QUEIMADURAS
# =========================================================
# Antes cada bola de fogo fazia state.entities.find() a cada frame para localizar
# alvo (e outra busca no impacto). Isso vira O(projéteis * tropas). Um Map por frame
# mantém exatamente os mesmos alvos/impactos em O(1).
insert_after_once(
    "const warFrameEnemiesByTeam=new Map();\n",
    """const warEntityById=new Map();
function rebuildWarEntityIdMap(){
 warEntityById.clear();
 for(const e of state.entities)warEntityById.set(e.id,e);
 return warEntityById;
}
""",
    'mapa de entidades da Guerra',
)
replace_once(
    "   const now=performance.now();\n   updateDragonProjectiles(dt);updateDragonBurns(now);\n   const living=state.entities.filter(e=>e.alive);",
    "   const now=performance.now();\n   const entityById=rebuildWarEntityIdMap();\n   updateDragonProjectiles(dt,entityById);updateDragonBurns(now,entityById);\n   const living=state.entities.filter(e=>e.alive);",
    'uso do mapa no updateWar',
)

replace_once(
    """          function dragonBurnAttacker(target){
           return state.entities.find(e=>e.id===target.dragonBurnSourceId)||{id:'dragon-burn',type:'dragon',x:Number(target.dragonBurnSourceX)||target.x,y:Number(target.dragonBurnSourceY)||target.y,heading:0,lastCombatAt:0};
          }
          function updateDragonBurns(now){
""",
    """          function dragonBurnAttacker(target,entityById=warEntityById){
           return entityById.get(target.dragonBurnSourceId)||{id:'dragon-burn',type:'dragon',x:Number(target.dragonBurnSourceX)||target.x,y:Number(target.dragonBurnSourceY)||target.y,heading:0,lastCombatAt:0};
          }
          function updateDragonBurns(now,entityById=warEntityById){
""",
    'lookup da fonte da queimadura',
)
replace_once(
    "               const burnSource=dragonBurnAttacker(target);",
    "               const burnSource=dragonBurnAttacker(target,entityById);",
    'mapa na queimadura',
)

old_projectile_update = """          function updateDragonProjectiles(dt){
           const now=performance.now(),list=state.dragonProjectiles||[];
           for(let i=list.length-1;i>=0;i--){
             const p=list[i],target=state.entities.find(t=>t.id===p.targetId&&t.alive&&t.team!==p.team);
             if(target){p.targetX=target.x;p.targetY=target.y}
             const tx=Number(p.targetX),ty=Number(p.targetY);
             if(!Number.isFinite(tx)||!Number.isFinite(ty)||now>Number(p.expireAt||0)){list.splice(i,1);continue}
             const dx=tx-p.x,dy=ty-p.y,d=Math.hypot(dx,dy)||1,step=DRAGON_FIREBALL_SPEED*dt;
             p.vx=dx/d*DRAGON_FIREBALL_SPEED;p.vy=dy/d*DRAGON_FIREBALL_SPEED;
             if(d<=Math.max(18,step+8)){
               p.x=tx;p.y=ty;
               if(target){
                 const source=state.entities.find(e=>e.id===p.sourceId)||{id:p.sourceId,type:'dragon',x:p.x,y:p.y,heading:0,lastCombatAt:0};
                 applyCombatHit(target,source,DRAGON_FIREBALL_DAMAGE,{knockForce:105,knockTime:.06,tilt:6});
                 if(target.alive)igniteDragonBurn(target,source);
               }
               list.splice(i,1);continue;
             }
             p.x+=p.vx*dt;p.y+=p.vy*dt;
           }
          }
"""
new_projectile_update = """          function updateDragonProjectiles(dt,entityById=warEntityById){
           const now=performance.now(),list=state.dragonProjectiles||[];
           for(let i=list.length-1;i>=0;i--){
             const p=list[i],candidate=entityById.get(p.targetId);
             const target=candidate&&candidate.alive&&candidate.team!==p.team?candidate:null;
             if(target){p.targetX=target.x;p.targetY=target.y}
             const tx=Number(p.targetX),ty=Number(p.targetY);
             if(!Number.isFinite(tx)||!Number.isFinite(ty)||now>Number(p.expireAt||0)){list.splice(i,1);continue}
             const dx=tx-p.x,dy=ty-p.y,d=Math.hypot(dx,dy)||1,step=DRAGON_FIREBALL_SPEED*dt;
             p.vx=dx/d*DRAGON_FIREBALL_SPEED;p.vy=dy/d*DRAGON_FIREBALL_SPEED;
             if(d<=Math.max(18,step+8)){
               p.x=tx;p.y=ty;
               if(target){
                 const source=entityById.get(p.sourceId)||{id:p.sourceId,type:'dragon',x:p.x,y:p.y,heading:0,lastCombatAt:0};
                 applyCombatHit(target,source,DRAGON_FIREBALL_DAMAGE,{knockForce:105,knockTime:.06,tilt:6});
                 if(target.alive)igniteDragonBurn(target,source);
               }
               list.splice(i,1);continue;
             }
             p.x+=p.vx*dt;p.y+=p.vy*dt;
           }
          }
"""
replace_once(old_projectile_update, new_projectile_update, 'update otimizado dos projéteis')


# =========================================================
# PERFORMANCE 5 — BOLAS DE FOGO: CACHE COMPARTILHADO + POOL DOM
# =========================================================
# restartGif criava uma Object URL diferente para CADA bola. Mesmo usando o mesmo
# arquivo, isso impede o navegador de compartilhar o recurso/decodificação. Projétil
# é um loop contínuo, então usa a mesma URL do asset e recicla nós DOM sem qualidade menor.
replace_once(
    "const dragonProjectileNodes=new Map();\n",
    "const dragonProjectileNodes=new Map();\nconst dragonProjectilePool=[];\nconst MAX_DRAGON_PROJECTILE_POOL=48;\n",
    'pool de projéteis',
)
insert_after_once(
    "const dragonProjectileActiveIds=new Set();\n",
    """
function acquireDragonProjectileNode(layer){
 let img=dragonProjectilePool.pop();
 if(!img){
   img=document.createElement('img');
   img.className='dragon-fireball-projectile';
   img.draggable=false;
   img.dataset.assetKey='dragonFireball';
 }
 if(!img.hasAttribute('src'))img.src=ASSETS.dragonFireball;
 if(img.parentElement!==layer)layer.appendChild(img);
 img.style.visibility='visible';
 return img;
}
function recycleDragonProjectileNode(img){
 if(!img)return;
 img.style.visibility='hidden';
 img.removeAttribute('src');
 img._projectileZoom=NaN;
 if(dragonProjectilePool.length<MAX_DRAGON_PROJECTILE_POOL)dragonProjectilePool.push(img);
 else img.remove();
}
""",
    'helpers do pool de projéteis',
)

old_projectile_sync = """function syncDragonProjectileEffects(left,top,zoom,screenW,screenH){
           const layer=combatFxLayer,active=dragonProjectileActiveIds;active.clear();
           for(const p of state.dragonProjectiles||[]){
             const sx=(p.x-left)*zoom,sy=(p.y-top)*zoom,margin=90;if(sx<-margin||sx>screenW+margin||sy<-margin||sy>screenH+margin)continue;
             active.add(p.id);let img=dragonProjectileNodes.get(p.id);
             if(!img){img=document.createElement('img');img.className='dragon-fireball-projectile';img.draggable=false;restartGif(img,'dragonFireball',p.serial||p.id);layer.appendChild(img);dragonProjectileNodes.set(p.id,img)}
             const angle=Math.atan2(Number(p.vy)||0,Number(p.vx)||1),size=48*zoom;
             img.style.left=sx+'px';img.style.top=sy+'px';img.style.width=size+'px';img.style.height=size+'px';img.style.transform=`translate(-50%,-50%) rotate(${angle-Math.PI/2}rad) scaleY(-1)`;img.style.visibility='visible';
           }
           for(const [id,img] of dragonProjectileNodes)if(!active.has(id)){releaseGifObjectUrl(img);img.remove();dragonProjectileNodes.delete(id)}
          }
"""
new_projectile_sync = """function syncDragonProjectileEffects(left,top,zoom,screenW,screenH){
           const layer=combatFxLayer,active=dragonProjectileActiveIds;active.clear();
           for(const p of state.dragonProjectiles||[]){
             const sx=(p.x-left)*zoom,sy=(p.y-top)*zoom,margin=90;if(sx<-margin||sx>screenW+margin||sy<-margin||sy>screenH+margin)continue;
             active.add(p.id);let img=dragonProjectileNodes.get(p.id);
             if(!img){img=acquireDragonProjectileNode(layer);dragonProjectileNodes.set(p.id,img)}
             const angle=Math.atan2(Number(p.vy)||0,Number(p.vx)||1);
             if(img._projectileZoom!==zoom){
               img._projectileZoom=zoom;
               const size=48*zoom;img.style.width=size+'px';img.style.height=size+'px';
             }
             img.style.left=sx+'px';img.style.top=sy+'px';img.style.transform=`translate(-50%,-50%) rotate(${angle-Math.PI/2}rad) scaleY(-1)`;img.style.visibility='visible';
           }
           for(const [id,img] of dragonProjectileNodes)if(!active.has(id)){recycleDragonProjectileNode(img);dragonProjectileNodes.delete(id)}
          }
"""
replace_once(old_projectile_sync, new_projectile_sync, 'render/pool das bolas de fogo')


# =========================================================
# PERFORMANCE 6 — QUEIMADURA DO DRAGÃO: 1 ELEMENTO, 1 GIF COMPARTILHADO
# =========================================================
# Antes cada alvo queimando criava 2 ou 3 <img> e cada um ganhava Object URL única.
# Agora o MESMO GIF é desenhado como 2/3 camadas de background no único layer da
# queimadura. Mesma resolução/asset/posições, muito menos DOM e decodificadores.
old_burn_css = """          .dragon-burn-layer{position:absolute;left:50%;top:42%;width:76px;height:76px;transform:translate(-50%,-50%);pointer-events:none;z-index:9;opacity:0}
          .dragon-burn-layer img{position:absolute;width:27px;height:27px;object-fit:contain;pointer-events:none;transform:translate(-50%,-50%)}
          .dragon-burn-layer img:nth-child(1){left:28%;top:55%}
          .dragon-burn-layer img:nth-child(2){left:68%;top:38%}
          .dragon-burn-layer img:nth-child(3){left:51%;top:70%}
"""
new_burn_css = """          .dragon-burn-layer{position:absolute;left:50%;top:42%;width:76px;height:76px;transform:translate(-50%,-50%);pointer-events:none;z-index:9;opacity:0;background-repeat:no-repeat}
"""
replace_once(old_burn_css, new_burn_css, 'CSS compacto da queimadura')

old_burn_sync = """          function syncDragonBurnOnEntity(el,e,now){
           const remaining=(Number(e.dragonBurnUntil)||0)-now;if(!e.alive||remaining<=0){if(el._dragonBurnLayer)el._dragonBurnLayer.style.opacity='0';return}
           let layer=el._dragonBurnLayer;const serial=Number(e.dragonBurnSerial)||0,count=clamp(Number(e.dragonBurnFlameCount)||2,2,3);
           if(!layer){layer=document.createElement('div');layer.className='dragon-burn-layer';el.appendChild(layer);el._dragonBurnLayer=layer;layer.dataset.serial='-1'}
           if(layer.dataset.serial!==String(serial)||layer.children.length!==count){[...layer.querySelectorAll('img')].forEach(releaseGifObjectUrl);layer.innerHTML='';for(let i=0;i<count;i++){const img=document.createElement('img');img.draggable=false;restartGif(img,'dragonFireball',serial*10+i);layer.appendChild(img)}layer.dataset.serial=String(serial)}
           const started=Number(e.dragonBurnStartedAt)||now,fadeIn=clamp((now-started)/350,0,1),fadeOut=clamp(remaining/500,0,1);layer.style.opacity=String(Math.min(fadeIn,fadeOut));
          }
"""
new_burn_sync = """          function syncDragonBurnOnEntity(el,e,now){
           const remaining=(Number(e.dragonBurnUntil)||0)-now;
           let layer=el._dragonBurnLayer;
           if(!e.alive||remaining<=0){
             if(layer){layer.style.opacity='0';layer.style.backgroundImage='none';layer.dataset.serial='-1';layer.dataset.count='0'}
             return;
           }
           const serial=Number(e.dragonBurnSerial)||0,count=clamp(Number(e.dragonBurnFlameCount)||2,2,3);
           if(!layer){layer=document.createElement('div');layer.className='dragon-burn-layer';el.appendChild(layer);el._dragonBurnLayer=layer;layer.dataset.serial='-1';layer.dataset.count='0'}
           if(layer.dataset.serial!==String(serial)||layer.dataset.count!==String(count)){
             const fire=`url("${ASSETS.dragonFireball}")`;
             layer.style.backgroundImage=count===3?`${fire},${fire},${fire}`:`${fire},${fire}`;
             layer.style.backgroundSize=count===3?'27px 27px,27px 27px,27px 27px':'27px 27px,27px 27px';
             layer.style.backgroundPosition=count===3?'28% 55%,68% 38%,51% 70%':'28% 55%,68% 38%';
             layer.style.backgroundRepeat='no-repeat';
             layer.dataset.serial=String(serial);layer.dataset.count=String(count);
           }
           const started=Number(e.dragonBurnStartedAt)||now,fadeIn=clamp((now-started)/350,0,1),fadeOut=clamp(remaining/500,0,1);layer.style.opacity=String(Math.min(fadeIn,fadeOut));
          }
"""
replace_once(old_burn_sync, new_burn_sync, 'queimadura compactada sem perda do asset')


# =========================================================
# PERFORMANCE 7 — POOL DOS FRAGMENTOS DO GOLEM
# =========================================================
# São PNGs, então a qualidade fica idêntica. Apenas evitamos criar/destruir até
# 16 nós novos a cada especial quando podemos reciclar os mesmos elementos.
insert_after_once(
    "const kingPowerActiveIds=new Set();\n",
    "const golemRockPool=[];\nconst MAX_GOLEM_ROCK_POOL=96;\n",
    'pool de pedras do Golem',
)
insert_after_once(
    "function spawnGolemRockBurst(golem){\n",
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
    'helpers do pool de pedras',
)
replace_once(
    "     fx.el?.remove();\n     effects.splice(i,1);",
    "     if(fx.el)recycleGolemRockNode(fx.el);\n     effects.splice(i,1);",
    'reciclagem de pedra ao terminar',
)
replace_once(
    """   let el=fx.el;
   if(!el){
     el=document.createElement('img');
     el.className='golem-rock-fragment';
     el.src=ASSETS.golemRocks;
     $('#combatFxLayer')?.appendChild(el);
     fx.el=el;
   }
""",
    """   let el=fx.el;
   if(!el){
     el=acquireGolemRockNode();
     fx.el=el;
   }
""",
    'aquisição de pedra pelo pool',
)

# Limpeza dos pools quando a rodada/tela é desmontada.
replace_once(
    " dragonProjectileNodes.clear();\n entityNodes.clear();",
    " dragonProjectileNodes.clear();\n dragonProjectilePool.length=0;\n golemRockPool.length=0;\n entityNodes.clear();",
    'limpeza dos pools',
)


# =========================================================
# VALIDAÇÕES DE INTEGRIDADE
# =========================================================
required = [
    'FIREBASE RTDB, HOST AUTORITATIVO',
    'WAR PERFORMANCE 2026-09-08',
    'REMOTE WAR ROUND TRANSITION SYNC',
    "e.hp=e.maxHp=200;",
    "e.shield=e.maxShield=200;",
    "e.damage=25;",
    "kingNormalCount)||0)>=6",
    "Math.min(6,(Number(e.kingNormalCount)||0)+1)",
    "e.type==='mage'?.96:e.type==='dragon'?1.16:e.type==='king'?.96:1;",
    'width:156px !important;height:184px !important;',
    'const KING_POWER_DELAY_MS=1000;',
    'const warEntityById=new Map();',
    'updateDragonProjectiles(dt,entityById);updateDragonBurns(now,entityById);',
    'const dragonProjectilePool=[];',
    'img.src=ASSETS.dragonFireball;',
    'recycleDragonProjectileNode(img)',
    'backgroundImage=count===3',
    'const golemRockPool=[];',
    'recycleGolemRockNode(fx.el)',
    "'attacking-alt'",
    "'hit-react-alt'",
    'syncKingPowerEffects(left,top,zoom,vw,vh);',
]
missing = [item for item in required if item not in text]
if missing:
    raise SystemExit('Validação falhou: ' + ' | '.join(missing))

# Não pode voltar a existir forced reflow no caminho quente de ataque/hit.
if "void el._sword.offsetWidth" in text or "void el._slash.offsetWidth" in text:
    raise SystemExit('Forced reflow de ataque ainda presente')
if "void el._facing.offsetWidth;\n     el._facing.classList.add('hit-react')" in text:
    raise SystemExit('Forced reflow de hit ainda presente')

# Projéteis/queimadura não podem voltar a criar Object URL individual da bola de fogo.
if "restartGif(img,'dragonFireball',p.serial||p.id)" in text:
    raise SystemExit('Projétil voltou a usar Object URL individual')
if "restartGif(img,'dragonFireball',serial*10+i)" in text:
    raise SystemExit('Queimadura voltou a criar vários decodificadores')

if 'i.postimg.cc' in text:
    raise SystemExit('Referência ao Postimg reapareceu')

path.write_text(text, encoding='utf-8')
print('Rei/Magos reduzidos e Guerra otimizada: menos forced reflow, menos camadas GPU, lookup O(1), fireballs/queimaduras compartilhadas e pools de DOM.')
