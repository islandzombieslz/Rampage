from pathlib import Path
import re

path=Path('index.html')
text=path.read_text(encoding='utf-8')

# 1) Wallpaper de todos os menus que ainda usam o wallpaper principal antigo.
old_wall='assets/ui/background-menu.png'
new_wall='assets/ui/walpaper-menus.png'
wall_count=text.count(old_wall)
if wall_count < 5:
    raise SystemExit(f'esperava pelo menos 5 referencias ao wallpaper antigo; encontrei {wall_count}')
text=text.replace(old_wall,new_wall)

# Prefetch dos novos sprites da loja para abrir instantaneamente.
prefetch_anchor='<link rel="prefetch" as="image" href="assets/ui/mestre-da-guerra-menu.png">'
prefetch_block='''<link rel="prefetch" as="image" href="assets/ui/mestre-da-guerra-menu.png">
<link rel="prefetch" as="image" href="assets/ui/botao-loja.png">
<link rel="prefetch" as="image" href="assets/ui/war-shop/card-guerreiros.png">
<link rel="prefetch" as="image" href="assets/ui/war-shop/card-magos-guerreiros.png">
<link rel="prefetch" as="image" href="assets/ui/war-shop/card-golem-guerreiro.png">
<link rel="prefetch" as="image" href="assets/ui/war-shop/card-dragao-guerreiro.png">'''
if text.count(prefetch_anchor)!=1:
    raise SystemExit(f'ancora de prefetch inesperada: {text.count(prefetch_anchor)}')
text=text.replace(prefetch_anchor,prefetch_block,1)

# 2) Botao da loja: mesma funcao/mesmo id, apenas sprite.
old_button='<button id="shopButton">Loja</button>'
new_button='''<button id="shopButton" aria-label="Abrir ou fechar loja" title="Loja">
      <img src="assets/ui/botao-loja.png" alt="" draggable="false" decoding="async">
    </button>'''
if text.count(old_button)!=1:
    raise SystemExit(f'botao antigo da loja: {text.count(old_button)} ocorrencias')
text=text.replace(old_button,new_button,1)

# 3) Loja: remove GIFs/textos e vira uma grade 2x2 somente com os cards clicaveis.
shop_pattern=re.compile(
    r'''<div id="shop">\s*<h3 style="margin-top:0">Loja</h3>\s*<div class="shop-items">.*?<p class="small">As tropas nascem dentro do seu território e aguardam o início da guerra\.</p>\s*</div>''',
    re.S
)
match=shop_pattern.search(text)
if not match:
    raise SystemExit('bloco HTML atual da loja nao encontrado')
new_shop='''<div id="shop" aria-label="Loja de tropas">
      <div class="shop-sprite-grid">
        <button id="buyWarrior" class="shop-sprite-card" aria-label="Comprar Guerreiro por 75 gemas" title="Guerreiro — 75 gemas">
          <img src="assets/ui/war-shop/card-guerreiros.png" alt="Guerreiro" draggable="false" decoding="async">
        </button>
        <button id="buyMage" class="shop-sprite-card" aria-label="Comprar Mago por 550 gemas" title="Mago — 550 gemas">
          <img src="assets/ui/war-shop/card-magos-guerreiros.png" alt="Mago Guerreiro" draggable="false" decoding="async">
        </button>
        <button id="buyGolem" class="shop-sprite-card" aria-label="Comprar Golem por 350 gemas" title="Golem — 350 gemas">
          <img src="assets/ui/war-shop/card-golem-guerreiro.png" alt="Golem Guerreiro" draggable="false" decoding="async">
        </button>
        <button id="buyDragon" class="shop-sprite-card" aria-label="Comprar Dragão por 350 gemas" title="Dragão — 350 gemas">
          <img src="assets/ui/war-shop/card-dragao-guerreiro.png" alt="Dragão Guerreiro" draggable="false" decoding="async">
        </button>
      </div>
    </div>'''
text=text[:match.start()]+new_shop+text[match.end():]

