const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const html=fs.readFileSync('index.html','utf8');
const script=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].at(-1)?.[1];
assert(script,'inline game script missing');
new vm.Script(script,{filename:'index.html PvP'});
function section(a,b){const i=script.indexOf(a),j=script.indexOf(b,i+a.length);assert(i>=0&&j>i,'missing '+a);return script.slice(i,j)}
let now=100000,mobile=false,damageCalls=[];
const state={mode:'pvp',phase:'combat',running:true,world:{w:2200,h:1400},entities:[],players:[],nextId:1,round:1,
 rounds:2,pveTime:60,timeLeft:60,speed:'normal',difficulty:'easy',particles:[],dragonProjectiles:[],
 spectator:{active:false,transitioning:false},matchStats:{}};
const nodes=new Map();
function node(key){if(!nodes.has(key))nodes.set(key,{
 style:{},dataset:{},classList:{add(){},remove(){},toggle(){}},
 addEventListener(){},querySelector(){return null},replaceChildren(){},append(){},appendChild(){},remove(){},
 setAttribute(){},children:[],hidden:false,disabled:false
 });return nodes.get(key)}
const net={localPlayerId:'u1',remoteInputs:{},attackSeq:0,online:false,isHost:true,sendInput(){}};
const ctx=vm.createContext({Math,Object,Date,Number,JSON,String,Map,Set,console,
 state,NetworkAdapter:net,performance:{now:()=>now},
 clamp:(v,a,b)=>Math.max(a,Math.min(b,v)),isMobileLike:()=>mobile,
 $:node,$$:()=>[],ASSETS:{},Image:class{},document:{createElement:()=>node('created-'+Math.random())},
 entityBase:(type,x,y,team,color)=>({id:state.nextId++,type,x,y,team,color,r:30,hp:100,maxHp:100,shield:50,maxShield:50,damage:20,
 speed:150,alive:true,knockTime:0,attackCooldown:0,attackSerial:0,comboStep:0,heading:0,facing:1,moving:false,
 mageAttackSerial:0}),
 applyCombatHit:(target,source,damage,options)=>{
   damageCalls.push({damage,options,target:target.id});
   const absorbed=Math.min(target.shield,damage);
   target.shield-=absorbed;target.hp-=Math.max(0,damage-absorbed);
   if(target.hp<=0)target.alive=false;
 },
 startEntityDeath:e=>{e.alive=false;e.deathStarted=now},
 distanceToSegment:(px,py,ax,ay,bx,by)=>{
   const dx=bx-ax,dy=by-ay,t=Math.max(0,Math.min(1,((px-ax)*dx+(py-ay)*dy)/(dx*dx+dy*dy)));
   return Math.hypot(px-(ax+t*dx),py-(ay+t*dy))
 },
 clearEntityVisuals(){},flash(){},navigateScreen(){},configureGameScreenForMode(){},
 beginMatchTracking(){},matchStatsFor:uid=>state.matchStats[uid]||(state.matchStats[uid]={damage:0,wonRounds:0,victorySeconds:0,victoryTimeLimit:0}),
 finishGame(){},difficultyConfig:{easy:{initial:1,every:20,wave:1}},getLocalMovement:()=>({dx:0,dy:0,attackSeq:net.attackSeq}),
 sendLocalPVEInput(){},setTimeout(){},requestAnimationFrame(){}
});
vm.runInContext(section('const PVP_HEROES=Object.freeze(', 'function setLobbySkin('),ctx);
vm.runInContext(section('const PVP_BASE=Object.freeze(', '/* ==================== PVE ==================== */'),ctx);
const run=expr=>vm.runInContext(expr,ctx);
const heroes=run('PVP_HEROES'),base=run('PVP_BASE');
assert.equal(heroes.length,8);
for(const h of heroes)assert(h.card.startsWith('assets/')&&h.name&&h.id);
assert.equal(new Set(heroes.map(h=>h.id)).size,8);
assert.equal(run('PVP_ENEMY_HERO_IDS.length'),5);
assert.equal(base.hp,200);assert.equal(base.shield,100);
assert.equal(base.damageMin,25);assert.equal(base.damageMax,40);
assert.equal(base.meleeCooldown,.70);assert.equal(base.specialCooldown,20000);
assert.equal(run('pvpDamageForRange(0)'),40);
assert.equal(run('pvpDamageForRange(133)'),25);
assert.equal(run('pvpDamageForRange(0,true)'),100);
assert.equal(run('pvpDamageForRange(270,true)'),80);
assert.equal(run('pvpCameraZoom(1920,1080)'),1.8);
mobile=true;assert(run('pvpCameraZoom(850,390)')<1.8);

