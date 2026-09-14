from pathlib import Path

path=Path('index.html')
text=path.read_text(encoding='utf-8')

old='''   if(e.clan==='egypt'){
     // Egito: 4 ataques normais -> o 5º ataque elegível é especial.
     // A trava é INDIVIDUAL: contam apenas guerreiros que ESTE mago invocou.
     // Se ainda houver 2 ou mais vivos, o especial nem entra em estado visual;
     // o mago segue atacando normalmente até restar no máximo 1 dos seus próprios invocados.
     const cycleDue=(Number(e.mageCycle)||0)>=4;
     const summonsAlive=countLivingEgyptSummonsForMage(e.id);
     if(e.specialCooldown<=0&&summonsAlive<=1&&cycleDue){
       if(startMageAttack(e,'special',target))return;
     }
   }else{'''

new='''   if(e.clan==='egypt'){
     // Egito: o especial fica devido quando QUALQUER uma destas condições ocorre:
     // 1) 4 ataques normais completos (o 5º ataque elegível vira especial);
     // 2) o escudo chega a zero;
     // 3) a vida chega a 50% ou menos.
     // A trava continua INDIVIDUAL: contam apenas guerreiros que ESTE mago invocou.
     // Se ainda houver 2 ou mais vivos, o especial nem entra no estado visual e o mago
     // continua atacando normalmente até restar no máximo 1 dos seus próprios invocados.
     const cycleDue=(Number(e.mageCycle)||0)>=4;
     const shieldDown=(Number(e.shield)||0)<=0;
     const halfHealth=Number(e.hp)<=Number(e.maxHp)*0.50;
     const specialDue=cycleDue||shieldDown||halfHealth;
     const summonsAlive=countLivingEgyptSummonsForMage(e.id);
     if(e.specialCooldown<=0&&summonsAlive<=1&&specialDue){
       if(startMageAttack(e,'special',target))return;
     }
   }else{'''

if old not in text:
    raise SystemExit('Current Egypt mage AI anchor not found; refusing unsafe patch')
text=text.replace(old,new,1)

marker='/* EGYPT MAGE INDIVIDUAL SUMMON CYCLE 2026-09-13 */'
if marker not in text:
    raise SystemExit('Expected Egypt mage revision marker missing')
text=text.replace(marker,marker+'\n/* EGYPT MAGE SHIELD + HALF-HP SPECIAL TRIGGERS 2026-09-13 */',1)

required=[
    "const cycleDue=(Number(e.mageCycle)||0)>=4;",
    "const shieldDown=(Number(e.shield)||0)<=0;",
    "const halfHealth=Number(e.hp)<=Number(e.maxHp)*0.50;",
    "const specialDue=cycleDue||shieldDown||halfHealth;",
    "const summonsAlive=countLivingEgyptSummonsForMage(e.id);",
    "if(e.specialCooldown<=0&&summonsAlive<=1&&specialDue){",
]
missing=[x for x in required if x not in text]
if missing:
    raise SystemExit('Missing new Egypt mage trigger markers: '+repr(missing))

forbidden=[
    "if(e.specialCooldown<=0&&summonsAlive<=1&&cycleDue){",
    'countLivingEgyptSummons(e.team)',
    'hasPendingEgyptSummonSpecial(e.team,e.id)',
    'WAR ADAPTIVE VISUAL LOD 2026-09-12',
]
present=[x for x in forbidden if x in text]
if present:
    raise SystemExit('Old/forbidden markers remain: '+repr(present))

path.write_text(text,encoding='utf-8')
print('Egypt mage special triggers updated: cycle OR shield zero OR HP <= 50%, with per-mage summon gate preserved.')
