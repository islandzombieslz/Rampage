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

# Confirmation/selection used a transaction on the whole room. A transaction can
# see a cold local value as null on its first pass and our old updater aborted.
# Use direct writes to the authenticated player's own node instead. The host
# reconciles the only race that matters: two real players confirming the same clan.
network_block='''  async setClan(clan){
    if(!this.roomId||!this.localPlayerId)return false;
    const F=await this.waitFirebase(),value=normalizeClan(clan);
    const playerRef=F.ref(F.firebaseDb,`rooms/${this.roomId}/players/${this.localPlayerId}`);
    const [mineSnap,playersSnap,npcSnap]=await Promise.all([
      F.get(playerRef),
      F.get(F.ref(F.firebaseDb,`rooms/${this.roomId}/players`)),
      F.get(F.ref(F.firebaseDb,`rooms/${this.roomId}/npcCount`))
    ]);
    const mine=mineSnap.val();
    if(!mine||mine.clanConfirmed)return false;
    const players=playersSnap.val()||{},humans=Object.values(players),total=humans.length+Math.max(0,Number(npcSnap.val())||0);
    if(total===2&&humans.length===2){
      const other=humans.find(p=>p.uid!==this.localPlayerId);
      if(other?.clanConfirmed&&normalizeClan(other.clan)===value)return false;
    }
    await F.update(playerRef,{clan:value,clanChosen:true,clanConfirmed:false,clanSelectedAt:Date.now()});
    return true;
  },
  async confirmClan(clan){
    if(!this.roomId||!this.localPlayerId)return false;
    const F=await this.waitFirebase(),selected=normalizeClan(clan);
    const playerRef=F.ref(F.firebaseDb,`rooms/${this.roomId}/players/${this.localPlayerId}`);
    const [mineSnap,playersSnap,npcSnap]=await Promise.all([
      F.get(playerRef),
      F.get(F.ref(F.firebaseDb,`rooms/${this.roomId}/players`)),
      F.get(F.ref(F.firebaseDb,`rooms/${this.roomId}/npcCount`))
    ]);
    const mine=mineSnap.val();
    if(!mine)return false;
    if(mine.clanConfirmed&&normalizeClan(mine.clan)===selected)return true;
    if(mine.clanConfirmed)return false;
    const players=playersSnap.val()||{},humans=Object.values(players),total=humans.length+Math.max(0,Number(npcSnap.val())||0);
    if(total===2&&humans.length===2){
      const other=humans.find(p=>p.uid!==this.localPlayerId);
      if(other?.clanConfirmed&&normalizeClan(other.clan)===selected)return false;
    }
    const now=Date.now();
    await F.update(playerRef,{clan:selected,clanChosen:true,clanConfirmed:true,clanSelectedAt:now,clanConfirmedAt:now});
    return true;
  },
  async sendInput(input)'''
sub_once(r'  async setClan\(clan\)\{.*?\n  async sendInput\(input\)',network_block,'replace room-wide clan transaction',re.S)

