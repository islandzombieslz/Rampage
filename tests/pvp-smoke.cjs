const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const html=fs.readFileSync('index.html','utf8');
const script=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].at(-1)?.[1];
assert(script,'inline game script missing');
new vm.Script(script,{filename:'index.html PvP'});
function section(a,b){const i=script.indexOf(a),j=script.indexOf(b,i+a.length);assert(i>=0&&j>i,'missing '+a);return script.slice(i,j)}
let now=100000,mobile=false,damageCalls=[];
const state={mode:'pvp',phase:'combat',running:true,world:{w:2200,h:1400},entities:[],players:[],nextId:1,round:1,
 rounds:2,pveTime:60,timeLeft:60,speed:'normal',difficulty:'easy',particles:[],dragonProjectiles:[],
 spectator:{active:false,transitioning:false},matchStats:{}};
const nodes=new Map();
function node(key){if(!nodes.has(key))nodes.set(key,{
 style:{},dataset:{},classList:{add(){},remove(){},toggle(){}},
 addEventListener(){},querySelector(){return null},replaceChildren(){},append(){},appendChild(){},remove(){},
 setAttribute(){},hasAttribute(name){return name==='src'&&!!this._src},children:[],hidden:false,disabled:false
 });return nodes.get(key)}
const net={localPlayerId:'u1',remoteInputs:{},attackSeq:0,online:false,isHost:true,sendInput(){}};
const ctx=vm.createContext({Math,Object,Date,Number,JSON,String,Map,Set,console,
 state,NetworkAdapter:net,performance:{now:()=>now},
 clamp:(v,a,b)=>Math.max(a,Math.min(b,v)),isMobileLike:()=>mobile,
 $:node,$$:()=>[],ASSETS:{},Image:class{},document:{createElement:()=>node('created-'+Math.random())},
 entityBase:(type,x,y,team,color)=>({id:state.nextId++,type,x,y,team,color,r:30,hp:100,maxHp:100,shield:50,maxShield:50,damage:20,
 speed:150,alive:true,knockTime:0,attackCooldown:0,attackSerial:0,comboStep:0,heading:0,facing:1,moving:false,
 mageAttackSerial:0}),
 applyCombatHit:(target,source,damage,options)=>{
   damageCalls.push({damage,options,target:target.id});
   const absorbed=Math.min(target.shield,damage);
   target.shield-=absorbed;target.hp-=Math.max(0,damage-absorbed);
   if(target.hp<=0)target.alive=false;
 },
 startEntityDeath:e=>{e.alive=false;e.deathStarted=now},
 distanceToSegment:(px,py,ax,ay,bx,by)=>{
   const dx=bx-ax,dy=by-ay,t=Math.max(0,Math.min(1,((px-ax)*dx+(py-ay)*dy)/(dx*dx+dy*dy)));
   return Math.hypot(px-(ax+t*dx),py-(ay+t*dy))
 },
 clearEntityVisuals(){},flash(){},navigateScreen(){},configureGameScreenForMode(){},pvpPlayEntitySfxNow(){},stopLayeredOneShot(){},
 beginMatchTracking(){},matchStatsFor:uid=>state.matchStats[uid]||(state.matchStats[uid]={damage:0,wonRounds:0,victorySeconds:0,victoryTimeLimit:0}),
 finishGame(){},difficultyConfig:{easy:{initial:1,every:20,wave:1}},getLocalMovement:()=>({dx:0,dy:0,attackSeq:net.attackSeq}),
 sendLocalPVEInput(){},setTimeout(){},requestAnimationFrame(){},
 pvpRegionalSimulationUid:null,pvpLocalRegionalAuthority:false,
 pvpHostShouldSimulateEntity:()=>true,pvpHostShouldSimulateProjectile:()=>true,
 pvpLocalRegionOwnsEntity:()=>true,pvpLocalRegionOwnsProjectile:()=>true,
 pvpIntegrateRemoteRegions(){},pvpMaybePublishRegion(){},pvpUpdateLocalRegionalAuthority:()=>false,
 pvpSetLocalRegionalAuthority:()=>false
});
vm.runInContext('const gifRuntime=new Map(); const pvpGifFullDurationMs=new Map(); const DRAGON_CLOSE_RANGE=175; const MAGE_SPECIAL_RADIUS=215;',ctx);
vm.runInContext(section('const PVP_HEROES=Object.freeze(', 'function setLobbySkin('),ctx);
vm.runInContext(section('const PVP_ARENA=Object.freeze(', '/* ==================== PVE ==================== */'),ctx);
const warCalls=[];
ctx.beginDragonTakeoff=e=>{e.dragonFlightState='takeoff';e.dragonTakeoffSerial=(e.dragonTakeoffSerial||0)+1;return true};
ctx.updateDragonState=e=>{if(e.dragonFlightState==='takeoff'&&now>=e.dragonTakeoffEndAt)e.dragonFlightState='flying';if(e.pendingDragonAttack&&now>=e.pendingDragonAttack.endAt)e.pendingDragonAttack=null};
ctx.aiFight=(e,dt,team,targets)=>{warCalls.push(e.type)};
ctx.warBurningEntities=new Set();
ctx.warFrameEnemiesByTeam=new Map();
ctx.rebuildWarEntityIdMap=()=>new Map(state.entities.map(e=>[e.id,e]));
ctx.updateDragonProjectiles=()=>{};
ctx.updateDragonBurns=()=>{};
ctx.buildWarAIGrid=()=>new Map();
const run=expr=>vm.runInContext(expr,ctx);
// An image-data sub-block can contain 21 F9 04 without being a GIF frame.
const syntheticGif=new Uint8Array([
 71,73,70,56,57,97,1,0,1,0,0,0,0,
 33,249,4,0,50,0,0,0,
 44,0,0,0,0,1,0,1,0,0,2,7,33,249,4,0,255,255,0,0,
 33,249,4,0,70,0,0,0,
 44,0,0,0,0,1,0,1,0,0,2,1,0,0,59
]);
ctx.syntheticGif=syntheticGif.buffer;
assert.equal(run('pvpParsedGifCycleMs(syntheticGif)'),1200,'PvP must parse real GIF blocks, not false markers in compressed bytes');
const heroes=run('PVP_HEROES'),base=run('PVP_BASE');
assert.equal(heroes.length,8);
assert.deepEqual(Array.from(run('PVP_SELECTABLE_HEROES'),h=>h.id),['warrior','mageFemale']);
assert.equal(run('PVP_SELECTABLE_BY_ID.king'),undefined);
for(const h of heroes)assert(h.card.startsWith('assets/')&&h.name&&h.id);
assert.equal(new Set(heroes.map(h=>h.id)).size,8);
assert.equal(run('PVP_ENEMY_HERO_IDS.length'),5);
assert.equal(base.hp,250);assert.equal(base.shield,150);
assert.equal(base.damageMin,25);assert.equal(base.damageMax,40);
assert.equal(base.meleeCooldown,.30);assert.equal(base.specialCooldown,20000);
assert.equal(run('pvpDamageForRange(0)'),40);
assert.equal(run('pvpDamageForRange(112)'),25);
assert.equal(run('pvpDamageForRange(0,true)'),100);
assert.equal(run('pvpDamageForRange(270,true)'),80);
assert.equal(run('PVP_ARENA.w'),1850);assert.equal(run('PVP_ARENA.h'),1542);
state.world.w=1850;state.world.h=1542;
assert.equal(run('pvpArenaBounds(30).left'),300);
assert.equal(run('pvpArenaBounds(30).right'),1550);
assert.equal(run('pvpNPCRecovery({type:"dragon"},performance.now())-performance.now()'),2000);
assert.equal(run('pvpNPCRecovery({type:"golem",pendingGolemAttack:{endAt:performance.now()+3100}},performance.now())-performance.now()'),4200);
assert(html.includes("state.mode==='pvp'&&e.pvpWarAI?3:POSEIDON_MELEE_ATTACKS_PER_CYCLE"),'PvP Poseidon summons after 3 normals');
assert(html.includes('id="pvpStatusHud"')&&html.includes('id="pvpHP"')&&html.includes('id="pvpShield"'),'PvP-only vitality HUD');
assert(html.includes("const sceneFloor=state.mode==='pvp'?pvpFloorImage"),'independent PvP floor');
assert(html.includes('id="pvpBarrierSprite"'),'independent PvP barrier');
assert(html.includes('drawPVPDamageNumbers(pvpDamageCtx,renderFrameNow)'),'foreground PvP damage overlay');
assert.equal(run('pvpCameraZoom(1920,1080)'),1.8);
mobile=true;assert(run('pvpCameraZoom(850,390)')<1.8);

