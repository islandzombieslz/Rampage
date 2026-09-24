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
   const e={id:100+state.entities.length,type:'seahorse',x,y,team,color,waterSummonerId:summonerId,alive:true,hp:150,shield:100};
   state.entities.push(e);return e;
 },
 nearestEngageableCandidate:()=>null
});
vm.runInContext(js.slice(start,end),ctx);
let poseidon={id:1,type:'poseidon',team:'water',color:'#0af',x:100,y:100,damage:60,
 alive:true,attackCooldown:0,knockTime:0,poseidonNormalCount:0,poseidonSpecialIndex:0};
let enemy={id:2,type:'warrior',team:'enemy',x:155,y:100,r:30,alive:true,hp:1000,shield:0};
state.entities.push(poseidon,enemy);
ctx.warEntityById.set(1,poseidon);ctx.warEntityById.set(2,enemy);
assert(ctx.startWaterAttack(poseidon,'normal',enemy));
let p=poseidon.pendingWaterAttack;
clock=p.impactAt;ctx.updateWaterAttackState(poseidon,clock,.016);
assert.equal(enemy.hp,940,'Poseidon normal should deal 60 once');
ctx.updateWaterAttackState(poseidon,clock,.016);
assert.equal(enemy.hp,940,'normal impact duplicated');
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
assert.equal(enemy.hp,915,'wave first 25 damage');
assert(enemy.waveDraggedUntil>clock,'wave should drag the target');
clock+=1000;
ctx.updateWaterAttackState(poseidon,clock,.016);
assert.equal(enemy.hp,890,'wave second one-second tick');
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
assert.equal(ctx.startWaterAttack(poseidon,'summon',enemy),false,'summon cap ignored');
let horse={id:3,type:'seahorse',team:'water',color:'#0af',x:110,y:100,damage:20,alive:true,attackCooldown:0,knockTime:0};
state.entities.push(horse);ctx.warEntityById.set(3,horse);
clock+=100;enemy.x=155;enemy.y=100;
assert(ctx.startWaterAttack(horse,'normal',enemy));
p=horse.pendingWaterAttack;
const oldHp=enemy.hp;
clock=p.hit1At;ctx.updateWaterAttackState(horse,clock,.016);
clock=p.hit2At;ctx.updateWaterAttackState(horse,clock,.016);
assert.equal(oldHp-enemy.hp,20,'Seahorse should deal two 10-damage hits');
ctx.updateWaterAttackState(horse,clock,.016);
assert.equal(oldHp-enemy.hp,20,'Seahorse attack duplicated');
console.log('Water clan assets, JS syntax and functional combat smoke: PASS');
