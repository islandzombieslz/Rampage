const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('index.html','utf8'),shared=fs.readFileSync('assets/history/rules.js','utf8');
const geometryCtx={window:{}};vm.runInNewContext(shared,geometryCtx);vm.runInNewContext(fs.readFileSync('assets/history/map-config.js','utf8'),geometryCtx);
const rules=geometryCtx.RampageHistoryRules,map=geometryCtx.window.RAMPAGE_HISTORY_MAP;
const workerSource=fs.readFileSync('history-server/src/index.js','utf8').replace(/^import .*;\n/gm,'').replace('export default','const workerDefault=').replace('export class HistoryRoom','class HistoryRoom');
let clock=10000;
const worker=vm.createContext({DurableObject:class{},Date:{now:()=>clock},console});
vm.runInContext(shared+'\n'+fs.readFileSync('history-server/src/map.js','utf8').replaceAll('export const','const')+'\n'+workerSource+'\nglobalThis.Room=HistoryRoom;',worker);
function cloud(){const r=Object.create(worker.Room.prototype);r.room=r.createRoom();r.broadcast=()=>{};r.projectileSeq=0;return r;}
const r=cloud();r.updateSpawnEvents(clock);
const alive=()=>r.room.dragons.filter(e=>e.alive);
assert.equal(alive().length,13);
for(let i=0;i<20;i++)r.updateSpawnEvents(clock+=60000);
assert.equal(alive().length,13,'endless waves must not accumulate living troops');
const killed=alive().find(e=>e.type==='dragon'&&e.historySpawnEventId==='event2');killed.alive=false;
const killedAnubis=alive().find(e=>e.type==='anubis');killedAnubis.alive=false;
r.updateSpawnEvents(clock+=60000);assert.equal(alive().length,13,'only missing types are replaced');
assert.equal(alive().filter(e=>e.type==='dragon'&&e.historySpawnEventId==='event2').length,3);
assert.equal(alive().filter(e=>e.type==='anubis'&&e.historySpawnEventId==='event6').length,2);
const free={id:'free',x:600,y:1400,troops:{naja:2},limitAlive:false,intervalMs:1000};
r.spawnEditorWave(free,clock);r.spawnEditorWave(free,clock);assert.equal(alive().filter(e=>e.historySpawnEventId==='free').length,4,'disabled limit allows explicit free waves');
const finite=vm.runInContext('HISTORY_MAP_EVENTS.find(e=>e.id==="event2")',worker),oldMode=finite.spawnMode;
finite.spawnMode='finite';const finiteRoom=cloud();finiteRoom.updateSpawnEvents(clock);finiteRoom.room.dragons.forEach(e=>e.alive=false);finiteRoom.updateSpawnEvents(clock+60000);
assert.equal(finiteRoom.room.dragons.filter(e=>e.alive&&e.historySpawnEventId==='event2').length,0,'finite waves must stop after their budget');finite.spawnMode=oldMode;
const local=vm.createContext({Date:{now:()=>clock},performance:{now:()=>clock},console,
 state:{historyActive:true,historyLocal:true,historyDoorState:{},historyObjectState:{},world:{w:3200,h:2200},entities:[],players:[{id:'me'}],dragonProjectiles:[]},
 historyMapData:()=>map,historyNavigationMap:null,historyNavigationCache:null,clamp:(v,a,b)=>Math.max(a,Math.min(b,v)),
 PVP_ENEMY_HEROES:Object.fromEntries(['naja','poseidon','anubis','golem','dragon','seahorse'].map(type=>[type,{type}])),
 beginDragonTakeoff:()=>{},flash:()=>{},warEntityById:new Map()});
