from pathlib import Path
p=Path('index.html')
t=p.read_text(encoding='utf-8')

required=[
    "const WAR_UNIT_COSTS=Object.freeze({warrior:100,brownWarrior:450,king:500,golem:550,mage:550,dragon:450,naja:550,anubis:450,isis:500});",
    "function spawnIsis(",
    "e.hp=e.maxHp=265;e.shield=e.maxShield=165;e.damage=ISIS_NORMAL_DAMAGE_1",
    "const ISIS_NORMAL_DAMAGE_1=Math.max(0,BROWN_NORMAL_DAMAGE_1-15);",
    "const ISIS_NORMAL_DAMAGE_2=Math.max(0,BROWN_NORMAL_DAMAGE_2-15);",
    "const ISIS_SPECIAL_DELAY_MS=2000;",
    "const ISIS_HEAL_AMOUNT=15;",
    "function updateIsisAttackState(",
    "function syncIsisPowerEffects(",
    "const WAR_BASIC_WARRIOR_SPEED_MULTIPLIER=.92;",
    "e.attackCooldown=e.type==='king'?.65:e.type==='warrior'?.70:.50;",
    "e.damage=33;",
    "e.hp=e.maxHp=650;",
    "e.shield=e.maxShield=250;",
    "e.hp=e.maxHp=265;",
    "e.shield=e.maxShield=165;",
    "e.type==='brownWarrior'?1.16",
    "e.hp=e.maxHp=165;e.shield=e.maxShield=65;e.damage=ANUBIS_PROJECTILE_DAMAGE",
    "e.hp=e.maxHp=165;e.shield=e.maxShield=65;e.damage=DRAGON_FIREBALL_DAMAGE",
]
missing=[x for x in required if x not in t]
if missing:
    raise SystemExit('War rebalance v3 missing: '+repr(missing))
print('War rebalance v3 validated.')
