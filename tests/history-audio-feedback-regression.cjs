const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
class FakeAudio {
 constructor(src){this.src=src;this.paused=true;this.currentTime=0;this.duration=30;this.ended=false;this.calls=0;this.volume=1;}
 addEventListener(){} play(){this.calls++;this.paused=false;return Promise.resolve()} pause(){this.paused=true}
 removeAttribute(){this.src=''} load(){}
}
const ctx={window:{},Audio:FakeAudio};
vm.runInNewContext(fs.readFileSync('assets/history/rules.js','utf8'),ctx);vm.runInNewContext(fs.readFileSync('assets/history/audio.js','utf8'),ctx);
vm.runInNewContext(fs.readFileSync('assets/history/map-config.js','utf8'),ctx);
const map=ctx.window.RAMPAGE_HISTORY_MAP,rules=ctx.RampageHistoryRules,tracks=map.events.filter(e=>e.kind==='sound');
assert.equal(tracks.length,3);
for(const event of tracks){assert(event.sound.src.startsWith('assets/history/'));assert(fs.existsSync(event.sound.src));assert.equal(event.sound.clipStart,0);assert.equal(event.sound.clipEnd,0);}
const plain=x=>JSON.parse(JSON.stringify(x)),base={kind:'sound',id:'sample',x:50,y:50,area:{x:0,y:0,w:100,h:100},sound:{src:'sample.mp3',trigger:'area',mode:'spatial',volume:100,playMode:'loop',clipStart:5,clipEnd:10}};
assert.equal(rules.soundMix(base,{bosses:[]},{},{x:0,y:0},[]).volume,.08,'the whole rectangle, including its corners, remains audible');
assert.equal(rules.soundMix(base,{bosses:[]},{},{x:-1,y:0},[]).volume,0);
assert.equal(rules.soundMix(base,{bosses:[]},{},{x:50,y:50},[]).volume,1);
const player={x:50,y:50},foe={alive:true,x:40,y:40};
for(const [condition,expected] of [['near_player',true],['no_near_player',false],['in_area',true],['no_in_area',false],['in_area_not_near',false]]){
 assert.equal(rules.soundMix({...base,sound:{...base.sound,enemyCondition:condition}},{bosses:[]},{},player,[foe]).active,expected,condition);
}
assert.equal(rules.soundMix({...base,sound:{...base.sound,enemyCondition:'near_player'}},{bosses:[]},{},player,[{...foe,alive:false}]).active,false,'dead troops cannot keep combat music on');
const bossMap={bosses:[{id:'boss',kind:'boss',x:10,y:10,w:60,h:60,hp:500}]};
assert(rules.soundMix({...base,sound:{...base.sound,enemyCondition:'near_player'}},bossMap,{},player,[]).active);
assert.equal(rules.soundMix({...base,sound:{...base.sound,enemyCondition:'near_player'}},bossMap,{boss:{hp:0,broken:true}},player,[]).active,false);
const shieldMap={width:200,height:200,colliders:[],doors:[],destructibles:[{id:'b',kind:'boss',x:100,y:50,w:30,h:30,collisionRect:[100,50,30,30],hp:20,shield:10}]},boss=shieldMap.destructibles[0],state=rules.initialObjects(shieldMap),attacker={id:'hero',x:90,y:60};
assert(rules.hitObject(shieldMap,boss,state.b,attacker,8,20,{},state,1000));assert.equal(state.b.hitDamage,8);assert.equal(state.b.hitSerial,1);assert.equal(state.b.hp,20);
assert.equal(rules.hitObject({...shieldMap,colliders:[[93,0,2,200]]},boss,state.b,attacker,10,20,{},state,1100),false);assert.equal(state.b.hitSerial,1,'blocked attacks cannot flash or emit damage numbers');
assert(rules.hitObject(shieldMap,boss,state.b,attacker,100,20,{},state,1200));assert.equal(state.b.hitDamage,22,'overkill displays only actual HP and shield removed');assert.equal(state.b.hitSerial,2);
const raw=JSON.parse(fs.readFileSync('assets/history/editor-project.json','utf8'));for(const t of tracks)assert.deepEqual(plain(t),raw.events.find(e=>e.id===t.id),'editor sound rules remain exact');
(async()=>{
 const music=ctx.RampageHistoryAudio.create({events:[base],bosses:[]});music.update(player,[],{});await Promise.resolve();
 const st=music.entries.get('sample');assert.equal(st.audio.currentTime,5);assert.equal(st.audio.paused,false);
 st.audio.currentTime=9;music.update({x:110,y:50},[],{});assert.equal(st.audio.paused,true);assert.equal(st.audio.currentTime,5,'loop resets on leaving its area');
 music.update(player,[],{});st.audio.currentTime=10;music.update(player,[],{});assert.equal(st.audio.currentTime,5,'loop obeys clip end');
 const resume=ctx.RampageHistoryAudio.create({events:[{...base,sound:{...base.sound,playMode:'resume'}}],bosses:[]});
 resume.update(player,[],{});await Promise.resolve();const rs=resume.entries.get('sample');rs.audio.currentTime=7;resume.update({x:110,y:50},[],{});assert(rs.audio.paused);assert.equal(rs.audio.currentTime,7);
 resume.update(player,[],{});assert.equal(rs.audio.currentTime,7,'resume keeps playback position');
 rs.audio.currentTime=10;resume.update(player,[],{});assert(rs.ended);assert(rs.audio.paused);resume.update(player,[],{});assert(rs.audio.paused,'resume stops at clip end');
 const once=ctx.RampageHistoryAudio.create({events:[{...base,sound:{...base.sound,playMode:'once'}}],bosses:[]});
 once.update(player,[],{});await Promise.resolve();const os=once.entries.get('sample');os.audio.currentTime=10;once.update(player,[],{});once.update({x:110,y:50},[],{});once.update(player,[],{});assert.equal(os.audio.calls,1);
 music.suspend();assert(st.audio.paused);music.clear();assert.equal(music.entries.size,0);assert.equal(st.audio.src,'');
 console.log('HISTORY AUDIO/FEEDBACK PASS: exact map music, rectangular attenuation, live enemies/boss conditions, clips, loop/once/resume, cleanup, confirmed shield/HP hits and bounded damage numbers.');
})().catch(e=>{console.error(e);process.exitCode=1});
