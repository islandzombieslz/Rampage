from pathlib import Path
import re

path=Path('index.html')
text=path.read_text(encoding='utf-8')

old_flee=re.search(r"function tryWarriorFleeFlyingDragon\(e,dt,hasAttackableTargets=false\)\{.*?\n\}\n\nfunction aiFight",text,re.S)
if not old_flee:
    raise SystemExit('função antiga de fuga não encontrada')
new_flee="""function tryWarriorFleeFlyingDragon(e,dt){
 if(e.type!=='warrior'||state.mode!=='war'||state.phase!=='combat'||!e.alive)return false;

 // Fuga é uma regra de fim de combate, não uma preferência de alvo:
 // se existir QUALQUER tropa inimiga que não seja Dragão, o Guerreiro luta normalmente.
 const enemies=state.entities.filter(t=>t.alive&&t.team!==e.team&&isRealCombatTarget(t));
 if(!enemies.length||enemies.some(t=>t.type!=='dragon'))return false;

 // Quando só restam Dragões, foge do Dragão voando mais próximo em vez de ficar parado.
 const dragons=enemies.filter(t=>t.dragonFlightState==='flying');
 if(!dragons.length)return false;
 let dragon=dragons[0],best=dist(e,dragon);
 for(let i=1;i<dragons.length;i++){const d=dist(e,dragons[i]);if(d<best){best=d;dragon=dragons[i]}}

 let mx=e.x-dragon.x,my=e.y-dragon.y;
 if(best<.001){mx=e.x<state.world.w/2?-1:1;my=e.y<state.world.h/2?-1:1}
 // Nas bordas, adiciona componente lateral para não ficar preso no mesmo canto.
 const edge=135;
 if(e.x<edge)mx+=.9;
 else if(e.x>state.world.w-edge)mx-=.9;
 if(e.y<edge)my+=.9;
 else if(e.y>state.world.h-edge)my-=.9;
 const len=Math.hypot(mx,my)||1;mx/=len;my/=len;
 e.target=dragon;e.heading=Math.atan2(my,mx);if(Math.abs(mx)>.05)e.facing=mx<0?-1:1;
 e.x+=mx*e.speed*dt;e.y+=my*e.speed*dt;e.moving=true;
 e.x=clamp(e.x,35,state.world.w-35);e.y=clamp(e.y,35,state.world.h-35);
 return true;
}

function aiFight"""
text=text[:old_flee.start()]+new_flee+text[old_flee.end():]

old_call="if(tryWarriorFleeFlyingDragon(e,dt,candidates.length>0))return;"
if text.count(old_call)!=1:
    raise SystemExit(f'chamada antiga da fuga: {text.count(old_call)} ocorrências')
text=text.replace(old_call,"if(tryWarriorFleeFlyingDragon(e,dt))return;",1)

old_rot="img.style.transform=`translate(-50%,-50%) rotate(${angle+Math.PI/2}rad)`;img.style.visibility='visible';"
if text.count(old_rot)!=1:
    raise SystemExit(f'rotação antiga da bola: {text.count(old_rot)} ocorrências')
# O GIF está visualmente 180° invertido em relação ao offset anterior.
text=text.replace(old_rot,"img.style.transform=`translate(-50%,-50%) rotate(${angle-Math.PI/2}rad)`;img.style.visibility='visible';",1)

# Garantias antes de gravar.
checks=[
    "enemies.some(t=>t.type!=='dragon')",
    "if(tryWarriorFleeFlyingDragon(e,dt))return;",
    "angle-Math.PI/2",
]
for marker in checks:
    if marker not in text:
        raise SystemExit('marcador final ausente: '+marker)
if "tryWarriorFleeFlyingDragon(e,dt,candidates.length>0)" in text:
    raise SystemExit('chamada conflitante antiga ainda existe')
if "angle+Math.PI/2" in text:
    raise SystemExit('rotação invertida antiga ainda existe')

path.write_text(text,encoding='utf-8')
