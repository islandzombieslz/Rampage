from pathlib import Path

path = Path('index.html')
text = path.read_text(encoding='utf-8')


def replace_once(old, new, label):
    global text
    if old in text:
        text = text.replace(old, new, 1)
        return
    if new in text:
        return
    raise SystemExit(f'Trecho não encontrado: {label}')


# ===== REI GUERREIRO: AJUSTE VISUAL NO CAMINHO REAL DE RENDER =====
# O ajuste anterior aumentou apenas as caixas CSS. O render também aplica um
# typeScale a cada frame; agora o Rei recebe escala própria ali, como Golem/Mago/Dragão.
old_css = """/* Rei Guerreiro: maior que o Guerreiro comum, mantendo a mesma lógica de combate. */
.entity-visual.king-visual{width:112px;height:138px}
.entity-visual.king-visual .entity-facing,
.entity-visual.king-visual .entity-weapon-facing{width:112px;height:132px}
.entity-visual.king-visual .entity-body{left:0;top:-4px;width:112px;height:132px}
.entity-visual.king-visual .entity-bars{left:17px;top:-7px;width:78px}
.entity-visual.king-visual .hp-bg,
.entity-visual.king-visual .shield-bg{width:78px}
/* A mão/espada do Rei fica mais baixa que antes. */
.entity-visual.king-visual .entity-sword{left:41px;top:4px;width:30px;height:88px}
/* O corpo do especial é propositalmente maior que idle/walk. */
.entity-visual.king-visual .entity-king-special{
  width:156px !important;height:184px !important;
  left:-22px !important;top:-32px !important;object-fit:contain !important;
}"""
new_css = """/* Rei Guerreiro: tamanho visual reforçado; colisão/atributos não mudam. */
.entity-visual.king-visual{width:138px;height:168px}
.entity-visual.king-visual .entity-facing,
.entity-visual.king-visual .entity-weapon-facing{width:138px;height:160px}
.entity-visual.king-visual .entity-body{left:0;top:-8px;width:138px;height:160px}
.entity-visual.king-visual .entity-bars{left:26px;top:-8px;width:86px}
.entity-visual.king-visual .hp-bg,
.entity-visual.king-visual .shield-bg{width:86px}
/* A mão/espada do Rei fica claramente mais baixa e proporcional ao corpo maior. */
.entity-visual.king-visual .entity-sword{left:51px;top:20px;width:34px;height:98px}
/* O GIF do corpo no especial é bem maior que idle/walk. */
.entity-visual.king-visual .entity-king-special{
  width:205px !important;height:238px !important;
  left:-34px !important;top:-50px !important;object-fit:contain !important;
}"""
replace_once(old_css, new_css, 'CSS final do Rei Guerreiro')

replace_once(
    "const typeScale=e.type==='golem'?1.34:e.type==='mage'?1.08:e.type==='dragon'?1.16:1;",
    "const typeScale=e.type==='golem'?1.34:e.type==='mage'?1.08:e.type==='dragon'?1.16:e.type==='king'?1.18:1;",
    'escala efetiva do Rei no render',
)

# ===== POWER.GIF DO ESPECIAL: EFEITO DE CHÃO, NÃO FILHO DO REI =====
# A implementação correta já existe no HTML atual: startKingSpecial grava originX/originY,
# syncKingPowerEffects cria um IMG independente no entityLayer e calcula sua posição
# sempre a partir dessa origem fixa + câmera. Aqui validamos isso explicitamente para
# impedir regressão para o comportamento de seguir o personagem.
required_ground_fx = [
    "originX:e.x,originY:e.y",
    "function syncKingPowerEffects(left,top,zoom,screenW,screenH){",
    "const ox=Number.isFinite(Number(p.originX))?Number(p.originX):e.x;",
    "const oy=Number.isFinite(Number(p.originY))?Number(p.originY):e.y;",
    "const sx=(ox-left)*zoom,sy=(oy-top)*zoom;",
    "const kingPowerNodes=new Map();",
    "syncKingPowerEffects(left,top,zoom,vw,vh);",
]
for item in required_ground_fx:
    if item not in text:
        raise SystemExit('Efeito de chão do Rei incompleto: ' + item)

king_template_start = text.find("}else if(e.type==='king'){")
king_template_end = text.find("}else if(e.type==='dragon'){", king_template_start)
if king_template_start < 0 or king_template_end < 0:
    raise SystemExit('Template do Rei não encontrado')
king_template = text[king_template_start:king_template_end]
if '<img class="king-special-power"' in king_template:
    raise SystemExit('power.gif voltou a ser filho do Rei; deveria ficar preso ao chão')


# ===== VALIDAÇÕES DE INTEGRIDADE =====
required = [
    'FIREBASE RTDB, HOST AUTORITATIVO',
    'WAR PERFORMANCE 2026-09-08',
    'REMOTE WAR ROUND TRANSITION SYNC',
    "e.hp=e.maxHp=200;",
    "e.shield=e.maxShield=200;",
    "e.damage=25;",
    "kingNormalCount)||0)>=6",
    '.entity-visual.king-visual{width:138px;height:168px}',
    '.entity-visual.king-visual .entity-sword{left:51px;top:20px;width:34px;height:98px}',
    'width:205px !important;height:238px !important;',
    "e.type==='king'?1.18:1;",
]
missing = [item for item in required if item not in text]
if missing:
    raise SystemExit('Validação falhou: ' + ' | '.join(missing))

if 'i.postimg.cc' in text:
    raise SystemExit('Referência ao Postimg reapareceu')

path.write_text(text, encoding='utf-8')
print('Rei Guerreiro corrigido no CSS e na escala efetiva do render; efeito do especial validado como fixo no chão.')
