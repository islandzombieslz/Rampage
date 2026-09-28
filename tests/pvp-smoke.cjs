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
 setAttribute(){},children:[],hidden:false,disabled:false
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
 clearEntityVisuals(){},flash(){},navigateScreen(){},configureGameScreenForMode(){},
 beginMatchTracking(){},matchStatsFor:uid=>state.matchStats[uid]||(state.matchStats[uid]={damage:0,wonRounds:0,victorySeconds:0,victoryTimeLimit:0}),
 finishGame(){},difficultyConfig:{easy:{initial:1,every:20,wave:1}},getLocalMovement:()=>({dx:0,dy:0,attackSeq:net.attackSeq}),
 sendLocalPVEInput(){},setTimeout(){},requestAnimationFrame(){}
});
vm.runInContext('const gifRuntime=new Map(); const pvpGifFullDurationMs=new Map();',ctx);
vm.runInContext(section('const PVP_HEROES=Object.freeze(', 'function setLobbySkin('),ctx);
vm.runInContext(section('const PVP_ARENA=Object.freeze(', '/* ==================== PVE ==================== */'),ctx);
const warCalls=[];
ctx.beginDragonTakeoff=e=>{e.dragonFlightState='takeoff';e.dragonTakeoffSerial=(e.dragonTakeoffSerial||0)+1;return true};
ctx.aiFight=(e,dt,team,targets)=>{warCalls.push(e.type)};
ctx.warBurningEntities=new Set();
ctx.warFrameEnemiesByTeam=new Map();
ctx.rebuildWarEntityIdMap=()=>new Map(state.entities.map(e=>[e.id,e]));
ctx.updateDragonProjectiles=()=>{};
ctx.updateDragonBurns=()=>{};
const run=expr=>vm.runInContext(expr,ctx);
const heroes=run('PVP_HEROES'),base=run('PVP_BASE');
assert.equal(heroes.length,8);
assert.deepEqual(Array.from(run('PVP_SELECTABLE_HEROES'),h=>h.id),['warrior','mageFemale','egyptMageFemale']);
assert.equal(run('PVP_SELECTABLE_BY_ID.king'),undefined);
for(const h of heroes)assert(h.card.startsWith('assets/')&&h.name&&h.id);
assert.equal(new Set(heroes.map(h=>h.id)).size,8);
assert.equal(run('PVP_ENEMY_HERO_IDS.length'),5);
assert.equal(base.hp,250);assert.equal(base.shield,150);
assert.equal(base.damageMin,25);assert.equal(base.damageMax,40);
assert.equal(base.meleeCooldown,.70);assert.equal(base.specialCooldown,20000);
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

const hero=run('pvpBaseEntity(PVP_HERO_BY_ID.warrior,500,500,"u1","#aaa","u1",false)');
const foe=run('pvpBaseEntity({...PVP_ENEMY_HEROES.naja,id:"naja"},595,500,"pvp-enemy","#f77",null,true)');
assert.equal(hero.maxHp,250);assert.equal(hero.maxShield,150);assert.equal(hero.speed,195);
assert.equal(foe.maxHp,300);assert.equal(foe.maxShield,250);assert.equal(foe.speed,117);
assert.equal(foe.pvpDamageBonus,10);
assert.equal(foe.damage,20);assert.equal(foe.controlled,false);
assert(run('pvpBasicAttack(state.entities[0])'));
assert.equal(damageCalls.length,1);assert(damageCalls[0].damage>=25&&damageCalls[0].damage<=40);
assert.equal(damageCalls[0].options.knockForce,95);
assert.equal(run('pvpBasicAttack(state.entities[0])'),false,'basic attack cooldown');

