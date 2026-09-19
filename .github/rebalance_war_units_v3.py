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
    "const ISIS_HEAL_AMOUNT=20;",
    "const ISIS_SELF_HEAL_AMOUNT=5;",
    "const ISIS_SHIELD_BREAK_TRIGGER_COUNT=3;",
    "const ISIS_FLIGHT_LIFT=52;",
    "const ISIS_MAX_ALLIES=3;",
    "const ISIS_HEAL_REUSE_LOCK_MS=5000;",
    "const hasNonIsisAlly=teamAllies.some(ally=>ally.type!=='isis');",
    "if(hasNonIsisAlly&&ally.type==='isis')continue;",
    "if(reserved.has(ally.id))continue;",
    "now-lastHealAt<ISIS_HEAL_REUSE_LOCK_MS",
    "ally.isisLastHealedAt=healAt;",
    "ally.isisLastHealedBy=e.id;",
    ".entity-visual.isis-visual .entity-body{left:24px;top:10px;width:142px;height:166px;object-fit:contain}",
    "e.speed=state.mode==='war'?102*WAR_TROOP_SPEED_MULTIPLIER:102;",
    "if(isisSpecialProtected(target))return;",
    "function isAirborneCombatTarget(",
    "function unitCannotHitFlying(",
    "function registerIsisAllyShieldBreak(",
    "registerIsisAllyShieldBreak(target)",
    "const specialDue=(Number(e.isisNormalCount)||0)>=4||(Number(e.isisShieldBreakCount)||0)>=ISIS_SHIELD_BREAK_TRIGGER_COUNT;",
    "e.hp=Math.min(Number(e.maxHp)||0,beforeSelf+ISIS_SELF_HEAL_AMOUNT);",
    "ally.hp=Math.min(Number(ally.maxHp)||0,beforeHp+ISIS_HEAL_AMOUNT);",
    "flightLift=ISIS_FLIGHT_LIFT",
    "e.type==='isis'?1.44",
    "img.style.width=(178*zoom)+'px'",
    "out.isisShieldBreakCount=Number(e.isisShieldBreakCount)||0;",
    "assets/egypt/isis/card.png",
    "assets/egypt/isis/walk.gif",
    "assets/egypt/isis/idle.gif",
    "assets/egypt/isis/attack-normal.gif",
    "assets/egypt/isis/special.gif",
    "assets/egypt/isis/power-special.gif",
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

forbidden=[
    "if(isisProtected)amount=5;",
    "const ISIS_HEAL_AMOUNT=15;",
    "assets/egypt/isis/card.webp",
    "assets/egypt/isis/idle.webp",
    "assets/egypt/isis/walk.webp",
    "assets/egypt/isis/attack-normal.webp",
    "assets/egypt/isis/special.webp",
    "assets/egypt/isis/power-special.webp",
]
stale=[x for x in forbidden if x in t]
if stale:
    raise SystemExit('Old Isis assets still referenced: '+repr(stale))

print('War rebalance v3 validated.')
