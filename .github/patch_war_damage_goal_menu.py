from pathlib import Path

path=Path('index.html')
text=path.read_text(encoding='utf-8')

def replace_once(old,new,label):
    global text
    count=text.count(old)
    if count!=1:
        raise SystemExit(f'{label}: expected 1 match, found {count}')
    text=text.replace(old,new,1)

# 1) Nova meta: 100 de dano real na rodada = +50 gemas.
replace_once(
"const WAR_GOALS=Object.freeze({specials:{target:5,reward:70},ranged:{target:3,reward:40}});",
"const WAR_GOALS=Object.freeze({specials:{target:5,reward:70},ranged:{target:3,reward:40},damage:{target:100,reward:50}});",
'WAR_GOALS'
)

old_goal_state="{specials:0,ranged:0,specialsClaimed:false,rangedClaimed:false}"
new_goal_state="{specials:0,ranged:0,damage:0,specialsClaimed:false,rangedClaimed:false,damageClaimed:false}"
count=text.count(old_goal_state)
if count<2:
    raise SystemExit(f'goal state: expected at least 2 matches, found {count}')
text=text.replace(old_goal_state,new_goal_state)

# Função separada porque dano progride por quantidade, não por evento.
anchor="function requestWarPurchase(type){"
if 'function addWarDamageProgress(teamId,amount)' not in text:
    if text.count(anchor)!=1:
        raise SystemExit(f'damage helper anchor: expected 1 match, found {text.count(anchor)}')
    helper="""function addWarDamageProgress(teamId,amount){
 const goal=WAR_GOALS.damage;
 if(state.mode!=='war'||state.phase!=='combat'||!goal)return;
 const value=Math.max(0,Number(amount)||0);
 if(value<=0)return;
 const p=state.players.find(player=>player.id===teamId);
 if(!p)return;
 const progress=p.warGoals||(p.warGoals={specials:0,ranged:0,damage:0,specialsClaimed:false,rangedClaimed:false,damageClaimed:false});
 progress.damage=Math.min(goal.target,(Number(progress.damage)||0)+value);
 if(progress.damageClaimed||progress.damage<goal.target)return;
 progress.damageClaimed=true;
 p.bonusGems=(Number(p.bonusGems)||0)+goal.reward;
 if(p.id===localWarTeamId())flash(`META DANO ${goal.target}/${goal.target} • +${goal.reward} 💎`,1.5);
}
"""
    text=text.replace(anchor,helper+anchor,1)

# Soma dano REAL retirado de escudo + vida, sem overkill.
replace_once(
" if(!options.allowFlying&&target.type==='dragon'&&target.dragonFlightState==='flying'&&(attacker.type==='warrior'||attacker.type==='king'))return;\n\n // Escudo absorve primeiro.",
" if(!options.allowFlying&&target.type==='dragon'&&target.dragonFlightState==='flying'&&(attacker.type==='warrior'||attacker.type==='king'))return;\n const beforeDurability=Math.max(0,Number(target.shield)||0)+Math.max(0,Number(target.hp)||0);\n\n // Escudo absorve primeiro.",
'combat durability before'
)
replace_once(
" if(remaining>0)target.hp-=remaining;\n\n // Direção do impacto.",
" if(remaining>0)target.hp-=remaining;\n const afterDurability=Math.max(0,Number(target.shield)||0)+Math.max(0,Number(target.hp)||0);\n const actualDamage=Math.max(0,beforeDurability-afterDurability);\n if(actualDamage>0&&attacker.team&&attacker.team!==target.team)addWarDamageProgress(attacker.team,actualDamage);\n\n // Direção do impacto.",
'combat actual damage'
)

# Mantém autoria da queimadura mesmo se a unidade que iniciou o fogo morrer antes do último tick.
replace_once(
"target.dragonBurnNextTick=now+DRAGON_BURN_TICK_MS;target.dragonBurnSourceId=source?.id??null;",
"target.dragonBurnNextTick=now+DRAGON_BURN_TICK_MS;target.dragonBurnSourceId=source?.id??null;target.dragonBurnSourceTeam=source?.team??null;",
'burn source team'
)
replace_once(
"return entityById.get(target.dragonBurnSourceId)||{id:'dragon-burn',type:'dragon',x:Number(target.dragonBurnSourceX)||target.x,y:Number(target.dragonBurnSourceY)||target.y,heading:0,lastCombatAt:0};",
"return entityById.get(target.dragonBurnSourceId)||{id:'dragon-burn',type:'dragon',team:target.dragonBurnSourceTeam??null,x:Number(target.dragonBurnSourceX)||target.x,y:Number(target.dragonBurnSourceY)||target.y,heading:0,lastCombatAt:0};",
'burn fallback team'
)
replace_once(
"target.dragonBurnUntil=0;target.dragonBurnStartedAt=0;target.dragonBurnNextTick=0;target.dragonBurnSourceId=null;",
"target.dragonBurnUntil=0;target.dragonBurnStartedAt=0;target.dragonBurnNextTick=0;target.dragonBurnSourceId=null;target.dragonBurnSourceTeam=null;",
'burn cleanup team'
)

