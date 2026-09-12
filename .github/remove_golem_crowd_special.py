from pathlib import Path
import re

path = Path('index.html')
text = path.read_text(encoding='utf-8')
original = text

# 1) Remove o estado persistente da antiga exceção de especial por aglomeração.
text = text.replace(
    "golemPhase:'seek',golemCrowdSpecialUsed:false,golemLastAttackCompletedAt:0,",
    "golemPhase:'seek',golemLastAttackCompletedAt:0,"
)

# 2) Atualiza os comentários/estado inicial do Golem: só existe o ciclo 4 normais -> especial.
text = text.replace(
    " // O especial do Golem agora é controlado pela máquina de estados:\n"
    " // 4 ataques normais -> 1 especial, com uma exceção única para aglomeração.\n"
    " e.specialCooldown=0;\n"
    " // Resistência a empurrão de Guerreiro/Mago: 1 impacto empurra, os 3 seguintes não.\n"
    " e.golemKnockCycle=0;\n"
    " e.golemNormalCount=0;\n"
    " // O bônus por aglomeração só pode furar o ciclo uma vez na vida deste Golem.\n"
    " // Depois dele, a regra é sempre quatro normais e um especial.\n"
    " e.golemCrowdSpecialUsed=false;\n",
    " // O especial do Golem é controlado pela máquina de estados:\n"
    " // 4 ataques normais completos -> 1 especial.\n"
    " e.specialCooldown=0;\n"
    " // Resistência a empurrão de Guerreiro/Mago: 1 impacto empurra, os 3 seguintes não.\n"
    " e.golemKnockCycle=0;\n"
    " e.golemNormalCount=0;\n"
)

# 3) Especial nunca mais precisa registrar o motivo 'crowd'.
text = text.replace("\n     if(p.reason==='crowd')e.golemCrowdSpecialUsed=true;", "")

# 4) Remove de aiFightGolem toda a contagem de inimigos próximos e o gatilho único por aglomeração.
pattern = re.compile(
    r"\n let nearbySpecialTarget=null,nearbySpecialBestSq=Infinity,nearbySpecialCount=0;"
    r".*?"
    r"\n // ESTADO 3B — ciclo padrão:",
    re.S,
)
text, count = pattern.subn("\n // ESTADO 3 — ciclo padrão:", text, count=1)
if count != 1:
    raise SystemExit(f'Expected exactly one Golem crowd-special AI block, found {count}')

# 5) Garantias: a mecânica antiga desapareceu e o ciclo principal continua intacto.
required = [
    "function aiFightGolem(e,dt,forcedTeam,preparedCandidates=null)",
    "if((Number(e.golemNormalCount)||0)>=4)",
    "startGolemAttack(e,'special',target,'cycle')",
    "if(d<=92)",
    "startGolemAttack(e,'normal',target,'cycle')",
    "const radius=230,r2=radius*radius;",
    "applyCombatHit(t,e,70,{",
    "e.golemKnockCycle=0;",
]
missing = [x for x in required if x not in text]
if missing:
    raise SystemExit('Preserved Golem mechanics missing: ' + repr(missing))

for forbidden in [
    'golemCrowdSpecialUsed',
    'crowdActive',
    "startGolemAttack(e,'special',nearbySpecialTarget,'crowd')",
    'nearbySpecialCount',
    'exceção de aglomeração',
]:
    if forbidden in text:
        raise SystemExit('Old Golem crowd-special logic remains: ' + forbidden)

if text == original:
    raise SystemExit('No changes applied')

path.write_text(text, encoding='utf-8')
print('Removed Golem crowd-triggered special. Cycle is now strictly 4 normal attacks -> special.')
