from pathlib import Path
import re

path=Path('index.html')
text=path.read_text(encoding='utf-8')
original=text

def replace_once(old,new,label):
    global text
    count=text.count(old)
    if count!=1:
        raise SystemExit(f'{label}: esperado 1 marcador, encontrado {count}')
    text=text.replace(old,new,1)

def regex_once(pattern,replacement,label,flags=re.S):
    global text
    text,count=re.subn(pattern,replacement,text,count=1,flags=flags)
    if count!=1:
        raise SystemExit(f'{label}: bloco nao encontrado')

# Audio local: menu carrega cedo; batalha fica preparada sem bloquear a tela inicial.
asset_marker='<link rel="prefetch" as="image" href="assets/ui/war-shop/card-dragao-guerreiro.png">\n'
replace_once(asset_marker,asset_marker+'<link rel="preload" as="audio" href="assets/audio/tema-menu.mp3">\n<link rel="prefetch" as="audio" href="assets/audio/som-batalha.mp3">\n','links de audio')

root_marker='<div id="landscapeRoot" class="force-landscape">\n'
replace_once(root_marker,root_marker+'<audio id="menuMusic" src="assets/audio/tema-menu.mp3" preload="auto" playsinline hidden></audio>\n<audio id="battleMusic" src="assets/audio/som-batalha.mp3" preload="auto" playsinline hidden></audio>\n','elementos de audio')

replace_once('const DRAGON_CLOSE_RANGE=175;\n','const DRAGON_CLOSE_RANGE=175;\nconst DRAGON_FIREBALL_RELEASE_DELAY_MS=1000;\n','constante do atraso do Dragao')

# Gerenciador independente de trilha. Nao reinicia ao navegar entre menus.
music_code=r'''
/* ==================== TRILHA SONORA ==================== */
const menuMusicEl=$('#menuMusic');
const battleMusicEl=$('#battleMusic');
const MUSIC_CROSSFADE_MS=700;
const MUSIC_LOOP_FADE_MS=1700;
const MUSIC_LOOP_FADE_SECONDS=2;
const MUSIC_VOLUME={menu:.30,battle:.38};
const musicFadeTokens=new WeakMap();
const musicTailFading=new WeakSet();
let desiredMusicMode='menu';
let activeMusicEl=null;

function musicElementFor(mode){return mode==='battle'?battleMusicEl:menuMusicEl}
function fadeMusicVolume(audio,target,duration,onDone){
 if(!audio)return;
 const token=(musicFadeTokens.get(audio)||0)+1;
 musicFadeTokens.set(audio,token);
 const from=Number.isFinite(audio.volume)?audio.volume:0;
 const start=performance.now();
 const step=now=>{
   if(musicFadeTokens.get(audio)!==token)return;
   const p=clamp((now-start)/Math.max(1,duration),0,1);
   const eased=p*p*(3-2*p);
   audio.volume=clamp(from+(target-from)*eased,0,1);
   if(p<1)requestAnimationFrame(step);else onDone?.();
 };
 requestAnimationFrame(step);
}
function startDesiredMusic(restart=false){
 const mode=desiredMusicMode;
 const next=musicElementFor(mode);
 if(!next)return;
 if(activeMusicEl===next&&!next.paused){
   fadeMusicVolume(next,MUSIC_VOLUME[mode],260);
   return;
 }
 const previous=activeMusicEl;
 activeMusicEl=next;
 musicTailFading.delete(next);
 if(restart||next.ended||!Number.isFinite(next.currentTime))next.currentTime=0;
 next.loop=false;
 next.volume=0;
 const playResult=next.play();
 Promise.resolve(playResult).then(()=>{
   if(activeMusicEl===next)fadeMusicVolume(next,MUSIC_VOLUME[mode],MUSIC_CROSSFADE_MS);
 }).catch(()=>{
   // Autoplay pode ser bloqueado. O proximo toque/tecla tenta novamente.
   if(activeMusicEl===next)activeMusicEl=null;
 });
 if(previous&&previous!==next&&!previous.paused){
   fadeMusicVolume(previous,0,MUSIC_CROSSFADE_MS,()=>{
     if(activeMusicEl!==previous){previous.pause();previous.currentTime=0;musicTailFading.delete(previous)}
   });
 }
}
function setGameMusicMode(mode){
 const normalized=mode==='battle'?'battle':'menu';
 const next=musicElementFor(normalized);
 const restart=activeMusicEl!==next;
 desiredMusicMode=normalized;
 startDesiredMusic(restart);
}
function retryDesiredMusicFromGesture(){
 const desired=musicElementFor(desiredMusicMode);
 if(!desired||activeMusicEl!==desired||desired.paused)startDesiredMusic(false);
}
function handleMusicTail(audio,mode){
 if(audio!==activeMusicEl||desiredMusicMode!==mode||audio.paused||musicTailFading.has(audio))return;
 if(!Number.isFinite(audio.duration)||audio.duration<=0)return;
 const remaining=audio.duration-audio.currentTime;
 if(remaining>0&&remaining<=MUSIC_LOOP_FADE_SECONDS){
   musicTailFading.add(audio);
   fadeMusicVolume(audio,0,Math.max(180,remaining*1000));
 }
}
function restartCompletedMusic(audio,mode){
 if(audio!==activeMusicEl||desiredMusicMode!==mode)return;
 musicTailFading.delete(audio);
 audio.currentTime=0;
 audio.volume=0;
 const playResult=audio.play();
 Promise.resolve(playResult).then(()=>{
   if(audio===activeMusicEl&&desiredMusicMode===mode)fadeMusicVolume(audio,MUSIC_VOLUME[mode],MUSIC_LOOP_FADE_MS);
 }).catch(()=>{if(audio===activeMusicEl)activeMusicEl=null});
}
for(const [mode,audio] of [['menu',menuMusicEl],['battle',battleMusicEl]]){
 if(!audio)continue;
 audio.loop=false;
 audio.addEventListener('timeupdate',()=>handleMusicTail(audio,mode));
 audio.addEventListener('ended',()=>restartCompletedMusic(audio,mode));
}
document.addEventListener('pointerdown',retryDesiredMusicFromGesture,{capture:true});
document.addEventListener('touchstart',retryDesiredMusicFromGesture,{capture:true,passive:true});
document.addEventListener('keydown',retryDesiredMusicFromGesture,{capture:true});
// Tenta iniciar no carregamento; navegadores que bloquearem liberam no primeiro gesto.
startDesiredMusic(true);

'''
replace_once('function generateCode(){ return Math.random().toString(36).slice(2,8).toUpperCase(); }',music_code+'function generateCode(){ return Math.random().toString(36).slice(2,8).toUpperCase(); }','gerenciador de musica')

