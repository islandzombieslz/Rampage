const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const html=fs.readFileSync('index.html','utf8');
const required=[
 'assets/water/poseidon/card.png','assets/water/poseidon/idle.gif',
 'assets/water/poseidon/walk.gif','assets/water/poseidon/normal.gif',
 'assets/water/poseidon/special-wave.gif','assets/water/poseidon/special-summon.gif',
 'assets/water/poseidon/wave.gif','assets/water/seahorse/card.png',
 'assets/water/seahorse/idle.gif','assets/water/seahorse/walk.gif',
 'assets/water/seahorse/attack.gif'
];
for(const filename of required){
 const bytes=fs.readFileSync(filename);
 assert(bytes.length>1000,filename);
 if(filename.endsWith('.gif'))assert(['GIF87a','GIF89a'].includes(bytes.subarray(0,6).toString()),filename);
 else assert.equal(bytes.subarray(0,8).toString('hex'),'89504e470d0a1a0a',filename);
 assert(html.includes(filename),filename+' not wired to game');
}
assert(!html.includes('i.postimg.cc'),'runtime depends on Postimages');
for(const clan of ['warriors','egypt','water'])assert(html.includes('data-clan="'+clan+'"'));
assert(html.includes('data-clan-shop="water"'));
assert(html.includes("if(target.type==='poseidon'&&entityHasActiveSpecial(target))return;"));
assert(html.includes('syncWaterWaveEffects(domCamera.left'));
assert(html.includes('waterSummonerId:e.waterSummonerId??null'));
const js=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].at(-1)?.[1];
assert(js,'main JS block');
new vm.Script(js,{filename:'Rampage index inline script'});

const start=js.indexOf('/* WATER CLAN COMBAT');
const end=js.indexOf('function brownPowerPosition(',start);
assert(start>0&&end>start,'water combat block not found');
let clock=1000;
const state={entities:[],world:{w:1850,h:1542}};
const hitLog=[];
const ctx=vm.createContext({
 state,performance:{now:()=>clock},Math,
 clamp:(x,a,b)=>Math.min(b,Math.max(a,x)),
 dist:(a,b)=>Math.hypot(a.x-b.x,a.y-b.y),
 isRealCombatTarget:t=>!!t?.alive,
 canEngageTarget:()=>true,
 warEntityById:new Map(),
 najaIsUnderground:()=>false,
 entityHasActiveSpecial:()=>false,
 addWarGoalProgress:()=>{},
 applyCombatHit:(target,source,damage)=>{target.hp-=damage;hitLog.push({target:target.id,damage})},
 forEachWarSpatialCandidate:(a,b,c,d,callback)=>{
   for(const t of state.entities)if(t.x>=a&&t.x<=c&&t.y>=b&&t.y<=d)callback(t);
 },
 spawnSeahorse:(x,y,team,color,summonerId)=>{
   const e={id:100+state.entities.length,type:'seahorse',x,y,team,color,waterSummonerId:summonerId,waterSummoned:summonerId!==null,alive:true,hp:150,shield:summonerId===null?100:0,maxShield:summonerId===null?100:0};
   state.entities.push(e);return e;
 },
 nearestEngageableCandidate:()=>null
});
vm.runInContext(js.slice(start,end),ctx);
assert(html.includes('poseidon:750'),'Poseidon price');
assert(html.includes('naja:650'),'Naja price');
assert(html.includes('e.hp=e.maxHp=550;e.shield=e.maxShield=150;e.damage=75'),'Poseidon hp decrease');
assert(html.includes('e.hp=e.maxHp=230;\n e.shield=e.maxShield=230;'),'King HP and shield decrease');
assert(html.includes("e.attackCooldown=e.type==='king'?.90"),'King slower attack');
assert(html.includes("e.hp=e.maxHp=e.clan==='warriors'?250:200"),'Warrior mage only gains HP');
assert(html.includes('e.hp=e.maxHp=215;e.shield=e.maxShield=65;e.damage=ANUBIS_PROJECTILE_DAMAGE'),'Anubis HP');
assert(html.includes('const SEAHORSE_NORMAL_MS=1050;'),'Seahorse faster attack');
let poseidon={id:1,type:'poseidon',team:'water',color:'#0af',x:100,y:100,damage:75,
 alive:true,attackCooldown:0,knockTime:0,poseidonNormalCount:0,poseidonSpecialIndex:0};
