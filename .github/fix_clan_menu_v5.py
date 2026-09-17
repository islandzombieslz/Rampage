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

# --- CSS: direct button selectors, independent of wrapper structure. ---
marker='/* CLAN MENU V5 DEFINITIVE LAYOUT 2026-09-17 */'
if marker not in t:
    css=r'''

/* CLAN MENU V5 DEFINITIVE LAYOUT 2026-09-17 */
#clanScreen>.card > .clan-options-grid{
  bottom:27.2% !important;
}
#clanScreen #clanSelectionStatus{
  position:absolute !important;
  left:22% !important;
  right:22% !important;
  bottom:21.7% !important;
  z-index:40 !important;
  pointer-events:none !important;
  text-align:center !important;
}
#clanScreen .clan-actions{
  position:static !important;
  display:block !important;
  pointer-events:none !important;
}
#clanScreen #confirmClanBtn,
#clanScreen #startWarBtn{
  position:absolute !important;
  top:auto !important;
  bottom:14.2% !important;
  width:27.5% !important;
  min-width:0 !important;
  min-height:34px !important;
  height:auto !important;
  margin:0 !important;
  padding:7px 7px !important;
  font-size:9.5px !important;
  line-height:1.1 !important;
  white-space:normal !important;
  z-index:50 !important;
  pointer-events:auto !important;
}
#clanScreen #confirmClanBtn{
  left:21% !important;
  right:auto !important;
}
#clanScreen #startWarBtn{
  left:auto !important;
  right:21% !important;
}
#clanScreen .clan-options-grid,
#clanScreen .clan-options-grid .clan-option{
  pointer-events:auto !important;
}
#clanScreen .clan-options-grid .clan-option{z-index:30 !important}
@media (max-height:650px) and (pointer:fine){
  #clanScreen>.card > .clan-options-grid{bottom:28% !important}
  #clanScreen #clanSelectionStatus{bottom:22.1% !important;font-size:7.4px !important}
  #clanScreen #confirmClanBtn,#clanScreen #startWarBtn{bottom:14% !important;min-height:30px !important;font-size:8.2px !important;padding:5px !important}
  #clanScreen #confirmClanBtn{left:20% !important}
  #clanScreen #startWarBtn{right:20% !important}
}
'''
    anchor='/* EGYPT SHOP + VISUAL TUNING 2026-09-13 */'
    if anchor not in t:
        raise SystemExit('CSS insertion anchor missing')
    t=t.replace(anchor,css+'\n'+anchor,1)

