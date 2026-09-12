from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')
orig=s

def rep(old,new,count=1):
    global s
    found=s.count(old)
    if found < count:
        raise SystemExit(f'guard missing: expected at least {count}, found {found}: {old[:120]!r}')
    s=s.replace(old,new,count)

# 1) CSS: lightweight static posters + heavy-mode paint reductions.
marker='/* ===== BOOT LOADER 2026-09-12 ===== */'
lod_css='''/* ===== WAR ADAPTIVE VISUAL LOD 2026-09-12 ===== */
.entity-lod-poster{
  display:none;
  opacity:0;
  z-index:2;
  object-fit:contain;
  pointer-events:none;
}
.entity-visual.entity-lod-static .entity-lod-poster{
  display:block !important;
  opacity:1 !important;
  visibility:visible !important;
}
/* Quando o LOD está ativo, o poster WebP substitui os GIFs do corpo. */
.entity-visual.entity-lod-static .entity-facing > img:not(.entity-lod-poster){
  display:none !important;
  opacity:0 !important;
}
/* Em carga pesada também eliminamos pequenas pinturas/filters que somam muito
   quando dezenas de tropas estão visíveis. A lógica do combate não muda. */
#gameScreen.war-lod-heavy .entity-bars{display:none !important}
#gameScreen.war-lod-heavy .entity-slash{display:none !important}
#gameScreen.war-lod-heavy .entity-facing.hit-react,
#gameScreen.war-lod-heavy .entity-facing.hit-react-alt{animation:none !important;filter:none !important}
#gameScreen.war-lod-heavy .dragon-burn-layer{display:none !important}
#gameScreen.war-lod-heavy .entity-visual.entity-lod-static .entity-weapon-facing{display:none !important}

'''
rep(marker,lod_css+marker)

# 2) Reduce only the visual rock count according to current LOD.
rep(''' const count=16;
''',''' const count=warVisualLodLevel>=2?6:warVisualLodLevel===1?10:16;
''')