state.players=[{id:'u1',human:true,pvpHero:'warrior'},{id:'ally-bot',human:false,pvpHero:'mageFemale'}];
const hero=run('pvpBaseEntity(PVP_HERO_BY_ID.warrior,500,500,"u1","#aaa","u1",false)');
const allyBot=run('pvpBaseEntity(PVP_HERO_BY_ID.mageFemale,360,360,"u1","#9cf","ally-bot",false)');
const foe=run('pvpBaseEntity({...PVP_ENEMY_HEROES.naja,id:"naja"},595,500,"pvp-enemy","#f77",null,true)');
assert.equal(hero.maxHp,350);assert.equal(hero.maxShield,250);assert.equal(hero.speed,195);
assert.equal(allyBot.maxHp,250);assert.equal(allyBot.maxShield,150,'allied NPC keeps old durability');
state.entities=state.entities.filter(e=>e!==allyBot);
assert.equal(foe.maxHp,300);assert.equal(foe.maxShield,250);assert.equal(foe.speed,117);
assert.equal(foe.pvpDamageBonus,10);
assert.equal(foe.damage,20);assert.equal(foe.controlled,false);
assert(run('pvpBasicAttack(state.entities[0])'));
assert.equal(damageCalls.length,1);assert(damageCalls[0].damage>=25&&damageCalls[0].damage<=40);
assert.equal(damageCalls[0].options.knockForce,95);
assert.equal(run('pvpBasicAttack(state.entities[0])'),false,'basic attack cooldown');
now+=301;hero.attackCooldown=0;
assert(run('pvpBasicAttack(state.entities[0])'),'second continued input starts Warrior combo');
assert(hero.pvpWarriorComboUntil>now,'continued attack enters combo GIF window');
assert.equal(hero.pvpWarriorSpecialHits,1,'first successful single attack counts toward unlock');
const comboStarted=hero.pvpWarriorComboStartedAt;
// Continued inputs keep the combo alive; without them the new system cancels it mid-animation.
now=comboStarted+250;run('pvpBasicAttack(state.entities[0])');run('pvpTickWarriorCombo(state.entities[0],performance.now())');
now=comboStarted+700;run('pvpBasicAttack(state.entities[0])');run('pvpTickWarriorCombo(state.entities[0],performance.now())');
now=comboStarted+1120;run('pvpBasicAttack(state.entities[0])');run('pvpTickWarriorCombo(state.entities[0],performance.now())');
assert.equal(hero.pvpWarriorComboHitIndex,3,'combo schedules exactly three damage contacts while input continues');
assert.equal(hero.pvpWarriorSpecialHits,4,'three combo contacts also count as successful attacks');
const releaseDeadline=hero.pvpWarriorComboRequestUntil;
now=releaseDeadline+1;run('pvpTickWarriorCombo(state.entities[0],performance.now())');
assert.equal(hero.pvpWarriorComboUntil,0,'stopping input interrupts the active combo');
hero.attackCooldown=0;
assert(run('pvpBasicAttack(state.entities[0])'),'next press after released combo restarts as single attack');
assert.equal(hero.pvpWarriorSpecialHits,5);
assert.equal(hero.pvpWarriorSpecialUnlocked,true,'five successful contacts unlock the Warrior special');
assert.equal(hero.pvpSpecialReadyAt,0,'first Warrior special is immediately ready after five hits');
hero.hp=300;hero.attackCooldown=0;hero.pvpActionUntil=0;
const specialAt=now;
assert(run('pvpSpecialAttack(state.entities[0])'),'unlocked Warrior special starts');
assert.equal(hero.hp,330,'Warrior special heals exactly 30 HP without exceeding max');
assert.equal(hero.pvpSpecialReadyAt,specialAt+20000,'after first unlock the special uses only a 20 second timer');
assert(hero.pvpWarriorChargeUntil>specialAt&&hero.pvpWarriorChargeHitIds.length===0);
foe.x=hero.x+55;foe.y=hero.y;foe.alive=true;
const foeBefore=foe.hp+foe.shield;
run('pvpTickWarriorSpecial(state.entities[0],{dx:1,dy:0},.016,performance.now())');
let chargeDamage=foeBefore-(foe.hp+foe.shield);
assert(chargeDamage>=50&&chargeDamage<=70,'first Warrior special contact deals 50-70 damage');
assert.equal(damageCalls.at(-1).options.knockForce,0,'first four Warrior special hits keep the target in the sequence');
const specialSequence=hero.pvpWarriorChargeHitState[foe.id];
const specialSequenceStart=specialSequence.startedAt;
const specialSequenceEnd=specialSequence.endAt;
for(const fraction of [.24,.49,.74,.96]){
  now=specialSequenceStart+(specialSequenceEnd-specialSequenceStart)*fraction+1;
  run('pvpTickWarriorSpecial(state.entities[0],{dx:1,dy:0},.016,performance.now())');
}
chargeDamage=foeBefore-(foe.hp+foe.shield);
assert(chargeDamage>=250&&chargeDamage<=350,'Warrior special deals five 50-70 damage hits across the full GIF');
assert.equal(hero.pvpWarriorChargeHitState[foe.id].count,5,'same enemy receives exactly five special hits');
assert(html.includes('const fractions=[0,.24,.49,.74,.96]'),
 'Warrior special distributes its five impacts from contact until near the final GIF frame');
