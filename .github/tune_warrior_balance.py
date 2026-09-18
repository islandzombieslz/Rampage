from pathlib import Path

p=Path('index.html')
t=p.read_text(encoding='utf-8')


def replace_one_of(olds,new,label):
    global t
    if new in t:
        return
    found=[old for old in olds if old in t]
    if len(found)!=1:
        raise SystemExit(f'{label}: expected exactly 1 migration anchor, found {len(found)}')
    t=t.replace(found[0],new,1)


# Economia: Guerreiro 90, Rei 500. Mantem os demais custos.
replace_one_of(
    [
        "const WAR_UNIT_COSTS=Object.freeze({warrior:65,brownWarrior:450,king:400,golem:550,mage:550,dragon:450,naja:550,anubis:450});",
        "const WAR_UNIT_COSTS=Object.freeze({warrior:65,brownWarrior:450,king:400,golem:550,mage:550,dragon:450,naja:550});",
        "const WAR_UNIT_COSTS=Object.freeze({warrior:50,brownWarrior:450,king:400,golem:550,mage:550,dragon:450,naja:550});",
    ],
    "const WAR_UNIT_COSTS=Object.freeze({warrior:90,brownWarrior:450,king:500,golem:550,mage:550,dragon:450,naja:550,anubis:450});",
    'War unit costs',
)

replace_one_of(
    [
        'aria-label="Comprar Guerreiro por 65 gemas" title="Guerreiro — 65 gemas"',
        'aria-label="Comprar Guerreiro por 50 gemas" title="Guerreiro — 50 gemas"',
    ],
    'aria-label="Comprar Guerreiro por 90 gemas" title="Guerreiro — 90 gemas"',
    'Normal warrior shop price',
)
replace_one_of(
    [
        'aria-label="Comprar Guerreiro do Egito por 65 gemas" title="Guerreiro do Egito — 65 gemas"',
        'aria-label="Comprar Guerreiro do Egito por 50 gemas" title="Guerreiro do Egito — 50 gemas"',
    ],
    'aria-label="Comprar Guerreiro do Egito por 90 gemas" title="Guerreiro do Egito — 90 gemas"',
    'Egypt warrior shop price',
)
replace_one_of(
    ['aria-label="Comprar Rei Guerreiro por 400 gemas" title="Rei Guerreiro — 400 gemas"'],
    'aria-label="Comprar Rei Guerreiro por 500 gemas" title="Rei Guerreiro — 500 gemas"',
    'King shop price',
)

# Cadencia atual dos Guerreiros permanece em 0,50 s.
replace_one_of(
    [" // Guerreiros atacam um pouco mais devagar que na versão anterior.\n e.attackCooldown=.38;\n e.attackAnim=.30;"],
    " // Guerreiros normais e do Egito atacam em cadencia um pouco mais lenta.\n e.attackCooldown=.50;\n e.attackAnim=.30;",
    'Warrior attack cadence',
)

# Golem: 50 normal / 80 especial.
replace_one_of([" e.damage=40;\n e.r=39;"]," e.damage=50;\n e.r=39;",'Golem entity damage')
replace_one_of(["     applyCombatHit(target,e,40,{"],"     applyCombatHit(target,e,50,{",'Golem normal hit')
replace_one_of(["     applyCombatHit(t,e,70,{"],"     applyCombatHit(t,e,80,{",'Golem special hit')

# Mago Guerreiro: cura 50 de si mesmo e dos aliados dentro do especial.
replace_one_of(["const MAGE_SPECIAL_HEAL=30;"],"const MAGE_SPECIAL_HEAL=50;",'Warrior Mage special heal')

# Janela de 2 s de imunidade de abertura para Rei e Mago Guerreiro.
replace_one_of(
    ["const KING_SPECIAL_DAMAGE=55;"],
    "const KING_SPECIAL_DAMAGE=55;\nconst WAR_SPECIAL_OPENING_INVULN_MS=2000;",
    'Special opening invulnerability constant',
)

entity_anchor="""function entityHasActiveSpecial(e,now=performance.now()){
 if(!e?.alive)return false;
 if(e.type==='mage')return e.pendingMageAttack?.kind==='special'&&Number(e.pendingMageAttack.endAt)>now;
 if(e.type==='golem')return e.pendingGolemAttack?.kind==='special'&&Number(e.pendingGolemAttack.endAt)>now;
 if(e.type==='naja')return e.pendingNajaAttack?.kind==='special'&&Number(e.pendingNajaAttack.endAt)>now;
 if(e.type==='brownWarrior')return e.pendingBrownAttack?.kind==='special'&&Number(e.pendingBrownAttack.endAt)>now;
 if(e.type==='king')return !!e.pendingKingSpecial&&Number(e.pendingKingSpecial.endAt)>now;
 return false;
}
"""
invuln_fn="""
function warSpecialOpeningInvulnerable(e,now=performance.now()){
 if(!e?.alive)return false;
 if(e.type==='king'){
   const p=e.pendingKingSpecial;
   return !!p&&Number(p.endAt)>now&&now<Number(p.startedAt||0)+WAR_SPECIAL_OPENING_INVULN_MS;
 }
 if(e.type==='mage'&&e.clan==='warriors'){
   const p=e.pendingMageAttack;
   return p?.kind==='special'&&Number(p.endAt)>now&&now<Number(p.startedAt||0)+WAR_SPECIAL_OPENING_INVULN_MS;
 }
 return false;
}
"""
if invuln_fn not in t:
    if entity_anchor not in t:
        raise SystemExit('Special helper anchor missing')
    t=t.replace(entity_anchor,entity_anchor+invuln_fn,1)

old_hit=""" // A Naja é invulnerável enquanto inicia a escavação e enquanto está subterrânea.
 if(target.type==='naja'&&najaIsInvulnerable(target))return;
"""
new_hit=""" // A Naja é invulnerável enquanto inicia a escavação e enquanto está subterrânea.
 if(target.type==='naja'&&najaIsInvulnerable(target))return;
 // Rei e Mago Guerreiro ignoram dano e empurrão nos 2 primeiros segundos do especial.
 if(warSpecialOpeningInvulnerable(target))return;
"""
if new_hit not in t:
    if old_hit not in t:
        raise SystemExit('Combat hit invulnerability anchor missing')
    t=t.replace(old_hit,new_hit,1)

p.write_text(t,encoding='utf-8')

required=[
    'warrior:90',
    'king:500',
    'Comprar Guerreiro por 90 gemas',
    'Comprar Guerreiro do Egito por 90 gemas',
    'Comprar Rei Guerreiro por 500 gemas',
    'e.attackCooldown=.50;',
    'e.damage=50;',
    'applyCombatHit(target,e,50,{',
    'applyCombatHit(t,e,80,{',
    'const MAGE_SPECIAL_HEAL=50;',
    'const WAR_SPECIAL_OPENING_INVULN_MS=2000;',
    "e.type==='mage'&&e.clan==='warriors'",
    'if(warSpecialOpeningInvulnerable(target))return;',
]
missing=[x for x in required if x not in t]
if missing:
    raise SystemExit('Missing war balance tuning: '+repr(missing))

print('War economy, Golem, Warrior Mage and special immunity tuning applied.')