let enemy={id:2,type:'warrior',team:'enemy',x:155,y:100,r:30,alive:true,hp:1000,shield:0};
const splash={id:3,type:'warrior',team:'enemy',x:175,y:100,r:30,alive:true,hp:1000,shield:0};
const ally={id:4,type:'warrior',team:'water',x:170,y:100,r:30,alive:true,hp:1000,shield:0};
state.entities.push(poseidon,enemy,splash,ally);
ctx.warEntityById.set(1,poseidon);ctx.warEntityById.set(2,enemy);ctx.warEntityById.set(3,splash);
assert(ctx.startWaterAttack(poseidon,'normal',enemy));
let p=poseidon.pendingWaterAttack;
clock=p.impactAt;ctx.updateWaterAttackState(poseidon,clock,.016);
assert.equal(enemy.hp,925,'Poseidon normal should deal 75 once');
assert.equal(splash.hp,925,'normal hit should affect the surrounding area');
assert.equal(ally.hp,1000,'normal area must not damage allies');
ctx.updateWaterAttackState(poseidon,clock,.016);
assert.equal(enemy.hp,925,'normal impact duplicated');
assert.equal(splash.hp,925,'normal splash duplicated');
clock=p.endAt+1;ctx.updateWaterAttackState(poseidon,clock,.016);
assert.equal(poseidon.poseidonNormalCount,1);
poseidon.attackCooldown=0;
clock+=100;
assert(ctx.startWaterAttack(poseidon,'wave',enemy));
p=poseidon.pendingWaterAttack;
assert.equal(p.waveStartAt-p.startedAt,1000);
assert.equal(p.endAt-p.waveStartAt,3040);
clock=p.waveStartAt;
enemy.x=ctx.waterWavePosition(p,clock).x;enemy.y=100;
ctx.updateWaterAttackState(poseidon,clock,.016);
assert.equal(enemy.hp,900,'wave first 25 damage');
assert(enemy.waveDraggedUntil>clock,'wave should drag the target');
clock+=1000;
ctx.updateWaterAttackState(poseidon,clock,.016);
assert.equal(enemy.hp,875,'wave second one-second tick');
clock=p.endAt+1;ctx.updateWaterAttackState(poseidon,clock,.016);
assert.equal(poseidon.pendingWaterAttack,null);
poseidon.attackCooldown=0;clock+=100;
enemy.x=150;enemy.y=100;
assert(ctx.startWaterAttack(poseidon,'summon',enemy));
p=poseidon.pendingWaterAttack;
clock=p.summonAt;ctx.updateWaterAttackState(poseidon,clock,.016);
assert.equal(state.entities.filter(e=>e.type==='seahorse'&&e.waterSummonerId===poseidon.id).length,3);
ctx.updateWaterAttackState(poseidon,clock,.016);
assert.equal(state.entities.filter(e=>e.type==='seahorse'&&e.waterSummonerId===poseidon.id).length,3,'summons duplicated');
clock=p.endAt+1;ctx.updateWaterAttackState(poseidon,clock,.016);
poseidon.attackCooldown=0;
assert(ctx.startWaterAttack(poseidon,'summon',enemy),'previous summons must not block a new cast');
p=poseidon.pendingWaterAttack;clock=p.summonAt;ctx.updateWaterAttackState(poseidon,clock,.016);
assert.equal(state.entities.filter(e=>e.alive&&e.type==='seahorse'&&e.waterSummonerId===poseidon.id).length,3,'second cast must not accumulate');
assert(state.entities.filter(e=>e.alive&&e.waterSummonerId===poseidon.id).every(e=>e.shield===0&&e.maxShield===0),'summoned seahorses have no shield');
clock=p.endAt+1;ctx.updateWaterAttackState(poseidon,clock,.016);
poseidon.attackCooldown=0;
const firstSummons=state.entities.filter(e=>e.alive&&e.waterSummonerId===poseidon.id);
firstSummons[0].alive=false;firstSummons[1].alive=false;
assert(ctx.startWaterAttack(poseidon,'summon',enemy),'summon special should refill losses');
p=poseidon.pendingWaterAttack;clock=p.summonAt;ctx.updateWaterAttackState(poseidon,clock,.016);
assert.equal(state.entities.filter(e=>e.alive&&e.type==='seahorse'&&e.waterSummonerId===poseidon.id).length,3,'refills two losses without exceeding three');
let horse={id:3,type:'seahorse',team:'water',color:'#0af',x:110,y:100,damage:25,alive:true,attackCooldown:0,knockTime:0};
state.entities.push(horse);ctx.warEntityById.set(3,horse);
clock+=100;enemy.x=155;enemy.y=100;
assert(ctx.startWaterAttack(horse,'normal',enemy));
p=horse.pendingWaterAttack;
assert.equal(p.duration,1050,'new Seahorse attack duration');
assert.equal(p.hit1At-p.startedAt,300,'first Seahorse hit');
assert.equal(p.hit2At-p.startedAt,730,'second Seahorse hit');
const oldHp=enemy.hp;
clock=p.hit1At;ctx.updateWaterAttackState(horse,clock,.016);
clock=p.hit2At;ctx.updateWaterAttackState(horse,clock,.016);
assert.equal(oldHp-enemy.hp,25,'Seahorse should deal two 12.5-damage hits');
ctx.updateWaterAttackState(horse,clock,.016);
assert.equal(oldHp-enemy.hp,25,'Seahorse attack duplicated');
// Full AI cycle: three ranged casts, six melee attacks, three summons, retreat,
// then three ranged casts again.
const boss={id:20,type:'poseidon',team:'water',color:'#0af',x:400,y:400,damage:75,speed:112,
 alive:true,attackCooldown:0,knockTime:0,poseidonPhase:'wave',poseidonWaveCount:0,poseidonWaveGoal:3,
 poseidonNormalCount:0,poseidonSpecialIndex:0,poseidonRetreatStartedAt:0};
