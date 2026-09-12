from pathlib import Path
import json
import re

p=Path('index.html')
t=p.read_text(encoding='utf-8')
MARK='ROOM FLOW + BOOT PRELOAD 2026-09-12'
if MARK in t:
    print('Room/boot/Brown v2 patch already applied.')
    raise SystemExit(0)

def rep(old,new,label,count=1):
    global t
    n=t.count(old)
    if n!=count:
        raise SystemExit(f'{label}: expected {count} match(es), found {n}')
    t=t.replace(old,new,count)

def slice_replace(start_marker,end_marker,new_block,label):
    global t
    start=t.find(start_marker)
    if start<0: raise SystemExit(f'{label}: start marker missing')
    end=t.find(end_marker,start)
    if end<0: raise SystemExit(f'{label}: end marker missing')
    t=t[:start]+new_block+t[end:]

# ---------- Brown Warrior: stability, cadence and visual alignment ----------
rep(
    '.entity-visual.brown-warrior-visual .entity-body{left:-7px;top:-9px;width:110px;height:110px;object-fit:contain}',
    '.entity-visual.brown-warrior-visual .entity-body{left:0;top:-9px;width:110px;height:110px;object-fit:contain}',
    'brown body alignment'
)

rep(
    ' e.brownNormalCount=0;\n state.entities.push(e);',
    ' e.brownNormalCount=0;\n // Estabilidade semelhante ao Golem: golpes comuns reduzem a velocidade, mas não travam a aproximação.\n e.brownKnockCycle=0;\n e.brownSlowUntil=0;\n state.entities.push(e);',
    'brown spawn stability'
)

rep('e.brownNormalCount=Math.min(6,(Number(e.brownNormalCount)||0)+1);',
    'e.brownNormalCount=Math.min(4,(Number(e.brownNormalCount)||0)+1);',
    'brown normal counter')

old_hit=""" let knockForce=options.knockForce??430;
 let knockTime=options.knockTime??.28;
 let applyKnockback=true;
 const golemVsWarriorMage=target.type==='golem' && (attacker.type==='warrior' || attacker.type==='brownWarrior' || attacker.type==='king' || attacker.type==='mage');

 // Golem: contra Guerreiro/Mago o dano entra normalmente, mas ele é muito mais estável.
 // Mantém o ciclo já definido: 1 impacto empurra, os 3 seguintes não.
 // Mesmo no impacto que empurra, a força/duração são reduzidas e a IA continua andando.
 if(golemVsWarriorMage){
   const cycle=Number(target.golemKnockCycle)||0;
   applyKnockback=(cycle===0);
   target.golemKnockCycle=(cycle+1)%4;
   target.golemSlowUntil=Math.max(Number(target.golemSlowUntil)||0,performance.now()+650);
   knockForce*=0.24;
   knockTime=Math.min(knockTime,0.11);
 }
 if(applyKnockback){
   target.knockTime=knockTime;
   target.knockVX=dx*knockForce;
   target.knockVY=dy*knockForce;
   if(!golemVsWarriorMage)target.moving=false;
 }"""
