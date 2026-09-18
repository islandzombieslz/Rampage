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

# Layered SFX system. Web Audio keeps these effects independent from menu/battle music.
music_anchor="""battleMusic.volume=.82;
"""
sfx_system=r'''
/* ==================== LAYERED SFX 2026-09-18 ==================== */
const SFX_SPRITE_URL='assets/audio/rampage-sfx.mp3';
const SFX_CUES=Object.freeze({
 click2:{start:0.000,duration:0.183},
 click:{start:0.253,duration:0.157},
 transition:{start:0.480,duration:2.116},
 fight:{start:2.666,duration:6.243},
 quake:{start:8.979,duration:2.220},
 fire:{start:11.269,duration:2.377},
 mage:{start:13.716,duration:4.650}
});
let sfxContext=null,sfxBuffer=null,sfxDecodePromise=null;
let sfxArrayBufferPromise=fetch(SFX_SPRITE_URL,{cache:'force-cache'}).then(r=>{
 if(!r.ok)throw Error('SFX sprite '+r.status);
 return r.arrayBuffer();
}).catch(err=>{console.warn('SFX preload failed',err);return null});
const sfxLastPlay=new Map();
const sfxLoopChannels=new Map();
let layeredBattleSfxLastUpdate=0;
const MELEE_FIGHT_SFX_TYPES=new Set(['warrior','brownWarrior','king','golem','naja','anubis']);

function getSfxContext(){
 if(!sfxContext){
   const AC=window.AudioContext||window.webkitAudioContext;
   if(!AC)return null;
   sfxContext=new AC();
 }
 if(sfxContext.state==='suspended')sfxContext.resume().catch(()=>{});
 return sfxContext;
}
async function ensureSfxReady(){
 const ctx=getSfxContext();if(!ctx)return null;
 if(sfxBuffer)return sfxBuffer;
 if(!sfxDecodePromise){
   sfxDecodePromise=(async()=>{
     const raw=await sfxArrayBufferPromise;
     if(!raw)return null;
     try{
       sfxBuffer=await ctx.decodeAudioData(raw.slice(0));
       return sfxBuffer;
     }catch(err){console.warn('SFX decode failed',err);return null}
   })();
 }
 return sfxDecodePromise;
}
function sfxZoomGain(){
 if(state.mode!=='war')return 1;
 const z=Number(state.camera?.zoom)||1;
 const t=clamp((z-.55)/(2.15-.55),0,1);
 return .035+.965*Math.pow(t,1.55);
}
function worldSfxMix(x,y){
 if(state.mode!=='war')return {gain:1,pan:0};
 const z=Number(state.camera?.zoom)||1,vp=gameViewportSize();
 const sx=(Number(x)-Number(state.camera.x||0))*z;
 const sy=(Number(y)-Number(state.camera.y||0))*z;
 const cx=vp.w*.5,cy=vp.h*.5;
 const dist=Math.hypot(sx-cx,sy-cy);
 const radius=Math.hypot(vp.w,vp.h)*.72;
 const spatial=Math.pow(clamp(1-dist/radius,0,1),.72);
 const pan=clamp((sx-cx)/Math.max(1,vp.w*.52),-1,1);
 return {gain:sfxZoomGain()*spatial,pan};
}
async function playSfxCue(name,volume=1,pan=0,cooldownMs=0){
 const cue=SFX_CUES[name];if(!cue)return;
 const now=performance.now(),last=Number(sfxLastPlay.get(name))||0;
 if(cooldownMs&&now-last<cooldownMs)return;
 sfxLastPlay.set(name,now);
 const buffer=await ensureSfxReady(),ctx=sfxContext;
 if(!buffer||!ctx||ctx.state!=='running')return;
 const src=ctx.createBufferSource(),gain=ctx.createGain();
 src.buffer=buffer;gain.gain.value=clamp(volume,0,1);
 src.connect(gain);
 if(ctx.createStereoPanner){
   const panner=ctx.createStereoPanner();panner.pan.value=clamp(pan,-1,1);
   gain.connect(panner);panner.connect(ctx.destination);
 }else gain.connect(ctx.destination);
 src.start(0,cue.start,Math.min(cue.duration,Math.max(.01,buffer.duration-cue.start)));
}
function playWorldSfx(name,x,y,baseVolume=1,cooldownMs=0){
 const m=worldSfxMix(x,y);
 if(m.gain<=.008)return;
 playSfxCue(name,baseVolume*m.gain,m.pan,cooldownMs);
}
async function setLoopSfx(name,volume,pan=0){
 const cue=SFX_CUES[name];if(!cue)return;
 const target=clamp(volume,0,1);
 let ch=sfxLoopChannels.get(name);
 if(!ch&&target>.005){
   const buffer=await ensureSfxReady(),ctx=sfxContext;
   if(!buffer||!ctx||ctx.state!=='running')return;
   // Condition might have vanished while decoding.
   ch=sfxLoopChannels.get(name);
   if(!ch){
     const src=ctx.createBufferSource(),gain=ctx.createGain();
     src.buffer=buffer;src.loop=true;src.loopStart=cue.start;src.loopEnd=cue.start+cue.duration;
     gain.gain.value=0;src.connect(gain);
     let panner=null;
     if(ctx.createStereoPanner){panner=ctx.createStereoPanner();gain.connect(panner);panner.connect(ctx.destination)}
     else gain.connect(ctx.destination);
     src.start(0,cue.start);
     ch={src,gain,panner};sfxLoopChannels.set(name,ch);
   }
 }
 if(!ch)return;
 const ctx=sfxContext;
 ch.gain.gain.cancelScheduledValues(ctx.currentTime);
 ch.gain.gain.setTargetAtTime(target,ctx.currentTime,target>0?.07:.12);
 if(ch.panner)ch.panner.pan.setTargetAtTime(clamp(pan,-1,1),ctx.currentTime,.08);
}
function stopBattleSfxLoops(){
 setLoopSfx('fight',0,0);
 setLoopSfx('fire',0,0);
}
function meleeFightSoundCandidate(e){
 if(!e?.alive||!MELEE_FIGHT_SFX_TYPES.has(e.type))return false;
 if(e.type==='naja'&&najaIsUnderground(e))return false;
 if(e.type==='anubis'&&e.pendingAnubisAttack?.kind==='ranged')return false;
 return true;
}
function bestMeleeFightCluster(){
 const fighters=state.entities.filter(meleeFightSoundCandidate);
 if(fighters.length<4)return null;
 const engageSq=140*140,linkSq=205*205;
 const engaged=fighters.filter(a=>fighters.some(b=>{
   if(a===b||a.team===b.team)return false;
   const dx=a.x-b.x,dy=a.y-b.y;return dx*dx+dy*dy<=engageSq;
 }));
 if(engaged.length<4)return null;
 const seen=new Set();let best=null,bestScore=0;
 for(const seed of engaged){
   if(seen.has(seed.id))continue;
   const stack=[seed],group=[];seen.add(seed.id);
   while(stack.length){
     const a=stack.pop();group.push(a);
     for(const b of engaged){
       if(seen.has(b.id))continue;
       const dx=a.x-b.x,dy=a.y-b.y;
       if(dx*dx+dy*dy<=linkSq){seen.add(b.id);stack.push(b)}
     }
   }
   if(group.length<4||new Set(group.map(e=>e.team)).size<2)continue;
   let crossCombat=false;
   for(let i=0;i<group.length&&!crossCombat;i++)for(let j=i+1;j<group.length;j++){
     if(group[i].team===group[j].team)continue;
     const dx=group[i].x-group[j].x,dy=group[i].y-group[j].y;
     if(dx*dx+dy*dy<=engageSq){crossCombat=true;break}
   }
   if(!crossCombat)continue;
   const x=group.reduce((s,e)=>s+e.x,0)/group.length;
   const y=group.reduce((s,e)=>s+e.y,0)/group.length;
   const mix=worldSfxMix(x,y);
   const score=mix.gain*(1+Math.min(8,group.length-4)*.06);
   if(score>bestScore){bestScore=score;best={x,y,count:group.length,mix}}
 }
 return best;
}
function bestBurnSoundSource(now){
 let best=null,bestGain=0,count=0;
 for(const e of state.entities){
   if(!e.alive||Number(e.dragonBurnUntil||0)<=now)continue;
   count++;
   const mix=worldSfxMix(e.x,e.y);
   if(mix.gain>bestGain){bestGain=mix.gain;best={x:e.x,y:e.y,mix}}
 }
 if(best)best.count=count;
 return best;
}
function updateLayeredBattleSfx(now){
 if(now-layeredBattleSfxLastUpdate<110)return;
 layeredBattleSfxLastUpdate=now;
 if(state.mode!=='war'||!state.running||state.phase!=='combat'){
   stopBattleSfxLoops();return;
 }
 const fight=bestMeleeFightCluster();
 if(fight){
   const density=Math.min(1,.76+(fight.count-4)*.045);
   setLoopSfx('fight',fight.mix.gain*density,fight.mix.pan);
 }else setLoopSfx('fight',0,0);
 const burn=bestBurnSoundSource(now);
 if(burn){
   const amount=Math.min(1,.78+Math.max(0,burn.count-1)*.055);
   setLoopSfx('fire',burn.mix.gain*amount,burn.mix.pan);
 }else setLoopSfx('fire',0,0);
}

// Unlock/decode on the first real gesture and route UI click sounds without
// touching the existing menu/battle music elements.
document.addEventListener('pointerdown',ev=>{
 getSfxContext();ensureSfxReady();
 const b=ev.target.closest?.('button');
 if(!b||b.disabled||b.id==='attackBtn')return;
 if(b.classList.contains('plus')||b.classList.contains('minus')||b.id==='shopButton'){
   playSfxCue('click2',.46,0,28);
 }else{
   playSfxCue('click',.42,0,24);
 }
},{capture:true,passive:true});
'''
insert_after(music_anchor,sfx_system,'Layered SFX engine')

