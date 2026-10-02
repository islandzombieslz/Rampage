// Real local art, real combat and DOM renderer. Firebase is isolated: this never
// joins a production room or writes an account's XP.
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),original=fs.readFileSync(path.join(root,'index.html'),'utf8');
const smoke=fs.readFileSync(path.join(__dirname,'pvp-browser-smoke.cjs'),'utf8');
const firebase=smoke.slice(smoke.indexOf('const firebaseStub=String.raw`')+'const firebaseStub=String.raw`'.length,smoke.indexOf('\n`;\n// Inject'));
assert(firebase.includes('window.FirebaseBridge=F'));
const hook=`const battleProfile={simulation:[],draw:[]};
const battleOriginalSimulation=updateGameSimulation,battleOriginalDraw=draw;
updateGameSimulation=function(dt,now){const start=performance.now();try{return battleOriginalSimulation(dt,now)}finally{battleProfile.simulation.push(performance.now()-start)}};
draw=function(){const start=performance.now();try{return battleOriginalDraw()}finally{battleProfile.draw.push(performance.now()-start)}};
window.__battleLoad={
 resetProfile(){battleProfile.simulation.length=0;battleProfile.draw.length=0},
 profile(){
  const summarize=list=>{const sorted=list.slice().sort((a,b)=>a-b);return {samples:sorted.length,medianMs:+(sorted[Math.floor(sorted.length*.5)]||0).toFixed(2),p95Ms:+(sorted[Math.floor(sorted.length*.95)]||0).toFixed(2)}};
  return {simulation:summarize(battleProfile.simulation),draw:summarize(battleProfile.draw)};
 },
 pvp(wave){
  NetworkAdapter.roomId=null;NetworkAdapter.hostUid=NetworkAdapter.localPlayerId;
  state.mode='pvp';state.difficulty='hard';state.phase='combat';state.running=true;state.round=1;state.rounds=99;
  state.players=[{id:NetworkAdapter.localPlayerId,human:true,pvpHero:'warrior',name:'Load test',color:'#58a6ff'},
   ...Array.from({length:4},(_,i)=>({id:'ally_'+i,human:false,pvpHero:i%2?'mageFemale':'warrior',name:'Ally '+i,color:'#9cf'}))];
  beginMatchTracking();beginPVPRound();
  if(wave){state.entities=state.entities.filter(e=>!e.pvpMinion);pvpSpawnWave(wave)}
  for(const e of state.entities){e.hp=e.maxHp=100000;e.shield=e.maxShield=100000}
  configureGameScreenForMode();navigateScreen('gameScreen');
  return {entities:state.entities.length,allies:state.entities.filter(e=>e.pvpAllyBot).length,wave:pvpLastWave};
 },
 war(count){
  state.mode='war';state.phase='combat';state.running=true;state.world.w=2200;state.world.h=1400;
  state.entities=[];state.particles=[];state.dragonProjectiles=[];clearEntityVisuals();
  warCombatGrid.clear();warCandidateCache.clear();warFrameEnemiesByTeam.clear();warAIGridBuiltAt=0;
  state.warTime=180;state.timeLeft=180;state.round=1;state.rounds=99;
  state.players=[{id:'army_a',human:true,local:true,color:'#58a6ff',clan:'warriors',score:0,gems:0,troops:count/2},
   {id:'army_b',human:false,color:'#fb6772',clan:'warriors',score:0,gems:0,troops:count/2}];
  beginMatchTracking();
  for(let i=0;i<count;i++){
   const e=entityBase('warrior',430+(i%24)*48,360+Math.floor(i/24)*52,i%2?'army_a':'army_b',i%2?'#58a6ff':'#fb6772');
   e.hp=e.maxHp=100000;e.shield=e.maxShield=100000;state.entities.push(e);
  }
  state.camera.x=180;state.camera.y=100;state.camera.zoom=1;state.camera.intro=false;
  configureGameScreenForMode();navigateScreen('gameScreen');return state.entities.length;
 },
 metrics(){
  const bodies=[...document.querySelectorAll('.entity-visual')].filter(e=>e._nodeVisible!==false&&!e.classList.contains('dying'));
  return {fps:state.fps,entities:state.entities.length,visible:bodies.length,
   missing:bodies.filter(el=>![...el.querySelectorAll('.entity-body')].some(img=>img.style.display!=='none'&&img.style.opacity!=='0'&&img.complete&&img.naturalWidth>0)).length,
   floorLoaded:(state.mode==='pvp'?pvpFloorImage:warFloorImage).naturalWidth>0,
   authorityErrors:state.entities.filter(e=>e.alive&&!Number.isFinite(e.x+e.y)).length};
 }
};`;
const html=original.replace(/<script type="module">[\s\S]*?<\/script>/,()=>'<script>'+firebase+'</script>')
 .replace('/* ==================== PVE ==================== */',hook+'\n/* ==================== PVE ==================== */');
