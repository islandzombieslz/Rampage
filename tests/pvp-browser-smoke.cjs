const assert=require('node:assert/strict');
const fs=require('node:fs'),http=require('node:http'),path=require('node:path');
const {chromium}=require('playwright');

const root=path.resolve(__dirname,'..');
const original=fs.readFileSync(path.join(root,'index.html'),'utf8');
const gif=Buffer.from('R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=','base64');
const firebaseStub=String.raw`
(() => {
 const user={uid:'browser-smoke-user',displayName:'Tester',isAnonymous:false};
 const database={rooms:{},profiles:{}},subscriptions=new Set();
 const parts=path=>String(path).split('/').filter(Boolean);
 function read(path){return parts(path).reduce((obj,key)=>obj?.[key],database)??null}
 function snapshotValue(path){return path==='.info/connected'?true:path==='.info/serverTimeOffset'?0:read(path)}
 function snapshot(path){const value=snapshotValue(path);return {val:()=>value,exists:()=>value!==null}}
 function write(path,value){
   const tokens=parts(path);let current=database;
   for(let i=0;i<tokens.length-1;i++)current=current[tokens[i]]??={};
   if(!tokens.length)return;
   if(value===null)delete current[tokens.at(-1)];
   else current[tokens.at(-1)]=value;
   queueMicrotask(()=>{for(const listener of [...subscriptions])try{listener.cb(snapshot(listener.path))}catch(e){console.error(e)}});
 }
 const F={
  firebaseAuth:{currentUser:user,authStateReady:async()=>{}},firebaseDb:{},
  googleProvider:{},ref:(_db,path)=>path,
  onAuthStateChanged:(_auth,cb)=>{queueMicrotask(()=>cb(user));return()=>{}},
  signInAnonymously:async()=>({user}),signInWithPopup:async()=>({user}),getRedirectResult:async()=>null,
  signOut:async()=>{},updateProfile:async()=>{},
  serverTimestamp:()=>Date.now(),
  get:async path=>({val:()=>read(path),exists:()=>read(path)!==null}),
  set:async(path,value)=>write(path,value),
  update:async(path,patch)=>{for(const [key,val] of Object.entries(patch))write(path+'/'+key,val)},
  remove:async path=>write(path,null),
  onDisconnect:()=>({remove:async()=>{}}),
  onValue:(path,cb)=>{const listener={path,cb};subscriptions.add(listener);
    queueMicrotask(()=>cb(snapshot(path)));
    return()=>subscriptions.delete(listener);
  },
  runTransaction:async(path,fn)=>{
    const candidate=fn(read(path));if(candidate===undefined)return {committed:false,snapshot:{val:()=>read(path)}};
    write(path,candidate);return {committed:true,snapshot:{val:()=>read(path)}};
  }
 };
 window.FirebaseBridge=F;
 queueMicrotask(()=>window.dispatchEvent(new Event('firebase-ready')));
})();
`;
// Inject a test-only hook inside the game's closure; nothing is exported by
// the production build and no production code is changed for browser tests.
const pvpTestHook=`window.__pvpBrowserTest={
 castEgyptianSpecial(){
   const hero=pvpLocalHero();
   if(!hero||hero.pvpHero!=='egyptMageFemale')return false;
   hero.pvpPowerUntil=0;hero.pvpActionUntil=0;hero.attackCooldown=0;
   hero.pvpSpecialReadyAt=performance.now()-1;
   return pvpSpecialAttack(hero);
 },
 castWarriorSpecial(){
   const ally=state.entities.find(e=>e.alive&&e.pvpAllyBot&&e.pvpHero==='mageFemale');
   if(!ally)return false;
   ally.pvpPowerUntil=0;ally.pvpActionUntil=0;ally.attackCooldown=0;
   ally.pvpSpecialReadyAt=performance.now()-1;
   return pvpSpecialAttack(ally);
 },
 warriorFx(){
   const ally=state.entities.find(e=>e.pvpAllyBot&&e.pvpHero==='mageFemale');
   const img=ally&&pvpSpecialFxNodes.get(ally.id);
   return {serial:ally?.pvpSpecialSerial||0,src:!!img?.hasAttribute('src'),
     played:ally?pvpSpecialFxPlayedSerial.get(ally.id):null,
     opacity:Number(img?.style.opacity||0),loaded:!!img?.naturalWidth,
     loading:!!img?.classList.contains('pvp-gif-loading'),
     currentUrl:img?.getAttribute('src')||''};
 },
 expireAndReplayWarriorFx(){
   const ally=state.entities.find(e=>e.pvpAllyBot&&e.pvpHero==='mageFemale');
   if(!ally)return false;
   ally.pvpSpecialFxUntil=performance.now()-1;
   syncPVPSpecialEffects(state.camera.x,state.camera.y,state.camera.zoom,innerWidth,innerHeight);
   ally.pvpSpecialFxUntil=performance.now()+1000;
   syncPVPSpecialEffects(state.camera.x,state.camera.y,state.camera.zoom,innerWidth,innerHeight);
   return !!pvpSpecialFxNodes.get(ally.id);
 },
 dragonFirstHit(){
   const hero=pvpLocalHero();
   if(!hero?.alive)return {armed:false,shot:false};
   const dragon=state.entities.find(e=>e.alive&&e.type==='dragon')||pvpSpawnNPC('dragon');
   dragon.pvpDragonFirstHitSeen=false;dragon.pvpDragonRetaliatePending=false;
   dragon.pendingDragonAttack=null;dragon.dragonFlightState='takeoff';
   dragon.dragonTakeoffEndAt=performance.now()+180;dragon.knockTime=.12;
   const before=state.dragonProjectiles.length;
   pvpCombatHit(dragon,hero,12);
   const armed=dragon.pvpDragonRetaliatePending===true;
   dragon.dragonTakeoffEndAt=performance.now()-1;
   pvpBotAction(dragon,.016);
   return {armed,shot:state.dragonProjectiles.length===before+1,
     correctSource:state.dragonProjectiles.some(p=>p.sourceId===dragon.id),
     cleared:dragon.pvpDragonRetaliatePending===false};
 },
 async decodedFlameFrames(){
   const out=[];
   if(typeof ImageDecoder==='undefined')return {available:false};
   for(const key of ['magePower','egyptMagePower']){
     const bytes=new Uint8Array(await (await fetch(ASSETS[key])).arrayBuffer());
     const decoder=new ImageDecoder({data:bytes,type:'image/gif'});
     await decoder.tracks.ready;
     const count=decoder.tracks.selectedTrack.frameCount;
     const picks=[0,Math.floor(count*.2),Math.floor(count*.4),Math.floor(count*.6),Math.floor(count*.8),count-1];
     const frames=[];
     for(const i of picks){
       const f=await decoder.decode({frameIndex:i,completeFramesOnly:true});
       const canvas=document.createElement('canvas');canvas.width=160;canvas.height=55;
       const g=canvas.getContext('2d',{willReadFrequently:true});g.drawImage(f.image,0,0,160,55);
       const d=g.getImageData(0,0,160,55).data;let count=0,minX=160,maxX=-1,minY=55,maxY=-1;
       for(let y=0;y<55;y++)for(let x=0;x<160;x++)if(d[(y*160+x)*4+3]>16){
         count++;minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y);
       }
       frames.push({i,duration:f.image.duration,count,bbox:[minX,minY,maxX,maxY],center:d[(27*160+57)*4+3]});
       f.image.close();
     }
     out.push({key,frameCount:count,frames});decoder.close();
   }
   return {available:true,out};
 },
 async realFlameProbe(){
   const out=[];
   for(const [clan,key] of [['warriors','magePower'],['egypt','egyptMagePower']]){
     const img=await new Promise((resolve,reject)=>{const i=new Image();i.onload=()=>resolve(i);i.onerror=reject;i.src=ASSETS[key]+'?probe='+Date.now()});
     const samples=[];
     for(const delay of [0,250,500,750]){
       if(delay)await new Promise(r=>setTimeout(r,delay));
       const canvas=document.createElement('canvas');canvas.width=160;canvas.height=55;
       const g=canvas.getContext('2d',{willReadFrequently:true});g.drawImage(img,0,0,160,55);
       const d=g.getImageData(0,0,160,55).data;let count=0,minX=160,maxX=-1,minY=55,maxY=-1;
       for(let y=0;y<55;y++)for(let x=0;x<160;x++)if(d[(y*160+x)*4+3]>16){
         count++;minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y);
       }
       samples.push({delay,count,bbox:[minX,minY,maxX,maxY],center:d[(27*160+57)*4+3]});
     }
     out.push({clan,dimensions:[img.naturalWidth,img.naturalHeight],samples});
   }
   return out;
 },
 missingSprites(){
   return [...document.querySelectorAll('#entityLayer img,#combatFxLayer img')]
     .filter(img=>!img.hasAttribute('src')&&getComputedStyle(img).visibility!=='hidden')
     .length;
 },
 async flameDamageWithoutRender(){
   const own=pvpLocalHero();if(!own||!state.running)return null;
   const canvas=document.createElement('canvas');canvas.width=2;canvas.height=2;
   const g=canvas.getContext('2d');g.fillStyle='#fff';g.fillRect(0,0,2,2);
   const load=src=>new Promise((resolve,reject)=>{
     const img=new Image();img.onload=()=>resolve(img);img.onerror=reject;img.src=src;
   });
   const opaque=await load(canvas.toDataURL('image/png'));
   g.clearRect(0,0,2,2);
   const transparent=await load(canvas.toDataURL('image/png'));
   const saved={egypt:PVP_FIRE_IMAGES.egypt,warrior:PVP_FIRE_IMAGES.warrior};
   const result=[];
   for(const clan of ['warriors','egypt']){
     const key=clan==='egypt'?'egypt':'warrior';
     const heroDef=PVP_HERO_BY_ID[clan==='egypt'?'egyptMageFemale':'mageFemale'];
     const caster=pvpBaseEntity(heroDef,650,650,own.team,own.color,null,false); // Test a real human-strength PvP mage, not a half-damage minion.
     const target=pvpBaseEntity(PVP_HERO_BY_ID.warrior,790,650,'pvp-enemy','#f55',null,true);
     const t=performance.now();
     caster.pvpPowerUntil=t+2500;caster.pvpPowerNextTick=t-1;caster.pvpAimTarget=target.id;caster.pvpAimAngle=0;
     PVP_FIRE_IMAGES[key]=opaque;
     const before=target.shield+target.hp;
     pvpTickPower(caster,t,null);
     const hit=before-(target.shield+target.hp);
     caster.pvpPowerNextTick=t-1;
     PVP_FIRE_IMAGES[key]=transparent;
     const middle=target.shield+target.hp;
     pvpTickPower(caster,t,null);
     const transparentHit=middle-(target.shield+target.hp);
     result.push({clan,hit,transparentHit,domPresent:pvpFlameNodes.has(caster.id)});
     state.entities=state.entities.filter(e=>e!==caster&&e!==target);
   }
   for(const key of ['egypt','warrior']){
     if(saved[key])PVP_FIRE_IMAGES[key]=saved[key];else delete PVP_FIRE_IMAGES[key];
   }
   return result;
 },
 dragonSecondHit(){
   const dragon=state.entities.find(e=>e.type==='dragon'&&e.alive&&e.pvpDragonFirstHitSeen);
   if(!dragon)return {queued:false,shot:false};
   dragon.pvpDragonRetaliatePending=false;dragon.pvpDragonRetaliateImmediate=false;
   dragon.pvpDragonObservedDurability=dragon.shield+dragon.hp;
   dragon.shield=Math.max(0,dragon.shield-10);
   const before=state.dragonProjectiles.length;
   pvpObserveDragonDamage(dragon);
   const queued=dragon.pvpDragonRetaliatePending&&!dragon.pvpDragonRetaliateImmediate;
   dragon.pendingDragonAttack=null;dragon.dragonFlightState='flying';dragon.knockTime=0;
   dragon.pvpNpcNextAttackAt=performance.now()-1;
   dragon.dragonNextShotAt=0;dragon.dragonCloseShotAt=0;
   pvpBotAction(dragon,.016);
   return {queued,shot:state.dragonProjectiles.length===before+1,cleared:!dragon.pvpDragonRetaliatePending};
 },
 enforceSpecialCycle(){
   const ally=state.entities.find(e=>e.pvpAllyBot&&e.pvpHero==='mageFemale');
   if(!ally)return false;
   pvpExactGifDurationMs.set('magePowerSpecial',400);
   ally.pvpSpecialFxStartedAt=performance.now()-500;
   syncPVPSpecialEffects(state.camera.x,state.camera.y,state.camera.zoom,innerWidth,innerHeight);
   syncPVPSpecialEffects(state.camera.x,state.camera.y,state.camera.zoom,innerWidth,innerHeight);
   return !pvpSpecialFxNodes.has(ally.id)&&pvpSpecialFxPlayedSerial.get(ally.id)===ally.pvpSpecialSerial;
 }

};`;
const testHTML=original.replace(/<script type="module">[\s\S]*?<\/script>/,()=>'<script>'+firebaseStub+'</script>')
 .replace('/* ==================== PVE ==================== */',pvpTestHook+'\n/* ==================== PVE ==================== */');
