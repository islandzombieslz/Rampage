from pathlib import Path
import re

INDEX = Path('index.html')
GENERATOR = Path('.github/update_asset_cache.py')
CACHE_WORKFLOW = Path('.github/workflows/asset-cache.yml')

text = INDEX.read_text(encoding='utf-8')

replacements = {
    'https://i.postimg.cc/Bbn4PbZ7/card-selecao-de-escolha.png': 'assets/egypt/ui/clan-card.png',
    'https://i.postimg.cc/N0sJcHdp/guerreiro-egitado-parado.gif': 'assets/egypt/warrior/male-idle.gif',
    'https://i.postimg.cc/FKrW4LTM/guerreiro-egito-andando.gif': 'assets/egypt/warrior/male-walk.gif',
    'https://i.postimg.cc/R0SsBHgG/guerreira-egito-parada.gif': 'assets/egypt/warrior/female-idle.gif',
    'https://i.postimg.cc/tgqSjxBr/guerreira-egito-andando.gif': 'assets/egypt/warrior/female-walk.gif',
    'https://i.postimg.cc/7LHsk2KN/espada-guerreiro-egpcios.png': 'assets/egypt/warrior/sword.png',
    'https://i.postimg.cc/fbz2N98d/card-guerreiros-egito.png': 'assets/egypt/warrior/card.png',
    'https://i.postimg.cc/SKgZNx5J/card-magos-egito.png': 'assets/egypt/mage/card.png',
    'https://i.postimg.cc/9XnvYJLX/mao-atras-mago-egito.gif': 'assets/egypt/mage/staff.gif',
    'https://i.postimg.cc/HxKBXPTC/mao-magos-egpcios.png': 'assets/egypt/mage/hand.png',
    'https://i.postimg.cc/hj4HpYkN/poder-normal-mago-egito.gif': 'assets/egypt/mage/power-normal.gif',
    'https://i.postimg.cc/KcHdDJJq/poder-especial-mago-egito.gif': 'assets/egypt/mage/power-special.gif',
    'https://i.postimg.cc/PJwK4z5c/mago-egito-parado.gif': 'assets/egypt/mage/male-idle.gif',
    'https://i.postimg.cc/gJ5N8Bm7/mago-egito-andando.gif': 'assets/egypt/mage/male-walk.gif',
    'https://i.postimg.cc/SRMVr7x3/mago-egito-especial.gif': 'assets/egypt/mage/male-special.gif',
    'https://i.postimg.cc/vBj3fSbL/maga-egito-parada.gif': 'assets/egypt/mage/female-idle.gif',
    'https://i.postimg.cc/76cm0QwB/maga-egito-andando.gif': 'assets/egypt/mage/female-walk.gif',
    'https://i.postimg.cc/Ss5DCtk5/maga-egito-especial.gif': 'assets/egypt/mage/female-special.gif',
    'https://i.postimg.cc/6qYQzvPc/bff3bb67-8426-4656-bdee-1313473758e2.png': 'assets/arena/floor.png',
    'https://i.postimg.cc/fywLxK8B/1919c5cb-ace6-4da5-b8f0-6db8bfb24c89.png': 'assets/arena/barrier.png',
}

for old, new in replacements.items():
    if old in text:
        text = text.replace(old, new)
    elif new not in text:
        raise SystemExit(f'Missing asset reference: {old}')

# Runtime must no longer depend on Postimg.
if 'i.postimg.cc' in text:
    refs = sorted(set(re.findall(r'https://i\.postimg\.cc/[^\'"<>\s]+', text)))
    raise SystemExit('Postimg references still present in index.html: ' + repr(refs))

# Always apply the clan filter immediately before the shop opens.
old_button = "$('#shopButton').onclick=()=>$('#shop').classList.toggle('open');"
new_button = "$('#shopButton').onclick=()=>{configureWarShopForClan();$('#shop').classList.toggle('open')};"
if old_button in text:
    text = text.replace(old_button, new_button, 1)
elif new_button not in text:
    raise SystemExit('Shop button anchor missing')

old_filter = """function configureWarShopForClan(){
 const clan=normalizeClan(localPlayer()?.clan);
 $$('.clan-shop').forEach(group=>group.hidden=normalizeClan(group.dataset.clanShop)!==clan);
}"""
new_filter = """function configureWarShopForClan(){
 const clan=normalizeClan(localPlayer()?.clan);
 $$('.clan-shop').forEach(group=>{
   const visible=normalizeClan(group.dataset.clanShop)===clan;
   group.hidden=!visible;
   group.style.display=visible?'grid':'none';
   group.setAttribute('aria-hidden',visible?'false':'true');
 });
}"""
if old_filter in text:
    text = text.replace(old_filter, new_filter, 1)
elif new_filter not in text:
    raise SystemExit('Clan shop filter anchor missing')

# Selecting a clan updates the hidden/visible shop groups immediately too.
old_select = """ p.clan=clan;
 renderClanSelection();
 if(NetworkAdapter.online){"""
new_select = """ p.clan=clan;
 renderClanSelection();
 configureWarShopForClan();
 if(NetworkAdapter.online){"""
if old_select in text:
    text = text.replace(old_select, new_select, 1)
elif new_select not in text:
    raise SystemExit('Clan selection anchor missing')

INDEX.write_text(text, encoding='utf-8')

# Same-origin GitHub Pages can sustain a few more parallel cache transfers safely.
# This only affects the loading screen; assets are still fully downloaded before entry.
g = GENERATOR.read_text(encoding='utf-8')
g = g.replace("const BOOT_FETCH_CONCURRENCY=8;", "const BOOT_FETCH_CONCURRENCY=10;")
GENERATOR.write_text(g, encoding='utf-8')

# Keep the persistent-cache workflow validation aligned with the generator.
w = CACHE_WORKFLOW.read_text(encoding='utf-8')
w = w.replace("'const BOOT_FETCH_CONCURRENCY=8;'", "'const BOOT_FETCH_CONCURRENCY=10;'")
CACHE_WORKFLOW.write_text(w, encoding='utf-8')

print('Loading/Postimg/shop patch applied successfully')
