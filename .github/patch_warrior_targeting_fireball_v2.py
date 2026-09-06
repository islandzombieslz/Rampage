from pathlib import Path

path=Path('index.html')
text=path.read_text(encoding='utf-8')

old_ai=""" if(!e.alive||e.knockTime>0){e.moving=false;return;}
 const candidates=(preparedCandidates||state.entities.filter(t=>t.alive&&t!==e&&(forcedTeam?t.team===forcedTeam:t.team!==e.team))).filter(t=>canEngageTarget(e,t));
 if(tryWarriorFleeFlyingDragon(e,dt))return;
 if(!candidates.length){e.moving=false;return}
"""
new_ai=""" if(!e.alive||e.knockTime>0){e.moving=false;return;}
 let candidates;
 if(e.type==='warrior'&&state.mode==='war'&&state.phase==='combat'){
   // Regra absoluta: enquanto existir QUALQUER tropa inimiga que não seja Dragão,
   // o Guerreiro ignora os Dragões e escolhe apenas entre essas tropas.
   // Não usa o recorte local do grid aqui, evitando conflito entre fuga e aquisição de alvo.
   const allEnemies=state.entities.filter(t=>t.alive&&t!==e&&(forcedTeam?t.team===forcedTeam:t.team!==e.team)&&isRealCombatTarget(t));
   const nonDragonEnemies=allEnemies.filter(t=>t.type!=='dragon');
   if(nonDragonEnemies.length){
     candidates=nonDragonEnemies.filter(t=>canEngageTarget(e,t));
   }else{
     if(tryWarriorFleeFlyingDragon(e,dt))return;
     candidates=[];
   }
 }else{
   candidates=(preparedCandidates||state.entities.filter(t=>t.alive&&t!==e&&(forcedTeam?t.team===forcedTeam:t.team!==e.team))).filter(t=>canEngageTarget(e,t));
 }
 if(!candidates.length){e.moving=false;return}
"""
if text.count(old_ai)!=1:
    raise SystemExit(f'bloco aiFight esperado 1 vez, encontrado {text.count(old_ai)}')
text=text.replace(old_ai,new_ai,1)

old_dragons="const dragons=enemies.filter(t=>t.dragonFlightState==='flying');"
new_dragons="const dragons=enemies.filter(t=>t.type==='dragon');"
if text.count(old_dragons)!=1:
    raise SystemExit(f'filtro de dragões esperado 1 vez, encontrado {text.count(old_dragons)}')
text=text.replace(old_dragons,new_dragons,1)

old_transform="img.style.transform=`translate(-50%,-50%) rotate(${angle-Math.PI/2}rad)`;img.style.visibility='visible';"
new_transform="img.style.transform=`translate(-50%,-50%) rotate(${angle-Math.PI/2}rad) scaleY(-1)`;img.style.visibility='visible';"
if text.count(old_transform)!=1:
    raise SystemExit(f'transform da bola esperado 1 vez, encontrado {text.count(old_transform)}')
text=text.replace(old_transform,new_transform,1)

checks=[
    "const nonDragonEnemies=allEnemies.filter(t=>t.type!=='dragon');",
    "if(nonDragonEnemies.length){",
    "if(tryWarriorFleeFlyingDragon(e,dt))return;",
    "rotate(${angle-Math.PI/2}rad) scaleY(-1)",
]
for marker in checks:
    if marker not in text:
        raise SystemExit('marcador ausente: '+marker)

path.write_text(text,encoding='utf-8')