assert.notEqual(testHTML,original);
const server=http.createServer((req,res)=>{
 const name=new URL(req.url,'http://127.0.0.1').pathname;
 if(name==='/'||name==='/index.html'){
   res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'});res.end(testHTML);return;
 }
 if(name==='/sw.js'){res.writeHead(200,{'Content-Type':'application/javascript'});res.end('self.addEventListener("install",()=>self.skipWaiting());');return}
 // Exercise the one-time canonical fallback when a cache-busted GIF fails.
 if(name==='/assets/mage/poder-mago-especial.gif'&&new URL(req.url,'http://127.0.0.1').searchParams.has('gifStart')){
   res.writeHead(404);res.end('test-only cache-buster failure');return;
 }
 if(name==='/assets/mage/poder-mago.gif'||name==='/assets/egypt/mage/power-normal.gif'){
   res.writeHead(200,{'Content-Type':'image/gif','Cache-Control':'no-store'});
   res.end(fs.readFileSync(path.join(root,name.slice(1))));return;
 }
 if(/\.(gif|png|webp|jpg|jpeg|svg)$/i.test(name)){res.writeHead(200,{'Content-Type':'image/gif'});res.end(gif);return}
 if(/\.(mp3|wav|ogg)$/i.test(name)){res.writeHead(200,{'Content-Type':'audio/mpeg'});res.end(Buffer.alloc(0));return}
 res.writeHead(404);res.end();
});
async function main(){
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({headless:true});
 const errors=[],renderErrors=[];
 const page=await browser.newPage({viewport:{width:1280,height:720}});
 page.on('pageerror',err=>errors.push(err.message));
 page.on('console',msg=>{if(msg.type()==='error'&&/PvP (desenho|simulação|entidade)|IndexSizeError/.test(msg.text()))renderErrors.push(msg.text())});
 try{
   await page.goto('http://127.0.0.1:'+server.address().port+'/',{waitUntil:'domcontentloaded'});
   await page.waitForFunction(()=>!document.body.classList.contains('booting'),null,{timeout:55000});
   try{
     await page.waitForFunction(()=>document.querySelector('#accountXpSync')?.textContent==='XP salvo na conta',null,{timeout:15000});
   }catch(err){
     const status=await page.evaluate(()=>({
       booting:document.body.classList.contains('booting'),
       xp:document.querySelector('#accountXpSync')?.textContent,
       account:document.querySelector('#accountStatus')?.textContent,
       firebase:document.querySelector('#firebaseStatus')?.textContent,
       name:document.querySelector('#accountName')?.textContent,
       auth:window.FirebaseBridge?.firebaseAuth?.currentUser?.uid
     }));
     console.error('Browser startup diagnostics:',status,'Page errors:',errors);
     throw err;
   }
   await page.locator('#createBtn').click();
   await page.locator('#modeScreen.active').waitFor({timeout:8000});
   await page.locator('.mode-card[data-mode="pvp"]').click();
   await page.locator('#configureBtn').click();
   await page.locator('#configScreen.active').waitFor({timeout:8000});
   await page.locator('#createRoomBtn').click();
   await page.locator('#lobbyScreen.active').waitFor({timeout:12000});
   const plus=page.locator('#lobbyScreen button.plus[data-target="npcs"]');
   for(let i=0;i<5;i++)await plus.click();
   await page.waitForFunction(()=>document.querySelector('#npcCountVal')?.textContent==='3');
   assert.equal(await page.locator('#lobbyScreen.pvp-lobby .pvp-player-card').count(),4,'maximum four allies in PvP lobby');
   assert.equal(await page.locator('#lobbyScreen.pvp-lobby .pvp-player-card:not(.empty)').count(),4,'one player and three allied NPCs');
   try{
     await page.locator('#playerList .pvp-player-card.mine').click({timeout:12000});
   }catch(err){
     const debug=await page.evaluate(()=>({
       cards:[...document.querySelectorAll('#playerList .pvp-player-card')].map(e=>({class:e.className,text:e.textContent})).slice(0,4),
       lobby:document.querySelector('#lobbyScreen')?.className,
       status:document.querySelector('#accountXpSync')?.textContent,
       roomCode:document.querySelector('#roomCode')?.textContent
     }));
     console.error('PvP lobby diagnostics:',debug,'Page errors:',errors);
     throw err;
   }
   await page.locator('#pvpPicker:not([hidden])').waitFor();
   assert.equal(await page.locator('#pvpHeroChoices button').count(),3,'PvP offers exactly three heroes');
   await page.locator('#pvpHeroChoices button').filter({hasText:'Maga do Egito'}).first().click();
   await page.locator('#pvpHeroConfirm').click();
   await page.locator('#gameScreen.active.pvp-mode').waitFor({timeout:13000});
   await page.locator('#pvpCombatHud:not([hidden])').waitFor();
   await page.locator('#pvpCombatHud [data-pvp-action="power"]').click();
   await page.locator('#attackBtn').click();
   await page.waitForTimeout(1250); // Includes live PvP update, aiming, GIF effect and combat frames.
   // Exercise the Egyptian mage special in the live frame loop, not only the
   // normal flame: it summons two Anubis and previously could black-screen PvP.
   const specialStarted=await page.evaluate(()=>window.__pvpBrowserTest.castEgyptianSpecial());
   assert(specialStarted,'Egyptian mage special must activate');
   await page.waitForTimeout(700);
   assert.equal(await page.locator('#gameScreen.active.pvp-mode').count(),1,'special must not black-screen the match');
   // A 1.8x PvP camera at fullscreen-size viewport formerly repeatedly threw
   // an IndexSizeError from the special's negative Canvas arc radius.
   await page.setViewportSize({width:1920,height:1080});
   await page.waitForTimeout(450);
   assert(!renderErrors.length,'PvP must render long specials without Canvas exceptions: '+renderErrors.join(' | '));
   assert(await page.evaluate(()=>window.__pvpBrowserTest.castWarriorSpecial()),'Warrior mage special must activate');
   await page.waitForTimeout(260);
   const firstFx=await page.evaluate(()=>window.__pvpBrowserTest.warriorFx());
   assert.equal(firstFx.serial,1,'Warrior special serial');
   assert.equal(firstFx.src,true,'Warrior power GIF starts behind the mage');
   assert.equal(firstFx.opacity,1,'Warrior special GIF remains fully bright between short fades');
   assert(firstFx.loaded&&!firstFx.loading,'PvP canonical retry finishes decoding before showing the image');
   assert(!firstFx.currentUrl.includes('gifStart='),'failed unique URL retries the cached canonical GIF');
   assert.equal(await page.evaluate(()=>window.__pvpBrowserTest.missingSprites()),0,'stopped sprites cannot paint broken image icons');
   const dragon=await page.evaluate(()=>window.__pvpBrowserTest.dragonFirstHit());
   assert.deepEqual(dragon,{armed:true,shot:true,correctSource:true,cleared:true},
     'first incoming hit must produce a real dragon projectile even during takeoff');
   const realFlames=await page.evaluate(()=>window.__pvpBrowserTest.realFlameProbe());
   console.log('REAL_PVP_FLAMES',JSON.stringify(realFlames));
   console.log('DECODED_PVP_FLAMES',JSON.stringify(await page.evaluate(()=>window.__pvpBrowserTest.decodedFlameFrames())));
   const bothMages=await page.evaluate(()=>window.__pvpBrowserTest.flameDamageWithoutRender());
   assert.deepEqual(bothMages,[
     {clan:'warriors',hit:15,transparentHit:0,domPresent:false},
     {clan:'egypt',hit:15,transparentHit:0,domPresent:false}
   ],'both PvP flame types must damage opaque pixels with no DOM sprite and ignore transparent pixels');
   const secondShot=await page.evaluate(()=>window.__pvpBrowserTest.dragonSecondHit());
   assert.deepEqual(secondShot,{queued:true,shot:true,cleared:true},
     'PvP dragon must continue launching projectiles after a second direct hit');
   assert(await page.evaluate(()=>window.__pvpBrowserTest.enforceSpecialCycle()),
     'accurate PvP GIF duration stops a special even if its old gameplay window remains');
   const replayed=await page.evaluate(()=>window.__pvpBrowserTest.expireAndReplayWarriorFx());
   assert.equal(replayed,false,'spent PvP special never recreates its GIF on a late snapshot');
   assert(!renderErrors.length,'Fullscreen PvP visuals must remain stable: '+renderErrors.join(' | '));
   assert.equal(await page.locator('#gameScreen.war-lobby').count(),0);
   assert(!errors.length,'browser JavaScript errors: '+errors.join('\n'));
   console.log('BROWSER PASS: login/profile, lobby, hero selection, solo PvP gameplay, mage flame, Egyptian/Warrior specials, fullscreen Canvas, first-hit dragon ball, decoded image fallback, both flame collisions, repeated dragon shots and no GIF replay');
 }finally{await browser.close();await new Promise(resolve=>server.close(resolve))}
}
main().catch(err=>{console.error(err);process.exitCode=1;server.close()});