new_hit=""" let knockForce=options.knockForce??430;
 let knockTime=options.knockTime??.28;
 let applyKnockback=true;
 const golemVsWarriorMage=target.type==='golem' && (attacker.type==='warrior' || attacker.type==='brownWarrior' || attacker.type==='king' || attacker.type==='mage');
 const brownStableHit=target.type==='brownWarrior' && (attacker.type==='warrior' || attacker.type==='brownWarrior' || attacker.type==='king' || attacker.type==='mage');

 // Golem: contra Guerreiro/Mago o dano entra normalmente, mas ele é muito mais estável.
 // Mantém o ciclo já definido: 1 impacto empurra, os 3 seguintes não.
 // Mesmo no impacto que empurra, a força/duração são reduzidas e a IA continua andando.
 if(golemVsWarriorMage){
   const cycle=Number(target.golemKnockCycle)||0;
   applyKnockback=(cycle===0);
   target.golemKnockCycle=(cycle+1)%4;
   target.golemSlowUntil=Math.max(Number(target.golemSlowUntil)||0,performance.now()+650);
   knockForce*=0.24;
   knockTime=Math.min(knockTime,0.11);
 }
 // Guerreira Marrom: estabilidade intermediária. Ela recebe o dano completo,
 // porém só 1 de cada 3 impactos comuns realmente empurra. Mesmo assim continua
 // andando, com redução temporária de velocidade, em vez de ficar travada.
 if(brownStableHit){
   const cycle=Number(target.brownKnockCycle)||0;
   applyKnockback=(cycle===0);
   target.brownKnockCycle=(cycle+1)%3;
   target.brownSlowUntil=Math.max(Number(target.brownSlowUntil)||0,performance.now()+600);
   knockForce*=0.34;
   knockTime=Math.min(knockTime,0.12);
 }
 if(applyKnockback){
   target.knockTime=knockTime;
   target.knockVX=dx*knockForce;
   target.knockVY=dy*knockForce;
   if(!golemVsWarriorMage&&!brownStableHit)target.moving=false;
 }"""
rep(old_hit,new_hit,'brown stability hit system')

old_ai="""function aiFightBrownWarrior(e,dt,forcedTeam,preparedCandidates=null){
 if(!e.alive||e.knockTime>0){e.moving=false;return}
 if(e.pendingBrownAttack){e.moving=false;return}
 const candidates=preparedCandidates||state.entities;
 const target=nearestEngageableCandidate(e,candidates,forcedTeam,false);
 if(!target){e.moving=false;e.target=null;return}
 e.target=target;
 const dx=target.x-e.x,dy=target.y-e.y,d=Math.hypot(dx,dy)||1;
 e.heading=Math.atan2(dy,dx);if(Math.abs(dx)>4)e.facing=dx<0?-1:1;
 if((Number(e.brownNormalCount)||0)>=6){
   if(d<=125&&startBrownWarriorAttack(e,'special',target))return;
   if(d>125){e.x+=dx/d*e.speed*dt;e.y+=dy/d*e.speed*dt;e.moving=true}else e.moving=false;
 }else if(d<=92){
   if(startBrownWarriorAttack(e,'normal',target))return;
   e.moving=false;
 }else{
   e.x+=dx/d*e.speed*dt;e.y+=dy/d*e.speed*dt;e.moving=true;
 }
 e.x=clamp(e.x,35,state.world.w-35);e.y=clamp(e.y,35,state.world.h-35);
}"""
new_ai="""function aiFightBrownWarrior(e,dt,forcedTeam,preparedCandidates=null){
 if(!e.alive){e.moving=false;return}
 if(e.pendingBrownAttack){e.moving=false;return}
 const now=performance.now();
 const moveSpeed=e.speed*((Number(e.brownSlowUntil)||0)>now?0.68:1);
 const candidates=preparedCandidates||state.entities;
 const target=nearestEngageableCandidate(e,candidates,forcedTeam,false);
 if(!target){e.moving=false;e.target=null;return}
 e.target=target;
 const dx=target.x-e.x,dy=target.y-e.y,d=Math.hypot(dx,dy)||1;
 e.heading=Math.atan2(dy,dx);if(Math.abs(dx)>4)e.facing=dx<0?-1:1;
 // 4 ataques normais completos; o 5º ataque é obrigatoriamente o especial.
 if((Number(e.brownNormalCount)||0)>=4){
   if(d<=125&&startBrownWarriorAttack(e,'special',target))return;
   if(d>125){e.x+=dx/d*moveSpeed*dt;e.y+=dy/d*moveSpeed*dt;e.moving=true}else e.moving=false;
 }else if(d<=92){
   if(startBrownWarriorAttack(e,'normal',target))return;
   e.moving=false;
 }else{
   e.x+=dx/d*moveSpeed*dt;e.y+=dy/d*moveSpeed*dt;e.moving=true;
 }
 e.x=clamp(e.x,35,state.world.w-35);e.y=clamp(e.y,35,state.world.h-35);
}"""
rep(old_ai,new_ai,'brown AI cadence and slow movement')

