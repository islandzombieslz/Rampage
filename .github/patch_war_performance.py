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


# ===== REI GUERREIRO: TAMANHO, ESPADA E ESPECIAL =====
old_css = """/* Rei Guerreiro: mantém o encaixe/ataque do Guerreiro, com corpo próprio. */
.entity-visual.king-visual{width:88px;height:112px}
.entity-visual.king-visual .entity-facing,
.entity-visual.king-visual .entity-weapon-facing{width:88px;height:104px}
.entity-visual.king-visual .entity-body{left:0;top:0;width:88px;height:104px}
.entity-visual.king-visual .entity-bars{left:9px;top:-5px;width:70px}
.entity-visual.king-visual .hp-bg,
.entity-visual.king-visual .shield-bg{width:70px}
.entity-visual.king-visual .entity-sword{left:30px}
.king-special-power{
  position:absolute;left:44px;top:52px;width:430px;height:430px;
  object-fit:contain;transform:translate(-50%,-50%);opacity:0;
  visibility:hidden;pointer-events:none;z-index:0;
}
.entity-visual.king-visual .entity-body{z-index:2}"""
new_css = """/* Rei Guerreiro: maior que o Guerreiro comum, mantendo a mesma lógica de combate. */
.entity-visual.king-visual{width:112px;height:138px}
.entity-visual.king-visual .entity-facing,
.entity-visual.king-visual .entity-weapon-facing{width:112px;height:132px}
.entity-visual.king-visual .entity-body{left:0;top:-4px;width:112px;height:132px}
.entity-visual.king-visual .entity-bars{left:17px;top:-7px;width:78px}
.entity-visual.king-visual .hp-bg,
.entity-visual.king-visual .shield-bg{width:78px}
/* A mão/espada do Rei fica mais baixa que antes. */
.entity-visual.king-visual .entity-sword{left:41px;top:4px;width:30px;height:88px}
/* O corpo do especial é propositalmente maior que idle/walk. */
.entity-visual.king-visual .entity-king-special{
  width:156px !important;height:184px !important;
  left:-22px !important;top:-32px !important;object-fit:contain !important;
}
/* power.gif agora é efeito de mundo independente, ancorado no chão do lançamento. */
.king-special-power{
  position:absolute;width:430px;height:430px;object-fit:contain;
  transform:translate(-50%,-50%);transform-origin:center;
  opacity:0;visibility:hidden;pointer-events:none;z-index:0;
}
.entity-visual.king-visual .entity-body{z-index:2}"""
replace_once(old_css, new_css, 'CSS visual do Rei Guerreiro')

# O power.gif não pode mais ser filho do Rei, pois isso faria o efeito seguir a entidade.
replace_once(
    "   el.innerHTML=`\n     <img class=\"king-special-power\" data-asset-key=\"kingPower\" draggable=\"false\">\n     <div class=\"entity-facing\">",
    "   el.innerHTML=`\n     <div class=\"entity-facing\">",
    'remoção do power.gif do nó do Rei',
)

# Mapa próprio para o efeito do Rei, assim como já existe para poderes/projéteis.
replace_once(
    "const entityNodes=new Map();\nconst magePowerNodes=new Map();\nconst dragonProjectileNodes=new Map();",
    "const entityNodes=new Map();\nconst magePowerNodes=new Map();\nconst kingPowerNodes=new Map();\nconst dragonProjectileNodes=new Map();",
    'mapa de efeitos do Rei',
)
replace_once(
    "const magePowerActiveIds=new Set();\nconst dragonProjectileActiveIds=new Set();",
    "const magePowerActiveIds=new Set();\nconst kingPowerActiveIds=new Set();\nconst dragonProjectileActiveIds=new Set();",
    'ids ativos do poder do Rei',
)

# Efeito independente usa originX/originY gravados em startKingSpecial().
if 'function syncKingPowerEffects(' not in text:
    anchor = 'function syncDragonProjectileEffects(left,top,zoom,screenW,screenH){'
    if anchor not in text:
        raise SystemExit('Âncora de efeitos do Dragão não encontrada')
    king_fx = """function syncKingPowerEffects(left,top,zoom,screenW,screenH){
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
    text = text.replace(anchor, king_fx + anchor, 1)

# Atualiza a posição do efeito a partir da câmera, nunca da posição atual do Rei.
replace_once(
    " syncEntityVisuals(visible,left,top,zoom,vw,vh);\n syncMagePowerEffects(left,top,zoom,vw,vh);",
    " syncEntityVisuals(visible,left,top,zoom,vw,vh);\n syncKingPowerEffects(left,top,zoom,vw,vh);\n syncMagePowerEffects(left,top,zoom,vw,vh);",
    'renderização do poder do Rei',
)

# Liberação de memória ao trocar de rodada/tela.
replace_once(
    " for(const img of magePowerNodes.values())releaseGifObjectUrl(img);\n for(const img of dragonProjectileNodes.values())releaseGifObjectUrl(img);",
    " for(const img of magePowerNodes.values())releaseGifObjectUrl(img);\n for(const img of kingPowerNodes.values())releaseGifObjectUrl(img);\n for(const img of dragonProjectileNodes.values())releaseGifObjectUrl(img);",
    'liberação dos efeitos do Rei',
)
replace_once(
    " magePowerNodes.clear();\n dragonProjectileNodes.clear();",
    " magePowerNodes.clear();\n kingPowerNodes.clear();\n dragonProjectileNodes.clear();",
    'limpeza do mapa de efeitos do Rei',
)

# ===== VALIDAÇÕES =====
required = [
    'FIREBASE RTDB, HOST AUTORITATIVO',
    'WAR PERFORMANCE 2026-09-08',
    "e.hp=e.maxHp=200;",
    "e.shield=e.maxShield=200;",
    "e.damage=25;",
    "kingNormalCount)||0)>=6",
    '.entity-visual.king-visual{width:112px;height:138px}',
    '.entity-visual.king-visual .entity-sword{left:41px;top:4px;width:30px;height:88px}',
    '.entity-visual.king-visual .entity-king-special{',
    'const kingPowerNodes=new Map();',
    'function syncKingPowerEffects(left,top,zoom,screenW,screenH){',
    'const ox=Number.isFinite(Number(p.originX))?Number(p.originX):e.x;',
    'syncKingPowerEffects(left,top,zoom,vw,vh);',
]
missing = [item for item in required if item not in text]
if missing:
    raise SystemExit('Validação falhou: ' + ' | '.join(missing))

# Não pode continuar existindo power.gif como filho direto do template do Rei.
king_template_start = text.find("}else if(e.type==='king'){")
king_template_end = text.find("}else if(e.type==='dragon'){", king_template_start)
if king_template_start < 0 or king_template_end < 0:
    raise SystemExit('Template do Rei não encontrado')
king_template = text[king_template_start:king_template_end]
if '<img class="king-special-power"' in king_template:
    raise SystemExit('power.gif ainda está preso ao nó do Rei')

if 'i.postimg.cc' in text:
    raise SystemExit('Referência ao Postimg reapareceu')

path.write_text(text, encoding='utf-8')
print('Ajustes visuais do Rei Guerreiro aplicados e validados.')
