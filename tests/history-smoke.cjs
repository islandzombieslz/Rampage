const fs=require('fs');
const assert=require('assert');
const html=fs.readFileSync('index.html','utf8');
const worker=fs.readFileSync('history-server/src/index.js','utf8');
const wrangler=fs.readFileSync('history-server/wrangler.jsonc','utf8');
const historyMapClient=fs.readFileSync('assets/history/map-config.js','utf8');
const historyMapServer=fs.readFileSync('history-server/src/map.js','utf8');

assert(html.includes('data-mode="history"')&&html.includes('id="historyServerScreen"')&&html.includes('id="historyServerList"'),
  'History must keep its dedicated mode and server browser');
assert(html.includes("HISTORY_SERVER_BASE_DEFAULT='https://rampage-history.island-zombie-slz.workers.dev'")&&
  html.includes('const HistoryAdapter=')&&html.includes('new WebSocket(url)'),
  'Cloudflare History multiplayer must remain available');
assert(html.includes("id:'history-local'")&&html.includes("name:'Servidor local • Solo'")&&html.includes('const HistoryLocalAdapter='),
  'History server browser must expose an offline/local solo host');
assert(html.includes("state.historyLocal?HistoryLocalAdapter:HistoryAdapter")&&
  html.includes("if(state.historyLocal){")&&html.includes("pvpHandleAction(me,action,pvpControls.targetId)"),
  'Local History must run combat and simulation on the player host without Cloudflare');
const localStart=html.indexOf('const HistoryLocalAdapter='),localEnd=html.indexOf('function renderHistoryServers',localStart);
const localBlock=html.slice(localStart,localEnd);
assert(localStart>=0&&localEnd>localStart&&!localBlock.includes('new WebSocket(')&&!localBlock.includes("rooms/"),
  'Local History adapter must not open a WebSocket or Firebase multiplayer room');

assert(worker.includes('class HistoryRoom extends DurableObject')&&worker.includes('new WebSocketPair()')&&worker.includes('status: 101'),
  'Cloudflare History must keep a Durable Object authority');
assert(worker.includes('const HISTORY_SCHEMA_VERSION = 7')&&worker.includes('HISTORY_MAP_EVENTS'),
  'History server schema must be upgraded for editor gameplay events');
assert(historyMapClient.includes('"id":"history-castle-v2"')&&historyMapServer.includes('HISTORY_MAP_ID = "history-castle-v2"'),
  'client and Cloudflare must use the updated editor map version');
assert(historyMapClient.includes('"visualCount":127')&&historyMapClient.includes('"colliderCount":55')&&historyMapClient.includes('"eventCount":7'),
  'updated map must contain all 127 visuals, 55 colliders and 7 gameplay events');
assert(historyMapServer.includes('HISTORY_MAP_SPAWN = Object.freeze({"x":597,"y":2049})'),
  'player origin must come from the editor player_start event');
assert((historyMapServer.match(/"kind":"enemy_spawn"/g)||[]).length===3&&
  (historyMapServer.match(/"kind":"checkpoint"/g)||[]).length===2&&
  (historyMapServer.match(/"kind":"victory"/g)||[]).length===1,
  'editor map must keep three troop spawns, two checkpoints and one victory area');
assert(historyMapServer.includes('"dragon":3')&&historyMapServer.includes('"naja":2')&&historyMapServer.includes('"anubis":2')&&
  historyMapServer.includes('"spawnMode":"endless"'),
  'editor troop quantities and endless spawn settings must reach the game config');
assert(worker.includes('spawnEditorWave(event')&&worker.includes('updateSpawnEvents(now')&&worker.includes('HISTORY_ENEMY_STATS'),
  'Cloudflare must create editor-defined PvP enemy types and schedules');
assert(worker.includes('historyLeashArea')&&worker.includes('pointInArea(p.x, p.y, dragon.historyLeashArea)')&&
  html.includes('historyConstrainEnemy')&&html.includes('historyPointInArea(t.x,t.y,e.historyLeashArea)'),
  'cloud and local enemies must obey editor reach areas');
assert(worker.includes('checkpointForPlayer(player)')&&worker.includes('type: "history_checkpoint"')&&
  worker.includes('type: "history_victory"')&&html.includes('finishHistoryVictory'),
  'checkpoints, respawn and victory must be wired from the editor');
assert(html.includes("this.checkpointId=event.id")&&html.includes("this.respawnPoint={x:Number(p.x),y:Number(p.y)}"),
  'local History must respawn at the latest reached checkpoint');