# --- Network selection methods: confirmation receives the exact visible draft. ---
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
      mine.clan=value;mine.clanChosen=true;mine.clanConfirmed=false;mine.clanSelectedAt=Date.now();
      return current;
    });
    return !!result.committed&&!rejected;
  },
  async confirmClan(clan){
    if(!this.roomId||!this.localPlayerId)return false;
    const F=await this.waitFirebase(),selected=normalizeClan(clan),roomRef=F.ref(F.firebaseDb,`rooms/${this.roomId}`);
    let rejected=false;
    const result=await F.runTransaction(roomRef,current=>{
      if(!current?.players?.[this.localPlayerId]){rejected=true;return}
      const players=current.players||{},humans=Object.values(players),mine=players[this.localPlayerId];
      if(mine.clanConfirmed)return current;
      const total=humans.length+Math.max(0,Number(current.npcCount)||0);
      if(total===2&&humans.length===2){
        const other=humans.find(p=>p.uid!==this.localPlayerId);
        if(other?.clanConfirmed&&normalizeClan(other.clan)===selected){rejected=true;return}
        if(other&&!other.clanConfirmed&&normalizeClan(other.clan)===selected){
          other.clan=oppositeClan(selected);other.clanChosen=true;other.clanConfirmed=false;other.clanSelectedAt=Date.now();
        }
      }
      mine.clan=selected;mine.clanChosen=true;mine.clanConfirmed=true;mine.clanSelectedAt=Date.now();mine.clanConfirmedAt=Date.now();
      return current;
    });
    return !!result.committed&&!rejected;
  },
  async sendInput(input)'''
sub_once(r'  async setClan\(clan\)\{.*?\n  async sendInput\(input\)',network_block,'network clan API',re.S)

# --- Entering clan screen resets only readiness and the local visual draft. ---
sub_once(
    r"renderPlayers\(\);\n    navigateScreen\('clanScreen'\);\n    renderClanSelection\(\);",
    "renderPlayers();\n    navigateScreen('clanScreen');\n    resetClanDraft();\n    renderClanSelection();",
    'reset clan draft on screen entry',
)

# --- Replace the whole selection helper/handler block, once. ---
clean_block=r'''let clanDraft=null;
function oppositeClan(clan){return normalizeClan(clan)==='egypt'?'warriors':'egypt'}
function resetClanDraft(){
 const me=localPlayer();
 clanDraft=normalizeClan(me?.clan||'warriors');
}
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
 const other=state.players.find(p=>p.human&&p.id!==me.id);
 return !!(other?.clanConfirmed&&normalizeClan(other.clan)===normalizeClan(clan));
}
function prepareWarClanAssignments(){
 if(state.mode!=='war')return;
 const humans=state.players.filter(p=>p.human),bots=state.players.filter(p=>!p.human);
 if(state.players.length===2&&humans.length===1&&bots.length===1){
   bots[0].clan=oppositeClan(humans[0].clan);bots[0].clanChosen=true;bots[0].clanConfirmed=true;
 }else if(state.players.length>=3){
   for(const p of bots){p.clan=Math.random()<.5?'warriors':'egypt';p.clanChosen=true;p.clanConfirmed=true}
 }
}
function renderClanSelection(){
 const me=localPlayer();
 if(!me)return;
 const confirmed=!!me.clanConfirmed;
 if(clanDraft==null)clanDraft=normalizeClan(me.clan);
 // If the opponent just confirmed our draft, the Firebase transaction moves us to
 // the other clan. Follow that authoritative reassignment immediately.
 if(!confirmed&&clanUnavailableForLocal(clanDraft))clanDraft=normalizeClan(me.clan);
 if(!confirmed&&clanUnavailableForLocal(clanDraft))clanDraft=oppositeClan(state.players.find(p=>p.human&&p.id!==me.id)?.clan);
 const shownClan=confirmed?normalizeClan(me.clan):normalizeClan(clanDraft);
 $$('.clan-option[data-clan]').forEach(btn=>{
   const optionClan=normalizeClan(btn.dataset.clan),unavailable=clanUnavailableForLocal(optionClan);
   btn.classList.toggle('selected',optionClan===shownClan);
   btn.disabled=confirmed||unavailable;
   btn.setAttribute('aria-disabled',(confirmed||unavailable)?'true':'false');
 });
 const status=$('#clanSelectionStatus');
 if(status)status.textContent=confirmed?`Clã confirmado: ${clanLabel(shownClan)}`:`Selecionado: ${clanLabel(shownClan)}`;
 const confirm=$('#confirmClanBtn');
 if(confirm){confirm.disabled=confirmed;confirm.textContent=confirmed?'Confirmado ✓':'Confirmar clã'}
 updateLobbyAuthority();
}
$$('.clan-option[data-clan]').forEach(btn=>btn.onclick=()=>{
 const me=localPlayer();if(!me||me.clanConfirmed)return;
 const selected=normalizeClan(btn.dataset.clan);
 if(clanUnavailableForLocal(selected))return;
 clanDraft=selected;
 me.clan=selected;me.clanChosen=true;me.clanSelectedAt=Date.now();
 const bot=state.players.length===2?state.players.find(p=>!p.human):null;
 if(bot)bot.clan=oppositeClan(selected);
 renderClanSelection();configureWarShopForClan();
 // Selection stays visually local immediately; Firebase mirrors it in the background.
 if(NetworkAdapter.online)NetworkAdapter.setClan(selected).then(ok=>{
   if(!ok&&localPlayer()&&!localPlayer().clanConfirmed){clanDraft=normalizeClan(localPlayer().clan);renderClanSelection()}
 }).catch(console.error);
});
$('#confirmClanBtn').onclick=async()=>{
 const me=localPlayer();if(!me||me.clanConfirmed)return;
 const selected=normalizeClan(clanDraft??me.clan);
 if(clanUnavailableForLocal(selected)){renderClanSelection();return}
 if(NetworkAdapter.online){
   try{
     const ok=await NetworkAdapter.confirmClan(selected);
     if(!ok){renderClanSelection();return}
   }catch(err){console.error(err);return}
 }
 const current=localPlayer();if(!current)return;
 current.clan=selected;current.clanChosen=true;current.clanConfirmed=true;
 clanDraft=selected;
 prepareWarClanAssignments();
 renderClanSelection();renderPlayers();configureWarShopForClan();
};
function configureWarShopForClan(){'''
sub_once(r'(?:let clanDraft=null;\n)?function oppositeClan\(clan\)\{.*?\nfunction configureWarShopForClan\(\)\{',clean_block,'complete clan UI logic',re.S)

# Validation: one set of handlers/functions and direct CSS guaranteed.
required=[
    '/* CLAN MENU V5 DEFINITIVE LAYOUT 2026-09-17 */',
    '#clanScreen #confirmClanBtn,',
    '#clanScreen #startWarBtn{',
    'let clanDraft=null;',
    'function resetClanDraft()',
    "$('#confirmClanBtn').onclick=async()=>{",
    "NetworkAdapter.confirmClan(selected)",
    "$$('.clan-option[data-clan]').forEach(btn=>btn.onclick=()=>{",
    "if(!confirmed&&clanUnavailableForLocal(clanDraft))clanDraft=normalizeClan(me.clan);",
]
missing=[x for x in required if x not in t]
if missing: raise SystemExit('Missing v5 clan repair: '+repr(missing))
checks={
    'confirm button HTML':t.count('id="confirmClanBtn"'),
    'start button HTML':t.count('id="startWarBtn"'),
    'confirm handler':t.count("$('#confirmClanBtn').onclick=async()=>{"),
    'card handler':t.count("$$('.clan-option[data-clan]').forEach(btn=>btn.onclick=()=>{"),
    'render function':t.count('function renderClanSelection(){'),
    'draft declaration':t.count('let clanDraft=null;'),
}
for label,count in checks.items():
    if count!=1: raise SystemExit(f'{label}: expected 1, found {count}')

p.write_text(t,encoding='utf-8')
print('Clan menu v5 deterministic selection/layout applied.')
