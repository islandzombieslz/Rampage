from pathlib import Path

path=Path('index.html')
text=path.read_text(encoding='utf-8')

marker='/* ROOM LIFECYCLE 2026-09-09 */'

# =========================================================
# ROOM CODES
# =========================================================
old_codes="const ROOM_CODES=['REI','PLEBEU','CONDE'];"
new_codes="const ROOM_CODES=['REI','PLEBEU','CONDE','VINHO','FURIA','PAZ','DRAGON'];"
if new_codes not in text:
    if old_codes not in text:
        raise SystemExit('Lista atual de códigos de sala não encontrada')
    text=text.replace(old_codes,new_codes,1)

if marker not in text:
    anchor=new_codes+'\n'
    helpers="""const ROOM_INACTIVITY_MS=10*60*1000;
const ROOM_HEARTBEAT_MS=30*1000;
const ROOM_CLEANUP_MS=60*1000;
function roomPlayers(room){return Object.values(room?.players||{})}
function roomLatestSeenAt(room){
 const players=roomPlayers(room);let latest=0;
 for(const p of players)latest=Math.max(latest,Number(p?.lastSeen)||Number(p?.joinedAt)||0);
 return Math.max(latest,Number(room?.lastActivityAt)||0,Number(room?.createdAt)||0);
}
function roomIsExpired(room,now){
 const players=roomPlayers(room);
 if(!players.length)return true;
 const last=roomLatestSeenAt(room);
 return !last || now-last>ROOM_INACTIVITY_MS;
}
"""
    if anchor not in text: raise SystemExit('Âncora dos códigos não encontrada')
    text=text.replace(anchor,marker+'\n'+anchor+helpers,1)

# =========================================================
# NETWORK ADAPTER STATE
# =========================================================
old_props="  remoteInputs:{},processedCommands:new Set(),commandSeq:0,attackSeq:0,lastInputAt:0,lastStateAt:0,lastRemoteSeq:0,pushing:false,remoteFinishScheduled:false,"
new_props="  remoteInputs:{},processedCommands:new Set(),commandSeq:0,attackSeq:0,lastInputAt:0,lastStateAt:0,lastRemoteSeq:0,pushing:false,remoteFinishScheduled:false,\n  presenceTimer:null,cleanupTimer:null,serverOffsetUnsub:null,serverTimeOffset:0,cleanupRunning:false,maintenanceStarted:false,leaving:false,"
if new_props not in text:
    if old_props not in text: raise SystemExit('Estado do NetworkAdapter não encontrado')
    text=text.replace(old_props,new_props,1)

# =========================================================
# CREATE / JOIN / PRESENCE
# =========================================================
old_create="  async createRoom(snapshot){const F=await this.waitFirebase(),user=await this.ensureAuth();let code=null;const roomCandidates=[...ROOM_CODES].sort(()=>Math.random()-.5);for(const c of roomCandidates){const s=await F.get(F.ref(F.firebaseDb,`rooms/${c}`));if(!s.exists()){code=c;break}}if(!code)throw Error('Falha ao gerar sala');const settings={mode:snapshot.mode,pveTime:snapshot.pveTime,warTime:snapshot.warTime,rounds:snapshot.rounds,difficulty:snapshot.difficulty,speed:snapshot.speed,gems:snapshot.gems};await F.set(F.ref(F.firebaseDb,`rooms/${code}`),{code,hostUid:user.uid,status:'lobby',npcCount:0,createdAt:F.serverTimestamp(),settings,players:{[user.uid]:{uid:user.uid,name:getCurrentNick(),human:true,slot:0,color:COLORS[0],joinedAt:F.serverTimestamp()}}});this.roomId=code;this.hostUid=user.uid;await this.attachPresence(code,user.uid);this.subscribeRoom(code);return {code,offline:false}},"
new_create="""  async createRoom(snapshot){
    const F=await this.waitFirebase(),user=await this.ensureAuth();
    await this.cleanupRooms();
    let code=null;
    const roomCandidates=[...ROOM_CODES].sort(()=>Math.random()-.5);
    for(const c of roomCandidates){
      const s=await F.get(F.ref(F.firebaseDb,`rooms/${c}`));
      if(!s.exists()){code=c;break}
    }
    if(!code)throw Error('Falha ao gerar sala');
    const settings={mode:snapshot.mode,pveTime:snapshot.pveTime,warTime:snapshot.warTime,rounds:snapshot.rounds,difficulty:snapshot.difficulty,speed:snapshot.speed,gems:snapshot.gems};
    await F.set(F.ref(F.firebaseDb,`rooms/${code}`),{
      code,hostUid:user.uid,status:'lobby',npcCount:0,createdAt:F.serverTimestamp(),lastActivityAt:F.serverTimestamp(),settings,
      players:{[user.uid]:{uid:user.uid,name:getCurrentNick(),human:true,slot:0,color:COLORS[0],joinedAt:F.serverTimestamp(),lastSeen:F.serverTimestamp()}}
    });
    this.roomId=code;this.hostUid=user.uid;
    await this.attachPresence(code,user.uid);
    this.subscribeRoom(code);
    return {code,offline:false};
  },"""