# ---------- Firebase room flow: remove heavy reads from the critical path ----------
rep(
    '  presenceTimer:null,cleanupTimer:null,serverOffsetUnsub:null,serverTimeOffset:0,cleanupRunning:false,maintenanceStarted:false,leaving:false,',
    '  presenceTimer:null,cleanupTimer:null,serverOffsetUnsub:null,serverTimeOffset:0,cleanupRunning:false,maintenanceStarted:false,leaving:false,createPromise:null,joinPromise:null,',
    'network in-flight guards'
)

new_create_join="""  async createRoom(snapshot){
    if(this.createPromise)return this.createPromise;
    this.createPromise=(async()=>{
      const F=await this.waitFirebase(),user=await this.ensureAuth();
      // Clique repetido durante a criação reutiliza a mesma sala, nunca cria outra por cima.
      if(this.roomId)return {code:this.roomId,offline:false,reused:true};
      const settings={mode:snapshot.mode,pveTime:snapshot.pveTime,warTime:snapshot.warTime,rounds:snapshot.rounds,difficulty:snapshot.difficulty,speed:snapshot.speed,gems:snapshot.gems};
      const roomCandidates=[...ROOM_CODES].sort(()=>Math.random()-.5);
      const now=this.serverNow();
      let code=null;
      // Reserva atômica: elimina corrida entre dois hosts escolhendo o mesmo código.
      // Não fazemos mais cleanup global antes de criar; isso removia/lia várias salas
      // e era a principal espera perceptível no botão Criar sala.
      for(const c of roomCandidates){
        const rr=F.ref(F.firebaseDb,`rooms/${c}`);
        const result=await F.runTransaction(rr,current=>{
          if(current&&!roomIsExpired(current,now))return;
          return {
            code:c,hostUid:user.uid,status:'lobby',npcCount:0,
            createdAt:F.serverTimestamp(),lastActivityAt:F.serverTimestamp(),settings,
            players:{[user.uid]:{uid:user.uid,name:getCurrentNick(),human:true,slot:0,color:COLORS[0],joinedAt:F.serverTimestamp(),lastSeen:F.serverTimestamp()}}
          };
        });
        if(result.committed){code=c;break}
      }
      if(!code)throw Error('Falha ao gerar sala');
      this.roomId=code;this.hostUid=user.uid;this.localPlayerId=user.uid;
      await this.attachPresence(code,user.uid);
      this.subscribeRoom(code);
      // Manutenção roda fora do caminho crítico da navegação.
      this.cleanupRooms().catch(()=>{});
      return {code,offline:false};
    })();
    try{return await this.createPromise}finally{this.createPromise=null}
  },
  async joinRoom(code){
    if(this.joinPromise)return this.joinPromise;
    this.joinPromise=(async()=>{
      const F=await this.waitFirebase(),user=await this.ensureAuth();
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
      this.cleanupRooms().catch(()=>{});
      return {ok:true,room,offline:false};
    })();
    try{return await this.joinPromise}finally{this.joinPromise=null}
  },
"""
slice_replace('  async createRoom(snapshot){','  async attachPresence(code,uid){',new_create_join,'create/join flow')

