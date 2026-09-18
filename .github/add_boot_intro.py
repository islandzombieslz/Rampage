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

replace_once(
"""#bootLoader{position:fixed;inset:0;z-index:60000;background:#000;color:#fff;display:flex;align-items:center;justify-content:center;font-family:Arial,sans-serif;transition:opacity .22s ease;pointer-events:auto}
#bootLoader.done{opacity:0;pointer-events:none}
#bootLoaderBox{width:min(420px,78vw);text-align:center}
#bootLoaderTitle{font-size:14px;font-weight:800;letter-spacing:3px;margin-bottom:14px}
#bootLoaderPercent{font-size:34px;font-weight:900;font-variant-numeric:tabular-nums;margin-bottom:12px}
#bootLoaderTrack{height:8px;border:1px solid #555;background:#111;overflow:hidden;border-radius:999px}
#bootLoaderBar{height:100%;width:0%;background:#fff;transition:width .12s linear}""",
"""#bootLoader{position:fixed;inset:0;z-index:60000;background:#000;color:#fff;display:flex;align-items:center;justify-content:center;font-family:Arial,sans-serif;transition:opacity .22s ease;pointer-events:auto;overflow:hidden}
#bootLoader.done{opacity:0;pointer-events:none}
#bootLoaderBox{width:min(420px,78vw);text-align:center;position:relative;z-index:1}
#bootLoaderTitle{font-size:14px;font-weight:800;letter-spacing:3px;margin-bottom:14px}
#bootLoaderPercent{font-size:34px;font-weight:900;font-variant-numeric:tabular-nums;margin-bottom:12px}
#bootLoaderTrack{height:8px;border:1px solid #555;background:#111;overflow:hidden;border-radius:999px}
#bootLoaderBar{height:100%;width:0%;background:#fff;transition:width .12s linear}
#bootIntro{
  position:fixed;
  left:50%;
  top:50%;
  width:100vw;
  height:100vh;
  z-index:2;
  background:#000;
  overflow:hidden;
  opacity:1;
  transform:translate(-50%,-50%);
  transform-origin:center center;
  transition:opacity .55s ease;
  pointer-events:auto;
}
#bootIntro.fade-out{opacity:0;pointer-events:none}
/* Intro sempre horizontal: em portrait a camada inteira é girada,
   sem alterar a viewport do jogo. */
#bootIntro iframe{
  position:absolute;
  left:50%;
  top:50%;
  width:177.78vh;
  height:100vh;
  min-width:100vw;
  min-height:56.25vw;
  transform:translate(-50%,-50%);
  border:0;
  pointer-events:none;
  background:#000;
}""",
'Boot intro CSS'
)

replace_once(
"""<div id="bootLoader" role="status" aria-live="polite" aria-label="Carregando jogo">
  <div id="bootLoaderBox">""",
"""<div id="bootLoader" role="status" aria-live="polite" aria-label="Carregando jogo">
  <div id="bootIntro" aria-hidden="true"></div>
  <div id="bootLoaderBox">""",
'Boot intro HTML'
)

replace_once(
"""function playDesiredMusic({restart=false}={}){
 const mode=desiredMusicMode,next=musicFor(mode);""",
"""function playDesiredMusic({restart=false}={}){
 if(document.body?.classList.contains('booting'))return;
 const mode=desiredMusicMode,next=musicFor(mode);""",
'Defer music during boot'
)

