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


# ===== REI GUERREIRO: ESCALA E POSIÇÃO DA MÃO/ESPADA =====
# Igualamos o multiplicador de escala do Rei ao do Mago (1.08), sem mexer
# em hitbox, vida, dano ou alcance. A mão/espada vai apenas alguns pixels à esquerda.
replace_once(
    ".entity-visual.king-visual .entity-sword{left:51px;top:20px;width:34px;height:98px}",
    ".entity-visual.king-visual .entity-sword{left:46px;top:20px;width:34px;height:98px}",
    'posição da mão/espada do Rei',
)
replace_once(
    "const typeScale=e.type==='golem'?1.34:e.type==='mage'?1.08:e.type==='dragon'?1.16:e.type==='king'?1.18:1;",
    "const typeScale=e.type==='golem'?1.34:e.type==='mage'?1.08:e.type==='dragon'?1.16:e.type==='king'?1.08:1;",
    'escala efetiva do Rei',
)


# ===== ESPECIAL DO REI: UM ÚNICO CICLO VISUAL DO CORPO =====
# A duração total do estado especial usa o maior entre special.gif e power.gif.
# Se power.gif é maior, special.gif terminava seu primeiro ciclo, começava outro e
# era cortado pouco depois. Guardamos a duração de UM ciclo do corpo e o render
# troca para idle assim que esse ciclo termina, enquanto o estado/dano continuam normais.
replace_once(
    "const KING_SPECIAL_DAMAGE=50;",
    "const KING_SPECIAL_DAMAGE=50;\nconst KING_POWER_DELAY_MS=1000;",
    'delay do poder especial do Rei',
)
replace_once(
    " e.pendingKingSpecial={\n   serial:e.kingSpecialSerial,duration,originX:e.x,originY:e.y,startedAt:now,\n   damageAt:now+Math.min(1200,Math.max(650,duration*.40)),",
    " e.pendingKingSpecial={\n   serial:e.kingSpecialSerial,duration,bodyDuration:KING_BODY_SPECIAL_DURATION,powerDelay:KING_POWER_DELAY_MS,\n   originX:e.x,originY:e.y,startedAt:now,\n   damageAt:now+Math.min(1200,Math.max(650,duration*.40)),",
    'metadados visuais do especial do Rei',
)

old_king_render = """   }else if(e.type==='king'){
     const p=e.pendingKingSpecial;
     const special=!!p&&p.endAt>localNow;
     setEntitySpriteState(el,special?'special':e.moving?'walk':'idle');
     if(special&&el.dataset.kingSpecialSerial!==String(e.kingSpecialSerial||0)){
       el.dataset.kingSpecialSerial=String(e.kingSpecialSerial||0);
       restartGif(el._kingSpecial,'kingSpecial',e.kingSpecialSerial);
       restartGif(el._kingPower,'kingPower',e.kingSpecialSerial);
     }
     if(el._weaponFacing)el._weaponFacing.style.visibility=special?'hidden':'visible';
     if(el._kingPower){
       if(special){
         const duration=p.duration||KING_SPECIAL_DURATION;
         const progress=clamp(1-Math.max(0,p.endAt-localNow)/duration,0,1);
         const alpha=Math.min(clamp(progress/.16,0,1),clamp((1-progress)/.22,0,1));
         el._kingPower.style.opacity=String(alpha);
         el._kingPower.style.visibility=alpha>.01?'visible':'hidden';
       }else{
         el._kingPower.style.opacity='0';
         el._kingPower.style.visibility='hidden';
       }
     }
"""
new_king_render = """   }else if(e.type==='king'){
     const p=e.pendingKingSpecial;
     const specialPending=!!p&&p.endAt>localNow;
     const totalDuration=Number(p?.duration)||KING_SPECIAL_DURATION;
     const startedAt=Number(p?.startedAt)||localNow-Math.max(0,totalDuration-Math.max(0,Number(p?.endAt||localNow)-localNow));
     const bodyDuration=Math.max(250,Number(p?.bodyDuration)||KING_BODY_SPECIAL_DURATION);
     // Encerra alguns ms antes do limite para o GIF nunca alcançar o primeiro
     // quadro do segundo loop. A regra do ataque continua sendo um único especial.
     const bodySpecial=specialPending&&localNow<startedAt+Math.max(250,bodyDuration-45);
     setEntitySpriteState(el,bodySpecial?'special':e.moving?'walk':'idle');
     if(bodySpecial&&el.dataset.kingSpecialSerial!==String(e.kingSpecialSerial||0)){
       el.dataset.kingSpecialSerial=String(e.kingSpecialSerial||0);
       restartGif(el._kingSpecial,'kingSpecial',e.kingSpecialSerial);
     }
     // A espada continua escondida durante todo o estado especial, mesmo depois
     // que o GIF do corpo terminou seu único ciclo.
     if(el._weaponFacing)el._weaponFacing.style.visibility=specialPending?'hidden':'visible';
"""
replace_once(old_king_render, new_king_render, 'render de um único ciclo do especial do Rei')