const foe={id:21,type:'warrior',team:'enemy',x:700,y:400,r:30,alive:true,hp:2000,shield:0};
state.entities.push(boss,foe);
ctx.warEntityById.set(20,boss);ctx.warEntityById.set(21,foe);
ctx.nearestEngageableCandidate=()=>foe;
function finishBossCast(){
 const cast=boss.pendingWaterAttack;assert(cast,'expected active attack');
 clock=cast.endAt+1;ctx.updateWaterAttackState(boss,clock,.016);
 boss.attackCooldown=0;clock+=10;
}
for(let n=1;n<=3;n++){
 ctx.aiFightPoseidon(boss,.016);
 assert.equal(boss.pendingWaterAttack?.kind,'wave','ranged cast '+n);
 finishBossCast();
 assert.equal(boss.poseidonWaveCount,n);
 assert.equal(boss.poseidonPhase,n===3?'melee':'wave');
}
foe.x=boss.x+100;foe.y=boss.y;
for(let n=1;n<=6;n++){
 ctx.aiFightPoseidon(boss,.016);
 assert.equal(boss.pendingWaterAttack?.kind,'normal','normal hit '+n);
 finishBossCast();
 assert.equal(boss.poseidonNormalCount,n);
 assert.equal(boss.poseidonPhase,n===6?'summon':'melee');
}
ctx.aiFightPoseidon(boss,.016);
assert.equal(boss.pendingWaterAttack?.kind,'summon','special summon follows six melee hits');
p=boss.pendingWaterAttack;clock=p.summonAt;ctx.updateWaterAttackState(boss,clock,.016);
assert.equal(state.entities.filter(e=>e.type==='seahorse'&&e.waterSummonerId===boss.id).length,3);
finishBossCast();
assert.equal(boss.poseidonPhase,'retreat');
assert.equal(boss.poseidonWaveGoal,3,'all subsequent ranged phases use three waves');
const beforeRetreat=boss.x;
ctx.aiFightPoseidon(boss,.1);
assert(boss.x<beforeRetreat,'Poseidon should move away before ranged attack');
assert.equal(boss.pendingWaterAttack,null,'retreat must precede the next wave');
clock+=1801;
for(let n=1;n<=3;n++){
 if(n>1){foe.x=boss.x+300;foe.y=boss.y}
 ctx.aiFightPoseidon(boss,.016);
 assert.equal(boss.pendingWaterAttack?.kind,'wave','next cycle ranged '+n);
 finishBossCast();
 assert.equal(boss.poseidonPhase,n===3?'melee':'wave');
}
assert.equal(boss.poseidonNormalCount,0,'normal hit count resets after ranged phase');
// Clã reservado pelo humano; os dois NPCs devem ocupar os outros clãs.
const clanStart=js.indexOf('function prepareWarClanAssignments(');
const clanEnd=js.indexOf('function renderClanSelection(',clanStart);
assert(clanStart>0&&clanEnd>clanStart,'clan assignment code missing');
for(const humanClan of ['warriors','egypt','water']){
 const clanState={mode:'war',players:[
   {id:'human',human:true,clan:humanClan},
   {id:'npc1',human:false,clan:'warriors'},
   {id:'npc2',human:false,clan:'warriors'}
 ]};
 const clanCtx=vm.createContext({state:clanState,normalizeClan:c=>['egypt','water'].includes(c)?c:'warriors'});
 vm.runInContext(js.slice(clanStart,clanEnd),clanCtx);
 clanCtx.prepareWarClanAssignments();
 assert.equal(new Set(clanState.players.map(p=>p.clan)).size,3,'three unique clans for '+humanClan);
 assert(clanState.players.slice(1).every(p=>p.clanChosen&&p.clanConfirmed));
 clanState.players[0].clan=humanClan==='water'?'egypt':'water';
 clanCtx.prepareWarClanAssignments();
 assert.equal(new Set(clanState.players.map(p=>p.clan)).size,3,'reassignment when human changes clan');
}
const enemiesStart=js.indexOf('function enemyWarComposition(');
const enemiesEnd=js.indexOf('function affordableBotWarTypes(',enemiesStart);
const enemiesCtx=vm.createContext({state:{entities:[
 {alive:true,team:'a',type:'seahorse'},{alive:true,team:'b',type:'poseidon'},
 {alive:true,team:'b',type:'seahorse'},{alive:false,team:'b',type:'poseidon'}] }});
