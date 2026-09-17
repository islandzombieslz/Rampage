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

# -----------------------------------------------------------------------------
# 1) Clan selection UI: always use the current state object after async Firebase
#    transactions. The previous code kept a stale `p` reference if onValue rebuilt
#    state.players while setClan() was awaiting Firebase.
# -----------------------------------------------------------------------------
old_handler="""$$('.clan-option[data-clan]').forEach(btn=>btn.onclick=async()=>{
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
});"""
new_handler="""$$('.clan-option[data-clan]').forEach(btn=>btn.onclick=async()=>{
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
replace_once(old_handler,new_handler,'fresh clan selection state after Firebase transaction')

# Whenever the Firebase lobby roster changes while clan screen is open, refresh both
# the selected card and the shop clan. This makes the automatically opposite 1x1 clan
# visible immediately on the non-host client instead of only becoming correct in-game.
replace_once(
    "if(room.status==='clan')renderClanSelection();",
    "if(room.status==='clan'){renderClanSelection();configureWarShopForClan();}",
    'live clan menu refresh',
)

# Make the status text explicit only for actual 1v1. With one participant there is no
# exclusivity and both buttons must remain available.
replace_once(
    "if(status)status.textContent='Seu clã: '+clanLabel(clan)+(state.players.length===2?' • 1x1: clãs exclusivos':'');",
    "if(status)status.textContent='Seu clã: '+clanLabel(clan)+(state.players.length===2?' • 1x1: clãs exclusivos':'');",
    'single-player clan freedom marker',
)

# -----------------------------------------------------------------------------
# 2) Replace short extrapolation with buffered LINEAR interpolation.
#    Extrapolating knockback/heading made corrections oscillate when a new Firebase
#    snapshot arrived. Instead, every remote entity moves from its current rendered
#    position to the newest authoritative position over roughly one snapshot period.
# -----------------------------------------------------------------------------
old_remote_clock=""" NetworkAdapter.lastRemoteSeq=Number(game.seq||0);
 const remoteNow=performance.now();
 const remoteGapSec=NetworkAdapter.lastSnapshotReceivedAt?clamp((remoteNow-NetworkAdapter.lastSnapshotReceivedAt)/1000,.04,.25):.10;
 NetworkAdapter.lastSnapshotReceivedAt=remoteNow;
 const remoteExtrapolateMs=clamp(remoteGapSec*700,45,110);
 const firstFrame=$('#gameScreen').style.display==='none';"""
new_remote_clock=""" NetworkAdapter.lastRemoteSeq=Number(game.seq||0);
 const remoteNow=performance.now();
 const remoteGapMs=NetworkAdapter.lastSnapshotReceivedAt?clamp(remoteNow-NetworkAdapter.lastSnapshotReceivedAt,70,220):120;
 NetworkAdapter.lastSnapshotReceivedAt=remoteNow;
 // Um pouco maior que o intervalo observado: o proximo snapshot normalmente chega
 // antes do tween terminar, evitando a micro-parada entre pacotes sem prever fisica.
 const remoteInterpMs=clamp(remoteGapMs*1.18,105,190);
 const firstFrame=$('#gameScreen').style.display==='none';"""
replace_once(old_remote_clock,new_remote_clock,'replace extrapolation clock with interpolation clock')

old_entity="""let netVelocityX=0,netVelocityY=0;
     if(Number(e.knockTime)>0){netVelocityX=Number(e.knockVX)||0;netVelocityY=Number(e.knockVY)||0}
     else if(e.moving&&Number(e.speed)>0){netVelocityX=Math.cos(Number(e.heading)||0)*Number(e.speed);netVelocityY=Math.sin(Number(e.heading)||0)*Number(e.speed)}
     const out={...e,x:old?.x??e.x,y:old?.y??e.y,netTargetX:Number(e.x)||0,netTargetY:Number(e.y)||0,netVelocityX,netVelocityY,netExtrapolateUntil:remoteNow+remoteExtrapolateMs,target:null,controlled:e.ownerId===NetworkAdapter.localPlayerId};"""
new_entity="""const fromX=old&&Number.isFinite(Number(old.x))?Number(old.x):(Number(e.x)||0);
     const fromY=old&&Number.isFinite(Number(old.y))?Number(old.y):(Number(e.y)||0);
     const toX=Number(e.x)||0,toY=Number(e.y)||0;
     const out={...e,x:fromX,y:fromY,netFromX:fromX,netFromY:fromY,netToX:toX,netToY:toY,netInterpStartedAt:remoteNow,netInterpDuration:remoteInterpMs,target:null,controlled:e.ownerId===NetworkAdapter.localPlayerId};"""
replace_once(old_entity,new_entity,'buffered entity interpolation state')

old_teleport="if(becameTeleported){out.x=Number(e.x);out.y=Number(e.y);out.netTargetX=Number(e.x);out.netTargetY=Number(e.y);out.netVelocityX=0;out.netVelocityY=0;out.netExtrapolateUntil=remoteNow}"
new_teleport="if(becameTeleported){out.x=Number(e.x);out.y=Number(e.y);out.netFromX=Number(e.x);out.netFromY=Number(e.y);out.netToX=Number(e.x);out.netToY=Number(e.y);out.netInterpStartedAt=remoteNow;out.netInterpDuration=1}"
replace_once(old_teleport,new_teleport,'Naja teleport interpolation reset')

old_projectiles="if(Array.isArray(game.dragonProjectiles))state.dragonProjectiles=game.dragonProjectiles.map(p=>({...p}));"
new_projectiles="""if(Array.isArray(game.dragonProjectiles)){
   // Fireballs are visually simulated every frame on clients. The host remains
   // authoritative; each snapshot only corrects their path smoothly.
   const previousProjectiles=new Map((state.dragonProjectiles||[]).map(p=>[p.id,p]));
   state.dragonProjectiles=game.dragonProjectiles.map(p=>{
     const old=previousProjectiles.get(p.id),authX=Number(p.x)||0,authY=Number(p.y)||0;
     return {...p,x:old?.x??authX,y:old?.y??authY,netTargetX:authX,netTargetY:authY};
   });
 }"""
replace_once(old_projectiles,new_projectiles,'smooth remote dragon projectiles')

old_client_loop="""if(NetworkAdapter.online&&!NetworkAdapter.isHost){
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
 }"""
new_client_loop="""if(NetworkAdapter.online&&!NetworkAdapter.isHost){
   const clientNow=performance.now();
   for(const e of state.entities){
     if(e.netToX==null)continue;
     const duration=Math.max(1,Number(e.netInterpDuration)||120);
     const alpha=clamp((clientNow-(Number(e.netInterpStartedAt)||clientNow))/duration,0,1);
     // Linear on purpose: no overshoot, spring or predicted knockback correction.
     e.x=(Number(e.netFromX)||0)+((Number(e.netToX)||0)-(Number(e.netFromX)||0))*alpha;
     e.y=(Number(e.netFromY)||0)+((Number(e.netToY)||0)-(Number(e.netFromY)||0))*alpha;
   }
   // Projectiles keep moving at render FPS between Firebase updates. The target
   // authority is advanced by the same velocity and the visible projectile converges
   // slowly to it, so a correction never looks like a teleport backwards.
   const projectileStep=Math.min(dt,.034),projectileSmooth=1-Math.exp(-9*dt);
   for(const p of state.dragonProjectiles||[]){
     const vx=Number(p.vx)||0,vy=Number(p.vy)||0;
     p.x=(Number(p.x)||0)+vx*projectileStep;p.y=(Number(p.y)||0)+vy*projectileStep;
     p.netTargetX=(Number(p.netTargetX)||0)+vx*projectileStep;p.netTargetY=(Number(p.netTargetY)||0)+vy*projectileStep;
     const dx=p.netTargetX-p.x,dy=p.netTargetY-p.y;
     if(dx*dx+dy*dy>240*240){p.x=p.netTargetX;p.y=p.netTargetY}
     else{p.x+=dx*projectileSmooth;p.y+=dy*projectileSmooth}
   }
 }"""
replace_once(old_client_loop,new_client_loop,'linear client interpolation and projectile render simulation')

# 120 ms reduces Firebase churn versus 100 ms while the interpolation keeps motion at
# display refresh rate. More writes were not making motion smoother; they amplified
# correction noise when callbacks arrived unevenly.
replace_once(
    "const networkPushInterval=state.mode==='war'?100:120;",
    "const networkPushInterval=state.mode==='war'?120:120;",
    'balanced war snapshot interval',
)

p.write_text(t,encoding='utf-8')

required=[
    'const p=localPlayer();if(!p)return;',
    "if(room.status==='clan'){renderClanSelection();configureWarShopForClan();}",
    'const remoteInterpMs=clamp(remoteGapMs*1.18,105,190);',
    'netInterpStartedAt:remoteNow,netInterpDuration:remoteInterpMs',
    'netFromX=Number(e.x);out.netFromY=Number(e.y);out.netToX=Number(e.x);out.netToY=Number(e.y)',
    'const previousProjectiles=new Map((state.dragonProjectiles||[]).map(p=>[p.id,p]));',
    'const projectileStep=Math.min(dt,.034),projectileSmooth=1-Math.exp(-9*dt);',
    "const networkPushInterval=state.mode==='war'?120:120;",
]
for forbidden in ['remoteExtrapolateMs=clamp(remoteGapSec*700,45,110)','netExtrapolateUntil:remoteNow+remoteExtrapolateMs','const rate=d>80?28:20,smooth=1-Math.exp(-rate*dt);']:
    if forbidden in t:
        raise SystemExit('Old unstable extrapolation still present: '+forbidden)
missing=[x for x in required if x not in t]
if missing:
    raise SystemExit('Missing clan/network v2 tuning: '+repr(missing))
print('Clan UI sync and buffered online interpolation v2 applied.')
