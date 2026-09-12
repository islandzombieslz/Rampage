from pathlib import Path
import hashlib
import json
import re

INDEX = Path('index.html')
SW = Path('sw.js')
OLD_MARK = '/* ROOM FLOW + BOOT PRELOAD 2026-09-12 */'
NEW_MARK = '/* PERSISTENT ASSET CACHE 2026-09-12 */'
CACHE_NAME = 'rampage-assets-v3'
MANIFEST_KEY = 'rampageAssetManifestV3'

text = INDEX.read_text(encoding='utf-8')
start = text.find(NEW_MARK)
if start < 0:
    start = text.find(OLD_MARK)
if start < 0:
    raise SystemExit('Boot loader marker not found')
end = text.find('\nconst state = {', start)
if end < 0:
    raise SystemExit('Boot loader end marker not found')

# Exclude the previous generated manifest itself before discovering referenced assets,
# otherwise removed assets would keep reappearing forever.
scan_text = text[:start] + text[end:]
local_urls = set(re.findall(r"['\"](assets/[^'\"<>?\\s]+)['\"]", scan_text))
external_urls = set(re.findall(r"['\"](https://i\\.postimg\\.cc/[^'\"<>\\s]+)['\"]", scan_text))

manifest = {}
for url in sorted(local_urls):
    path = Path(url)
    if not path.is_file():
        print(f'warning: referenced asset missing: {url}')
        continue
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:20]
    manifest[url] = digest
for url in sorted(external_urls):
    # External Postimg resources are versioned by URL. When the URL changes, the
    # manifest changes and the client refreshes only that resource.
    manifest[url] = 'ext-' + hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]

manifest_json = json.dumps(manifest, ensure_ascii=False, separators=(',', ':'))

loader = r'''/* PERSISTENT ASSET CACHE 2026-09-12 */
const BOOT_ASSET_MANIFEST=Object.freeze(''' + manifest_json + r''');
const BOOT_CACHE_NAME=''' + json.dumps(CACHE_NAME) + r''';
const BOOT_MANIFEST_KEY=''' + json.dumps(MANIFEST_KEY) + r''';
const BOOT_FETCH_CONCURRENCY=8;
function setBootProgress(value){
 const pct=Math.max(0,Math.min(100,Math.round(value)));
 const text=document.getElementById('bootLoaderPercent'),bar=document.getElementById('bootLoaderBar');
 if(text)text.textContent=pct+'%';if(bar)bar.style.width=pct+'%';
}
function setBootTitle(text){const el=document.getElementById('bootLoaderTitle');if(el)el.textContent=text}
function bootReadSavedManifest(){
 try{return JSON.parse(localStorage.getItem(BOOT_MANIFEST_KEY)||'{}')||{}}catch(_){return {}}
}
function bootWriteSavedManifest(value){try{localStorage.setItem(BOOT_MANIFEST_KEY,JSON.stringify(value))}catch(_){}}
async function bootOpenCache(){
 if(!('caches' in window))return null;
 try{return await caches.open(BOOT_CACHE_NAME)}catch(_){return null}
}
function bootRevisionUrl(url,revision){
 const sep=url.includes('?')?'&':'?';
 return url+sep+'rampageRev='+encodeURIComponent(revision);
}
async function registerAssetServiceWorker(){
 if(!('serviceWorker' in navigator))return;
 try{await navigator.serviceWorker.register('./sw.js',{scope:'./',updateViaCache:'none'})}catch(_){}
}
async function bootFetchAndStore(url,revision,cache){
 const requestUrl=bootRevisionUrl(url,revision);
 const absolute=new URL(url,location.href);
 const sameOrigin=absolute.origin===location.origin;
 for(let attempt=0;attempt<2;attempt++){
   const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),60000);
   try{
     const options=sameOrigin
       ? {cache:'reload',credentials:'same-origin',signal:controller.signal}
       : {cache:'reload',mode:'no-cors',credentials:'omit',signal:controller.signal};
     const response=await fetch(requestUrl,options);
     if(!response||(response.type!=='opaque'&&!response.ok))throw Error('asset fetch failed');
     if(cache){
       await cache.put(url,response.clone());
     }else if(response.body){
       const reader=response.body.getReader();
       while(true){const part=await reader.read();if(part.done)break}
     }else{
       await response.arrayBuffer();
     }
     clearTimeout(timer);return true;
   }catch(_){
     clearTimeout(timer);
     if(attempt===0)continue;
   }
 }
 return false;
}
async function runBootLoader(){
 registerAssetServiceWorker();
 try{navigator.storage?.persist?.().catch(()=>{})}catch(_){}
 // Firebase aquece em paralelo, mas não bloqueia mais a tela de 0-100%.
 NetworkAdapter.ensureAuth().catch(()=>{});
 const entries=Object.entries(BOOT_ASSET_MANIFEST);
 const previous=bootReadSavedManifest();
 const cache=await bootOpenCache();
 const ready={};
 let completed=0,failed=0;
 setBootProgress(0);setBootTitle('VERIFICANDO ARQUIVOS');

 const cached=await Promise.all(entries.map(async([url,revision])=>{
   if(previous[url]!==revision||!cache)return false;
   try{return !!(await cache.match(url))}catch(_){return false}
 }));
 const pending=[];
 entries.forEach(([url,revision],i)=>{
   if(cached[i]){ready[url]=revision;completed++}
   else pending.push([url,revision]);
 });
 const total=Math.max(1,entries.length);
 setBootProgress(completed/total*100);

 if(pending.length){
   setBootTitle(pending.length===entries.length?'BAIXANDO ARQUIVOS':`ATUALIZANDO ${pending.length} ARQUIVO${pending.length===1?'':'S'}`);
   let next=0;
   const worker=async()=>{
     while(true){
       const i=next++;if(i>=pending.length)return;
       const [url,revision]=pending[i];
       const ok=await bootFetchAndStore(url,revision,cache);
       if(ok)ready[url]=revision;else failed++;
       completed++;setBootProgress(completed/total*100);
     }
   };
   await Promise.all(Array.from({length:Math.min(BOOT_FETCH_CONCURRENCY,pending.length)},worker));
 }

 if(cache){
   const obsolete=Object.keys(previous).filter(url=>!(url in BOOT_ASSET_MANIFEST));
   if(obsolete.length)await Promise.all(obsolete.map(url=>cache.delete(url).catch(()=>false)));
 }
 bootWriteSavedManifest(ready);
 setBootProgress(100);setBootTitle(failed?'CARREGAMENTO CONCLUÍDO':'PRONTO');
 if(failed&&typeof assetWarning!=='undefined'&&assetWarning){
   assetWarning.textContent=`${failed} recurso(s) não puderam ser atualizados.`;
   assetWarning.classList.add('show');
 }
 document.body.classList.remove('booting');
 const loader=document.getElementById('bootLoader');
 if(loader){loader.classList.add('done');setTimeout(()=>loader.remove(),120)}
}
'''