const hero=run('pvpBaseEntity(PVP_HERO_BY_ID.warrior,500,500,"u1","#aaa","u1",false)');
const foe=run('pvpBaseEntity({...PVP_ENEMY_HEROES.naja,id:"naja"},595,500,"pvp-enemy","#f77",null,true)');
assert.equal(hero.maxHp,200);assert.equal(hero.maxShield,100);assert.equal(hero.speed,195);
assert.equal(foe.maxHp,100);assert.equal(foe.maxShield,50);assert.equal(foe.speed,97.5);
assert.equal(foe.damage,20);assert.equal(foe.controlled,false);
assert(run('pvpBasicAttack(state.entities[0])'));
assert.equal(damageCalls.length,1);assert(damageCalls[0].damage>=25&&damageCalls[0].damage<=40);
assert.equal(damageCalls[0].options.knockForce,95);
assert.equal(run('pvpBasicAttack(state.entities[0])'),false,'basic attack cooldown');

const mage=run('pvpBaseEntity(PVP_HERO_BY_ID.mage,1050,500,"u2","#ffe","u2",false)');
assert(mage.pvpSpecialReadyAt>1e13,'warrior mage cannot cast before shield break');
mage.shield=10;
const attacker=foe;attacker.x=1100;attacker.y=500;
run('pvpCombatHit(state.entities[2],state.entities[1],20)');
assert.equal(mage.shield,0);
assert.equal(mage.pvpSpecialReadyAt,110000,'10 s shield break gate');
now=110001;
assert(run('pvpSpecialAttack(state.entities[2])'));
assert.equal(mage.pvpSpecialDuration,40000);
assert.equal(mage.pvpSpecialReadyAt,150001);

const egypt=run('pvpBaseEntity(PVP_HERO_BY_ID.egyptMage,1450,700,"u3","#e0c","u3",false)');
assert.equal(egypt.pvpSpecialReadyAt,now+10000);
now+=10001;
const hitsBefore=damageCalls.length;
assert(run('pvpSpecialAttack(state.entities.find(e=>e.id==='+egypt.id+'))'));
assert.equal(damageCalls.length,hitsBefore,'Egypt summon special deals no damage');
const minions=state.entities.filter(e=>e.pvpSummonerId===egypt.id);
assert.equal(minions.length,2);assert(minions.every(e=>e.type==='anubis'&&e.maxHp===100&&e.maxShield===50));
now=egypt.pvpSpecialReadyAt+1;run('pvpExpireSummons(performance.now())');
assert(minions.every(e=>!e.alive),'summons die immediately on cooldown completion');
assert.equal(egypt.pvpSpecialDuration,30000);

const power=run('pvpBaseEntity(PVP_HERO_BY_ID.egyptMage,400,1000,"u4","#e0c","u4",false)');
const victim=run('pvpBaseEntity({...PVP_ENEMY_HEROES.golem,id:"golem"},585,1000,"pvp-enemy","#f77",null,true)');
assert(run('pvpCastPower(state.entities.find(e=>e.id==='+power.id+'),'+victim.id+')'));
now+=1;
const shieldBefore=victim.shield;
run('pvpTickPower(state.entities.find(e=>e.id==='+power.id+'),performance.now(),0)');
assert.equal(victim.shield,shieldBefore-15,'15 damage per 500ms');
now+=500;
run('pvpTickPower(state.entities.find(e=>e.id==='+power.id+'),performance.now(),0)');
assert.equal(victim.shield,shieldBefore-30);
assert.equal(run('pvpCanPower(state.entities.find(e=>e.id==='+hero.id+'))'),false);

assert(html.includes('id="pvpCombatHud"')&&html.includes('id="pvpPicker"'));
assert(html.includes("state.mode==='pvp'?pvpCameraZoom(vw,vh):1.80"));
assert(html.includes("if(state.mode==='pvp')updatePVP(dt);else updateWar(dt)"));
assert(html.includes("pvpConfirmed:true"),'networked hero confirmation');
assert(html.includes("if(state.mode==='pvp')syncPVPPowerEffects("),'animated mage power');
console.log('PvP hero registry, independent stats, mage specials, summons, power damage, mobile camera: PASS');
