const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const shared=fs.readFileSync('assets/history/rules.js','utf8'),ctx={window:{}};
vm.runInNewContext(shared,ctx);vm.runInNewContext(fs.readFileSync('assets/history/map-config.js','utf8'),ctx);
const map=ctx.window.RAMPAGE_HISTORY_MAP,rules=ctx.RampageHistoryRules,config=map.soldier;
assert.equal(map.id,'history-castle-v9');assert.equal(map.events.filter(e=>e.kind==='sound').length,1);
assert.equal(map.events.filter(e=>e.kind==='enemy_spawn').reduce((n,e)=>n+e.troops.soldier_enemy,0),19);
assert.deepEqual([config.hp,config.shield,config.damage],[100,50,10]);
// Every source frame survives the display-size conversion, with identical delays.
function gifTimeline(file){const g=fs.readFileSync(file);let p=13,d=100,delays=[];if(g[10]&128)p+=3*(1<<((g[10]&7)+1));function blocks(){while(p<g.length){const n=g[p++];if(!n)return;p+=n}throw Error('truncated GIF')}
 while(p<g.length){const tag=g[p++];if(tag===59)break;if(tag===33){const label=g[p++];if(label===249){assert.equal(g[p++],4);p++;d=g.readUInt16LE(p)*10;p+=4}else blocks()}else if(tag===44){const packed=g[p+8];p+=9;if(packed&128)p+=3*(1<<((packed&7)+1));p++;blocks();delays.push(d);d=100}else throw Error('GIF block '+tag)}return delays;}
for(const [key,s] of Object.entries(config.sprites)){const original=gifTimeline(s.source),display=gifTimeline(s.src);assert.deepEqual(display,original,key+' complete animation');assert.equal(display.length,s.frames);assert.equal(display.reduce((a,b)=>a+b,0),s.durationMs);}
for(const [w,h] of [[1280,720],[360,780],[2560,1440],[4000,3000]])for(const z of [.1,.5,1,3])for(const x of [-200,0,1600,3200,4000])for(const y of [-200,0,2200,4000]){
 const v=rules.safeCamera(map,w,h,x,y,z,10,-10);assert(v.left>=-1e-6&&v.top>=-1e-6);assert(v.left+w/v.zoom<=map.width+1e-6&&v.top+h/v.zoom<=map.height+1e-6,'camera/shake reveals outside map');
}
const p={x:0,y:0};rules.queuePush(p,{x:90,y:0});assert.equal(p.x,0,'queue must never teleport');rules.stepPush(p,.033,(p,x,y)=>{p.x+=x;p.y+=y});assert(p.x>0&&p.x<20);
for(let i=0;i<20;i++)rules.stepPush(p,.016,(p,x,y)=>{p.x+=x;p.y+=y});assert(Math.abs(p.x-90)<1e-6);
const wall={x:0,y:0};rules.queuePush(wall,{x:90,y:0});for(let i=0;i<40;i++)rules.stepPush(wall,.016,(p,x)=>{if(p.x+x<35)p.x+=x});assert(wall.x<35,'stepwise push cannot tunnel through walls');
const hero={singleUntil:15000,pvpWarriorComboUntil:15000};assert.equal(rules.attackMovement(hero,10000),.45);assert.equal(rules.attackMovement(hero,10000,true),.45);assert.equal(rules.attackMovement(hero,15001),1);
let clock=10000;const worker=vm.createContext({DurableObject:class{},Date:{now:()=>clock},console});
const source=fs.readFileSync('history-server/src/index.js','utf8').replace(/^import .*;\n/gm,'').replace('export default','const workerDefault=').replace('export class HistoryRoom','class HistoryRoom');
vm.runInContext(shared+'\n'+fs.readFileSync('history-server/src/map.js','utf8').replaceAll('export const','const')+'\n'+source+'\nglobalThis.Room=HistoryRoom',worker);
const room=Object.create(worker.Room.prototype);room.room=room.createRoom();room.broadcast=()=>{};
const enemy=room.createEnemy('soldier_enemy',{id:'test',x:600,y:1000},1,0,clock);assert(enemy);
const victim={id:'victim',alive:true,hp:350,shield:100,x:enemy.x+70,y:enemy.y};room.room.players={victim};room.room.dragons=[enemy];
room.updateSoldier(enemy,.016,clock);assert.equal(victim.shield,90);assert.equal(enemy.soldierVariant,1);
for(const fraction of config.hitFractions.slice(1))room.updateSoldier(enemy,.016,clock+Math.ceil(4270*fraction));
assert.equal(victim.shield,50,'five confirmed hits each deal 10, with no extra single attack');
room.updateSoldier(enemy,.016,clock+4270);clock+=4770;room.updateSoldier(enemy,.016,clock);assert.equal(enemy.soldierVariant,2);
room.updateSoldier(enemy,.016,clock+4270);clock+=4770;room.updateSoldier(enemy,.016,clock);assert.equal(enemy.soldierVariant,1,'combo A/B/A alternation');
const comboHero={id:'combo',alive:true,x:600,y:1500,hp:350,shield:50,comboUntil:clock+3000,comboStartedAt:clock,comboRequestUntil:clock+460,comboHitIndex:0,comboSfxIndex:0,singleSerial:0,attackSerial:1,knockUntil:clock+300};
room.applyAction(comboHero,'attack',{});assert(comboHero.comboUntil>clock);assert.equal(comboHero.comboRequestUntil,clock+460,'hit stun cannot prevent combo continuation');
console.log('HISTORY V9 PASS: exact soldier GIF frames, 20-troop cap, A/B five-hit combos, camera bounds including shake, gradual collision-safe push, attack movement scaling and combo continuity.');

// New editor mixer: map scope, boss condition, custom combat radius, one music winner and fades.
const sample={id:'a',kind:'sound',x:50,y:50,area:{x:0,y:0,w:100,h:100},sound:{src:'a.mp3',scope:'map',trigger:'always',mode:'spatial',volume:100,bus:'music',priority:1,playMode:'loop',fadeIn:.2,fadeOut:.5}};
assert.equal(rules.soundMix(sample,{bosses:[]},{},{x:1000,y:1000},[]).volume,1);
const nearby={...sample,sound:{...sample.sound,trigger:'enemies_near',combatRadius:50}};
assert.equal(rules.soundMix(nearby,{bosses:[]},{},{x:0,y:0},[{x:51,y:0,alive:true}]).active,false);
class Media {constructor(){this.paused=true;this.currentTime=0;this.duration=30}addEventListener(){}pause(){this.paused=true}play(){this.paused=false;return Promise.resolve()}removeAttribute(){}load(){}}
ctx.Audio=Media;vm.runInNewContext(fs.readFileSync('assets/history/audio.js','utf8'),ctx);
const high={...sample,id:'b',sound:{...sample.sound,src:'b.mp3',priority:2}};
const mixer=ctx.RampageHistoryAudio.create({events:[sample,high],bosses:[]});mixer.update({x:50,y:50},[],{},1000);mixer.update({x:50,y:50},[],{},1100);
assert.equal(mixer.entries.get('a').want,false);assert.equal(mixer.entries.get('b').want,true);assert.equal(mixer.entries.get('b').audio.volume,.5);
assert.equal(mixer.entries.get('b').audio.paused,false);mixer.suspend();assert(mixer.entries.get('b').audio.paused);
