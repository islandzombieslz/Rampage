const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const html=fs.readFileSync('index.html','utf8');
const js=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].at(-1)?.[1];
assert(js,'main game script');
new vm.Script(js,{filename:'Rampage inline script'});
function section(start,end){
 const a=js.indexOf(start),b=js.indexOf(end,a+start.length);
 assert(a>=0&&b>a,'missing section: '+start);
 return js.slice(a,b);
}
const levels=vm.createContext({Math});
vm.runInContext(section('function xpRequiredForLevel(', 'function renderAccountXP('),levels);
assert.equal(levels.xpRequiredForLevel(1),500);
assert.equal(levels.xpRequiredForLevel(2),950);
assert.equal(levels.xpRequiredForLevel(15),6800);
assert.equal(levels.xpRequiredForLevel(16),7650);
assert.equal(levels.xpRequiredForLevel(50),36550);
assert.equal(levels.xpRequiredForLevel(51),37550);
assert.equal(levels.xpLevelProgress(500).level,2);
assert.equal(levels.xpLevelProgress(500).xp,0);
assert.equal(levels.xpLevelProgress(1450).level,3);
assert.equal(levels.xpLevelProgress(1450).xp,0);

const state={mode:'war',phase:'combat',players:[
 {id:'u1',name:'Alice',clan:'warriors',human:true},
 {id:'u2',name:'Beto',clan:'water',human:true},
 {id:'npc1',name:'NPC 1',clan:'egypt',human:false}
],round:1,matchStats:{}};
const game=vm.createContext({Math,Date,state,clearWarGoalToasts:()=>{},
 clamp:(value,low,high)=>Math.max(low,Math.min(high,value)),
 clanLabel:c=>c==='egypt'?'Egito':c==='water'?'Água':'Guerreiros'});
vm.runInContext(section('function beginMatchTracking()', 'function localPlayer()'),game);
game.beginMatchTracking();
assert.match(state.matchId,/^m_[a-z0-9_]{12,70}$/i);
game.recordMatchDamage({team:'u1'},1200);
game.matchStatsFor('u1').wonRounds=1;
game.matchStatsFor('u1').victorySeconds=20;
game.matchStatsFor('u1').victoryTimeLimit=120;
let result=game.makeMatchResult('u1');
assert.equal(result.pvp,true);
assert(result.awards.u1>=200&&result.awards.u1<=400);
assert.equal(result.awards.u2,50);
assert.equal(game.matchResultMessage(result,'u2'),'A partida acabou, Alice foi o vencedor!');
result=game.makeMatchResult(null);
assert.equal(result.awards.u1,50);
assert.equal(game.matchResultMessage(result,'u1'),'A partida terminou em empate.');
state.players=[state.players[0],state.players[2]];
game.beginMatchTracking();
result=game.makeMatchResult('npc1');
assert.equal(result.awards.u1,50);
assert.equal(game.matchResultMessage(result,'u1'),'Você foi derrotado, clã: Egito venceu!');
result=game.makeMatchResult('u1');
assert(result.awards.u1>=100&&result.awards.u1<=200);
assert.equal(game.matchResultMessage(result,'u1'),'Você venceu!');
state.mode='pve';game.beginMatchTracking();
result=game.makeMatchResult('players');
assert(result.awards.u1>=100&&result.awards.u1<=200);
assert.equal(game.matchResultMessage(result,'u1'),'Você venceu!');
result=game.makeMatchResult('enemy');
assert.equal(result.awards.u1,50);

const goalState={mode:'war',phase:'combat',round:1,players:[{id:'u1',bonusGems:0}],warGoalSerial:0,warGoalEvents:[]};
const goals=vm.createContext({Math,Object,state:goalState,
 $:()=>null,localWarTeamId:()=>null});
