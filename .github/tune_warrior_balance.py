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

replace_one_of(
    [
        "const WAR_TROOP_SPEED_MULTIPLIER=.50;\nconst WAR_GOLEM_EXTRA_SPEED_MULTIPLIER=.87;",
    ],
    "const WAR_TROOP_SPEED_MULTIPLIER=.50;\nconst WAR_BASIC_WARRIOR_SPEED_MULTIPLIER=.92; // guerreiros básicos: leve redução adicional de movimento\nconst WAR_GOLEM_EXTRA_SPEED_MULTIPLIER=.87;",
    'Basic warrior speed multiplier',
)

replace_one_of(
    [
        "const WAR_UNIT_COSTS=Object.freeze({warrior:90,brownWarrior:450,king:500,golem:550,mage:550,dragon:450,naja:550,anubis:450});",
        "const WAR_UNIT_COSTS=Object.freeze({warrior:65,brownWarrior:450,king:400,golem:550,mage:550,dragon:450,naja:550,anubis:450});",
    ],
    "const WAR_UNIT_COSTS=Object.freeze({warrior:100,brownWarrior:450,king:500,golem:550,mage:550,dragon:450,naja:550,anubis:450});",
    'War unit costs',
)

replace_one_of(
    ['aria-label="Comprar Guerreiro por 90 gemas" title="Guerreiro — 90 gemas"'],
    'aria-label="Comprar Guerreiro por 100 gemas" title="Guerreiro — 100 gemas"',
    'Normal warrior shop price',
)
replace_one_of(
    ['aria-label="Comprar Guerreiro do Egito por 90 gemas" title="Guerreiro do Egito — 90 gemas"'],
    'aria-label="Comprar Guerreiro do Egito por 100 gemas" title="Guerreiro do Egito — 100 gemas"',
    'Egypt warrior shop price',
)

replace_one_of(
    [" if(state.mode==='war')e.speed*=WAR_TROOP_SPEED_MULTIPLIER;\n e.hp=e.maxHp=150;"],
    [" if(state.mode==='war')e.speed*=WAR_TROOP_SPEED_MULTIPLIER*WAR_BASIC_WARRIOR_SPEED_MULTIPLIER;\n e.hp=e.maxHp=150;"][0],
    'Basic warrior movement speed',
)

replace_one_of(
    [" // Guerreiros normais e do Egito atacam em cadencia um pouco mais lenta.\n e.attackCooldown=.50;\n e.attackAnim=.30;"],
    " // Cadências separadas: Rei menos sequencial; Guerreiros básicos com pausa mais perceptível.\n e.attackCooldown=e.type==='king'?.65:e.type==='warrior'?.70:.50;\n e.attackAnim=.30;",
    'Warrior and King cadence',
)

replace_one_of(
    [" e.hp=e.maxHp=280;\n e.shield=e.maxShield=280;\n e.damage=38;"],
    " e.hp=e.maxHp=280;\n e.shield=e.maxShield=280;\n e.damage=33;",
    'King normal damage',
)

replace_one_of(
    [" e.hp=e.maxHp=600;\n e.shield=e.maxShield=200;\n e.damage=50;"],
    " e.hp=e.maxHp=650;\n e.shield=e.maxShield=250;\n e.damage=50;",
    'Golem durability',
)
replace_one_of(
    [" e.clan='egypt';\n e.hp=e.maxHp=600;\n e.shield=e.maxShield=200;\n e.damage=60;"],
    " e.clan='egypt';\n e.hp=e.maxHp=650;\n e.shield=e.maxShield=250;\n e.damage=60;",
    'Naja durability',
)
replace_one_of(
    [" e.hp=e.maxHp=250;\n e.shield=e.maxShield=150;"],
    " e.hp=e.maxHp=265;\n e.shield=e.maxShield=165;",
    'Brown Warrior durability',
)
replace_one_of(
    ["const typeScale=e.type==='golem'?1.34:e.type==='anubis'?1.34:e.type==='naja'?1.75:e.type==='brownWarrior'?1.10:e.type==='mage'?0.96:e.type==='dragon'?1.16:e.type==='king'?0.96:1;"],
    "const typeScale=e.type==='golem'?1.34:e.type==='anubis'?1.34:e.type==='naja'?1.75:e.type==='brownWarrior'?1.16:e.type==='mage'?0.96:e.type==='dragon'?1.16:e.type==='king'?0.96:1;",
    'Brown Warrior visual size',
)
replace_one_of(
    [" e.hp=e.maxHp=150;e.shield=e.maxShield=50;e.damage=ANUBIS_PROJECTILE_DAMAGE;e.r=34;"],
    " e.hp=e.maxHp=165;e.shield=e.maxShield=65;e.damage=ANUBIS_PROJECTILE_DAMAGE;e.r=34;",
    'Anubis durability',
)
replace_one_of(
    [" e.hp=e.maxHp=150;e.shield=e.maxShield=50;e.damage=DRAGON_FIREBALL_DAMAGE;e.r=34;"],
    " e.hp=e.maxHp=165;e.shield=e.maxShield=65;e.damage=DRAGON_FIREBALL_DAMAGE;e.r=34;",
    'Dragon durability',
)

p.write_text(t,encoding='utf-8')

required=[
    'warrior:100',
    'Comprar Guerreiro por 100 gemas',
    'Comprar Guerreiro do Egito por 100 gemas',
    'const WAR_BASIC_WARRIOR_SPEED_MULTIPLIER=.92;',
    "e.attackCooldown=e.type==='king'?.65:e.type==='warrior'?.70:.50;",
    'e.damage=33;',
    'e.hp=e.maxHp=650;',
    'e.shield=e.maxShield=250;',
    'e.hp=e.maxHp=265;',
    'e.shield=e.maxShield=165;',
    "e.type==='brownWarrior'?1.16",
    'e.hp=e.maxHp=165;e.shield=e.maxShield=65;e.damage=ANUBIS_PROJECTILE_DAMAGE',
    'e.hp=e.maxHp=165;e.shield=e.maxShield=65;e.damage=DRAGON_FIREBALL_DAMAGE',
    'const MAGE_SPECIAL_HEAL=50;',
    'const WAR_SPECIAL_OPENING_INVULN_MS=2000;',
]
missing=[x for x in required if x not in t]
if missing:
    raise SystemExit('Missing war rebalance: '+repr(missing))

print('War troop rebalance v2 applied.')
