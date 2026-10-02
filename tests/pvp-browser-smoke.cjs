const assert=require('node:assert/strict');
const fs=require('node:fs'),http=require('node:http'),path=require('node:path');
const {chromium}=require('playwright');

const root=path.resolve(__dirname,'..');
const original=fs.readFileSync(path.join(root,'index.html'),'utf8');
const gif=Buffer.from('R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=','base64');
const firebaseStub=String.raw`
(() => {
 const user={uid:'browser-smoke-user',displayName:'Tester',isAnonymous:false};
 const database={rooms:{},profiles:{}},subscriptions=new Set(),disconnectOps=new Map();
 const parts=path=>String(path).split('/').filter(Boolean);
 function read(path){return parts(path).reduce((obj,key)=>obj?.[key],database)??null}
 function snapshotValue(path){return path==='.info/connected'?true:path==='.info/serverTimeOffset'?0:read(path)}
 function snapshot(path){const value=snapshotValue(path);return {val:()=>value,exists:()=>value!==null}}
 function write(path,value){
   const tokens=parts(path);let current=database;
   for(let i=0;i<tokens.length-1;i++)current=current[tokens[i]]??={};
   if(!tokens.length)return;
   if(value===null)delete current[tokens.at(-1)];
   else current[tokens.at(-1)]=value;
   queueMicrotask(()=>{for(const listener of [...subscriptions])try{listener.cb(snapshot(listener.path))}catch(e){console.error(e)}});
 }
 const F={
  firebaseAuth:{currentUser:user,authStateReady:async()=>{}},firebaseDb:{},
  googleProvider:{},ref:(_db,path)=>path,
  onAuthStateChanged:(_auth,cb)=>{queueMicrotask(()=>cb(user));return()=>{}},
  signInAnonymously:async()=>({user}),signInWithPopup:async()=>({user}),getRedirectResult:async()=>null,
  signOut:async()=>{},updateProfile:async()=>{},
  serverTimestamp:()=>Date.now(),
  get:async path=>({val:()=>read(path),exists:()=>read(path)!==null}),
  set:async(path,value)=>write(path,value),
  update:async(path,patch)=>{for(const [key,val] of Object.entries(patch))write(path+'/'+key,val)},
  remove:async path=>write(path,null),
  onDisconnect:path=>({
    remove:async()=>{disconnectOps.set(path,{type:'remove'})},
    set:async value=>{disconnectOps.set(path,{type:'set',value})},
    cancel:async()=>{disconnectOps.delete(path)}
  }),
  onValue:(path,cb)=>{const listener={path,cb};subscriptions.add(listener);
    queueMicrotask(()=>cb(snapshot(path)));
    return()=>subscriptions.delete(listener);
  },
  runTransaction:async(path,fn)=>{
    const current=read(path);
    if(/^rooms\/[^/]+$/.test(path)&&current!==null){
      const err=new Error('PERMISSION_DENIED: whole-room rewrite blocked by per-player rules');
      err.code='PERMISSION_DENIED';throw err;
    }
    const candidate=fn(current);if(candidate===undefined)return {committed:false,snapshot:{val:()=>read(path)}};
    write(path,candidate);return {committed:true,snapshot:{val:()=>read(path)}};
  }
 };
 window.FirebaseBridge=F;
 queueMicrotask(()=>window.dispatchEvent(new Event('firebase-ready')));
})();
`;
// Inject a test-only hook inside the game's closure; nothing is exported by
// the production build and no production code is changed for browser tests.
const pvpTestHook=`window.__pvpBrowserTest={
 accountXpReady(){return accountProgress.verified&&accountProgress.status==='ready'},
 roundClock(){return {duration:state.pvpRoundDuration,left:state.timeLeft}},
 humanRoster(){return state.players.filter(p=>p.human).map(p=>p.id)},
 remoteHumanLabel(){
   const remote=state.entities.find(e=>e.alive&&!e.pvpMinion&&e.ownerId==='remote-user');
   return remote?entityUiDisplayName(remote):null;
 },
 guestPredictionStep(){
   const hero=pvpLocalHero();if(!hero)return null;
   const oldHost=NetworkAdapter.hostUid,oldD=keys.d;
   const before={x:hero.x,y:hero.y};
   hero.netAuthX=hero.x;hero.netAuthY=hero.y;hero.knockTime=0;hero.pvpWarriorChargeUntil=0;
   NetworkAdapter.hostUid='remote-host';keys.d=true;
   pvpPredictGuestLocal(.05);
   keys.d=oldD;NetworkAdapter.hostUid=oldHost;
   return {dx:hero.x-before.x,dy:hero.y-before.y,x:hero.x,y:hero.y};
 },
 staleSnapshotReconciliation(){
   const hero=pvpLocalHero();if(!hero)return null;
   const saved={
     x:hero.x,y:hero.y,heading:hero.heading,facing:hero.facing,moving:hero.moving,knockTime:hero.knockTime,
     pvpWarriorChargeUntil:hero.pvpWarriorChargeUntil,netAuthX:hero.netAuthX,netAuthY:hero.netAuthY,
     netAuthInputSeq:hero.netAuthInputSeq,netAuthArrivalAt:hero.netAuthArrivalAt,
     hostUid:NetworkAdapter.hostUid,pvpInputSeq:NetworkAdapter.pvpInputSeq,
     latestHostView:pvpLatestHostView,regional:pvpLocalRegionalAuthority,d:keys.d
   };
   const now=performance.now();
   NetworkAdapter.hostUid='remote-host';NetworkAdapter.pvpInputSeq=10;pvpLatestHostView=null;pvpSetLocalRegionalAuthority(false);
   hero.knockTime=0;hero.pvpWarriorChargeUntil=0;hero.netAuthX=hero.x-310;hero.netAuthY=hero.y;
   hero.netAuthInputSeq=8;hero.netAuthArrivalAt=now;keys.d=true;
   const before=hero.x;pvpPredictGuestLocal(1/60);const afterStale=hero.x;
   keys.d=false;hero.netAuthX=hero.x-80;hero.netAuthY=hero.y;hero.netAuthInputSeq=10;hero.netAuthArrivalAt=performance.now();
   const beforeAck=hero.x;pvpPredictGuestLocal(1/60);const afterAck=hero.x;
   const result={staleForward:afterStale>before,staleDidNotSnap:afterStale>before-20,ackedCorrected:afterAck<beforeAck};
   Object.assign(hero,{x:saved.x,y:saved.y,heading:saved.heading,facing:saved.facing,moving:saved.moving,knockTime:saved.knockTime,
     pvpWarriorChargeUntil:saved.pvpWarriorChargeUntil,netAuthX:saved.netAuthX,netAuthY:saved.netAuthY,
     netAuthInputSeq:saved.netAuthInputSeq,netAuthArrivalAt:saved.netAuthArrivalAt});
   NetworkAdapter.hostUid=saved.hostUid;NetworkAdapter.pvpInputSeq=saved.pvpInputSeq;pvpLatestHostView=saved.latestHostView;
   pvpSetLocalRegionalAuthority(saved.regional);keys.d=saved.d;
   return result;
 },
 regionalAuthorityCycle(){
   const remote=state.entities.find(e=>e.alive&&!e.pvpMinion&&e.ownerId==='remote-user');
   if(!remote)return null;
   const saved={x:remote.x,y:remote.y,heading:remote.heading,facing:remote.facing,moving:remote.moving,
     knockTime:remote.knockTime,pvpWarriorChargeUntil:remote.pvpWarriorChargeUntil,pvpRegionalAuthorityUid:remote.pvpRegionalAuthorityUid};
   const uid=NetworkAdapter.localPlayerId,now=performance.now(),packetAt=NetworkAdapter.serverNow();
   const own=pvpLocalHero(),ownSaved={x:own.x,y:own.y};
   own.x=300;own.y=300;remote.x=1400;remote.y=1150;remote.knockTime=0;remote.pvpWarriorChargeUntil=0;
   pvpCoordinateNearbyHumans();
   pvpRemoteRegionalAuthority.delete('remote-user');
   const farView={hostUid:uid,left:250,top:250,right:800,bottom:700};
   const accepted=pvpApplyDelegatedRemotePose(remote,{
     t:packetAt,pvpRegionalAuthority:true,
     pvpRegionalPose:{seq:1,x:1460,y:1150,heading:0,facing:1,moving:true}
   },now,farView);
   const moved=remote.x>1400;
   const nearView={hostUid:uid,left:1200,top:900,right:1650,bottom:1300};
   const yielded=pvpApplyDelegatedRemotePose(remote,{
     t:packetAt+16,pvpRegionalAuthority:true,
     pvpRegionalPose:{seq:2,x:1500,y:1150,heading:0,facing:1,moving:true}
   },now+16,nearView);
   Object.assign(remote,saved);Object.assign(own,ownSaved);pvpCoordinateNearbyHumans();pvpRemoteRegionalAuthority.delete('remote-user');
   return {accepted,moved,yielded};
 },
 distributedRegionCycle(){
   const remote=state.entities.find(e=>e.alive&&!e.pvpMinion&&e.ownerId==='remote-user');
   const template=state.entities.find(e=>e.alive&&e.pvpMinion&&e.team==='pvp-enemy');
   if(!remote||!template)return null;
   const hostView=pvpCurrentAuthorityView(),now=performance.now();
   const bounds=pvpArenaBounds(30),cx=(Number(hostView.left)+Number(hostView.right))/2,cy=(Number(hostView.top)+Number(hostView.bottom))/2;
   const corners=[
     {x:bounds.left,y:bounds.top},{x:bounds.right,y:bounds.top},
     {x:bounds.left,y:bounds.bottom},{x:bounds.right,y:bounds.bottom}
   ];
   corners.sort((a,b)=>((b.x-cx)**2+(b.y-cy)**2)-((a.x-cx)**2+(a.y-cy)**2));
   const farX=corners[0].x,farY=corners[0].y;
   const remoteSaved={x:remote.x,y:remote.y,pvpRegionalAuthorityUid:remote.pvpRegionalAuthorityUid,pvpRegionalEpoch:remote.pvpRegionalEpoch};
   const templateSaved={...template,pendingDragonAttack:template.pendingDragonAttack?{...template.pendingDragonAttack}:null};
   const regionalId=template.id;
   const remotePacket={...remote,x:farX,y:farY,alive:true,pvpRegionalAuthorityUid:null,pvpRegionalEpoch:0};
   const regionalEnemy={...template,id:regionalId,x:farX-55,y:farY-25,hp:73,maxHp:100,shield:12,maxShield:50,
     alive:true,deathStarted:0,removeAt:0,pvpRegionalAuthorityUid:null,pvpRegionalEpoch:0,
     dragonAttackSerial:9,pendingDragonAttack:{serial:9,startedAt:now-500,endAt:now+900}};
   const view={hostUid:'remote-user',left:Math.max(0,farX-430),top:Math.max(0,farY-350),
     right:Math.min(state.world.w,farX+430),bottom:Math.min(state.world.h,farY+350)};
   const packet={uid:'remote-user',epoch:4,seq:1,active:true,handoff:false,at:NetworkAdapter.serverNow(),
     view,focus:{x:farX,y:farY,entityId:remote.id},
     entities:[pvpPackRegionalEntity(remotePacket,now),pvpPackRegionalEntity(regionalEnemy,now)],
     dragonProjectiles:[],players:[],matchStats:{},pvpDamageEvents:[]};
   remote.x=farX;remote.y=farY;template.x=regionalEnemy.x;template.y=regionalEnemy.y;
   NetworkAdapter.roomCache.regions={'remote-user':packet};pvpHostRegionState.clear();
   pvpIntegrateRemoteRegions(now);
   const leased=state.entities.find(e=>String(e.id)===String(regionalId));
   const first={exists:!!leased,hp:leased?.hp,shield:leased?.shield,owner:leased?.pvpRegionalAuthorityUid,
     remaining:leased?.pendingDragonAttack?Math.round(leased.pendingDragonAttack.endAt-now):0,
     hostSimulates:leased?pvpHostShouldSimulateEntity(leased):true};
   const nextNow=now+80;
   const regionalEnemy2={...regionalEnemy,hp:61,shield:0,pendingDragonAttack:{serial:9,startedAt:now-500,endAt:now+620}};
   NetworkAdapter.roomCache.regions={'remote-user':{...packet,seq:2,active:false,handoff:true,at:NetworkAdapter.serverNow(),
     entities:[pvpPackRegionalEntity({...remotePacket,x:farX-10},nextNow),pvpPackRegionalEntity(regionalEnemy2,nextNow)]}};
   pvpIntegrateRemoteRegions(nextNow);
   const handed=state.entities.find(e=>String(e.id)===String(regionalId));
   const second={hp:handed?.hp,shield:handed?.shield,owner:handed?.pvpRegionalAuthorityUid||null,
     remaining:handed?.pendingDragonAttack?Math.round(handed.pendingDragonAttack.endAt-nextNow):0,
     hostSimulates:handed?pvpHostShouldSimulateEntity(handed):false};
   Object.assign(template,templateSaved);
   remote.x=remoteSaved.x;remote.y=remoteSaved.y;remote.pvpRegionalAuthorityUid=remoteSaved.pvpRegionalAuthorityUid;
   remote.pvpRegionalEpoch=remoteSaved.pvpRegionalEpoch;NetworkAdapter.roomCache.regions={};pvpHostRegionState.clear();
   return {first,second,debug:{hostView,farX,farY,
     allowed:pvpRegionalAuthorityDecision({alive:true,pvpMinion:false,ownerId:'remote-user',x:farX,y:farY},hostView,false),
     fresh:pvpRegionalPacketFresh(packet),players:Object.keys(NetworkAdapter.roomCache.players||{})}};
 },
 async hostMigrationCycle(){
   const F=window.FirebaseBridge,roomId=NetworkAdapter.roomId,local=NetworkAdapter.localPlayerId;
   await NetworkAdapter.setForeground(true);
   await NetworkAdapter.refreshPVPHostDisconnect(NetworkAdapter.roomCache);
   const armed=NetworkAdapter.hostDisconnectSuccessorUid;
   const handoff=await NetworkAdapter.handoffPVPHost('hidden');
   await new Promise(r=>setTimeout(r,0));
   const afterHandoff=(await F.get(F.ref(F.firebaseDb,'rooms/'+roomId+'/hostUid'))).val();
   const runningAfterHandoff=state.running&&state.phase==='combat';
   // Emulate the server-side onDisconnect results of the new remote host closing:
   // authority moves back and the closed player's own presence/input nodes disappear.
   await F.set(F.ref(F.firebaseDb,'rooms/'+roomId+'/hostUid'),local);
   await F.remove(F.ref(F.firebaseDb,'rooms/'+roomId+'/players/remote-user'));
   await F.remove(F.ref(F.firebaseDb,'rooms/'+roomId+'/inputs/remote-user'));
   await new Promise(r=>setTimeout(r,0));
   return {
     armed,handoff,afterHandoff,
     localHost:NetworkAdapter.isHost,host:NetworkAdapter.hostUid,
     runningAfterHandoff,runningNow:state.running&&state.phase==='combat',
     remotePlayer:state.players.some(p=>p.id==='remote-user'),
     remoteEntity:state.entities.some(e=>e.ownerId==='remote-user')
   };
 },
 async roomLifecycleCycle(){
   const F=window.FirebaseBridge,roomId=NetworkAdapter.roomId;
   finishGame('',pvpResult(NetworkAdapter.localPlayerId));
   await new Promise(r=>setTimeout(r,4700));
   const liveSnap=await F.get(F.ref(F.firebaseDb,'rooms/'+roomId));
   const old=Date.now()-5*60*1000;
   await F.set(F.ref(F.firebaseDb,'rooms/OLD123'),{
     code:'OLD123',hostUid:'legacy-user',status:'lobby',createdAt:old,lastActivityAt:old,
     settings:{mode:'pvp'},players:{'legacy-user':{uid:'legacy-user',slot:0,joinedAt:old,lastSeen:old}}
   });
   await NetworkAdapter.cleanupRooms();
   const legacySnap=await F.get(F.ref(F.firebaseDb,'rooms/OLD123'));
   return {
     liveExists:liveSnap.exists(),roomId:NetworkAdapter.roomId,phase:state.phase,
     legacyExists:legacySnap.exists()
   };
 },
 async addRemoteConfirmedPlayer(){
   const F=window.FirebaseBridge,roomId=NetworkAdapter.roomId;
   await F.set(F.ref(F.firebaseDb,'rooms/'+roomId+'/players/remote-user'),{
     uid:'remote-user',name:'Amigo',level:7,human:true,slot:1,color:'#58a6ff',
     clan:'warriors',clanChosen:false,clanConfirmed:false,clanSelectedAt:0,
     pvpHero:'warrior',pvpConfirmed:true,joinedAt:F.serverTimestamp(),lastSeen:F.serverTimestamp()
   });
   return roomId;
 },
 castLocalMageSpecial(){
   const hero=pvpLocalHero();
   if(!hero||hero.pvpHero!=='mageFemale')return false;
   hero.pvpPowerUntil=0;hero.pvpActionUntil=0;hero.attackCooldown=0;
   hero.pvpSpecialReadyAt=performance.now()-1;
   return pvpSpecialAttack(hero);
 },
 castWarriorSpecial(){
   const ally=state.entities.find(e=>e.alive&&e.pvpAllyBot&&e.pvpHero==='mageFemale');
   if(!ally)return false;
   ally.pvpPowerUntil=0;ally.pvpActionUntil=0;ally.attackCooldown=0;
   ally.pvpSpecialReadyAt=performance.now()-1;
   return pvpSpecialAttack(ally);
 },
 warriorFx(){
   const ally=state.entities.find(e=>e.pvpAllyBot&&e.pvpHero==='mageFemale');
   const img=ally&&pvpSpecialFxNodes.get(ally.id);
   return {serial:ally?.pvpSpecialSerial||0,src:!!img?.hasAttribute('src'),
     played:ally?pvpSpecialFxPlayedSerial.get(ally.id):null,
     opacity:Number(img?.style.opacity||0),loaded:!!img?.naturalWidth,
     loading:!!img?.classList.contains('pvp-gif-loading'),
     currentUrl:img?.getAttribute('src')||''};
 },
 expireAndReplayWarriorFx(){
   const ally=state.entities.find(e=>e.pvpAllyBot&&e.pvpHero==='mageFemale');
   if(!ally)return false;
   ally.pvpSpecialFxUntil=performance.now()-1;
   syncPVPSpecialEffects(state.camera.x,state.camera.y,state.camera.zoom,innerWidth,innerHeight);
   ally.pvpSpecialFxUntil=performance.now()+1000;
   syncPVPSpecialEffects(state.camera.x,state.camera.y,state.camera.zoom,innerWidth,innerHeight);
   return !!pvpSpecialFxNodes.get(ally.id);
 },
 dragonFirstHit(){
   const hero=pvpLocalHero();
   if(!hero?.alive)return {armed:false,shot:false};
   const dragon=state.entities.find(e=>e.alive&&e.type==='dragon')||pvpSpawnNPC('dragon');
   dragon.pvpDragonFirstHitSeen=false;dragon.pvpDragonRetaliatePending=false;
   dragon.pendingDragonAttack=null;dragon.dragonFlightState='takeoff';
   dragon.dragonTakeoffEndAt=performance.now()+180;dragon.knockTime=.12;
   const before=state.dragonProjectiles.length;
   pvpCombatHit(dragon,hero,12);
   const armed=dragon.pvpDragonRetaliatePending===true;
   dragon.dragonTakeoffEndAt=performance.now()-1;
   pvpBotAction(dragon,.016);
   return {armed,shot:state.dragonProjectiles.length===before+1,
     correctSource:state.dragonProjectiles.some(p=>p.sourceId===dragon.id),
     cleared:dragon.pvpDragonRetaliatePending===false};
 },
 flameFramesReady(){
   return pvpFlameFrames.has('warriors')&&pvpFlameFrames.has('egypt');
 },
 realFlameFrameHits(){
   const own=pvpLocalHero();if(!own)return null;
   const result=[];
   for(const [clan,key] of [['warriors','mageFemale'],['egypt','egyptMageFemale']]){
     const entry=pvpFlameFrames.get(clan);
     const frameIndex=Math.floor(entry.frames.length*.48);
     const frame=entry.frames[frameIndex],previousEnd=frameIndex?entry.frames[frameIndex-1].end:0;
     const elapsed=previousEnd+Math.max(1,Math.floor((frame.end-previousEnd)/2));
     let px=-1,py=-1;
     for(let y=12;y<43&&px<0;y++)for(let x=16;x<144;x++)
       if(frame.data[y*160+x]>16){px=x;py=y;break}
     if(px<0)throw Error('No visible GIF pixels for '+clan);
     const caster=pvpBaseEntity(PVP_HERO_BY_ID[key],650,650,own.team,own.color,null,false);
     const victim=pvpBaseEntity(PVP_HERO_BY_ID.warrior,0,0,'pvp-enemy','#f55',null,true);
     const now=performance.now();
     caster.pvpPowerStartedAt=now-elapsed;caster.pvpPowerUntil=now+1000;
     caster.pvpPowerNextTick=now-1;caster.pvpAimTarget=victim.id;caster.pvpAimAngle=0;
     victim.x=caster.x+30+(px+.5)*305/160;
     victim.y=caster.y-13+(py+.5)*105/55-52.5;
     const before=victim.shield+victim.hp;
     pvpTickPower(caster,now,0);
     const hit=before-(victim.shield+victim.hp);
     victim.x=caster.x+400;victim.y=caster.y;
     caster.pvpPowerNextTick=now-1;
     const after=victim.shield+victim.hp;
     pvpTickPower(caster,now,0);
     const miss=after-(victim.shield+victim.hp);
     result.push({clan,hit,miss,frames:entry.frames.length,domPresent:pvpFlameNodes.has(caster.id)});
     state.entities=state.entities.filter(e=>e!==caster&&e!==victim);
   }
   return result;
 },
 linearDragonShot(){
   const own=pvpLocalHero();if(!own)return null;
   const target=pvpBaseEntity(PVP_HERO_BY_ID.warrior,500,950,'pvp-enemy','#f55',null,true);
   const p={id:'linear-test',kind:'dragon',x:450,y:600,vx:100,vy:0,speed:100,
     targetId:target.id,targetX:target.x,targetY:target.y,team:own.team,sourceId:own.id,
     damage:5,burn:false,expireAt:performance.now()+3000};
   state.dragonProjectiles.push(p);
   const map=new Map(state.entities.map(e=>[e.id,e]));
   updateDragonProjectiles(.1,map);
   const first=[p.x,p.y,p.vx,p.vy];
   target.x=1000;target.y=200;
   updateDragonProjectiles(.1,map);
   const second=[p.x,p.y,p.vx,p.vy];
   target.x=p.x+5;target.y=p.y;
   const before=target.hp+target.shield;
   updateDragonProjectiles(.1,map);
   const impact=before-(target.hp+target.shield);
   state.dragonProjectiles=state.dragonProjectiles.filter(x=>x!==p);
   state.entities=state.entities.filter(e=>e!==target);
   return {first,second,impact,hit:p.pvpHit===true};
 },
 missingSprites(){
   return [...document.querySelectorAll('#entityLayer img,#combatFxLayer img')]
     .filter(img=>!img.hasAttribute('src')&&getComputedStyle(img).visibility!=='hidden')
     .length;
 },
 async flameDamageWithoutRender(){
   const own=pvpLocalHero();if(!own||!state.running)return null;
   const canvas=document.createElement('canvas');canvas.width=2;canvas.height=2;
   const g=canvas.getContext('2d');g.fillStyle='#fff';g.fillRect(0,0,2,2);
   const load=src=>new Promise((resolve,reject)=>{
     const img=new Image();img.onload=()=>resolve(img);img.onerror=reject;img.src=src;
   });
   const opaque=await load(canvas.toDataURL('image/png'));
   g.clearRect(0,0,2,2);
   const transparent=await load(canvas.toDataURL('image/png'));
   const saved={egypt:PVP_FIRE_IMAGES.egypt,warrior:PVP_FIRE_IMAGES.warrior};
   const result=[];
   for(const clan of ['warriors','egypt']){
     const key=clan==='egypt'?'egypt':'warrior';
     const heroDef=PVP_HERO_BY_ID[clan==='egypt'?'egyptMageFemale':'mageFemale'];
     const caster=pvpBaseEntity(heroDef,650,650,own.team,own.color,null,false); // Test a real human-strength PvP mage, not a half-damage minion.
     const target=pvpBaseEntity(PVP_HERO_BY_ID.warrior,790,650,'pvp-enemy','#f55',null,true);
     const t=performance.now();
     caster.pvpPowerUntil=t+2500;caster.pvpPowerNextTick=t-1;caster.pvpAimTarget=target.id;caster.pvpAimAngle=0;
     PVP_FIRE_IMAGES[key]=opaque;
     const before=target.shield+target.hp;
     pvpTickPower(caster,t,null);
     const hit=before-(target.shield+target.hp);
     caster.pvpPowerNextTick=t-1;
     PVP_FIRE_IMAGES[key]=transparent;
     const middle=target.shield+target.hp;
     pvpTickPower(caster,t,null);
     const transparentHit=middle-(target.shield+target.hp);
     result.push({clan,hit,transparentHit,domPresent:pvpFlameNodes.has(caster.id)});
     state.entities=state.entities.filter(e=>e!==caster&&e!==target);
   }
   for(const key of ['egypt','warrior']){
     if(saved[key])PVP_FIRE_IMAGES[key]=saved[key];else delete PVP_FIRE_IMAGES[key];
   }
   return result;
 },
 dragonSecondHit(){
   const dragon=state.entities.find(e=>e.type==='dragon'&&e.alive&&e.pvpDragonFirstHitSeen);
   if(!dragon)return {queued:false,shot:false};
   dragon.pvpDragonRetaliatePending=false;dragon.pvpDragonRetaliateImmediate=false;
   // Guarantee this is a REAL second durability loss. Earlier browser steps can
   // legitimately consume the dragon's entire shield before this regression check.
   if(dragon.shield<=0&&dragon.hp<=10)dragon.hp=20;
   dragon.pvpDragonObservedDurability=dragon.shield+dragon.hp;
   if(dragon.shield>0)dragon.shield=Math.max(0,dragon.shield-10);
   else dragon.hp=Math.max(1,dragon.hp-10);
   const before=state.dragonProjectiles.length;
   pvpObserveDragonDamage(dragon);
   const queued=dragon.pvpDragonRetaliatePending&&!dragon.pvpDragonRetaliateImmediate;
   dragon.pendingDragonAttack=null;dragon.dragonFlightState='flying';dragon.knockTime=0;
   dragon.pvpNpcNextAttackAt=performance.now()-1;
   dragon.dragonNextShotAt=0;dragon.dragonCloseShotAt=0;
   pvpBotAction(dragon,.016);
   return {queued,shot:state.dragonProjectiles.length===before+1,cleared:!dragon.pvpDragonRetaliatePending};
 },
 enforceSpecialCycle(){
   const ally=state.entities.find(e=>e.pvpAllyBot&&e.pvpHero==='mageFemale');
   if(!ally)return false;
   pvpExactGifDurationMs.set('magePowerSpecial',400);
   ally.pvpSpecialFxStartedAt=performance.now()-500;
   syncPVPSpecialEffects(state.camera.x,state.camera.y,state.camera.zoom,innerWidth,innerHeight);
   syncPVPSpecialEffects(state.camera.x,state.camera.y,state.camera.zoom,innerWidth,innerHeight);
   return !pvpSpecialFxNodes.has(ally.id)&&pvpSpecialFxPlayedSerial.get(ally.id)===ally.pvpSpecialSerial;
 },
 durability(){
   const hero=pvpLocalHero();
   const allies=state.entities.filter(e=>e.alive&&e.pvpAllyBot);
   const humans=state.entities.filter(e=>e.alive&&!e.pvpMinion&&e.ownerId)
     .map(e=>[e.ownerId,e.maxHp,e.maxShield]);
   return {player:[hero?.maxHp,hero?.maxShield],allies:allies.map(e=>[e.maxHp,e.maxShield]),humans};
 },
 basicSerial(){return pvpLocalHero()?.attackSerial||0},
 historyAttackVisualIsolation(){
   const local=pvpLocalHero();if(!local)return null;
   const own=pvpBaseEntity(PVP_HERO_BY_ID.warrior,700,700,local.team,'#fff','history-visual-test',false);
   own.pvpHero='warrior';own.clan='warriors';own.variant='male';
   const now=performance.now(),serverTime=Date.now();
   const keys=['controlled','attackCooldown','attackSerial','comboStep','regenSerial',
     'pvpWarriorSingleSerial','pvpWarriorSingleUntil','pvpWarriorLastBasicAt',
     'pvpWarriorComboSerial','pvpWarriorComboStartedAt','pvpWarriorComboUntil','pvpWarriorComboRequestUntil',
     'pvpMeleeVisualUntil','pvpActionUntil','historyServerSingleSerial','historyServerComboSerial',
     'historyServerSpecialSerial','pvpSpecialSerial','pvpWarriorChargeUntil','pvpWarriorChargeStartedAt','pvpWarriorChargeAngle'];
   const saved=Object.fromEntries(keys.map(k=>[k,own[k]]));
   own.controlled=true;own.attackCooldown=.12;own.pvpWarriorLastBasicAt=now-180;
   own.pvpWarriorSingleSerial=7;own.pvpWarriorSingleUntil=now+760;
   own.historyServerSingleSerial=6;own.historyServerComboSerial=3;
   const singleUntil=own.pvpWarriorSingleUntil,lastBasic=own.pvpWarriorLastBasicAt,cooldown=own.attackCooldown;
   historySyncWarriorCombatSnapshot(own,{
     attackSerial:Math.max(1,Number(own.attackSerial)||0),comboStep:1,regenSerial:Number(own.regenSerial)||0,
     attackCooldownUntil:serverTime+900,singleSerial:7,singleUntil:serverTime-1,lastBasicAt:serverTime-900,
     comboSerial:3,comboUntil:0,comboRequestUntil:0,
     specialSerial:Number(own.historyServerSpecialSerial)||0,specialActiveUntil:0,specialAngle:Number(own.heading)||0
   },now,serverTime);
   const snapshotPreserved=own.pvpWarriorSingleUntil===singleUntil&&
     own.pvpWarriorLastBasicAt===lastBasic&&Math.abs(own.attackCooldown-cooldown)<.001;
   own.pvpWarriorComboUntil=now+800;own.pvpWarriorComboStartedAt=now-100;own.pvpWarriorComboRequestUntil=now+350;
   own.attackSerial=20;own.historyServerComboSerial=4;
   historyApplyAuthoritativeAction(own,{action:'attack',kind:'combo-cancel',attackSerial:19,comboSerial:4,at:serverTime});
   const stalePreserved=own.pvpWarriorComboUntil>now;
   historyApplyAuthoritativeAction(own,{action:'attack',kind:'combo-cancel',attackSerial:20,comboSerial:4,at:serverTime});
   const currentCancelled=Number(own.pvpWarriorComboUntil)===0;
   Object.assign(own,saved);
   state.entities=state.entities.filter(e=>e!==own);
   return {snapshotPreserved,stalePreserved,currentCancelled};
 },
 warriorMechanics(){
   const own=pvpLocalHero();if(!own)return null;
   const warrior=pvpBaseEntity(PVP_HERO_BY_ID.warrior,700,700,own.team,'#fff',null,false);
   const enemy=pvpBaseEntity({...PVP_HERO_BY_ID.warrior,id:'warrior'},755,700,'pvp-enemy','#f55',null,true);
   warrior.hp=warrior.maxHp-40;warrior.heading=0;
   warrior.pvpWarriorSpecialHits=5;warrior.pvpWarriorSpecialUnlocked=true;warrior.pvpSpecialReadyAt=0;
   warrior.attackCooldown=0;warrior.pvpActionUntil=0;
   const beforeHp=warrior.hp;
   const started=pvpSpecialAttack(warrior);
   const healed=warrior.hp-beforeHp,cooldown=Math.round(warrior.pvpSpecialReadyAt-performance.now());
   const beforeEnemy=enemy.hp+enemy.shield;
   pvpTickWarriorSpecial(warrior,{dx:1,dy:0},.016,performance.now());
   const contactDamage=beforeEnemy-(enemy.hp+enemy.shield);
   const afterContact=enemy.hp+enemy.shield;
   pvpTickWarriorSpecial(warrior,{dx:1,dy:0},.016,performance.now());
   const repeatedDamage=afterContact-(enemy.hp+enemy.shield);
   const beforeIncoming=warrior.hp+warrior.shield;
   applyCombatHit(warrior,enemy,80,{knockForce:140,knockTime:.3,allowFlying:true});
   const incoming=beforeIncoming-(warrior.hp+warrior.shield);
   const noKnock=warrior.knockTime===0&&warrior.knockVX===0&&warrior.knockVY===0;
   const angleBefore=warrior.pvpWarriorChargeAngle;
   pvpTickWarriorSpecial(warrior,{dx:0,dy:1},.016,performance.now());
   const steered=warrior.pvpWarriorChargeAngle!==angleBefore&&Math.abs(warrior.pvpWarriorChargeAngle-Math.PI/2)<.01;
   state.entities=state.entities.filter(e=>e!==warrior&&e!==enemy);
   return {started,healed,cooldown,contactDamage,repeatedDamage,incoming,noKnock,steered,
     unlocked:warrior.pvpWarriorSpecialUnlocked,hits:warrior.pvpWarriorSpecialHits};
 },
 touchAimIsolation(){
   const hero=pvpLocalHero();if(!hero)return null;
   const world=document.querySelector('#world'),r=world.getBoundingClientRect();
   hero.pvpPowerUntil=performance.now()+1200;hero.pvpAimAngle=0;
   joystick.active=true;joystick.pointerId=41;joystick.x=.62;joystick.y=-.31;
   pvpControls.aimPointerId=null;pvpControls.aimManual=false;pvpControls.aimAngle=null;
   const fake=(pointerId,x,y)=>({pointerId,target:world,clientX:x,clientY:y});
   const blocked=pvpBeginAimPointer(fake(41,r.left+r.width*.8,r.top+r.height*.3));
   const accepted=pvpBeginAimPointer(fake(42,r.left+r.width*.82,r.top+r.height*.28));
   const input=getLocalMovement();
   const result={blocked,accepted,aimPointer:pvpControls.aimPointerId,
     dx:Math.round(input.dx*100)/100,dy:Math.round(input.dy*100)/100,
     manual:pvpControls.aimManual,angle:Number.isFinite(input.pvpAimAngle)};
   pvpEndAimPointer({pointerId:42});
   joystick.active=false;joystick.pointerId=null;joystick.x=0;joystick.y=0;
   hero.pvpPowerUntil=0;pvpControls.aimManual=false;pvpControls.aimAngle=null;
   return result;
 }

};`;
const testHTML=original.replace(/<script type="module">[\s\S]*?<\/script>/,()=>'<script>'+firebaseStub+'</script>')
 .replace('/* ==================== PVE ==================== */',pvpTestHook+'\n/* ==================== PVE ==================== */');
