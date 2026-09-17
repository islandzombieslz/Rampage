from pathlib import Path
import re

p=Path('index.html')
t=p.read_text(encoding='utf-8')


def sub_once(pattern,repl,label,flags=0):
    global t
    new,count=re.subn(pattern,repl,t,count=1,flags=flags)
    if count!=1:
        raise SystemExit(f'{label}: expected exactly one match, found {count}')
    t=new


# -----------------------------------------------------------------------------
# 1) Clean clan screen actions markup. Keep only ONE confirmation button and ONE start.
# -----------------------------------------------------------------------------
sub_once(
    r'<div id="clanSelectionStatus">.*?</div>\s*<div class="divider"></div>\s*(?:<button id="confirmClanBtn"[^>]*>.*?</button>\s*)?<button id="startWarBtn"[^>]*>.*?</button>',
    '''<div id="clanSelectionStatus">Selecionado: Guerreiros</div>
    <div class="divider"></div>
    <div class="clan-actions">
      <button id="confirmClanBtn" type="button">Confirmar clã</button>
      <button id="startWarBtn" class="primary" type="button">Iniciar preparação</button>
    </div>''',
    'clan actions markup',
    re.S,
)

# -----------------------------------------------------------------------------
# 2) Final CSS override. Old absolute #startWarBtn rules remain harmless because
#    this block comes later and has greater specificity inside .clan-actions.
# -----------------------------------------------------------------------------
css_marker='/* CLAN MENU V4 FIX 2026-09-17 */'
if css_marker not in t:
    css='''\n\n/* CLAN MENU V4 FIX 2026-09-17 */
#clanScreen>.card > .clan-options-grid{
  bottom:26.2% !important;
}
#clanScreen #clanSelectionStatus{
  bottom:21.2% !important;
  z-index:18 !important;
  pointer-events:none !important;
}
#clanScreen .clan-actions{
  position:absolute !important;
  left:21% !important;
  right:21% !important;
  bottom:13.4% !important;
  display:grid !important;
  grid-template-columns:1fr 1fr !important;
  gap:8px !important;
  z-index:30 !important;
  pointer-events:auto !important;
}
#clanScreen .clan-actions #confirmClanBtn,
#clanScreen .clan-actions #startWarBtn{
  position:static !important;
  inset:auto !important;
  width:100% !important;
  min-width:0 !important;
  min-height:36px !important;
  margin:0 !important;
  padding:7px 8px !important;
  font-size:10px !important;
  line-height:1.05 !important;
  white-space:normal !important;
  z-index:31 !important;
  pointer-events:auto !important;
}
#clanScreen .clan-options-grid .clan-option{
  z-index:12 !important;
  pointer-events:auto !important;
}
#clanScreen .clan-options-grid .clan-option:disabled{
  cursor:not-allowed !important;
}
@media (max-height:650px) and (pointer:fine){
  #clanScreen>.card > .clan-options-grid{bottom:27% !important}
  #clanScreen #clanSelectionStatus{bottom:21.7% !important}
  #clanScreen .clan-actions{left:20% !important;right:20% !important;bottom:13.1% !important;gap:6px !important}
  #clanScreen .clan-actions #confirmClanBtn,
  #clanScreen .clan-actions #startWarBtn{min-height:31px !important;font-size:9px !important;padding:5px 6px !important}
}
'''
    anchor='/* EGYPT SHOP + VISUAL TUNING 2026-09-13 */'
    if anchor not in t:
        raise SystemExit('CSS insertion anchor missing')
    t=t.replace(anchor,css+'\n'+anchor,1)