vm.runInContext(js.slice(enemiesStart,enemiesEnd),enemiesCtx);
const composition=enemiesCtx.enemyWarComposition('a');
assert.equal(composition.poseidon,1,'bots count enemy Poseidon');
assert.equal(composition.seahorse,1,'bots count enemy Seahorse');
// Real spawn: purchased horses keep shield; Poseidon summons have zero shield.
const horseSpawnStart=js.indexOf('function spawnSeahorse(');
const horseSpawnEnd=js.indexOf('function spawnMage(',horseSpawnStart);
const horseState={mode:'war',entities:[]};
const horseCtx=vm.createContext({state:horseState,entityBase:(type,x,y,team,color)=>({type,x,y,team,color,speed:195}),
 WAR_TROOP_SPEED_MULTIPLIER:.5,WAR_BASIC_WARRIOR_SPEED_MULTIPLIER:.92});
vm.runInContext(js.slice(horseSpawnStart,horseSpawnEnd),horseCtx);
const bought=horseCtx.spawnSeahorse(1,2,'a','blue');
const summoned=horseCtx.spawnSeahorse(1,2,'a','blue',123);
assert.equal(bought.shield,100);assert.equal(bought.maxShield,100);
assert.equal(summoned.shield,0);assert.equal(summoned.maxShield,0);
assert.equal(bought.damage,25);assert.equal(summoned.damage,25);
// Regression: rendering during the preparation phase must not stop the main RAF loop.
// This function runs even when there are no Poseidon waves on screen.
const waveRenderStart=js.indexOf('function syncWaterWaveEffects(');
const waveRenderEnd=js.indexOf('function syncKingPowerEffects(',waveRenderStart);
assert(waveRenderStart>0&&waveRenderEnd>waveRenderStart,'Water render block not found');
let renderClock=1000;
const renderCtx=vm.createContext({
 entityCameraLayer:{appendChild(){}},
 waterWaveActiveIds:new Set(),
 renderFrameNow:renderClock,performance:{now:()=>renderClock},
 renderWaterEffectEntities:[],waterWaveNodes:new Map(),
 releaseGifObjectUrl:()=>{}
});
vm.runInContext(js.slice(waveRenderStart,waveRenderEnd),renderCtx);
assert.doesNotThrow(()=>renderCtx.syncWaterWaveEffects(0,0,1,1000,600));
renderClock+=16;renderCtx.renderFrameNow=renderClock;
assert.doesNotThrow(()=>renderCtx.syncWaterWaveEffects(0,0,1,1000,600));
console.log('Water clan assets, JS syntax and functional combat smoke: PASS');