vm.runInContext(section('const WAR_GOALS=Object.freeze(', 'const difficultyConfig='),goals);
vm.runInContext(section('function showWarGoalToast(', "$('#shopButton').onclick="),goals);
goalState.players[0].warGoals=goals.freshWarGoals();
goals.addWarGoalProgress('u1','damage',100);
goals.addWarGoalProgress('u1','damage',100);
goals.addWarGoalProgress('u1','damageHigh',500);
goals.addWarGoalProgress('u1','eliminations',3);
goals.addWarGoalProgress('u1','shields',2);
assert.equal(goalState.players[0].bonusGems,50+90+65+45);
assert.equal(goalState.warGoalEvents.length,4);
assert.equal(goalState.warGoalEvents[0].serial,1);
assert.equal(goalState.warGoalEvents.at(-1).serial,4);
assert(html.includes("F.runTransaction(F.ref(F.firebaseDb,'profiles/'+uid),current=>"),'Firebase atomic XP claim');
assert(html.includes("'profiles/'+uid"),'independent profile location');
assert(html.includes("ap.settled.add(id)"),'prevent repeat claims in cloud');
assert(html.includes("id==='gameScreen'"),'XP HUD not displayed during matches');
assert(html.includes('id="warGoalToasts"'),'goal toast container');
const screens=['menuScreen','modeScreen','joinScreen','gameScreen'].map(id=>({
 id,style:{display:'none'},classList:{classes:new Set(),add(value){this.classes.add(value)},remove(value){this.classes.delete(value)},contains(value){return this.classes.has(value)}}
}));
const xpHud={hidden:true};
const screenCtx=vm.createContext({
 $:selector=>selector==='#accountXpHud'?xpHud:screens.find(item=>selector==='#'+item.id),
 [String.fromCharCode(36,36)]:selector=>selector==='.screen'?screens:[],
 window:{FirebaseBridge:{firebaseAuth:{currentUser:{uid:'test-user'}}}}
});
vm.runInContext(section('function screen(id){','const MENU_SCREEN_IDS='),screenCtx);
screenCtx.screen('modeScreen');
assert.equal(screens.filter(item=>item.style.display==='flex').length,1,'one menu must be visible');
assert.equal(screens.find(item=>item.id==='modeScreen').style.display,'flex','create match menu opens');
assert.equal(xpHud.hidden,false,'level indicator visible in menus');
screenCtx.screen('joinScreen');
assert.equal(screens.filter(item=>item.style.display==='flex').length,1,'previous menu must close');
assert.equal(screens.find(item=>item.id==='joinScreen').style.display,'flex','join code menu opens');
screenCtx.screen('gameScreen');
assert.equal(xpHud.hidden,true,'level indicator hidden during match');
console.log('Level thresholds, match rewards, goals and menu navigation: PASS');