assert.notEqual(testHTML,original);
const server=http.createServer((req,res)=>{
 const name=new URL(req.url,'http://127.0.0.1').pathname;
 if(name==='/'||name==='/index.html'){
   res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'});res.end(testHTML);return;
 }
 if(name==='/sw.js'){res.writeHead(200,{'Content-Type':'application/javascript'});res.end('self.addEventListener("install",()=>self.skipWaiting());');return}
 // Exercise the one-time canonical fallback when a cache-busted GIF fails.
 if((name==='/assets/mage/poder-mago-especial.gif'||name==='/assets/runtime/magePowerSpecial.gif')&&new URL(req.url,'http://127.0.0.1').searchParams.has('gifStart')){
   res.writeHead(404);res.end('test-only cache-buster failure');return;
 }
 if(name==='/assets/mage/poder-mago.gif'||name==='/assets/egypt/mage/power-normal.gif'){
   res.writeHead(200,{'Content-Type':'image/gif','Cache-Control':'no-store'});
   res.end(fs.readFileSync(path.join(root,name.slice(1))));return;
 }
 if(/\.(gif|png|webp|jpg|jpeg|svg)$/i.test(name)){res.writeHead(200,{'Content-Type':'image/gif'});res.end(gif);return}
 if(/\.(mp3|wav|ogg)$/i.test(name)){res.writeHead(200,{'Content-Type':'audio/mpeg'});res.end(Buffer.alloc(0));return}
 res.writeHead(404);res.end();
});
async function main(){
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({headless:true});
 const errors=[],renderErrors=[];
 const page=await browser.newPage({viewport:{width:1280,height:720}});
 await page.route('https://i.postimg.cc/**',route=>route.fulfill({status:200,contentType:'image/gif',body:gif}));
 page.on('pageerror',err=>errors.push(err.message));
 page.on('console',msg=>{if(msg.type()==='error'&&/PvP (desenho|simulação|entidade)|IndexSizeError/.test(msg.text()))renderErrors.push(msg.text())});
 try{
   await page.goto('http://127.0.0.1:'+server.address().port+'/',{waitUntil:'domcontentloaded'});
   await page.waitForFunction(()=>!document.body.classList.contains('booting'),null,{timeout:55000});
   try{
     await page.waitForFunction(()=>window.__pvpBrowserTest?.accountXpReady?.()===true,null,{timeout:15000});
   }catch(err){
     const status=await page.evaluate(()=>({
       booting:document.body.classList.contains('booting'),
       xpState:document.querySelector('#accountXpSync')?.dataset?.state,
       xpLevel:document.querySelector('#accountXpLevel')?.textContent,
       account:document.querySelector('#accountStatus')?.textContent,
       firebase:document.querySelector('#firebaseStatus')?.textContent,
       name:document.querySelector('#accountName')?.textContent,
       auth:window.FirebaseBridge?.firebaseAuth?.currentUser?.uid
     }));
     console.error('Browser startup diagnostics:',status,'Page errors:',errors);
     throw err;
   }
   await page.locator('#createBtn').click();
   await page.locator('#modeScreen.active').waitFor({timeout:8000});
   await page.locator('.mode-card[data-mode="pvp"]').click();
   await page.locator('#configureBtn').click();
   await page.locator('#configScreen.active').waitFor({timeout:8000});
   assert.equal(await page.locator('#pveConfig .config:visible').count(),2,'PvP config shows only rounds and difficulty');
   assert.equal(await page.locator('#pvpTimeConfig:visible').count(),0,'PvP time selector is removed from the visible menu');
   assert.equal(await page.locator('#pvpSpeedConfig:visible').count(),0,'PvP speed selector is removed from the visible menu');
   await page.locator('#configScreen button.minus[data-target="rounds"]').click();
   assert.equal(await page.locator('#roundsVal').textContent(),'1','PvP can be configured with one round');
   await page.locator('#createRoomBtn').click();
   await page.locator('#lobbyScreen.active').waitFor({timeout:12000});
   const plus=page.locator('#lobbyScreen button.plus[data-target="npcs"]');
   for(let i=0;i<5;i++)await plus.click();
   await page.waitForFunction(()=>document.querySelector('#npcCountVal')?.textContent==='3');
   assert.equal(await page.locator('#lobbyScreen.pvp-lobby .pvp-player-card').count(),4,'maximum four allies in PvP lobby');
   assert.equal(await page.locator('#lobbyScreen.pvp-lobby .pvp-player-card:not(.empty)').count(),4,'one player and three allied NPCs');
   const minus=page.locator('#lobbyScreen button.minus[data-target="npcs"]');
   await minus.click();
   await page.waitForFunction(()=>document.querySelector('#npcCountVal')?.textContent==='2');
   await page.evaluate(()=>window.__pvpBrowserTest.addRemoteConfirmedPlayer());
   await page.waitForFunction(()=>document.querySelectorAll('#playerList .pvp-player-card:not(.empty)').length===4);
   assert.deepEqual((await page.evaluate(()=>window.__pvpBrowserTest.humanRoster())).sort(),
     ['browser-smoke-user','remote-user'],
     'PvP lobby must keep host and remote participant as two real humans');
   try{
     await page.locator('#playerList .pvp-player-card.mine').click({timeout:12000});
   }catch(err){
     const debug=await page.evaluate(()=>({
       cards:[...document.querySelectorAll('#playerList .pvp-player-card')].map(e=>({class:e.className,text:e.textContent})).slice(0,4),
       lobby:document.querySelector('#lobbyScreen')?.className,
       status:document.querySelector('#accountXpSync')?.textContent,
       roomCode:document.querySelector('#roomCode')?.textContent
     }));
     console.error('PvP lobby diagnostics:',debug,'Page errors:',errors);
     throw err;
   }
   await page.locator('#pvpPicker:not([hidden])').waitFor();
   assert.equal(await page.locator('#pvpHeroChoices button').count(),2,'PvP offers only Warrior and Warrior Mage');
   await page.locator('#pvpHeroChoices button').filter({hasText:'Maga Guerreira'}).first().click();
   await page.locator('#pvpHeroConfirm').click();
   assert.equal(await page.locator('#gameScreen.active.pvp-mode').count(),0,
     'confirming a hero must not auto-start PvP; only the host starts after everyone confirms');
   await page.locator('#lobbyContinue:not([disabled])').waitFor({timeout:8000});
   assert.equal(await page.locator('#lobbyContinue').textContent(),'Iniciar PvP');
   await page.locator('#lobbyContinue').click();
   await page.locator('#gameScreen.active.pvp-mode').waitFor({timeout:13000});
   const humanRoster=await page.evaluate(()=>window.__pvpBrowserTest.humanRoster());
   assert.deepEqual(humanRoster.sort(),['browser-smoke-user','remote-user'],
     'the started match must preserve both Firebase humans instead of replacing the remote player with an NPC');
   assert.equal(await page.evaluate(()=>window.__pvpBrowserTest.remoteHumanLabel()),'Amigo • Nv. 7',
     'remote human combat label must show nick and account level instead of generic hero name');
   const prediction=await page.evaluate(()=>window.__pvpBrowserTest.guestPredictionStep());
   assert(prediction&&prediction.dx>5&&Math.abs(prediction.dy)<1,
     'a non-host local hero must respond immediately to movement before a new authoritative snapshot');
   const reconciliation=await page.evaluate(()=>window.__pvpBrowserTest.staleSnapshotReconciliation());
   assert.deepEqual(reconciliation,{staleForward:true,staleDidNotSnap:true,ackedCorrected:true},
     'guest prediction must ignore stale unacknowledged host poses, then reconcile once the host acknowledges the input');
   const regional=await page.evaluate(()=>window.__pvpBrowserTest.regionalAuthorityCycle());
   assert.deepEqual(regional,{accepted:true,moved:true,yielded:false},
     'a remote player may own its pose outside the host camera, but authority returns immediately inside the host view');
   const distributed=await page.evaluate(()=>window.__pvpBrowserTest.distributedRegionCycle());
   assert(distributed?.first?.exists&&distributed.first.hp===73&&distributed.first.shield===12&&
     distributed.first.owner==='remote-user'&&!distributed.first.hostSimulates,
     'offscreen regional snapshots must lease complete enemy state to the remote player, not only its position: '+JSON.stringify(distributed));
   assert(distributed.first.remaining>750&&distributed.first.remaining<=950,
     'regional attack/GIF timing must arrive with its remaining runtime intact');
   assert.deepEqual({hp:distributed.second.hp,shield:distributed.second.shield,owner:distributed.second.owner,
     hostSimulates:distributed.second.hostSimulates},{hp:61,shield:0,owner:null,hostSimulates:true},
     'handoff must preserve the latest regional combat state and return simulation to the host');
   assert(distributed.second.remaining>450&&distributed.second.remaining<=700,
     'host takeover must continue the existing attack/GIF timeline instead of restarting it');
   await page.locator('#pvpCombatHud:not([hidden])').waitFor();
   const clock=await page.evaluate(()=>window.__pvpBrowserTest.roundClock());
   assert.deepEqual(clock,{duration:0,left:0},'PvP round has no countdown timer');
   assert.equal(await page.locator('#timer:visible').count(),0,'PvP gameplay hides the obsolete round timer');
   const durability=await page.evaluate(()=>window.__pvpBrowserTest.durability());
   assert.deepEqual(durability.player,[350,250],'human PvP player gets +100 HP and +100 shield');
   assert(durability.allies.length===2&&durability.allies.every(v=>v[0]===250&&v[1]===150),
     'two configured allied NPCs must keep NPC durability');
   const remoteDurability=durability.humans.find(v=>v[0]==='remote-user');
   assert.deepEqual(remoteDurability,['remote-user',350,250],
     'remote Firebase participant must spawn with full human durability, not NPC durability');
   const beforeBasic=await page.evaluate(()=>window.__pvpBrowserTest.basicSerial());
   const attackButton=page.locator('#attackBtn');
   await attackButton.hover();await page.mouse.down();
   const immediateBasic=await page.evaluate(()=>window.__pvpBrowserTest.basicSerial());
   assert(immediateBasic>beforeBasic,'normal attack reacts immediately on press');
   await page.waitForTimeout(900);await page.mouse.up();
   const heldBasic=await page.evaluate(()=>window.__pvpBrowserTest.basicSerial());
   assert(heldBasic>=beforeBasic+3,'holding attack must produce repeated basic attacks');
   const historyVisual=await page.evaluate(()=>window.__pvpBrowserTest.historyAttackVisualIsolation());
   assert.deepEqual(historyVisual,{snapshotPreserved:true,stalePreserved:true,currentCancelled:true},
     'History local attack GIF clocks must survive snapshots and ignore stale combo cancels');
   const touchAim=await page.evaluate(()=>window.__pvpBrowserTest.touchAimIsolation());
   assert.deepEqual(touchAim,{blocked:false,accepted:true,aimPointer:42,dx:.62,dy:-.31,manual:true,angle:true},
     'joystick pointer cannot steer flame; a second touch aims while movement stays active');
   const warriorMechanics=await page.evaluate(()=>window.__pvpBrowserTest.warriorMechanics());
   assert(warriorMechanics.started&&warriorMechanics.unlocked&&warriorMechanics.hits===5,'Warrior special starts after unlock');
   assert.equal(warriorMechanics.healed,30,'Warrior special heals 30 HP');
   assert(warriorMechanics.cooldown>19000&&warriorMechanics.cooldown<=20000,'Warrior special starts a 20 second cooldown');
   assert(warriorMechanics.contactDamage>=50&&warriorMechanics.contactDamage<=70,'Warrior charge deals 50-70 on contact');
   assert.equal(warriorMechanics.repeatedDamage,0,'same target is hit once during one Warrior special');
   assert.equal(warriorMechanics.incoming,2,'incoming damage becomes exactly 2 during Warrior special');
   assert(warriorMechanics.noKnock&&warriorMechanics.steered,'Warrior special ignores knockback and remains steerable');
   await page.locator('#pvpCombatHud [data-pvp-action="power"]').click();
   await page.locator('#attackBtn').click();
   await page.waitForTimeout(1250); // Includes live PvP update, aiming, GIF effect and combat frames.
   // Exercise the Egyptian mage special in the live frame loop, not only the
   // normal flame: it summons two Anubis and previously could black-screen PvP.
   const specialStarted=await page.evaluate(()=>window.__pvpBrowserTest.castLocalMageSpecial());
   assert(specialStarted,'Warrior Mage special must activate');
   await page.waitForTimeout(700);
   assert.equal(await page.locator('#gameScreen.active.pvp-mode').count(),1,'special must not black-screen the match');
   // A 1.8x PvP camera at fullscreen-size viewport formerly repeatedly threw
   // an IndexSizeError from the special's negative Canvas arc radius.
   await page.setViewportSize({width:1920,height:1080});
   await page.waitForTimeout(450);
   assert(!renderErrors.length,'PvP must render long specials without Canvas exceptions: '+renderErrors.join(' | '));
   assert(await page.evaluate(()=>window.__pvpBrowserTest.castWarriorSpecial()),'Warrior mage special must activate');
   await page.waitForTimeout(260);
   const firstFx=await page.evaluate(()=>window.__pvpBrowserTest.warriorFx());
   assert.equal(firstFx.serial,1,'Warrior special serial');
   assert.equal(firstFx.src,true,'Warrior power GIF starts behind the mage');
   assert.equal(firstFx.opacity,1,'Warrior special GIF remains fully bright between short fades');
   assert(firstFx.loaded&&!firstFx.loading,'PvP canonical retry finishes decoding before showing the image');
   assert(!firstFx.currentUrl.includes('gifStart='),'failed unique URL retries the cached canonical GIF');
   assert.equal(await page.evaluate(()=>window.__pvpBrowserTest.missingSprites()),0,'stopped sprites cannot paint broken image icons');
   const dragon=await page.evaluate(()=>window.__pvpBrowserTest.dragonFirstHit());
   assert.deepEqual(dragon,{armed:true,shot:true,correctSource:true,cleared:true},
     'first incoming hit must produce a real dragon projectile even during takeoff');
   await page.waitForFunction(()=>window.__pvpBrowserTest.flameFramesReady(),null,{timeout:60000});
   const realFlameHits=await page.evaluate(()=>window.__pvpBrowserTest.realFlameFrameHits());
   assert.deepEqual(realFlameHits.map(({clan,hit,miss,domPresent})=>({clan,hit,miss,domPresent})),[
     {clan:'warriors',hit:15,miss:0,domPresent:false},
     {clan:'egypt',hit:15,miss:0,domPresent:false}
   ],'both REAL animated GIFs must damage visible pixels even offscreen');
   assert(realFlameHits.every(e=>e.frames>20),'real animated frames were decoded');
   const linearDragon=await page.evaluate(()=>window.__pvpBrowserTest.linearDragonShot());
   assert.deepEqual(linearDragon,{first:[460,600,100,0],second:[470,600,100,0],impact:5,hit:true},
     'PvP dragon projectile flies straight, misses a moving target and hits only on crossing its line');
   const bothMages=await page.evaluate(()=>window.__pvpBrowserTest.flameDamageWithoutRender());
   assert.deepEqual(bothMages,[
     {clan:'warriors',hit:15,transparentHit:0,domPresent:false},
     {clan:'egypt',hit:15,transparentHit:0,domPresent:false}
   ],'both PvP flame types must damage opaque pixels with no DOM sprite and ignore transparent pixels');
   const secondShot=await page.evaluate(()=>window.__pvpBrowserTest.dragonSecondHit());
   assert.deepEqual(secondShot,{queued:true,shot:true,cleared:true},
     'PvP dragon must continue launching projectiles after a second direct hit');
   assert(await page.evaluate(()=>window.__pvpBrowserTest.enforceSpecialCycle()),
     'accurate PvP GIF duration stops a special even if its old gameplay window remains');
   const replayed=await page.evaluate(()=>window.__pvpBrowserTest.expireAndReplayWarriorFx());
   assert.equal(replayed,false,'spent PvP special never recreates its GIF on a late snapshot');
   assert(!renderErrors.length,'Fullscreen PvP visuals must remain stable: '+renderErrors.join(' | '));
   const migration=await page.evaluate(()=>window.__pvpBrowserTest.hostMigrationCycle());
   assert.deepEqual(migration,{
     armed:'remote-user',handoff:true,afterHandoff:'remote-user',
     localHost:true,host:'browser-smoke-user',
     runningAfterHandoff:true,runningNow:true,remotePlayer:false,remoteEntity:false
   },'PvP authority must migrate through background/close without pausing, and a closed host character must leave the match');
   const lifecycle=await page.evaluate(()=>window.__pvpBrowserTest.roomLifecycleCycle());
   assert(lifecycle.liveExists&&lifecycle.roomId&&lifecycle.phase==='finished'&&!lifecycle.legacyExists,
     'finished room with an active player must stay, while a stale legacy room must be deleted');
   assert.equal(await page.locator('#gameScreen.war-lobby').count(),0);
   assert(!errors.length,'browser JavaScript errors: '+errors.join('\n'));
   console.log('BROWSER PASS: PvP two-hero picker, Warrior special rules, round clock, durability, touch aim, mage flames, linear dragon balls and one-shot specials');
 }finally{await browser.close();await new Promise(resolve=>server.close(resolve))}
}
main().catch(err=>{console.error(err);process.exitCode=1;server.close()});