const specialHit=damageCalls.at(-1);
assert.equal(specialHit.options.knockForce,560,'fifth Warrior special hit uses the stronger PvP-only shove');
assert.equal(specialHit.options.tilt,20,'final Warrior special hit uses the stronger impact tilt');
assert.equal(foe.hitTilt,20,'Warrior special leaves the target visibly tilted');
assert(Math.hypot(foe.knockVX,foe.knockVY)>550,'Warrior special finishes with a strong lateral velocity');
assert(html.includes('pvpWarriorSpecialCinematic')&&html.includes('specialCameraZoom:1.12')&&html.includes('specialSceneDim:.26'),
 'Warrior special includes PvP-only linear zoom and scene dimming');
const afterFifthCharge=foe.hp+foe.shield;
now=specialSequenceEnd+1;
run('pvpTickWarriorSpecial(state.entities[0],{dx:1,dy:0},.016,performance.now())');
assert.equal(foe.hp+foe.shield,afterFifthCharge,'same enemy is capped at five hits per special');
assert(html.includes("target.pvpHero==='warrior'")&&html.includes('amount=2')&&html.includes('knockForce:0,knockTime:0'),
 'Warrior special converts incoming PvP hits to 2 damage with no knockback');
assert(html.includes("Number(a.pvpWarriorChargeUntil)>now||Number(b.pvpWarriorChargeUntil)>now"),
 'Warrior charge passes through entity separation');
assert(html.includes("pvpWarriorDeathGifAt=now+PVP_WARRIOR.deathFallMs")&&html.includes('pvp-warrior-death-gif'),
 'Warrior uses the existing fall followed by a fading one-shot death GIF');
now=hero.pvpWarriorChargeUntil+1;run('pvpTickWarriorSpecial(state.entities[0],{},.016,performance.now())');
now=hero.pvpSpecialReadyAt+1;hero.attackCooldown=0;hero.pvpActionUntil=0;
assert(run('pvpSpecialAttack(state.entities[0])'),'20 second cooldown re-enables special without another five-hit requirement');

const mage=run('pvpBaseEntity(PVP_HERO_BY_ID.mage,1050,500,"u2","#ffe","u2",false)');
assert.equal(mage.pvpSpecialReadyAt,now+40000,'warrior mage waits only for initial 40 second timer');
mage.shield=10;
const attacker=foe;attacker.x=1100;attacker.y=500;
run('pvpCombatHit(state.entities[2],state.entities[1],20)');
assert.equal(mage.shield,0);
assert.equal(mage.pvpSpecialReadyAt,now+40000,'shield break cannot change timer');
assert.equal(run('pvpSpecialAttack(state.entities[2])'),false,'special remains timer-locked');
now+=40001;
assert(run('pvpSpecialAttack(state.entities[2])'),'special works even with shield intact once timer completes');
assert.equal(mage.pvpSpecialDuration,40000);
assert.equal(mage.pvpSpecialReadyAt,now+40000);

const egypt=run('pvpBaseEntity(PVP_HERO_BY_ID.egyptMage,1450,700,"u3","#e0c","u3",false)');
assert.equal(egypt.pvpSpecialReadyAt,now+10000);
now+=10001;
const hitsBefore=damageCalls.length;
assert(run('pvpSpecialAttack(state.entities.find(e=>e.id==='+egypt.id+'))'));
assert.equal(damageCalls.length,hitsBefore,'Egypt summon special deals no damage');
const minions=state.entities.filter(e=>e.pvpSummonerId===egypt.id);
assert.equal(minions.length,2);assert(minions.every(e=>e.type==='anubis'&&e.maxHp===125&&e.maxShield===75));
now=egypt.pvpSpecialReadyAt+1;run('pvpExpireSummons(performance.now())');
assert(minions.every(e=>!e.alive),'summons die immediately on cooldown completion');
assert.equal(egypt.pvpSpecialDuration,30000);

const power=run('pvpBaseEntity(PVP_HERO_BY_ID.egyptMage,400,1000,"u4","#e0c","u4",false)');
const victim=run('pvpBaseEntity({...PVP_ENEMY_HEROES.golem,id:"golem"},585,1000,"pvp-enemy","#f77",null,true)');
assert(run('pvpCastPower(state.entities.find(e=>e.id==='+power.id+'),'+victim.id+')'));
now+=110;
const fullFlameMask={width:160,height:55,data:new Uint8ClampedArray(160*55*4).fill(255)};
ctx.pvpReadFlameAlpha=()=>fullFlameMask;
const shieldBefore=victim.shield;
run('pvpTickPower(state.entities.find(e=>e.id==='+power.id+'),performance.now(),0)');
assert.equal(victim.shield,shieldBefore-15,'15 damage per 500ms');
now+=500;
run('pvpTickPower(state.entities.find(e=>e.id==='+power.id+'),performance.now(),0)');
assert.equal(victim.shield,shieldBefore-30);
ctx.pvpReadFlameAlpha=()=>({width:160,height:55,data:new Uint8ClampedArray(160*55*4)});
now+=500;run('pvpTickPower(state.entities.find(e=>e.id==='+power.id+'),performance.now(),null)');
assert.equal(victim.shield,shieldBefore-30,'transparent GIF pixels cannot damage');
ctx.pvpReadFlameAlpha=()=>fullFlameMask;
run('pvpTickPower(state.entities.find(e=>e.id==='+power.id+'),performance.now(),Math.PI/2)');
assert.equal(power.pvpAimAngle,Math.PI/2,'manual aim overrides automatic targeting');
now+=100;run('pvpTickPower(state.entities.find(e=>e.id==='+power.id+'),performance.now(),Math.PI/2)');
assert.equal(power.pvpAimAngle,Math.PI/2,'manual direction does not oscillate');
assert.equal(run('pvpCanPower(state.entities.find(e=>e.id==='+hero.id+'))'),false);

assert(html.includes('id="pvpCombatHud"')&&html.includes('id="pvpPicker"'));
assert(html.includes("specialInactive:'assets/ui/pvp/punho-especial-inativo.png'")&&
 html.includes("specialActive:'assets/ui/pvp/punho-especial-ativo.gif'")&&
 html.includes("slotFrame:'assets/ui/pvp/moldura-armas.png'")&&
 html.includes("attackButton:'assets/ui/pvp/botao-ataque.png'"),
 'PvP HUD artwork must stay local instead of depending on Postimg at runtime');
