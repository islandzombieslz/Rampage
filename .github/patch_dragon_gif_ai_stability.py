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


def regex_once(pattern, replacement, label):
    global text
    text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f'{label}: regex encontrou {count} trechos')


# 1) O ataque do Dragão passa a usar a duração REAL do GIF.
replace_once(
    "const DRAGON_SHOT_COOLDOWN_MS=2000;\nconst DRAGON_ATTACK_VISUAL_MS=850;",
    "const DRAGON_SHOT_COOLDOWN_MS=2000;\nconst DRAGON_CLOSE_SHOT_COOLDOWN_MS=5000;\nconst DRAGON_CLOSE_RANGE=175;\nlet DRAGON_ATTACK_VISUAL_MS=1800;",
    'constantes do ataque do Dragão'
)
replace_once(
    "     if(key==='dragonTakeoff')DRAGON_TAKEOFF_DURATION=validGifDuration(duration,DRAGON_TAKEOFF_DURATION);",
    "     if(key==='dragonTakeoff')DRAGON_TAKEOFF_DURATION=validGifDuration(duration,DRAGON_TAKEOFF_DURATION);\n     if(key==='dragonAttack')DRAGON_ATTACK_VISUAL_MS=validGifDuration(duration,DRAGON_ATTACK_VISUAL_MS);",
    'medição do GIF de ataque do Dragão'
)
replace_once(
    "dragonTakeoffStartedAt:0,dragonTakeoffEndAt:0,dragonNextShotAt:0,",
    "dragonTakeoffStartedAt:0,dragonTakeoffEndAt:0,dragonNextShotAt:0,dragonCloseShotAt:0,",
    'estado do cooldown de emergência do Dragão'
)

# 2) Troca estável de sprites: o sprite anterior só desaparece depois que o novo
#    está carregado. Tokens impedem callbacks atrasados de uma troca antiga.
stable_sprite_function = r'''function setEntitySpriteState(el,desired){
 const previous=el.dataset.anim||'';
 if(previous===desired)return false;

 const sprites=[
   [el._idle,'idle'],[el._walk,'walk'],[el._golemAttack,'attack'],
   [el._golemSpecial,'special'],[el._mageSpecial,'special'],
   [el._dragonGround,'ground'],[el._dragonTakeoff,'takeoff'],[el._dragonFly,'fly'],[el._dragonAttack,'dragonAttack']
 ];
 const desiredImg=(sprites.find(([img,stateName])=>img&&stateName===desired)||[])[0]||null;
 const token=(el._spriteSwitchToken||0)+1;
 el._spriteSwitchToken=token;
 el.dataset.anim=desired;

 // Mostra o novo imediatamente, mas mantém o estado anterior como "rede de segurança"
 // até o browser confirmar que existe imagem decodificável para a nova animação.
 for(const [img,stateName] of sprites){
   if(!img)continue;
   if(stateName===desired){
     img.style.opacity='1';
     img.classList.add('active-sprite');
   }else if(stateName!==previous){
     img.style.opacity='0';
     img.classList.remove('active-sprite');
   }
 }

 const finalize=()=>{
   if(el._spriteSwitchToken!==token||el.dataset.anim!==desired)return;
   for(const [img,stateName] of sprites){
     if(!img)continue;
     const active=stateName===desired;
     img.style.opacity=active?'1':'0';
     img.classList.toggle('active-sprite',active);
   }

   // Só interrompe a decodificação do GIF antigo DEPOIS que o novo já entrou.
   if(previous==='attack'&&desired!=='attack')stopGif(el._golemAttack);
   if(previous==='special'&&desired!=='special'){
     stopGif(el._golemSpecial);
     stopGif(el._mageSpecial);
   }
   if(previous==='takeoff'&&desired!=='takeoff')stopGif(el._dragonTakeoff);
   if(previous==='dragonAttack'&&desired!=='dragonAttack')stopGif(el._dragonAttack);
 };
 const settle=()=>requestAnimationFrame(finalize);

 if(!desiredImg){
   finalize();
 }else if(desiredImg.complete&&desiredImg.naturalWidth>0){
   settle();
 }else{
   desiredImg.addEventListener('load',settle,{once:true});
   desiredImg.addEventListener('error',settle,{once:true});
   // Failsafe apenas para um asset realmente problemático; o token evita
   // que esse timeout interfira caso outra animação já tenha sido escolhida.
   setTimeout(settle,700);
 }
 return true;
}'''
regex_once(
    r"function setEntitySpriteState\(el,desired\)\{.*?\n\}\n\nfunction setEntityNodeVisible",
    stable_sprite_function + "\n\nfunction setEntityNodeVisible",
    'troca estável de sprites'
)

