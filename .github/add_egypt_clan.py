from pathlib import Path
import re

path = Path('index.html')
text = path.read_text(encoding='utf-8')
MARK = '/* EGYPT CLAN SYSTEM 2026-09-13 */'
if MARK in text:
    print('Egypt clan already applied')
    raise SystemExit(0)

def replace_once(old, new, label):
    global text
    if old not in text:
        raise SystemExit(f'Missing anchor: {label}')
    text = text.replace(old, new, 1)

def sub_once(pattern, repl, label, flags=0):
    global text
    text2, n = re.subn(pattern, repl, text, count=1, flags=flags)
    if n != 1:
        raise SystemExit(f'Expected 1 replacement for {label}, got {n}')
    text = text2

# ---------- CSS: two selectable clans, separate shops, summon fade ----------
css = r'''

/* EGYPT CLAN SYSTEM 2026-09-13 */
#clanScreen>.card > .clan-options-grid{
  position:absolute !important;
  left:20% !important;
  right:20% !important;
  top:40.5% !important;
  bottom:23.5% !important;
  display:grid !important;
  grid-template-columns:repeat(2,minmax(0,1fr)) !important;
  gap:9px !important;
  align-items:stretch !important;
  min-width:0 !important;
}
#clanScreen .clan-options-grid .clan-option{
  position:relative !important;
  inset:auto !important;
  width:auto !important;
  min-width:0 !important;
  height:100% !important;
  display:flex !important;
  flex-direction:column !important;
  justify-content:center !important;
  align-items:center !important;
  gap:4px !important;
  padding:5px !important;
  text-align:center !important;
  cursor:pointer !important;
  overflow:hidden !important;
}
#clanScreen .clan-options-grid .clan-option img{
  width:min(92px,80%) !important;
  height:min(92px,58%) !important;
  max-width:none !important;
  max-height:none !important;
  object-fit:contain !important;
  flex:0 1 auto !important;
}
#clanScreen .clan-options-grid .clan-option h3{
  margin:1px 0 2px !important;
  font-size:13px !important;
}
#clanScreen .clan-options-grid .clan-option .small{
  font-size:7.7px !important;
  line-height:1.12 !important;
}
#clanScreen .clan-option[data-clan="egypt"].selected{
  border-color:rgba(227,179,65,.82) !important;
  box-shadow:inset 0 0 16px rgba(227,179,65,.14) !important;
}
#clanScreen #clanSelectionStatus{
  position:absolute !important;
  left:22% !important;
  right:22% !important;
  bottom:20.1% !important;
  text-align:center !important;
  font-size:8.5px !important;
  color:#f2f4f7 !important;
  text-shadow:0 1px 3px #000 !important;
}
.clan-shop[hidden]{display:none !important}
.entity-visual.egypt-summoned-spawn{animation:egyptSummonFade .58s ease-out both}
@keyframes egyptSummonFade{from{opacity:0}to{opacity:1}}
@media (max-height:650px) and (pointer:fine){
  #clanScreen>.card > .clan-options-grid{left:19% !important;right:19% !important;top:40% !important;bottom:23% !important;gap:7px !important}
  #clanScreen .clan-options-grid .clan-option img{width:min(76px,78%) !important;height:min(76px,55%) !important}
  #clanScreen .clan-options-grid .clan-option h3{font-size:11px !important}
  #clanScreen .clan-options-grid .clan-option .small{font-size:6.7px !important}
  #clanScreen #clanSelectionStatus{bottom:19.5% !important;font-size:7.5px !important}
}
'''
replace_once('\n</style>', css + '\n</style>', 'style close')

# ---------- Clan selection HTML ----------
clan_html = '''<section id="clanScreen" class="screen">
  <div class="card">
    <h2>Escolha seu clã</h2>
    <p class="sub">Cada jogador escolhe seu próprio clã. As lojas e tropas permanecem separadas.</p>
    <div class="clan-options-grid">
      <button class="clan-option selected" data-clan="warriors" type="button" aria-label="Escolher clã Guerreiros">
        <img src="assets/ui/cla-guerreiros.png" alt="Clã Guerreiros" loading="lazy" decoding="async">
        <div>
          <h3>Guerreiros</h3>
          <div class="small">Guerreiros • Guerreira Marrom • Rei • Magos • Golem • Dragão</div>
        </div>
      </button>
      <button class="clan-option" data-clan="egypt" type="button" aria-label="Escolher clã Egito">
        <img src="https://i.postimg.cc/Bbn4PbZ7/card-selecao-de-escolha.png" alt="Clã Egito" loading="lazy" decoding="async">
        <div>
          <h3>Egito</h3>
          <div class="small">Guerreiro/Guerreira do Egito • Mago/Maga do Egito</div>
        </div>
      </button>
    </div>
    <div id="clanSelectionStatus">Seu clã: Guerreiros</div>
    <div class="divider"></div>
    <button id="startWarBtn" class="primary">Iniciar preparação</button>
  </div>
</section>'''
sub_once(r'<section id="clanScreen" class="screen">.*?</section>', clan_html, 'clan screen', re.S)

# ---------- Shop HTML: completely separate grids ----------
old_shop = '''    <div id="shop" aria-label="Loja de tropas">
      <div class="shop-sprite-grid">
        <button id="buyWarrior" class="shop-sprite-card" aria-label="Comprar Guerreiro por 50 gemas" title="Guerreiro — 50 gemas">
          <img src="assets/ui/war-shop/card-guerreiros.png" alt="Guerreiro" draggable="false" decoding="async">
        </button>
        <button id="buyBrownWarrior" class="shop-sprite-card" aria-label="Comprar Guerreira Marrom por 450 gemas" title="Guerreira Marrom — 450 gemas">
          <img src="assets/ui/war-shop/card-guerreira-marrom.png" alt="Guerreira Marrom" draggable="false" decoding="async">
        </button>
        <button id="buyKing" class="shop-sprite-card" aria-label="Comprar Rei Guerreiro por 400 gemas" title="Rei Guerreiro — 400 gemas">
          <img src="assets/king/card.png" alt="Rei Guerreiro" draggable="false" decoding="async">
        </button>
        <button id="buyMage" class="shop-sprite-card" aria-label="Comprar Mago por 550 gemas" title="Mago — 550 gemas">
          <img src="assets/ui/war-shop/card-magos-guerreiros.png" alt="Mago Guerreiro" draggable="false" decoding="async">
        </button>
        <button id="buyGolem" class="shop-sprite-card" aria-label="Comprar Golem por 550 gemas" title="Golem — 550 gemas">
          <img src="assets/ui/war-shop/card-golem-guerreiro.png" alt="Golem Guerreiro" draggable="false" decoding="async">
        </button>
        <button id="buyDragon" class="shop-sprite-card" aria-label="Comprar Dragão por 450 gemas" title="Dragão — 450 gemas">
          <img src="assets/ui/war-shop/card-dragao-guerreiro.png" alt="Dragão Guerreiro" draggable="false" decoding="async">
        </button>
      </div>
    </div>'''
