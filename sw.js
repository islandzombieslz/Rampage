/* GENERATED PERSISTENT ASSET CACHE - DO NOT EDIT BY HAND */
const CACHE_NAME="rampage-assets-v3";
const ASSET_REVISIONS=Object.freeze({"assets/audio/tema.mp3":"4ea25460a082ec24d41c","assets/brown-warrior/guerreira-marrom-andando.gif":"61c0609c9195f705c034","assets/brown-warrior/guerreira-marrom-ataque-normal.gif":"df1dcfa3755167f11e21","assets/brown-warrior/guerreira-marrom-parada.gif":"5054bcb25e3ecac21947","assets/dragon/bola-de-fogo.gif":"a53adcb311ee24a75b1c","assets/dragon/dragao-guerreiro-atacando.gif":"361d4109a32d72a1477b","assets/dragon/dragao-guerreiro-parado.gif":"3957c1c2d3ced76e2025","assets/dragon/dragao-guerreiro-pulando.gif":"15e9cff46f277368ccaa","assets/dragon/dragao-guerreiro-voando.gif":"37226564c62889b89e40","assets/golem/golem-andando.gif":"c5d97e981381fac0c515","assets/golem/golem-ataque.gif":"16e57c364d4183534477","assets/golem/golem-parado.gif":"bbf80c6627ce48d2efcd","assets/king/card.png":"65a1234077906cbb8d47","assets/king/idle.gif":"57f9985d1a8cb61283b1","assets/king/power.gif":"09ef34bf326adbfb3542","assets/king/walk.gif":"de13759b74f421ab5177","assets/mage/maga-andando.gif":"d7fb255ed05b949c1759","assets/mage/maga-parada.gif":"53bdbf02d9a18fd650db","assets/mage/mago-andando.gif":"07c053928df29d54c4de","assets/mage/mago-parado.gif":"dd2d9f7333dc3485093f","assets/mage/mao-cajado.gif":"57ceebcf1c3044204319","assets/mage/poder-mago.gif":"ac235a426b9db43d1048","assets/ui/botao-loja.png":"0e8b751a876e189eb958","assets/ui/botao-pvp.png":"2146131b8b84bee9563c","assets/ui/criar-partida.png":"ef738c5fbc59ae6f68b1","assets/ui/pvp-menu.png":"00a74b607b4342b82318","assets/warrior/guerreira-andando.gif":"110fe58f5ac993759d7f","assets/warrior/guerreira-parada.gif":"6196ec9884d23a185852","assets/warrior/guerreiro-andando.gif":"9d74fab3a5bda9d15343","assets/warrior/guerreiro-parado.gif":"3ee1716010bc42021ac5"});
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