new_touch="""  async touchPresence(){
    const code=this.roomId,uid=this.localPlayerId;if(!code||!uid)return;
    const F=await this.waitFirebase(),rr=F.ref(F.firebaseDb,`rooms/${code}`);
    try{
      // Antes o heartbeat baixava a sala inteira (inclusive /game) a cada 30 s.
      // Agora lê só o nó minúsculo deste jogador e atualiza dois timestamps.
      const playerRef=F.ref(F.firebaseDb,`rooms/${code}/players/${uid}`);
      const snap=await F.get(playerRef);
      if(!snap.exists()){this.expireLocalRoom(code);return}
      const patch={lastActivityAt:F.serverTimestamp()};
      patch[`players/${uid}/lastSeen`]=F.serverTimestamp();
      await F.update(rr,patch);
    }catch(_){}
  },
"""
slice_replace('  async touchPresence(){','  startRoomHeartbeat(){',new_touch,'light heartbeat')

new_cleanup="""  async cleanupRooms(){
    if(this.cleanupRunning)return;
    this.cleanupRunning=true;
    try{
      const F=await this.waitFirebase(),now=this.serverNow();
      // Uma única leitura de /rooms. A versão anterior fazia outra leitura por sala,
      // multiplicando latência e tráfego justamente durante criar/entrar.
      const all=await F.get(F.ref(F.firebaseDb,'rooms'));
      if(!all.exists())return;
      const rooms=all.val()||{};
      const expired=[];
      for(const [code,room] of Object.entries(rooms))if(roomIsExpired(room,now))expired.push(code);
      if(expired.length){
        await Promise.all(expired.map(code=>F.remove(F.ref(F.firebaseDb,`rooms/${code}`)).catch(()=>{})));
        for(const code of expired)this.expireLocalRoom(code);
      }
    }catch(_){}finally{this.cleanupRunning=false}
  },
"""
slice_replace('  async cleanupRooms(){','  startRoomMaintenance(){',new_cleanup,'single-read cleanup')

# UI-level double-click guards.
old_create_ui="""$('#createRoomBtn').onclick=async()=>{
  const res=await NetworkAdapter.createRoom({...state}); state.roomCode=res.code; $('#roomCode').textContent=res.code;
  $('#lobbyModeTitle').textContent=state.mode==='pve'?'Players vs Inimigos':'Mestre da Guerra';
  setLobbySkin(state.mode);
  renderPlayers(); navigateScreen('lobbyScreen');
};
$('#confirmJoin').onclick=async()=>{
  const code=normalizeRoomCode($('#roomCodeInput').value);
  const res=await NetworkAdapter.joinRoom(code);
  if(res.ok){
    const joinedMode=res.room.settings?.mode||state.mode;
    state.mode=joinedMode;
    state.roomCode=code;
    $('#roomCode').textContent=code;
    $('#lobbyModeTitle').textContent=joinedMode==='pve'?'Players vs Inimigos':'Mestre da Guerra';
    setLobbySkin(joinedMode);
    navigateScreen('lobbyScreen');
  }else $('#joinError').textContent=res.reason==='full'?'Sala cheia.':res.reason==='started'?'A partida já começou.':'Sala não encontrada.';
};"""
new_create_ui="""let roomCreateInFlight=false,roomJoinInFlight=false;
$('#createRoomBtn').onclick=async()=>{
  if(roomCreateInFlight)return;
  roomCreateInFlight=true;
  const btn=$('#createRoomBtn'),oldText=btn.textContent;btn.disabled=true;btn.textContent='Criando...';
  try{
    const res=await NetworkAdapter.createRoom({...state}); state.roomCode=res.code; $('#roomCode').textContent=res.code;
    $('#lobbyModeTitle').textContent=state.mode==='pve'?'Players vs Inimigos':'Mestre da Guerra';
    setLobbySkin(state.mode);
    renderPlayers(); navigateScreen('lobbyScreen');
  }catch(err){
    console.error(err);flash('Não foi possível criar a sala.',1.5);
  }finally{
    roomCreateInFlight=false;btn.textContent=oldText;
    if($('#configScreen').style.display!=='none')btn.disabled=false;
  }
};
$('#confirmJoin').onclick=async()=>{
  if(roomJoinInFlight)return;
  roomJoinInFlight=true;
  const btn=$('#confirmJoin'),oldText=btn.textContent;btn.disabled=true;btn.textContent='Entrando...';
  try{
    const code=normalizeRoomCode($('#roomCodeInput').value);
    const res=await NetworkAdapter.joinRoom(code);
    if(res.ok){
      const joinedMode=res.room.settings?.mode||state.mode;
      state.mode=joinedMode;
      state.roomCode=code;
      $('#roomCode').textContent=code;
      $('#lobbyModeTitle').textContent=joinedMode==='pve'?'Players vs Inimigos':'Mestre da Guerra';
      setLobbySkin(joinedMode);
      navigateScreen('lobbyScreen');
    }else $('#joinError').textContent=res.reason==='full'?'Sala cheia.':res.reason==='started'?'A partida já começou.':'Sala não encontrada.';
  }catch(err){console.error(err);$('#joinError').textContent='Falha de conexão. Tente novamente.'}
  finally{roomJoinInFlight=false;btn.textContent=oldText;btn.disabled=false}
};"""
rep(old_create_ui,new_create_ui,'room UI guards')