# 3) Dragão: cada serial visual toca uma vez e até o último quadro. Snapshot atrasado
#    não consegue ressuscitar o mesmo ataque e causar pisca-pisca.
dragon_visual_branch = r'''}else if(e.type==='dragon'){
     const flight=e.dragonFlightState||'ground';
     const takeoffSerial=Number(e.dragonTakeoffSerial)||0;

     if(flight==='takeoff'&&takeoffSerial>0&&el.dataset.dragonTakeoffSerial!==String(takeoffSerial)){
       el.dataset.dragonTakeoffSerial=String(takeoffSerial);
       el._dragonTakeoffVisualEndAt=localNow+DRAGON_TAKEOFF_DURATION;
       restartGif(el._dragonTakeoff,'dragonTakeoff',takeoffSerial);
     }
     const takeoffActive=takeoffSerial>0&&Number(el._dragonTakeoffVisualEndAt||0)>localNow;

     const pendingAttack=e.pendingDragonAttack;
     const attackSerial=Number(pendingAttack?.serial||e.dragonAttackSerial)||0;
     // Se o cliente recebeu a decolagem um pouco atrasada, ela termina primeiro.
     // Depois o ataque começa do quadro zero, sem cortar nenhum frame.
     if(!takeoffActive&&flight==='flying'&&pendingAttack&&attackSerial>0&&el.dataset.dragonAttackSerial!==String(attackSerial)){
       el.dataset.dragonAttackSerial=String(attackSerial);
       el._dragonAttackVisualEndAt=localNow+DRAGON_ATTACK_VISUAL_MS;
       restartGif(el._dragonAttack,'dragonAttack',attackSerial);
     }
     const attackActive=flight==='flying'&&Number(el._dragonAttackVisualEndAt||0)>localNow;

     const desired=takeoffActive?'takeoff':attackActive?'dragonAttack':flight==='flying'?'fly':'ground';
     setEntitySpriteState(el,desired);
   }else{
     const desired=e.moving?'walk':'idle';'''
regex_once(
    r"\}else if\(e\.type==='dragon'\)\{\n\s+const flight=e\.dragonFlightState\|\|'ground';.*?\n\s+\}else\{\n\s+const desired=e\.moving\?'walk':'idle';",
    dragon_visual_branch,
    'máquina visual estável do Dragão'
)

# 4) Disparo normal e disparo de emergência quando o alvo cola demais.
launch_function = r'''function launchDragonFireball(e,target,{emergency=false}={}){
           if(!e?.alive||e.type!=='dragon'||e.dragonFlightState!=='flying'||!target?.alive)return false;
           const now=performance.now();
           const gate=emergency?(Number(e.dragonCloseShotAt)||0):(Number(e.dragonNextShotAt)||0);
           if(now<gate)return false;
           const angle=Math.atan2(target.y-e.y,target.x-e.x);e.heading=angle;if(Math.abs(target.x-e.x)>4)e.facing=target.x<e.x?-1:1;
           e.moving=false;e.dragonAttackSerial=(e.dragonAttackSerial||0)+1;
           e.pendingDragonAttack={serial:e.dragonAttackSerial,startedAt:now,endAt:now+DRAGON_ATTACK_VISUAL_MS,emergency:!!emergency};
           if(emergency){
             e.dragonCloseShotAt=now+DRAGON_CLOSE_SHOT_COOLDOWN_MS;
             e.dragonNextShotAt=Math.max(Number(e.dragonNextShotAt)||0,now+DRAGON_SHOT_COOLDOWN_MS);
           }else{
             e.dragonNextShotAt=now+DRAGON_SHOT_COOLDOWN_MS;
             // Se o alvo correr para cima do Dragão logo após um tiro normal,
             // esse mesmo tiro conta para a janela de 5 s do modo de emergência.
             e.dragonCloseShotAt=Math.max(Number(e.dragonCloseShotAt)||0,now+DRAGON_CLOSE_SHOT_COOLDOWN_MS);
           }
           const startX=e.x+Math.cos(angle)*42,startY=e.y-16+Math.sin(angle)*18;
           state.dragonProjectiles.push({id:'df_'+(++state.dragonProjectileSeq),serial:e.dragonAttackSerial,x:startX,y:startY,vx:Math.cos(angle)*DRAGON_FIREBALL_SPEED,vy:Math.sin(angle)*DRAGON_FIREBALL_SPEED,targetId:target.id,targetX:target.x,targetY:target.y,team:e.team,sourceId:e.id,createdAt:now,expireAt:now+4500});
           return true;
          }
          function updateDragonProjectiles'''
regex_once(
    r"function launchDragonFireball\(e,target\)\{.*?\n\s*\}\n\s*function updateDragonProjectiles",
    launch_function,
    'lançamento de bola de fogo'
)

