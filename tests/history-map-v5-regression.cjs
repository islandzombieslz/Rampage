const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const shared=fs.readFileSync('assets/history/rules.js','utf8'),ctx={window:{}};
vm.runInNewContext(shared,ctx);vm.runInNewContext(fs.readFileSync('assets/history/map-config.js','utf8'),ctx);
const map=ctx.window.RAMPAGE_HISTORY_MAP,rules=ctx.RampageHistoryRules,source=JSON.parse(fs.readFileSync('assets/history/editor-project.json','utf8'));
const plain=x=>JSON.parse(JSON.stringify(x));
const server=vm.createContext({});vm.runInContext(fs.readFileSync('history-server/src/map.js','utf8').replaceAll('export const','globalThis.'),server);
for(const [key,value] of [['WORLD',{width:map.width,height:map.height}],['SPAWN',map.spawn],['COLLIDERS',map.colliders],['DOORS',map.doors],['EVENTS',map.events],['OBJECTS',map.destructibles]])assert.deepEqual(plain(server['HISTORY_MAP_'+key]),plain(value),'Cloudflare/client parity '+key);
const rect=o=>{
 const r=o.collisionShape?.rect;
 return o.collisionShape?.mode==='custom'?[o.x+o.w*r.x,o.y+o.h*r.y,o.w*r.w,o.h*r.h]:[o.x,o.y,o.w,o.h];
};
const visible=source.objects.filter(o=>['asset','door','boss'].includes(o.type));
assert.equal(visible.length,map.objects.length);
visible.forEach((o,i)=>{
 assert.deepEqual(plain(map.objects[i].slice(1,5)),[o.x,o.y,o.w,o.h],o.id+' visual coordinates and size');
 const ref=o.type==='boss'?o.boss.moves.idle[0].asset.assetId:o.assetId;
 assert.equal(map.assets[map.objects[i][0]],source.assets[ref],o.id+' editor artwork');
});
const staticObjects=source.objects.filter(o=>o.collision&&o.type!=='door'&&o.type!=='boss'&&!o.interaction?.destructible?.enabled);
assert.deepEqual(plain(map.colliders),staticObjects.map(rect),'exact custom collision coordinates, without rounding');
for(const o of source.objects.filter(o=>o.type==='door')){
 const d=map.doors.find(d=>d.id===o.id);assert.deepEqual(plain(d.collisionRect),rect(o));
 for(const k of ['openWhen','proximity','enemyCount','enemyArea','closedCollision','openCollision','transitionEnabled','transitionMode'])assert.deepEqual(plain(d[k]),o.door[k],o.id+' '+k);
}
for(const e of source.events){const imported=map.events.find(x=>x.id===e.id);for(const k of Object.keys(e))assert.deepEqual(plain(imported[k]),e[k],e.id+' '+k);}
for(const url of map.assets)assert(fs.existsSync(url),url);
assert.equal(map.destructibles.filter(o=>o.kind==='destructible').length,10);
const boss=map.bosses[0];assert.equal(boss.hp,3000);assert.equal(boss.shield,1500);
assert.equal(boss.moves.idle.length,1);assert.equal(boss.moves.attack.length+boss.moves.special.length+boss.moves.power.length,0,'no invented boss attacks');
const objects=rules.initialObjects(map),doors=Object.fromEntries(map.doors.map(d=>[d.id,{open:true}]));
const r=boss.collisionRect,player={id:'me',x:r[0]+r[2]/2,y:r[1]-40};
assert(rules.hitObject(map,boss,objects[boss.id],player,100,60,doors,objects,10000),'own collision cannot block a melee strike');
assert.equal(objects[boss.id].shield,1400);assert.equal(objects[boss.id].hp,3000);
assert(rules.hitObject(map,boss,objects[boss.id],player,1400,60,doors,objects,11000));
assert.equal(objects[boss.id].shield,0);assert.equal(objects[boss.id].hp,3000);
assert(rules.hitObject(map,boss,objects[boss.id],player,70,60,doors,objects,12000,780));
assert.equal(rules.hitObject(map,boss,objects[boss.id],player,70,60,doors,objects,12033,780),false,'special cannot damage the boss on every frame');
assert.equal(objects[boss.id].hp,2930);
assert(rules.hitObject(map,boss,objects[boss.id],player,3000,60,doors,objects,13000));
assert(objects[boss.id].broken);assert.equal(objects[boss.id].respawnAt,0);
assert.equal(rules.firstWallHit(map,doors,player.x,player.y,player.x,r[1]+20,0,objects),null,'defeated boss releases collision');
const wall={width:320,height:160,colliders:[],doors:[],destructibles:[{id:'crate',kind:'destructible',x:140,y:0,w:40,h:160,collisionRect:[140,0,40,160],collision:true,hp:20,removeCollisionOnBreak:true,respawn:true,respawnSeconds:60}]};
const state=rules.initialObjects(wall),nav=rules.createNavigator(wall),npc={x:60,y:80},goal={x:260,y:80};
assert.equal(nav.direction(npc,goal,16,{},0,state).x,0);
assert.equal(rules.hitObject({...wall,colliders:[[90,0,10,160]]},wall.destructibles[0],state.crate,npc,40,120,{},state,1000),false,'wall blocks object damage');
assert(rules.hitObject(wall,wall.destructibles[0],state.crate,npc,40,120,{},state,1000));
assert.equal(state.crate.respawnAt,61000);assert(nav.direction(npc,goal,16,{},1,state).x>0,'barrel break invalidates cached route immediately');
assert.equal(rules.firstWallHit(wall,{},60,80,260,80,8,state),null);
Object.assign(state.crate,{hp:20,broken:false});
assert.equal(nav.direction(npc,goal,16,{},2,state).x,0,'barrel respawn restores collision and navigation');
const ellipse=[100,100,80,80,'circle'];assert.equal(rules.rectHitTime(100,100,100,100,ellipse),null);assert.equal(rules.rectHitTime(140,140,140,140,ellipse),0);
console.log('MAP V5 PASS: exact editor artwork/geometry/events, cloud/local parity, four combined-condition doors, dynamic collisions, boss shield/HP and no invented attacks.');
