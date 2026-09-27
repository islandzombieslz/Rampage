const assert=require('node:assert/strict');
const fs=require('node:fs');
const html=fs.readFileSync('index.html','utf8');
const js=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].at(-1)?.[1];
assert(js,'inline game code');
function hash(s){let h=2166136261;for(let i=0;i<s.length;i++)h=Math.imul(h^s.charCodeAt(i),16777619)>>>0;return h.toString(16)}
// Recorded from the last stable pre-PvP version of Rampage. These exact source
// ranges may only change when Clan War is intentionally authorized to change.
const expected=[
 ['updateWar','function updateWar(dt){','function finishWarRound(){','6cb00bee',1684],
 ['finishWarRound','function finishWarRound(){','function aiFightAgainstList(','375a0583',2191],
 ['War camera','function warCameraMinZoom(){','function clampWarCameraAxis(','e8867180',241],
 ['War intro','function beginWarCameraIntro(){','function updateWarCameraIntro(','4bbc9bb8',1007],
 ['combat damage','function applyCombatHit(','function startEntityDeath(','b11088ff',5484],
 ['normal attack','function performAttack(','function attackControlled(','b3f106b5',1093],
 ['War troop setup','function setupWarRound(){','function startCombatPhase(){','5c94a04d',15696]
];
for(const [name,a,b,checksum,size] of expected){
 const i=js.indexOf(a),j=js.indexOf(b,i+a.length);
 assert(i>=0&&j>i,'missing '+name);
 const actual=js.slice(i,j);
 // Ignore only the explicitly mode-gated PvP NPC balance branch. The original
 // damage function must otherwise match the recorded Clan War baseline byte-for-byte.
 const preserved=name==='combat damage'?actual.replace(/\n \/\/ PVP-ONLY NPC DAMAGE:[\s\S]*?\n \/\/ END PVP-ONLY NPC DAMAGE/,''):actual;
 if(name==='combat damage')assert.notEqual(preserved,actual,'expected isolated PvP NPC branch');
 assert.equal(preserved.length,size,name+' source length differs from pre-PvP War baseline');
 assert.equal(hash(preserved),checksum,name+' changed unexpectedly');
}
assert(html.includes('#lobbyScreen.war-lobby>.card{'));
assert(html.includes('assets/ui/mestre-da-guerra-menu.png'));
assert(html.includes("if(state.mode==='pve')updatePVE(dt);else if(state.mode==='pvp')updatePVP(dt);else updateWar(dt)"));
console.log('Baseline War combat, arena, camera, attack, and round source: UNCHANGED');
