from pathlib import Path

INDEX = Path('index.html')
text = INDEX.read_text(encoding='utf-8')
MARK = '/* EGYPT SHOP + VISUAL TUNING 2026-09-13 */'

# The shop's existing #shop .shop-sprite-grid { display:grid !important }
# can override a normal inline display:none. Force the clan-specific display
# with inline !important, while preserving hidden/aria-hidden as semantic state.
old = "group.style.display=visible?'grid':'none';"
new = "group.style.setProperty('display',visible?'grid':'none','important');"
if old in text:
    text = text.replace(old, new, 1)
elif new not in text:
    raise SystemExit('Clan shop display line not found')

css = r'''

/* EGYPT SHOP + VISUAL TUNING 2026-09-13 */
/* A regra original #shop .shop-sprite-grid usa !important; esta regra
   mais específica garante que o grupo do outro clã desapareça visualmente. */
#shop .clan-shop[hidden],
#shop .clan-shop[aria-hidden="true"]{
  display:none !important;
}

/* Egito: apenas escala visual. Hitbox, alcance, velocidade e atributos não mudam. */
.entity-visual.egypt-unit:not(.mage-visual) .entity-body{
  width:96px;
  height:113px;
  left:-9px;
  top:-10px;
}
/* A espada egípcia estava grande em relação ao corpo. Mantém o pivô perto
   do mesmo ponto visual, mas reduz o sprite. */
.entity-visual.egypt-unit:not(.mage-visual) .entity-sword{
  width:22px;
  height:64px;
  left:28px;
  top:8px;
}

/* Mago/Maga do Egito maiores sem alterar a caixa física da entidade. */
.entity-visual.mage-visual.egypt-unit .entity-body{
  width:108px;
  height:128px;
  left:-10px;
  top:-12px;
}
.entity-visual.mage-visual.egypt-unit .entity-mage-special{
  width:128px !important;
  height:151px !important;
  left:-20px !important;
  top:-24px !important;
}
/* Cajado egípcio menor; animações/rotação continuam usando a mesma lógica. */
.entity-visual.mage-visual.egypt-unit .mage-staff{
  width:68px;
  height:80px;
  left:32px;
  top:4px;
}
'''

if MARK not in text:
    anchor = '\n</style>'
    if anchor not in text:
        raise SystemExit('Style close not found')
    text = text.replace(anchor, css + anchor, 1)

# Validation: both shops remain separate and current Egypt shop contains only 2 cards.
required = [
    'data-clan-shop="warriors"',
    'data-clan-shop="egypt"',
    'id="buyEgyptWarrior"',
    'id="buyEgyptMage"',
    "group.style.setProperty('display',visible?'grid':'none','important');",
    MARK,
]
missing = [x for x in required if x not in text]
if missing:
    raise SystemExit('Missing required markers: ' + repr(missing))

# Guard against accidentally restoring the cancelled static-GIF LOD system.
if 'WAR ADAPTIVE VISUAL LOD 2026-09-12' in text:
    raise SystemExit('Cancelled static GIF LOD unexpectedly present')

INDEX.write_text(text, encoding='utf-8')
print('Egypt clan shop visibility and visual sizes patched')