# Slightly lower RTDB full-state write rate; clients already interpolate positions.
rep("const networkPushInterval=state.mode==='war'?125:100;",
    "const networkPushInterval=state.mode==='war'?150:120;",
    'network push interval')

# ---------- Loading screen ----------
# Capture every literal game media asset currently referenced in the page, including
# the two external Postimg arena images. This keeps the manifest in sync with the file.
asset_urls=set(re.findall(r"assets/[A-Za-z0-9_./%+ -]+\.(?:png|gif|jpe?g|webp|mp3|ogg|wav)",t,re.I))
asset_urls.update(re.findall(r"https://i\.postimg\.cc/[A-Za-z0-9_./%+-]+\.(?:png|gif|jpe?g|webp)",t,re.I))
asset_urls={u.replace(' ','%20') for u in asset_urls}
manifest=json.dumps(sorted(asset_urls),ensure_ascii=False,separators=(',',':'))

boot_css="""
/* ===== BOOT LOADER 2026-09-12 ===== */
body.booting{background:#000;overflow:hidden}
body.booting #landscapeRoot{visibility:hidden}
#bootLoader{position:fixed;inset:0;z-index:60000;background:#000;color:#fff;display:flex;align-items:center;justify-content:center;font-family:Arial,sans-serif;transition:opacity .22s ease;pointer-events:auto}
#bootLoader.done{opacity:0;pointer-events:none}
#bootLoaderBox{width:min(420px,78vw);text-align:center}
#bootLoaderTitle{font-size:14px;font-weight:800;letter-spacing:3px;margin-bottom:14px}
#bootLoaderPercent{font-size:34px;font-weight:900;font-variant-numeric:tabular-nums;margin-bottom:12px}
#bootLoaderTrack{height:8px;border:1px solid #555;background:#111;overflow:hidden;border-radius:999px}
#bootLoaderBar{height:100%;width:0%;background:#fff;transition:width .12s linear}
"""
if t.count('</style>')<1: raise SystemExit('style close marker missing')
t=t.replace('</style>',boot_css+'\n</style>',1)

rep('<body>','''<body class="booting">
<div id="bootLoader" role="status" aria-live="polite" aria-label="Carregando jogo">
  <div id="bootLoaderBox">
    <div id="bootLoaderTitle">CARREGANDO</div>
    <div id="bootLoaderPercent">0%</div>
    <div id="bootLoaderTrack"><div id="bootLoaderBar"></div></div>
  </div>
</div>''','boot loader HTML')