new_shop = '''    <div id="shop" aria-label="Loja de tropas">
      <div class="shop-sprite-grid clan-shop" data-clan-shop="warriors">
        <button id="buyWarrior" class="shop-sprite-card" aria-label="Comprar Guerreiro por 50 gemas" title="Guerreiro — 50 gemas">
          <img src="assets/ui/war-shop/card-guerreiros.png" alt="Guerreiro" draggable="false" decoding="async">
        </button>
        <button id="buyBrownWarrior" class="shop-sprite-card" aria-label="Comprar Guerreira Marrom por 450 gemas" title="Guerreira Marrom — 450 gemas">
          <img src="assets/ui/war-shop/card-guerreira-marrom.png" alt="Guerreira Marrom" draggable="false" decoding="async">
        </button>
        <button id="buyKing" class="shop-sprite-card" aria-label="Comprar Rei Guerreiro por 400 gemas" title="Rei Guerreiro — 400 gemas">
          <img src="assets/king/card.png" alt="Rei Guerreiro" draggable="false" decoding="async">
        </button>
        <button id="buyMage" class="shop-sprite-card" aria-label="Comprar Mago por 550 gemas" title="Mago — 550 gemas">
          <img src="assets/ui/war-shop/card-magos-guerreiros.png" alt="Mago Guerreiro" draggable="false" decoding="async">
        </button>
        <button id="buyGolem" class="shop-sprite-card" aria-label="Comprar Golem por 550 gemas" title="Golem — 550 gemas">
          <img src="assets/ui/war-shop/card-golem-guerreiro.png" alt="Golem Guerreiro" draggable="false" decoding="async">
        </button>
        <button id="buyDragon" class="shop-sprite-card" aria-label="Comprar Dragão por 450 gemas" title="Dragão — 450 gemas">
          <img src="assets/ui/war-shop/card-dragao-guerreiro.png" alt="Dragão Guerreiro" draggable="false" decoding="async">
        </button>
      </div>
      <div class="shop-sprite-grid clan-shop" data-clan-shop="egypt" hidden>
        <button id="buyEgyptWarrior" class="shop-sprite-card" aria-label="Comprar Guerreiro do Egito por 50 gemas" title="Guerreiro do Egito — 50 gemas">
          <img src="https://i.postimg.cc/fbz2N98d/card-guerreiros-egito.png" alt="Guerreiros do Egito" draggable="false" decoding="async">
        </button>
        <button id="buyEgyptMage" class="shop-sprite-card" aria-label="Comprar Mago do Egito por 550 gemas" title="Mago do Egito — 550 gemas">
          <img src="https://i.postimg.cc/SKgZNx5J/card-magos-egito.png" alt="Magos do Egito" draggable="false" decoding="async">
        </button>
      </div>
    </div>'''
replace_once(old_shop, new_shop, 'shop html')

# ---------- Firebase room player clan ----------
replace_once("players:{[user.uid]:{uid:user.uid,name:getCurrentNick(),human:true,slot:0,color:COLORS[0],joinedAt:F.serverTimestamp(),lastSeen:F.serverTimestamp()}}",
             "players:{[user.uid]:{uid:user.uid,name:getCurrentNick(),human:true,slot:0,color:COLORS[0],clan:'warriors',joinedAt:F.serverTimestamp(),lastSeen:F.serverTimestamp()}}",
             'create room clan')
replace_once("{uid:user.uid,name:getCurrentNick(),human:true,slot,color:COLORS[slot%COLORS.length],joinedAt:F.serverTimestamp(),lastSeen:F.serverTimestamp()}",
             "{uid:user.uid,name:getCurrentNick(),human:true,slot,color:COLORS[slot%COLORS.length],clan:'warriors',joinedAt:F.serverTimestamp(),lastSeen:F.serverTimestamp()}",
             'join room clan')
replace_once("  async pushLobbyState(patch){if(!this.roomId)return;const F=await this.waitFirebase();await F.update(F.ref(F.firebaseDb,`rooms/${this.roomId}`),patch)},\n  async sendInput(input)",
             "  async pushLobbyState(patch){if(!this.roomId)return;const F=await this.waitFirebase();await F.update(F.ref(F.firebaseDb,`rooms/${this.roomId}`),patch)},\n  async setClan(clan){if(!this.roomId||!this.localPlayerId)return;const F=await this.waitFirebase(),value=normalizeClan(clan);await F.update(F.ref(F.firebaseDb,`rooms/${this.roomId}/players/${this.localPlayerId}`),{clan:value,lastSeen:F.serverTimestamp()})},\n  async sendInput(input)",
             'setClan method')

# ---------- Egypt assets ----------
asset_block = '''

  // Clã Egito — Guerreiro/Guerreira
  egyptWarriorIdle:'https://i.postimg.cc/N0sJcHdp/guerreiro-egitado-parado.gif',
  egyptWarriorWalk:'https://i.postimg.cc/FKrW4LTM/guerreiro-egito-andando.gif',
  egyptFemaleWarriorIdle:'https://i.postimg.cc/R0SsBHgG/guerreira-egito-parada.gif',
  egyptFemaleWarriorWalk:'https://i.postimg.cc/tgqSjxBr/guerreira-egito-andando.gif',
  egyptSword:'https://i.postimg.cc/7LHsk2KN/espada-guerreiro-egpcios.png',

  // Clã Egito — Mago/Maga
  egyptMageStaff:'https://i.postimg.cc/9XnvYJLX/mao-atras-mago-egito.gif',
  egyptMageHand:'https://i.postimg.cc/HxKBXPTC/mao-magos-egpcios.png',
  egyptMagePower:'https://i.postimg.cc/hj4HpYkN/poder-normal-mago-egito.gif',
  egyptMagePowerSpecial:'https://i.postimg.cc/KcHdDJJq/poder-especial-mago-egito.gif',
  egyptMageIdle:'https://i.postimg.cc/PJwK4z5c/mago-egito-parado.gif',
  egyptMageWalk:'https://i.postimg.cc/gJ5N8Bm7/mago-egito-andando.gif',
  egyptMageSpecial:'https://i.postimg.cc/SRMVr7x3/mago-egito-especial.gif',
  egyptFemaleMageIdle:'https://i.postimg.cc/vBj3fSbL/maga-egito-parada.gif',
  egyptFemaleMageWalk:'https://i.postimg.cc/76cm0QwB/maga-egito-andando.gif',
  egyptFemaleMageSpecial:'https://i.postimg.cc/Ss5DCtk5/maga-egito-especial.gif',
'''
replace_once("\n  // Dragão Guerreiro — clã Guerreiros", asset_block + "\n  // Dragão Guerreiro — clã Guerreiros", 'egypt assets')

# ---------- State / utility ----------
replace_once("players:[{id:'p1',name:'Player 1',human:true,color:'#58a6ff'}]",
             "players:[{id:'p1',name:'Player 1',human:true,color:'#58a6ff',clan:'warriors'}]", 'default player clan')