assert(html.includes('class="pvp-special-fill"')&&
 html.includes("button.style.setProperty('--pvp-special-progress'"),
 'special HUD must use the existing cooldown/unlock state to fill its progress bar');
assert(html.includes("#pvpCombatHud .pvp-special-button{position:relative;width:clamp(48px,7vw,64px);height:clamp(48px,7vw,64px)"),
 'special control must match the stone power/weapon slot size');
assert(html.includes("const iconActive=specialReady||specialRunning")&&
 html.includes("specialIcon.src=iconActive?PVP_UI_ASSETS.specialActive:PVP_UI_ASSETS.specialInactive"),
 'Warrior special icon must switch between inactive sprite and active GIF from the existing special state');
assert(html.includes("background:transparent url('assets/ui/pvp/moldura-armas.png')")&&
 html.includes('class="pvp-slot-icon"'),
 'power and weapon slots must use the requested local frame with their existing icons');
assert(html.includes("background:transparent url('assets/ui/pvp/botao-ataque.png')")&&
 html.includes("attackBtn.classList.add('pvp-attack-pulse')"),
 'PvP attack control must use the local attack sprite and pulse on touch/click');
assert(html.includes('PVP_BASIC_HOLD_REPEAT_MS=300'),'holding attack must keep PvP combo continuity');
assert(html.includes("?220\n      :PVP_BASIC_HOLD_REPEAT_MS"),'holding Warrior attack must enter combo without repeated taps');
assert(html.includes('comboRange:148'),'Warrior combo has the slightly larger requested hitbox');
assert(html.includes('top:-43px'),'Warrior combo GIF is shifted slightly upward');
assert(html.includes('img===previousImg&&previous!==desired'),'Warrior sprite handoff keeps the previous frame visible during GIF changes');
assert(html.includes("pvpControls.aimPointerId!==event.pointerId"),'flame aim must use a dedicated pointer');
assert(html.includes("joystick.pointerId===event.pointerId"),'joystick pointer must never steer the flame');
assert(html.includes("const baseZoom=pvpCameraZoom(vw,vh)")&&html.includes("specialCameraZoom"),'PvP camera keeps its base zoom and adds the Warrior special cinematic');
assert(html.includes("if(state.mode==='pvp')updatePVP(dt);else updateWar(dt)"));
assert(html.includes("pvpConfirmed:true"),'networked hero confirmation');
assert(!html.includes("state.players.filter(p=>p.human).length===1)await launchPVP()"),
 'hero confirmation must never auto-start PvP from a stale one-player roster');
assert(html.includes("async function reservePVPStart()")&&html.includes("rooms/${roomId}/status"),
 'host start must atomically reserve only the Firebase status node before simulation');
assert(html.includes("function pvpFirebaseRoomReady(room,uid)"),
 'server-side roster validation must gate the PvP start');
assert(!section('async function reservePVPStart(){','async function launchPVP(){').includes("runTransaction(roomRef"),
 'PvP start must never transact the entire room because guest player nodes can be write-protected');
assert(html.includes("state.players=pvpRosterFromFirebaseRoom(room)"),
 'match start must rebuild players from the authoritative Firebase roster');
assert(html.includes("const PVP_INPUT_INTERVAL_MS=33")&&html.includes("const PVP_SNAPSHOT_INTERVAL_MS=60")&&
 html.includes("const PVP_REMOTE_RENDER_DELAY_MS=90")&&html.includes("const PVP_REMOTE_RENDER_DELAY_MIN_MS=72"),
 'PvP uses a faster authoritative cadence plus a jitter-safe interpolation buffer without changing War constants');
assert(html.includes("if(state.mode==='pvp'){")&&html.includes("F.set(F.ref(F.firebaseDb,`rooms/${roomId}/inputs/${uid}`)")&&
 html.includes("const tail=this.inputQueue[this.inputQueue.length-1]"),
 'PvP inputs bypass ACK backpressure while PvE retains the previous queued transport');
assert(html.includes("const roomId=this.roomId,uid=this.localPlayerId")&&html.includes("this.roomId===roomId&&this.localPlayerId===uid"),
 'the legacy queued transport stays scoped to the room and player that created it');
assert(html.includes("const PVP_INPUT_KEEPALIVE_MS=150")&&html.includes("signature===NetworkAdapter.lastInputSignature"),
 'unchanged PvP inputs are deduplicated with a bounded keepalive instead of flooding Firebase');
assert(html.includes("input.pvpInputSeq=++NetworkAdapter.pvpInputSeq")&&html.includes("e.pvpLastInputSeq=inputSeq"),
 'PvP uses monotonic input sequence numbers and host acknowledgements for reconciliation');
assert(html.includes("hasUnacknowledgedInput")&&html.includes("authArrivalAge<800")&&html.includes("netAuthInputSeq"),
 'a guest never snaps back to an authoritative pose that predates its latest unacknowledged input');
assert(html.includes("serverAt:F.serverTimestamp()")&&html.includes("remoteSampleAt")&&html.includes("pvpSnapshotJitterEwma"),
 'PvP snapshots carry host time and use an adaptive jitter buffer instead of packet arrival time');
assert(html.includes("function pvpRemoteInputFor(ownerId)")&&html.includes("const PVP_INPUT_STALE_MS=420"),
 'the host stops stale guest movement if keepalives disappear instead of drifting indefinitely');
assert(html.includes("async handoffPVPHost(reason='hidden')")&&html.includes("pvpNextHostCandidate(room,this.localPlayerId,requireForeground)"),
 'a backgrounded PvP host must hand authority to another participant instead of pausing the match');
assert(html.includes("const op=F.onDisconnect(F.ref(F.firebaseDb,successorUid?")&&
 html.includes("`rooms/${code}/hostUid`")&&
 html.includes("`rooms/${code}`")&&
 html.includes("await op.set(successorUid)")&&html.includes("await op.remove()"),
 'the current PvP host must transfer hostUid when a successor exists, or delete the whole room when it is the last player');
assert(html.includes("function claimPVPHostIfOrphaned(room)")&&html.includes("function pvpSyncOnlineParticipants(room)"),
 'PvP must recover an orphaned host and remove disconnected human characters during a running match');
assert(html.includes("if(wasHost&&runningPVP)await this.handoffPVPHost('leave')"),
 'leaving a running PvP match must migrate host authority instead of deleting the room');
assert(html.includes("NetworkAdapter.handoffPVPHost('hidden')")&&html.includes("window.addEventListener('pagehide'"),
 'visibility/pagehide must trigger PvP host migration on PC and mobile');
assert(html.includes("const ROOM_LEGACY_INACTIVITY_MS=2*60*1000")&&html.includes("function roomIsCurrentCode(code)"),
 'legacy/random room codes must use a shorter stale timeout than current room codes');
