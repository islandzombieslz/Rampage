from pathlib import Path

path=Path('index.html')
text=path.read_text(encoding='utf-8')
MARKER='EGYPT SUMMON HALF HP + BROWN KING DAMAGE 2026-09-13'


def replace_once(old,new,label):
    global text
    if new in text:
        return
    count=text.count(old)
    if count!=1:
        raise SystemExit(f'{label}: expected 1 occurrence, found {count}')
    text=text.replace(old,new,1)


# Marker.
if MARKER not in text:
    anchor='/* WAR SPECIALS + GEMS STABILITY 2026-09-13 */'
    if anchor not in text:
        raise SystemExit('marker anchor missing')
    text=text.replace(anchor,anchor+'\n/* '+MARKER+' */',1)

# Egypt Mage special: exactly 2 summons. Summoned warriors have no shield and
# have half the normal HP capacity, but spawn at that reduced max HP so their
# health bar is visually full.
old_spawn="""function spawnEgyptMageWarriors(e,p){
 const ox=Number(p.originX)||e.x,oy=Number(p.originY)||e.y;
 const base=(Number(e.mageAttackSerial)||0)*.37;
 for(let i=0;i<3;i++){
   const angle=base+(Math.PI*2/3)*i;
   const radius=62+(i%2)*30;
   const x=clamp(ox+Math.cos(angle)*radius,45,state.world.w-45);
   const y=clamp(oy+Math.sin(angle)*radius,45,state.world.h-45);
   const variant=i%2===0?'male':'female';
   const summon=spawnWarrior(x,y,e.team,e.color,false,variant,null,'egypt',true,e.id);
   summon.shield=0;
   summon.maxShield=0;
 }
}
"""
new_spawn="""function spawnEgyptMageWarriors(e,p){
 const ox=Number(p.originX)||e.x,oy=Number(p.originY)||e.y;
 const base=(Number(e.mageAttackSerial)||0)*.37;
 for(let i=0;i<2;i++){
   const angle=base+Math.PI*i;
   const radius=70+(i%2)*22;
   const x=clamp(ox+Math.cos(angle)*radius,45,state.world.w-45);
   const y=clamp(oy+Math.sin(angle)*radius,45,state.world.h-45);
   const variant=i%2===0?'male':'female';
   const summon=spawnWarrior(x,y,e.team,e.color,false,variant,null,'egypt',true,e.id);
   const halfHp=Math.max(1,Math.round((Number(summon.maxHp)||Number(summon.hp)||1)*.5));
   summon.maxHp=halfHp;
   summon.hp=halfHp;
   summon.shield=0;
   summon.maxShield=0;
 }
}
"""
replace_once(old_spawn,new_spawn,'Egypt summon count/HP')

# Brown Warrior: +12 to every normal hit and every special tick.
replace_once('const BROWN_NORMAL_DAMAGE_1=40;','const BROWN_NORMAL_DAMAGE_1=52;','Brown normal hit 1')
replace_once('const BROWN_NORMAL_DAMAGE_2=25;','const BROWN_NORMAL_DAMAGE_2=37;','Brown normal hit 2')
replace_once('const BROWN_SPECIAL_DAMAGE=25;','const BROWN_SPECIAL_DAMAGE=37;','Brown special damage')

# Warrior King: +12 normal and special.
replace_once('const KING_SPECIAL_DAMAGE=50;','const KING_SPECIAL_DAMAGE=62;','King special damage')
old_king="""function spawnKing(x,y,team,color){
 const e=entityBase('king',x,y,team,color);
 if(state.mode==='war')e.speed*=WAR_TROOP_SPEED_MULTIPLIER;
 e.hp=e.maxHp=280;
 e.shield=e.maxShield=280;
 e.damage=35;
 e.r=29;
 e.kingNormalCount=0;
 state.entities.push(e);
 return e;
}
"""
new_king=old_king.replace('e.damage=35;','e.damage=47;')
replace_once(old_king,new_king,'King normal damage')

path.write_text(text,encoding='utf-8')
print('Applied Egypt summon HP/count and Brown/King +12 damage patch')