if new_create not in text:
    if old_create not in text: raise SystemExit('createRoom atual não encontrado')
    text=text.replace(old_create,new_create,1)

old_join="  async joinRoom(code){const F=await this.waitFirebase(),user=await this.ensureAuth();code=normalizeRoomCode(code);const rr=F.ref(F.firebaseDb,`rooms/${code}`),snap=await F.get(rr);if(!snap.exists())return {ok:false,reason:'not-found'};const room=snap.val();if(room.status!=='lobby')return {ok:false,reason:'started'};const count=room.players?Object.keys(room.players).length:0,max=room.settings?.mode==='pve'?10:3;if(count+(room.npcCount||0)>=max&&!room.players?.[user.uid])return {ok:false,reason:'full'};const slot=Object.values(room.players||{}).reduce((m,p)=>Math.max(m,Number(p.slot)||0),-1)+1;await F.set(F.ref(F.firebaseDb,`rooms/${code}/players/${user.uid}`),{uid:user.uid,name:getCurrentNick(),human:true,slot,color:COLORS[slot%COLORS.length],joinedAt:F.serverTimestamp()});this.roomId=code;this.hostUid=room.hostUid;this.localPlayerId=user.uid;await this.attachPresence(code,user.uid);this.subscribeRoom(code);return {ok:true,room,offline:false}},"
new_join="""  async joinRoom(code){
    const F=await this.waitFirebase(),user=await this.ensureAuth();
    await this.cleanupRooms();
    code=normalizeRoomCode(code);
    const rr=F.ref(F.firebaseDb,`rooms/${code}`),snap=await F.get(rr);
    if(!snap.exists())return {ok:false,reason:'not-found'};
    const room=snap.val();
    if(roomIsExpired(room,this.serverNow())){await F.remove(rr);return {ok:false,reason:'not-found'}}
    if(room.status!=='lobby')return {ok:false,reason:'started'};
    const count=room.players?Object.keys(room.players).length:0,max=room.settings?.mode==='pve'?10:3;
    if(count+(room.npcCount||0)>=max&&!room.players?.[user.uid])return {ok:false,reason:'full'};
    const slot=Object.values(room.players||{}).reduce((m,p)=>Math.max(m,Number(p.slot)||0),-1)+1;
    await F.set(F.ref(F.firebaseDb,`rooms/${code}/players/${user.uid}`),{uid:user.uid,name:getCurrentNick(),human:true,slot,color:COLORS[slot%COLORS.length],joinedAt:F.serverTimestamp(),lastSeen:F.serverTimestamp()});
    await F.update(rr,{lastActivityAt:F.serverTimestamp()});
    this.roomId=code;this.hostUid=room.hostUid;this.localPlayerId=user.uid;
    await this.attachPresence(code,user.uid);
    this.subscribeRoom(code);
    return {ok:true,room,offline:false};
  },"""
if new_join not in text:
    if old_join not in text: raise SystemExit('joinRoom atual não encontrado')
    text=text.replace(old_join,new_join,1)