const server=http.createServer((req,res)=>{
 const name=new URL(req.url,'http://localhost').pathname;
 if(name==='/'||name==='/index.html'){res.writeHead(200,{'Content-Type':'text/html;charset=utf-8'});res.end(html);return}
 const file=path.resolve(root,'.'+decodeURIComponent(name));
 if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end();return}
 const ext=path.extname(file),type={'.js':'application/javascript','.gif':'image/gif','.png':'image/png','.mp3':'audio/mpeg','.ogg':'audio/ogg'}[ext]||'application/octet-stream';
 res.writeHead(200,{'Content-Type':type,'Cache-Control':'public,max-age=3600'});fs.createReadStream(file).pipe(res);
});
async function measure(page,name){
 await page.waitForTimeout(1500);
 await page.evaluate(()=>window.__battleLoad.resetProfile());
 const frames=await page.evaluate(()=>new Promise(resolve=>{
  const times=[];let started=performance.now(),last=started;
  function frame(now){times.push(now-last);last=now;if(now-started>=2000)resolve(times);else requestAnimationFrame(frame)}
  requestAnimationFrame(frame);
 }));
 frames.sort((a,b)=>a-b);
 const result={name,...await page.evaluate(()=>window.__battleLoad.metrics()),
  cpu:await page.evaluate(()=>window.__battleLoad.profile()),
  frameMedianMs:+frames[Math.floor(frames.length*.5)].toFixed(1),frameP95Ms:+frames[Math.floor(frames.length*.95)].toFixed(1),
  frameMaxMs:+frames.at(-1).toFixed(1)};
 assert(result.floorLoaded,name+' floor must load');assert(result.visible>0,name+' sprites must render');
 assert.equal(result.authorityErrors,0,name+' finite positions');
 assert(result.missing<Math.max(2,result.visible*.05),name+' sprites must recover: '+JSON.stringify(result));
 assert(result.frameP95Ms<500,name+' main loop must not freeze for half a second');
 console.log(JSON.stringify(result));return result;
}
async function main(){
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const browser=await chromium.launch({headless:true}),errors=[],reports=[];
 try{
  const page=await browser.newPage({viewport:{width:1280,height:720}});
  page.on('pageerror',e=>errors.push(e.message));
  page.on('console',msg=>{if(msg.type()==='error'&&/PvP (desenho|simulação|entidade|física)|IndexSizeError|ReferenceError/.test(msg.text()))errors.push(msg.text())});
  await page.goto('http://127.0.0.1:'+server.address().port+'/',{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>!document.body.classList.contains('booting'),null,{timeout:180000});
  for(let wave=0;wave<4;wave++){
   const setup=await page.evaluate(w=>window.__battleLoad.pvp(w),wave);assert.equal(setup.allies,4);
   reports.push(await measure(page,'hard-wave-'+(wave+1)+'-four-allies'));
  }
  for(const count of [96,240]){
   assert.equal(await page.evaluate(n=>window.__battleLoad.war(n),count),count);
   reports.push(await measure(page,'war-'+count+'-troops'));
  }
  assert(!errors.length,'real-art combat errors: '+errors.join('\n'));
  fs.mkdirSync(path.join(root,'test-results'),{recursive:true});
  fs.writeFileSync(path.join(root,'test-results','battle-load.json'),JSON.stringify(reports,null,2));
  await page.screenshot({path:path.join(root,'test-results','battle-load.png')});
  console.log('BROWSER LOAD PASS: all hard waves + four allies, real GIFs, 96/240 Clan War troops');
 }finally{await browser.close();await new Promise(r=>server.close(r))}
}
main().catch(e=>{console.error(e);process.exitCode=1;server.close()});
