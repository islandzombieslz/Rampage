from pathlib import Path
import re

path = Path('index.html')
text = path.read_text(encoding='utf-8')

# =========================================================
# ROOM CODES: APENAS REI / PLEBEU / CONDE
# =========================================================
room_codes = "const ROOM_CODES=['REI','PLEBEU','CONDE'];"
if room_codes not in text:
    pattern = r"const ROOM_COLOR_NAMES=\[.*?\];\nfunction normalizeRoomCode"
    replacement = room_codes + "\nfunction normalizeRoomCode"
    text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit('Não foi possível substituir a lista antiga de códigos por cores')

old_generate = """function generateCode(){
 const n=ROOM_COLOR_NAMES.length;
 const ai=Math.floor(Math.random()*n);
 let bi=Math.floor(Math.random()*(n-1));
 if(bi>=ai)bi++;
 return ROOM_COLOR_NAMES[ai]+'-'+ROOM_COLOR_NAMES[bi];
}"""
new_generate = """function generateCode(){
 return ROOM_CODES[Math.floor(Math.random()*ROOM_CODES.length)];
}"""
if new_generate not in text:
    if old_generate not in text:
        raise SystemExit('Função antiga de geração de código não encontrada')
    text = text.replace(old_generate, new_generate, 1)

# =========================================================
# GEMAS: 3000 É SÓ O TETO DA CONFIGURAÇÃO INICIAL
# =========================================================
old_round_gems = "p.gems=clamp(state.gems+(p.bonusGems||0),0,3000);"
new_round_gems = "p.gems=Math.max(0,state.gems+(p.bonusGems||0));"
if new_round_gems not in text:
    if old_round_gems not in text:
        raise SystemExit('Clamp de gemas por rodada não encontrado')
    text = text.replace(old_round_gems, new_round_gems, 1)

# O configurador deve continuar limitado a 3000.
config_gem_cap = "if(b.dataset.target==='gems') state.gems=clamp(state.gems+dir*100,300,3000);"
if config_gem_cap not in text:
    raise SystemExit('Teto de 3000 da configuração inicial foi alterado inesperadamente')

# =========================================================
# BARRAS DE VIDA/ESCUDO UM POUCO MENORES E CENTRALIZADAS
# =========================================================
old_king = ".entity-visual.king-visual .entity-bars{left:26px;top:-8px;width:86px}\n.entity-visual.king-visual .hp-bg,\n.entity-visual.king-visual .shield-bg{width:86px}"
new_king = ".entity-visual.king-visual .entity-bars{left:31px;top:-8px;width:76px}\n.entity-visual.king-visual .hp-bg,\n.entity-visual.king-visual .shield-bg{width:76px}"
if new_king not in text:
    if old_king not in text:
        raise SystemExit('Barras do Rei não encontradas')
    text = text.replace(old_king, new_king, 1)

old_bars = ".entity-bars{\n  position:absolute;left:7px;top:-7px;width:64px;height:12px;\n}"
new_bars = ".entity-bars{\n  position:absolute;left:11px;top:-7px;width:56px;height:12px;\n}"
if new_bars not in text:
    if old_bars not in text:
        raise SystemExit('Barra base das entidades não encontrada')
    text = text.replace(old_bars, new_bars, 1)

old_bg = ".hp-bg,.shield-bg{position:absolute;left:0;width:64px;background:#000b;overflow:hidden}"
new_bg = ".hp-bg,.shield-bg{position:absolute;left:0;width:56px;background:#000b;overflow:hidden}"
if new_bg not in text:
    if old_bg not in text:
        raise SystemExit('Largura base de HP/escudo não encontrada')
    text = text.replace(old_bg, new_bg, 1)

marker = '/* ROOM/GEMS/BARS TUNING 2026-09-09 */'
if marker not in text:
    anchor = room_codes
    text = text.replace(anchor, marker + "\n" + anchor, 1)

required = [
    marker,
    room_codes,
    'return ROOM_CODES[Math.floor(Math.random()*ROOM_CODES.length)];',
    config_gem_cap,
    new_round_gems,
    'position:absolute;left:11px;top:-7px;width:56px;height:12px;',
    '.hp-bg,.shield-bg{position:absolute;left:0;width:56px',
    '.entity-visual.king-visual .entity-bars{left:31px;top:-8px;width:76px}',
    '.entity-visual.king-visual .shield-bg{width:76px}',
]
missing = [m for m in required if m not in text]
if missing:
    raise SystemExit('Validação final falhou: ' + repr(missing))

forbidden = [
    'const ROOM_COLOR_NAMES=[',
    "return ROOM_COLOR_NAMES[ai]+'-'+ROOM_COLOR_NAMES[bi];",
    'p.gems=clamp(state.gems+(p.bonusGems||0),0,3000);',
]
present = [m for m in forbidden if m in text]
if present:
    raise SystemExit('Comportamento antigo ainda presente: ' + repr(present))

path.write_text(text, encoding='utf-8')
print('Códigos REI/PLEBEU/CONDE aplicados; teto de 3000 restrito à configuração; barras reduzidas.')