# O estado de ataque nasce imediatamente, mas o projetil so e criado apos 1 segundo.
update_state=r'''function updateDragonState(e,now=performance.now()){
           if(!e||e.type!=='dragon')return;
           if(e.dragonFlightState==='takeoff'&&now>=(e.dragonTakeoffEndAt||0)){
             e.dragonFlightState='flying';e.dragonTakeoffEndAt=0;e.dragonTakeoffStartedAt=0;
             e.dragonNextShotAt=Math.max(Number(e.dragonNextShotAt)||0,now+150);
           }
           if(e.pendingDragonAttack){
             const pending=e.pendingDragonAttack;
             if(!pending.released&&now>=Number(pending.releaseAt||0))releasePendingDragonFireball(e,pending,now);
             if(now>=Number(pending.endAt||0))e.pendingDragonAttack=null;
           }
          }
          function igniteDragonBurn'''
regex_once(r"function updateDragonState\(e,now=performance\.now\(\)\)\{.*?\n\s*\}\n\s*function igniteDragonBurn",update_state,'updateDragonState')

launch_block=r'''function releasePendingDragonFireball(e,pending,now=performance.now()){
           if(!e?.alive||e.type!=='dragon'||!pending||pending.released)return false;
           pending.released=true;
           const target=state.entities.find(t=>t.id===pending.targetId&&t.alive&&t.team!==e.team);
           const tx=Number(target?.x??pending.targetX),ty=Number(target?.y??pending.targetY);
           if(!Number.isFinite(tx)||!Number.isFinite(ty))return false;
           const angle=Math.atan2(ty-e.y,tx-e.x);
           e.heading=angle;if(Math.abs(tx-e.x)>4)e.facing=tx<e.x?-1:1;
           const startX=e.x+Math.cos(angle)*42,startY=e.y-16+Math.sin(angle)*18;
           state.dragonProjectiles.push({id:'df_'+(++state.dragonProjectileSeq),serial:Number(pending.serial)||e.dragonAttackSerial,x:startX,y:startY,vx:Math.cos(angle)*DRAGON_FIREBALL_SPEED,vy:Math.sin(angle)*DRAGON_FIREBALL_SPEED,targetId:target?.id??pending.targetId,targetX:tx,targetY:ty,team:e.team,sourceId:e.id,createdAt:now,expireAt:now+4500});
           return true;
          }
          function launchDragonFireball(e,target,{emergency=false}={}){
           if(!e?.alive||e.type!=='dragon'||e.dragonFlightState!=='flying'||!target?.alive)return false;
           const now=performance.now();
           const gate=emergency?(Number(e.dragonCloseShotAt)||0):(Number(e.dragonNextShotAt)||0);
           if(now<gate)return false;
           const angle=Math.atan2(target.y-e.y,target.x-e.x);e.heading=angle;if(Math.abs(target.x-e.x)>4)e.facing=target.x<e.x?-1:1;
           e.moving=false;e.dragonAttackSerial=(e.dragonAttackSerial||0)+1;
           e.pendingDragonAttack={
             serial:e.dragonAttackSerial,startedAt:now,
             releaseAt:now+DRAGON_FIREBALL_RELEASE_DELAY_MS,
             endAt:now+Math.max(DRAGON_ATTACK_VISUAL_MS,DRAGON_FIREBALL_RELEASE_DELAY_MS+150),
             emergency:!!emergency,released:false,
             targetId:target.id,targetX:target.x,targetY:target.y,angle
           };
           if(emergency){
             e.dragonCloseShotAt=now+DRAGON_CLOSE_SHOT_COOLDOWN_MS;
             e.dragonNextShotAt=Math.max(Number(e.dragonNextShotAt)||0,now+DRAGON_SHOT_COOLDOWN_MS);
           }else{
             e.dragonNextShotAt=now+DRAGON_SHOT_COOLDOWN_MS;
             // O tiro normal tambem ocupa a janela do disparo de emergencia.
             e.dragonCloseShotAt=Math.max(Number(e.dragonCloseShotAt)||0,now+DRAGON_CLOSE_SHOT_COOLDOWN_MS);
           }
           return true;
          }
          function updateDragonProjectiles'''
