from pathlib import Path

path = Path('index.html')
text = path.read_text(encoding='utf-8')

def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected 1 match, found {count}')
    text = text.replace(old, new, 1)

# Shop accessibility/title prices.
for old, new, label in [
    ('Comprar Guerreiro por 75 gemas', 'Comprar Guerreiro por 50 gemas', 'warrior aria price'),
    ('Guerreiro — 75 gemas', 'Guerreiro — 50 gemas', 'warrior title price'),
    ('Comprar Rei Guerreiro por 250 gemas', 'Comprar Rei Guerreiro por 300 gemas', 'king aria price'),
    ('Rei Guerreiro — 250 gemas', 'Rei Guerreiro — 300 gemas', 'king title price'),
    ('Comprar Golem por 350 gemas', 'Comprar Golem por 550 gemas', 'golem aria price'),
    ('Golem — 350 gemas', 'Golem — 550 gemas', 'golem title price'),
    ('Comprar Dragão por 350 gemas', 'Comprar Dragão por 450 gemas', 'dragon aria price'),
    ('Dragão — 350 gemas', 'Dragão — 450 gemas', 'dragon title price'),
]:
    replace_once(old, new, label)

# Centralized war economy constants.
replace_once(
"const WAR_GOLEM_EXTRA_SPEED_MULTIPLIER=.87; // depois dos -50%, o Golem fica um pouco mais lento que o Mago\nconst difficultyConfig={",
"const WAR_GOLEM_EXTRA_SPEED_MULTIPLIER=.87; // depois dos -50%, o Golem fica um pouco mais lento que o Mago\nconst WAR_UNIT_COSTS=Object.freeze({warrior:50,king:300,golem:550,mage:550,dragon:450});\nconst WAR_ROUND_GEM_REWARD=Object.freeze({winner:200,loser:100,tie:100});\nconst WAR_GOALS=Object.freeze({specials:{target:5,reward:70},ranged:{target:3,reward:40}});\nconst difficultyConfig={",
'economy constants')

# Reset round goals each round and add the goal tracker.
replace_once(
"   p.troops=0;\n   p.territory=territoryFor(i,state.players.length);",
"   p.troops=0;\n   p.warGoals={specials:0,ranged:0,specialsClaimed:false,rangedClaimed:false};\n   p.territory=territoryFor(i,state.players.length);",
'round goal reset')

replace_once(
"}\n$('#shopButton').onclick=()=>$('#shop').classList.toggle('open');",
"}\nfunction addWarGoalProgress(teamId,kind){\n const goal=WAR_GOALS[kind];\n if(state.mode!=='war'||state.phase!=='combat'||!goal)return;\n const p=state.players.find(player=>player.id===teamId);\n if(!p)return;\n const progress=p.warGoals||(p.warGoals={specials:0,ranged:0,specialsClaimed:false,rangedClaimed:false});\n const claimedKey=kind+'Claimed';\n progress[kind]=Math.min(goal.target,(Number(progress[kind])||0)+1);\n if(progress[claimedKey]||progress[kind]<goal.target)return;\n progress[claimedKey]=true;\n p.bonusGems=(Number(p.bonusGems)||0)+goal.reward;\n if(p.id===localWarTeamId()){\n   const label=kind==='specials'?'ESPECIAIS':'DISTÂNCIA';\n   flash(`META ${label} ${goal.target}/${goal.target} • +${goal.reward} 💎`,1.5);\n }\n}\n$('#shopButton').onclick=()=>$('#shop').classList.toggle('open');",
'goal tracker')