boot_js=f"""
/* {MARK} */
const BOOT_ASSET_URLS=Object.freeze({manifest});
const BOOT_FETCH_CONCURRENCY=4;
function setBootProgress(value){{
 const pct=Math.max(0,Math.min(100,Math.round(value)));
 const text=document.getElementById('bootLoaderPercent'),bar=document.getElementById('bootLoaderBar');
 if(text)text.textContent=pct+'%';if(bar)bar.style.width=pct+'%';
}}
async function bootFallbackMedia(url){{
 return new Promise(resolve=>{{
   const clean=url.split('?')[0].toLowerCase();
   if(/\.(mp3|ogg|wav)$/.test(clean)){{
     const a=new Audio();let settled=false;
     const done=ok=>{{if(settled)return;settled=true;a.oncanplaythrough=a.onerror=null;resolve(ok)}};
     a.preload='auto';a.oncanplaythrough=()=>done(true);a.onerror=()=>done(false);a.src=url;a.load();setTimeout(()=>done(a.readyState>=3),30000);
   }}else{{
     const img=new Image();let settled=false;
     const done=ok=>{{if(settled)return;settled=true;img.onload=img.onerror=null;resolve(ok)}};
     img.decoding='async';img.onload=()=>done(true);img.onerror=()=>done(false);img.src=url;setTimeout(()=>done(img.complete&&img.naturalWidth>0),30000);
   }}
 }});
}}
async function bootFetchAsset(url){{
 for(let attempt=0;attempt<2;attempt++){{
   const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),90000);
   try{{
     const r=await fetch(url,{{cache:'force-cache',signal:controller.signal,credentials:url.startsWith('assets/')?'same-origin':'omit'}});
     if(!r.ok)throw Error('HTTP '+r.status);
     if(r.body){{
       const reader=r.body.getReader();
       while(true){{const part=await reader.read();if(part.done)break}}
     }}else await r.arrayBuffer();
     clearTimeout(timer);return true;
   }}catch(_){{clearTimeout(timer);if(attempt===0)continue}}
 }}
 return bootFallbackMedia(url);
}}
async function runBootLoader(){{
 const urls=[...new Set(BOOT_ASSET_URLS)];
 const total=urls.length+1;let completed=0,failed=0,next=0;
 setBootProgress(0);
 const finishTask=ok=>{{if(!ok)failed++;completed++;setBootProgress(completed/total*100)}};
 const worker=async()=>{{
   while(true){{const i=next++;if(i>=urls.length)return;finishTask(await bootFetchAsset(urls[i]))}}
 }};
 await Promise.all(Array.from({{length:Math.min(BOOT_FETCH_CONCURRENCY,Math.max(1,urls.length))}},worker));
 // Firebase/auth também aquece antes do menu; assim o primeiro Criar sala não paga esse custo.
 let authReady=true;
 try{{
   await Promise.race([NetworkAdapter.ensureAuth(),new Promise((_,reject)=>setTimeout(()=>reject(Error('firebase warmup timeout')),10000))]);
 }}catch(_){{authReady=false}}
 finishTask(authReady);
 setBootProgress(100);
 if(failed&&typeof assetWarning!=='undefined'&&assetWarning){{assetWarning.textContent=`${{failed}} recurso(s) não puderam ser pré-carregados.`;assetWarning.classList.add('show')}}
 document.body.classList.remove('booting');
 const loader=document.getElementById('bootLoader');
 if(loader){{loader.classList.add('done');setTimeout(()=>loader.remove(),260)}}
}}
"""
rep('const state = {',boot_js+'\nconst state = {','boot JS')

# Start boot only after all synchronous handlers/constants in this script have initialized.
rep('requestAnimationFrame(loop);\n\nfunction updateEntities(dt){',
    "requestAnimationFrame(loop);\nrunBootLoader().catch(err=>{console.error(err);document.body.classList.remove('booting');document.getElementById('bootLoader')?.remove()});\n\nfunction updateEntities(dt){",
    'boot start')

p.write_text(t,encoding='utf-8')
print(f'Applied room/boot/Brown v2 patch with {len(asset_urls)} preloaded media URLs.')
