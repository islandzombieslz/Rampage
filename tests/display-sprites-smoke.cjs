// Preserve the animation contract and the optimized cache across regeneration.
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const {execFileSync}=require('node:child_process');
const root=path.resolve(__dirname,'..'),html=fs.readFileSync(path.join(root,'index.html'),'utf8');
const report=JSON.parse(fs.readFileSync(path.join(root,'assets/runtime/sprite-report.json'),'utf8'));
const manifest=JSON.parse(html.match(/const BOOT_ASSET_MANIFEST=Object.freeze\((\{.*?\})\);/)[1]);
const sw=fs.readFileSync(path.join(root,'sw.js'),'utf8');
assert.deepEqual(JSON.parse(sw.match(/const ASSET_REVISIONS=Object.freeze\((\{.*?\})\);/)[1]),manifest);
function animation(file){
 const b=fs.readFileSync(path.join(root,file));assert.equal(b.subarray(0,3).toString(),'GIF');
 let p=13,delay=100;const delays=[];
 if(b[10]&128)p+=3*(1<<((b[10]&7)+1));
 const blocks=()=>{while(p<b.length){const n=b[p++];if(!n)return;p+=n}throw Error('Truncated GIF '+file)};
 while(p<b.length){
  const tag=b[p++];if(tag===59)break;
  if(tag===33){
   const label=b[p++];
   if(label===249){assert.equal(b[p++],4);p++;delay=b.readUInt16LE(p)*10;p+=3;assert.equal(b[p++],0)}
   else blocks();
  }else if(tag===44){
   const packed=b[p+8];p+=9;if(packed&128)p+=3*(1<<((packed&7)+1));p++;blocks();delays.push(delay);delay=100;
  }else throw Error('Invalid GIF block '+file+' at '+p);
 }
 return {width:b.readUInt16LE(6),height:b.readUInt16LE(8),delays};
}
assert.equal(report.length,72,'all existing animated game assets have display variants');
for(const sprite of report){
 const original=animation(sprite.original),display=animation(sprite.runtime);
 assert.deepEqual(display.delays,original.delays,sprite.key+' must preserve every frame and delay');
 assert.deepEqual([display.width,display.height],sprite.runtimeSize);
 assert.equal(display.delays.length,sprite.frames);
 assert.equal(display.delays.reduce((sum,n)=>sum+n,0),sprite.durationMs);
 assert(display.width<=original.width&&display.height<=original.height);
 assert(manifest[sprite.runtime],sprite.key+' must be cached before combat');
 if(!['magePower','egyptMagePower'].includes(sprite.key))assert(!manifest[sprite.original],'avoid eager duplicate original '+sprite.key);
}
assert(manifest['assets/mage/poder-mago.gif']&&manifest['assets/egypt/mage/power-normal.gif'],'native flame masks stay cached for exact collision');
// Run the actual regeneration job in an isolated directory: it must retain the
// optimized manifest, with no changes to the shipped HTML or service worker.
const temporary=fs.mkdtempSync(path.join(os.tmpdir(),'rampage-display-cache-'));
try{
 fs.writeFileSync(path.join(temporary,'index.html'),html);fs.writeFileSync(path.join(temporary,'sw.js'),sw);
 fs.symlinkSync(path.join(root,'assets'),path.join(temporary,'assets'),'dir');
 execFileSync('python',['.github/rebalance_war_units_v3.py'],{cwd:root,stdio:'pipe'});
 execFileSync('python',[path.join(root,'.github/update_asset_cache.py')],{cwd:temporary,stdio:'pipe'});
 assert.equal(fs.readFileSync(path.join(temporary,'index.html'),'utf8'),html,'cache regeneration must preserve HTML');
 assert.equal(fs.readFileSync(path.join(temporary,'sw.js'),'utf8'),sw,'cache regeneration must preserve service worker');
}finally{fs.rmSync(temporary,{recursive:true,force:true})}
const originalBytes=report.reduce((sum,r)=>sum+r.originalBytes,0),runtimeBytes=report.reduce((sum,r)=>sum+r.runtimeBytes,0);
assert(runtimeBytes<originalBytes*.5,'display art must reduce the real download budget');
console.log('SPRITE/CACHE PASS: 72 complete animations, exact frame delays, original collision art, idempotent optimized cache ('+Math.round((1-runtimeBytes/originalBytes)*100)+'% fewer GIF bytes)');