ai_dragon_function = r'''function aiFightDragon(e,dt,forcedTeam,preparedCandidates=null){
           if(!e.alive||e.knockTime>0){e.moving=false;return}
           const now=performance.now();updateDragonState(e,now);
           if(e.dragonFlightState!=='flying'){e.moving=false;return}
           if(e.pendingDragonAttack&&now<e.pendingDragonAttack.endAt){e.moving=false;return}
           const candidates=(preparedCandidates||state.entities.filter(t=>t.alive&&t!==e&&(forcedTeam?t.team===forcedTeam:t.team!==e.team))).filter(t=>canEngageTarget(e,t));
           if(!candidates.length){e.moving=false;e.target=null;return}
           let target=candidates[0],best=dist(e,target);for(let i=1;i<candidates.length;i++){const d=dist(e,candidates[i]);if(d<best){best=d;target=candidates[i]}}
           e.target=target;const dx=target.x-e.x,dy=target.y-e.y,d=Math.hypot(dx,dy)||1;e.heading=Math.atan2(dy,dx);if(Math.abs(dx)>4)e.facing=dx<0?-1:1;

           // Alvo perto demais: ainda consegue se defender, mas só uma vez a cada 5 s.
           // Entre esses disparos, tenta abrir espaço para voltar à faixa normal de 185–285.
           if(d<DRAGON_CLOSE_RANGE){
             if(now>=Number(e.dragonCloseShotAt||0)&&launchDragonFireball(e,target,{emergency:true}))return;
             let mx=-dx/d,my=-dy/d;
             const edge=125;
             if(e.x<edge)mx+=.85;else if(e.x>state.world.w-edge)mx-=.85;
             if(e.y<edge)my+=.85;else if(e.y>state.world.h-edge)my-=.85;
             const ml=Math.hypot(mx,my)||1;mx/=ml;my/=ml;
             e.x+=mx*e.speed*dt;e.y+=my*e.speed*dt;e.moving=true;
             e.x=clamp(e.x,40,state.world.w-40);e.y=clamp(e.y,40,state.world.h-40);
             return;
           }

           if(d>=185&&d<=285&&now>=Number(e.dragonNextShotAt||0)){launchDragonFireball(e,target);return}
           if(d>285){e.x+=dx/d*e.speed*dt;e.y+=dy/d*e.speed*dt;e.moving=true}
           else if(d<185){e.x-=dx/d*e.speed*dt;e.y-=dy/d*e.speed*dt;e.moving=true}
           else e.moving=false;
           e.x=clamp(e.x,40,state.world.w-40);e.y=clamp(e.y,40,state.world.h-40);
          }

          function aiFightMage'''
regex_once(
    r"function aiFightDragon\(e,dt,forcedTeam,preparedCandidates=null\)\{.*?\n\s*\}\n\n\s*function aiFightMage",
    ai_dragon_function,
    'IA de combate do Dragão'
)

# 5) NPCs deixam de gastar tudo instantaneamente. As primeiras compras são mais
#    aleatórias; depois cada compra observa a composição dos exércitos adversários.
bot_setup = r'''  // Bots compram ao longo da preparação: abrem com alguma aleatoriedade
  // e depois passam a reagir ao que os outros exércitos realmente colocaram.
  const botPrepNow=performance.now();
  state.players.filter(p=>!p.human).forEach((p,i)=>{
   p.botWarPurchases=0;
   p.botNextPurchaseAt=botPrepNow+350+i*180+rand(0,450);
  });
}
$('#shopButton')'''
regex_once(
    r"  // Bots usam os quatro tipos do clã Guerreiros\.\n  state\.players\.filter\(p=>!p\.human\)\.forEach\(p=>\{.*?\n  \}\);\n\}\n\$\('#shopButton'\)",
    bot_setup,
    'planejamento inicial dos bots'
)