assert(html.includes("const maxIdle=roomIsCurrentCode(code)?ROOM_INACTIVITY_MS:ROOM_LEGACY_INACTIVITY_MS"),
 'room expiration must depend on heartbeat age and code generation, not match-finished status');
assert(!section('function finishGame(msg,result=null){','})();').includes("NetworkAdapter.leaveRoom().catch(console.error)"),
 'finishing a match must preserve the current room and its players');
assert(!section("if(state.phase==='finished'&&!NetworkAdapter.remoteFinishScheduled){",'function configureGameScreenForMode(){').includes("NetworkAdapter.leaveRoom().catch(console.error)"),
 'remote peers must remain in the room after the result screen');
assert(html.includes("const patch={};for(const code of expired)patch[code]=null")&&html.includes("if(!bulkRemoved)await Promise.all"),
 'room cleanup must bulk-delete stale rooms with a per-room fallback for Firebase rules');
assert(html.includes("const op=F.onDisconnect(F.ref(F.firebaseDb,successorUid?")&&html.includes("`rooms/${code}`"),
 'the final running PvP host must arm whole-room deletion on abrupt disconnect');
assert(html.includes("function pvpPredictGuestLocal(dt)")&&html.includes("PVP_LOCAL_SOFT_ERROR_PX"),
 'non-host PvP movement must be predicted locally and softly reconciled');
assert(html.includes("const PVP_REGION_ENTER_MARGIN_PX=140")&&html.includes("const PVP_REGION_SIM_MARGIN_PX=380")&&
 html.includes("function pvpRegionalAuthorityDecision"),
 'PvP must use stable expanded authority bubbles with hysteresis instead of changing the global room host');
assert(html.includes("pvpHostView=state.mode==='pvp'?pvpCurrentAuthorityView():null")&&html.includes("pvpDamageEvents,pvpHostView"),
 'the global host publishes its actual PvP camera rectangle with each authoritative snapshot');
assert(html.includes("rooms/${roomId}/regions/${uid}")&&html.includes("async pushPVPRegion(snapshot)"),
 'non-hosts must publish isolated regional simulation snapshots through Firebase');
assert(html.includes("function pvpBuildRegionalSnapshot(handoff=false)")&&html.includes("pvpPackRegionalEntity")&&
 html.includes("dragonProjectiles:projectiles.map"),
 'regional snapshots must carry complete entity, projectile and runtime animation state');
assert(html.includes("function pvpIntegrateRemoteRegions(now=performance.now())")&&html.includes("pvpHostShouldSimulateEntity"),
 'the global host must ingest remote bubbles and stop double-simulating leased entities');
assert(html.includes("function updatePVPRegional(dt)")&&html.includes("pvpAllyBotAction(e,dt)")&&html.includes("pvpBotAction(e,dt)"),
 'a delegated guest must run the complete local PvP combat engine, including NPC AI');
assert(html.includes("updateDragonProjectiles(dt,entityById,pvpLocalRegionOwnsProjectile)")&&
 html.includes("updateDragonBurns(now,entityById,pvpLocalRegionOwnsEntity)"),
 'regional authority must include projectiles and burn damage, not only player movement');
assert(html.includes("pvpRegionEncodeRuntime")&&html.includes("__pvpRegionTime")&&html.includes("pvpRegionDecodeRuntime"),
 'handoff must transfer running timers so attacks and GIF timelines continue instead of restarting');
assert(html.includes("PVP_REGION_HOST_PRIORITY_MARGIN_PX=90")&&html.includes("takeover=!!packet.handoff"),
 'the host must take priority when camera regions meet and continue from the final regional snapshot');
assert(html.includes("pvpNextRegionalEntityId()")&&html.includes("pvpNextRegionalProjectileId"),
 'region-created summons and projectiles need collision-safe distributed IDs');
assert(html.includes("input.pvpRegionalAuthority=!!regionalPose")&&html.includes("input.pvpRegionalPose=regionalPose"),
 'pose packets remain as a low-latency first-packet fallback before full regional snapshots arrive');
assert(html.includes("if(regional){")&&html.includes("PVP_REGION_HARD_SNAP_ERROR_PX"),
 'a delegated guest ignores stale host pullback while retaining catastrophic reconnect correction');
assert(html.includes("pvpPredictGuestLocal(dt);\n     if(pvpLocalRegionalAuthority){\n       updatePVPRegional(dt);"),
 'guest prediction must feed full regional simulation before its state is published');
assert(html.includes("(pvpLocalRegionalAuthority&&pvpLocalRegionOwnsEntity(e))"),
 'all locally owned regional entities must bypass delayed host interpolation');
assert(html.includes("const networkPushInterval=state.mode==='pvp'?PVP_SNAPSHOT_INTERVAL_MS:120;"),
 'only PvP uses the faster host snapshot cadence');
assert(html.includes("return nick+' • Nv. '+level"),
 'human PvP combat labels must show account nick and level');
assert(html.includes("level:currentAccountLevel()"),
 'PvP room participants must publish their current account level');
assert(html.includes("state.mode!=='war'&&state.mode!=='pvp'"),
 'PvP uses the GPU camera compositor during camera motion and Warrior zoom');
assert(html.includes("requestIdleCallback")&&html.includes("pvpWarriorSpecial','pvpWarriorAttack"),
 'large PvP GIF duration parsing is prioritized in idle time from the lobby');
assert(html.includes("syncPVPPowerEffects(domCamera.left"),'animated mage power');
// Wave staging and the actual War AI dispatch are PvP-only.
assert(html.includes("if(state.mode==='pvp'&&e.pvpMode&&!e.pvpWarAI)"),'NPCs must use real War GIF states');
assert(html.includes("if(state.mode==='pvp'&&e.pvpWarAI)Object.assign(out,serializeWarEntityForNetwork(e,now))"),'real NPC attack state must reach remote peers');
assert(html.includes('updateDragonProjectiles(dt,entityById,pvpHostShouldSimulateProjectile);updateDragonBurns(now,entityById,pvpHostShouldSimulateEntity);'),'host PvP projectiles and burns must respect regional authority');
assert(html.includes("state.mode==='pvp'&&attacker.pvpWarAI&&target.pvpMode"),'NPC damage needs PvP-only tuning');
assert(!section('function updatePVP(dt){','function updatePVPHUD(){').includes('state.timeLeft-=dt;'),'PvP simulation must not decrement a round timer');
assert(html.includes("if(!enemiesAlive&&pvpLastWave===PVP_ENEMY_WAVES.length-1)endPVPRound()"),
 'a PvP round ends only after the final clan/wave cycle is cleared');
assert(html.includes("humans.length===1&&humans[0].pvpEliminated"),
 'solo match ends only after the difficulty life limit is exhausted');