# -----------------------------------------------------------------------------
# 3) Replace the network clan methods as ONE block. Selection is provisional.
#    Confirmation is the only thing that reserves a clan in a real 1x1.
# -----------------------------------------------------------------------------
network_block='''  async setClan(clan){
    if(!this.roomId||!this.localPlayerId)return false;
    const F=await this.waitFirebase(),value=normalizeClan(clan),roomRef=F.ref(F.firebaseDb,`rooms/${this.roomId}`);
    let rejected=false;
    const result=await F.runTransaction(roomRef,current=>{
      if(!current?.players?.[this.localPlayerId]){rejected=true;return}
      const players=current.players||{},humans=Object.values(players),mine=players[this.localPlayerId];
      if(mine.clanConfirmed){rejected=true;return}
      const total=humans.length+Math.max(0,Number(current.npcCount)||0);
      if(total===2&&humans.length===2){
        const other=humans.find(p=>p.uid!==this.localPlayerId);
        if(other?.clanConfirmed&&normalizeClan(other.clan)===value){rejected=true;return}
      }
      mine.clan=value;
      mine.clanChosen=true;
      mine.clanConfirmed=false;
      mine.clanSelectedAt=Date.now();
      return current;
    });
    return !!result.committed&&!rejected;
  },
  async confirmClan(){
    if(!this.roomId||!this.localPlayerId)return false;
    const F=await this.waitFirebase(),roomRef=F.ref(F.firebaseDb,`rooms/${this.roomId}`);
    let rejected=false;
    const result=await F.runTransaction(roomRef,current=>{
      if(!current?.players?.[this.localPlayerId]){rejected=true;return}
      const players=current.players||{},humans=Object.values(players),mine=players[this.localPlayerId];
      if(mine.clanConfirmed)return current;
      const selected=normalizeClan(mine.clan),total=humans.length+Math.max(0,Number(current.npcCount)||0);
      if(total===2&&humans.length===2){
        const other=humans.find(p=>p.uid!==this.localPlayerId);
        if(other?.clanConfirmed&&normalizeClan(other.clan)===selected){rejected=true;return}
        if(other&&!other.clanConfirmed&&normalizeClan(other.clan)===selected){
          other.clan=oppositeClan(selected);
          other.clanChosen=true;
          other.clanConfirmed=false;
          other.clanSelectedAt=Date.now();
        }
      }
      mine.clan=selected;
      mine.clanChosen=true;
      mine.clanConfirmed=true;
      mine.clanConfirmedAt=Date.now();
      return current;
    });
    return !!result.committed&&!rejected;
  },
  async sendInput(input)'''
sub_once(
    r'  async setClan\(clan\)\{.*?\n  async sendInput\(input\)',
    network_block,
    'network clan methods',
    re.S,
)


# -----------------------------------------------------------------------------
# 4) Entering clan selection always begins a fresh ready-state. Existing selected
#    clan may remain highlighted, but nobody is considered confirmed yet.
# -----------------------------------------------------------------------------
new_authority='''function updateLobbyAuthority(){
 const host=NetworkAdapter.isHost;
 $('#lobbyContinue').disabled=NetworkAdapter.online&&!host;
 $('#lobbyContinue').textContent=NetworkAdapter.online&&!host?'Aguardando o host...':'Continuar';
 $$('[data-target="npcs"]').forEach(b=>b.disabled=NetworkAdapter.online&&!host);
 const allConfirmed=allWarClanHumansConfirmed();
 const start=$('#startWarBtn');
 if(start){
   const nonHost=NetworkAdapter.online&&!host;
   start.disabled=nonHost||!allConfirmed;
   start.textContent=!allConfirmed?'Aguardando confirmações...':(nonHost?'Aguardando o host...':'Iniciar preparação');
 }
}'''
sub_once(
    r'function updateLobbyAuthority\(\)\{.*?\n\}\n(?=\$\(\'#lobbyContinue\'\)\.onclick)',
    new_authority+'\n',
    'lobby authority',
    re.S,
)

new_continue='''$('#lobbyContinue').onclick=async()=>{
  if(NetworkAdapter.online&&!NetworkAdapter.isHost)return;
  if(state.mode==='war'){
    if(state.players.length<2){
      state.players.push({id:'p2',name:'Player 2',human:false,local:false,color:COLORS[1],clan:'warriors',clanChosen:true,clanConfirmed:true});
    }
    for(const p of state.players){
      if(p.human){p.clanConfirmed=false;p.clanChosen=false}
      else{p.clanConfirmed=true;p.clanChosen=true}
    }
    const humans=state.players.filter(p=>p.human),bots=state.players.filter(p=>!p.human);
    if(state.players.length===2&&humans.length===1&&bots.length===1)bots[0].clan=oppositeClan(humans[0].clan);
    renderPlayers();
    navigateScreen('clanScreen');
    renderClanSelection();
    if(NetworkAdapter.online){
      const patch={status:'clan',npcCount:bots.length};
      for(const hp of humans){
        patch[`players/${hp.id}/clanConfirmed`]=false;
        patch[`players/${hp.id}/clanChosen`]=false;
      }
      await NetworkAdapter.pushLobbyState(patch);
    }
  } else {
    startPVE();
    if(NetworkAdapter.online)await NetworkAdapter.pushState(serializeGame());
  }
};'''
sub_once(
    r'\$\(\'#lobbyContinue\'\)\.onclick=async\(\)=>\{.*?\n\};(?=\n\n+function oppositeClan)',
    new_continue,
    'enter clan selection handler',
    re.S,
)


