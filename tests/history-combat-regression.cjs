const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('index.html','utf8');
let clock=10000;const sounds=[],entities=[];
const ctx=vm.createContext({performance:{now:()=>clock},PVP_WARRIOR:{comboContinueMs:460,comboChainMs:950,specialCooldownMs:20000,specialFallbackMs:1800},PVP_BASE:{meleeCooldown:.3},
 pvpIsWarriorHero:e=>e?.type==='warrior',pvpFullGifDuration:(_k,f)=>f,
 pvpNearestEnemy:()=>null,stopLayeredOneShot:()=>{},historyFindEntity:(_k,id)=>entities.find(e=>e.ownerId===id),NetworkAdapter:{attackSeq:0},
 pvpPlayEntitySfxNow:(e,event,serial,key,volume)=>{sounds.push({event,serial,volume,id:e.id});return true;}
});
function load(name){const start=html.indexOf('function '+name+'('),end=html.indexOf('\nfunction ',start+1);assert(start>=0);vm.runInContext(html.slice(start,end),ctx);}
for(const name of ['pvpCancelWarriorCombo','pvpPreviewBasicAttack','pvpPreviewGuestAction','historyServerRemaining','historyWarriorDuration','historyApplyAuthoritativeAction','historyApplyCombatSfx','historyStartLocalWarriorCombo','historyTickLocalWarriorComboVisual','historyPreviewLocalAction','historySyncWarriorCombatSnapshot'])load(name);
const e={id:1,ownerId:'local',type:'warrior',alive:true,controlled:true,attackSerial:0,comboStep:0,pvpWarriorSingleSerial:0};entities.push(e);
assert(ctx.historyPreviewLocalAction(e,'attack'));assert.equal(sounds.length,1);assert.equal(e.pvpWarriorSingleUntil-clock,1430);
assert.equal(ctx.historyPreviewLocalAction(e,'attack'),false,'immediate duplicate input is blocked');
assert.equal(sounds.length,1);
const until=e.pvpWarriorSingleUntil;
ctx.historyApplyAuthoritativeAction(e,{action:'attack',kind:'single',attackSerial:20,singleSerial:1,at:50000});
ctx.historySyncWarriorCombatSnapshot(e,{attackSerial:20,singleSerial:1,singleUntil:51430},clock,50000);
assert.equal(e.attackSerial,1,'ack must not replay sword/slash');assert.equal(e.pvpWarriorSingleUntil,until);
clock+=160;assert(ctx.historyPreviewLocalAction(e,'attack'));const combo=e.pvpWarriorComboSerial,comboUntil=e.pvpWarriorComboUntil;
assert.equal(comboUntil-clock,3130);assert.equal(sounds.length,2);
ctx.historyApplyCombatSfx({uid:'local',event:'warrior-single',serial:50,volume:.38});assert.equal(sounds.length,2,'server must not echo predicted sound');
const singleSerial=e.pvpWarriorSingleSerial;
for(let elapsed=100;elapsed<=3100;elapsed+=100){clock=10160+elapsed;ctx.historyPreviewLocalAction(e,'attack');ctx.historyTickLocalWarriorComboVisual(e,clock);}
assert.equal(e.pvpWarriorComboSerial,combo);assert.equal(e.pvpWarriorSingleSerial,singleSerial,'combo sound must not advance single GIF clock');
assert.deepEqual(sounds.map(s=>s.volume),[1,.38,.52,.38]);
clock=comboUntil;ctx.historyTickLocalWarriorComboVisual(e,clock);assert.equal(e.pvpWarriorComboSerial,combo+1);assert.equal(sounds.length,5);
clock+=461;ctx.historyTickLocalWarriorComboVisual(e,clock);assert.equal(e.pvpWarriorComboUntil,0);assert.equal(sounds.length,5,'release cancels future cues');
const remote={id:2,ownerId:'remote',type:'warrior',alive:true,pvpWarriorSingleSerial:1};entities.push(remote);
for(const serial of [8,8,7,9])ctx.historyApplyCombatSfx({uid:'remote',event:'warrior-single',serial,volume:.52});
assert.equal(sounds.length,7,'duplicate and older server cues are discarded');assert.equal(remote.pvpWarriorSingleSerial,1);
e.pvpSpecialSerial=8;e.historyServerSpecialSerial=3;e.knockTime=0;
assert(ctx.historyPreviewLocalAction(e,'special'));const special=e.pvpSpecialSerial,specialUntil=e.pvpWarriorChargeUntil;
assert.equal(specialUntil-clock,3900);
ctx.historySyncWarriorCombatSnapshot(e,{specialSerial:3,specialActiveUntil:0},clock+50,50000);
assert.equal(e.pvpWarriorChargeUntil,specialUntil,'pre-action snapshot must not cancel prediction');
ctx.historyApplyAuthoritativeAction(e,{action:'special',specialSerial:4,specialActiveUntil:53900,at:50000});
assert.equal(e.pvpSpecialSerial,special,'confirmation must not replay special');
let serverClock=50000;const events=[];
const historyMap=fs.readFileSync('history-server/src/map.js','utf8').replaceAll('export const','const');
const worker=fs.readFileSync('history-server/src/index.js','utf8').replace(/^import .*;\n/gm,'').replace('export default','const workerDefault=').replace('export class HistoryRoom','class HistoryRoom');
const server=vm.createContext({DurableObject:class{},Date:{now:()=>serverClock},console});
vm.runInContext(fs.readFileSync('assets/history/rules.js','utf8')+'\n'+historyMap+'\n'+worker+'\n globalThis.Room=HistoryRoom;',server);
load('pvpParsedGifCycleMs');
for(const [key,file,constant] of [
 ['pvpWarriorAttack','guerreiro-ataque-unico.gif','WARRIOR_SINGLE_VISUAL_MS'],
 ['pvpWarriorCombo','combo-ataque-guerreiro.gif','WARRIOR_COMBO_DURATION_MS'],
 ['pvpWarriorSpecial','especial-guerreiro.gif','WARRIOR_SPECIAL_DURATION_MS']]){
 const buffer=fs.readFileSync('assets/warrior/pvp/'+file);
 const actual=ctx.pvpParsedGifCycleMs(buffer);
 assert.equal(ctx.historyWarriorDuration(key),actual,'History preview must match actual PvP GIF');
 assert.equal(vm.runInContext(constant,server),actual,'Cloudflare must match actual PvP GIF');
}
const room=Object.create(server.Room.prototype);room.room=room.createRoom();room.broadcast=event=>events.push(event);
const player={id:'local',alive:true,attackSerial:1,singleSerial:1};
room.startWarriorCombo(player,serverClock);assert.equal(player.comboUntil-serverClock,3130);
for(let elapsed=100;elapsed<=3100;elapsed+=100){serverClock=50000+elapsed;player.comboRequestUntil=serverClock+460;room.updateWarriorCombo(player,serverClock);}
assert.deepEqual(events.filter(e=>e.type==='combat_sfx').map(e=>e.volume),[.38,.52,.38]);
serverClock=53130;room.updateWarriorCombo(player,serverClock);assert.equal(player.comboSerial,2);
serverClock+=461;room.updateWarriorCombo(player,serverClock);assert.equal(player.comboUntil,0);
assert.equal(events.filter(e=>e.type==='combat_sfx').length,4);
console.log('History combat regression passed: audio, GIF clocks, cancellation, special acknowledgements, server cycles.');
