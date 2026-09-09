from pathlib import Path

INDEX = Path('index.html')
text = INDEX.read_text(encoding='utf-8')

FLOOR_URL = 'https://i.postimg.cc/6qYQzvPc/bff3bb67-8426-4656-bdee-1313473758e2.png'
BARRIER_URL = 'https://i.postimg.cc/fywLxK8B/1919c5cb-ace6-4da5-b8f0-6db8bfb24c89.png'

# O sprite solicitado foi produzido em 1920x1600. A Guerra fica um pouco menor
# que o antigo 2200x1400 e preserva praticamente a mesma proporção do desenho.
WAR_W = 1850
WAR_H = 1542


def replace_once(old: str, new: str, label: str):
    global text
    if new in text:
        return
    if old not in text:
        raise SystemExit(f'Trecho não encontrado: {label}')
    text = text.replace(old, new, 1)


def insert_after_once(marker: str, addition: str, label: str):
    global text
    if addition.strip() in text:
        return
    if marker not in text:
        raise SystemExit(f'Marcador não encontrado: {label}')
    text = text.replace(marker, marker + addition, 1)


# =========================================================
# CAMADA VISUAL DA BARREIRA
# =========================================================
replace_once(
    "#entityLayer{position:absolute;inset:0;overflow:hidden;overflow:clip;pointer-events:none;z-index:2;contain:layout paint;transform:translateZ(0)}\n#hud{position:absolute;inset:0;pointer-events:none;z-index:5}",
    "#entityLayer{position:absolute;inset:0;overflow:hidden;overflow:clip;pointer-events:none;z-index:2;contain:layout paint;transform:translateZ(0)}\n#warBarrierSprite{position:absolute;left:0;top:0;display:none;pointer-events:none;user-select:none;-webkit-user-drag:none;z-index:4;object-fit:fill;transform-origin:0 0;backface-visibility:hidden;-webkit-backface-visibility:hidden}\n#hud{position:absolute;inset:0;pointer-events:none;z-index:5}",
    'CSS da barreira visual da Guerra',
)

replace_once(
    "#gameScreen.spectator-mode #world,\n#gameScreen.spectator-mode #entityLayer{",
    "#gameScreen.spectator-mode #world,\n#gameScreen.spectator-mode #entityLayer,\n#gameScreen.spectator-mode #warBarrierSprite{",
    'filtro espectador incluindo a barreira',
)

replace_once(
    "  <canvas id=\"world\"></canvas>\n  <div id=\"entityLayer\"></div>\n  <div id=\"combatFxLayer\"></div>\n  <div id=\"hud\">",
    f"  <canvas id=\"world\"></canvas>\n  <div id=\"entityLayer\"></div>\n  <div id=\"combatFxLayer\"></div>\n  <img id=\"warBarrierSprite\" src=\"{BARRIER_URL}\" draggable=\"false\" alt=\"\">\n  <div id=\"hud\">",
    'HTML da barreira visual da Guerra',
)

# =========================================================
# TAMANHO DO MAPA — SOMENTE GUERRA
# =========================================================
replace_once(
    "function beginPVERound(){\n state.spectator=",
    "function beginPVERound(){\n state.world.w=2200;state.world.h=1400;\n state.spectator=",
    'restaurar tamanho original no PVE',
)
replace_once(
    "function setupWarRound(){\n state.entities=[];state.particles=[];state.dragonProjectiles=[];",
    f"function setupWarRound(){{\n state.world.w={WAR_W};state.world.h={WAR_H};\n state.entities=[];state.particles=[];state.dragonProjectiles=[];",
    'tamanho compacto da Guerra',
)

# O host envia as dimensões reais junto do snapshot para câmera/colisão dos clientes.
replace_once(
    "nextId:state.nextId,players:state.players.map(p=>({...p,local:false}))",
    "nextId:state.nextId,world:{w:state.world.w,h:state.world.h},players:state.players.map(p=>({...p,local:false}))",
    'dimensões do mapa no snapshot online',
)

remote_state_line = " state.mode=game.mode??state.mode;state.round=game.round??state.round;state.rounds=game.rounds??state.rounds;state.phase=game.phase??state.phase;state.running=!!game.running;state.timeLeft=game.timeLeft??0;state.prepLeft=game.prepLeft??0;state.nextId=game.nextId??state.nextId;\n"
remote_world = " if(game.world&&Number.isFinite(Number(game.world.w))&&Number.isFinite(Number(game.world.h))){state.world.w=Number(game.world.w);state.world.h=Number(game.world.h)}\n"
if remote_world.strip() not in text:
    if remote_state_line not in text:
        raise SystemExit('Trecho não encontrado: aplicação remota do estado da Guerra')
    text = text.replace(remote_state_line, remote_state_line + remote_world, 1)

