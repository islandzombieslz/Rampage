from pathlib import Path
import re

path=Path('index.html')
text=path.read_text(encoding='utf-8')


def replace_once(old,new,label):
    global text
    if new in text:
        return
    if old not in text:
        raise SystemExit(f'Trecho não encontrado: {label}')
    text=text.replace(old,new,1)


# =========================================================
# LIMITES FÍSICOS MAIS INTERNOS
# =========================================================
# Ajuste fino atual: topo/laterais um pouco mais internos; base preservada.
NEW_INSET="const WAR_ARENA_INSET={left:270,right:270,top:275,bottom:245};"

old_territory="""function territoryFor(i,n){
 const pad=140, lane=(state.world.w-2*pad)/Math.max(1,n-1);
 return {x:n===1?state.world.w/2:pad+i*lane,y:i%2===0?240:state.world.h-240};
}
"""
new_territory=f"""// A muralha é somente visual, mas ocupa parte da borda do sprite.
// Estes recuos definem o retângulo físico realmente livre para as tropas.
// O tamanho visual do mapa/sprite continua 1850x1542.
{NEW_INSET}
const WAR_SPAWN_INSET=125;
function warArenaBounds(radius=0){{
 const r=Math.max(0,Number(radius)||0);
 return {{
   left:WAR_ARENA_INSET.left+r,
   right:state.world.w-WAR_ARENA_INSET.right-r,
   top:WAR_ARENA_INSET.top+r,
   bottom:state.world.h-WAR_ARENA_INSET.bottom-r
 }};
}}
function constrainWarEntityToArena(e){{
 if(state.mode!=='war'||!e?.alive)return;
 const b=warArenaBounds(e.r||0);
 e.x=clamp(e.x,b.left,b.right);
 e.y=clamp(e.y,b.top,b.bottom);
}}
function constrainWarEntitiesToArena(){{
 if(state.mode!=='war')return;
 for(const e of state.entities)constrainWarEntityToArena(e);
}}
function territoryFor(i,n){{
 const b=warArenaBounds(0);
 const minX=b.left+WAR_SPAWN_INSET,maxX=b.right-WAR_SPAWN_INSET;
 const lane=(maxX-minX)/Math.max(1,n-1);
 return {{
   x:n===1?(minX+maxX)/2:minX+i*lane,
   y:i%2===0?b.top+WAR_SPAWN_INSET:b.bottom-WAR_SPAWN_INSET
 }};
}}
"""

inset_pattern=r"const WAR_ARENA_INSET=\{left:\d+,right:\d+,top:\d+,bottom:\d+\};"
match=re.search(inset_pattern,text)
if match:
    if match.group(0)!=NEW_INSET:
        text=text[:match.start()]+NEW_INSET+text[match.end():]
else:
    replace_once(old_territory,new_territory,'territórios/spawn internos da Guerra')

old_update=""" separateLivingEntities();
 cleanupDeadEntities(now);
}
"""
new_update=""" separateLivingEntities();
 // Knockback e separação podem empurrar a unidade alguns pixels depois da IA.
 // O clamp final garante que ninguém atravesse visualmente a muralha.
 if(state.mode==='war')constrainWarEntitiesToArena();
 cleanupDeadEntities(now);
}
"""
if "if(state.mode==='war')constrainWarEntitiesToArena();" not in text:
    replace_once(old_update,new_update,'clamp físico final da arena')


