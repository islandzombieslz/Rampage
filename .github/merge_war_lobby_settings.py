from pathlib import Path
import re

p=Path('index.html')
t=p.read_text(encoding='utf-8')

MARK='/* WAR LOBBY COMBINED SETTINGS 2026-09-17 */'
if MARK in t:
    print('Unified War lobby already present.')
    raise SystemExit(0)

# 1) Remove the separate Mestre da Guerra configuration block.
old_war_config='''
    <div id="warConfig" class="stack" style="display:none">
      <div class="config">
        <div class="label">Tempo de cada guerra</div>
        <div class="row option-group" data-setting="warTime">
          <button data-value="120" class="selected">2 min</button>
          <button data-value="180">3 min</button>
        </div>
      </div>
      <div class="config">
        <div class="label">Rodadas</div>
        <div class="counter"><button class="minus" data-target="rounds">−</button><b id="roundsVal2">2</b><button class="plus" data-target="rounds">+</button></div>
      </div>
      <div class="config">
        <div class="label">Gemas iniciais por jogador</div>
        <div class="counter"><button class="minus" data-target="gems">−</button><b id="gemsVal">500</b><button class="plus" data-target="gems">+</button></div>
      </div>
    </div>'''
if old_war_config not in t:
    raise SystemExit('Old separate warConfig block not found')
t=t.replace(old_war_config,'',1)

# 2) Put War settings directly in the room/lobby, above NPCs.
old_lobby_anchor='''      <div class="player-list" id="playerList"></div>
      <div class="player-item lobby-npc-row">'''
new_lobby_anchor='''      <div class="player-list" id="playerList"></div>
      <div id="warLobbySettings" aria-label="Configurações do Mestre da Guerra">
        <div class="war-lobby-top-row">
          <div class="war-lobby-setting war-time-setting">
            <div class="label">Tempo de cada guerra</div>
            <div class="row option-group" data-setting="warTime">
              <button data-value="120" class="selected">2 min</button>
              <button data-value="180">3 min</button>
            </div>
          </div>
          <div class="war-lobby-setting">
            <div class="label">Rodadas</div>
            <div class="counter"><button class="minus" data-target="rounds">−</button><b id="roundsVal2">2</b><button class="plus" data-target="rounds">+</button></div>
          </div>
        </div>
        <div class="war-lobby-setting war-gems-setting">
          <div class="label">Gemas iniciais</div>
          <div class="counter"><button class="minus" data-target="gems">−</button><b id="gemsVal">500</b><button class="plus" data-target="gems">+</button></div>
        </div>
      </div>
      <div class="player-item lobby-npc-row">'''
if old_lobby_anchor not in t:
    raise SystemExit('Lobby insertion anchor not found')
t=t.replace(old_lobby_anchor,new_lobby_anchor,1)

old_actions='''    <div class="row lobby-actions">
      <button data-back="menuScreen">Sair</button>
      <button id="lobbyContinue" class="primary">Continuar</button>
    </div>'''
new_actions='''    <div class="row lobby-actions">
      <button data-back="modeScreen">Voltar</button>
      <button id="lobbyContinue" class="primary">Continuar</button>
    </div>'''
if old_actions not in t:
    raise SystemExit('Lobby actions anchor not found')
t=t.replace(old_actions,new_actions,1)