adaptive_bot_helpers = r'''
function warCompositionForTeam(teamId){
 const out={warrior:0,mage:0,golem:0,dragon:0};
 for(const e of state.entities){
   if(!e.alive||e.team!==teamId||!(e.type in out))continue;
   out[e.type]++;
 }
 return out;
}
function enemyWarComposition(teamId){
 const out={warrior:0,mage:0,golem:0,dragon:0};
 for(const e of state.entities){
   if(!e.alive||e.team===teamId||!(e.type in out))continue;
   out[e.type]++;
 }
 return out;
}
function affordableBotWarTypes(p){
 const types=[];
 if(p.gems>=75)types.push('warrior');
 if(p.gems>=350){types.push('golem');types.push('dragon')}
 if(p.gems>=550)types.push('mage');
 return types;
}
function chooseBotWarPurchase(p){
 const affordable=affordableBotWarTypes(p);
 if(!affordable.length)return null;
 const enemy=enemyWarComposition(p.id),own=warCompositionForTeam(p.id);
 const enemyTotal=enemy.warrior+enemy.mage+enemy.golem+enemy.dragon;
 const opening=(Number(p.botWarPurchases)||0)<2;

 // Abertura ainda tem personalidade/variação e evita todos os NPCs montarem
 // exatamente o mesmo exército quando ninguém comprou nada ainda.
 if(enemyTotal===0||Math.random()<(opening?.65:.28)){
   return affordable[Math.floor(Math.random()*affordable.length)];
 }

 const score={warrior:1,mage:1,golem:1,dragon:1};
 // Contra Mago, Guerreiro consegue pressionar; contra muitos Guerreiros, Golem
 // e Mago ganham valor; Golem/Dragão inimigos aumentam bastante o valor de ranged.
 score.warrior+=enemy.mage*1.45+enemy.golem*.12;
 score.golem+=enemy.warrior*1.65+enemy.mage*.35+enemy.dragon*.45;
 score.mage+=enemy.golem*1.85+enemy.dragon*2.15+enemy.warrior*.55;
 score.dragon+=enemy.golem*1.35+enemy.mage*.85+enemy.warrior*.45+enemy.dragon*.70;
 // Guerreiro não alcança Dragão voando: evita responder a um exército aéreo
 // comprando mais unidades que não conseguem atacá-lo.
 if(enemy.dragon>0)score.warrior*=.10;

 // Pequeno redutor por repetição mantém composição variada, sem transformar
 // a escolha adaptativa numa regra rígida e previsível.
 for(const type of Object.keys(score))score[type]-=(own[type]||0)*.32;

 let bestType=affordable[0],bestScore=-Infinity;
 for(const type of affordable){
   const value=score[type]+Math.random()*.40;
   if(value>bestScore){bestScore=value;bestType=type}
 }
 return bestType;
}
function buyBotWarType(p,type){
 if(type==='dragon')return buyDragonForPlayer(p,true);
 if(type==='golem')return buyGolemForPlayer(p,true);
 if(type==='mage')return buyMageForPlayer(p,true);
 return buyForPlayer(p,true);
}
function updateWarBotPurchases(now,force=false){
 for(const p of state.players.filter(p=>!p.human)){
   let guard=0;
   while(p.gems>=75&&(force||now>=Number(p.botNextPurchaseAt||0))&&guard<(force?30:1)){
     const type=chooseBotWarPurchase(p);
     if(!type)break;
     let bought=buyBotWarType(p,type);
     if(!bought&&p.gems>=75)bought=buyForPlayer(p,true);
     if(!bought)break;
     p.botWarPurchases=(Number(p.botWarPurchases)||0)+1;
     p.botNextPurchaseAt=now+(state.prepLeft<3?rand(220,420):rand(650,1250));
     guard++;
   }
 }
}

'''
anchor = "\nfunction startCombatPhase(){"
if text.count(anchor) != 1:
    raise SystemExit('âncora de startCombatPhase não encontrada de forma única')
text = text.replace(anchor, "\n" + adaptive_bot_helpers + "function startCombatPhase(){", 1)

replace_once(
    " if(state.phase==='prep'){\n   state.prepLeft-=dt;\n   if(state.prepLeft<=0)startCombatPhase();",
    " if(state.phase==='prep'){\n   const now=performance.now();\n   updateWarBotPurchases(now,false);\n   state.prepLeft-=dt;\n   if(state.prepLeft<=0){updateWarBotPurchases(now,true);startCombatPhase();}",
    'compras adaptativas durante preparação'
)

# Guardas finais do patch.
required = [
    "let DRAGON_ATTACK_VISUAL_MS=1800;",
    "if(key==='dragonAttack')DRAGON_ATTACK_VISUAL_MS=validGifDuration(duration,DRAGON_ATTACK_VISUAL_MS);",
    "DRAGON_CLOSE_SHOT_COOLDOWN_MS=5000",
    "function updateWarBotPurchases(now,force=false)",
    "function chooseBotWarPurchase(p)",
    "el._dragonAttackVisualEndAt=localNow+DRAGON_ATTACK_VISUAL_MS",
    "function setEntitySpriteState(el,desired)",
    "launchDragonFireball(e,target,{emergency=true})"
]
for marker in required:
    if marker not in text:
        raise SystemExit('marcador final ausente: '+marker)
if 'const DRAGON_ATTACK_VISUAL_MS=850;' in text:
    raise SystemExit('timer antigo do ataque do Dragão ainda presente')
if 'i.postimg.cc' in text:
    raise SystemExit('referência externa ao Postimg reapareceu')

path.write_text(text, encoding='utf-8')
