from pathlib import Path

path = Path('index.html')
text = path.read_text(encoding='utf-8')
MARKER = 'EGYPT SUMMON FULL HP + KING REBALANCE 2026-09-15'


def replace_once(old, new, label):
    global text
    if new in text:
        return
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected 1 occurrence, found {count}')
    text = text.replace(old, new, 1)


# Marker for this balance pass.
if MARKER not in text:
    anchor = '/* EGYPT SUMMON HALF HP + BROWN KING DAMAGE 2026-09-13 */'
    if anchor not in text:
        raise SystemExit('marker anchor missing')
    text = text.replace(anchor, anchor + '\n/* ' + MARKER + ' */', 1)

# Egypt Mage still spawns exactly 2 warriors, but each summon now has the
# normal Egypt Warrior HP capacity (150/150) while remaining shieldless.
old_hp = """   const summon=spawnWarrior(x,y,e.team,e.color,false,variant,null,'egypt',true,e.id);
   const halfHp=Math.max(1,Math.round((Number(summon.maxHp)||Number(summon.hp)||1)*.5));
   summon.maxHp=halfHp;
   summon.hp=halfHp;
   summon.shield=0;
   summon.maxShield=0;
"""
new_hp = """   const summon=spawnWarrior(x,y,e.team,e.color,false,variant,null,'egypt',true,e.id);
   summon.hp=150;
   summon.maxHp=150;
   summon.shield=0;
   summon.maxShield=0;
"""
replace_once(old_hp, new_hp, 'Egypt summon full HP')

# Warrior King rebalance only. Brown Warrior values remain unchanged.
replace_once('const KING_SPECIAL_DAMAGE=62;', 'const KING_SPECIAL_DAMAGE=55;', 'King special damage')

old_king = """function spawnKing(x,y,team,color){
 const e=entityBase('king',x,y,team,color);
 if(state.mode==='war')e.speed*=WAR_TROOP_SPEED_MULTIPLIER;
 e.hp=e.maxHp=280;
 e.shield=e.maxShield=280;
 e.damage=47;
 e.r=29;
 e.kingNormalCount=0;
 state.entities.push(e);
 return e;
}
"""
new_king = old_king.replace('e.damage=47;', 'e.damage=38;')
replace_once(old_king, new_king, 'King normal damage')

path.write_text(text, encoding='utf-8')
print('Applied Egypt summons 150 HP/no shield and King 38/55 rebalance')

# Direct commit marker used only to trigger GitHub Pages after the workflow commit.