# ===== POWER.GIF: COMEÇA APÓS 1 SEGUNDO, FIXO NO PONTO DO CHÃO =====
old_power_fn = """function syncKingPowerEffects(left,top,zoom,screenW,screenH){
 const layer=entityLayer,active=kingPowerActiveIds;active.clear();const now=performance.now();
 for(const e of state.entities){
   const p=e.pendingKingSpecial;
   if(!p||Number(p.endAt||0)<=now)continue;
   const ox=Number.isFinite(Number(p.originX))?Number(p.originX):e.x;
   const oy=Number.isFinite(Number(p.originY))?Number(p.originY):e.y;
   const half=215*zoom;
   const sx=(ox-left)*zoom,sy=(oy-top)*zoom;
   const effectVisible=sx+half>=-40&&sx-half<=screenW+40&&sy+half>=-40&&sy-half<=screenH+40;
   if(!effectVisible){
     const old=kingPowerNodes.get(e.id);
     if(old){releaseGifObjectUrl(old);old.remove();kingPowerNodes.delete(e.id)}
     continue;
   }
   active.add(e.id);
   let img=kingPowerNodes.get(e.id);
   if(!img){
     img=document.createElement('img');img.className='king-special-power';img.draggable=false;
     img.dataset.serial='-1';layer.appendChild(img);kingPowerNodes.set(e.id,img);
   }
   const serial=String(p.serial||e.kingSpecialSerial||0);
   if(img.dataset.serial!==serial){img.dataset.serial=serial;restartGif(img,'kingPower',serial)}
   const duration=p.duration||KING_SPECIAL_DURATION;
   const progress=clamp(1-Math.max(0,p.endAt-now)/duration,0,1);
   const alpha=Math.min(clamp(progress/.16,0,1),clamp((1-progress)/.22,0,1));
   const size=430*zoom;
   img.style.left=sx+'px';img.style.top=sy+'px';img.style.width=size+'px';img.style.height=size+'px';
   img.style.opacity=String(alpha);img.style.visibility=alpha>.01?'visible':'hidden';
   img.style.transform='translate(-50%,-50%)';
   // Fica atrás das tropas próximas, mas preso ao ponto do chão em que nasceu.
   img.style.zIndex=String(40+Math.round(sy));
 }
 for(const [id,img] of kingPowerNodes)if(!active.has(id)){
   releaseGifObjectUrl(img);img.remove();kingPowerNodes.delete(id);
 }
}
"""
new_power_fn = """function syncKingPowerEffects(left,top,zoom,screenW,screenH){
 const layer=entityLayer,active=kingPowerActiveIds;active.clear();const now=performance.now();
 for(const e of state.entities){
   const p=e.pendingKingSpecial;
   if(!p||Number(p.endAt||0)<=now)continue;
   const duration=Number(p.duration)||KING_SPECIAL_DURATION;
   const startedAt=Number(p.startedAt)||now-Math.max(0,duration-Math.max(0,Number(p.endAt)-now));
   const delay=Math.max(0,Number(p.powerDelay)||KING_POWER_DELAY_MS);
   const showAt=startedAt+delay;
   // Não cria nem inicia o GIF antes de 1 segundo. Assim ele realmente começa
   // no quadro 0 após o atraso, em vez de tocar escondido desde o início.
   if(now<showAt){
     const old=kingPowerNodes.get(e.id);
     if(old){releaseGifObjectUrl(old);old.remove();kingPowerNodes.delete(e.id)}
     continue;
   }
   const ox=Number.isFinite(Number(p.originX))?Number(p.originX):e.x;
   const oy=Number.isFinite(Number(p.originY))?Number(p.originY):e.y;
   const half=215*zoom;
   const sx=(ox-left)*zoom,sy=(oy-top)*zoom;
   const effectVisible=sx+half>=-40&&sx-half<=screenW+40&&sy+half>=-40&&sy-half<=screenH+40;
   if(!effectVisible){
     const old=kingPowerNodes.get(e.id);
     if(old){releaseGifObjectUrl(old);old.remove();kingPowerNodes.delete(e.id)}
     continue;
   }
   active.add(e.id);
   let img=kingPowerNodes.get(e.id);
   if(!img){
     img=document.createElement('img');img.className='king-special-power';img.draggable=false;
     img.dataset.serial='-1';layer.appendChild(img);kingPowerNodes.set(e.id,img);
   }
   const serial=String(p.serial||e.kingSpecialSerial||0);
   if(img.dataset.serial!==serial){img.dataset.serial=serial;restartGif(img,'kingPower',serial)}
   const visibleDuration=Math.max(1,Number(p.endAt)-showAt);
   const progress=clamp((now-showAt)/visibleDuration,0,1);
   const alpha=Math.min(clamp(progress/.12,0,1),clamp((1-progress)/.20,0,1));
   const size=430*zoom;
   img.style.left=sx+'px';img.style.top=sy+'px';img.style.width=size+'px';img.style.height=size+'px';
   img.style.opacity=String(alpha);img.style.visibility=alpha>.01?'visible':'hidden';
   img.style.transform='translate(-50%,-50%)';
   // Continua preso ao ponto do chão em que o especial foi acionado.
   img.style.zIndex=String(40+Math.round(sy));
 }
 for(const [id,img] of kingPowerNodes)if(!active.has(id)){
   releaseGifObjectUrl(img);img.remove();kingPowerNodes.delete(id);
 }
}
"""
replace_once(old_power_fn, new_power_fn, 'delay real do power.gif do Rei')


