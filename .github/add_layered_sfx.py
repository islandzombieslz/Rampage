from pathlib import Path

p=Path('index.html')
t=p.read_text(encoding='utf-8')

def replace_once(old,new,label):
    global t
    if new in t:
        return
    c=t.count(old)
    if c!=1:
        raise SystemExit(f'{label}: expected 1 anchor, found {c}')
    t=t.replace(old,new,1)

def insert_after(anchor,addition,label):
    global t
    if addition in t:
        return
    c=t.count(anchor)
    if c!=1:
        raise SystemExit(f'{label}: expected 1 anchor, found {c}')
    t=t.replace(anchor,anchor+addition,1)

sfx_system=r'''
/* ==================== LAYERED SFX 2026-09-18 ==================== */
const SFX_ASSETS=Object.freeze({
 click:'assets/audio/sfx/click.mp3',
 click2:'assets/audio/sfx/click2.mp3',
 transition:'assets/audio/sfx/transition.mp3',
 melee:'assets/audio/sfx/melee.mp3',
 shake:'assets/audio/sfx/shake.mp3',
 burn:'assets/audio/sfx/burn.mp3',
 mage:'assets/audio/sfx/mage.mp3'
});
let layeredSfxContext=null;
const layeredSfxRaw=new Map(Object.entries(SFX_ASSETS).map(([key,url])=>[
 key,
 fetch(url,{cache:'force-cache'}).then(r=>{
   if(!r.ok)throw Error('SFX '+key+' '+r.status);
   return r.arrayBuffer();
 }).catch(err=>{console.warn('SFX preload failed',key,err);return null})
]));
const layeredSfxBuffers=new Map();
const layeredSfxDecodePromises=new Map();
const layeredSfxLastAt=new Map();
const layeredSfxLoops=new Map();
let layeredBattleSfxLastScan=0;
const MELEE_FIGHT_SFX_TYPES=new Set(['warrior','brownWarrior','king','golem','naja','anubis']);

function getLayeredSfxContext(){
 if(!layeredSfxContext){
   const AC=window.AudioContext||window.webkitAudioContext;
   if(!AC)return null;
   layeredSfxContext=new AC();
 }
 if(layeredSfxContext.state==='suspended')layeredSfxContext.resume().catch(()=>{});
 return layeredSfxContext;
}
async function ensureLayeredSfxBuffer(key){
 if(layeredSfxBuffers.has(key))return layeredSfxBuffers.get(key);
 if(layeredSfxDecodePromises.has(key))return layeredSfxDecodePromises.get(key);
 const ctx=getLayeredSfxContext();if(!ctx)return null;
 const promise=(async()=>{
   const raw=await layeredSfxRaw.get(key);
   if(!raw)return null;
   try{
     const decoded=await ctx.decodeAudioData(raw.slice(0));
     layeredSfxBuffers.set(key,decoded);
     return decoded;
   }catch(err){
     console.warn('SFX decode failed',key,err);
     return null;
   }
 })();
 layeredSfxDecodePromises.set(key,promise);
 return promise;
}
function warmLayeredSfx(){
 getLayeredSfxContext();
 for(const key of Object.keys(SFX_ASSETS))ensureLayeredSfxBuffer(key);
}
function warZoomSfxVolume(){
 if(state.mode!=='war')return 1;
 const z=clamp(Number(state.camera?.zoom)||1,.55,2.15);
 const t=clamp((z-.55)/(2.15-.55),0,1);
 return .025+.975*Math.pow(t,1.45);
}
function worldSfxMix(x,y){
 if(state.mode!=='war')return {gain:1,pan:0};
 const z=clamp(Number(state.camera?.zoom)||1,.55,2.15);
 const vp=gameViewportSize();
 const sx=(Number(x)-Number(state.camera.x||0))*z;
 const sy=(Number(y)-Number(state.camera.y||0))*z;
 const cx=vp.w*.5,cy=vp.h*.5;
 const dist=Math.hypot(sx-cx,sy-cy);
 const radius=Math.max(1,Math.hypot(vp.w,vp.h)*.72);
 const spatial=Math.pow(clamp(1-dist/radius,0,1),.70);
 const pan=clamp((sx-cx)/Math.max(1,vp.w*.52),-1,1);
 return {gain:warZoomSfxVolume()*spatial,pan};
}
async function playLayeredSfx(key,volume=1,pan=0,cooldownMs=0){
 if(!SFX_ASSETS[key])return false;
 const now=performance.now(),last=Number(layeredSfxLastAt.get(key))||-Infinity;
 if(cooldownMs&&now-last<cooldownMs)return false;
 layeredSfxLastAt.set(key,now);
 const buffer=await ensureLayeredSfxBuffer(key),ctx=layeredSfxContext;
 if(!buffer||!ctx||ctx.state!=='running')return false;
 const src=ctx.createBufferSource(),gain=ctx.createGain();
 src.buffer=buffer;gain.gain.value=clamp(volume,0,1);
 src.connect(gain);
 if(ctx.createStereoPanner){
   const panner=ctx.createStereoPanner();
   panner.pan.value=clamp(pan,-1,1);
   gain.connect(panner);panner.connect(ctx.destination);
 }else gain.connect(ctx.destination);
 src.start();
 return true;
}
function playWorldLayeredSfx(key,x,y,baseVolume=1,cooldownMs=0){
 const mix=worldSfxMix(x,y);
 if(mix.gain<=.006)return false;
 return playLayeredSfx(key,baseVolume*mix.gain,mix.pan,cooldownMs);
}
async function setLayeredLoop(key,volume,pan=0){
 const target=clamp(volume,0,1);
 let channel=layeredSfxLoops.get(key);
 if(!channel&&target>.004){
   const buffer=await ensureLayeredSfxBuffer(key),ctx=layeredSfxContext;
   if(!buffer||!ctx||ctx.state!=='running')return;
   channel=layeredSfxLoops.get(key);
   if(!channel){
     const src=ctx.createBufferSource(),gain=ctx.createGain();
     src.buffer=buffer;src.loop=true;gain.gain.value=0;src.connect(gain);
     let panner=null;
     if(ctx.createStereoPanner){
       panner=ctx.createStereoPanner();
       gain.connect(panner);panner.connect(ctx.destination);
     }else gain.connect(ctx.destination);
     src.start();
     channel={src,gain,panner};
     layeredSfxLoops.set(key,channel);
   }
 }
 if(!channel)return;
 const ctx=layeredSfxContext;
 channel.gain.gain.cancelScheduledValues(ctx.currentTime);
 channel.gain.gain.setTargetAtTime(target,ctx.currentTime,target>.004?.07:.13);
 if(channel.panner)channel.panner.pan.setTargetAtTime(clamp(pan,-1,1),ctx.currentTime,.08);
}
function stopLayeredBattleLoops(){
 setLayeredLoop('melee',0,0);
 setLayeredLoop('burn',0,0);
}
function meleeFightSfxCandidate(e){
 if(!e?.alive||!MELEE_FIGHT_SFX_TYPES.has(e.type))return false;
 if(e.type==='naja'&&najaIsUnderground(e))return false;
 return true;
}
function meleeFightSfxAttacking(e,now){
 if(e.type==='warrior')return Number(e.attackAnim)>0;
 if(e.type==='king')return Number(e.attackAnim)>0&&!e.pendingKingSpecial;
 if(e.type==='brownWarrior')return e.pendingBrownAttack?.kind==='normal'&&Number(e.pendingBrownAttack.endAt)>now;
 if(e.type==='golem')return e.pendingGolemAttack?.kind==='normal'&&Number(e.pendingGolemAttack.endAt)>now;
 if(e.type==='naja')return e.pendingNajaAttack?.kind==='normal'&&Number(e.pendingNajaAttack.endAt)>now;
 if(e.type==='anubis')return e.pendingAnubisAttack?.kind==='melee'&&Number(e.pendingAnubisAttack.endAt)>now;
 return false;
}
function bestMeleeFightSfxCluster(now){
 const fighters=state.entities.filter(meleeFightSfxCandidate);
 if(fighters.length<4)return null;
 const clusterSq=170*170,enemySq=125*125;
 let best=null,bestGain=0;
 for(const attacker of fighters){
   if(!meleeFightSfxAttacking(attacker,now))continue;
   const group=[];let enemyClose=false;
   for(const other of fighters){
     const dx=other.x-attacker.x,dy=other.y-attacker.y,d2=dx*dx+dy*dy;
     if(d2<=clusterSq)group.push(other);
     if(other.team!==attacker.team&&d2<=enemySq)enemyClose=true;
   }
   if(group.length<4||!enemyClose||new Set(group.map(e=>e.team)).size<2)continue;
   const x=group.reduce((sum,e)=>sum+e.x,0)/group.length;
   const y=group.reduce((sum,e)=>sum+e.y,0)/group.length;
   const mix=worldSfxMix(x,y);
   if(mix.gain>bestGain){bestGain=mix.gain;best={x,y,mix,count:group.length}}
 }
 return best;
}
function bestBurnSfxSource(now){
 let best=null,bestGain=0;
 for(const e of state.entities){
   if(!e.alive||Number(e.dragonBurnUntil||0)<=now)continue;
   const mix=worldSfxMix(e.x,e.y);
   if(mix.gain>bestGain){bestGain=mix.gain;best={x:e.x,y:e.y,mix}}
 }
 return best;
}
function updateLayeredBattleSfx(now){
 if(now-layeredBattleSfxLastScan<110)return;
 layeredBattleSfxLastScan=now;
 if(state.mode!=='war'||!state.running||state.phase!=='combat'){
   stopLayeredBattleLoops();
   return;
 }
 const fight=bestMeleeFightSfxCluster(now);
 if(fight)setLayeredLoop('melee',fight.mix.gain,fight.mix.pan);
 else setLayeredLoop('melee',0,0);
 const burning=bestBurnSfxSource(now);
 if(burning)setLayeredLoop('burn',burning.mix.gain,burning.mix.pan);
 else setLayeredLoop('burn',0,0);
}

document.addEventListener('pointerdown',ev=>{
 warmLayeredSfx();
 const button=ev.target.closest?.('button');
 if(!button||button.disabled||button.id==='attackBtn')return;
 if(button.classList.contains('plus')||button.classList.contains('minus')||button.id==='shopButton'){
   playLayeredSfx('click2',.55,0,25);
 }else{
   playLayeredSfx('click',.50,0,20);
 }
},{capture:true,passive:true});
document.addEventListener('keydown',warmLayeredSfx,{capture:true});
'''
insert_after("playDesiredMusic({restart:true});\n",sfx_system,'Layered SFX engine')