# Purchase prices use centralized constants.
replace_once(" if(p.gems<75)return false;\n p.gems-=75;", " const cost=WAR_UNIT_COSTS.warrior;if(p.gems<cost)return false;\n p.gems-=cost;", 'warrior purchase')
replace_once(" if(p.gems<250)return false;\n p.gems-=250;", " const cost=WAR_UNIT_COSTS.king;if(p.gems<cost)return false;\n p.gems-=cost;", 'king purchase')
replace_once(" if(p.gems<350)return false;\n p.gems-=350;", " const cost=WAR_UNIT_COSTS.golem;if(p.gems<cost)return false;\n p.gems-=cost;", 'golem purchase')
replace_once(" if(p.gems<550)return false;p.gems-=550;p.troops++;", " const cost=WAR_UNIT_COSTS.mage;if(p.gems<cost)return false;p.gems-=cost;p.troops++;", 'mage purchase')
replace_once(" if(p.gems<350)return false;p.gems-=350;p.troops++;", " const cost=WAR_UNIT_COSTS.dragon;if(p.gems<cost)return false;p.gems-=cost;p.troops++;", 'dragon purchase')

replace_once(
" if(p.gems>=75)types.push('warrior');\n if(p.gems>=250)types.push('king');\n if(p.gems>=350){types.push('golem');types.push('dragon')}\n if(p.gems>=550)types.push('mage');",
" if(p.gems>=WAR_UNIT_COSTS.warrior)types.push('warrior');\n if(p.gems>=WAR_UNIT_COSTS.king)types.push('king');\n if(p.gems>=WAR_UNIT_COSTS.golem)types.push('golem');\n if(p.gems>=WAR_UNIT_COSTS.dragon)types.push('dragon');\n if(p.gems>=WAR_UNIT_COSTS.mage)types.push('mage');",
'bot affordability')
replace_once(
"   while(p.gems>=75&&(force||now>=Number(p.botNextPurchaseAt||0))&&guard<(force?30:1)){",
"   while(p.gems>=WAR_UNIT_COSTS.warrior&&(force||now>=Number(p.botNextPurchaseAt||0))&&guard<(force?30:1)){",
'bot minimum while')
replace_once("     if(!bought&&p.gems>=75)bought=buyForPlayer(p,true);", "     if(!bought&&p.gems>=WAR_UNIT_COSTS.warrior)bought=buyForPlayer(p,true);", 'bot fallback')

# Goal events: count attack launches, not damage ticks/hits.
replace_once(
"   impacted:false\n };\n return true;\n}\n\nfunction resolveGolemImpact",
"   impacted:false\n };\n if(kind==='special')addWarGoalProgress(e.team,'specials');\n return true;\n}\n\nfunction resolveGolemImpact",
'golem special goal')
replace_once(
"   };\n   e.mageCycle=0;\n }else{",
"   };\n   e.mageCycle=0;\n   addWarGoalProgress(e.team,'specials');\n }else{",
'mage special goal')
replace_once(
"   };\n   e.mageCycle=(e.mageCycle||0)+1;\n }\n return true;\n}",
"   };\n   e.mageCycle=(e.mageCycle||0)+1;\n   addWarGoalProgress(e.team,'ranged');\n }\n return true;\n}",
'mage ranged goal')
replace_once(
"   endAt:now+duration,impacted:false,hitIds:{}\n };\n return true;\n}\n\nfunction updateKingSpecialState",
"   endAt:now+duration,impacted:false,hitIds:{}\n };\n addWarGoalProgress(e.team,'specials');\n return true;\n}\n\nfunction updateKingSpecialState",
'king special goal')
replace_once(
"           state.dragonProjectiles.push({id:'df_'+(++state.dragonProjectileSeq),serial:e.dragonAttackSerial,x:startX,y:startY,vx:Math.cos(angle)*DRAGON_FIREBALL_SPEED,vy:Math.sin(angle)*DRAGON_FIREBALL_SPEED,targetId:target.id,targetX:target.x,targetY:target.y,team:e.team,sourceId:e.id,createdAt:now,expireAt:now+4500});\n           return true;",
"           state.dragonProjectiles.push({id:'df_'+(++state.dragonProjectileSeq),serial:e.dragonAttackSerial,x:startX,y:startY,vx:Math.cos(angle)*DRAGON_FIREBALL_SPEED,vy:Math.sin(angle)*DRAGON_FIREBALL_SPEED,targetId:target.id,targetX:target.x,targetY:target.y,team:e.team,sourceId:e.id,createdAt:now,expireAt:now+4500});\n           addWarGoalProgress(e.team,'ranged');\n           return true;",
'dragon ranged goal')