replace_once("function localPlayer(){return state.players.find(p=>p.id===NetworkAdapter.localPlayerId)||state.players.find(p=>p.local)||state.players[0]}\nfunction serializeWarEntityForNetwork",
             "function localPlayer(){return state.players.find(p=>p.id===NetworkAdapter.localPlayerId)||state.players.find(p=>p.local)||state.players[0]}\nfunction normalizeClan(value){return value==='egypt'?'egypt':'warriors'}\nfunction clanLabel(value){return normalizeClan(value)==='egypt'?'Egito':'Guerreiros'}\nfunction serializeWarEntityForNetwork",
             'clan helpers')

# ---------- Egypt mage GIF durations ----------
replace_once("let MAGE_POWER_SPECIAL_DURATION=3000;\nlet GOLEM_NORMAL_DURATION=3000;",
             "let MAGE_POWER_SPECIAL_DURATION=3000;\nlet EGYPT_MAGE_NORMAL_DURATION=3000;\nlet EGYPT_MAGE_SPECIAL_MALE_DURATION=3000;\nlet EGYPT_MAGE_SPECIAL_FEMALE_DURATION=3000;\nlet EGYPT_MAGE_POWER_SPECIAL_DURATION=3000;\nlet GOLEM_NORMAL_DURATION=3000;",
             'egypt mage durations')
replace_once("let magePowerAssetReady=false;\nlet golemAttackAssetsReady=false;",
             "let magePowerAssetReady=false;\nlet egyptMagePowerAssetReady=false;\nlet golemAttackAssetsReady=false;",
             'egypt mage ready')
replace_once("const gifKeys=['golemAttack','golemSpecial','brownAttack','brownSpecial','brownPower','magePower','mageSpecial','femaleMageSpecial','magePowerSpecial','kingSpecial','kingPower','dragonTakeoff','dragonAttack','dragonFireball'];",
             "const gifKeys=['golemAttack','golemSpecial','brownAttack','brownSpecial','brownPower','magePower','mageSpecial','femaleMageSpecial','magePowerSpecial','egyptMagePower','egyptMageSpecial','egyptFemaleMageSpecial','egyptMagePowerSpecial','kingSpecial','kingPower','dragonTakeoff','dragonAttack','dragonFireball'];",
             'gif preload list')
replace_once("     if(key==='magePowerSpecial')MAGE_POWER_SPECIAL_DURATION=validGifDuration(duration,MAGE_POWER_SPECIAL_DURATION);\n     if(key==='golemAttack')",
             "     if(key==='magePowerSpecial')MAGE_POWER_SPECIAL_DURATION=validGifDuration(duration,MAGE_POWER_SPECIAL_DURATION);\n     if(key==='egyptMagePower')EGYPT_MAGE_NORMAL_DURATION=validGifDuration(duration,EGYPT_MAGE_NORMAL_DURATION);\n     if(key==='egyptMageSpecial')EGYPT_MAGE_SPECIAL_MALE_DURATION=validGifDuration(duration,EGYPT_MAGE_SPECIAL_MALE_DURATION);\n     if(key==='egyptFemaleMageSpecial')EGYPT_MAGE_SPECIAL_FEMALE_DURATION=validGifDuration(duration,EGYPT_MAGE_SPECIAL_FEMALE_DURATION);\n     if(key==='egyptMagePowerSpecial')EGYPT_MAGE_POWER_SPECIAL_DURATION=validGifDuration(duration,EGYPT_MAGE_POWER_SPECIAL_DURATION);\n     if(key==='golemAttack')",
             'egypt duration measurement')
replace_once("     if(key==='magePower')magePowerAssetReady=true;\n     if(key==='golemAttack'",
             "     if(key==='magePower')magePowerAssetReady=true;\n     if(key==='egyptMagePower')egyptMagePowerAssetReady=true;\n     if(key==='golemAttack'",
             'egypt ready flag')
replace_once("setTimeout(()=>{magePowerAssetReady=true},2000);",
             "setTimeout(()=>{magePowerAssetReady=true},2000);\nsetTimeout(()=>{egyptMagePowerAssetReady=true},2500);",
             'egypt ready fallback')

# ---------- Entity clan fields and spawns ----------
replace_once(" variant:'male',\n\n // Máquina de estados do Golem", " variant:'male',clan:'warriors',egyptSummoned:false,\n\n // Máquina de estados do Golem", 'entity clan fields')
old_spawn_w = '''function spawnWarrior(x,y,team,color,controlled=false,variant='male',ownerId=null){
 const e=entityBase('warrior',x,y,team,color);
 if(state.mode==='war')e.speed*=WAR_TROOP_SPEED_MULTIPLIER;
 e.hp=e.maxHp=150;
 e.shield=e.maxShield=100;
 e.controlled=controlled;
 e.ownerId=ownerId;
 e.variant=variant==='female'?'female':'male';
 state.entities.push(e);
 return e;
}'''
new_spawn_w = '''function spawnWarrior(x,y,team,color,controlled=false,variant='male',ownerId=null,clan='warriors',egyptSummoned=false){
 const e=entityBase('warrior',x,y,team,color);
 if(state.mode==='war')e.speed*=WAR_TROOP_SPEED_MULTIPLIER;
 e.hp=e.maxHp=150;
 e.shield=e.maxShield=100;
 e.controlled=controlled;
 e.ownerId=ownerId;
 e.variant=variant==='female'?'female':'male';
 e.clan=normalizeClan(clan);
 e.egyptSummoned=!!egyptSummoned;
 state.entities.push(e);
 return e;
}'''
replace_once(old_spawn_w, new_spawn_w, 'spawn warrior')
old_spawn_m = '''function spawnMage(x,y,team,color,variant='male'){
 const e=entityBase('mage',x,y,team,color);
 e.variant=variant==='female'?'female':'male';e.hp=e.maxHp=200;e.shield=e.maxShield=50;e.damage=5;e.r=31;
 // Mantém a velocidade-base própria; no modo Guerra recebe exatamente -50%.
 e.speed=state.mode==='war'?92*WAR_TROOP_SPEED_MULTIPLIER:92;e.attackCooldown=0;e.mageCycle=0;
 state.entities.push(e);return e;
}'''
new_spawn_m = '''function spawnMage(x,y,team,color,variant='male',clan='warriors'){
 const e=entityBase('mage',x,y,team,color);
 e.variant=variant==='female'?'female':'male';e.clan=normalizeClan(clan);e.hp=e.maxHp=200;e.shield=e.maxShield=50;e.damage=5;e.r=31;
 // Mantém a velocidade-base própria; no modo Guerra recebe exatamente -50%.
 e.speed=state.mode==='war'?92*WAR_TROOP_SPEED_MULTIPLIER:92;e.attackCooldown=0;e.mageCycle=0;
 state.entities.push(e);return e;
}'''
replace_once(old_spawn_m, new_spawn_m, 'spawn mage')

