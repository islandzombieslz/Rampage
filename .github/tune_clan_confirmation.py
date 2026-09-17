from pathlib import Path

p=Path('index.html')
t=p.read_text(encoding='utf-8')


def replace_once(old,new,label):
    global t
    if new in t:
        return
    count=t.count(old)
    if count!=1:
        raise SystemExit(f'{label}: expected 1 old anchor, found {count}')
    t=t.replace(old,new,1)


def replace_all_exact(old,new,expected,label):
    global t
    if new in t and old not in t:
        return
    count=t.count(old)
    if count!=expected:
        raise SystemExit(f'{label}: expected {expected} old anchors, found {count}')
    t=t.replace(old,new)


# -----------------------------------------------------------------------------
# Clan state now has an explicit confirmation flag.
# -----------------------------------------------------------------------------
replace_all_exact(
    "clan:'warriors',clanChosen:false,clanSelectedAt:0,joinedAt:F.serverTimestamp(),lastSeen:F.serverTimestamp()",
    "clan:'warriors',clanChosen:false,clanConfirmed:false,clanSelectedAt:0,joinedAt:F.serverTimestamp(),lastSeen:F.serverTimestamp()",
    2,
    'initial online clan confirmation state',
)

# Selection is provisional. Only confirmation reserves a clan in a 1x1.
old_set_clan="""  async setClan(clan){
    if(!this.roomId||!this.localPlayerId)return false;
    const F=await this.waitFirebase(),value=normalizeClan(clan),roomRef=F.ref(F.firebaseDb,`rooms/${this.roomId}`);
    let rejected=false;
    const result=await F.runTransaction(roomRef,current=>{
      if(!current?.players?.[this.localPlayerId]){rejected=true;return}
      const players=current.players||{},humans=Object.values(players),total=humans.length+Math.max(0,Number(current.npcCount)||0);
      const mine=players[this.localPlayerId];
      if(total===2&&humans.length===2){
        const other=humans.find(p=>p.uid!==this.localPlayerId);
        if(other?.clanChosen&&normalizeClan(other.clan)===value){rejected=true;return}
        if(other&&!other.clanChosen)other.clan=value==='egypt'?'warriors':'egypt';
      }
      mine.clan=value;mine.clanChosen=true;mine.clanSelectedAt=Date.now();
      return current;
    });
    return !!result.committed&&!rejected;
  },"""
new_set_clan="""  async setClan(clan){
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
        // A selecao continua livre ate alguem CONFIRMAR. Depois disso o cla
        // confirmado fica reservado e nao pode ser selecionado pelo adversario.
        if(other?.clanConfirmed&&normalizeClan(other.clan)===value){rejected=true;return}
      }
      mine.clan=value;mine.clanChosen=true;mine.clanConfirmed=false;mine.clanSelectedAt=Date.now();
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
        // Se o outro apenas estava apontando para o mesmo cla, a confirmacao deste
        // jogador ganha a reserva e move a selecao provisoria do outro para o livre.
        if(other&&!other.clanConfirmed&&normalizeClan(other.clan)===selected){
          other.clan=selected==='egypt'?'warriors':'egypt';
          other.clanChosen=true;other.clanSelectedAt=Date.now();
        }
      }
      mine.clan=selected;mine.clanChosen=true;mine.clanConfirmed=true;mine.clanConfirmedAt=Date.now();
      return current;
    });
    return !!result.committed&&!rejected;
  },"""
replace_once(old_set_clan,new_set_clan,'provisional clan selection plus confirm transaction')

