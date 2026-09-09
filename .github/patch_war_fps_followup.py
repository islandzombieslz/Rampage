from pathlib import Path

path=Path('index.html')
text=path.read_text(encoding='utf-8')
MARKER='WAR FPS CANDIDATE SAFETY 2026-09-09'
if MARKER in text:
    print('War FPS candidate-safety patch already applied.')
    raise SystemExit(0)


def replace_once(old,new,label):
    global text
    if old not in text:
        raise SystemExit(f'Trecho não encontrado: {label}')
    text=text.replace(old,new,1)

old_golem=""" for(const candidate of candidates){
   const ndx=candidate.x-e.x,ndy=candidate.y-e.y,ds=ndx*ndx+ndy*ndy;
   if(ds<=golemSpecialRadiusSq){
"""
new_golem=""" // WAR FPS CANDIDATE SAFETY 2026-09-09
 for(const candidate of candidates){
   // O cache de alvo dura poucos ms; um candidato pode morrer entre dois refreshes.
   // Ignora stale/aliado sem recriar arrays com filter().
   if(!candidate||!candidate.alive||candidate===e||candidate.team===e.team||
      (forcedTeam&&candidate.team!==forcedTeam)||!canEngageTarget(e,candidate))continue;
   const ndx=candidate.x-e.x,ndy=candidate.y-e.y,ds=ndx*ndx+ndy*ndy;
   if(ds<=golemSpecialRadiusSq){
"""
replace_once(old_golem,new_golem,'candidatos próximos do Golem')

old_mage="""   for(const t of candidates){
     const sdx=t.x-e.x,sdy=t.y-e.y;
     if(sdx*sdx+sdy*sdy<=mageSpecialRadiusSq)nearbyForSpecial++;
   }
"""
new_mage="""   for(const t of candidates){
     if(!t||!t.alive||t===e||t.team===e.team||
        (forcedTeam&&t.team!==forcedTeam)||!canEngageTarget(e,t))continue;
     const sdx=t.x-e.x,sdy=t.y-e.y;
     if(sdx*sdx+sdy*sdy<=mageSpecialRadiusSq)nearbyForSpecial++;
   }
"""
replace_once(old_mage,new_mage,'candidatos próximos do Mago')

checks=[
    MARKER,
    "(forcedTeam&&candidate.team!==forcedTeam)||!canEngageTarget(e,candidate)",
    "(forcedTeam&&t.team!==forcedTeam)||!canEngageTarget(e,t)",
    'const WAR_AI_GRID_REFRESH_MS=90;',
    'function nearestEngageableCandidate',
]
for marker in checks:
    if marker not in text:
        raise SystemExit(f'Validação candidate-safety falhou: {marker}')

for marker in [
    'function tryWarriorFleeFlyingDragon',
    'if(tryWarriorFleeFlyingDragon(e,dt))return;',
]:
    if marker in text:
        raise SystemExit(f'Fuga do Dragão reapareceu: {marker}')

path.write_text(text,encoding='utf-8')
print('Cache de candidatos da Guerra validado sem voltar a criar arrays temporários.')