# ---------- Network serialization ----------
replace_once("   variant:e.variant||'male',ownerId:e.ownerId??null\n };",
             "   variant:e.variant||'male',ownerId:e.ownerId??null,clan:normalizeClan(e.clan),egyptSummoned:!!e.egyptSummoned\n };",
             'serialize clan')
replace_once("   out.mageAttackSerial=Number(e.mageAttackSerial)||0;\n   if(e.pendingMageAttack){",
             "   out.mageAttackSerial=Number(e.mageAttackSerial)||0;\n   out.mageCycle=Number(e.mageCycle)||0;\n   if(e.pendingMageAttack){",
             'serialize mage cycle')

# ---------- Firebase roster keeps clans ----------
replace_once("name:p.name||`Player ${i+1}`,human:true,local:p.uid===NetworkAdapter.localPlayerId,color:p.color||COLORS[i%COLORS.length]}",
             "name:p.name||`Player ${i+1}`,human:true,local:p.uid===NetworkAdapter.localPlayerId,color:p.color||COLORS[i%COLORS.length],clan:normalizeClan(p.clan)}",
             'firebase human clan')
replace_once("const bots=Array.from({length:npcCount},(_,i)=>({id:`npc_${i+1}`,name:`NPC ${i+1}`,human:false,local:false,color:COLORS[(humans.length+i)%COLORS.length]}));",
             "const bots=Array.from({length:npcCount},(_,i)=>({id:`npc_${i+1}`,name:`NPC ${i+1}`,human:false,local:false,color:COLORS[(humans.length+i)%COLORS.length],clan:'warriors'}));",
             'firebase bot clan')
replace_once("        color:COLORS[idx%COLORS.length]\n      });",
             "        color:COLORS[idx%COLORS.length],\n        clan:'warriors'\n      });",
             'offline bot clan')

# ---------- Clan selection interaction ----------
clan_js = r'''
function renderClanSelection(){
 const clan=normalizeClan(localPlayer()?.clan);
 $$('.clan-option[data-clan]').forEach(btn=>btn.classList.toggle('selected',normalizeClan(btn.dataset.clan)===clan));
 const status=$('#clanSelectionStatus');if(status)status.textContent='Seu clã: '+clanLabel(clan);
}
$$('.clan-option[data-clan]').forEach(btn=>btn.onclick=async()=>{
 const p=localPlayer();if(!p)return;
 const clan=normalizeClan(btn.dataset.clan);
 p.clan=clan;
 renderClanSelection();
 if(NetworkAdapter.online){
   try{await NetworkAdapter.setClan(clan)}catch(err){console.error(err)}
 }
});
function configureWarShopForClan(){
 const clan=normalizeClan(localPlayer()?.clan);
 $$('.clan-shop').forEach(group=>group.hidden=normalizeClan(group.dataset.clanShop)!==clan);
}
'''
replace_once("let warStartInFlight=false;", clan_js + "\nlet warStartInFlight=false;", 'clan selection js')
replace_once("if(state.players.length<2){state.players.push({id:'p2',name:'Player 2',human:false,color:COLORS[1]});}\n    renderPlayers();navigateScreen('clanScreen');",
             "if(state.players.length<2){state.players.push({id:'p2',name:'Player 2',human:false,color:COLORS[1],clan:'warriors'});}\n    renderPlayers();navigateScreen('clanScreen');renderClanSelection();",
             'lobby clan navigation')
replace_once("if(room.status==='clan'&&$('#clanScreen').style.display==='none')navigateScreen('clanScreen');",
             "if(room.status==='clan'&&$('#clanScreen').style.display==='none')navigateScreen('clanScreen');\n   if(room.status==='clan')renderClanSelection();",
             'remote clan render')
replace_once("function configureGameScreenForMode(){\n const pve=state.mode==='pve';$('#gameScreen').classList.toggle('pve-mode',pve);$('#shopButton').style.display=pve?'none':'block';$('#touchControls').style.display=pve&&isMobileLike()?'block':'none';$('#attackBtn').style.display=pve?'block':'none';$('#cameraHint').style.display=pve?'none':'block';\n}",
             "function configureGameScreenForMode(){\n const pve=state.mode==='pve';$('#gameScreen').classList.toggle('pve-mode',pve);$('#shopButton').style.display=pve?'none':'block';$('#touchControls').style.display=pve&&isMobileLike()?'block':'none';$('#attackBtn').style.display=pve?'block':'none';$('#cameraHint').style.display=pve?'none':'block';if(!pve)configureWarShopForClan();\n}",
             'shop clan configure')

# ---------- Host command clan authorization ----------
old_cmds = '''     if(cmd.type==='buy-warrior')buyForPlayer(p,false);
     if(cmd.type==='buy-brown-warrior')buyBrownWarriorForPlayer(p,false);
     if(cmd.type==='buy-king')buyKingForPlayer(p,false);
     if(cmd.type==='buy-golem')buyGolemForPlayer(p,false);
     if(cmd.type==='buy-mage')buyMageForPlayer(p,false);
     if(cmd.type==='buy-dragon')buyDragonForPlayer(p,false);'''
new_cmds = '''     const clan=normalizeClan(p.clan);
     if(clan==='warriors'&&cmd.type==='buy-warrior')buyForPlayer(p,false);
     if(clan==='warriors'&&cmd.type==='buy-brown-warrior')buyBrownWarriorForPlayer(p,false);
     if(clan==='warriors'&&cmd.type==='buy-king')buyKingForPlayer(p,false);
     if(clan==='warriors'&&cmd.type==='buy-golem')buyGolemForPlayer(p,false);
     if(clan==='warriors'&&cmd.type==='buy-mage')buyMageForPlayer(p,false);
     if(clan==='warriors'&&cmd.type==='buy-dragon')buyDragonForPlayer(p,false);
     if(clan==='egypt'&&cmd.type==='buy-egypt-warrior')buyEgyptWarriorForPlayer(p,false);
     if(clan==='egypt'&&cmd.type==='buy-egypt-mage')buyEgyptMageForPlayer(p,false);'''
replace_once(old_cmds, new_cmds, 'host commands')