# Host-side atomic-enough reconciliation. Both players may select the same clan,
# but once one confirms it is reserved. If both confirmation writes cross, the
# earliest confirmation wins and the other player is moved/unconfirmed.
reconcile_block='''let clanReservationRepairInFlight=false;
async function reconcileClanReservations(room){
 if(clanReservationRepairInFlight||!NetworkAdapter.isHost||state.mode!=='war'||room?.status!=='clan')return;
 const entries=Object.entries(room.players||{});
 const total=entries.length+Math.max(0,Number(room.npcCount)||0);
 if(total!==2||entries.length!==2)return;
 const [a,b]=entries;
 const ca=normalizeClan(a[1]?.clan),cb=normalizeClan(b[1]?.clan);
 if(ca!==cb)return;
 const aConfirmed=!!a[1]?.clanConfirmed,bConfirmed=!!b[1]?.clanConfirmed;
 if(!aConfirmed&&!bConfirmed)return;
 let winner,loser;
 if(aConfirmed&&!bConfirmed){winner=a;loser=b}
 else if(!aConfirmed&&bConfirmed){winner=b;loser=a}
 else{
   const at=Number(a[1]?.clanConfirmedAt)||Number.MAX_SAFE_INTEGER;
   const bt=Number(b[1]?.clanConfirmedAt)||Number.MAX_SAFE_INTEGER;
   if(at<bt){winner=a;loser=b}
   else if(bt<at){winner=b;loser=a}
   else if((Number(a[1]?.slot)||0)<=(Number(b[1]?.slot)||0)){winner=a;loser=b}
   else{winner=b;loser=a}
 }
 const desired=oppositeClan(winner[1]?.clan);
 clanReservationRepairInFlight=true;
 try{
   const F=await NetworkAdapter.waitFirebase();
   await F.update(F.ref(F.firebaseDb,`rooms/${NetworkAdapter.roomId}/players/${loser[0]}`),{
     clan:desired,clanChosen:true,clanConfirmed:false,clanConfirmedAt:null,clanSelectedAt:Date.now()
   });
 }finally{clanReservationRepairInFlight=false}
}
function syncFirebaseRoom(room){'''
sub_once(r'(?:let clanReservationRepairInFlight=false;\nasync function reconcileClanReservations\(room\)\{.*?\n\}\n)?function syncFirebaseRoom\(room\)\{',reconcile_block,'install host clan reconciliation',re.S)

# Run reconciliation whenever the host receives fresh room state.
anchor="function syncFirebaseRoom(room){\n if(!room)return;"
replacement="function syncFirebaseRoom(room){\n if(!room)return;\n reconcileClanReservations(room).catch(console.error);"
if anchor not in t:
    raise SystemExit('syncFirebaseRoom entry anchor missing')
t=t.replace(anchor,replacement,1)

# Make confirmation visibly lock immediately after a successful write, and make
# failure explicit instead of appearing as a dead button.
old_handler="""$('#confirmClanBtn').onclick=async()=>{
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
new_handler="""$('#confirmClanBtn').onclick=async()=>{
 const me=localPlayer();if(!me||me.clanConfirmed||clanConfirmInFlight)return;
 const selected=normalizeClan(clanDraft??me.clan);
 if(clanUnavailableForLocal(selected)){flash('Esse clã já foi reservado.',1.3);renderClanSelection();return}
 clanConfirmInFlight=true;
 renderClanSelection();
 try{
   if(NetworkAdapter.online){
     const ok=await NetworkAdapter.confirmClan(selected);
     if(!ok){flash('Esse clã não pôde ser confirmado.',1.5);return}
   }
   const current=localPlayer();
   if(!current){flash('Jogador local não encontrado.',1.5);return}
   current.clan=selected;
   current.clanChosen=true;
   current.clanConfirmed=true;
   current.clanConfirmedAt=Date.now();
   clanDraft=selected;
   prepareWarClanAssignments();
   renderPlayers();
   configureWarShopForClan();
 }catch(err){
   console.error('confirmClan failed',err);
   flash('Falha de rede ao confirmar o clã.',1.6);
 }finally{
   clanConfirmInFlight=false;
   renderClanSelection();
 }
};"""
if old_handler not in t:
    raise SystemExit('V6 confirm handler anchor missing')
t=t.replace(old_handler,new_handler,1)

required=[
    'async confirmClan(clan){',
    'await F.update(playerRef,{clan:selected,clanChosen:true,clanConfirmed:true',
    'let clanReservationRepairInFlight=false;',
    'async function reconcileClanReservations(room){',
    'reconcileClanReservations(room).catch(console.error);',
    "flash('Falha de rede ao confirmar o clã.'",
    'current.clanConfirmed=true;',
]
missing=[x for x in required if x not in t]
if missing: raise SystemExit('Missing V7 confirmation repair: '+repr(missing))

# The old fragile room-wide transaction must be gone from setClan/confirmClan.
network=t[t.index('  async setClan(clan){'):t.index('  async sendInput(input)')]
if 'runTransaction(roomRef' in network:
    raise SystemExit('Old room-wide clan transaction still present')

p.write_text(t,encoding='utf-8')
print('Clan confirmation V7 direct-write/reconciliation repair applied.')