# 3) One compact visual layout inside the existing Mestre da Guerra sprite.
css=r'''

/* WAR LOBBY COMBINED SETTINGS 2026-09-17 */
#lobbyScreen #warLobbySettings{
  display:none !important;
}
#lobbyScreen.war-lobby .lobby-content{
  gap:4px !important;
}
#lobbyScreen.war-lobby #playerList{
  flex:0 1 auto !important;
  max-height:76px !important;
  min-height:26px !important;
}
#lobbyScreen.war-lobby #warLobbySettings{
  flex:0 0 auto !important;
  width:100% !important;
  display:grid !important;
  gap:4px !important;
  margin:0 !important;
  padding:0 !important;
}
#lobbyScreen.war-lobby .war-lobby-top-row{
  display:grid !important;
  grid-template-columns:minmax(0,1.45fr) minmax(0,.9fr) !important;
  gap:5px !important;
}
#lobbyScreen.war-lobby .war-lobby-setting{
  min-width:0 !important;
  display:grid !important;
  grid-template-columns:minmax(0,1fr) auto !important;
  align-items:center !important;
  gap:5px !important;
  padding:4px 6px !important;
  margin:0 !important;
  border-radius:8px !important;
  background:rgba(8,12,16,.28) !important;
  border:1px solid rgba(255,255,255,.10) !important;
}
#lobbyScreen.war-lobby .war-lobby-top-row .war-lobby-setting{
  grid-template-columns:1fr !important;
  gap:3px !important;
  text-align:center !important;
}
#lobbyScreen.war-lobby .war-lobby-setting .label{
  min-width:0 !important;
  margin:0 !important;
  font-size:8.7px !important;
  line-height:1.05 !important;
  color:#f0f6fc !important;
  font-weight:800 !important;
  white-space:nowrap !important;
}
#lobbyScreen.war-lobby .war-time-setting .option-group{
  display:grid !important;
  grid-template-columns:repeat(2,minmax(0,1fr)) !important;
  width:100% !important;
  gap:4px !important;
}
#lobbyScreen.war-lobby .war-time-setting .option-group button{
  min-width:0 !important;
  width:100% !important;
  min-height:24px !important;
  height:24px !important;
  padding:2px 4px !important;
  margin:0 !important;
  font-size:8.7px !important;
  border-radius:6px !important;
}
#lobbyScreen.war-lobby #warLobbySettings .counter,
#lobbyScreen.war-lobby .lobby-npc-row .counter{
  display:grid !important;
  grid-template-columns:27px 34px 27px !important;
  align-items:center !important;
  justify-content:center !important;
  gap:4px !important;
  margin:0 !important;
}
#lobbyScreen.war-lobby #warLobbySettings .counter button{
  width:27px !important;
  min-width:27px !important;
  height:25px !important;
  min-height:25px !important;
  padding:0 !important;
  font-size:12px !important;
  border-radius:6px !important;
}
#lobbyScreen.war-lobby #warLobbySettings .counter b{
  width:34px !important;
  min-width:34px !important;
  text-align:center !important;
  font-size:11px !important;
}
#lobbyScreen.war-lobby .lobby-npc-row{
  flex:0 0 auto !important;
  min-height:31px !important;
}
#lobbyScreen.war-lobby #participantLimitHint{
  font-size:7.3px !important;
  line-height:1 !important;
}
@media (max-height:650px) and (pointer:fine){
  #lobbyScreen.war-lobby #playerList{max-height:61px !important}
  #lobbyScreen.war-lobby .war-lobby-setting{padding:3px 5px !important}
  #lobbyScreen.war-lobby .war-lobby-setting .label{font-size:8px !important}
  #lobbyScreen.war-lobby .war-time-setting .option-group button{height:21px !important;min-height:21px !important;font-size:8px !important}
  #lobbyScreen.war-lobby #warLobbySettings .counter button{height:22px !important;min-height:22px !important}
  #lobbyScreen.war-lobby .lobby-npc-row{min-height:27px !important}
}
'''
style_anchor='\n</style>\n\n<script type="module">'
if style_anchor not in t:
    raise SystemExit('Final style anchor missing')
t=t.replace(style_anchor,css+style_anchor,1)

# 4) Mestre da Guerra now creates the room directly from the mode screen.
old_configure="""$('#configureBtn').onclick=()=>{
  $('#pveConfig').style.display=state.mode==='pve'?'grid':'none';
  $('#warConfig').style.display=state.mode==='war'?'grid':'none';
  $('#configTitle').textContent=state.mode==='pve'?'Configurar Players vs Inimigos':'Configurar Mestre da Guerra';
  const configScreen=$('#configScreen');
  configScreen.classList.toggle('pve-config',state.mode==='pve');
  configScreen.classList.toggle('war-config',state.mode==='war');
  navigateScreen('configScreen');
};"""
new_configure="""$('#configureBtn').onclick=async()=>{
  if(state.mode==='war'){
    await createCurrentRoom($('#configureBtn'));
    return;
  }
  $('#pveConfig').style.display='grid';
  $('#configTitle').textContent='Configurar Players vs Inimigos';
  const configScreen=$('#configScreen');
  configScreen.classList.add('pve-config');
  configScreen.classList.remove('war-config');
  navigateScreen('configScreen');
};"""
if old_configure not in t:
    raise SystemExit('configureBtn handler anchor not found')