# -----------------------------------------------------------------------------
# 5) Replace ALL clan menu helper/handler code as one block, eliminating remnants
#    from v1/v2/v3. Clicking a card ONLY selects. Confirming locks it.
# -----------------------------------------------------------------------------
clean_clan_block='''function oppositeClan(clan){return normalizeClan(clan)==='egypt'?'warriors':'egypt'}
function allWarClanHumansConfirmed(){
 if(state.mode!=='war')return true;
 const humans=state.players.filter(p=>p.human);
 if(!humans.length||humans.some(p=>!p.clanConfirmed))return false;
 if(state.players.length===2&&humans.length===2&&normalizeClan(humans[0].clan)===normalizeClan(humans[1].clan))return false;
 return true;
}
function clanUnavailableForLocal(clan){
 if(state.mode!=='war'||state.players.length!==2)return false;
 const me=localPlayer();if(!me)return false;
 const humans=state.players.filter(p=>p.human),other=humans.find(p=>p.id!==me.id);
 return !!(other?.clanConfirmed&&normalizeClan(other.clan)===normalizeClan(clan));
}
function prepareWarClanAssignments(){
 if(state.mode!=='war')return;
 const humans=state.players.filter(p=>p.human),bots=state.players.filter(p=>!p.human);
 if(state.players.length===2&&humans.length===1&&bots.length===1){
   bots[0].clan=oppositeClan(humans[0].clan);
   bots[0].clanChosen=true;
   bots[0].clanConfirmed=true;
 }else if(state.players.length>=3){
   for(const p of bots){p.clan=Math.random()<.5?'warriors':'egypt';p.clanChosen=true;p.clanConfirmed=true}
 }
}
function renderClanSelection(){
 const me=localPlayer();
 const clan=normalizeClan(me?.clan);
 const confirmed=!!me?.clanConfirmed;
 $$('.clan-option[data-clan]').forEach(btn=>{
   const optionClan=normalizeClan(btn.dataset.clan);
   const unavailable=clanUnavailableForLocal(optionClan);
   btn.classList.toggle('selected',optionClan===clan);
   btn.disabled=confirmed||unavailable;
   btn.setAttribute('aria-disabled',(confirmed||unavailable)?'true':'false');
 });
 const status=$('#clanSelectionStatus');
 if(status)status.textContent=confirmed?`Clã confirmado: ${clanLabel(clan)}`:`Selecionado: ${clanLabel(clan)} • toque em Confirmar clã`;
 const confirm=$('#confirmClanBtn');
 if(confirm){
   confirm.disabled=!me||confirmed;
   confirm.textContent=confirmed?'Confirmado ✓':'Confirmar clã';
 }
 updateLobbyAuthority();
}
$$('.clan-option[data-clan]').forEach(btn=>btn.onclick=async()=>{
 const me=localPlayer();
 if(!me||me.clanConfirmed)return;
 const requestedClan=normalizeClan(btn.dataset.clan);
 if(clanUnavailableForLocal(requestedClan)){renderClanSelection();return}
 const previousClan=normalizeClan(me.clan);
 // Feedback imediato: o clique no card apenas muda a selecao visual/local.
 me.clan=requestedClan;
 me.clanChosen=true;
 me.clanSelectedAt=Date.now();
 const bot=state.players.length===2?state.players.find(p=>!p.human):null;
 if(bot)bot.clan=oppositeClan(requestedClan);
 renderClanSelection();
 configureWarShopForClan();
 if(NetworkAdapter.online){
   try{
     const accepted=await NetworkAdapter.setClan(requestedClan);
     if(!accepted){
       const current=localPlayer();
       if(current&&!current.clanConfirmed)current.clan=previousClan;
       renderClanSelection();
       return;
     }
     const current=localPlayer();
     if(current&&!current.clanConfirmed){current.clan=requestedClan;current.clanChosen=true}
     renderClanSelection();
   }catch(err){
     console.error(err);
     const current=localPlayer();if(current&&!current.clanConfirmed)current.clan=previousClan;
     renderClanSelection();
   }
 }
});
$('#confirmClanBtn').onclick=async()=>{
 const me=localPlayer();if(!me||me.clanConfirmed)return;
 if(NetworkAdapter.online){
   try{
     const accepted=await NetworkAdapter.confirmClan();
     if(!accepted){
       const status=$('#clanSelectionStatus');if(status)status.textContent='Esse clã acabou de ser reservado pelo outro jogador.';
       renderClanSelection();return;
     }
   }catch(err){console.error(err);return}
 }
 const current=localPlayer();if(!current)return;
 current.clanChosen=true;
 current.clanConfirmed=true;
 prepareWarClanAssignments();
 renderClanSelection();
 renderPlayers();
 configureWarShopForClan();
};
function configureWarShopForClan(){'''
sub_once(
    r'function oppositeClan\(clan\)\{.*?\nfunction configureWarShopForClan\(\)\{',
    clean_clan_block,
    'entire clan menu logic block',
    re.S,
)