assert(html.includes("humans.length>1&&!humans.some(p=>pvpHumanStillInRound(p))"),
 'online PvP keeps going while at least one real player can still fight or revive');
state.players=[{id:'u1',name:'Alice',human:true,pvpHero:'warrior',color:'#abc'}];
run('beginPVPRound()');
assert.equal(state.pvpRoundDuration,0,'PvP rounds are untimed');
assert.equal(state.timeLeft,0,'PvP no longer counts down a round clock');
assert(html.includes('id="pvpTimeConfig"')&&html.includes('id="pvpSpeedConfig"')&&html.includes('pvp-simple-config'),
 'PvP configuration hides time and speed controls');
assert(html.includes("const minRounds=state.mode==='pvp'&&!b.closest('#warLobbySettings')?1:2"),
 'PvP round selector allows one round while War keeps two as minimum');
assert.equal(run('pvpLastWave'),0);
assert.deepEqual([...state.entities.filter(e=>e.team==='pvp-enemy').map(e=>e.type)],['dragon','dragon']);
assert(state.entities.filter(e=>e.type==='dragon').every(e=>e.dragonFlightState==='takeoff'));
run('updatePVP(.016)');
assert(warCalls.includes('dragon'),'PvP NPC invokes the real NPC AI dispatcher');
for(let wave=1;wave<4;wave++){
 state.entities.filter(e=>e.team==='pvp-enemy').forEach(e=>e.alive=false);
 run('updatePVP(.016)');
 assert.equal(run('pvpLastWave'),wave-1,'next group waits for its delay');
 now+=1250;run('updatePVP(.016)');
 assert.equal(run('pvpLastWave'),wave);
 const kinds=state.entities.filter(e=>e.alive&&e.team==='pvp-enemy').map(e=>e.type);
 const expected=[['poseidon','seahorse','seahorse','seahorse','seahorse','seahorse'],['anubis','naja'],['golem']][wave-1];
 assert.deepEqual([...kinds],expected,'wave '+wave+' composition and no previous enemies');
 if(wave===1){
   const poseidon=state.entities.find(e=>e.alive&&e.type==='poseidon');
   assert(state.entities.filter(e=>e.alive&&e.type==='seahorse').every(e=>e.waterSummonerId===poseidon.id));
 }
}
assert.equal(run('PVP_ENEMY_WAVES.length'),4);
assert.equal(run('PVP_DIFFICULTY.normal.waves[0][0][0]'),'dragon');
assert.equal(run('PVP_DIFFICULTY.normal.waves[0][0][1]'),5);
assert.equal(run('PVP_DIFFICULTY.normal.waves[1][1][1]'),9);
assert.equal(run('PVP_DIFFICULTY.normal.waves[2][0][1]'),5);
assert.equal(run('PVP_DIFFICULTY.hard.waves[0][0][1]'),6);
assert.equal(run('PVP_DIFFICULTY.hard.waves[1][1][1]'),11);
assert.equal(run('PVP_DIFFICULTY.hard.waves[3][0][1]'),4);
assert.equal(run('PVP_REVIVE_DELAY_MS'),10000,'each participant receives a ten-second revive while lives remain');
assert.equal(run('pvpLifeLimit()'),2,'easy and normal PvP keep two total lives');
let roundHero=state.entities.find(e=>e.ownerId==='u1'&&!e.pvpMinion);
assert(roundHero&&roundHero.alive);
run('pvpRegisterRoundDeath(state.entities.find(e=>e.ownerId==="u1"&&!e.pvpMinion),performance.now())');
roundHero.alive=false;
assert.equal(state.players[0].pvpRoundDeaths,1);
assert.equal(state.players[0].pvpEliminated,false);
assert.equal(state.players[0].pvpReviveAt,now+10000);
now+=9999;run('pvpProcessRoundRevives(performance.now())');
assert.equal(state.entities.some(e=>e.alive&&!e.pvpMinion&&e.ownerId==='u1'),false,'first death waits ten seconds');
now+=2;run('pvpProcessRoundRevives(performance.now())');
roundHero=state.entities.find(e=>e.alive&&!e.pvpMinion&&e.ownerId==='u1');
assert(roundHero,'first death respawns the participant in the same round');
assert.equal(state.players[0].pvpRoundDeaths,1);
run('pvpRegisterRoundDeath(state.entities.find(e=>e.alive&&!e.pvpMinion&&e.ownerId==="u1"),performance.now())');
roundHero.alive=false;
assert.equal(state.players[0].pvpRoundDeaths,2);
assert.equal(state.players[0].pvpEliminated,true,'second death eliminates the participant for the current round');
assert.equal(state.players[0].pvpReviveAt,0);
run('beginPVPRound()');
assert.equal(state.players[0].pvpRoundDeaths,0,'new round restores the extra life');
assert.equal(state.players[0].pvpEliminated,false);
assert(state.entities.some(e=>e.alive&&!e.pvpMinion&&e.ownerId==='u1'),'new round restores full participant spawn');
state.difficulty='normal';
run('beginPVPRound()');
assert.equal(state.entities.filter(e=>e.team==='pvp-enemy').length,5);
assert(state.entities.filter(e=>e.type==='dragon').every(e=>e.maxHp===300&&e.maxShield===250&&e.pvpDamageBonus===10));
const mediumNaja=run('pvpBaseEntity({...PVP_ENEMY_HEROES.naja,id:"naja"},700,700,"pvp-enemy","#f77",null,true)');
assert.equal(mediumNaja.maxHp,350);assert.equal(mediumNaja.maxShield,300);assert.equal(mediumNaja.pvpDamageBonus,20);
state.difficulty='hard';
const hardPoseidon=run('pvpBaseEntity({...PVP_ENEMY_HEROES.poseidon,id:"poseidon"},700,700,"pvp-enemy","#f77",null,true)');
assert.equal(hardPoseidon.maxHp,375);assert.equal(hardPoseidon.maxShield,325);assert.equal(hardPoseidon.pvpDamageBonus,25);
assert.equal(run('pvpLifeLimit()'),3,'hard PvP grants three total lives');
run('beginPVPRound()');
for(let death=1;death<=2;death++){
 roundHero=state.entities.find(e=>e.alive&&!e.pvpMinion&&e.ownerId==='u1');
 assert(roundHero,'hard mode participant must be alive before death '+death);
 run('pvpRegisterRoundDeath(state.entities.find(e=>e.alive&&!e.pvpMinion&&e.ownerId==="u1"),performance.now())');
 roundHero.alive=false;
 assert.equal(state.players[0].pvpRoundDeaths,death);
 assert.equal(state.players[0].pvpEliminated,false,'hard mode still has a life after death '+death);
 assert.equal(state.players[0].pvpReviveAt,now+10000);
 now+=10001;run('pvpProcessRoundRevives(performance.now())');
 assert(state.entities.some(e=>e.alive&&!e.pvpMinion&&e.ownerId==='u1'),'hard mode revives after death '+death);
}
roundHero=state.entities.find(e=>e.alive&&!e.pvpMinion&&e.ownerId==='u1');
run('pvpRegisterRoundDeath(state.entities.find(e=>e.alive&&!e.pvpMinion&&e.ownerId==="u1"),performance.now())');
roundHero.alive=false;
assert.equal(state.players[0].pvpRoundDeaths,3);
assert.equal(state.players[0].pvpEliminated,true,'third death eliminates the participant on hard');
assert.equal(state.players[0].pvpReviveAt,0);
state.difficulty='easy';
assert(html.includes("const networkPushInterval=state.mode==='pvp'?PVP_SNAPSHOT_INTERVAL_MS:120;"),
 'PvP uses its low-latency cadence while Clan War remains at 120ms');