const mage=run('pvpBaseEntity(PVP_HERO_BY_ID.mage,1050,500,"u2","#ffe","u2",false)');
assert(mage.pvpSpecialReadyAt>1e13,'warrior mage cannot cast before shield break');
mage.shield=10;
const attacker=foe;attacker.x=1100;attacker.y=500;
run('pvpCombatHit(state.entities[2],state.entities[1],20)');
assert.equal(mage.shield,0);
assert.equal(mage.pvpSpecialReadyAt,110000,'10 s shield break gate');
now=110001;
assert(run('pvpSpecialAttack(state.entities[2])'));
assert.equal(mage.pvpSpecialDuration,40000);
assert.equal(mage.pvpSpecialReadyAt,150001);

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
assert(html.includes("state.mode==='pvp'?pvpCameraZoom(vw,vh):1.80"));
assert(html.includes("if(state.mode==='pvp')updatePVP(dt);else updateWar(dt)"));
assert(html.includes("pvpConfirmed:true"),'networked hero confirmation');
assert(html.includes("syncPVPPowerEffects(domCamera.left"),'animated mage power');
// Wave staging and the actual War AI dispatch are PvP-only.
assert(html.includes("if(state.mode==='pvp'&&e.pvpMode&&!e.pvpWarAI)"),'NPCs must use real War GIF states');
assert(html.includes("if(state.mode==='pvp'&&e.pvpWarAI)Object.assign(out,serializeWarEntityForNetwork(e,now))"),'real NPC attack state must reach remote peers');
assert(html.includes('updateDragonProjectiles(dt,entityById);updateDragonBurns(now,entityById);'),'PvP projectiles and burns must simulate');
assert(html.includes("state.mode==='pvp'&&attacker.pvpWarAI&&target.pvpMode"),'NPC damage needs PvP-only tuning');
state.players=[{id:'u1',name:'Alice',human:true,pvpHero:'warrior',color:'#abc'}];
run('beginPVPRound()');
assert.equal(state.pvpRoundDuration,180);
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
state.difficulty='normal';
run('beginPVPRound()');
assert.equal(state.entities.filter(e=>e.team==='pvp-enemy').length,5);
assert(state.entities.filter(e=>e.type==='dragon').every(e=>e.maxHp===300&&e.maxShield===250&&e.pvpDamageBonus===10));
const mediumNaja=run('pvpBaseEntity({...PVP_ENEMY_HEROES.naja,id:"naja"},700,700,"pvp-enemy","#f77",null,true)');
assert.equal(mediumNaja.maxHp,350);assert.equal(mediumNaja.maxShield,300);assert.equal(mediumNaja.pvpDamageBonus,20);
state.difficulty='hard';
const hardPoseidon=run('pvpBaseEntity({...PVP_ENEMY_HEROES.poseidon,id:"poseidon"},700,700,"pvp-enemy","#f77",null,true)');
assert.equal(hardPoseidon.maxHp,375);assert.equal(hardPoseidon.maxShield,325);assert.equal(hardPoseidon.pvpDamageBonus,25);
state.difficulty='easy';
assert(html.includes("state.mode==='pvp'?180:120"),'PvP-only lower snapshot frequency');
assert(html.includes("if(state.mode==='pvp')desired=pvpPreserveGifState(el,desired)"),'PvP full GIF-cycle protection');
assert(html.includes("state.mode==='pvp'&&stateName==='anubisRanged'"),'Anubis ranged GIF visible in PvP');
assert(html.includes("syncPVPSpecialEffects(domCamera.left"),'PvP ally special effect layer');
state.players=[{id:'u1',name:'Alice',human:true,pvpHero:'warrior',color:'#abc'},
 {id:'npc_1',name:'NPC 1',human:false,pvpHero:'mageFemale',color:'#e3b341'},
 {id:'npc_2',name:'NPC 2',human:false,pvpHero:'egyptMageFemale',color:'#3fb950'}];
net.hostUid='u1';run('beginPVPRound()');
assert.equal(state.world.w,1850);assert.equal(state.world.h,1542);
const allied=state.entities.filter(e=>e.pvpAllyBot);
assert.deepEqual([...allied.map(e=>e.type)],['mage','mage']);
assert(allied.every(e=>e.team==='u1'&&e.maxHp===250&&e.maxShield===150&&e.speed===195&&!e.pvpWarAI));
assert(state.entities.filter(e=>e.team==='pvp-enemy').every(e=>!e.pvpAllyBot));
run('updatePVP(.016)');
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
const visual={_src:'gif',closest:()=>element,hasAttribute:()=>!!visual._src,removeAttribute(){this._src=''}};
const element={_pvpGifCycle:null,classList:{contains:()=>false}};
ctx.fakePvpImage=visual;ctx.fakePvpElement=element;
ctx.stopGif=image=>{if(image._src){visualStops++;image._src=''}};
run('pvpGifFullDurationMs.set("kingSpecial",1000)');
run('pvpRememberGifCycle(fakePvpImage,"kingSpecial",7)');
assert.equal(run('pvpPreserveGifState(fakePvpElement,"idle")'),'special');
assert.equal(run('pvpMayRestartGif(fakePvpImage,"kingSpecial",8)'),false,'new attack cannot restart a GIF mid-cycle');
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
royal.pvpSpecialFxUntil=now+3000;
run('syncPVPSpecialEffects(0,0,1,2000,1600)');
assert.equal(fxRestarts,1);
now+=880;ctx.renderFrameNow=now;run('syncPVPSpecialEffects(0,0,1,2000,1600)');
assert.equal(fxStops,1);
now+=200;ctx.renderFrameNow=now;run('syncPVPSpecialEffects(0,0,1,2000,1600)');
assert.equal(fxRestarts,1,'spent special FX serial must not replay while its window remains active');
royal.pvpSpecialSerial++;royal.pvpSpecialFxUntil=now+3000;
run('syncPVPSpecialEffects(0,0,1,2000,1600)');
assert.equal(fxRestarts,2,'a genuinely new activation plays a new effect');
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
 run("pvpPickerDraft='egyptMageFemale'");
 await run('commitPVPCharacterPicker()');
 assert.equal(updates.length,1);
 assert.equal(updates[0].path,'rooms/TEST/players/u1');
 assert.equal(updates[0].data.pvpHero,'egyptMageFemale');
 assert.equal(updates[0].data.pvpConfirmed,true);
 assert.equal(state.players[0].pvpConfirmed,true);
 assert.equal(state.players[0].pvpHero,'egyptMageFemale');
 assert.equal(run('pvpAllPlayersConfirmed()'),false,'wait for other human');
 state.players[1].pvpConfirmed=true;
 assert.equal(run('pvpAllPlayersConfirmed()'),true);
 console.log('PvP four-ally cap, own-card hero confirmation and readiness: PASS');
}
testPVPReadyLobby().catch(e=>{console.error(e);process.exitCode=1});