# ---------- Purchase system ----------
purchase_pattern = r"function requestWarPurchase\(type\)\{.*?function buyDragonForPlayer\(p,bot\)\{.*?\n\}\n\n\nfunction warCompositionForTeam"
purchase_block = r'''function requestWarPurchase(type){
 if(state.phase!=='prep')return;const p=localPlayer();if(!p)return;
 const clan=normalizeClan(p.clan);
 const allowed=clan==='egypt'?new Set(['buy-egypt-warrior','buy-egypt-mage']):new Set(['buy-warrior','buy-brown-warrior','buy-king','buy-golem','buy-mage','buy-dragon']);
 if(!allowed.has(type))return;
 if(NetworkAdapter.online&&!NetworkAdapter.isHost)NetworkAdapter.sendCommand(type).catch(console.error);
 else {
   if(type==='buy-warrior')buyForPlayer(p,false);
   if(type==='buy-brown-warrior')buyBrownWarriorForPlayer(p,false);
   if(type==='buy-king')buyKingForPlayer(p,false);
   if(type==='buy-golem')buyGolemForPlayer(p,false);
   if(type==='buy-mage')buyMageForPlayer(p,false);
   if(type==='buy-dragon')buyDragonForPlayer(p,false);
   if(type==='buy-egypt-warrior')buyEgyptWarriorForPlayer(p,false);
   if(type==='buy-egypt-mage')buyEgyptMageForPlayer(p,false);
 }
}
$('#buyWarrior').onclick=()=>requestWarPurchase('buy-warrior');
$('#buyBrownWarrior').onclick=()=>requestWarPurchase('buy-brown-warrior');
$('#buyKing').onclick=()=>requestWarPurchase('buy-king');
$('#buyGolem').onclick=()=>requestWarPurchase('buy-golem');
$('#buyMage').onclick=()=>requestWarPurchase('buy-mage');
$('#buyDragon').onclick=()=>requestWarPurchase('buy-dragon');
$('#buyEgyptWarrior').onclick=()=>requestWarPurchase('buy-egypt-warrior');
$('#buyEgyptMage').onclick=()=>requestWarPurchase('buy-egypt-mage');
function buyForPlayer(p,bot){
 if(normalizeClan(p.clan)!=='warriors')return false;
 const cost=WAR_UNIT_COSTS.warrior;if(p.gems<cost)return false;
 p.gems-=cost;p.troops++;
 const t=p.territory,angle=Math.random()*Math.PI*2,r=Math.random()*95;
 const variant=p.nextWarriorVariant==='female'?'female':'male';
 spawnWarrior(t.x+Math.cos(angle)*r,t.y+Math.sin(angle)*r,p.id,p.color,false,variant,null,'warriors',false);
 p.nextWarriorVariant=variant==='male'?'female':'male';
 return true;
}
function buyEgyptWarriorForPlayer(p,bot){
 if(normalizeClan(p.clan)!=='egypt')return false;
 const cost=WAR_UNIT_COSTS.warrior;if(p.gems<cost)return false;
 p.gems-=cost;p.troops++;
 const t=p.territory,angle=Math.random()*Math.PI*2,r=Math.random()*95;
 const variant=p.nextWarriorVariant==='female'?'female':'male';
 spawnWarrior(t.x+Math.cos(angle)*r,t.y+Math.sin(angle)*r,p.id,p.color,false,variant,null,'egypt',false);
 p.nextWarriorVariant=variant==='male'?'female':'male';
 return true;
}
function buyBrownWarriorForPlayer(p,bot){
 if(normalizeClan(p.clan)!=='warriors')return false;
 const cost=WAR_UNIT_COSTS.brownWarrior;if(p.gems<cost)return false;
 p.gems-=cost;p.troops++;
 const t=p.territory,angle=Math.random()*Math.PI*2,r=Math.random()*88;
 spawnBrownWarrior(t.x+Math.cos(angle)*r,t.y+Math.sin(angle)*r,p.id,p.color);
 return true;
}
function buyKingForPlayer(p,bot){
 if(normalizeClan(p.clan)!=='warriors')return false;
 const cost=WAR_UNIT_COSTS.king;if(p.gems<cost)return false;
 p.gems-=cost;p.troops++;
 const t=p.territory,angle=Math.random()*Math.PI*2,r=Math.random()*84;
 spawnKing(t.x+Math.cos(angle)*r,t.y+Math.sin(angle)*r,p.id,p.color);
 return true;
}
function buyGolemForPlayer(p,bot){
 if(normalizeClan(p.clan)!=='warriors')return false;
 const cost=WAR_UNIT_COSTS.golem;if(p.gems<cost)return false;
 p.gems-=cost;p.troops++;
 const t=p.territory,angle=Math.random()*Math.PI*2,r=Math.random()*78;
 spawnGolem(t.x+Math.cos(angle)*r,t.y+Math.sin(angle)*r,p.id,p.color);
 return true;
}
function buyMageForPlayer(p,bot){
 if(normalizeClan(p.clan)!=='warriors')return false;
 const cost=WAR_UNIT_COSTS.mage;if(p.gems<cost)return false;p.gems-=cost;p.troops++;
 const t=p.territory,angle=Math.random()*Math.PI*2,r=Math.random()*84;
 spawnMage(t.x+Math.cos(angle)*r,t.y+Math.sin(angle)*r,p.id,p.color,Math.random()<.5?'male':'female','warriors');
 return true;
}
function buyEgyptMageForPlayer(p,bot){
 if(normalizeClan(p.clan)!=='egypt')return false;
 const cost=WAR_UNIT_COSTS.mage;if(p.gems<cost)return false;p.gems-=cost;p.troops++;
 const t=p.territory,angle=Math.random()*Math.PI*2,r=Math.random()*84;
 spawnMage(t.x+Math.cos(angle)*r,t.y+Math.sin(angle)*r,p.id,p.color,Math.random()<.5?'male':'female','egypt');
 return true;
}
function buyDragonForPlayer(p,bot){
 if(normalizeClan(p.clan)!=='warriors')return false;
 const cost=WAR_UNIT_COSTS.dragon;if(p.gems<cost)return false;p.gems-=cost;p.troops++;
 const t=p.territory,angle=Math.random()*Math.PI*2,r=Math.random()*82;
 spawnDragon(t.x+Math.cos(angle)*r,t.y+Math.sin(angle)*r,p.id,p.color);
 return true;
}


function warCompositionForTeam'''
sub_once(purchase_pattern, purchase_block, 'purchase system', re.S)

