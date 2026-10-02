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
assert(html.includes("HISTORY_SERVER_BASE_DEFAULT=''"),
  'History client must wait for the deployed workers.dev endpoint instead of falling back to player-host Firebase');

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
assert(wrangler.includes('"HISTORY_ROOMS"')&&wrangler.includes('"new_sqlite_classes": ["HistoryRoom"]'),
  'Wrangler must bind and migrate the History Durable Object');

console.log('History smoke checks passed.');