old_presence="  async attachPresence(code,uid){const F=await this.waitFirebase();try{await F.onDisconnect(F.ref(F.firebaseDb,`rooms/${code}/players/${uid}`)).remove();await F.onDisconnect(F.ref(F.firebaseDb,`rooms/${code}/inputs/${uid}`)).remove()}catch(_){}},"
new_presence="""  async attachPresence(code,uid){
    const F=await this.waitFirebase();
    try{
      await F.onDisconnect(F.ref(F.firebaseDb,`rooms/${code}/players/${uid}`)).remove();
      await F.onDisconnect(F.ref(F.firebaseDb,`rooms/${code}/inputs/${uid}`)).remove();
    }catch(_){}
    this.startRoomHeartbeat();
  },
  serverNow(){return Date.now()+(Number(this.serverTimeOffset)||0)},
  async touchPresence(){
    const code=this.roomId,uid=this.localPlayerId;if(!code||!uid)return;
    const F=await this.waitFirebase(),rr=F.ref(F.firebaseDb,`rooms/${code}`);
    try{
      const snap=await F.get(rr);
      if(!snap.exists()){this.expireLocalRoom(code);return}
      const room=snap.val(),now=this.serverNow();
      if(roomIsExpired(room,now)){await F.remove(rr);this.expireLocalRoom(code);return}
      if(!room.players?.[uid]){this.expireLocalRoom(code);return}
      const patch={lastActivityAt:F.serverTimestamp()};
      patch[`players/${uid}/lastSeen`]=F.serverTimestamp();
      await F.update(rr,patch);
    }catch(_){}
  },
  startRoomHeartbeat(){
    this.stopRoomHeartbeat();
    this.touchPresence().catch(()=>{});
    this.presenceTimer=setInterval(()=>this.touchPresence().catch(()=>{}),ROOM_HEARTBEAT_MS);
  },
  stopRoomHeartbeat(){if(this.presenceTimer){clearInterval(this.presenceTimer);this.presenceTimer=null}},
  expireLocalRoom(code){
    if(this.roomId!==code||this.leaving)return;
    this.stopRoomHeartbeat();
    this.roomUnsubscribes.forEach(fn=>{try{fn()}catch(_){}});this.roomUnsubscribes=[];
    this.roomCache={};this.roomId=null;this.hostUid=null;this.roomStatus='idle';
    try{state.running=false}catch(_){}
    try{navigateScreen('menuScreen')}catch(_){}
  },
  async removeRoomIfEmpty(code,notifyCurrent=true){
    if(!code)return false;
    const F=await this.waitFirebase(),rr=F.ref(F.firebaseDb,`rooms/${code}`);
    try{
      const snap=await F.get(F.ref(F.firebaseDb,`rooms/${code}/players`));
      if(snap.exists())return false;
      await F.remove(rr);
      if(notifyCurrent)this.expireLocalRoom(code);
      return true;
    }catch(_){return false}
  },
  async cleanupRooms(){
    if(this.cleanupRunning)return;
    this.cleanupRunning=true;
    try{
      const F=await this.waitFirebase(),now=this.serverNow();
      let codes=[];
      try{
        const all=await F.get(F.ref(F.firebaseDb,'rooms'));
        if(all.exists())codes=Object.keys(all.val()||{});
      }catch(_){codes=[...ROOM_CODES]}
      if(!codes.length)return;
      for(const code of [...new Set(codes)]){
        try{
          const rr=F.ref(F.firebaseDb,`rooms/${code}`),snap=await F.get(rr);
          if(!snap.exists())continue;
          const room=snap.val();
          if(roomIsExpired(room,now)){
            await F.remove(rr);
            this.expireLocalRoom(code);
          }
        }catch(_){}
      }
    }finally{this.cleanupRunning=false}
  },
  startRoomMaintenance(){
    if(this.maintenanceStarted)return;
    this.maintenanceStarted=true;
    this.waitFirebase().then(F=>{
      try{this.serverOffsetUnsub=F.onValue(F.ref(F.firebaseDb,'.info/serverTimeOffset'),s=>{this.serverTimeOffset=Number(s.val())||0})}catch(_){}
      this.cleanupRooms().catch(()=>{});
      this.cleanupTimer=setInterval(()=>this.cleanupRooms().catch(()=>{}),ROOM_CLEANUP_MS);
    }).catch(()=>{this.maintenanceStarted=false});
  },"""
if new_presence not in text:
    if old_presence not in text: raise SystemExit('attachPresence atual não encontrado')
    text=text.replace(old_presence,new_presence,1)

# =========================================================
# EMPTY ROOM WATCHER
# =========================================================
old_callback="""          this.roomCache[key]=s.exists()?s.val():null;
          // O host acabou de gerar esse snapshot; processá-lo outra vez localmente"""
new_callback="""          this.roomCache[key]=s.exists()?s.val():null;
          if(key==='players'&&!s.exists()){this.removeRoomIfEmpty(code).catch(()=>{});return}
          // O host acabou de gerar esse snapshot; processá-lo outra vez localmente"""
if new_callback not in text:
    if old_callback not in text: raise SystemExit('Callback de subscribeRoom não encontrado')
    text=text.replace(old_callback,new_callback,1)