async function testCloudOnlyAccountProgress(){
 const uid='xp-user',storage=new Map();
 const localStorage={
   getItem:k=>storage.get(k)||null,
   setItem:(k,v)=>storage.set(k,String(v)),
   removeItem:k=>storage.delete(k)
 };
 let permitted=false,connected=true,profile=null,readError=null,connectionCallback=null;
 const F={
   firebaseAuth:{currentUser:{uid}},firebaseDb:{},
   ref:(_db,path)=>path,
   onValue:(path,ok,fail)=>{
     if(path==='.info/connected'){connectionCallback=ok;ok({val:()=>connected});return ()=>{}}
     if(!permitted)fail(Object.assign(new Error('PERMISSION_DENIED'),{code:'PERMISSION_DENIED'}));
     else ok({val:()=>profile});
     return ()=>{};
   },
   runTransaction:async (_path,fn,options)=>{
     assert.equal(options.applyLocally,false,'no optimistic Firebase transactions');
     if(!permitted)throw Object.assign(new Error('PERMISSION_DENIED'),{code:'PERMISSION_DENIED'});
     if(!connected)throw Object.assign(new Error('network disconnected'),{code:'network-error'});
     const next=fn(profile);
     if(next!==undefined)profile=next;
     return {committed:next!==undefined,snapshot:{val:()=>profile}};
   }
 };
 const mockNodes={};
 for(const id of ['accountXpHud','accountXpFill','accountXpLevel','accountXpText','accountXpSync','accountXpReward','accountStatus'])
   mockNodes['#'+id]={style:{},dataset:{},hidden:false,textContent:'',classList:{add(){},remove(){}}};
 mockNodes['#gameScreen']={style:{display:'none'}};
 const ctx=vm.createContext({
   Math,Object,Date,Number,String,JSON,localStorage,console,
   window:{addEventListener(){},FirebaseBridge:{firebaseAuth:F.firebaseAuth}},
   document:{addEventListener(){},hidden:false},
   $:selector=>mockNodes[selector],
   setTimeout:()=>{},requestAnimationFrame:fn=>fn(),
   NetworkAdapter:{localPlayerId:uid,waitFirebase:async()=>F}
 });
 vm.runInContext(section('const accountProgress={','function beginMatchTracking(){'),ctx);
 const ap=()=>vm.runInContext('accountProgress',ctx);
 const tick=()=>new Promise(resolve=>setImmediate(resolve));
 ctx.watchAccountXP({uid});
 await tick();await tick();
 assert.equal(ap().status,'error','denied Firebase is shown, not masked as local XP');
 assert.equal(ap().totalXp,null,'no local XP fallback');
 assert.match(mockNodes['#accountXpSync'].textContent,/regras do Firebase/i);
 assert.equal(mockNodes['#accountXpHud'].hidden,false,'HUD visible on initial menu');
 assert.equal(mockNodes['#accountXpLevel'].textContent,'Nível —');

 permitted=true;connected=false;connectionCallback({val:()=>false});
 connected=true;connectionCallback({val:()=>true});
 await tick();await tick();
 assert.equal(ap().status,'ready','profile read+write verification succeeds');
 assert.equal(profile.totalXp,0);
 assert.equal(mockNodes['#accountXpLevel'].textContent,'Nível 1');

 const first={id:'m_abcdefghijklmnop',mode:'war',winnerId:uid,awards:{[uid]:150}};
 ctx.mockResult=first;
 assert.equal(await vm.runInContext('claimMatchXP(mockResult)',ctx),true);
 assert.equal(profile.totalXp,150,'XP committed to profile first');
 assert.equal(ap().totalXp,150);
 assert.equal(mockNodes['#accountXpText'].textContent,'150 / 500 XP');
 assert.equal(await vm.runInContext('claimMatchXP(mockResult)',ctx),true);
 assert.equal(profile.totalXp,150,'repeated result cannot award a second time');
 assert.equal(storage.size,0,'new rewards never written to localStorage');

 permitted=false;
 const failed={id:'m_ponmlkjihgfedcba',mode:'war',winnerId:uid,awards:{[uid]:175}};
 ctx.mockResult=failed;
 assert.equal(await vm.runInContext('claimMatchXP(mockResult)',ctx),false);
 assert.equal(profile.totalXp,150,'denied write must never pretend it saved XP');
 assert.equal(ap().pending.has(failed.id),true,'result held in memory only');
 assert.equal(storage.size,0,'no local XP fallback after error');
 permitted=true;connected=false;connectionCallback({val:()=>false});
 connected=true;connectionCallback({val:()=>true});
 await tick();await tick();await tick();
 assert.equal(profile.totalXp,325,'retry saves previously failed match to Firebase');
 assert.equal(ap().pending.size,0);
 assert.equal(mockNodes['#accountXpText'].textContent,'325 / 500 XP');

 // Old-version pending receipts migrate only after the Firebase profile is reachable.
 const old={id:'m_qwertyuiopasdfgh',mode:'war',winnerId:uid,awards:{[uid]:200}};
 storage.set('rampageXpPendingV1:'+uid,JSON.stringify(old));
 connected=false;connectionCallback({val:()=>false});
 connected=true;connectionCallback({val:()=>true});
 await tick();await tick();await tick();
 assert.equal(profile.totalXp,525,'old pending match is migrated once');
 assert.equal(storage.has('rampageXpPendingV1:'+uid),false);
 assert.equal(mockNodes['#accountXpLevel'].textContent,'Nível 2');
 assert.equal(mockNodes['#accountXpText'].textContent,'25 / 950 XP');

 mockNodes['#gameScreen'].style.display='flex';
 ctx.refreshAccountXP();
 assert.equal(mockNodes['#accountXpHud'].hidden,true,'hide HUD only in visible game');
 mockNodes['#gameScreen'].style.display='none';
 ctx.refreshAccountXP();
 assert.equal(mockNodes['#accountXpHud'].hidden,false);
 console.log('Cloud-only XP: denied rules, verified profile, atomic reward, retries, legacy import and HUD: PASS');
}
testCloudOnlyAccountProgress().catch(err=>{console.error(err);process.exitCode=1});