# Every actual menu fade starts the transition sound once.
replace_once(
"""function screenWithFade(id){
 if(screenTransitionBusy){queuedScreenId=id;return}
 const fade=$('#screenTransitionFade');""",
"""function screenWithFade(id){
 if(screenTransitionBusy){queuedScreenId=id;return}
 playSfxCue('transition',1,0,320);
 const fade=$('#screenTransitionFade');""",
'Menu transition SFX'
)

# Networked quake event state.
replace_once(
""" hitSerial:0,hitDirX:0,hitDirY:0,hitTilt:13,knockVX:0,knockVY:0,knockTime:0,""",
""" hitSerial:0,hitDirX:0,hitDirY:0,hitTilt:13,shakeSerial:0,shakePower:0,knockVX:0,knockVY:0,knockTime:0,""",
'Entity quake state'
)
replace_once(
"""   hitSerial:Number(e.hitSerial)||0,hitDirX:Number(e.hitDirX)||0,hitDirY:Number(e.hitDirY)||0,hitTilt:Number(e.hitTilt)||13,""",
"""   hitSerial:Number(e.hitSerial)||0,hitDirX:Number(e.hitDirX)||0,hitDirY:Number(e.hitDirY)||0,hitTilt:Number(e.hitTilt)||13,
   shakeSerial:Number(e.shakeSerial)||0,shakePower:Number(e.shakePower)||0,""",
'Serialize quake state'
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
'Quake event serial'
)