# ---------- Bot shop respects clan ----------
old_affordable = '''function affordableBotWarTypes(p){
 const types=[];
 if(p.gems>=WAR_UNIT_COSTS.warrior)types.push('warrior');
 if(p.gems>=WAR_UNIT_COSTS.brownWarrior)types.push('brownWarrior');
 if(p.gems>=WAR_UNIT_COSTS.king)types.push('king');
 if(p.gems>=WAR_UNIT_COSTS.golem)types.push('golem');
 if(p.gems>=WAR_UNIT_COSTS.dragon)types.push('dragon');
 if(p.gems>=WAR_UNIT_COSTS.mage)types.push('mage');
 return types;
}'''
new_affordable = '''function affordableBotWarTypes(p){
 const types=[];
 if(normalizeClan(p.clan)==='egypt'){
   if(p.gems>=WAR_UNIT_COSTS.warrior)types.push('warrior');
   if(p.gems>=WAR_UNIT_COSTS.mage)types.push('mage');
   return types;
 }
 if(p.gems>=WAR_UNIT_COSTS.warrior)types.push('warrior');
 if(p.gems>=WAR_UNIT_COSTS.brownWarrior)types.push('brownWarrior');
 if(p.gems>=WAR_UNIT_COSTS.king)types.push('king');
 if(p.gems>=WAR_UNIT_COSTS.golem)types.push('golem');
 if(p.gems>=WAR_UNIT_COSTS.dragon)types.push('dragon');
 if(p.gems>=WAR_UNIT_COSTS.mage)types.push('mage');
 return types;
}'''
replace_once(old_affordable, new_affordable, 'bot affordable')
old_buybot = '''function buyBotWarType(p,type){
 if(type==='brownWarrior')return buyBrownWarriorForPlayer(p,true);
 if(type==='king')return buyKingForPlayer(p,true);
 if(type==='dragon')return buyDragonForPlayer(p,true);
 if(type==='golem')return buyGolemForPlayer(p,true);
 if(type==='mage')return buyMageForPlayer(p,true);
 return buyForPlayer(p,true);
}'''
new_buybot = '''function buyBotWarType(p,type){
 if(normalizeClan(p.clan)==='egypt'){
   if(type==='mage')return buyEgyptMageForPlayer(p,true);
   return buyEgyptWarriorForPlayer(p,true);
 }
 if(type==='brownWarrior')return buyBrownWarriorForPlayer(p,true);
 if(type==='king')return buyKingForPlayer(p,true);
 if(type==='dragon')return buyDragonForPlayer(p,true);
 if(type==='golem')return buyGolemForPlayer(p,true);
 if(type==='mage')return buyMageForPlayer(p,true);
 return buyForPlayer(p,true);
}'''
replace_once(old_buybot, new_buybot, 'bot buy')
replace_once("if(!bought&&p.gems>=WAR_UNIT_COSTS.warrior)bought=buyForPlayer(p,true);",
             "if(!bought&&p.gems>=WAR_UNIT_COSTS.warrior)bought=normalizeClan(p.clan)==='egypt'?buyEgyptWarriorForPlayer(p,true):buyForPlayer(p,true);",
             'bot fallback')

# ---------- Egypt mage special: summon five ----------
start_mage_pattern = r"function startMageAttack\(e,kind,target=null\)\{.*?\n\}\nfunction updateMageAttackState"
start_mage_new = r'''function startMageAttack(e,kind,target=null){
 if(!e.alive||e.type!=='mage'||e.pendingMageAttack||e.attackCooldown>0||e.knockTime>0)return false;
 const egypt=e.clan==='egypt';
 if(kind==='normal'&&!(egypt?egyptMagePowerAssetReady:magePowerAssetReady))return false;
 const now=performance.now();e.attackCooldown=4;e.lastAttackAt=now;e.lastCombatAt=now;e.mageAttackKind=kind;e.mageAttackSerial=(e.mageAttackSerial||0)+1;
 if(kind==='special'){
   const bodyDuration=egypt
     ? (e.variant==='female'?EGYPT_MAGE_SPECIAL_FEMALE_DURATION:EGYPT_MAGE_SPECIAL_MALE_DURATION)
     : (e.variant==='female'?MAGE_SPECIAL_FEMALE_DURATION:MAGE_SPECIAL_MALE_DURATION);
   const powerDuration=egypt?EGYPT_MAGE_POWER_SPECIAL_DURATION:MAGE_POWER_SPECIAL_DURATION;
   const duration=Math.max(bodyDuration,powerDuration);
   e.specialCooldown=MAGE_SPECIAL_COOLDOWN;
   e.moving=false;e.pendingMageAttack={
     kind,targetId:null,originX:e.x,originY:e.y,startedAt:now,duration,
     damageAt:now+Math.min(1200,Math.max(650,duration*.40)),
     endAt:now+duration,impacted:false,hitIds:{}
   };
   e.mageCycle=0;
   addWarGoalProgress(e.team,'specials');
 }else{
   const angle=target?Math.atan2(target.y-e.y,target.x-e.x):(e.heading||0);
   const targetDistance=target?dist(e,target):245;
   e.moving=false;
   const duration=egypt?EGYPT_MAGE_NORMAL_DURATION:MAGE_NORMAL_DURATION;
   e.pendingMageAttack={
     kind,targetId:target?.id??null,originX:e.x,originY:e.y,
     angle,length:clamp(targetDistance-20,140,310),duration,
     startedAt:now,endAt:now+duration,
     damageStartAt:now+MAGE_DAMAGE_DELAY,
     damageEndAt:now+duration-100,
     nextTickAt:now+MAGE_DAMAGE_DELAY
   };
   e.mageCycle=(e.mageCycle||0)+1;
   addWarGoalProgress(e.team,'ranged');
 }
 return true;
}
function countLivingEgyptSummons(team){
 let count=0;
 for(const t of state.entities){
   if(t.alive&&t.team===team&&t.type==='warrior'&&t.clan==='egypt'&&t.egyptSummoned)count++;
 }
 return count;
}
function spawnEgyptMageWarriors(e,p){
 const ox=Number(p.originX)||e.x,oy=Number(p.originY)||e.y;
 const base=(Number(e.mageAttackSerial)||0)*.37;
 for(let i=0;i<5;i++){
   const angle=base+(Math.PI*2/5)*i;
   const radius=58+(i%3)*34;
   const x=clamp(ox+Math.cos(angle)*radius,45,state.world.w-45);
   const y=clamp(oy+Math.sin(angle)*radius,45,state.world.h-45);
   const variant=i%2===0?'male':'female';
   spawnWarrior(x,y,e.team,e.color,false,variant,null,'egypt',true);
 }
}
function updateMageAttackState'''
sub_once(start_mage_pattern, start_mage_new, 'start mage function', re.S)

# Replace only special impact body: Egypt summons; Warriors keep damage and heal. Literal request preserves existing ally heal for Egypt.
old_special_prefix = '''     p.impacted=true;
     p.hitIds=p.hitIds||{};
     const ox=p.originX,oy=p.originY,r=MAGE_SPECIAL_RADIUS,r2=r*r;

     // Dano: mesmas regras e mesma distância final; só deixamos de testar
     // entidades que estão em células impossíveis de alcançar.
     forEachWarSpatialCandidate(ox-r,oy-r,ox+r,oy+r,t=>{
       if(!t.alive||t===e||t.team===e.team)return;
       const dx=t.x-ox,dy=t.y-oy;if(dx*dx+dy*dy>r2)return;
       if(p.hitIds[t.id])return;p.hitIds[t.id]=true;
       applyCombatHit(t,e,MAGE_SPECIAL_DAMAGE,{knockForce:260,knockTime:.18,tilt:10});
     });

     // Cura mantém exatamente a regra anterior, inclusive o próprio Mago.
     forEachWarSpatialCandidate(ox-r,oy-r,ox+r,oy+r,ally=>{'''
