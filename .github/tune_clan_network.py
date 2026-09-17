from pathlib import Path

p = Path('index.html')
t = p.read_text(encoding='utf-8')


def replace_once(old, new, label):
    global t
    if new in t:
        return
    count = t.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected 1 old anchor, found {count}')
    t = t.replace(old, new, 1)


def replace_exact_count(old, new, expected, label):
    global t
    if new in t and old not in t:
        return
    count = t.count(old)
    if count != expected:
        raise SystemExit(f'{label}: expected {expected} old anchors, found {count}')
    t = t.replace(old, new)


# ---------- Clan exclusivity in 1x1 ----------
replace_exact_count(
    "clan:'warriors',joinedAt:F.serverTimestamp(),lastSeen:F.serverTimestamp()",
    "clan:'warriors',clanChosen:false,clanSelectedAt:0,joinedAt:F.serverTimestamp(),lastSeen:F.serverTimestamp()",
    2,
    'online player clan selection fields',
)

replace_once(
    "remoteInputs:{},processedCommands:new Set(),commandSeq:0,attackSeq:0,lastInputAt:0,lastStateAt:0,lastRemoteSeq:0,pushing:false,remoteFinishScheduled:false,",
    "remoteInputs:{},processedCommands:new Set(),commandSeq:0,attackSeq:0,lastInputAt:0,lastStateAt:0,lastRemoteSeq:0,lastSnapshotReceivedAt:0,pushing:false,remoteFinishScheduled:false,",
    'network snapshot timestamp state',
)

replace_once(
    "this.lastRemoteSeq=0;this.remoteFinishScheduled=false;this.processedCommands.clear();",
    "this.lastRemoteSeq=0;this.lastSnapshotReceivedAt=0;this.remoteFinishScheduled=false;this.processedCommands.clear();",
    'network snapshot timestamp reset',
)

replace_once(
    "  async setClan(clan){if(!this.roomId||!this.localPlayerId)return;const F=await this.waitFirebase(),value=normalizeClan(clan);await F.update(F.ref(F.firebaseDb,`rooms/${this.roomId}/players/${this.localPlayerId}`),{clan:value,lastSeen:F.serverTimestamp()})},",
    """  async setClan(clan){
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
  },""",
    'transactional clan selection',
)

replace_once(
    "const humans=Object.values(room.players||{}).sort((a,b)=>(a.slot??999)-(b.slot??999)).map((p,i)=>({id:p.uid,uid:p.uid,name:p.name||`Player ${i+1}`,human:true,local:p.uid===NetworkAdapter.localPlayerId,color:p.color||COLORS[i%COLORS.length],clan:normalizeClan(p.clan)}));",
    "const humans=Object.values(room.players||{}).sort((a,b)=>(a.slot??999)-(b.slot??999)).map((p,i)=>({id:p.uid,uid:p.uid,name:p.name||`Player ${i+1}`,human:true,local:p.uid===NetworkAdapter.localPlayerId,color:p.color||COLORS[i%COLORS.length],clan:normalizeClan(p.clan),clanChosen:!!p.clanChosen,clanSelectedAt:Number(p.clanSelectedAt)||0}));",
    'lobby clan metadata reconstruction',
)

replace_once(
    "const bots=Array.from({length:npcCount},(_,i)=>({id:`npc_${i+1}`,name:`NPC ${i+1}`,human:false,local:false,color:COLORS[(humans.length+i)%COLORS.length],clan:'warriors'}));\n   state.players=[...humans,...bots];renderPlayers();",
    """const bots=Array.from({length:npcCount},(_,i)=>({id:`npc_${i+1}`,name:`NPC ${i+1}`,human:false,local:false,color:COLORS[(humans.length+i)%COLORS.length],clan:'warriors',clanChosen:false,clanSelectedAt:0}));
   state.players=[...humans,...bots];
   const chosen1v1=state.players.filter(p=>p.clanChosen).sort((a,b)=>(a.clanSelectedAt||0)-(b.clanSelectedAt||0))[0];
   if(state.mode==='war'&&state.players.length===2&&(chosen1v1||bots.length))enforceTwoPlayerClanExclusivity(chosen1v1?.id||humans[0]?.id);
   renderPlayers();""",
    'online lobby 1x1 clan reconstruction',
)