# New visual nodes start with the current quake serial, avoiding stale sounds on join/camera reveal.
replace_once(
""" el._lastHitSerial=0;
 el._lastRegenSerial=0;""",
""" el._lastHitSerial=0;
 el._lastShakeSerial=Number(e.shakeSerial)||0;
 el._lastRegenSerial=0;""",
'Quake visual baseline'
)

# Visible networked quake events play once at the affected world position.
hit_anchor="""   if((el._lastHitSerial||0)!==(e.hitSerial||0)){
"""
quake_hook="""   if((el._lastShakeSerial||0)!==(e.shakeSerial||0)){
     el._lastShakeSerial=e.shakeSerial||0;
     if(e.shakeSerial>0){
       const power=clamp((Number(e.shakePower)||12)/22,.45,1);
       playWorldSfx('quake',e.x,e.y,.95*power,90);
     }
   }

"""
if quake_hook not in t:
    if hit_anchor not in t: raise SystemExit('Quake render anchor missing')
    t=t.replace(hit_anchor,quake_hook+hit_anchor,1)

# Any Mage normal or special attack gets its spatial one-shot, including remote players.
replace_once(
"""     if(el.dataset.mageAttackSerial!==String(e.mageAttackSerial)){
       el.dataset.mageAttackSerial=String(e.mageAttackSerial);
       if(e.mageAttackSerial>0&&special)restartGif(el._mageSpecial,el._gifKeys?.special||(e.variant==='female'?'femaleMageSpecial':'mageSpecial'),e.mageAttackSerial);
     }""",
"""     if(el.dataset.mageAttackSerial!==String(e.mageAttackSerial)){
       el.dataset.mageAttackSerial=String(e.mageAttackSerial);
       if(e.mageAttackSerial>0)playWorldSfx('mage',e.x,e.y,.92,70);
       if(e.mageAttackSerial>0&&special)restartGif(el._mageSpecial,el._gifKeys?.special||(e.variant==='female'?'femaleMageSpecial':'mageSpecial'),e.mageAttackSerial);
     }""",
'Mage attack SFX'
)

# Update area loops after the camera/game render is current.
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
 "const SFX_SPRITE_URL='assets/audio/rampage-sfx.mp3';",
 "playSfxCue('transition',1,0,320);",
 "b.classList.contains('plus')||b.classList.contains('minus')||b.id==='shopButton'",
 "const MELEE_FIGHT_SFX_TYPES=new Set(['warrior','brownWarrior','king','golem','naja','anubis']);",
 "setLoopSfx('fight'",
 "setLoopSfx('fire'",
 "shakeSerial:Number(e.shakeSerial)||0",
 "target.shakeSerial=(Number(target.shakeSerial)||0)+1;",
 "playWorldSfx('quake'",
 "playWorldSfx('mage'",
 "updateLayeredBattleSfx(now);",
]
missing=[x for x in required if x not in t]
if missing: raise SystemExit('Missing layered SFX integration: '+repr(missing))
print('Layered UI and battle SFX integration applied.')