# 3) Add LOD engine near reusable render structures.
needle='''const dragonProjectileActiveIds=new Set();

const DRAGON_PROJECTILE_GIF_GRACE_MS=850;'''
lod_js=r'''const dragonProjectileActiveIds=new Set();

/* WAR ADAPTIVE VISUAL LOD 2026-09-12
   CSS scale não reduz o custo de decodificar um GIF 800x800. Em zoom distante
   ou com muitas tropas, usamos um poster estático ~128 px gerado uma vez no
   próprio navegador a partir do asset já cacheado. A simulação continua igual. */
const WAR_LOD_MEDIUM_COUNT=8;
const WAR_LOD_HEAVY_COUNT=13;
const WAR_LOD_MEDIUM_ZOOM=.84;
const WAR_LOD_HEAVY_ZOOM=.64;
const WAR_LOD_HEAVY_ATTACK_BUDGET=4;
const WAR_LOD_RECOVER_MS=1800;
const WAR_LOD_MEDIUM_SYNC_MS=22;
const WAR_LOD_HEAVY_SYNC_MS=34;
const WAR_LOD_POSTER_MAX_SIDE=128;
const WAR_LOD_POSTER_KEYS=Object.freeze([
  'idle','femaleIdle','brownIdle','kingIdle','golemIdle',
  'mageIdle','femaleMageIdle','dragonGround','dragonFly'
]);
const warLodPosterUrls=new Map();
const warLodPosterPromises=new Map();
let warVisualLodLevel=0;
let warVisualLodRecoverSince=0;
let warVisualSyncLastAt=0;

function warLodPosterKeyForEntity(e){
 if(e.type==='brownWarrior')return 'brownIdle';
 if(e.type==='golem')return 'golemIdle';
 if(e.type==='mage')return e.variant==='female'?'femaleMageIdle':'mageIdle';
 if(e.type==='king')return 'kingIdle';
 if(e.type==='dragon')return e.dragonFlightState==='flying'||e.dragonFlightState==='takeoff'?'dragonFly':'dragonGround';
 return e.variant==='female'?'femaleIdle':'idle';
}
function canvasBlob(canvas,type,quality){
 return new Promise(resolve=>canvas.toBlob(resolve,type,quality));
}
async function makeWarLodPoster(key){
 const src=ASSETS[key];if(!src)return null;
 const response=await fetch(src,{cache:'force-cache'});
 if(!response.ok)throw Error('LOD poster '+key+' '+response.status);
 const blob=await response.blob();
 let width=0,height=0,draw=null,cleanup=()=>{};
 if('createImageBitmap' in window){
   try{
     const bitmap=await createImageBitmap(blob);
     width=bitmap.width;height=bitmap.height;draw=(ctx,w,h)=>ctx.drawImage(bitmap,0,0,w,h);
     cleanup=()=>{try{bitmap.close()}catch(_){}};
   }catch(_){}
 }
 if(!draw){
   const objectUrl=URL.createObjectURL(blob),img=new Image();
   try{
     await new Promise((resolve,reject)=>{img.onload=resolve;img.onerror=reject;img.src=objectUrl});
     width=img.naturalWidth;height=img.naturalHeight;draw=(ctx,w,h)=>ctx.drawImage(img,0,0,w,h);
     cleanup=()=>URL.revokeObjectURL(objectUrl);
   }catch(err){URL.revokeObjectURL(objectUrl);throw err}
 }
 if(!width||!height){cleanup();return null}
 const scale=Math.min(1,WAR_LOD_POSTER_MAX_SIDE/Math.max(width,height));
 const canvas=document.createElement('canvas');
 canvas.width=Math.max(1,Math.round(width*scale));canvas.height=Math.max(1,Math.round(height*scale));
 const c=canvas.getContext('2d',{alpha:true});c.imageSmoothingEnabled=true;c.imageSmoothingQuality='medium';
 draw(c,canvas.width,canvas.height);cleanup();
 let poster=await canvasBlob(canvas,'image/webp',.58);
 if(!poster)poster=await canvasBlob(canvas,'image/png');
 if(!poster)return null;
 const url=URL.createObjectURL(poster);warLodPosterUrls.set(key,url);return url;
}
function ensureWarLodPoster(key){
 if(warLodPosterUrls.has(key))return Promise.resolve(warLodPosterUrls.get(key));
 if(warLodPosterPromises.has(key))return warLodPosterPromises.get(key);
 const promise=makeWarLodPoster(key).catch(()=>null).finally(()=>warLodPosterPromises.delete(key));
 warLodPosterPromises.set(key,promise);return promise;
}
async function warmWarLodPosters(){
 for(const key of WAR_LOD_POSTER_KEYS){
   if(warLodPosterUrls.has(key))continue;
   await new Promise(resolve=>{
     if('requestIdleCallback' in window)requestIdleCallback(()=>resolve(),{timeout:700});
     else setTimeout(resolve,80);
   });
   await ensureWarLodPoster(key);
 }
}
function ensureEntityLodPosterNode(el){
 if(el._lodPoster)return el._lodPoster;
 const img=document.createElement('img');img.className='entity-body entity-lod-poster';img.draggable=false;img.decoding='async';
 el._facing?.appendChild(img);el._lodPoster=img;return img;
}
function activateEntityLodPoster(el,e){
 const key=warLodPosterKeyForEntity(e),url=warLodPosterUrls.get(key);
 if(!url){ensureWarLodPoster(key);return false}
 const img=ensureEntityLodPosterNode(el);
 if(img.dataset.posterKey!==key){img.dataset.posterKey=key;img.src=url}
 if(!el._lodStatic){
   el._lodStatic=true;el.classList.add('entity-lod-static');
   suspendEntityLoopGif(el);
   for(const transient of [el._brownAttack,el._brownSpecial,el._golemAttack,el._golemSpecial,el._mageSpecial,el._kingSpecial,el._dragonTakeoff,el._dragonAttack])stopGif(transient);
 }
 return true;
}
function deactivateEntityLodPoster(el){
 if(!el?._lodStatic)return;
 el._lodStatic=false;el.classList.remove('entity-lod-static');
}
function warEntityHasTransientVisual(e,now){
 if(!e?.alive)return false;
 if(e.type==='brownWarrior')return !!e.pendingBrownAttack&&Number(e.pendingBrownAttack.endAt)>now;
 if(e.type==='golem')return !!activeGolemPending(e,now);
 if(e.type==='mage')return e.pendingMageAttack?.kind==='special'&&Number(e.pendingMageAttack.endAt)>now;
 if(e.type==='king')return !!e.pendingKingSpecial&&Number(e.pendingKingSpecial.endAt)>now;
 if(e.type==='dragon')return e.dragonFlightState==='takeoff'||(!!e.pendingDragonAttack&&Number(e.pendingDragonAttack.endAt)>now);
 return false;
}
function applyWarVisualLodClass(level){
 if(!gameScreenPerfEl)return;
 gameScreenPerfEl.classList.toggle('war-lod-medium',level===1);
 gameScreenPerfEl.classList.toggle('war-lod-heavy',level===2);
}
function updateWarVisualLod(zoom,visibleCount,now=performance.now()){
 let target=0;
 if(state.mode==='war'&&state.phase!=='idle'){
   const fps=Number(state.fps)||60;
   if(zoom<=WAR_LOD_HEAVY_ZOOM||visibleCount>=WAR_LOD_HEAVY_COUNT||(visibleCount>=8&&fps<32))target=2;
   else if(zoom<=WAR_LOD_MEDIUM_ZOOM||visibleCount>=WAR_LOD_MEDIUM_COUNT||(visibleCount>=6&&fps<48))target=1;
 }
 if(target>warVisualLodLevel){warVisualLodLevel=target;warVisualLodRecoverSince=0;applyWarVisualLodClass(warVisualLodLevel)}
 else if(target<warVisualLodLevel){
   if(!warVisualLodRecoverSince)warVisualLodRecoverSince=now;
   if(now-warVisualLodRecoverSince>=WAR_LOD_RECOVER_MS){warVisualLodLevel=target;warVisualLodRecoverSince=0;applyWarVisualLodClass(warVisualLodLevel)}
 }else warVisualLodRecoverSince=0;
 return warVisualLodLevel;
}
function shouldSyncWarVisuals(now){
 const interval=warVisualLodLevel>=2?WAR_LOD_HEAVY_SYNC_MS:warVisualLodLevel===1?WAR_LOD_MEDIUM_SYNC_MS:0;
 if(!interval||now-warVisualSyncLastAt>=interval){warVisualSyncLastAt=now;return true}
 return false;
}

const DRAGON_PROJECTILE_GIF_GRACE_MS=850;'''
rep(needle,lod_js)