# ===== VALIDAÇÕES DE INTEGRIDADE =====
required = [
    'FIREBASE RTDB, HOST AUTORITATIVO',
    'WAR PERFORMANCE 2026-09-08',
    'REMOTE WAR ROUND TRANSITION SYNC',
    "e.hp=e.maxHp=200;",
    "e.shield=e.maxShield=200;",
    "e.damage=25;",
    "kingNormalCount)||0)>=6",
    "Math.min(6,(Number(e.kingNormalCount)||0)+1)",
    ".entity-visual.king-visual .entity-sword{left:46px;top:20px;width:34px;height:98px}",
    "e.type==='king'?1.08:1;",
    'const KING_POWER_DELAY_MS=1000;',
    'bodyDuration:KING_BODY_SPECIAL_DURATION,powerDelay:KING_POWER_DELAY_MS',
    'const bodySpecial=specialPending&&localNow<startedAt+Math.max(250,bodyDuration-45);',
    'const showAt=startedAt+delay;',
    "restartGif(img,'kingPower',serial)",
    "originX:e.x,originY:e.y",
    "const ox=Number.isFinite(Number(p.originX))?Number(p.originX):e.x;",
    'syncKingPowerEffects(left,top,zoom,vw,vh);',
]
missing = [item for item in required if item not in text]
if missing:
    raise SystemExit('Validação falhou: ' + ' | '.join(missing))

if 'i.postimg.cc' in text:
    raise SystemExit('Referência ao Postimg reapareceu')

path.write_text(text, encoding='utf-8')
print('Rei ajustado: escala do Mago, espada à esquerda, um ciclo do special.gif e power.gif iniciado após 1 segundo.')