replace_once(
"""function screenWithFade(id){
 if(screenTransitionBusy){queuedScreenId=id;return}
 const fade=$('#screenTransitionFade');
 if(!fade){screen(id);return}
 screenTransitionBusy=true;fade.classList.add('show');""",
"""function screenWithFade(id){
 if(screenTransitionBusy){queuedScreenId=id;return}
 const fade=$('#screenTransitionFade');
 if(!fade){screen(id);return}
 playLayeredSfx('transition',.75,0,260);
 screenTransitionBusy=true;fade.classList.add('show');""",
'Menu transition SFX'
)

replace_once(
"""function navigateScreen(id){
 const current=$('.screen.active')?.id||null;
 if(current===id)return;""",
"""function navigateScreen(id){
 const current=$('.screen.active')?.id||null;
 if(current===id)return;
 if(id!=='gameScreen')stopLayeredBattleLoops();""",
'Stop battle loops on navigation'
)

replace_once(
" hitSerial:0,hitDirX:0,hitDirY:0,hitTilt:13,knockVX:0,knockVY:0,knockTime:0,",
" hitSerial:0,hitDirX:0,hitDirY:0,hitTilt:13,shakeSerial:0,shakePower:0,knockVX:0,knockVY:0,knockTime:0,",
'Entity shake SFX state'
)

