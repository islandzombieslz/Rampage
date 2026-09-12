/* GENERATED PERSISTENT ASSET CACHE - DO NOT EDIT BY HAND */
const CACHE_NAME="rampage-assets-v3";
const ASSET_REVISIONS=Object.freeze({"assets/audio/som-de-batalha.mp3":"f00bb902c04e5cdde50c","assets/audio/tema.mp3":"4ea25460a082ec24d41c","assets/brown-warrior/guerreira-marrom-andando.gif":"61c0609c9195f705c034","assets/brown-warrior/guerreira-marrom-ataque-especial.gif":"6d6dce18a65003ae9b7f","assets/brown-warrior/guerreira-marrom-ataque-normal.gif":"df1dcfa3755167f11e21","assets/brown-warrior/guerreira-marrom-parada.gif":"5054bcb25e3ecac21947","assets/brown-warrior/poder-especial-guerreira-marrom.gif":"d4706ce61dd0d8e94b06","assets/dragon/bola-de-fogo.gif":"a53adcb311ee24a75b1c","assets/dragon/dragao-guerreiro-atacando.gif":"361d4109a32d72a1477b","assets/dragon/dragao-guerreiro-parado.gif":"3957c1c2d3ced76e2025","assets/dragon/dragao-guerreiro-pulando.gif":"15e9cff46f277368ccaa","assets/dragon/dragao-guerreiro-voando.gif":"37226564c62889b89e40","assets/golem/golem-andando.gif":"c5d97e981381fac0c515","assets/golem/golem-ataque.gif":"16e57c364d4183534477","assets/golem/golem-especial.gif":"e475e6dc5ead0f00dd95","assets/golem/golem-parado.gif":"bbf80c6627ce48d2efcd","assets/golem/pedras-golem.png":"5a1a30b96d673a3318fc","assets/king/card.png":"65a1234077906cbb8d47","assets/king/idle.gif":"57f9985d1a8cb61283b1","assets/king/power.gif":"09ef34bf326adbfb3542","assets/king/special.gif":"ef1a885b7376595d5668","assets/king/sword.png":"8105d9f3509070ea78e2","assets/king/walk.gif":"de13759b74f421ab5177","assets/mage/maga-andando.gif":"d7fb255ed05b949c1759","assets/mage/maga-especial.gif":"b4dad793b9f7379787ba","assets/mage/maga-parada.gif":"53bdbf02d9a18fd650db","assets/mage/mago-andando.gif":"07c053928df29d54c4de","assets/mage/mago-especial.gif":"9f326f228e93c6d7d00c","assets/mage/mago-parado.gif":"dd2d9f7333dc3485093f","assets/mage/mao-cajado.gif":"57ceebcf1c3044204319","assets/mage/mao-magos.png":"dce8cb4d6b00bc73892d","assets/mage/poder-mago-especial.gif":"f46eb1e4fd4bb4f2097e","assets/mage/poder-mago.gif":"ac235a426b9db43d1048","assets/ui/botao-loja.png":"0e8b751a876e189eb958","assets/ui/botao-mestre-da-guerra.png":"962f83ce7386c6c7a79a","assets/ui/botao-pvp.png":"2146131b8b84bee9563c","assets/ui/cla-guerreiros.png":"efca29243cc7a74f402b","assets/ui/criar-partida.png":"ef738c5fbc59ae6f68b1","assets/ui/mestre-da-guerra-menu.png":"66d7766fbfec3c9682c2","assets/ui/pvp-menu.png":"00a74b607b4342b82318","assets/ui/usar-codigo.png":"f2f0e3a60b7e79ed4e04","assets/ui/walpaper-menus.png":"fe6c5ee3f25d35e7b434","assets/ui/war-shop/card-dragao-guerreiro.png":"70c9c1ad9686774f24cc","assets/ui/war-shop/card-golem-guerreiro.png":"d87869d5bbd7b2b215f4","assets/ui/war-shop/card-guerreira-marrom.png":"8ce3e554f3c816cf65f6","assets/ui/war-shop/card-guerreiros.png":"a443fb8789b9c457ba48","assets/ui/war-shop/card-magos-guerreiros.png":"0cb1763d193bc4e91e5b","assets/warrior/espada-guerreiro.png":"9e8f429f8bd38fc96eb1","assets/warrior/guerreira-andando.gif":"110fe58f5ac993759d7f","assets/warrior/guerreira-parada.gif":"6196ec9884d23a185852","assets/warrior/guerreiro-andando.gif":"9d74fab3a5bda9d15343","assets/warrior/guerreiro-parado.gif":"3ee1716010bc42021ac5","https://i.postimg.cc/6qYQzvPc/bff3bb67-8426-4656-bdee-1313473758e2.png":"ext-2d573995d99be8ac","https://i.postimg.cc/fywLxK8B/1919c5cb-ace6-4da5-b8f0-6db8bfb24c89.png":"ext-eb0f021462d53397"});
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
