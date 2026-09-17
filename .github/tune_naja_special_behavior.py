from pathlib import Path

p = Path('index.html')
t = p.read_text(encoding='utf-8')


def replace_one_of(olds, new, label):
    global t
    if new in t:
        return
    for old in olds:
        count = t.count(old)
        if count == 1:
            t = t.replace(old, new, 1)
            return
    raise SystemExit(f'{label}: no unique migration anchor found')


# 1) A Naja nao recebe dano em nenhuma fase do especial, incluindo a emergencia.
replace_one_of(
    [
        "function najaIsInvulnerable(e,now=performance.now()){\n const phase=najaSpecialPhase(e,now);\n return phase==='burrowing'||phase==='underground';\n}"
    ],
    "function najaIsInvulnerable(e,now=performance.now()){\n const phase=najaSpecialPhase(e,now);\n return phase!==null;\n}",
    'Naja full special invulnerability',
)

# 2) Offset visual perceptivel para a direita e para baixo, sem mudar hitbox/logica.
replace_one_of(
    [
        ".entity-visual.naja-visual .entity-body{\n  left:-8px;\n  top:-8px;\n  width:126px;\n  height:132px;\n  object-fit:contain;\n}",
        ".entity-visual.naja-visual .entity-body{\n  left:-2px;\n  top:-2px;\n  width:126px;\n  height:132px;\n  object-fit:contain;\n}"
    ],
    ".entity-visual.naja-visual .entity-body{\n  left:8px;\n  top:10px;\n  width:126px;\n  height:132px;\n  object-fit:contain;\n}",
    'Naja visual offset',
)

# 3) Estado do especial unico disparado pelo rompimento do escudo.
replace_one_of(
    [
        " e.najaAttackSerial=0;\n e.najaNormalCount=0;\n e.najaPhase='seek';\n e.pendingNajaAttack=null;"
    ],
    " e.najaAttackSerial=0;\n e.najaNormalCount=0;\n e.najaShieldSpecialUsed=false;\n e.najaShieldSpecialPending=false;\n e.najaPhase='seek';\n e.pendingNajaAttack=null;",
    'Naja shield special initial state',
)

# Replica os dois flags no snapshot online.
replace_one_of(
    [
        "   out.najaAttackSerial=Number(e.najaAttackSerial)||0;\n   out.najaNormalCount=Number(e.najaNormalCount)||0;\n   out.najaPhase=e.najaPhase||'seek';"
    ],
    "   out.najaAttackSerial=Number(e.najaAttackSerial)||0;\n   out.najaNormalCount=Number(e.najaNormalCount)||0;\n   out.najaShieldSpecialUsed=!!e.najaShieldSpecialUsed;\n   out.najaShieldSpecialPending=!!e.najaShieldSpecialPending;\n   out.najaPhase=e.najaPhase||'seek';",
    'Naja shield special network state',
)

# Guarda o escudo anterior para detectar exatamente a primeira transicao para zero.
replace_one_of(
    [
        "const beforeDurability=Math.max(0,Number(target.shield)||0)+Math.max(0,Number(target.hp)||0);"
    ],
    "const beforeShield=Math.max(0,Number(target.shield)||0);\n const beforeDurability=beforeShield+Math.max(0,Number(target.hp)||0);",
    'Naja shield break detection baseline',
)

# Quando o escudo rompe pela primeira vez, arma apenas um especial e libera o cooldown.
replace_one_of(
    [
        " if(remaining>0)target.hp-=remaining;\n const afterDurability=Math.max(0,Number(target.shield)||0)+Math.max(0,Number(target.hp)||0);"
    ],
    " if(remaining>0)target.hp-=remaining;\n // O primeiro rompimento do escudo da Naja arma exatamente um especial extra.\n if(target.type==='naja'&&!target.najaShieldSpecialUsed&&beforeShield>0&&target.shield<=0){\n   target.najaShieldSpecialUsed=true;\n   target.najaShieldSpecialPending=true;\n   target.attackCooldown=0;\n }\n const afterDurability=Math.max(0,Number(target.shield)||0)+Math.max(0,Number(target.hp)||0);",
    'Naja shield break special trigger',
)

# Consome o gatilho assim que qualquer especial realmente comeca.
replace_one_of(
    [
        " }else{\n   // Cancela qualquer empurrão que já estivesse em andamento no instante em que cava.\n   e.knockTime=0;e.knockVX=0;e.knockVY=0;"
    ],
    " }else{\n   // Consome o gatilho do escudo ao iniciar qualquer especial; o marcador used impede repeticao.\n   e.najaShieldSpecialPending=false;\n   // Cancela qualquer empurrão que já estivesse em andamento no instante em que cava.\n   e.knockTime=0;e.knockVX=0;e.knockVY=0;",
    'Naja shield special consumption',
)

# O especial do escudo tem prioridade; depois dele a propria conclusao do especial zera
# najaNormalCount, devolvendo a Naja ao ciclo normal de 4 ataques + especial.
replace_one_of(
    [
        " // 4 ataques normais completos; o 5º ataque é o especial de escavação.\n if((Number(e.najaNormalCount)||0)>=4){"
    ],
    " // Escudo zerado prioriza um especial unico; depois segue o ciclo normal de 4 ataques + especial.\n const najaNeedsSpecial=!!e.najaShieldSpecialPending||(Number(e.najaNormalCount)||0)>=4;\n if(najaNeedsSpecial){",
    'Naja shield special AI priority',
)

p.write_text(t, encoding='utf-8')

required = [
    "return phase!==null;",
    "left:8px;",
    "top:10px;",
    "e.najaShieldSpecialUsed=false;",
    "e.najaShieldSpecialPending=false;",
    "out.najaShieldSpecialUsed=!!e.najaShieldSpecialUsed;",
    "out.najaShieldSpecialPending=!!e.najaShieldSpecialPending;",
    "target.type==='naja'&&!target.najaShieldSpecialUsed&&beforeShield>0&&target.shield<=0",
    "target.najaShieldSpecialUsed=true;",
    "target.najaShieldSpecialPending=true;",
    "e.najaShieldSpecialPending=false;",
    "const najaNeedsSpecial=!!e.najaShieldSpecialPending||(Number(e.najaNormalCount)||0)>=4;",
]
missing = [x for x in required if x not in t]
if missing:
    raise SystemExit('Missing Naja special behavior tuning: ' + repr(missing))

print('Naja special invulnerability, stronger visual offset and shield-break trigger applied.')
