from pathlib import Path

path=Path('index.html')
text=path.read_text(encoding='utf-8')

MARKER='GIF SWITCH STABILITY 2026-09-08'
if MARKER in text:
    print('GIF stability patch already applied.')
    raise SystemExit(0)


def replace_once(old,new,label):
    global text
    if old not in text:
        raise SystemExit(f'Trecho não encontrado: {label}')
    text=text.replace(old,new,1)


# =========================================================
# 1) TROCAS IDLE/WALK/FLY SEM DESCARREGAR O GIF A CADA FRAME
# =========================================================
old_loop_block="""const ENTITY_LOOP_STATES=new Set(['idle','walk','ground','fly']);
// WAR PERFORMANCE 2026-09-08: only active looping GIFs stay decoded.
// Um GIF invisível com opacity:0 continua consumindo CPU/memória no navegador.
// A URL do asset não muda e nenhum GIF é removido do jogo: só pausamos o loop oculto.
function entitySpriteForState(el,stateName){
 if(stateName==='idle')return el._idle;
 if(stateName==='walk')return el._walk;
 if(stateName==='ground')return el._dragonGround;
 if(stateName==='fly')return el._dragonFly;
 if(stateName==='attack')return el._golemAttack;
 if(stateName==='special')return el._golemSpecial||el._mageSpecial||el._kingSpecial;
 if(stateName==='takeoff')return el._dragonTakeoff;
 if(stateName==='dragonAttack')return el._dragonAttack;
 return null;
}
function ensureEntityLoopGif(el,stateName,img=null){
 if(!ENTITY_LOOP_STATES.has(stateName))return;
 img=img||entitySpriteForState(el,stateName);
 const key=el._gifKeys?.[stateName];
 const src=key?ASSETS[key]:null;
 if(!img||!src||img.hasAttribute('src'))return;
 img.dataset.assetKey=key;
 img.src=src;
}
function suspendEntityLoopGif(el){
 const stateName=el?.dataset?.anim||'';
 if(!ENTITY_LOOP_STATES.has(stateName))return;
 stopGif(entitySpriteForState(el,stateName));
}
"""
new_loop_block="""const ENTITY_LOOP_STATE_LIST=['idle','walk','ground','fly'];
const ENTITY_LOOP_STATES=new Set(ENTITY_LOOP_STATE_LIST);
const ENTITY_LOOP_GIF_GRACE_MS=1400;
// GIF SWITCH STABILITY 2026-09-08
// Idle/andar/voar não perdem mais o src imediatamente em toda troca. Esses GIFs
// são grandes; remover e recolocar o src repetidamente força novo ciclo de
// carregamento/decodificação e provoca a piscada. O estado anterior fica oculto
// com display:none e só é descarregado depois de uma pequena janela de graça.
// Fora da câmera todos os loops continuam sendo suspensos imediatamente.
function entitySpriteForState(el,stateName){
 if(stateName==='idle')return el._idle;
 if(stateName==='walk')return el._walk;
 if(stateName==='ground')return el._dragonGround;
 if(stateName==='fly')return el._dragonFly;
 if(stateName==='attack')return el._golemAttack;
 if(stateName==='special')return el._golemSpecial||el._mageSpecial||el._kingSpecial;
 if(stateName==='takeoff')return el._dragonTakeoff;
 if(stateName==='dragonAttack')return el._dragonAttack;
 return null;
}
function clearEntityLoopSuspendTimer(el,stateName){
 const timers=el?._loopGifSuspendTimers;
 if(!timers)return;
 const timer=timers.get(stateName);
 if(timer){clearTimeout(timer);timers.delete(stateName)}
}
function clearEntityLoopSuspendTimers(el){
 const timers=el?._loopGifSuspendTimers;
 if(!timers)return;
 for(const timer of timers.values())clearTimeout(timer);
 timers.clear();
}
function ensureEntityLoopGif(el,stateName,img=null){
 if(!ENTITY_LOOP_STATES.has(stateName))return;
 clearEntityLoopSuspendTimer(el,stateName);
 img=img||entitySpriteForState(el,stateName);
 const key=el._gifKeys?.[stateName];
 const src=key?ASSETS[key]:null;
 if(!img||!src)return;
 img.dataset.assetKey=key;
 img.decoding='async';
 img.style.display='block';
 if(!img.hasAttribute('src'))img.src=src;
}
function scheduleEntityLoopGifSuspend(el,stateName){
 if(!el||!ENTITY_LOOP_STATES.has(stateName)||el.dataset.anim===stateName)return;
 const img=entitySpriteForState(el,stateName);
 if(!img||!img.hasAttribute('src'))return;
 let timers=el._loopGifSuspendTimers;
 if(!timers){timers=new Map();el._loopGifSuspendTimers=timers}
 clearEntityLoopSuspendTimer(el,stateName);
 const timer=setTimeout(()=>{
   timers.delete(stateName);
   if(el.dataset.anim===stateName)return;
   img.style.display='none';
   stopGif(img);
 },ENTITY_LOOP_GIF_GRACE_MS);
 timers.set(stateName,timer);
}
function suspendEntityLoopGif(el){
 if(!el)return;
 clearEntityLoopSuspendTimers(el);
 for(const stateName of ENTITY_LOOP_STATE_LIST){
   const img=entitySpriteForState(el,stateName);
   if(!img)continue;
   img.style.display='none';
   stopGif(img);
 }
}
"""
replace_once(old_loop_block,new_loop_block,'controle dos GIFs persistentes')