# Reconstruct confirmation state from Firebase and never force two real players while
# they are only selecting. NPC follows the human choice in a 1-human + 1-NPC match.
replace_once(
    "const humans=Object.values(room.players||{}).sort((a,b)=>(a.slot??999)-(b.slot??999)).map((p,i)=>({id:p.uid,uid:p.uid,name:p.name||`Player ${i+1}`,human:true,local:p.uid===NetworkAdapter.localPlayerId,color:p.color||COLORS[i%COLORS.length],clan:normalizeClan(p.clan),clanChosen:!!p.clanChosen,clanSelectedAt:Number(p.clanSelectedAt)||0}));",
    "const humans=Object.values(room.players||{}).sort((a,b)=>(a.slot??999)-(b.slot??999)).map((p,i)=>({id:p.uid,uid:p.uid,name:p.name||`Player ${i+1}`,human:true,local:p.uid===NetworkAdapter.localPlayerId,color:p.color||COLORS[i%COLORS.length],clan:normalizeClan(p.clan),clanChosen:!!p.clanChosen,clanConfirmed:!!p.clanConfirmed,clanSelectedAt:Number(p.clanSelectedAt)||0}));",
    'lobby clan confirmation reconstruction',
)
replace_once(
    "const bots=Array.from({length:npcCount},(_,i)=>({id:`npc_${i+1}`,name:`NPC ${i+1}`,human:false,local:false,color:COLORS[(humans.length+i)%COLORS.length],clan:'warriors',clanChosen:false,clanSelectedAt:0}));",
    "const bots=Array.from({length:npcCount},(_,i)=>({id:`npc_${i+1}`,name:`NPC ${i+1}`,human:false,local:false,color:COLORS[(humans.length+i)%COLORS.length],clan:'warriors',clanChosen:true,clanConfirmed:true,clanSelectedAt:0}));",
    'NPC clan ready state',
)
replace_once(
    """   const chosen1v1=state.players.filter(p=>p.clanChosen).sort((a,b)=>(a.clanSelectedAt||0)-(b.clanSelectedAt||0))[0];
   if(state.mode==='war'&&state.players.length===2&&(chosen1v1||bots.length))enforceTwoPlayerClanExclusivity(chosen1v1?.id||humans[0]?.id);
   renderPlayers();""",
    """   // Nao forca dois humanos para clans diferentes enquanto estao apenas selecionando.
   // Contra um unico NPC, o bot acompanha visualmente o cla oposto sem bloquear o humano.
   if(state.mode==='war'&&state.players.length===2&&humans.length===1&&bots.length===1){
     bots[0].clan=oppositeClan(humans[0].clan);
   }
   renderPlayers();""",
    'remove premature real-player clan forcing',
)

# Add explicit Confirm button to the clan screen.
replace_once(
    """    <div id=\"clanSelectionStatus\">Seu clã: Guerreiros</div>
    <div class=\"divider\"></div>
    <button id=\"startWarBtn\" class=\"primary\">Iniciar preparação</button>""",
    """    <div id=\"clanSelectionStatus\">Selecionado: Guerreiros</div>
    <div class=\"divider\"></div>
    <button id=\"confirmClanBtn\" type=\"button\">Confirmar clã</button>
    <button id=\"startWarBtn\" class=\"primary\">Iniciar preparação</button>""",
    'clan confirmation button',
)

# Replace the old helper semantics with select -> confirm -> start.
old_helpers="""function oppositeClan(clan){return normalizeClan(clan)==='egypt'?'warriors':'egypt'}
function enforceTwoPlayerClanExclusivity(preferredId=null){
 if(state.mode!=='war'||state.players.length!==2)return;
 const preferred=state.players.find(p=>p.id===preferredId)||state.players.find(p=>p.clanChosen)||state.players.find(p=>p.human)||state.players[0];
 const other=state.players.find(p=>p!==preferred);
 if(!preferred||!other)return;
 preferred.clan=normalizeClan(preferred.clan);
 other.clan=oppositeClan(preferred.clan);
}
function prepareWarClanAssignments(){
 if(state.mode!=='war')return;
 if(state.players.length===2){
   const claimed=state.players.filter(p=>p.clanChosen).sort((a,b)=>(a.clanSelectedAt||0)-(b.clanSelectedAt||0))[0];
   enforceTwoPlayerClanExclusivity(claimed?.id||state.players.find(p=>p.human)?.id||state.players[0]?.id);
 }else if(state.players.length>=3){
   for(const p of state.players)if(!p.human)p.clan=Math.random()<.5?'warriors':'egypt';
 }
}
function clanUnavailableForLocal(clan){
 if(state.mode!=='war'||state.players.length!==2)return false;
 const me=localPlayer(),other=state.players.find(p=>p!==me);
 return !!(other?.human&&other.clanChosen&&normalizeClan(other.clan)===normalizeClan(clan));
}
"""
new_helpers="""function oppositeClan(clan){return normalizeClan(clan)==='egypt'?'warriors':'egypt'}
function allWarClanHumansConfirmed(){
 if(state.mode!=='war')return true;
 const humans=state.players.filter(p=>p.human);
 if(!humans.length||humans.some(p=>!p.clanConfirmed))return false;
 // Em 1x1 humano x humano a reserva e exclusiva.
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
   bots[0].clan=oppositeClan(humans[0].clan);bots[0].clanChosen=true;bots[0].clanConfirmed=true;
 }else if(state.players.length>=3){
   for(const p of bots){p.clan=Math.random()<.5?'warriors':'egypt';p.clanChosen=true;p.clanConfirmed=true}
 }
}
"""
replace_once(old_helpers,new_helpers,'new clan select-confirm-start helpers')

