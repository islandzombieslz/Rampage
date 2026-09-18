from pathlib import Path
import hashlib
import json
import re

INDEX = Path('index.html')
SW = Path('sw.js')
NEW_MARK = '/* PERSISTENT ASSET CACHE 2026-09-12 */'
CACHE_NAME = 'rampage-assets-v3'

text = INDEX.read_text(encoding='utf-8')
if NEW_MARK not in text:
    raise SystemExit('Persistent cache marker not found')

manifest_pattern = re.compile(
    r'const BOOT_ASSET_MANIFEST=Object\.freeze\(\{.*?\}\);',
    re.S,
)
matches = list(manifest_pattern.finditer(text))
if len(matches) != 1:
    raise SystemExit(f'Expected exactly one BOOT_ASSET_MANIFEST declaration, found {len(matches)}')

# Remove only the generated manifest contents while scanning.
# All loader/custom boot JavaScript remains untouched.
scan_text = manifest_pattern.sub(
    'const BOOT_ASSET_MANIFEST=Object.freeze({});',
    text,
    count=1,
)

local_urls = set(re.findall(r'''['"](assets/[^'"<>?\s]+)['"]''', scan_text))
external_urls = set(re.findall(r'''['"](https://i\.postimg\.cc/[^'"<>\s]+)['"]''', scan_text))

manifest = {}
for url in sorted(local_urls):
    path = Path(url)
    if not path.is_file():
        print(f'warning: referenced asset missing: {url}')
        continue
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:20]
    manifest[url] = digest

for url in sorted(external_urls):
    manifest[url] = 'ext-' + hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]

manifest_json = json.dumps(manifest, ensure_ascii=False, separators=(',', ':'))
new_manifest = 'const BOOT_ASSET_MANIFEST=Object.freeze(' + manifest_json + ');'
text = manifest_pattern.sub(lambda _m: new_manifest, text, count=1)
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

print(f'Persistent cache manifest generated with {len(manifest)} assets without rewriting boot logic.')