regex_once(r"function launchDragonFireball\(e,target,\{emergency=false\}=\{\}\)\{.*?\n\s*\}\n\s*function updateDragonProjectiles",launch_block,'launchDragonFireball')

serialize_old="""   if(out.pendingDragonAttack){
     out.pendingDragonAttack={...out.pendingDragonAttack,remainingMs:Math.max(0,out.pendingDragonAttack.endAt-now)};
   }"""
serialize_new="""   if(out.pendingDragonAttack){
     const pending={
       ...out.pendingDragonAttack,
       remainingMs:Math.max(0,out.pendingDragonAttack.endAt-now),
       releaseRemainingMs:Math.max(0,(out.pendingDragonAttack.releaseAt||now)-now)
     };
     delete pending.startedAt;delete pending.releaseAt;delete pending.endAt;
     out.pendingDragonAttack=pending;
   }"""
replace_once(serialize_old,serialize_new,'serializacao do ataque do Dragao')

remote_old="""     if(out.pendingDragonAttack?.remainingMs!=null){
       const remaining=Math.max(0,Number(out.pendingDragonAttack.remainingMs)||0);
       out.pendingDragonAttack={...out.pendingDragonAttack,endAt:localNow+remaining};
     }"""
remote_new="""     if(out.pendingDragonAttack?.remainingMs!=null){
       const remaining=Math.max(0,Number(out.pendingDragonAttack.remainingMs)||0);
       const releaseRemaining=Math.max(0,Number(out.pendingDragonAttack.releaseRemainingMs)||0);
       out.pendingDragonAttack={...out.pendingDragonAttack,releaseAt:localNow+releaseRemaining,endAt:localNow+remaining};
     }"""
replace_once(remote_old,remote_new,'desserializacao do ataque do Dragao')

# Troca de trilha somente ao entrar/sair de uma partida; menus nao reiniciam o tema.
replace_once('function startPVE(){\n state.round=1;','function startPVE(){\n setGameMusicMode(\'battle\');\n state.round=1;','musica ao iniciar PVE')
replace_once('function startWarMode(){\n state.round=1;','function startWarMode(){\n setGameMusicMode(\'battle\');\n state.round=1;','musica ao iniciar Guerra')
replace_once("if(firstFrame){navigateScreen('gameScreen');configureGameScreenForMode();if(state.mode==='war')beginWarCameraIntro()}","if(firstFrame){setGameMusicMode('battle');navigateScreen('gameScreen');configureGameScreenForMode();if(state.mode==='war')beginWarCameraIntro()}",'musica em cliente remoto')
replace_once("setTimeout(()=>{navigateScreen('menuScreen');state.entities=[];state.particles=[];state.dragonProjectiles=[];clearEntityVisuals();$('#shop').classList.remove('open')},4200);","setTimeout(()=>{setGameMusicMode('menu');navigateScreen('menuScreen');state.entities=[];state.particles=[];state.dragonProjectiles=[];clearEntityVisuals();$('#shop').classList.remove('open')},4200);",'retorno da musica de menu')

if text==original:
    raise SystemExit('nenhuma alteracao aplicada')
path.write_text(text,encoding='utf-8')
print('Dragon timing and soundtrack patch applied')