# =========================================================
# LEAVE ROOM: LAST PLAYER CLEANUP
# =========================================================
old_leave="  async leaveRoom(){if(!this.roomId||!this.localPlayerId)return;const F=await this.waitFirebase(),code=this.roomId;try{await F.remove(F.ref(F.firebaseDb,`rooms/${code}/players/${this.localPlayerId}`));await F.remove(F.ref(F.firebaseDb,`rooms/${code}/inputs/${this.localPlayerId}`));if(this.isHost)await F.remove(F.ref(F.firebaseDb,`rooms/${code}`))}catch(_){}this.roomUnsubscribes.forEach(fn=>fn());this.roomUnsubscribes=[];this.roomCache={};this.roomId=null;this.hostUid=null;this.roomStatus='idle'},"
new_leave="""  async leaveRoom(){
    if(!this.roomId||!this.localPlayerId)return;
    const F=await this.waitFirebase(),code=this.roomId,uid=this.localPlayerId,wasHost=this.isHost;
    this.leaving=true;this.stopRoomHeartbeat();
    try{
      await F.remove(F.ref(F.firebaseDb,`rooms/${code}/players/${uid}`));
      await F.remove(F.ref(F.firebaseDb,`rooms/${code}/inputs/${uid}`));
      if(wasHost)await F.remove(F.ref(F.firebaseDb,`rooms/${code}`));
      else await this.removeRoomIfEmpty(code,false);
    }catch(_){}
    this.roomUnsubscribes.forEach(fn=>{try{fn()}catch(_){}});this.roomUnsubscribes=[];
    this.roomCache={};this.roomId=null;this.hostUid=null;this.roomStatus='idle';this.leaving=false;
  },"""
if new_leave not in text:
    if old_leave not in text: raise SystemExit('leaveRoom atual não encontrado')
    text=text.replace(old_leave,new_leave,1)

# =========================================================
# START MAINTENANCE WITH FIREBASE
# =========================================================
old_ready="window.addEventListener('firebase-ready',()=>{const s=$('#firebaseStatus');if(s)s.textContent='Firebase: online';initFirebaseAccountUI().catch(console.error)});if(window.FirebaseBridge)initFirebaseAccountUI().catch(console.error);"
new_ready="window.addEventListener('firebase-ready',()=>{const s=$('#firebaseStatus');if(s)s.textContent='Firebase: online';NetworkAdapter.startRoomMaintenance();initFirebaseAccountUI().catch(console.error)});if(window.FirebaseBridge){NetworkAdapter.startRoomMaintenance();initFirebaseAccountUI().catch(console.error)}"
if new_ready not in text:
    if old_ready not in text: raise SystemExit('Inicialização firebase-ready não encontrada')
    text=text.replace(old_ready,new_ready,1)

required=[
 marker,new_codes,
 'const ROOM_INACTIVITY_MS=10*60*1000;',
 'const ROOM_HEARTBEAT_MS=30*1000;',
 'const ROOM_CLEANUP_MS=60*1000;',
 'function roomIsExpired(room,now)',
 'lastSeen:F.serverTimestamp()',
 'async touchPresence()',
 'startRoomHeartbeat()',
 'async removeRoomIfEmpty(code,notifyCurrent=true)',
 'async cleanupRooms()',
 "F.ref(F.firebaseDb,'.info/serverTimeOffset')",
 "F.ref(F.firebaseDb,'rooms')",
 "if(key==='players'&&!s.exists()){this.removeRoomIfEmpty(code).catch(()=>{});return}",
 'else await this.removeRoomIfEmpty(code,false);',
 'NetworkAdapter.startRoomMaintenance();',
 "const WAR_UNIT_COSTS=Object.freeze({warrior:50,king:400,golem:550,mage:550,dragon:450});",
 'e.hp=e.maxHp=280;',
 'e.shield=e.maxShield=280;',
 'e.damage=35;',
 'e.hp=e.maxHp=150;',
 'e.shield=e.maxShield=100;',
 'WAR CAMERA COMPOSITOR 2026-09-09',
]
missing=[m for m in required if m not in text]
if missing: raise SystemExit('Validação final falhou: '+repr(missing))

forbidden=[old_codes,"const ROOM_COLOR_NAMES=["]
present=[m for m in forbidden if m in text]
if present: raise SystemExit('Configuração antiga ainda presente: '+repr(present))

path.write_text(text,encoding='utf-8')
print('Room codes expanded; presence heartbeat and 10-minute/empty-room cleanup installed.')