old_same=""" if(previous===desired){
   if(desiredImg){desiredImg.style.opacity='1';desiredImg.classList.add('active-sprite')}
   return false;
 }
"""
new_same=""" if(previous===desired){
   if(desiredImg){desiredImg.style.display='block';desiredImg.style.opacity='1';desiredImg.classList.add('active-sprite')}
   return false;
 }
"""
replace_once(old_same,new_same,'estado de sprite já ativo')

old_switch="""   if(stateName===desired){
     img.style.opacity='1';
     img.classList.add('active-sprite');
   }else if(stateName!==previous){
     img.style.opacity='0';
     img.classList.remove('active-sprite');
   }
"""
new_switch="""   if(stateName===desired){
     img.style.display='block';
     img.style.opacity='1';
     img.classList.add('active-sprite');
   }else if(stateName!==previous){
     img.style.display='none';
     img.style.opacity='0';
     img.classList.remove('active-sprite');
   }
"""
replace_once(old_switch,new_switch,'pré-troca sem piscar')

old_finalize="""     const active=stateName===desired;
     img.style.opacity=active?'1':'0';
     img.classList.toggle('active-sprite',active);
   }

   // Loops persistentes invisíveis deixam de decodificar. Na próxima troca,
   // ensureEntityLoopGif recoloca a mesma URL e o cache do navegador é reutilizado.
   if(ENTITY_LOOP_STATES.has(previous)&&previous!==desired)stopGif(entitySpriteForState(el,previous));
"""
new_finalize="""     const active=stateName===desired;
     img.style.display=active?'block':'none';
     img.style.opacity=active?'1':'0';
     img.classList.toggle('active-sprite',active);
   }

   // O loop anterior fica pronto por pouco tempo para uma possível troca de volta.
   // Se a unidade estabilizar no novo estado, aí sim o src antigo é removido.
   if(ENTITY_LOOP_STATES.has(previous)&&previous!==desired) scheduleEntityLoopGifSuspend(el,previous);
"""
replace_once(old_finalize,new_finalize,'finalização da troca com janela de graça')

# O navegador pode decodificar os frames fora do caminho crítico do frame atual.
old_keys=""" else el._gifKeys={idle:e.variant==='female'?'femaleIdle':'idle',walk:e.variant==='female'?'femaleWalk':'walk'};
 // O nó nasce em idle/ground. O segundo loop pesado só recebe src quando virar ativo.
"""
new_keys=""" else el._gifKeys={idle:e.variant==='female'?'femaleIdle':'idle',walk:e.variant==='female'?'femaleWalk':'walk'};
 for(const img of el.querySelectorAll('img'))img.decoding='async';
 // O nó nasce em idle/ground. O segundo loop pesado só recebe src quando virar ativo.
"""
replace_once(old_keys,new_keys,'decodificação assíncrona dos sprites')