text = text[:start] + loader + text[end:]
INDEX.write_text(text, encoding='utf-8')

sw = r'''/* GENERATED PERSISTENT ASSET CACHE - DO NOT EDIT BY HAND */
const CACHE_NAME=''' + json.dumps(CACHE_NAME) + r''';
const ASSET_REVISIONS=Object.freeze(''' + manifest_json + r''');
function assetKey(requestUrl){
 const url=new URL(requestUrl);
 if(url.searchParams.has('rampageRev'))return null;
 const scope=new URL(self.registration.scope);
 if(url.origin===scope.origin&&url.pathname.startsWith(scope.pathname)){
   const relative=decodeURIComponent(url.pathname.slice(scope.pathname.length));
   if(Object.prototype.hasOwnProperty.call(ASSET_REVISIONS,relative))return relative;
 }
 const absolute=url.href;
 if(Object.prototype.hasOwnProperty.call(ASSET_REVISIONS,absolute))return absolute;
 return null;
}
function cacheRequest(key){return /^https?:\/\//i.test(key)?key:new URL(key,self.registration.scope).href}
self.addEventListener('install',event=>{event.waitUntil(self.skipWaiting())});
self.addEventListener('activate',event=>{
 event.waitUntil((async()=>{
   const names=await caches.keys();
   await Promise.all(names.filter(name=>name.startsWith('rampage-assets-')&&name!==CACHE_NAME).map(name=>caches.delete(name)));
   await self.clients.claim();
 })());
});
self.addEventListener('fetch',event=>{
 if(event.request.method!=='GET')return;
 const key=assetKey(event.request.url);if(!key)return;
 event.respondWith((async()=>{
   const cache=await caches.open(CACHE_NAME);
   const lookup=cacheRequest(key);
   const cached=await cache.match(lookup);
   if(cached)return cached;
   try{
     const response=await fetch(event.request);
     if(response&&(response.ok||response.type==='opaque'))await cache.put(lookup,response.clone());
     return response;
   }catch(err){
     const fallback=await cache.match(lookup);
     if(fallback)return fallback;
     throw err;
   }
 })());
});
'''
SW.write_text(sw, encoding='utf-8')

print(f'Persistent cache manifest generated with {len(manifest)} assets.')
