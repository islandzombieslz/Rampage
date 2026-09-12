from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
orig=s

def rep(old,new,count=1):
    global s
    n=s.count(old)
    if n<count: raise SystemExit(f'guard missing {n}/{count}: {old[:100]!r}')
    s=s.replace(old,new,count)

rep("const WAR_LOD_POSTER_MAX_SIDE=128;\n", "const WAR_LOD_POSTER_MAX_SIDE=128;\nconst WAR_LOD_POSTER_CACHE='rampage-war-lod-posters-v1';\n")

old='''function canvasBlob(canvas,type,quality){
 return new Promise(resolve=>canvas.toBlob(resolve,type,quality));
}
async function makeWarLodPoster(key){'''
new='''function canvasBlob(canvas,type,quality){
 return new Promise(resolve=>canvas.toBlob(resolve,type,quality));
}
function warLodPosterCacheUrl(key){
 const src=ASSETS[key]||key;
 const rev=BOOT_ASSET_MANIFEST?.[src]||'runtime';
 return new URL(`__war_lod__/${encodeURIComponent(key)}-${encodeURIComponent(rev)}.poster`,location.href).href;
}
async function loadCachedWarLodPoster(key){
 if(!('caches' in window))return null;
 try{
   const cache=await caches.open(WAR_LOD_POSTER_CACHE),hit=await cache.match(warLodPosterCacheUrl(key));
   if(!hit)return null;
   const blob=await hit.blob();if(!blob.size)return null;
   const url=URL.createObjectURL(blob);warLodPosterUrls.set(key,url);return url;
 }catch(_){return null}
}
async function makeWarLodPoster(key){'''
rep(old,new)

old2=''' if(!poster)return null;
 const url=URL.createObjectURL(poster);warLodPosterUrls.set(key,url);return url;
}
function ensureWarLodPoster(key){
 if(warLodPosterUrls.has(key))return Promise.resolve(warLodPosterUrls.get(key));
 if(warLodPosterPromises.has(key))return warLodPosterPromises.get(key);
 const promise=makeWarLodPoster(key).catch(()=>null).finally(()=>warLodPosterPromises.delete(key));
 warLodPosterPromises.set(key,promise);return promise;
}'''
new2=''' if(!poster)return null;
 if('caches' in window){
   try{
     const cache=await caches.open(WAR_LOD_POSTER_CACHE);
     await cache.put(warLodPosterCacheUrl(key),new Response(poster,{headers:{'Content-Type':poster.type||'image/webp','Cache-Control':'public,max-age=31536000,immutable'}}));
   }catch(_){}
 }
 const url=URL.createObjectURL(poster);warLodPosterUrls.set(key,url);return url;
}
function ensureWarLodPoster(key){
 if(warLodPosterUrls.has(key))return Promise.resolve(warLodPosterUrls.get(key));
 if(warLodPosterPromises.has(key))return warLodPosterPromises.get(key);
 const promise=(async()=>await loadCachedWarLodPoster(key)||await makeWarLodPoster(key))().catch(()=>null).finally(()=>warLodPosterPromises.delete(key));
 warLodPosterPromises.set(key,promise);return promise;
}'''
rep(old2,new2)

rep('/* WAR VISUAL LOD ACTIVE 2026-09-12 */','/* WAR VISUAL LOD ACTIVE 2026-09-12 */\n/* WAR LOD PERSISTENT POSTERS 2026-09-12 */')

if s==orig: raise SystemExit('no changes')
p.write_text(s,encoding='utf-8')
print('persistent LOD poster cache patched')