# Menu render: selection is editable until confirmation; confirmed reservation blocks only
# the opponent in a true 1v1.
old_render="""function renderClanSelection(){
 const clan=normalizeClan(localPlayer()?.clan);
 $$('.clan-option[data-clan]').forEach(btn=>{
   const optionClan=normalizeClan(btn.dataset.clan);
   btn.classList.toggle('selected',optionClan===clan);
   const locked=clanUnavailableForLocal(optionClan);
   btn.disabled=locked;
   btn.setAttribute('aria-disabled',locked?'true':'false');
 });
 const status=$('#clanSelectionStatus');
 if(status)status.textContent='Seu clã: '+clanLabel(clan)+(state.players.length===2?' • 1x1: clãs exclusivos':'');
}"""
new_render="""function renderClanSelection(){
 const me=localPlayer(),clan=normalizeClan(me?.clan),confirmed=!!me?.clanConfirmed;
 $$('.clan-option[data-clan]').forEach(btn=>{
   const optionClan=normalizeClan(btn.dataset.clan);
   btn.classList.toggle('selected',optionClan===clan);
   const locked=confirmed||clanUnavailableForLocal(optionClan);
   btn.disabled=locked;
   btn.setAttribute('aria-disabled',locked?'true':'false');
 });
 const status=$('#clanSelectionStatus');
 if(status)status.textContent=confirmed?`Clã confirmado: ${clanLabel(clan)}`:`Selecionado: ${clanLabel(clan)} • confirme para reservar`;
 const confirm=$('#confirmClanBtn');
 if(confirm){confirm.disabled=!me||confirmed;confirm.textContent=confirmed?'Confirmado ✓':'Confirmar clã'}
 updateLobbyAuthority();
}"""
replace_once(old_render,new_render,'confirmed clan menu rendering')

# Clicking a clan only SELECTS it. It does not reserve it and never changes another
# player's choice. Firebase onValue propagates provisional selections live.
old_handler="""$$('.clan-option[data-clan]').forEach(btn=>btn.onclick=async()=>{
 const requestedClan=normalizeClan(btn.dataset.clan);
 const before=localPlayer();if(!before)return;
 // So existe bloqueio quando ha exatamente dois HUMANOS e o outro ja confirmou o cla.
 // Sozinho na sala, ou jogando contra NPC, o jogador pode trocar livremente de cla;
 // no 1x1 contra NPC o bot simplesmente acompanha com o cla oposto.
 if(clanUnavailableForLocal(requestedClan)){renderClanSelection();return}
 if(NetworkAdapter.online){
   try{
     const accepted=await NetworkAdapter.setClan(requestedClan);
     if(!accepted){
       const status=$('#clanSelectionStatus');if(status)status.textContent='Esse clã já está ocupado no 1x1.';
       renderClanSelection();return;
     }
   }catch(err){console.error(err);return}
 }
 // onValue pode reconstruir state.players durante o await acima. Rebusca o player
 // atual antes de alterar a selecao visual para nunca escrever num objeto obsoleto.
 const p=localPlayer();if(!p)return;
 p.clan=requestedClan;p.clanChosen=true;p.clanSelectedAt=Date.now();
 if(state.players.length===2)enforceTwoPlayerClanExclusivity(p.id);
 renderClanSelection();renderPlayers();configureWarShopForClan();
});"""
new_handler="""$$('.clan-option[data-clan]').forEach(btn=>btn.onclick=async()=>{
 const requestedClan=normalizeClan(btn.dataset.clan),before=localPlayer();if(!before||before.clanConfirmed)return;
 if(clanUnavailableForLocal(requestedClan)){renderClanSelection();return}
 if(NetworkAdapter.online){
   try{if(!(await NetworkAdapter.setClan(requestedClan))){renderClanSelection();return}}catch(err){console.error(err);return}
 }
 const p=localPlayer();if(!p||p.clanConfirmed)return;
 p.clan=requestedClan;p.clanChosen=true;p.clanSelectedAt=Date.now();
 const bot=state.players.length===2?state.players.find(x=>!x.human):null;
 if(bot)bot.clan=oppositeClan(requestedClan);
 renderClanSelection();renderPlayers();configureWarShopForClan();
});
$('#confirmClanBtn').onclick=async()=>{
 const before=localPlayer();if(!before||before.clanConfirmed)return;
 if(NetworkAdapter.online){
   try{
     if(!(await NetworkAdapter.confirmClan())){
       const status=$('#clanSelectionStatus');if(status)status.textContent='Esse clã acabou de ser confirmado pelo outro jogador.';
       renderClanSelection();return;
     }
   }catch(err){console.error(err);return}
 }
 const p=localPlayer();if(!p)return;
 p.clanChosen=true;p.clanConfirmed=true;
 prepareWarClanAssignments();
 renderClanSelection();renderPlayers();configureWarShopForClan();
};"""
replace_once(old_handler,new_handler,'provisional select and explicit confirm controls')