boot_intro=r'''
/* ===== ALPHA YOUTUBE BOOT INTRO 2026-09-18 ===== */
const BOOT_INTRO_VIDEO_ID='j84JmKNz_5Q';
const BOOT_INTRO_PLAY_MS=12400;
let bootIntroFinished=false,bootIntroTimer=null,bootIntroFallbackTimer=null;
let bootIntroViewportCleanup=()=>{};
let resolveBootIntroDone=()=>{};
const bootIntroDone=new Promise(resolve=>{resolveBootIntroDone=resolve});

function syncBootIntroLandscape(){
 const intro=document.getElementById('bootIntro');
 if(!intro)return;
 const rawW=Math.max(1,window.innerWidth||document.documentElement.clientWidth||1);
 const rawH=Math.max(1,window.innerHeight||document.documentElement.clientHeight||1);
 const portrait=rawH>rawW;
 const viewW=portrait?rawH:rawW;
 const viewH=portrait?rawW:rawH;
 intro.style.left='50%';
 intro.style.top='50%';
 intro.style.width=viewW+'px';
 intro.style.height=viewH+'px';
 intro.style.transform='translate(-50%,-50%) rotate('+(portrait?'90deg':'0deg')+')';
 const frame=intro.querySelector('iframe');
 if(frame){
   const coverW=Math.max(viewW,viewH*(16/9));
   const coverH=coverW*(9/16);
   frame.style.left='50%';
   frame.style.top='50%';
   frame.style.width=coverW+'px';
   frame.style.height=coverH+'px';
   frame.style.transform='translate(-50%,-50%)';
 }
}
function bindBootIntroLandscape(){
 const sync=()=>requestAnimationFrame(syncBootIntroLandscape);
 window.addEventListener('resize',sync,{passive:true});
 window.addEventListener('orientationchange',sync,{passive:true});
 window.screen.orientation?.addEventListener?.('change',sync);
 bootIntroViewportCleanup=()=>{
   window.removeEventListener('resize',sync);
   window.removeEventListener('orientationchange',sync);
   window.screen.orientation?.removeEventListener?.('change',sync);
 };
 syncBootIntroLandscape();
 setTimeout(syncBootIntroLandscape,80);
 setTimeout(syncBootIntroLandscape,350);
}

function bootIntroCommand(frame,func,args=[]){
 try{
   frame?.contentWindow?.postMessage(JSON.stringify({event:'command',func,args}),'*');
 }catch(_){}
}
function finishBootIntro(){
 if(bootIntroFinished)return;
 bootIntroFinished=true;
 clearTimeout(bootIntroTimer);
 clearTimeout(bootIntroFallbackTimer);
 const intro=document.getElementById('bootIntro');
 if(!intro){bootIntroViewportCleanup();resolveBootIntroDone();return}
 intro.classList.add('fade-out');
 setTimeout(()=>{
   bootIntroViewportCleanup();
   intro.remove();
   resolveBootIntroDone();
 },560);
}
function startBootIntro(){
 const intro=document.getElementById('bootIntro');
 if(!intro){finishBootIntro();return}
 bindBootIntroLandscape();
 const frame=document.createElement('iframe');
 frame.id='bootIntroFrame';
 frame.title='Introdução - Alpha (Mestre da Guerra)';
 frame.tabIndex=-1;
 frame.setAttribute('allow','autoplay; encrypted-media');
 frame.setAttribute('referrerpolicy','strict-origin-when-cross-origin');
 frame.setAttribute('aria-hidden','true');
 frame.addEventListener('load',()=>{
   const kick=()=>{
     bootIntroCommand(frame,'unMute');
     bootIntroCommand(frame,'setVolume',[100]);
     bootIntroCommand(frame,'playVideo');
   };
   kick();setTimeout(kick,260);setTimeout(kick,900);
   clearTimeout(bootIntroTimer);
   bootIntroTimer=setTimeout(finishBootIntro,BOOT_INTRO_PLAY_MS);
 },{once:true});
 const origin=encodeURIComponent(location.origin);
 frame.src='https://www.youtube-nocookie.com/embed/'+BOOT_INTRO_VIDEO_ID+
   '?autoplay=1&mute=0&controls=0&disablekb=1&fs=0&playsinline=1&rel=0&modestbranding=1&iv_load_policy=3&cc_load_policy=0&enablejsapi=1&origin='+origin;
 intro.appendChild(frame);
 syncBootIntroLandscape();
 try{requestGameFullscreenLandscape().catch(()=>{})}catch(_){}
 bootIntroFallbackTimer=setTimeout(finishBootIntro,16000);
}
'''
insert_after("function setBootTitle(text){const el=document.getElementById('bootLoaderTitle');if(el)el.textContent=text}\n",boot_intro,'Boot intro controller')