assert(html.includes("desired=pvpPreserveGifState(el,desired)"),'PvP full GIF-cycle protection');
assert(html.includes("img.pvp-gif-loading")&&html.includes("img:not([src])"),'PvP hides unloaded sprites');
assert(html.includes("return String(cycle.serial)!==String(serial)"),'same serial never replays; new cast can start');
assert(html.includes("alpha=Math.min(clamp((now-started)/180"),'PvP special power is not dimmed for most of its duration');
assert(html.includes("state.mode==='pvp'&&stateName==='anubisRanged'"),'Anubis ranged GIF visible in PvP');
assert(html.includes("syncPVPSpecialEffects(domCamera.left"),'PvP ally special effect layer');
state.players=[{id:'u1',name:'Alice',human:true,pvpHero:'warrior',color:'#abc'},
 {id:'npc_1',name:'NPC 1',human:false,pvpHero:'mageFemale',color:'#e3b341'},
 {id:'npc_2',name:'NPC 2',human:false,pvpHero:'warrior',color:'#3fb950'}];
net.hostUid='u1';run('beginPVPRound()');
assert.equal(state.world.w,1850);assert.equal(state.world.h,1542);
const allied=state.entities.filter(e=>e.pvpAllyBot);
assert.deepEqual([...allied.map(e=>e.type)],['mage','warrior']);
assert(allied.every(e=>e.team==='u1'&&e.maxHp===250&&e.maxShield===150&&e.speed===195&&!e.pvpWarAI));
assert(state.entities.filter(e=>e.team==='pvp-enemy').every(e=>!e.pvpAllyBot));
run('updatePVP(.016)');
// A PvP dragon must emit an actual ball even when repetitive hits keep it
// briefly knocked back; the War AI intentionally does not act during knockback.
const defendingDragon=state.entities.find(e=>e.alive&&e.type==='dragon');
const defendingTarget=state.entities.find(e=>e.alive&&!e.pvpMinion);
defendingDragon.x=defendingTarget.x+110;defendingDragon.y=defendingTarget.y;
defendingDragon.dragonFlightState='flying';defendingDragon.knockTime=.06;
defendingDragon.dragonNextShotAt=0;defendingDragon.dragonCloseShotAt=0;defendingDragon.pvpNpcNextAttackAt=0;
let retaliatoryShots=0;
ctx.launchDragonFireball=e=>{retaliatoryShots++;e.dragonAttackSerial=(e.dragonAttackSerial||0)+1;return true};
run('pvpBotAction(state.entities.find(e=>e.id==='+defendingDragon.id+'),.016)');
assert.equal(retaliatoryShots,1,'PvP dragon releases a projectile when hit');
assert(defendingDragon.pvpNpcNextAttackAt>now,'retaliation observes complete GIF recovery');
defendingDragon.pvpDragonFirstHitSeen=true;defendingDragon.pvpDragonRetaliatePending=false;
defendingDragon.pvpDragonObservedDurability=defendingDragon.hp+defendingDragon.shield;
defendingDragon.shield-=10;
run('pvpObserveDragonDamage(state.entities.find(e=>e.id==='+defendingDragon.id+'))');
assert(defendingDragon.pvpDragonRetaliatePending,'direct NPC hits also queue dragon fire');
assert(!defendingDragon.pvpDragonRetaliateImmediate,'later hits retain their cooldown');
now=defendingDragon.pvpNpcNextAttackAt+1;defendingDragon.knockTime=0;
run('pvpBotAction(state.entities.find(e=>e.id==='+defendingDragon.id+'),.016)');
assert.equal(retaliatoryShots,2,'dragon attacks again after a subsequent hit');
state.pvpDamageSeq=0;state.pvpDamageEvents=[];
run('recordPVPDamage(state.entities[0],15)');
assert.equal(state.pvpDamageEvents[0].amount,15);
assert.equal(state.pvpDamageEvents[0].serial,1);
const drawing=[];
const paint={save(){},restore(){},strokeText:(...a)=>drawing.push(a),fillText(){}};
ctx.paint=paint;run('drawPVPDamageNumbers(paint,performance.now()+500)');
assert.equal(drawing[0][0],'-15');
run('drawPVPDamageNumbers(paint,performance.now()+1100)');
assert.equal(drawing.length,1,'damage text expires after one second');
// Regression: one special serial triggers exactly one action and one complete GIF.
run('pvpGifFullDurationMs.set("kingSpecial",1200);pvpGifFullDurationMs.set("kingPower",900)');
const royal=run('pvpBaseEntity(PVP_HERO_BY_ID.king,500,500,"u1","#e3b341","royal",false)');
const started=now;
assert(run('pvpSpecialAttack(state.entities.find(e=>e.id==='+royal.id+'))'));
assert.equal(royal.pvpSpecialSerial,1);
assert.equal(royal.pvpActionUntil,started+1200);
assert.equal(run('pvpSpecialAttack(state.entities.find(e=>e.id==='+royal.id+'))'),false,'no repeated special during action');
assert.equal(royal.pvpSpecialSerial,1);
now+=700;royal.attackCooldown=0;
assert.equal(run('pvpBasicAttack(state.entities.find(e=>e.id==='+royal.id+'))'),false,'basic cannot interrupt special');
now+=501;
assert(run('pvpBasicAttack(state.entities.find(e=>e.id==='+royal.id+'))'),'basic resumes after complete special');
assert.equal(royal.pvpSpecialSerial,1,'normal attack does not retrigger special');

