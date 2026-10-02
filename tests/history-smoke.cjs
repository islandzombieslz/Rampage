const fs=require('fs');
const assert=require('assert');
const html=fs.readFileSync('index.html','utf8');
const worker=fs.readFileSync('history-server/src/index.js','utf8');
const wrangler=fs.readFileSync('history-server/wrangler.jsonc','utf8');

assert(html.includes('data-mode="history"'),'History card must exist in the mode selector');
assert(html.includes('Botao-modo-historia.png'),'History must use the supplied mode artwork');
assert(html.includes('id="historyServerScreen"')&&html.includes('id="historyServerList"'),
  'History must have a dedicated server-browser screen');
assert(html.includes("state.mode='history'")&&html.includes("openHistoryServerBrowser"),
  'History card must open the server browser directly');
assert(html.includes("HISTORY_SERVER_BASE_DEFAULT='https://rampage-history.island-zombie-slz.workers.dev'"),
  'History client must use the deployed Cloudflare Worker endpoint');
assert(html.includes('const HistoryAdapter=')&&html.includes("new WebSocket(url)")&&html.includes("state.historyActive=true"),
  'History must connect directly to Cloudflare over WebSocket with no player host');
assert(html.includes("if(state.historyActive){if(state.running)HistoryAdapter.tick(dt,now);return}"),
  'History simulation must bypass the Firebase host simulation loop');
assert(html.includes("HistoryAdapter.sendAction(action)")&&html.includes("HistoryAdapter.connect(historySelectedServerId)"),
  'History controls and server selection must use the Cloudflare adapter');

assert(worker.includes('class HistoryRoom extends DurableObject'),
  'History must use a Durable Object as the server authority');
assert(worker.includes('new WebSocketPair()')&&worker.includes('status: 101'),
  'History server must accept WebSocket clients');
assert(worker.includes('spawnDragons(wave)')&&worker.includes('history-dragon-a')&&worker.includes('history-dragon-b'),
  'History server must own exactly two dragon slots');
assert(worker.includes('this.room.dragons.every(d => !d.alive)')&&worker.includes('Date.now() + 2000'),
  'both dragons must respawn two seconds after both are defeated');
assert(worker.includes('rounds: null')&&worker.includes('mode: "history"'),
  'History snapshots must not contain round progression');
assert(worker.includes('const PVP_WORLD = Object.freeze({ width: 1850, height: 1542 })'),
  'History must use the exact PvP arena dimensions');
assert(worker.includes('WARRIOR_SPECIAL_UNLOCK_HITS = 5')&&worker.includes('specialActiveUntil'),
  'History server must own warrior special unlock, cooldown and movement');
assert(worker.includes('DRAGON_SHOT_COOLDOWN_MS')&&worker.includes('DRAGON_CLOSE_SHOT_COOLDOWN_MS')&&worker.includes('player_defeated'),
  'History dragons must attack players authoritatively');
assert(wrangler.includes('"HISTORY_ROOMS"')&&wrangler.includes('"new_sqlite_classes": ["HistoryRoom"]'),
  'Wrangler must bind and migrate the History Durable Object');

console.log('History smoke checks passed.');
