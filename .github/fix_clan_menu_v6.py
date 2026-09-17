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

# Remove the two conflicting action-layout blocks completely.
sub_once(
    r'\n*/\* CLAN MENU V4 FIX 2026-09-17 \*/.*?(?=/\* CLAN MENU V5 DEFINITIVE LAYOUT 2026-09-17 \*/)',
    '\n\n',
    'remove V4 clan layout',
    re.S,
)

v6_css=r'''/* CLAN MENU V6 SINGLE ACTION LAYOUT 2026-09-17 */
#clanScreen>.card > .clan-options-grid{
  bottom:27% !important;
}
#clanScreen #clanSelectionStatus{
  position:absolute !important;
  left:22% !important;
  right:22% !important;
  bottom:20.2% !important;
  width:auto !important;
  margin:0 !important;
  text-align:center !important;
  z-index:40 !important;
  pointer-events:none !important;
}
#clanScreen>.card > .clan-actions{
  position:absolute !important;
  left:22% !important;
  right:22% !important;
  bottom:12.3% !important;
  width:auto !important;
  height:auto !important;
  margin:0 !important;
  padding:0 !important;
  display:grid !important;
  grid-template-columns:1fr 1fr !important;
  gap:8px !important;
  z-index:60 !important;
  pointer-events:auto !important;
}
#clanScreen>.card > .clan-actions > #confirmClanBtn,
#clanScreen>.card > .clan-actions > #startWarBtn{
  position:static !important;
  inset:auto !important;
  left:auto !important;
  right:auto !important;
  top:auto !important;
  bottom:auto !important;
  display:block !important;
  width:100% !important;
  max-width:none !important;
  min-width:0 !important;
  min-height:36px !important;
  height:auto !important;
  margin:0 !important;
  padding:7px 8px !important;
  font-size:9.5px !important;
  line-height:1.08 !important;
  white-space:normal !important;
  transform:none !important;
  z-index:61 !important;
  pointer-events:auto !important;
}
#clanScreen>.card > .clan-actions > #confirmClanBtn:not(:disabled),
#clanScreen>.card > .clan-actions > #startWarBtn:not(:disabled){
  cursor:pointer !important;
}
@media (max-height:650px) and (pointer:fine){
  #clanScreen>.card > .clan-options-grid{bottom:28% !important}
  #clanScreen #clanSelectionStatus{bottom:20.8% !important;font-size:7.4px !important}
  #clanScreen>.card > .clan-actions{left:21% !important;right:21% !important;bottom:12% !important;gap:6px !important}
  #clanScreen>.card > .clan-actions > #confirmClanBtn,
  #clanScreen>.card > .clan-actions > #startWarBtn{min-height:31px !important;font-size:8.2px !important;padding:5px 6px !important}
}

'''
sub_once(
    r'/\* CLAN MENU V5 DEFINITIVE LAYOUT 2026-09-17 \*/.*?(?=/\* EGYPT SHOP \+ VISUAL TUNING 2026-09-13 \*/)',
    v6_css,
    'replace V5 with single V6 clan layout',
    re.S,
)

# Add an explicit in-flight flag so confirmation cannot double-fire and the UI shows progress.
if 'let clanConfirmInFlight=false;' not in t:
    t=t.replace('let clanDraft=null;','let clanDraft=null;\nlet clanConfirmInFlight=false;',1)

old_render=""" const confirm=$('#confirmClanBtn');
 if(confirm){confirm.disabled=confirmed;confirm.textContent=confirmed?'Confirmado ✓':'Confirmar clã'}
 updateLobbyAuthority();"""
new_render=""" const confirm=$('#confirmClanBtn');
 if(confirm){
   confirm.disabled=confirmed||clanConfirmInFlight;
   confirm.textContent=confirmed?'Confirmado ✓':(clanConfirmInFlight?'Confirmando...':'Confirmar clã');
 }
 updateLobbyAuthority();"""
if old_render not in t:
    raise SystemExit('confirm render anchor missing')
t=t.replace(old_render,new_render,1)

old_handler="""$('#confirmClanBtn').onclick=async()=>{
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
};"""
new_handler="""$('#confirmClanBtn').onclick=async()=>{
 const me=localPlayer();if(!me||me.clanConfirmed||clanConfirmInFlight)return;
 const selected=normalizeClan(clanDraft??me.clan);
 if(clanUnavailableForLocal(selected)){renderClanSelection();return}
 clanConfirmInFlight=true;
 renderClanSelection();
 try{
   if(NetworkAdapter.online){
     const ok=await NetworkAdapter.confirmClan(selected);
     if(!ok){flash('Não foi possível confirmar esse clã.',1.4);return}
   }
   const current=localPlayer();if(!current)return;
   current.clan=selected;
   current.clanChosen=true;
   current.clanConfirmed=true;
   clanDraft=selected;
   prepareWarClanAssignments();
   renderPlayers();
   configureWarShopForClan();
 }catch(err){
   console.error(err);
   flash('Falha ao confirmar o clã.',1.4);
 }finally{
   clanConfirmInFlight=false;
   renderClanSelection();
 }
};"""
if old_handler not in t:
    raise SystemExit('confirm handler anchor missing')
t=t.replace(old_handler,new_handler,1)

# Validate that only V6 remains and all controls are unique.
for forbidden in ['/* CLAN MENU V4 FIX 2026-09-17 */','/* CLAN MENU V5 DEFINITIVE LAYOUT 2026-09-17 */']:
    if forbidden in t:
        raise SystemExit('Old conflicting clan CSS remains: '+forbidden)
required=[
    '/* CLAN MENU V6 SINGLE ACTION LAYOUT 2026-09-17 */',
    '#clanScreen>.card > .clan-actions{',
    '#clanScreen>.card > .clan-actions > #confirmClanBtn,',
    'let clanConfirmInFlight=false;',
    "confirm.textContent=confirmed?'Confirmado ✓':(clanConfirmInFlight?'Confirmando...':'Confirmar clã');",
    "const ok=await NetworkAdapter.confirmClan(selected);",
    "current.clanConfirmed=true;",
    "clanConfirmInFlight=false;",
]
missing=[x for x in required if x not in t]
if missing:
    raise SystemExit('Missing V6 clan repair: '+repr(missing))
checks={
    'confirm HTML':t.count('id="confirmClanBtn"'),
    'start HTML':t.count('id="startWarBtn"'),
    'confirm handler':t.count("$('#confirmClanBtn').onclick=async()=>{"),
    'card handler':t.count("$$('.clan-option[data-clan]').forEach(btn=>btn.onclick=()=>{"),
    'render':t.count('function renderClanSelection(){'),
}
for label,count in checks.items():
    if count!=1:
        raise SystemExit(f'{label}: expected 1, found {count}')

p.write_text(t,encoding='utf-8')
print('Clan menu V6 layout and confirmation flow repaired.')