new_special_prefix = '''     p.impacted=true;
     p.hitIds=p.hitIds||{};
     const ox=p.originX,oy=p.originY,r=MAGE_SPECIAL_RADIUS,r2=r*r;

     if(e.clan==='egypt'){
       // Especial do Egito: substitui o dano em área pela invocação de 5 guerreiros egípcios.
       spawnEgyptMageWarriors(e,p);
     }else{
       forEachWarSpatialCandidate(ox-r,oy-r,ox+r,oy+r,t=>{
         if(!t.alive||t===e||t.team===e.team)return;
         const dx=t.x-ox,dy=t.y-oy;if(dx*dx+dy*dy>r2)return;
         if(p.hitIds[t.id])return;p.hitIds[t.id]=true;
         applyCombatHit(t,e,MAGE_SPECIAL_DAMAGE,{knockForce:260,knockTime:.18,tilt:10});
       });
     }

     // A cura de 30 do Mago original é preservada; a diferença egípcia substitui somente o dano pela invocação.
     forEachWarSpatialCandidate(ox-r,oy-r,ox+r,oy+r,ally=>{'''
replace_once(old_special_prefix, new_special_prefix, 'egypt mage summon impact')

# ---------- Egypt mage AI trigger ----------
ai_pattern = r"function aiFightMage\(e,dt,forcedTeam,preparedCandidates=null\)\{.*?\n\}\n\n\nfunction aiFightBrownWarrior"
ai_new = r'''function aiFightMage(e,dt,forcedTeam,preparedCandidates=null){
 if(!e.alive||e.knockTime>0){e.moving=false;return}
 const now=performance.now();
 if(e.pendingMageAttack){e.moving=false;return}
 const candidates=preparedCandidates||state.entities;
 const target=nearestEngageableCandidate(e,candidates,forcedTeam,false);
 if(!target){e.moving=false;e.target=null;return}
 e.target=target;const dx=target.x-e.x,dy=target.y-e.y,d=Math.hypot(dx,dy)||1;e.heading=Math.atan2(dy,dx);if(Math.abs(dx)>4)e.facing=dx<0?-1:1;
 if(e.attackCooldown<=0&&!e.pendingMageAttack){
   const lowHealth=e.hp<=e.maxHp*.5;
   if(e.clan==='egypt'){
     // Egito: vida baixa OU 5 normais completos tornam o especial devido.
     // Porém a invocação só acontece quando restar no máximo 1 guerreiro invocado vivo.
     const cycleDue=(Number(e.mageCycle)||0)>=5;
     const summonsAlive=countLivingEgyptSummons(e.team);
     if(e.specialCooldown<=0&&summonsAlive<=1&&(lowHealth||cycleDue)){
       if(startMageAttack(e,'special',target))return;
     }
   }else{
     // Mago Guerreiro mantém sua regra original: aglomeração OU vida baixa.
     let nearbyForSpecial=0;
     const mageSpecialRadiusSq=MAGE_SPECIAL_RADIUS*MAGE_SPECIAL_RADIUS;
     for(const t of candidates){
       if(!t||!t.alive||t===e||t.team===e.team||
          (forcedTeam&&t.team!==forcedTeam)||!canEngageTarget(e,t))continue;
       const sdx=t.x-e.x,sdy=t.y-e.y;
       if(sdx*sdx+sdy*sdy<=mageSpecialRadiusSq)nearbyForSpecial++;
     }
     if(e.specialCooldown<=0&&(nearbyForSpecial>=3||lowHealth)){
       if(startMageAttack(e,'special',target))return;
     }
   }
   if(d>=185&&d<=285){startMageAttack(e,'normal',target);return}
 }
 if(d<175){e.x-=dx/d*e.speed*dt;e.y-=dy/d*e.speed*dt;e.moving=true}
 else if(d>285){e.x+=dx/d*e.speed*dt;e.y+=dy/d*e.speed*dt;e.moving=true}
 else e.moving=false;
 e.x=clamp(e.x,40,state.world.w-40);e.y=clamp(e.y,40,state.world.h-40);
}


function aiFightBrownWarrior'''
sub_once(ai_pattern, ai_new, 'mage AI', re.S)

# ---------- Entity visuals choose assets by clan ----------
old_mage_visual = ''' }else if(e.type==='mage'){
   el.classList.add('mage-visual');
   const bodyIdle=e.variant==='female'?ASSETS.femaleMageIdle:ASSETS.mageIdle;
   const bodyWalk=e.variant==='female'?ASSETS.femaleMageWalk:ASSETS.mageWalk;
   const bodySpecialKey=e.variant==='female'?'femaleMageSpecial':'mageSpecial';
   el.innerHTML=`
     <div class="entity-facing">
       <img class="mage-staff" src="${ASSETS.mageStaff}" draggable="false">
       <img class="entity-body entity-idle active-sprite" src="${bodyIdle}" draggable="false" style="opacity:1">
       <img class="entity-body entity-walk" src="${bodyWalk}" draggable="false" style="opacity:0">
       <img class="entity-body entity-mage-special" data-asset-key="${bodySpecialKey}" draggable="false" style="opacity:0">
       <img class="mage-hand" src="${ASSETS.mageHand}" draggable="false">
     </div>'''
new_mage_visual = ''' }else if(e.type==='mage'){
   el.classList.add('mage-visual');
   const egypt=e.clan==='egypt';
   if(egypt)el.classList.add('egypt-unit');
   const bodyIdle=e.variant==='female'?(egypt?ASSETS.egyptFemaleMageIdle:ASSETS.femaleMageIdle):(egypt?ASSETS.egyptMageIdle:ASSETS.mageIdle);
   const bodyWalk=e.variant==='female'?(egypt?ASSETS.egyptFemaleMageWalk:ASSETS.femaleMageWalk):(egypt?ASSETS.egyptMageWalk:ASSETS.mageWalk);
   const bodySpecialKey=e.variant==='female'?(egypt?'egyptFemaleMageSpecial':'femaleMageSpecial'):(egypt?'egyptMageSpecial':'mageSpecial');
   const staff=egypt?ASSETS.egyptMageStaff:ASSETS.mageStaff;
   const hand=egypt?ASSETS.egyptMageHand:ASSETS.mageHand;
   el.innerHTML=`
     <div class="entity-facing">
       <img class="mage-staff" src="${staff}" draggable="false">
       <img class="entity-body entity-idle active-sprite" src="${bodyIdle}" draggable="false" style="opacity:1">
       <img class="entity-body entity-walk" src="${bodyWalk}" draggable="false" style="opacity:0">
       <img class="entity-body entity-mage-special" data-asset-key="${bodySpecialKey}" draggable="false" style="opacity:0">
       <img class="mage-hand" src="${hand}" draggable="false">
     </div>'''
replace_once(old_mage_visual, new_mage_visual, 'mage visual assets')
old_warrior_visual = ''' }else{
   const bodyIdle=e.variant==='female'?ASSETS.femaleIdle:ASSETS.idle;
   const bodyWalk=e.variant==='female'?ASSETS.femaleWalk:ASSETS.walk;

   el.innerHTML=`
     <div class="entity-facing">
       <!-- Guerreiro/Guerreira compartilham toda a lógica; só muda o corpo. -->
       <img class="entity-body entity-idle active-sprite" src="${bodyIdle}" draggable="false" style="opacity:1">
       <img class="entity-body entity-walk" src="${bodyWalk}" draggable="false" style="opacity:0">
     </div>
     <div class="entity-weapon-facing">
       <div class="entity-slash"></div>
       <img class="entity-sword" src="${ASSETS.sword}" draggable="false">'''