replace_once(
"""   hitSerial:Number(e.hitSerial)||0,hitDirX:Number(e.hitDirX)||0,hitDirY:Number(e.hitDirY)||0,hitTilt:Number(e.hitTilt)||13,
   deathStarted:e.deathStarted?1:0,""",
"""   hitSerial:Number(e.hitSerial)||0,hitDirX:Number(e.hitDirX)||0,hitDirY:Number(e.hitDirY)||0,hitTilt:Number(e.hitTilt)||13,
   shakeSerial:Number(e.shakeSerial)||0,shakePower:Number(e.shakePower)||0,
   deathStarted:e.deathStarted?1:0,""",
'Serialize shake SFX event'
)

replace_once(
""" if(options.shake){
   triggerHitCameraShake(target,options.shake,options.shakeDuration??.42);
 }""",
""" if(options.shake){
   target.shakeSerial=(Number(target.shakeSerial)||0)+1;
   target.shakePower=Number(options.shake)||12;
   triggerHitCameraShake(target,options.shake,options.shakeDuration??.42);
 }""",
'Shake event serial'
)

replace_once(
""" el._lastHitSerial=0;
 el._lastRegenSerial=0;""",
""" el._lastHitSerial=0;
 el._lastShakeSerial=Number(e.shakeSerial)||0;
 el._lastRegenSerial=0;""",
'Shake SFX visual baseline'
)

