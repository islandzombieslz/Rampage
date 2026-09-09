from pathlib import Path

path=Path('index.html')
text=path.read_text(encoding='utf-8')


def replace_once(old,new,label):
    global text
    if new in text:
        return
    if old not in text:
        raise SystemExit(f'Trecho não encontrado: {label}')
    text=text.replace(old,new,1)


old_territory="""function territoryFor(i,n){
 const pad=140, lane=(state.world.w-2*pad)/Math.max(1,n-1);
 return {x:n===1?state.world.w/2:pad+i*lane,y:i%2===0?240:state.world.h-240};
}
"""
new_territory="""// A muralha é somente visual, mas ocupa parte da borda do sprite.
// Estes recuos definem o retângulo físico realmente livre para as tropas.
// O tamanho visual do mapa/sprite continua 1850x1542.
const WAR_ARENA_INSET={left:160,right:160,top:155,bottom:175};
const WAR_SPAWN_INSET=125;
function warArenaBounds(radius=0){
 const r=Math.max(0,Number(radius)||0);
 return {
   left:WAR_ARENA_INSET.left+r,
   right:state.world.w-WAR_ARENA_INSET.right-r,
   top:WAR_ARENA_INSET.top+r,
   bottom:state.world.h-WAR_ARENA_INSET.bottom-r
 };
}
function constrainWarEntityToArena(e){
 if(state.mode!=='war'||!e?.alive)return;
 const b=warArenaBounds(e.r||0);
 e.x=clamp(e.x,b.left,b.right);
 e.y=clamp(e.y,b.top,b.bottom);
}
function constrainWarEntitiesToArena(){
 if(state.mode!=='war')return;
 for(const e of state.entities)constrainWarEntityToArena(e);
}
function territoryFor(i,n){
 const b=warArenaBounds(0);
 const minX=b.left+WAR_SPAWN_INSET,maxX=b.right-WAR_SPAWN_INSET;
 const lane=(maxX-minX)/Math.max(1,n-1);
 return {
   x:n===1?(minX+maxX)/2:minX+i*lane,
   y:i%2===0?b.top+WAR_SPAWN_INSET:b.bottom-WAR_SPAWN_INSET
 };
}
"""
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
replace_once(old_update,new_update,'clamp físico final da arena')

checks=[
 "const WAR_ARENA_INSET={left:160,right:160,top:155,bottom:175};",
 "const WAR_SPAWN_INSET=125;",
 "function warArenaBounds(radius=0)",
 "function constrainWarEntityToArena(e)",
 "function constrainWarEntitiesToArena()",
 "if(state.mode==='war')constrainWarEntitiesToArena();",
 "const minX=b.left+WAR_SPAWN_INSET,maxX=b.right-WAR_SPAWN_INSET;",
]
for marker in checks:
    if marker not in text:
        raise SystemExit(f'Validação dos limites internos falhou: {marker}')

# A arena visual e os sprites não podem ser alterados por este ajuste.
for marker in [
 "state.world.w=1850;state.world.h=1542;",
 "https://i.postimg.cc/6qYQzvPc/bff3bb67-8426-4656-bdee-1313473758e2.png",
 "https://i.postimg.cc/fywLxK8B/1919c5cb-ace6-4da5-b8f0-6db8bfb24c89.png",
]:
    if marker not in text:
        raise SystemExit(f'Visual da arena foi alterado inesperadamente: {marker}')

path.write_text(text,encoding='utf-8')
print('Limites internos da arena e territórios de spawn reposicionados.')