# =========================================================
# 2) PROJÉTEIS DO DRAGÃO: POOL SEM REMOVE/ADD DE SRC EM RAJADAS
# =========================================================
old_projectiles="""function acquireDragonProjectileNode(layer){
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
"""
new_projectiles="""const DRAGON_PROJECTILE_GIF_GRACE_MS=850;
function acquireDragonProjectileNode(layer){
 let img=dragonProjectilePool.pop();
 if(!img){
   img=document.createElement('img');
   img.className='dragon-fireball-projectile';
   img.draggable=false;
   img.decoding='async';
   img.dataset.assetKey='dragonFireball';
 }
 if(img._poolGifSuspendTimer){clearTimeout(img._poolGifSuspendTimer);img._poolGifSuspendTimer=null}
 if(!img.hasAttribute('src'))img.src=ASSETS.dragonFireball;
 if(img.parentElement!==layer)layer.appendChild(img);
 img.style.display='block';
 img.style.visibility='visible';
 return img;
}
function recycleDragonProjectileNode(img){
 if(!img)return;
 img.style.visibility='hidden';
 img.style.display='none';
 img._projectileZoom=NaN;
 if(img._poolGifSuspendTimer){clearTimeout(img._poolGifSuspendTimer);img._poolGifSuspendTimer=null}
 if(dragonProjectilePool.length<MAX_DRAGON_PROJECTILE_POOL){
   img._poolGifSuspendTimer=setTimeout(()=>{
     img._poolGifSuspendTimer=null;
     if(img.style.visibility==='hidden')stopGif(img);
   },DRAGON_PROJECTILE_GIF_GRACE_MS);
   dragonProjectilePool.push(img);
 }else{
   stopGif(img);
   img.remove();
 }
}
"""
replace_once(old_projectiles,new_projectiles,'pool estável das bolas de fogo')


# =========================================================
# 3) LIMPEZA DOS TIMERS PARA NÃO DEIXAR TRABALHO PENDENTE
# =========================================================
old_remove="""     if(entity && !transient && localNow-lastSeen>1400){
       el.querySelectorAll('img').forEach(releaseGifObjectUrl);
       el.remove();
       entityNodes.delete(id);
     }
"""
new_remove="""     if(entity && !transient && localNow-lastSeen>1400){
       clearEntityLoopSuspendTimers(el);
       el.querySelectorAll('img').forEach(releaseGifObjectUrl);
       el.remove();
       entityNodes.delete(id);
     }
"""
replace_once(old_remove,new_remove,'limpeza do nó fora da câmera')

old_clear="""function clearEntityVisuals(){
 for(const el of entityNodes.values())el.querySelectorAll('img').forEach(releaseGifObjectUrl);
 for(const img of magePowerNodes.values())releaseGifObjectUrl(img);
 for(const img of kingPowerNodes.values())releaseGifObjectUrl(img);
 for(const img of dragonProjectileNodes.values())releaseGifObjectUrl(img);
 entityLayer.innerHTML='';
"""
new_clear="""function clearEntityVisuals(){
 for(const el of entityNodes.values()){
   clearEntityLoopSuspendTimers(el);
   el.querySelectorAll('img').forEach(releaseGifObjectUrl);
 }
 for(const img of magePowerNodes.values())releaseGifObjectUrl(img);
 for(const img of kingPowerNodes.values())releaseGifObjectUrl(img);
 for(const img of dragonProjectileNodes.values()){
   if(img._poolGifSuspendTimer)clearTimeout(img._poolGifSuspendTimer);
   releaseGifObjectUrl(img);
 }
 for(const img of dragonProjectilePool){
   if(img._poolGifSuspendTimer)clearTimeout(img._poolGifSuspendTimer);
   stopGif(img);
 }
 entityLayer.innerHTML='';
"""
replace_once(old_clear,new_clear,'limpeza completa dos GIFs/timers')

checks=[
 MARKER,
 "const ENTITY_LOOP_GIF_GRACE_MS=1400;",
 "function scheduleEntityLoopGifSuspend(el,stateName)",
 "img.style.display=active?'block':'none';",
 "scheduleEntityLoopGifSuspend(el,previous);",
 "for(const stateName of ENTITY_LOOP_STATE_LIST)",
 "const DRAGON_PROJECTILE_GIF_GRACE_MS=850;",
 "if(img._poolGifSuspendTimer){clearTimeout(img._poolGifSuspendTimer);img._poolGifSuspendTimer=null}",
 "for(const img of el.querySelectorAll('img'))img.decoding='async';",
]
for marker in checks:
    if marker not in text:
        raise SystemExit(f'Validação GIF falhou: {marker}')

# Garantias: ataques especiais continuam reiniciando por serial e o culling continua ativo.
for marker in [
 "restartGif(el._golemSpecial,'golemSpecial'",
 "restartGif(el._mageSpecial",
 "restartGif(el._kingSpecial,'kingSpecial'",
 "restartGif(el._dragonTakeoff,'dragonTakeoff'",
 "restartGif(el._dragonAttack,'dragonAttack'",
 "suspendEntityLoopGif(el);",
 "if(entity && !transient && localNow-lastSeen>1400)",
]:
    if marker not in text:
        raise SystemExit(f'Sistema visual preservado inesperadamente ausente: {marker}')

path.write_text(text,encoding='utf-8')
print('Trocas de GIF estabilizadas sem reduzir qualidade visual.')