# =========================================================
# CHÃO DA GUERRA NO CANVAS + BARREIRA EM DOM
# =========================================================
canvas_marker = "const assetWarning=document.getElementById('assetWarning');\n"
canvas_add = f"""
const warBarrierSprite=$('#warBarrierSprite');
const warFloorImage=new Image();
warFloorImage.decoding='async';
warFloorImage.src='{FLOOR_URL}';

function syncWarArenaOverlay(left,top,zoom){{
 if(!warBarrierSprite)return;
 if(state.mode!=='war'){{
   if(warBarrierSprite.style.display!=='none')warBarrierSprite.style.display='none';
   return;
 }}
 if(warBarrierSprite.style.display!=='block')warBarrierSprite.style.display='block';
 const x=-left*zoom,y=-top*zoom,w=state.world.w*zoom,h=state.world.h*zoom;
 if(warBarrierSprite._arenaX!==x){{warBarrierSprite._arenaX=x;warBarrierSprite.style.left=x+'px'}}
 if(warBarrierSprite._arenaY!==y){{warBarrierSprite._arenaY=y;warBarrierSprite.style.top=y+'px'}}
 if(warBarrierSprite._arenaW!==w){{warBarrierSprite._arenaW=w;warBarrierSprite.style.width=w+'px'}}
 if(warBarrierSprite._arenaH!==h){{warBarrierSprite._arenaH=h;warBarrierSprite.style.height=h+'px'}}
}}
"""
insert_after_once(canvas_marker, canvas_add, 'preload/sync dos sprites da arena')

replace_once(
    " ctx.fillStyle='#665642';\n ctx.fillRect(left,top,right-left,bottom-top);",
    """ if(state.mode==='war'&&warFloorImage.complete&&warFloorImage.naturalWidth>0){
   const dw=right-left,dh=bottom-top;
   const sx=left/state.world.w*warFloorImage.naturalWidth;
   const sy=top/state.world.h*warFloorImage.naturalHeight;
   const sw=dw/state.world.w*warFloorImage.naturalWidth;
   const sh=dh/state.world.h*warFloorImage.naturalHeight;
   ctx.drawImage(warFloorImage,sx,sy,sw,sh,left,top,dw,dh);
 }else{
   ctx.fillStyle='#665642';
   ctx.fillRect(left,top,right-left,bottom-top);
 }""",
    'sprite do chão da Guerra',
)

# O contorno antigo deixa de aparecer na Guerra, mas a colisão continua usando
# exatamente os limites state.world.
replace_once(
    " ctx.globalAlpha=1;\n ctx.strokeStyle='#ffffff2e';ctx.lineWidth=3/zoom;ctx.strokeRect(2,2,state.world.w-4,state.world.h-4);\n ctx.restore();",
    " ctx.globalAlpha=1;\n if(state.mode!=='war'){ctx.strokeStyle='#ffffff2e';ctx.lineWidth=3/zoom;ctx.strokeRect(2,2,state.world.w-4,state.world.h-4)}\n ctx.restore();",
    'ocultar contorno antigo somente na Guerra',
)

replace_once(
    " ctx.restore();\n\n syncEntityVisuals(visible,left,top,zoom,vw,vh);",
    " ctx.restore();\n\n syncWarArenaOverlay(left,top,zoom);\n syncEntityVisuals(visible,left,top,zoom,vw,vh);",
    'sincronizar muralha com câmera',
)

checks = [
    "id=\"warBarrierSprite\"",
    "pointer-events:none",
    FLOOR_URL,
    BARRIER_URL,
    "syncWarArenaOverlay(left,top,zoom)",
    f"state.world.w={WAR_W};state.world.h={WAR_H}",
    "world:{w:state.world.w,h:state.world.h}",
]
for marker in checks:
    if marker not in text:
        raise SystemExit(f'Validação da arena falhou: {marker}')

INDEX.write_text(text,encoding='utf-8')
print(f'Arena da Guerra aplicada: mapa {WAR_W}x{WAR_H}, chão e barreira por sprite.')