let visualStops=0;
const visual={_src:'gif',closest:()=>element,classList:{contains:()=>false},hasAttribute:()=>!!visual._src,removeAttribute(){this._src=''}};
const element={_pvpGifCycle:null,classList:{contains:()=>false}};
ctx.fakePvpImage=visual;ctx.fakePvpElement=element;
ctx.stopGif=image=>{if(image._src){visualStops++;image._src=''}};
run('pvpGifFullDurationMs.set("kingSpecial",1000)');
run('pvpRememberGifCycle(fakePvpImage,"kingSpecial",7)');
assert.equal(run('pvpPreserveGifState(fakePvpElement,"idle")'),'special');
assert.equal(run('pvpMayRestartGif(fakePvpImage,"kingSpecial",8)'),true,'new cast can replace a prior special GIF without waiting for its deadline');
assert.equal(run('pvpMayRestartGif(fakePvpImage,"kingSpecial",7)'),false,'the same cast cannot replay its GIF');
now+=976;
assert.equal(run('pvpPreserveGifState(fakePvpElement,"special")'),'idle','spent serial cannot remain in special');
assert.equal(visualStops,1,'GIF is stopped exactly once before its second loop');
assert.equal(run('pvpMayRestartGif(fakePvpImage,"kingSpecial",8)'),true,'new action may start after one full cycle');
assert.equal(run('pvpPreserveGifState(fakePvpElement,"special")'),'idle','stale pending special cannot revive same GIF');
assert.equal(visualStops,1);

// PvP FX nodes are retained after playback until the ability window ends, preventing
// the same serial from being re-created or replayed by a delayed network snapshot.
let fxRestarts=0,fxStops=0;
ctx.restartGif=(image,key,serial)=>{image._src='gif';fxRestarts++;return true};
ctx.stopGif=image=>{if(image._src){image._src='';fxStops++}};
ctx.entityCameraLayer={appendChild(){}};ctx.combatCameraLayer={appendChild(){}};ctx.renderFrameNow=now;
// PvP effect maps/functions were already loaded with the isolated PvP section.
royal.pvpSpecialFxStartedAt=now;royal.pvpSpecialFxUntil=now+3000;
run('syncPVPSpecialEffects(0,0,1,2000,1600)');
assert.equal(fxRestarts,1);
now+=880;ctx.renderFrameNow=now;run('syncPVPSpecialEffects(0,0,1,2000,1600)');
assert.equal(fxStops,1);
now+=200;ctx.renderFrameNow=now;run('syncPVPSpecialEffects(0,0,1,2000,1600)');
assert.equal(fxRestarts,1,'spent special FX serial must not replay while its window remains active');
// Long PvP specials must not create a negative Canvas radius.
const oldEntities=state.entities;
state.entities=[royal];royal.pvpSpecialVisualUntil=now+4000;royal.pvpSpecialBodyDuration=4000;
royal.pvpSpecialOriginX=royal.x;royal.pvpSpecialOriginY=royal.y;
let canvasSaveCount=0;const drawnRadii=[];
ctx.effectCtx={save(){canvasSaveCount++},restore(){canvasSaveCount--},beginPath(){},
 arc(x,y,r){assert(r>=0&&Number.isFinite(r),'PvP special radius must be finite/nonnegative');drawnRadii.push(r)},
 stroke(){},translate(){},rotate(){},fillRect(){},moveTo(){},lineTo(){}};
run('drawPVPEffects(effectCtx,performance.now())');
assert(drawnRadii.some(r=>r>=90&&r<=240),'long special draws its area circle');
assert.equal(canvasSaveCount,0,'PvP visuals restore Canvas state');
state.entities=oldEntities;royal.pvpSpecialVisualUntil=0;
royal.pvpSpecialSerial++;royal.pvpSpecialFxStartedAt=now;royal.pvpSpecialFxUntil=now+3000;
run('syncPVPSpecialEffects(0,0,1,2000,1600)');
assert.equal(fxRestarts,2,'a genuinely new activation plays a new effect');
royal.pvpSpecialFxUntil=now-1;run('syncPVPSpecialEffects(0,0,1,2000,1600)');
const alreadyPlayed=royal.pvpSpecialSerial;
royal.pvpSpecialFxUntil=now+400; // stale network snapshot for the same cast
run('syncPVPSpecialEffects(0,0,1,2000,1600)');
assert.equal(fxRestarts,2,'late snapshot cannot replay an already spent GIF');
assert.equal(run('pvpSpecialFxPlayedSerial.get('+royal.id+')'),alreadyPlayed);
console.log('PvP serial-based special, action lock, one-shot body and effect GIFs: PASS');
console.log('PvP isolated arena, allied NPCs, NPC recovery, Poseidon and damage text: PASS');
console.log('PvP real NPC dispatcher, dragon takeoff, remote state and sequential enemy groups: PASS');
console.log('PvP hero registry, independent stats, mage specials, summons, power damage, mobile camera: PASS');

async function testPVPReadyLobby(){
 state.running=false;state.phase='idle';
 state.players=[
   {id:'u1',name:'Alice',human:true,pvpHero:'warrior',pvpConfirmed:false,color:'#abc'},
   {id:'u2',name:'Beto',human:true,pvpHero:'mageFemale',pvpConfirmed:false,color:'#def'}
 ];
 const grid=node('#playerList');
 grid.children=[];grid.replaceChildren=function(){this.children=[]};grid.appendChild=function(child){this.children.push(child)};
 ctx.localPlayer=()=>state.players.find(p=>p.id===net.localPlayerId);
 ctx.renderPlayers=()=>{};
 const updates=[];
 net.roomId='TEST';net.isHost=true;
 net.waitFirebase=async()=>({
   firebaseAuth:{currentUser:{uid:'u1'}},firebaseDb:{},
   ref:(_db,path)=>path,
   update:async (path,data)=>{updates.push({path,data})}
 });
 assert.equal(run('pvpAllPlayersConfirmed()'),false);
 run('renderPVPPlayers(state.players,[])');
 assert.equal(grid.children.length,4,'PvP lobby maximum four participants');
 assert.equal(grid.children[0].className.includes('mine'),true);
 run('openPVPCharacterPicker()');
 assert.equal(node('#pvpPicker').hidden,false);
 run("pvpPickerDraft='mageFemale'");
 await run('commitPVPCharacterPicker()');
 assert.equal(updates.length,1);
 assert.equal(updates[0].path,'rooms/TEST/players/u1');
 assert.equal(updates[0].data.pvpHero,'mageFemale');
 assert.equal(updates[0].data.pvpConfirmed,true);
 assert.equal(state.players[0].pvpConfirmed,true);
 assert.equal(state.players[0].pvpHero,'mageFemale');
 assert.equal(run('pvpAllPlayersConfirmed()'),false,'wait for other human');
 state.players[1].pvpConfirmed=true;
 assert.equal(run('pvpAllPlayersConfirmed()'),true);
 console.log('PvP four-ally cap, own-card hero confirmation and readiness: PASS');
}
testPVPReadyLobby().catch(e=>{console.error(e);process.exitCode=1});