# All humans must confirm before the host can start. Non-host confirmation remains enabled.
old_authority="""function updateLobbyAuthority(){
 const host=NetworkAdapter.isHost;
 $('#lobbyContinue').disabled=NetworkAdapter.online&&!host;
 $('#lobbyContinue').textContent=NetworkAdapter.online&&!host?'Aguardando o host...':'Continuar';
 $$('[data-target=\"npcs\"]').forEach(b=>b.disabled=NetworkAdapter.online&&!host);
 $('#startWarBtn').disabled=NetworkAdapter.online&&!host;
}"""
new_authority="""function updateLobbyAuthority(){
 const host=NetworkAdapter.isHost;
 $('#lobbyContinue').disabled=NetworkAdapter.online&&!host;
 $('#lobbyContinue').textContent=NetworkAdapter.online&&!host?'Aguardando o host...':'Continuar';
 $$('[data-target=\"npcs\"]').forEach(b=>b.disabled=NetworkAdapter.online&&!host);
 const allConfirmed=allWarClanHumansConfirmed();
 const start=$('#startWarBtn');
 if(start){
   start.disabled=(NetworkAdapter.online&&!host)||!allConfirmed;
   start.textContent=!allConfirmed?'Aguardando confirmações...':(NetworkAdapter.online&&!host?'Aguardando o host...':'Iniciar preparação');
 }
}"""
replace_once(old_authority,new_authority,'start only after all humans confirm')

# Guard the start action too, not only the button UI.
replace_once(
    """$('#startWarBtn').onclick=async()=>{
 if(warStartInFlight||(NetworkAdapter.online&&!NetworkAdapter.isHost))return;
 warStartInFlight=true;""",
    """$('#startWarBtn').onclick=async()=>{
 if(warStartInFlight||(NetworkAdapter.online&&!NetworkAdapter.isHost))return;
 if(!allWarClanHumansConfirmed()){renderClanSelection();flash('Todos precisam confirmar o clã.',1.4);return}
 warStartInFlight=true;""",
    'hard guard all clan confirmations before start',
)

p.write_text(t,encoding='utf-8')

required=[
    'clanConfirmed:false',
    'async confirmClan(){',
    'other&&!other.clanConfirmed&&normalizeClan(other.clan)===selected',
    'id="confirmClanBtn"',
    'function allWarClanHumansConfirmed()',
    'if(!humans.length||humans.some(p=>!p.clanConfirmed))return false;',
    "btn.classList.toggle('selected',optionClan===clan);",
    "confirm.textContent=confirmed?'Confirmado ✓':'Confirmar clã'",
    "$('#confirmClanBtn').onclick=async()=>{",
    "start.textContent=!allConfirmed?'Aguardando confirmações...'",
    "if(!allWarClanHumansConfirmed()){renderClanSelection();flash('Todos precisam confirmar o clã.',1.4);return}",
    "bots[0].clan=oppositeClan(humans[0].clan)",
]
for forbidden in [
    'enforceTwoPlayerClanExclusivity(',
    "other?.clanChosen&&normalizeClan(other.clan)===value",
]:
    if forbidden in t:
        raise SystemExit('Old premature clan lock still present: '+forbidden)
missing=[x for x in required if x not in t]
if missing:
    raise SystemExit('Missing select-confirm clan system: '+repr(missing))
print('Explicit select -> confirm -> all ready clan flow applied.')