clan_helper = r"""
function oppositeClan(clan){return normalizeClan(clan)==='egypt'?'warriors':'egypt'}
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
anchor = "function renderClanSelection(){"
if clan_helper.strip() not in t:
    if t.count(anchor) != 1:
        raise SystemExit('clan helper insertion anchor missing')
    t = t.replace(anchor, clan_helper + anchor, 1)

replace_once(
    """function renderClanSelection(){
 const clan=normalizeClan(localPlayer()?.clan);
 $$('.clan-option[data-clan]').forEach(btn=>btn.classList.toggle('selected',normalizeClan(btn.dataset.clan)===clan));
 const status=$('#clanSelectionStatus');if(status)status.textContent='Seu clã: '+clanLabel(clan);
}""",
    """function renderClanSelection(){
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
}""",
    'clan selection lock UI',
)

replace_once(
    """$$('.clan-option[data-clan]').forEach(btn=>btn.onclick=async()=>{
 const p=localPlayer();if(!p)return;
 const clan=normalizeClan(btn.dataset.clan);
 p.clan=clan;
 renderClanSelection();
 configureWarShopForClan();
 if(NetworkAdapter.online){
   try{await NetworkAdapter.setClan(clan)}catch(err){console.error(err)}
 }
});""",
    """$$('.clan-option[data-clan]').forEach(btn=>btn.onclick=async()=>{
 const p=localPlayer();if(!p)return;
 const clan=normalizeClan(btn.dataset.clan);
 if(clanUnavailableForLocal(clan)){renderClanSelection();return}
 if(NetworkAdapter.online){
   try{
     const accepted=await NetworkAdapter.setClan(clan);
     if(!accepted){
       const status=$('#clanSelectionStatus');if(status)status.textContent='Esse clã já está ocupado no 1x1.';
       renderClanSelection();return;
     }
   }catch(err){console.error(err);return}
 }
 p.clan=clan;p.clanChosen=true;p.clanSelectedAt=Date.now();
 if(state.players.length===2)enforceTwoPlayerClanExclusivity(p.id);
 renderClanSelection();renderPlayers();configureWarShopForClan();
});""",
    'clan selection behavior',
)

replace_once(
    """   // Um clique inicia a preparação imediatamente. O guard local impede callbacks
   // atrasados de 'clan' de devolver a tela ou reconstruir state.players; em seguida
   // status:'playing' e o snapshot completo são publicados juntos pelo pushState().
   startWarMode();""",
    """   // Fecha as regras de clã antes de criar as tropas da rodada.
   // Em 1x1 os clãs ficam exclusivos; com 3 participantes NPCs podem repetir aleatoriamente.
   prepareWarClanAssignments();renderPlayers();renderClanSelection();
   // Um clique inicia a preparação imediatamente. O guard local impede callbacks
   // atrasados de 'clan' de devolver a tela ou reconstruir state.players; em seguida
   // status:'playing' e o snapshot completo são publicados juntos pelo pushState().
   startWarMode();""",
    'war start clan finalization',
)

# ---------- Network smoothing for non-host clients ----------
replace_once(
    """   alive:!!e.alive,moving:!!e.moving,facing:Number(e.facing)||1,heading:Number(e.heading)||0,
   attackSerial:Number(e.attackSerial)||0,comboStep:Number(e.comboStep)||0,""",
    """   alive:!!e.alive,moving:!!e.moving,facing:Number(e.facing)||1,heading:Number(e.heading)||0,
   speed:Number(e.speed)||0,knockTime:Number(e.knockTime)||0,knockVX:Number(e.knockVX)||0,knockVY:Number(e.knockVY)||0,
   attackSerial:Number(e.attackSerial)||0,comboStep:Number(e.comboStep)||0,""",
    'network motion fields',
)

replace_once(
    """ NetworkAdapter.lastRemoteSeq=Number(game.seq||0);
 const firstFrame=$('#gameScreen').style.display==='none';""",
    """ NetworkAdapter.lastRemoteSeq=Number(game.seq||0);
 const remoteNow=performance.now();
 const remoteGapSec=NetworkAdapter.lastSnapshotReceivedAt?clamp((remoteNow-NetworkAdapter.lastSnapshotReceivedAt)/1000,.04,.25):.10;
 NetworkAdapter.lastSnapshotReceivedAt=remoteNow;
 const remoteExtrapolateMs=clamp(remoteGapSec*700,45,110);
 const firstFrame=$('#gameScreen').style.display==='none';""",
    'remote snapshot cadence tracking',
)

replace_once(
    "const out={...e,x:old?.x??e.x,y:old?.y??e.y,netTargetX:e.x,netTargetY:e.y,target:null,controlled:e.ownerId===NetworkAdapter.localPlayerId};",
    """let netVelocityX=0,netVelocityY=0;
     if(Number(e.knockTime)>0){netVelocityX=Number(e.knockVX)||0;netVelocityY=Number(e.knockVY)||0}
     else if(e.moving&&Number(e.speed)>0){netVelocityX=Math.cos(Number(e.heading)||0)*Number(e.speed);netVelocityY=Math.sin(Number(e.heading)||0)*Number(e.speed)}
     const out={...e,x:old?.x??e.x,y:old?.y??e.y,netTargetX:Number(e.x)||0,netTargetY:Number(e.y)||0,netVelocityX,netVelocityY,netExtrapolateUntil:remoteNow+remoteExtrapolateMs,target:null,controlled:e.ownerId===NetworkAdapter.localPlayerId};""",
    'remote entity motion prediction',
)

replace_once(
    "if(becameTeleported){out.x=Number(e.x);out.y=Number(e.y);out.netTargetX=Number(e.x);out.netTargetY=Number(e.y)}",
    "if(becameTeleported){out.x=Number(e.x);out.y=Number(e.y);out.netTargetX=Number(e.x);out.netTargetY=Number(e.y);out.netVelocityX=0;out.netVelocityY=0;out.netExtrapolateUntil=remoteNow}",
    'Naja teleport prediction reset',
)

replace_once(
    "if(NetworkAdapter.online&&!NetworkAdapter.isHost)for(const e of state.entities){if(e.netTargetX==null)continue;const smooth=Math.min(1,dt*14);e.x+=(e.netTargetX-e.x)*smooth;e.y+=(e.netTargetY-e.y)*smooth}",
    """if(NetworkAdapter.online&&!NetworkAdapter.isHost){
   const clientNow=performance.now();
   for(const e of state.entities){
     if(e.netTargetX==null)continue;
     if(clientNow<Number(e.netExtrapolateUntil||0)){
       const step=Math.min(dt,.034);
       e.netTargetX+=(Number(e.netVelocityX)||0)*step;
       e.netTargetY+=(Number(e.netVelocityY)||0)*step;
     }
     const dx=e.netTargetX-e.x,dy=e.netTargetY-e.y,d=Math.hypot(dx,dy);
     if(d>260){e.x=e.netTargetX;e.y=e.netTargetY;continue}
     const rate=d>80?28:20,smooth=1-Math.exp(-rate*dt);
     e.x+=dx*smooth;e.y+=dy*smooth;
   }
 }""",
    'client interpolation and short extrapolation',
)

replace_once(
    "const networkPushInterval=state.mode==='war'?150:120;",
    "const networkPushInterval=state.mode==='war'?100:120;",
    'war network snapshot interval',
)

p.write_text(t, encoding='utf-8')

required = [
    "clanChosen:false,clanSelectedAt:0",
    "async setClan(clan){",
    "total===2&&humans.length===2",
    "function enforceTwoPlayerClanExclusivity(",
    "function prepareWarClanAssignments(",
    "function clanUnavailableForLocal(",
    "1x1: clãs exclusivos",
    "prepareWarClanAssignments();renderPlayers();renderClanSelection();",
    "speed:Number(e.speed)||0,knockTime:Number(e.knockTime)||0",
    "lastSnapshotReceivedAt:0",
    "remoteExtrapolateMs=clamp(remoteGapSec*700,45,110)",
    "netExtrapolateUntil:remoteNow+remoteExtrapolateMs",
    "const rate=d>80?28:20,smooth=1-Math.exp(-rate*dt);",
    "const networkPushInterval=state.mode==='war'?100:120;",
]
missing = [x for x in required if x not in t]
if missing:
    raise SystemExit('Missing clan/network tuning: ' + repr(missing))

print('1x1 clan exclusivity and smoother client networking applied.')