t=t.replace(old_configure,new_configure,1)

# 5) Host settings in the combined lobby are mirrored live to Firebase.
old_option="""$$('.option-group button').forEach(b=>b.onclick=()=>{
  const group=b.parentElement; group.querySelectorAll('button').forEach(x=>x.classList.remove('selected')); b.classList.add('selected');
  state[group.dataset.setting]=isNaN(b.dataset.value)?b.dataset.value:Number(b.dataset.value);
});"""
new_option="""let warLobbySettingsSyncTimer=null;
function scheduleWarLobbySettingsSync(){
  if(!NetworkAdapter.online||!NetworkAdapter.isHost||state.mode!=='war')return;
  clearTimeout(warLobbySettingsSyncTimer);
  warLobbySettingsSyncTimer=setTimeout(()=>{
    NetworkAdapter.pushLobbyState({
      'settings/warTime':state.warTime,
      'settings/rounds':state.rounds,
      'settings/gems':normalizeWarStartingGems(state.gems)
    }).catch(console.error);
  },90);
}
$$('.option-group button').forEach(b=>b.onclick=()=>{
  const group=b.parentElement; group.querySelectorAll('button').forEach(x=>x.classList.remove('selected')); b.classList.add('selected');
  state[group.dataset.setting]=isNaN(b.dataset.value)?b.dataset.value:Number(b.dataset.value);
  if(b.closest('#warLobbySettings'))scheduleWarLobbySettingsSync();
});"""
if old_option not in t:
    raise SystemExit('option group handler anchor not found')
t=t.replace(old_option,new_option,1)

old_step="""  if(b.dataset.target==='rounds') state.rounds=clamp(state.rounds+dir,2,10);
  if(b.dataset.target==='gems') state.gems=normalizeWarStartingGems((Number(state.gems)||300)+dir*100);

  if(b.dataset.target==='npcs'){"""
new_step="""  if(b.dataset.target==='rounds') state.rounds=clamp(state.rounds+dir,2,10);
  if(b.dataset.target==='gems') state.gems=normalizeWarStartingGems((Number(state.gems)||300)+dir*100);
  if((b.dataset.target==='rounds'||b.dataset.target==='gems')&&b.closest('#warLobbySettings'))scheduleWarLobbySettingsSync();

  if(b.dataset.target==='npcs'){"""
if old_step not in t:
    raise SystemExit('stepper settings anchor missing')
t=t.replace(old_step,new_step,1)

# 6) Reuse one room-creation function for PVE and quick War creation.
pattern=r"let roomCreateInFlight=false,roomJoinInFlight=false;\n\$\('#createRoomBtn'\)\.onclick=async\(\)=>\{.*?\n\};\n(?=\$\('#confirmJoin'\)\.onclick=async\(\)=>\{)"
replacement="""let roomCreateInFlight=false,roomJoinInFlight=false;
async function createCurrentRoom(btn){
  if(roomCreateInFlight)return false;
  roomCreateInFlight=true;
  const oldText=btn?.textContent||'';
  if(btn){btn.disabled=true;btn.textContent='Criando...'}
  try{
    state.gems=normalizeWarStartingGems(state.gems);
    const roomSnapshot={...state,gems:state.gems};
    const res=await NetworkAdapter.createRoom(roomSnapshot);
    state.roomCode=res.code;
    $('#roomCode').textContent=res.code;
    $('#lobbyModeTitle').textContent=state.mode==='pve'?'Players vs Inimigos':'Mestre da Guerra';
    setLobbySkin(state.mode);
    renderWarLobbySettings();
    renderPlayers();
    navigateScreen('lobbyScreen');
    return true;
  }catch(err){
    console.error(err);flash('Não foi possível criar a sala.',1.5);return false;
  }finally{
    roomCreateInFlight=false;
    if(btn){btn.textContent=oldText;btn.disabled=false}
  }
}
$('#createRoomBtn').onclick=()=>createCurrentRoom($('#createRoomBtn'));
"""
t,count=re.subn(pattern,replacement,t,count=1,flags=re.S)
if count!=1:
    raise SystemExit(f'create room handler replacement failed: {count}')