vm.runInContext(shared,local);
const functionSource=name=>{
 const a=html.indexOf('function '+name+'(');assert(a>=0,name);
 const lineStart=html.lastIndexOf('\n',a)+1,indent=html.slice(lineStart,a),lineEnd=html.indexOf('\n',a);
 if(html.slice(a,lineEnd).trim().endsWith('}'))return html.slice(a,lineEnd);
 return html.slice(a,html.indexOf('\n'+indent+'}',lineEnd)+indent.length+2);
};
for(const name of ['historyMapEvents','historyNavigator','historyLineOfSight','historyLocalSpawnPoint','historyInitialObjectState','historyUpdateObjects','historyHitMapObjects','updateDragonProjectiles'])vm.runInContext(functionSource(name),local);
local.pvpBaseEntity=(hero,x,y,team)=>{const e={id:local.state.entities.length+1,type:hero.type,x,y,team,alive:true,r:30};local.state.entities.push(e);return e;};
const a=html.indexOf('const HISTORY_LOCAL_ENEMY_STATS='),b=html.indexOf('function renderHistoryServers',a);
vm.runInContext(html.slice(a,b)+'\nglobalThis.adapter=HistoryLocalAdapter;',local);
for(let i=0;i<20;i++)local.adapter.updateSpawns(clock+=60000);
assert.equal(local.state.entities.filter(e=>e.alive).length,13,'local host enforces the same cap');
local.state.entities.find(e=>e.type==='anubis').alive=false;local.adapter.updateSpawns(clock+=60000);
assert.equal(local.state.entities.filter(e=>e.alive&&e.type==='anubis').length,2);
// Navigate a wall and a U-shaped enclosure: no teleporting, corner clipping or lost leash.
function walk(map,start,goal,area){
 const nav=rules.createNavigator(map),e={...start,historyLeashArea:area};let reached=false,detour=false;
 for(let i=0;i<700;i++){
   const old={...e},v=nav.direction(e,goal,16,{},i*33);e.x+=v.x*7;e.y+=v.y*7;
   assert.equal(rules.firstWallHit(map,{},old.x,old.y,e.x,e.y,16),null,'route crossed an obstacle');
   if(area)assert(e.x>=area.x+16&&e.x<=area.x+area.w-16&&e.y>=area.y+16&&e.y<=area.y+area.h-16);
   detour ||= Math.abs(e.y-start.y)>70;
   if(Math.hypot(e.x-goal.x,e.y-goal.y)<9){reached=true;break;}
 }
 assert(reached,'NPC must reach the target around the obstacle');return detour;
}
assert(walk({width:640,height:480,colliders:[[160,80,32,230]],doors:[]},{x:80,y:200},{x:320,y:200},{x:0,y:0,w:640,h:480}));
walk({width:640,height:480,colliders:[[160,64,32,250],[440,64,32,250],[160,64,312,30]],doors:[]},{x:300,y:200},{x:300,y:32});
const doorMap={width:480,height:320,colliders:[],doors:[{id:'d',x:220,y:0,w:32,h:320,closedCollision:true,openCollision:false}]};
const nav=rules.createNavigator(doorMap),npc={x:100,y:160},goal={x:380,y:160};
assert.equal(nav.direction(npc,goal,16,{},0).x,0,'closed sealed door has no route');
assert(nav.direction(npc,goal,16,{d:{open:true}},1).x>0,'opening a door immediately invalidates the cached route');
assert.equal(rules.firstWallHit(doorMap,{},100,160,380,160,8)!==null,true);
assert.equal(rules.firstWallHit(doorMap,{d:{open:true}},100,160,380,160,8),null);
// Swept tests travel through the full thickness in a single update.
function projectileChecks(room,kind){
 const events=[];room.applyDamage=(_kind,_target,amount)=>events.push(amount);room.armKnockback=()=>null;room.igniteBurn=()=>events.push('burn');
 room.room.players={target:{id:'target',x:340,y:1750,alive:true,hp:350}};
 room.room.projectiles=[{id:'test',kind,x:170,y:1750,vx:1000,vy:0,damage:kind==='anubis'?20:10,burn:kind==='dragon',expireAt:clock+10000}];
 room.updateProjectiles(.2,clock);assert.equal(room.room.projectiles.length,0);assert.equal(events.length,0,'wall must win before damage behind it');
 room.room.players.target.x=180;room.room.projectiles=[{id:'front',kind,x:170,y:1750,vx:1000,vy:0,damage:kind==='anubis'?20:10,burn:kind==='dragon',expireAt:clock+10000}];
 room.updateProjectiles(.2,clock);assert.equal(events[0],kind==='anubis'?20:10,'a target hit before the wall still takes damage');
 assert.equal(events.includes('burn'),kind==='dragon');
}
for(const kind of ['dragon','anubis'])projectileChecks(cloud(),kind);
for(const kind of ['dragon','anubis']){
 const target={id:'t',team:'player',x:340,y:1750,alive:true,r:30};const hits=[];
 local.state.entities=[target];local.state.dragonProjectiles=[{id:'p',team:'enemy',kind,x:170,y:1750,vx:1000,vy:0,damage:20,burn:false,expireAt:clock+10000}];
 local.applyCombatHit=()=>hits.push(1);local.igniteDragonBurn=()=>{};local.updateDragonProjectiles(.2,new Map());
 assert.equal(local.state.dragonProjectiles.length,0);assert.equal(hits.length,0,'local projectile cannot damage through a wall');
}
const aimRoom=cloud();assert.equal(aimRoom.launchDragonFireball({alive:true,flightState:'flying',x:170,y:1750},{alive:true,x:340,y:1750},clock),false,'Cloudflare cannot aim a shot behind a wall');
vm.runInContext(functionSource('launchAnubisProjectile'),local);vm.runInContext(functionSource('launchDragonFireball'),local);
assert.equal(local.launchAnubisProjectile({alive:true,type:'anubis',x:170,y:1750},{alive:true,x:340,y:1750}),false);
assert.equal(local.launchDragonFireball({alive:true,type:'dragon',dragonFlightState:'flying',x:170,y:1750},{alive:true,x:340,y:1750}),false);
// Editor object rules: one break, one XP award, a full GIF cycle and a 60-second respawn.
const barrel=map.destructibles.find(o=>o.kind==='destructible'),rect=barrel.collisionRect;
const objectsRoom=cloud(),player={id:'me',x:rect[0]-10,y:rect[1]+rect[3]/2,alive:true};objectsRoom.room.doorState.obj218.open=true;
objectsRoom.hitMapObjects(player,40,20,clock);assert.equal(player.historyObjectXP,25);
objectsRoom.hitMapObjects(player,40,20,clock);assert.equal(player.historyObjectXP,25,'a broken barrel cannot reward repeated hits');
objectsRoom.updateObjects(clock+59999);assert(objectsRoom.room.objectState[barrel.id].broken);
objectsRoom.updateObjects(clock+60000);assert.equal(objectsRoom.room.objectState[barrel.id].broken,false);
assert.equal(map.destructibles.length,11);assert.equal(barrel.breakDurationMs,1330);
local.state.historyDoorState={obj218:{open:true}};local.state.historyObjectState=local.historyInitialObjectState();
local.historyHitMapObjects({alive:true,ownerId:'me',x:player.x,y:player.y},40,20,clock);assert.equal(local.state.players[0].historyObjectXP,25);
local.historyUpdateObjects(clock+60000);assert.equal(local.state.historyObjectState[barrel.id].broken,false);
vm.runInContext(functionSource('historyRewardChunks'),local);
const chunks=local.historyRewardChunks({id:'m_history_test',awards:{a:425,b:1075}});
for(const c of chunks)for(const amount of Object.values(c.awards))assert(amount>=50&&amount<=400);
assert.equal(chunks.reduce((sum,c)=>sum+(c.awards.a||0),0),425);
assert.equal(chunks.reduce((sum,c)=>sum+(c.awards.b||0),0),1075);
console.log('HISTORY RULES PASS: capped/replenished spawns, finite/free waves, wall/U routes, door invalidation, swept dragon/Anubis projectiles, aim occlusion, barrel XP/GIF/respawn.');
