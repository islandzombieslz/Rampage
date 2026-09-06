from pathlib import Path
import re

path = Path('index.html')
text = path.read_text(encoding='utf-8')

def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: esperado 1 trecho, encontrado {count}')
    text = text.replace(old, new, 1)

replace_once(
    'const DRAGON_BURN_DAMAGE=50;',
    'const DRAGON_BURN_DAMAGE=5;',
    'dano da queimadura'
)

replace_once(
    'Dispara a cada 2s • queimadura 50/s por 6s • voador',
    'Dispara a cada 2s • queimadura: 6 pulsos de 5 (1/s) • voador',
    'descrição da loja'
)

old_collision = """       const b=living[j];
       if((a.type==='dragon'&&a.dragonFlightState==='flying')||(b.type==='dragon'&&b.dragonFlightState==='flying'))continue;
     let dx=b.x-a.x,dy=b.y-a.y;
     let d=Math.hypot(dx,dy);
     const minD=Math.min(58,a.r+b.r);"""
new_collision = """       const b=living[j];
       const aFlyingDragon=a.type==='dragon'&&a.dragonFlightState==='flying';
       const bFlyingDragon=b.type==='dragon'&&b.dragonFlightState==='flying';
       // Dragões voando atravessam tropas terrestres, mas colidem entre si para não se amontoarem.
       if((aFlyingDragon||bFlyingDragon)&&!(aFlyingDragon&&bFlyingDragon))continue;
     let dx=b.x-a.x,dy=b.y-a.y;
     let d=Math.hypot(dx,dy);
     const minD=aFlyingDragon&&bFlyingDragon?76:Math.min(58,a.r+b.r);"""
replace_once(old_collision, new_collision, 'colisão entre dragões')

replace_once(
    "img.style.transform=`translate(-50%,-50%) rotate(${angle}rad)`;img.style.visibility='visible';",
    "img.style.transform=`translate(-50%,-50%) rotate(${angle+Math.PI/2}rad)`;img.style.visibility='visible';",
    'rotação da bola de fogo'
)

old_lift = """   // O scale geral aplica a câmera; o flip fica só no miolo do personagem.
   el.style.left=sx+'px';
   el.style.top=sy+'px';
   const typeScale=e.type==='golem'?1.34:e.type==='mage'?1.08:e.type==='dragon'?1.16:1;"""
new_lift = """   // O scale geral aplica a câmera; o flip fica só no miolo do personagem.
   // Durante a decolagem o Dragão sobe visualmente e mantém altitude enquanto voa.
   // A posição lógica no mapa não muda: é apenas altura visual, preservando alcance e sincronização.
   let dragonLift=0;
   if(e.type==='dragon'){
     if(e.dragonFlightState==='takeoff'){
       const start=Number(e.dragonTakeoffStartedAt)||localNow;
       const end=Math.max(start+1,Number(e.dragonTakeoffEndAt)||start+DRAGON_TAKEOFF_DURATION);
       const progress=clamp((localNow-start)/(end-start),0,1);
       dragonLift=36*(1-Math.pow(1-progress,2));
     }else if(e.dragonFlightState==='flying')dragonLift=36;
   }
   el.style.left=sx+'px';
   el.style.top=(sy-dragonLift*zoom)+'px';
   const typeScale=e.type==='golem'?1.34:e.type==='mage'?1.08:e.type==='dragon'?1.16:1;"""
replace_once(old_lift, new_lift, 'subida visual da decolagem')

flee_function = """
function tryWarriorFleeFlyingDragon(e,dt,hasAttackableTargets=false){
 if(e.type!=='warrior'||state.mode!=='war'||state.phase!=='combat'||!e.alive)return false;
 // Quando restam apenas um ou dois Guerreiros do time, eles passam a preservar distância do Dragão.
 const livingWarriors=state.entities.filter(t=>t.alive&&t.team===e.team&&t.type==='warrior').length;
 if(livingWarriors>2)return false;
 const dragons=state.entities.filter(t=>t.alive&&t.team!==e.team&&t.type==='dragon'&&t.dragonFlightState==='flying');
 if(!dragons.length)return false;
 let dragon=dragons[0],best=dist(e,dragon);
 for(let i=1;i<dragons.length;i++){const d=dist(e,dragons[i]);if(d<best){best=d;dragon=dragons[i]}}
 // Se ainda existem alvos terrestres atacáveis, só abandona a luta quando o Dragão realmente ameaça de perto.
 if(hasAttackableTargets&&best>380)return false;
 let mx=e.x-dragon.x,my=e.y-dragon.y;
 if(best<.001){mx=e.x<state.world.w/2?-1:1;my=e.y<state.world.h/2?-1:1}
 // Evita ficar pressionando a mesma borda do mapa: adiciona componente lateral para continuar escapando.
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

"""
ai_anchor = 'function aiFight(e,dt,forcedTeam,preparedCandidates=null){\n'
if 'function tryWarriorFleeFlyingDragon' in text:
    raise SystemExit('função de fuga já existe inesperadamente')
if text.count(ai_anchor) != 1:
    raise SystemExit('âncora de aiFight não encontrada de forma única')
text = text.replace(ai_anchor, flee_function + ai_anchor, 1)

old_ai = """ if(!e.alive||e.knockTime>0){e.moving=false;return;}
 const candidates=(preparedCandidates||state.entities.filter(t=>t.alive&&t!==e&&(forcedTeam?t.team===forcedTeam:t.team!==e.team))).filter(t=>canEngageTarget(e,t));
 if(!candidates.length){e.moving=false;return}"""
new_ai = """ if(!e.alive||e.knockTime>0){e.moving=false;return;}
 const candidates=(preparedCandidates||state.entities.filter(t=>t.alive&&t!==e&&(forcedTeam?t.team===forcedTeam:t.team!==e.team))).filter(t=>canEngageTarget(e,t));
 if(tryWarriorFleeFlyingDragon(e,dt,candidates.length>0))return;
 if(!candidates.length){e.moving=false;return}"""
replace_once(old_ai, new_ai, 'integração da fuga do guerreiro')

path.write_text(text, encoding='utf-8')

scripts = re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>', text, flags=re.S)
if not scripts:
    raise SystemExit('nenhum script encontrado')
Path('/tmp/rampage-main.js').write_text(max(scripts,key=len),encoding='utf-8')