# -----------------------------------------------------------------------------
# 6) Keep the hard start guard and make its wording/menu refresh deterministic.
# -----------------------------------------------------------------------------
if "if(!allWarClanHumansConfirmed()){renderClanSelection();flash('Todos precisam confirmar o clã.',1.4);return}" not in t:
    raise SystemExit('hard start confirmation guard missing')

# Current Firebase roster mapping must preserve clanConfirmed.
if 'clanConfirmed:!!p.clanConfirmed' not in t:
    raise SystemExit('Firebase clanConfirmed roster mapping missing')

# One-human + NPC reconstruction keeps NPC opposite visually.
# Remove any old premature two-human forcing if it somehow survived.
t=t.replace("const chosen1v1=state.players.filter(p=>p.clanChosen).sort((a,b)=>(a.clanSelectedAt||0)-(b.clanSelectedAt||0))[0];\n   if(state.mode==='war'&&state.players.length===2&&(chosen1v1||bots.length))enforceTwoPlayerClanExclusivity(chosen1v1?.id||humans[0]?.id);\n   ","")

p.write_text(t,encoding='utf-8')

# Strong duplicate / structure validation.
checks={
    'confirm button id': t.count('id="confirmClanBtn"'),
    'start button id': t.count('id="startWarBtn"'),
    'confirm handler': t.count("$('#confirmClanBtn').onclick=async()=>{"),
    'card handler registration': t.count("$$('.clan-option[data-clan]').forEach(btn=>btn.onclick=async()=>{"),
    'renderClanSelection function': t.count('function renderClanSelection(){'),
    'allWarClanHumansConfirmed function': t.count('function allWarClanHumansConfirmed(){'),
    'configureWarShopForClan function': t.count('function configureWarShopForClan(){'),
    'clan actions wrapper': t.count('class="clan-actions"'),
    'v4 css marker': t.count(css_marker),
}
for label,count in checks.items():
    if count!=1:
        raise SystemExit(f'{label}: expected exactly 1, found {count}')

required=[
    "me.clan=requestedClan;",
    "const accepted=await NetworkAdapter.setClan(requestedClan);",
    "const accepted=await NetworkAdapter.confirmClan();",
    "other&&!other.clanConfirmed&&normalizeClan(other.clan)===selected",
    "bots[0].clan=oppositeClan(humans[0].clan);",
    "patch[`players/${hp.id}/clanConfirmed`]=false;",
    "start.disabled=nonHost||!allConfirmed;",
    "#clanScreen .clan-actions #startWarBtn",
]
missing=[x for x in required if x not in t]
if missing:
    raise SystemExit('Missing clan v4 requirements: '+repr(missing))
if 'enforceTwoPlayerClanExclusivity(' in t:
    raise SystemExit('Old enforceTwoPlayerClanExclusivity still remains')
print('Clan menu v4 rebuilt cleanly with no duplicate handlers/buttons.')