# 4) Overrides visuais no fim do CSS para vencer regras antigas sem mexer na logica existente.
css_marker='</style>'
css='''

/* ===== LOJA MESTRE DA GUERRA — SPRITES 2x2 ===== */
#gameScreen:not(.pve-mode) #shopButton{
  display:block !important;
  position:absolute !important;
  right:calc(var(--safe-right) + 8px) !important;
  bottom:calc(var(--safe-bottom) + 8px) !important;
  width:76px !important;
  height:76px !important;
  min-width:0 !important;
  min-height:0 !important;
  max-width:none !important;
  padding:0 !important;
  margin:0 !important;
  border:0 !important;
  border-radius:0 !important;
  outline:0 !important;
  background:transparent !important;
  box-shadow:none !important;
  overflow:visible !important;
  line-height:0 !important;
  z-index:64 !important;
  pointer-events:auto !important;
}
#gameScreen:not(.pve-mode) #shopButton:hover{filter:brightness(1.06)}
#gameScreen:not(.pve-mode) #shopButton:active{transform:scale(.96)}
#shopButton img{
  display:block !important;
  width:100% !important;
  height:100% !important;
  object-fit:contain !important;
  pointer-events:none !important;
  user-select:none !important;
  -webkit-user-drag:none !important;
}

/* O overlay apenas escurece/borra o que esta atras. Nao pausa jogo, IA nem timer. */
#shop{
  display:none !important;
  position:absolute !important;
  inset:0 !important;
  width:100% !important;
  height:100% !important;
  max-height:none !important;
  padding:0 !important;
  margin:0 !important;
  border:0 !important;
  border-radius:0 !important;
  background:rgba(7,8,10,.34) !important;
  -webkit-backdrop-filter:blur(2.2px) brightness(.72) !important;
  backdrop-filter:blur(2.2px) brightness(.72) !important;
  box-shadow:none !important;
  overflow:hidden !important;
  align-items:center !important;
  justify-content:center !important;
  z-index:60 !important;
  pointer-events:auto !important;
}
#shop.open{display:flex !important}
#shop .shop-sprite-grid{
  width:min(470px,58vw,78vh) !important;
  max-width:calc(100vw - 120px) !important;
  display:grid !important;
  grid-template-columns:repeat(2,minmax(0,1fr)) !important;
  grid-template-rows:repeat(2,minmax(0,1fr)) !important;
  gap:8px !important;
  padding:7px !important;
  margin:0 !important;
  background:rgba(10,10,10,.10) !important;
  border:0 !important;
  border-radius:18px !important;
  box-shadow:0 16px 48px rgba(0,0,0,.20) !important;
}
#shop .shop-sprite-card{
  display:block !important;
  width:100% !important;
  aspect-ratio:1/1 !important;
  min-width:0 !important;
  min-height:0 !important;
  padding:0 !important;
  margin:0 !important;
  border:0 !important;
  border-radius:13px !important;
  outline:0 !important;
  background:transparent !important;
  box-shadow:none !important;
  overflow:hidden !important;
  line-height:0 !important;
  cursor:pointer !important;
}
#shop .shop-sprite-card img{
  display:block !important;
  width:100% !important;
  height:100% !important;
  object-fit:contain !important;
  pointer-events:none !important;
  user-select:none !important;
  -webkit-user-drag:none !important;
}
#shop .shop-sprite-card:not(:disabled):hover{filter:brightness(1.06)}
#shop .shop-sprite-card:not(:disabled):active{transform:scale(.975)}
#shop .shop-sprite-card:disabled{
  opacity:.42 !important;
  filter:grayscale(.20) brightness(.78) !important;
  cursor:not-allowed !important;
}
@media (pointer:coarse), (max-height:650px), (max-width:900px){
  #gameScreen:not(.pve-mode) #shopButton{
    width:62px !important;
    height:62px !important;
    right:calc(var(--safe-right) + 5px) !important;
    bottom:calc(var(--safe-bottom) + 5px) !important;
  }
  #shop .shop-sprite-grid{
    width:min(410px,52vw,78vh) !important;
    max-width:calc(100vw - 92px) !important;
    gap:6px !important;
    padding:5px !important;
  }
}
@media (max-width:620px) and (orientation:portrait){
  #shop .shop-sprite-grid{
    width:min(88vw,440px) !important;
    max-width:88vw !important;
  }
}
'''
if text.count(css_marker)!=1:
    raise SystemExit(f'esperava 1 </style>, encontrei {text.count(css_marker)}')
text=text.replace(css_marker,css+css_marker,1)

# 5) Mantem o mesmo toggle e adiciona fechamento ao clicar no fundo do overlay.
old_toggle="$('#shopButton').onclick=()=>$('#shop').classList.toggle('open');"
new_toggle="""$('#shopButton').onclick=()=>$('#shop').classList.toggle('open');
$('#shop').onclick=(ev)=>{if(ev.target===$('#shop'))$('#shop').classList.remove('open')};"""
if text.count(old_toggle)!=1:
    raise SystemExit(f'toggle da loja: {text.count(old_toggle)} ocorrencias')
text=text.replace(old_toggle,new_toggle,1)

# Garantias finais.
required=[
  'assets/ui/walpaper-menus.png',
  'assets/ui/botao-loja.png',
  'assets/ui/war-shop/card-guerreiros.png',
  'assets/ui/war-shop/card-magos-guerreiros.png',
  'assets/ui/war-shop/card-golem-guerreiro.png',
  'assets/ui/war-shop/card-dragao-guerreiro.png',
  'class="shop-sprite-grid"',
  'backdrop-filter:blur(2.2px) brightness(.72)',
]
for marker in required:
    if marker not in text:
        raise SystemExit('marcador final ausente: '+marker)
if old_wall in text:
    raise SystemExit('wallpaper antigo ainda referenciado no HTML')
if 'i.postimg.cc' in text:
    raise SystemExit('URL Postimg nao deve ficar no runtime')

path.write_text(text,encoding='utf-8')
