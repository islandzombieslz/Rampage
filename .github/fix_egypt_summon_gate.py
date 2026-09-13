from pathlib import Path
import re

path = Path('index.html')
text = path.read_text(encoding='utf-8')

helper = '''function hasPendingEgyptSummonSpecial(team,excludeId=null){
 for(const t of state.entities){
   if(!t.alive||t.id===excludeId||t.team!==team||t.type!=='mage'||t.clan!=='egypt')continue;
   if(t.pendingMageAttack?.kind==='special')return true;
 }
 return false;
}
'''

if 'function hasPendingEgyptSummonSpecial(' not in text:
    anchor = '''function spawnEgyptMageWarriors(e,p){'''
    if anchor not in text:
        raise SystemExit('spawnEgyptMageWarriors anchor not found')
    text = text.replace(anchor, helper + anchor, 1)

old_gate = "if(e.specialCooldown<=0&&summonsAlive<=1&&(lowHealth||cycleDue)){"
new_gate = "if(e.specialCooldown<=0&&summonsAlive<=1&&!hasPendingEgyptSummonSpecial(e.team,e.id)&&(lowHealth||cycleDue)){"
if old_gate in text:
    text = text.replace(old_gate, new_gate, 1)
elif new_gate not in text:
    raise SystemExit('Egypt special gate anchor not found')

required = [
    'function hasPendingEgyptSummonSpecial(team,excludeId=null)',
    new_gate,
    'function spawnEgyptMageWarriors(e,p)',
    "spawnWarrior(x,y,e.team,e.color,false,variant,null,'egypt',true)",
]
missing = [x for x in required if x not in text]
if missing:
    raise SystemExit('Missing guard markers: ' + repr(missing))

for forbidden in ['WAR ADAPTIVE VISUAL LOD 2026-09-12', 'entity-lod-poster', 'WAR_LOD_POSTER_CACHE']:
    if forbidden in text:
        raise SystemExit('Reverted LOD code found: ' + forbidden)

path.write_text(text, encoding='utf-8')
print('Egypt summon concurrency guard applied.')
