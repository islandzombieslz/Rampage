const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const html=fs.readFileSync('index.html','utf8');
const script=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].at(-1)[1];
new vm.Script(script);
function section(a,b){const i=script.indexOf(a),j=script.indexOf(b,i+a.length);assert(i>=0&&j>i,a);return script.slice(i,j)}
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
function regionalTests(){
 let now=100000,serverNow=200000;
 const state={mode:'pvp',running:true,phase:'combat',round:1,matchId:'match-1',world:{w:2200,h:1600},
  camera:{x:200,y:200,zoom:1},entities:[],players:[{id:'g1'},{id:'g2'}],dragonProjectiles:[],matchStats:{}};
 const net={localPlayerId:'host',hostUid:'host',online:true,serverNow:()=>serverNow,roomCache:{players:{host:{slot:0},g1:{slot:1},g2:{slot:2}},regions:{}}};
 Object.defineProperty(net,'isHost',{get(){return this.localPlayerId===this.hostUid}});
 const ctx=vm.createContext({console,Math,Number,String,Object,Map,Set,WeakSet,state,NetworkAdapter:net,clamp,
  performance:{now:()=>now},gameViewport:()=>({w:400,h:300}),PVP_DAMAGE_TEXT_MS:600,PVP_BASE:{speed:210},
  pvpClampEntity(){},pvpLocalHero:()=>state.entities.find(e=>e.ownerId===net.localPlayerId&&!e.pvpMinion)});
 vm.runInContext(section('const REMOTE_WAR_RENDER_DELAY_MS=','function appendRemotePositionSample('),ctx);
 const run=s=>vm.runInContext(s,ctx);
 const host={id:1,type:'warrior',ownerId:'host',team:'host',x:320,y:340,alive:true,pvpMode:true};
 const g1={id:2,type:'warrior',ownerId:'g1',team:'g1',x:1500,y:1100,alive:true,pvpMode:true};
 const g2={id:3,type:'mage',ownerId:'g2',team:'g2',x:1700,y:1200,alive:true,pvpMode:true};
 const npc={id:4,type:'dragon',pvpMinion:true,team:'enemy',x:1450,y:1100,alive:true,pvpMode:true,hp:100,shield:50};
 state.entities=[host,g1,g2,npc];
 function packet(uid,seq,entities,extra={}){
  ctx.toEncode=entities;
  const encoded=run('toEncode.map(e=>pvpPackRegionalEntity(e,performance.now()))');
  return {uid,epoch:1,seq,active:true,handoff:false,at:serverNow,authorityUid:'host',matchId:state.matchId,round:1,
   view:{hostUid:uid,left:1000,top:750,right:2100,bottom:1500},focus:uid==='g1'?{x:1500,y:1100}:{x:1700,y:1200},
   entities:encoded,dragonProjectiles:[],players:[],...extra};
 }
 const apply=()=>run('pvpIntegrateRemoteRegions(performance.now())');
 net.roomCache.regions={g1:packet('g1',1,[g1])};apply();
 assert.equal(npc.pvpRegionalAuthorityUid,'g1','host grants NPC before guest starts simulating it');
 assert.equal(host.pvpRegionalAuthorityUid,null,'human host cannot be leased to a guest');
 const cached=run('pvpHostRegionState.get("g1").decodedEntities');now+=16;serverNow+=16;apply();
 assert.equal(run('pvpHostRegionState.get("g1").decodedEntities'),cached,'duplicate frames do not recursively decode packets');
 net.roomCache.regions.g1=packet('g1',2,[g1,{...npc,hp:73,shield:12,pendingDragonAttack:{serial:9,endAt:now+900}}]);apply();
 assert.equal(npc.hp,73);const end=npc.pendingDragonAttack.endAt;
 now+=32;serverNow+=32;apply();assert.equal(npc.pendingDragonAttack.endAt,end,'same attack does not gain time each frame');
 net.roomCache.regions.g1=packet('g1',1,[g1,{...npc,hp:999}]);apply();
 assert.equal(npc.hp,73,'older sequence cannot reset HP');assert.equal(run('pvpHostRegionState.get("g1").seq'),2);
 net.roomCache.regions.g1=packet('g1',3,[g1,{...npc,hp:61}]);
 net.roomCache.regions.g2=packet('g2',1,[g2,{...npc,hp:888}]);apply();
 assert.equal(npc.pvpRegionalAuthorityUid,'g1','overlapping regions have exactly one stable owner');assert.equal(npc.hp,61);
 net.localPlayerId='g2';run('pvpLocalRegionalAuthority=true;pvpLastRegionalView=NetworkAdapter.roomCache.regions.g2.view');
 ctx.npc=npc;ctx.g1=g1;assert(!run('pvpLocalRegionOwnsEntity(npc)'),'second guest cannot simulate first guest NPC');
 assert(!run('pvpLocalRegionOwnsEntity(g1)'),'second guest cannot simulate another human');
 net.localPlayerId='g1';assert(run('pvpLocalRegionOwnsEntity(npc)'));
 net.localPlayerId='host';net.roomCache.regions.g2=null;delete net.roomCache.regions.g2;
 net.roomCache.regions.g1=packet('g1',4,[g1,{...npc,hp:54}],{active:false,handoff:true});apply();
 assert.equal(npc.hp,54);assert.equal(npc.pvpRegionalAuthorityUid,null,'handoff returns simulation to host');
 npc.hp=45;now+=16;serverNow+=16;apply();assert.equal(npc.hp,45,'completed handoff never replays');
 net.roomCache.regions.g1=packet('g1',99,[{...g1,x:1600},{...npc,hp:999}],{epoch:0});apply();
 assert.equal(npc.hp,45,'previous authority generation never resurrects old state');
 net.roomCache.regions.g1=packet('g1',5,[{...npc,hp:999}],{round:2});apply();assert.equal(npc.hp,45);
 net.roomCache.regions.g1=packet('g1',5,[{...npc,hp:999}],{authorityUid:'old-host'});apply();assert.equal(npc.hp,45);
 console.log('NETWORK PASS: single NPC grants, no other-human takeover, monotonic packets, decode reuse, timed handoffs');
}
function loadTests(){
 let ownershipChecks=0;
 const state={mode:'pvp',phase:'combat',world:{w:4000,h:3000},entities:[]};
 const ctx=vm.createContext({console,Math,Number,String,Object,Map,Set,state,clamp,performance:{now:()=>1000},
  pvpRegionalSimulationUid:null,NetworkAdapter:{isHost:true},pvpHostShouldSimulateEntity:()=>{ownershipChecks++;return true},
  pvpLocalRegionOwnsEntity:()=>true,isRealCombatTarget:()=>true,canEngageTarget:(e,t)=>!(e.type==='warrior'&&t.type==='dragon')});
 vm.runInContext(section('const WAR_AI_GRID_CELL=','function updateWar(dt){'),ctx);
 vm.runInContext(section('const pvpFrameTargetLists=new Map(),','function pvpNPCSerial('),ctx);
 let seed=24681357;const rand=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/2**32};
 for(let i=0;i<600;i++)state.entities.push({id:i,type:i%11?'warrior':'dragon',team:i%3,x:rand()*4000,y:rand()*3000,alive:true});
 const start=performance.now();
 vm.runInContext('pvpRebuildTargets()',ctx);
 assert.equal(ownershipChecks,600,'ownership filtering is linear, once per frame');
 const lists=vm.runInContext('[...pvpFrameTargetLists.values()]',ctx);
 for(const e of state.entities){ctx.e=e;assert.equal(vm.runInContext('pvpTargetsFor(e)',ctx),lists[e.team]);}
 assert.equal(ownershipChecks,600,'no per-NPC filtered array allocation');
 vm.runInContext('pvpRebuildTargets()',ctx);assert.equal(vm.runInContext('pvpFrameTargetLists.get(0)',ctx),lists[0]);
 // A broad phase can only optimize work if the nearest target and every exact
 // area hit match the full scan. Include far cells and non-flying constraints.
 for(let i=0;i<120;i++){
  const e=state.entities[i];ctx.e=e;
  for(const nonDragon of [false,true]){
   const valid=state.entities.filter(t=>t!==e&&t.team!==e.team&&(!nonDragon||t.type!=='dragon')&&!(e.type==='warrior'&&t.type==='dragon'));
   valid.sort((a,b)=>((a.x-e.x)**2+(a.y-e.y)**2)-((b.x-e.x)**2+(b.y-e.y)**2));
   assert.equal(vm.runInContext(`nearestEnemyFromWarGrid(e,warCombatGrid,${nonDragon})`,ctx)?.id,valid[0]?.id);
  }
  const expected=state.entities.filter(t=>Math.hypot(t.x-e.x,t.y-e.y)<=200).map(t=>t.id).sort((a,b)=>a-b);
  ctx.hits=[];vm.runInContext('forEachWarSpatialCandidate(e.x-200,e.y-200,e.x+200,e.y+200,t=>{if(Math.hypot(t.x-e.x,t.y-e.y)<=200)hits.push(t.id)})',ctx);
  assert.deepEqual(Array.from(ctx.hits).sort((a,b)=>a-b),expected);
 }
 console.log('LOAD PASS: 600 troops, linear ownership work, shared target arrays, exact nearest/area hits ('+Math.round(performance.now()-start)+' ms verification)');
}
function clockTests(){
 for(const hz of [30,60,90,120,144,240]){
  let updates=0,renders=0,distance=0;
  const state={mode:'pvp',fpsFrames:0,fpsLast:0,hudLast:0};
  const noop=()=>{};
  const ctx=vm.createContext({state,NetworkAdapter:{online:false},Math,clamp,last:0,messageUntil:0,performance,PVP_SNAPSHOT_INTERVAL_MS:80,
   gameScreenPerfEl:{style:{}},centerMessagePerfEl:{textContent:''},requestAnimationFrame:noop,
   updateGameSimulation:dt=>{updates++;distance+=210*dt},draw:()=>renders++,updateWarCameraIntro:noop,updateWarCameraInertia:noop,
   updateSpectatorTransition:noop,updateGolemRockEffects:noop,updateLayeredBattleSfx:noop,updatePvpCombatSfx:noop,
   syncPvpWarriorCinematicPresentation:noop,pvpReportError:(tag,e)=>{throw e},updateHUD:noop});
  vm.runInContext(section('const GAME_RENDER_MAX_FPS=120;','requestAnimationFrame(loop);\nrunBootLoader'),ctx);
  for(let i=1;i<=hz*2;i++)vm.runInContext(`loop(${i*1000/hz})`,ctx);
  assert.equal(updates,120,'60 simulation steps per second at '+hz+' Hz');assert(Math.abs(distance-420)<1e-6);
  assert(renders<=241,'render limit at '+hz+' Hz: '+renders);
  const before=updates;vm.runInContext('loop(5000)',ctx);assert(updates-before<=3,'tab resume cannot produce a catchup spiral');
 }
 console.log('CLOCK PASS: 30–240 Hz screens preserve movement, simulation 60 Hz, render <=120 FPS, bounded catchup');
}
async function adapterTests(){
 const calls=[],listeners=new Map();let generalSyncs=0,resolveArm;
 const F={ref:(_db,p)=>p,firebaseDb:{},update:async(p,v)=>calls.push(['update',p,v]),
  onValue:(p,cb)=>{listeners.set(p,cb);return()=>listeners.delete(p)},
  onDisconnect:p=>({set:async uid=>{calls.push(['arm',p,uid]);await new Promise(r=>{resolveArm=r})},
   remove:async()=>calls.push(['remove',p]),cancel:async()=>calls.push(['cancel',p])})};
 const state={mode:'pvp',phase:'combat',running:true};
 const ctx=vm.createContext({console,Math,Date,Map,Set,Promise,Object,Number,String,state,window:{FirebaseBridge:F},
  syncFirebaseRoom:()=>generalSyncs++,handleHostCommands(){},applyRemoteGame(){},
  pvpNextHostCandidate:room=>Object.values(room.players||{}).find(p=>p.uid==='guest')});
 vm.runInContext(section('const NetworkAdapter = {','/* ==================== CONFIGURAÇÃO'),ctx);
 const net=vm.runInContext('NetworkAdapter',ctx);
 Object.assign(net,{roomId:'ROOM',localPlayerId:'host',hostUid:'host',roomStatus:'playing',roomCache:{players:{host:{uid:'host'},guest:{uid:'guest'}}}});
 net.subscribeRoom('ROOM');await Promise.resolve();
 const input={host:{dx:1}};listeners.get('rooms/ROOM/inputs')({exists:()=>true,val:()=>input});
 assert.equal(net.remoteInputs,input);assert.equal(generalSyncs,0,'hot input path never runs lobby/presence reconciliation');
 Object.assign(net.roomCache,{players:{host:{uid:'host'},guest:{uid:'guest'}},settings:{mode:'pvp'}});
 const a=net.refreshPVPHostDisconnect(),b=net.refreshPVPHostDisconnect();
 for(let i=0;i<8&&!resolveArm;i++)await Promise.resolve();assert(resolveArm);
 net.hostUid='guest';await net.cancelPVPHostDisconnect();resolveArm();await Promise.all([a,b]);
 assert.equal(calls.filter(x=>x[0]==='arm').length,1,'overlapping refreshes arm only one disconnect write');
 assert(calls.some(x=>x[0]==='cancel'));assert.equal(net.hostDisconnectOp,null,'obsolete host cannot keep a disconnect write armed');
 let releaseFirebase;net.hostUid='host';net.waitFirebase=()=>new Promise(r=>{releaseFirebase=r});
 const pending=net.pushState({seq:1});net.hostUid='guest';releaseFirebase(F);await pending;
 assert.equal(calls.filter(x=>x[0]==='update').length,0,'old host cannot publish after async handoff');
 console.log('ADAPTER PASS: hot-path input delivery, serialized disconnect registration and late host-write rejection');
}
regionalTests();loadTests();clockTests();adapterTests().catch(e=>{console.error(e);process.exitCode=1});