# Round reward: winner keeps +200, every loser gets +100; ties give +100 to everyone.
replace_once(
" // Bônus acumulativo do Mestre da Guerra:\n // o vencedor único recebe +200 gemas nas rodadas seguintes.\n if(winners.length===1){\n   winners[0].bonusGems=(winners[0].bonusGems||0)+200;\n   flash(`${winners[0].name} venceu a rodada! +200 💎`,1.8);\n }else{\n   flash('Empate na rodada! Sem bônus de gemas.',1.8);\n }",
" // Recompensas acumulativas para as rodadas seguintes.\n // Vencedor recebe +200; cada perdedor também progride, mas recebe +100.\n if(winners.length===1){\n   const winner=winners[0];\n   state.players.forEach(p=>{\n     const reward=p.id===winner.id?WAR_ROUND_GEM_REWARD.winner:WAR_ROUND_GEM_REWARD.loser;\n     p.bonusGems=(Number(p.bonusGems)||0)+reward;\n   });\n   flash(`${winner.name} venceu! +${WAR_ROUND_GEM_REWARD.winner} 💎 • perdedores +${WAR_ROUND_GEM_REWARD.loser} 💎`,2);\n }else{\n   state.players.forEach(p=>p.bonusGems=(Number(p.bonusGems)||0)+WAR_ROUND_GEM_REWARD.tie);\n   flash(`Empate! Todos recebem +${WAR_ROUND_GEM_REWARD.tie} 💎`,1.8);\n }",
'round rewards')

# HUD shows current achievement progress and uses the new prices for availability.
replace_once(
"    const me=localPlayer(),gems=me?.gems??0;\n    perfSetText(hudMainPerfEl,`${state.round}/${state.rounds}`);\n    perfSetText(hudSubPerfEl,`💎 ${gems}`);",
"    const me=localPlayer(),gems=me?.gems??0,goals=me?.warGoals||{};\n    const specials=Math.min(WAR_GOALS.specials.target,Number(goals.specials)||0),ranged=Math.min(WAR_GOALS.ranged.target,Number(goals.ranged)||0);\n    perfSetText(hudMainPerfEl,`${state.round}/${state.rounds}`);\n    perfSetText(hudSubPerfEl,`💎 ${gems} • ✨ ${specials}/${WAR_GOALS.specials.target} • 🎯 ${ranged}/${WAR_GOALS.ranged.target}`);",
'hud goal progress')
replace_once(
"    perfSetDisabled(buyWarriorPerfEl,state.phase!=='prep'||gems<75);\n    perfSetDisabled(buyKingPerfEl,state.phase!=='prep'||gems<250);\n    perfSetDisabled(buyGolemPerfEl,state.phase!=='prep'||gems<350);\n    perfSetDisabled(buyMagePerfEl,state.phase!=='prep'||gems<550);\n    perfSetDisabled(buyDragonPerfEl,state.phase!=='prep'||gems<350);",
"    perfSetDisabled(buyWarriorPerfEl,state.phase!=='prep'||gems<WAR_UNIT_COSTS.warrior);\n    perfSetDisabled(buyKingPerfEl,state.phase!=='prep'||gems<WAR_UNIT_COSTS.king);\n    perfSetDisabled(buyGolemPerfEl,state.phase!=='prep'||gems<WAR_UNIT_COSTS.golem);\n    perfSetDisabled(buyMagePerfEl,state.phase!=='prep'||gems<WAR_UNIT_COSTS.mage);\n    perfSetDisabled(buyDragonPerfEl,state.phase!=='prep'||gems<WAR_UNIT_COSTS.dragon);",
'hud purchase availability')

path.write_text(text, encoding='utf-8')
print('war economy/goals patch applied')