old_finish=""" if(failed&&typeof assetWarning!=='undefined'&&assetWarning){
   assetWarning.textContent=`${failed} recurso(s) não puderam ser atualizados.`;
   assetWarning.classList.add('show');
 }
 document.body.classList.remove('booting');
 const loader=document.getElementById('bootLoader');
 if(loader){loader.classList.add('done');setTimeout(()=>loader.remove(),120)}
}"""
new_finish=""" if(failed&&typeof assetWarning!=='undefined'&&assetWarning){
   assetWarning.textContent=`${failed} recurso(s) não puderam ser atualizados.`;
   assetWarning.classList.add('show');
 }
 // O carregamento nunca pausa: apenas seguramos a SAÍDA visual até a intro terminar.
 await bootIntroDone;
 await new Promise(resolve=>setTimeout(resolve,220));
 document.body.classList.remove('booting');
 const loader=document.getElementById('bootLoader');
 if(loader){loader.classList.add('done');setTimeout(()=>loader.remove(),120)}
 playDesiredMusic({restart:true});
}"""
replace_once(old_finish,new_finish,'Boot visual gate')

replace_once(
"""requestAnimationFrame(loop);
runBootLoader().catch(err=>{console.error(err);document.body.classList.remove('booting');document.getElementById('bootLoader')?.remove()});""",
"""requestAnimationFrame(loop);
startBootIntro();
runBootLoader().catch(async err=>{
 console.error(err);
 await bootIntroDone.catch(()=>{});
 document.body.classList.remove('booting');
 document.getElementById('bootLoader')?.remove();
 playDesiredMusic({restart:true});
});""",
'Boot intro start'
)

# Transition audio: keep fade, but no transition SFX from initial menu or into gameplay.
old_fade="""function screenWithFade(id){
 if(screenTransitionBusy){queuedScreenId=id;return}
 const fade=$('#screenTransitionFade');
 if(!fade){screen(id);return}
 playLayeredSfx('transition',.75,0,260);
 screenTransitionBusy=true;fade.classList.add('show');"""
new_fade="""function screenWithFade(id,playTransitionSound=true){
 if(screenTransitionBusy){queuedScreenId=id;return}
 const fade=$('#screenTransitionFade');
 if(!fade){screen(id);return}
 if(playTransitionSound)playLayeredSfx('transition',.75,0,260);
 screenTransitionBusy=true;fade.classList.add('show');"""
replace_once(old_fade,new_fade,'Conditional transition SFX')

old_nav=""" // Qualquer entrada, saída ou troca entre menus recebe fade-out + fade-in.
 if(MENU_SCREEN_IDS.has(current)||MENU_SCREEN_IDS.has(id))screenWithFade(id);
 else screen(id);"""
new_nav=""" // O fade visual continua em todas as trocas; o SFX toca somente ENTRE menus internos.
 // Não toca ao sair do menu inicial nem quando a navegação entra na partida.
 const transitionSound=MENU_SCREEN_IDS.has(current)&&MENU_SCREEN_IDS.has(id)&&current!=='menuScreen';
 if(MENU_SCREEN_IDS.has(current)||MENU_SCREEN_IDS.has(id))screenWithFade(id,transitionSound);
 else screen(id);"""
replace_once(old_nav,new_nav,'Transition audio navigation rule')

p.write_text(t,encoding='utf-8')

required=[
    "BOOT_INTRO_VIDEO_ID='j84JmKNz_5Q'",
    "youtube-nocookie.com/embed/",
    "controls=0&disablekb=1",
    "frame.setAttribute('allow','autoplay; encrypted-media')",
    "bootIntroCommand(frame,'unMute')",
    "bootIntroCommand(frame,'setVolume',[100])",
    "await bootIntroDone;",
    "startBootIntro();",
    "function syncBootIntroLandscape(){",
    "const viewW=portrait?rawH:rawW;",
    "const coverW=Math.max(viewW,viewH*(16/9));",
    "bindBootIntroLandscape();",
    "syncBootIntroLandscape();",
    "width:100vw;",
    "height:100vh;",
    "current!=='menuScreen'",
    "screenWithFade(id,transitionSound)",
]
missing=[x for x in required if x not in t]
if missing:
    raise SystemExit('Missing boot intro/menu SFX behavior: '+repr(missing))
intro=t[t.index("/* ===== ALPHA YOUTUBE BOOT INTRO 2026-09-18 ===== */"):t.index('function bootReadSavedManifest')]
forbidden=['window.visualViewport','applyLandscapeFallback()','try{resize()}']
bad=[x for x in forbidden if x in intro]
if bad:
    raise SystemExit('Boot intro must stay isolated from game viewport: '+repr(bad))
print('Alpha boot intro and transition sound rules applied.')

# retrigger after workflow race fix
