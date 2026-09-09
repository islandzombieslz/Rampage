from pathlib import Path

path = Path('index.html')
text = path.read_text(encoding='utf-8')

# =========================================================
# BARRAS: MAIS COMPACTAS E UM POUCO MAIS BAIXAS
# =========================================================
old_base_bars = ".entity-bars{\n  position:absolute;left:11px;top:-7px;width:56px;height:12px;\n}"
new_base_bars = ".entity-bars{\n  position:absolute;left:15px;top:-3px;width:48px;height:12px;\n}"
if new_base_bars not in text:
    if old_base_bars not in text:
        raise SystemExit('Barras base atuais não encontradas')
    text = text.replace(old_base_bars, new_base_bars, 1)

old_base_bg = ".hp-bg,.shield-bg{position:absolute;left:0;width:56px;background:#000b;overflow:hidden}"
new_base_bg = ".hp-bg,.shield-bg{position:absolute;left:0;width:48px;background:#000b;overflow:hidden}"
if new_base_bg not in text:
    if old_base_bg not in text:
        raise SystemExit('Fundos atuais de HP/escudo não encontrados')
    text = text.replace(old_base_bg, new_base_bg, 1)

old_king_bars = ".entity-visual.king-visual .entity-bars{left:31px;top:-8px;width:76px}\n.entity-visual.king-visual .hp-bg,\n.entity-visual.king-visual .shield-bg{width:76px}"
new_king_bars = ".entity-visual.king-visual .entity-bars{left:36px;top:-4px;width:66px}\n.entity-visual.king-visual .hp-bg,\n.entity-visual.king-visual .shield-bg{width:66px}"
if new_king_bars not in text:
    if old_king_bars not in text:
        raise SystemExit('Barras atuais do Rei não encontradas')
    text = text.replace(old_king_bars, new_king_bars, 1)

# =========================================================
# REI: +80 HP, +80 ESCUDO, 35 DANO, +100 CUSTO
# =========================================================
old_cost = "const WAR_UNIT_COSTS=Object.freeze({warrior:50,king:300,golem:550,mage:550,dragon:450});"
new_cost = "const WAR_UNIT_COSTS=Object.freeze({warrior:50,king:400,golem:550,mage:550,dragon:450});"
if new_cost not in text:
    if old_cost not in text:
        raise SystemExit('Custo atual do Rei não encontrado')
    text = text.replace(old_cost, new_cost, 1)

text = text.replace('aria-label="Comprar Rei Guerreiro por 300 gemas"', 'aria-label="Comprar Rei Guerreiro por 400 gemas"', 1)
text = text.replace('title="Rei Guerreiro — 300 gemas"', 'title="Rei Guerreiro — 400 gemas"', 1)

old_king_stats = """function spawnKing(x,y,team,color){
 const e=entityBase('king',x,y,team,color);
 if(state.mode==='war')e.speed*=WAR_TROOP_SPEED_MULTIPLIER;
 e.hp=e.maxHp=200;
 e.shield=e.maxShield=200;
 e.damage=25;"""
new_king_stats = """function spawnKing(x,y,team,color){
 const e=entityBase('king',x,y,team,color);
 if(state.mode==='war')e.speed*=WAR_TROOP_SPEED_MULTIPLIER;
 e.hp=e.maxHp=280;
 e.shield=e.maxShield=280;
 e.damage=35;"""
if new_king_stats not in text:
    if old_king_stats not in text:
        raise SystemExit('Atributos atuais do Rei não encontrados')
    text = text.replace(old_king_stats, new_king_stats, 1)

# =========================================================
# GUERREIRO: +50 HP E +50 ESCUDO
# =========================================================
old_warrior = """function spawnWarrior(x,y,team,color,controlled=false,variant='male',ownerId=null){
 const e=entityBase('warrior',x,y,team,color);
 if(state.mode==='war')e.speed*=WAR_TROOP_SPEED_MULTIPLIER;
 e.controlled=controlled;"""
new_warrior = """function spawnWarrior(x,y,team,color,controlled=false,variant='male',ownerId=null){
 const e=entityBase('warrior',x,y,team,color);
 if(state.mode==='war')e.speed*=WAR_TROOP_SPEED_MULTIPLIER;
 e.hp=e.maxHp=150;
 e.shield=e.maxShield=100;
 e.controlled=controlled;"""
if new_warrior not in text:
    if old_warrior not in text:
        raise SystemExit('Spawn atual do Guerreiro não encontrado')
    text = text.replace(old_warrior, new_warrior, 1)

marker = '/* UNIT STATS/BARS TUNING 2026-09-09 */'
if marker not in text:
    anchor = new_cost
    if anchor not in text:
        raise SystemExit('Âncora para marcador não encontrada')
    text = text.replace(anchor, marker + "\n" + anchor, 1)

required = [
    marker,
    'position:absolute;left:15px;top:-3px;width:48px;height:12px;',
    '.hp-bg,.shield-bg{position:absolute;left:0;width:48px',
    '.entity-visual.king-visual .entity-bars{left:36px;top:-4px;width:66px}',
    '.entity-visual.king-visual .shield-bg{width:66px}',
    new_cost,
    'aria-label="Comprar Rei Guerreiro por 400 gemas"',
    'title="Rei Guerreiro — 400 gemas"',
    'e.hp=e.maxHp=280;',
    'e.shield=e.maxShield=280;',
    'e.damage=35;',
    'e.hp=e.maxHp=150;',
    'e.shield=e.maxShield=100;',
]
missing = [m for m in required if m not in text]
if missing:
    raise SystemExit('Validação final falhou: ' + repr(missing))

forbidden = [
    'position:absolute;left:11px;top:-7px;width:56px;height:12px;',
    '.hp-bg,.shield-bg{position:absolute;left:0;width:56px',
    '.entity-visual.king-visual .entity-bars{left:31px;top:-8px;width:76px}',
    'const WAR_UNIT_COSTS=Object.freeze({warrior:50,king:300,golem:550,mage:550,dragon:450});',
    'aria-label="Comprar Rei Guerreiro por 300 gemas"',
    'title="Rei Guerreiro — 300 gemas"',
]
present = [m for m in forbidden if m in text]
if present:
    raise SystemExit('Configuração anterior ainda presente: ' + repr(present))

path.write_text(text, encoding='utf-8')
print('Barras menores/mais baixas; Rei 280/280, dano 35, custo 400; Guerreiro 150/100.')