assert(html.includes("awards:{[String(uid)]:200}")&&html.includes("mode:'history'"),
  'History victory must produce an XP-eligible match result');

assert(worker.includes('const PVP_WORLD = HISTORY_MAP_WORLD')&&historyMapServer.includes('width: 3200, height: 2200'),
  'History must use the editor world dimensions without changing PvP arena constants');
assert(html.includes('historyMoveEntity(me')&&worker.includes('moveHistoryPlayer(player')&&
  html.includes('historyPositionBlocked')&&worker.includes('historyPositionBlocked'),
  'client/local prediction and Cloudflare authority must share map wall collision');
assert(html.includes('const rawEnemies=Array.isArray(snapshot.enemies)')&&worker.includes('enemies: this.room.dragons'),
  'Cloudflare snapshots must support every editor enemy type, not only dragons');
assert(html.includes("PVP_ENEMY_HEROES[type]")&&html.includes('pvpBotAction(e,dt)'),
  'local History must reuse the existing PvP troop registry and NPC combat AI');

assert(worker.includes('WARRIOR_SPECIAL_UNLOCK_HITS = 5')&&worker.includes('specialActiveUntil')&&
  worker.includes('WARRIOR_COMBO_CHAIN_MS = 950')&&worker.includes('WARRIOR_COMBO_CONTINUE_MS = 460'),
  'Cloudflare Warrior combo/special rules must remain authoritative');
assert(worker.includes('WARRIOR_SPECIAL_DAMAGE_MIN = 50')&&worker.includes('WARRIOR_SPECIAL_DAMAGE_MAX = 70')&&
  worker.includes('WARRIOR_SPECIAL_DAMAGE_HITS = 5')&&worker.includes('WARRIOR_SPECIAL_HEAL = 30'),
  'History Warrior special must preserve PvP five-hit damage/heal rules');
assert(worker.includes('DRAGON_SHOT_COOLDOWN_MS')&&worker.includes('DRAGON_CLOSE_SHOT_COOLDOWN_MS')&&worker.includes('launchDragonFireball'),
  'History dragon mechanics must remain present for editor-spawned dragons');
assert(worker.includes('const DRAGON_MAX_HP = 100')&&worker.includes('const DRAGON_MAX_SHIELD = 50')&&
  worker.includes('const DRAGON_DAMAGE = 10')&&worker.includes('const DRAGON_BURN_DAMAGE = 2.5'),
  'History dragon durability/direct/burn damage must remain unchanged');
assert(worker.includes('now - this.lastBroadcastAt >= 50')&&worker.includes('}, 33);'),
  'Cloudflare active simulation/snapshot cadence must remain unchanged');

assert(html.includes('HISTORY_RENDER_DELAY_MIN_MS=35')&&html.includes('HISTORY_RENDER_DELAY_MAX_MS=80')&&html.includes('HISTORY_INPUT_KEEPALIVE_MS=50'),
  'Cloud History must retain the low-latency interpolation/input profile');
assert(html.includes("data.type==='damage'")&&html.includes('recordPVPDamage(e,Number(data.amount)||0)')&&
  html.includes('historyApplyHitFeedback(e,data.impact,data.sourceId)'),
  'Cloud History damage must still update visual hit feedback immediately');
assert(html.includes("!state.historyActive&&e.pvpMode")&&html.includes('startEntityDeath(e,Number(e.hitDirX)||0,Number(e.hitDirY)||0)'),
  'History deaths must keep PvP death visuals without consuming PvP round lives');
assert(html.includes('historyPreviewLocalAction(me,action,pvpControls.targetId)')&&html.includes('if(!state.historyLocal)HistoryAdapter.sendComboCancel()'),
  'Cloud History must retain predicted Warrior input while local History stays off the socket path');
assert(html.includes('function historyTickLocalWarriorComboVisual')&&html.includes('historyTickLocalWarriorComboVisual(me,now)'),
  'History Warrior combo visuals must remain continuous');
assert(html.includes("pvpFullGifDuration('pvpWarriorAttack',PVP_WARRIOR.singleFallbackMs)")&&
  html.includes("pvpFullGifDuration('pvpWarriorCombo',PVP_WARRIOR.comboFallbackMs)"),
  'History Warrior attacks must keep the exact PvP GIF duration logic');

assert(wrangler.includes('"HISTORY_ROOMS"')&&wrangler.includes('"new_sqlite_classes": ["HistoryRoom"]'),
  'Wrangler must keep the History Durable Object binding');
console.log('History smoke checks passed.');
require('./history-combat-regression.cjs');