# 7) Keep the combined controls reflecting the authoritative room settings.
old_skin="""function setLobbySkin(mode=state.mode){
  const lobby=$('#lobbyScreen');
  if(!lobby)return;
  const war=mode==='war';
  lobby.classList.toggle('war-lobby',war);
  lobby.classList.toggle('pve-lobby',!war);
}"""
new_skin="""function renderWarLobbySettings(){
  const box=$('#warLobbySettings');if(!box)return;
  $$('#warLobbySettings [data-setting=\"warTime\"] button').forEach(btn=>btn.classList.toggle('selected',Number(btn.dataset.value)===Number(state.warTime)));
  const rounds=$('#roundsVal2');if(rounds)rounds.textContent=state.rounds;
  const gems=$('#gemsVal');if(gems)gems.textContent=normalizeWarStartingGems(state.gems);
}
function setLobbySkin(mode=state.mode){
  const lobby=$('#lobbyScreen');
  if(!lobby)return;
  const war=mode==='war';
  lobby.classList.toggle('war-lobby',war);
  lobby.classList.toggle('pve-lobby',!war);
  renderWarLobbySettings();
}"""
if old_skin not in t:
    raise SystemExit('setLobbySkin anchor missing')
t=t.replace(old_skin,new_skin,1)

old_render_end="""  if(limitHint)limitHint.textContent=state.mode==='war'
    ? 'Máximo de 3 participantes/clãs no modo Guerra, contando jogadores e NPCs.'
    : 'Máximo de 10 participantes no Players vs Inimigos.';
}"""
new_render_end="""  if(limitHint)limitHint.textContent=state.mode==='war'
    ? 'Máximo de 3 participantes/clãs no modo Guerra, contando jogadores e NPCs.'
    : 'Máximo de 10 participantes no Players vs Inimigos.';
  renderWarLobbySettings();
}"""
if old_render_end not in t:
    raise SystemExit('renderPlayers end anchor missing')
t=t.replace(old_render_end,new_render_end,1)

old_authority=""" $$('[data-target=\"npcs\"]').forEach(b=>b.disabled=NetworkAdapter.online&&!host);
 const allConfirmed=allWarClanHumansConfirmed();"""
new_authority=""" $$('[data-target=\"npcs\"]').forEach(b=>b.disabled=NetworkAdapter.online&&!host);
 $$('#warLobbySettings button').forEach(b=>b.disabled=NetworkAdapter.online&&!host);
 const allConfirmed=allWarClanHumansConfirmed();"""
if old_authority not in t:
    raise SystemExit('lobby authority anchor missing')
t=t.replace(old_authority,new_authority,1)

old_sync="""   state.gems=normalizeWarStartingGems(room.settings.gems??state.gems);
   const gemsLabel=$('#gemsVal');if(gemsLabel)gemsLabel.textContent=state.gems;
 }"""
new_sync="""   state.gems=normalizeWarStartingGems(room.settings.gems??state.gems);
   const gemsLabel=$('#gemsVal');if(gemsLabel)gemsLabel.textContent=state.gems;
   renderWarLobbySettings();
 }"""
if old_sync not in t:
    raise SystemExit('Firebase settings sync anchor missing')
t=t.replace(old_sync,new_sync,1)

# Final consistency checks.
required=[
    MARK,
    'id="warLobbySettings"',
    'id="roundsVal2"',
    'id="gemsVal"',
    "await createCurrentRoom($('#configureBtn'));",
    "'settings/warTime':state.warTime",
    "'settings/rounds':state.rounds",
    "'settings/gems':normalizeWarStartingGems(state.gems)",
    'function renderWarLobbySettings(){',
    "$$('#warLobbySettings button').forEach",
    '<button data-back="modeScreen">Voltar</button>',
]
missing=[x for x in required if x not in t]
if missing:
    raise SystemExit('Missing unified War lobby markers: '+repr(missing))
if 'id="warConfig"' in t:
    raise SystemExit('Separate warConfig menu still exists')
if t.count('id="roundsVal2"')!=1 or t.count('id="gemsVal"')!=1 or t.count('id="warLobbySettings"')!=1:
    raise SystemExit('Duplicate unified War lobby IDs detected')

p.write_text(t,encoding='utf-8')
print('Mestre da Guerra now creates directly into one combined online lobby.')