# 2) HUD do modo Guerra: só gemas; metas continuam sendo calculadas em segundo plano.
replace_once(
"    const me=localPlayer(),gems=me?.gems??0,goals=me?.warGoals||{};\n    const specials=Math.min(WAR_GOALS.specials.target,Number(goals.specials)||0),ranged=Math.min(WAR_GOALS.ranged.target,Number(goals.ranged)||0);",
"    const me=localPlayer(),gems=me?.gems??0;",
'HUD goal vars'
)
replace_once(
"    perfSetText(hudSubPerfEl,`💎 ${gems} • ✨ ${specials}/${WAR_GOALS.specials.target} • 🎯 ${ranged}/${WAR_GOALS.ranged.target}`);",
"    perfSetText(hudSubPerfEl,`💎 ${gems}`);",
'HUD gem only'
)

# 3) Remove textos econômicos do painel para liberar espaço dentro do sprite.
info_block="""        <div class=\"small\">Guerreiro 50 • Rei 300 • Dragão 450 • Golem 550 • Mago 550 gemas.</div>
        <div class=\"small\">Rodada: vencedor +200 • perdedores +100 • empate +100 para todos.</div>
        <div class=\"small\">Metas: 5 especiais +70 • 3 ataques à distância +40 gemas.</div>
"""
replace_once(info_block,"",'economy info block')

# Ajuste exclusivo do Mestre da Guerra: painel maior no landscape, controles menores e counter em 3 colunas.
css_anchor=".config{padding:16px;background:#0d1117;border:1px solid var(--line);border-radius:15px}"
menu_css="""
/* Mestre da Guerra: mantém todos os controles dentro da área útil do sprite. */
#configScreen.war-config>.card{
  width:min(730px,94vw,94vh);
  height:min(730px,94vw,94vh);
  padding:15.2% 15.8% 13.2%;
  gap:2px;
}
#configScreen.war-config #warConfig{gap:5px 8px}
#configScreen.war-config #warConfig .config{padding:2px 0}
#configScreen.war-config #warConfig .label{font-size:12px;margin-bottom:3px}
#configScreen.war-config #warConfig .option-group button,
#configScreen.war-config #warConfig .counter button{
  min-height:30px;
  padding:4px 6px;
  font-size:12px;
}
#configScreen.war-config #warConfig .counter{
  display:grid;
  grid-template-columns:32px minmax(36px,1fr) 32px;
  gap:6px;
  align-items:center;
  width:100%;
}
#configScreen.war-config #warConfig .counter button{width:100%;min-width:0}
#configScreen.war-config #warConfig .counter b{min-width:0;font-size:17px;text-align:center}
#configScreen.war-config>.card>.divider{margin:2px 0 3px}
#configScreen.war-config>.card>.row:last-child button{min-height:34px;padding:5px 7px}
@media (pointer:coarse), (max-height:560px), (max-width:700px){
  #configScreen.war-config>.card{
    width:min(660px,96vw,96vh);
    height:min(660px,96vw,96vh);
    padding:14.2% 14.8% 12.4%;
  }
  #configScreen.war-config #warConfig{gap:3px 5px}
  #configScreen.war-config #warConfig .config{padding:1px 0}
  #configScreen.war-config #warConfig .label{font-size:10.5px;margin-bottom:1px}
  #configScreen.war-config #warConfig .option-group button,
  #configScreen.war-config #warConfig .counter button{min-height:27px;padding:3px 4px;font-size:10.5px}
  #configScreen.war-config #warConfig .counter{grid-template-columns:28px minmax(32px,1fr) 28px;gap:4px}
  #configScreen.war-config #warConfig .counter b{font-size:14px}
  #configScreen.war-config>.card>.row:last-child button{min-height:30px;font-size:11px}
}
"""
if '/* Mestre da Guerra: mantém todos os controles dentro da área útil do sprite. */' not in text:
    if text.count(css_anchor)!=1:
        raise SystemExit(f'menu css anchor: expected 1 match, found {text.count(css_anchor)}')
    text=text.replace(css_anchor,menu_css+css_anchor,1)

path.write_text(text,encoding='utf-8')
print('war damage goal + HUD + menu patch applied')