hit_anchor="""   if((el._lastHitSerial||0)!==(e.hitSerial||0)){
"""
shake_hook="""   if((el._lastShakeSerial||0)!==(e.shakeSerial||0)){
     el._lastShakeSerial=e.shakeSerial||0;
     if(e.shakeSerial>0){
       const shakeGain=clamp((Number(e.shakePower)||12)/22,.45,1);
       playWorldLayeredSfx('shake',e.x,e.y,shakeGain,90);
     }
   }

"""
if shake_hook not in t:
    if t.count(hit_anchor)!=1:
        raise SystemExit('Shake render anchor missing/duplicate')
    t=t.replace(hit_anchor,shake_hook+hit_anchor,1)

replace_once(
"""     if(el.dataset.mageAttackSerial!==String(e.mageAttackSerial)){
       el.dataset.mageAttackSerial=String(e.mageAttackSerial);
       if(e.mageAttackSerial>0&&special)restartGif(el._mageSpecial,el._gifKeys?.special||(e.variant==='female'?'femaleMageSpecial':'mageSpecial'),e.mageAttackSerial);
     }""",
"""     if(el.dataset.mageAttackSerial!==String(e.mageAttackSerial)){
       el.dataset.mageAttackSerial=String(e.mageAttackSerial);
       if(e.mageAttackSerial>0)playWorldLayeredSfx('mage',e.x,e.y,1,55);
       if(e.mageAttackSerial>0&&special)restartGif(el._mageSpecial,el._gifKeys?.special||(e.variant==='female'?'femaleMageSpecial':'mageSpecial'),e.mageAttackSerial);
     }""",
'Mage attack SFX'
)

replace_once(
""" updateGolemRockEffects(now);
 draw();

 const networkPushInterval=state.mode==='war'?120:120;""",
""" updateGolemRockEffects(now);
 draw();
 updateLayeredBattleSfx(now);

 const networkPushInterval=state.mode==='war'?120:120;""",
'Battle loop SFX update'
)

p.write_text(t,encoding='utf-8')

required=[
 "LAYERED SFX 2026-09-18",
 "assets/audio/sfx/click.mp3",
 "assets/audio/sfx/click2.mp3",
 "assets/audio/sfx/transition.mp3",
 "assets/audio/sfx/melee.mp3",
 "assets/audio/sfx/shake.mp3",
 "assets/audio/sfx/burn.mp3",
 "assets/audio/sfx/mage.mp3",
 "playLayeredSfx('transition',.75,0,260);",
 "button.classList.contains('plus')||button.classList.contains('minus')||button.id==='shopButton'",
 "MELEE_FIGHT_SFX_TYPES",
 "meleeFightSfxAttacking",
 "setLayeredLoop('melee'",
 "setLayeredLoop('burn'",
 "shakeSerial:Number(e.shakeSerial)||0",
 "target.shakeSerial=(Number(target.shakeSerial)||0)+1;",
 "playWorldLayeredSfx('shake'",
 "playWorldLayeredSfx('mage'",
 "updateLayeredBattleSfx(now);",
]
missing=[x for x in required if x not in t]
if missing:
    raise SystemExit('Missing layered SFX integration: '+repr(missing))
print('Layered UI and War battle SFX integration applied.')