new_warrior_visual = ''' }else{
   const egypt=e.type==='warrior'&&e.clan==='egypt';
   if(egypt)el.classList.add('egypt-unit');
   if(e.egyptSummoned)el.classList.add('egypt-summoned-spawn');
   const bodyIdle=e.variant==='female'?(egypt?ASSETS.egyptFemaleWarriorIdle:ASSETS.femaleIdle):(egypt?ASSETS.egyptWarriorIdle:ASSETS.idle);
   const bodyWalk=e.variant==='female'?(egypt?ASSETS.egyptFemaleWarriorWalk:ASSETS.femaleWalk):(egypt?ASSETS.egyptWarriorWalk:ASSETS.walk);
   const sword=egypt?ASSETS.egyptSword:ASSETS.sword;

   el.innerHTML=`
     <div class="entity-facing">
       <!-- Guerreiro/Guerreira compartilham toda a lógica; clã troca somente os sprites. -->
       <img class="entity-body entity-idle active-sprite" src="${bodyIdle}" draggable="false" style="opacity:1">
       <img class="entity-body entity-walk" src="${bodyWalk}" draggable="false" style="opacity:0">
     </div>
     <div class="entity-weapon-facing">
       <div class="entity-slash"></div>
       <img class="entity-sword" src="${sword}" draggable="false">'''
replace_once(old_warrior_visual, new_warrior_visual, 'warrior visual assets')
replace_once(" else if(e.type==='mage')el._gifKeys={idle:e.variant==='female'?'femaleMageIdle':'mageIdle',walk:e.variant==='female'?'femaleMageWalk':'mageWalk',special:e.variant==='female'?'femaleMageSpecial':'mageSpecial'};",
             " else if(e.type==='mage'){const egypt=e.clan==='egypt';el._gifKeys={idle:e.variant==='female'?(egypt?'egyptFemaleMageIdle':'femaleMageIdle'):(egypt?'egyptMageIdle':'mageIdle'),walk:e.variant==='female'?(egypt?'egyptFemaleMageWalk':'femaleMageWalk'):(egypt?'egyptMageWalk':'mageWalk'),special:e.variant==='female'?(egypt?'egyptFemaleMageSpecial':'femaleMageSpecial'):(egypt?'egyptMageSpecial':'mageSpecial')}};",
             'mage gif keys')
replace_once(" else el._gifKeys={idle:e.variant==='female'?'femaleIdle':'idle',walk:e.variant==='female'?'femaleWalk':'walk'};",
             " else {const egypt=e.type==='warrior'&&e.clan==='egypt';el._gifKeys={idle:e.variant==='female'?(egypt?'egyptFemaleWarriorIdle':'femaleIdle'):(egypt?'egyptWarriorIdle':'idle'),walk:e.variant==='female'?(egypt?'egyptFemaleWarriorWalk':'femaleWalk'):(egypt?'egyptWarriorWalk':'walk')}};",
             'warrior gif keys')

# Mage special body restart must use the entity's actual special key.
replace_once("if(e.mageAttackSerial>0&&special)restartGif(el._mageSpecial,e.variant==='female'?'femaleMageSpecial':'mageSpecial',e.mageAttackSerial);",
             "if(e.mageAttackSerial>0&&special)restartGif(el._mageSpecial,el._gifKeys?.special||(e.variant==='female'?'femaleMageSpecial':'mageSpecial'),e.mageAttackSerial);",
             'mage special visual key')

# Mage power effect assets by clan.
old_power = '''     img.className=p.kind==='special'?'mage-power-special':'mage-power-normal';
     if(p.kind==='special')restartGif(img,'magePowerSpecial',serial);
     else restartMagePowerGif(img,serial);'''
new_power = '''     img.className=p.kind==='special'?'mage-power-special':'mage-power-normal';
     const egypt=e.clan==='egypt';
     if(p.kind==='special')restartGif(img,egypt?'egyptMagePowerSpecial':'magePowerSpecial',serial);
     else restartGif(img,egypt?'egyptMagePower':'magePower',serial);'''
replace_once(old_power, new_power, 'mage power assets')

# ---------- HUD button refs / disabled ----------
replace_once("const buyWarriorPerfEl=$('#buyWarrior'),buyBrownWarriorPerfEl=$('#buyBrownWarrior'),buyKingPerfEl=$('#buyKing'),buyGolemPerfEl=$('#buyGolem'),buyMagePerfEl=$('#buyMage'),buyDragonPerfEl=$('#buyDragon');",
             "const buyWarriorPerfEl=$('#buyWarrior'),buyBrownWarriorPerfEl=$('#buyBrownWarrior'),buyKingPerfEl=$('#buyKing'),buyGolemPerfEl=$('#buyGolem'),buyMagePerfEl=$('#buyMage'),buyDragonPerfEl=$('#buyDragon'),buyEgyptWarriorPerfEl=$('#buyEgyptWarrior'),buyEgyptMagePerfEl=$('#buyEgyptMage');",
             'hud refs')
replace_once("    perfSetDisabled(buyDragonPerfEl,state.phase!=='prep'||gems<WAR_UNIT_COSTS.dragon);",
             "    perfSetDisabled(buyDragonPerfEl,state.phase!=='prep'||gems<WAR_UNIT_COSTS.dragon);\n    perfSetDisabled(buyEgyptWarriorPerfEl,state.phase!=='prep'||gems<WAR_UNIT_COSTS.warrior);\n    perfSetDisabled(buyEgyptMagePerfEl,state.phase!=='prep'||gems<WAR_UNIT_COSTS.mage);",
             'hud egypt buttons')

# ---------- Validate ----------
required = [
    MARK,
    'data-clan="egypt"',
    'data-clan-shop="egypt"',
    'buyEgyptWarrior', 'buyEgyptMage',
    'egyptWarriorIdle', 'egyptFemaleWarriorWalk', 'egyptSword',
    'egyptMagePowerSpecial', 'egyptFemaleMageSpecial',
    'spawnEgyptMageWarriors', 'countLivingEgyptSummons',
    "summonsAlive<=1&&(lowHealth||cycleDue)",
    "clan:normalizeClan(e.clan),egyptSummoned:!!e.egyptSummoned",
]
for item in required:
    if item not in text:
        raise SystemExit(f'Validation missing: {item}')

# We must not accidentally reintroduce the reverted static-GIF LOD system.
for forbidden in ['WAR ADAPTIVE VISUAL LOD 2026-09-12','entity-lod-poster','WAR_LOD_POSTER_CACHE']:
    if forbidden in text:
        raise SystemExit(f'Forbidden reverted optimization found: {forbidden}')

path.write_text(text, encoding='utf-8')
print('Egypt clan patch applied successfully')