# =========================================================
# PROFUNDIDADE VISUAL DA MURALHA SUPERIOR
# =========================================================
# Só aplica a divisão se ainda não existir. Em execuções seguintes a camada é
# preservada e o script mexe apenas nos limites físicos.
if 'id="warBarrierTopSprite"' not in text:
    old_css="#warBarrierSprite{position:absolute;left:0;top:0;display:none;pointer-events:none;user-select:none;-webkit-user-drag:none;z-index:4;object-fit:fill;transform-origin:0 0;backface-visibility:hidden;-webkit-backface-visibility:hidden}"
    new_css="""#warBarrierTopSprite,#warBarrierSprite{position:absolute;left:0;top:0;display:none;pointer-events:none;user-select:none;-webkit-user-drag:none;object-fit:fill;transform-origin:0 0;backface-visibility:hidden;-webkit-backface-visibility:hidden}
#warBarrierTopSprite{z-index:1;clip-path:polygon(12% 0,88% 0,88% 22%,12% 22%);-webkit-clip-path:polygon(12% 0,88% 0,88% 22%,12% 22%)}
#warBarrierSprite{z-index:4;clip-path:polygon(0 0,12% 0,12% 22%,88% 22%,88% 0,100% 0,100% 100%,0 100%);-webkit-clip-path:polygon(0 0,12% 0,12% 22%,88% 22%,88% 0,100% 0,100% 100%,0 100%)}"""
    replace_once(old_css,new_css,'camadas de profundidade da muralha')

    old_spectator="""#gameScreen.spectator-mode #world,
#gameScreen.spectator-mode #entityLayer,
#gameScreen.spectator-mode #warBarrierSprite{"""
    new_spectator="""#gameScreen.spectator-mode #world,
#gameScreen.spectator-mode #warBarrierTopSprite,
#gameScreen.spectator-mode #entityLayer,
#gameScreen.spectator-mode #warBarrierSprite{"""
    replace_once(old_spectator,new_spectator,'filtro espectador das duas camadas da muralha')

    barrier_url='https://i.postimg.cc/fywLxK8B/1919c5cb-ace6-4da5-b8f0-6db8bfb24c89.png'
    old_html=f"""  <canvas id=\"world\"></canvas>
  <div id=\"entityLayer\"></div>
  <div id=\"combatFxLayer\"></div>
  <img id=\"warBarrierSprite\" src=\"{barrier_url}\" draggable=\"false\" alt=\"\">"""
    new_html=f"""  <canvas id=\"world\"></canvas>
  <img id=\"warBarrierTopSprite\" draggable=\"false\" alt=\"\">
  <div id=\"entityLayer\"></div>
  <div id=\"combatFxLayer\"></div>
  <img id=\"warBarrierSprite\" src=\"{barrier_url}\" draggable=\"false\" alt=\"\">"""
    replace_once(old_html,new_html,'segunda camada visual da muralha')

    old_const="const warBarrierSprite=$('#warBarrierSprite');\n"
    new_const="""const warBarrierSprite=$('#warBarrierSprite');
const warBarrierTopSprite=$('#warBarrierTopSprite');
if(warBarrierTopSprite&&warBarrierSprite)warBarrierTopSprite.src=warBarrierSprite.src;
"""
    replace_once(old_const,new_const,'referência da camada superior atrás das entidades')

    old_sync="""function syncWarArenaOverlay(left,top,zoom){
 if(!warBarrierSprite)return;
 if(state.mode!=='war'){
   if(warBarrierSprite.style.display!=='none')warBarrierSprite.style.display='none';
   return;
 }
 if(warBarrierSprite.style.display!=='block')warBarrierSprite.style.display='block';
 const x=-left*zoom,y=-top*zoom,w=state.world.w*zoom,h=state.world.h*zoom;
 if(warBarrierSprite._arenaX!==x){warBarrierSprite._arenaX=x;warBarrierSprite.style.left=x+'px'}
 if(warBarrierSprite._arenaY!==y){warBarrierSprite._arenaY=y;warBarrierSprite.style.top=y+'px'}
 if(warBarrierSprite._arenaW!==w){warBarrierSprite._arenaW=w;warBarrierSprite.style.width=w+'px'}
 if(warBarrierSprite._arenaH!==h){warBarrierSprite._arenaH=h;warBarrierSprite.style.height=h+'px'}
}
"""
    new_sync="""function syncWarBarrierNode(node,x,y,w,h){
 if(!node)return;
 if(node.style.display!=='block')node.style.display='block';
 if(node._arenaX!==x){node._arenaX=x;node.style.left=x+'px'}
 if(node._arenaY!==y){node._arenaY=y;node.style.top=y+'px'}
 if(node._arenaW!==w){node._arenaW=w;node.style.width=w+'px'}
 if(node._arenaH!==h){node._arenaH=h;node.style.height=h+'px'}
}
function hideWarBarrierNode(node){
 if(node&&node.style.display!=='none')node.style.display='none';
}
function syncWarArenaOverlay(left,top,zoom){
 if(!warBarrierSprite)return;
 if(state.mode!=='war'){
   hideWarBarrierNode(warBarrierTopSprite);
   hideWarBarrierNode(warBarrierSprite);
   return;
 }
 const x=-left*zoom,y=-top*zoom,w=state.world.w*zoom,h=state.world.h*zoom;
 syncWarBarrierNode(warBarrierTopSprite,x,y,w,h);
 syncWarBarrierNode(warBarrierSprite,x,y,w,h);
}
"""
    replace_once(old_sync,new_sync,'sincronização das duas camadas da muralha')

barrier_url='https://i.postimg.cc/fywLxK8B/1919c5cb-ace6-4da5-b8f0-6db8bfb24c89.png'
checks=[
 NEW_INSET,
 "const WAR_SPAWN_INSET=125;",
 "function warArenaBounds(radius=0)",
 "function constrainWarEntityToArena(e)",
 "function constrainWarEntitiesToArena()",
 "if(state.mode==='war')constrainWarEntitiesToArena();",
 "const minX=b.left+WAR_SPAWN_INSET,maxX=b.right-WAR_SPAWN_INSET;",
 "id=\"warBarrierTopSprite\"",
 "#warBarrierTopSprite{z-index:1",
 "#warBarrierSprite{z-index:4",
 "clip-path:polygon(12% 0,88% 0,88% 22%,12% 22%)",
 "function syncWarBarrierNode(node,x,y,w,h)",
 "syncWarBarrierNode(warBarrierTopSprite,x,y,w,h);",
]
for marker in checks:
    if marker not in text:
        raise SystemExit(f'Validação dos limites/camadas falhou: {marker}')

for marker in [
 "state.world.w=1850;state.world.h=1542;",
 "https://i.postimg.cc/6qYQzvPc/bff3bb67-8426-4656-bdee-1313473758e2.png",
 barrier_url,
]:
    if marker not in text:
        raise SystemExit(f'Visual da arena foi alterado inesperadamente: {marker}')

path.write_text(text,encoding='utf-8')
print('Topo/laterais reduzidos um pouco mais; base e profundidade preservadas.')