# 4) Compute LOD from real visible troop count/zoom and throttle expensive DOM sync under load.
old=''' syncWarArenaOverlay(left,top,zoom);
 const domCamera=prepareCameraComposite(left,top,zoom);
 syncEntityVisuals(visible,domCamera.left,domCamera.top,domCamera.zoom,vw,vh,left,top,zoom);
 syncBrownWarriorPowerEffects(domCamera.left,domCamera.top,domCamera.zoom,vw,vh,left,top,zoom);
 syncKingPowerEffects(domCamera.left,domCamera.top,domCamera.zoom,vw,vh,left,top,zoom);
 syncMagePowerEffects(domCamera.left,domCamera.top,domCamera.zoom,vw,vh,left,top,zoom);
 syncDragonProjectileEffects(domCamera.left,domCamera.top,domCamera.zoom,vw,vh,left,top,zoom);
}'''
new=''' syncWarArenaOverlay(left,top,zoom);
 const domCamera=prepareCameraComposite(left,top,zoom);
 const visualNow=performance.now();
 updateWarVisualLod(zoom,visible.length,visualNow);
 if(state.mode!=='war'||shouldSyncWarVisuals(visualNow)){
   syncEntityVisuals(visible,domCamera.left,domCamera.top,domCamera.zoom,vw,vh,left,top,zoom);
   syncBrownWarriorPowerEffects(domCamera.left,domCamera.top,domCamera.zoom,vw,vh,left,top,zoom);
   syncKingPowerEffects(domCamera.left,domCamera.top,domCamera.zoom,vw,vh,left,top,zoom);
   syncMagePowerEffects(domCamera.left,domCamera.top,domCamera.zoom,vw,vh,left,top,zoom);
   syncDragonProjectileEffects(domCamera.left,domCamera.top,domCamera.zoom,vw,vh,left,top,zoom);
 }
}'''
rep(old,new)

# 5) Set per-frame animation budget in entity sync.
rep(''' const localNow=performance.now();

 // Culling usa a câmera real; posicionamento usa a câmera-base do compositor.

 for(const e of visible){''',''' const localNow=performance.now();
 let lodAnimatedTransientUsed=0;

 // Culling usa a câmera real; posicionamento usa a câmera-base do compositor.

 for(const e of visible){''')

# Insert LOD activation after entity is confirmed on-screen and before sprite-state work.
rep('''   const visualMoving=entityVisualMoving(el,e,localNow);

   // PVE: contorno fino seguindo exatamente a silhueta/transparência do GIF.''','''   const visualMoving=entityVisualMoving(el,e,localNow);

   const transientVisual=warEntityHasTransientVisual(e,localNow);
   let animateTransient=transientVisual;
   if(state.mode==='war'&&warVisualLodLevel>=2&&transientVisual){
     animateTransient=lodAnimatedTransientUsed<WAR_LOD_HEAVY_ATTACK_BUDGET;
     if(animateTransient)lodAnimatedTransientUsed++;
   }
   const wantLodStatic=state.mode==='war'&&warVisualLodLevel>0&&(!transientVisual||!animateTransient);
   const lodStatic=wantLodStatic&&activateEntityLodPoster(el,e);
   if(!lodStatic)deactivateEntityLodPoster(el);

   // PVE: contorno fino seguindo exatamente a silhueta/transparência do GIF.''')

# Skip expensive per-unit GIF state machine while poster LOD is active.
rep("""   if(e.type==='brownWarrior'){
     const p=e.pendingBrownAttack;""","""   if(lodStatic){
     // Poster estático: o estado lógico continua sendo processado fora do render.
     // Não religamos nenhum GIF pesado neste frame.
   }else if(e.type==='brownWarrior'){
     const p=e.pendingBrownAttack;""")

# 6) Warm posters after boot without blocking menu/loader.
rep("""runBootLoader().catch(err=>{console.error(err);document.body.classList.remove('booting');document.getElementById('bootLoader')?.remove()});""","""runBootLoader().then(()=>{setTimeout(()=>warmWarLodPosters().catch(()=>{}),250)}).catch(err=>{console.error(err);document.body.classList.remove('booting');document.getElementById('bootLoader')?.remove()});""")

# Marker for future validation.
rep('''/* ==================== CÂMERA MESTRE DA GUERRA ==================== */''','''/* WAR VISUAL LOD ACTIVE 2026-09-12 */
/* ==================== CÂMERA MESTRE DA GUERRA ==================== */''')

if s==orig:
    raise SystemExit('no changes')
p.write_text(s,encoding='utf-8')
print('patched adaptive war visual LOD')
