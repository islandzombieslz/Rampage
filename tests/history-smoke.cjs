const fs=require('fs');
const assert=require('assert');
const html=fs.readFileSync('index.html','utf8');
const worker=fs.readFileSync('history-server/src/index.js','utf8');
const wrangler=fs.readFileSync('history-server/wrangler.jsonc','utf8');
const historyMapClient=fs.readFileSync('assets/history/map-config.js','utf8');
const historyMapServer=fs.readFileSync('history-server/src/map.js','utf8');

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
assert(worker.includes('spawnDragons(wave)')&&historyMapServer.includes('history-dragon-a')&&historyMapServer.includes('history-dragon-b'),
  'History server must own exactly two dragon slots');
assert(worker.includes('this.room.dragons.every(d => !d.alive)')&&worker.includes('Date.now() + 2000'),
  'both dragons must respawn two seconds after both are defeated');
assert(worker.includes('rounds: null')&&worker.includes('mode: "history"'),
  'History snapshots must not contain round progression');
assert(worker.includes('const PVP_WORLD = HISTORY_MAP_WORLD')&&historyMapServer.includes('width: 3200, height: 2200'),
  'History must use the final editor map dimensions without changing PvP geometry');
assert(historyMapClient.includes('"visualCount":127')&&historyMapClient.includes('"colliderCount":55')&&
  historyMapServer.includes('HISTORY_MAP_COLLIDERS'),
  'History must load all final-map visuals and server-authoritative collision rectangles');
assert(html.includes('historyMoveEntity(me')&&worker.includes('moveHistoryPlayer(player'),
  'History client prediction and Cloudflare authority must share wall collision behavior');
assert(worker.includes('WARRIOR_SPECIAL_UNLOCK_HITS = 5')&&worker.includes('specialActiveUntil'),
  'History server must own warrior special unlock, cooldown and movement');
assert(worker.includes('DRAGON_SHOT_COOLDOWN_MS')&&worker.includes('DRAGON_CLOSE_SHOT_COOLDOWN_MS')&&worker.includes('player_defeated'),
  'History dragons must attack players authoritatively');
assert(wrangler.includes('"HISTORY_ROOMS"')&&wrangler.includes('"new_sqlite_classes": ["HistoryRoom"]'),
  'Wrangler must bind and migrate the History Durable Object');


assert(html.includes('HISTORY_RENDER_DELAY_MIN_MS=35')&&html.includes('HISTORY_RENDER_DELAY_MAX_MS=80'),
  'History must use a lower adaptive interpolation buffer than Firebase PvP');
assert(html.includes("data.type==='damage'")&&html.includes('recordPVPDamage(e,Number(data.amount)||0)'),
  'History server damage events must update damage text immediately');
assert(html.includes("e.dragonFlightState=flight")&&html.includes('historySyncProjectiles(snapshot.projectiles||[],this.lastServerTime)'),
  'History must render authoritative dragon flight and fireballs');
assert(html.includes("unacked=ack<(Number(this.inputSeq)||0)")&&html.includes('error>760'),
  'History local prediction must avoid reconciling against snapshots that have not acknowledged recent input');
assert(worker.includes('const DRAGON_MAX_HP = 100')&&worker.includes('const DRAGON_MAX_SHIELD = 50'),
  'History dragons must have exactly 100 HP and 50 shield');
assert(worker.includes('const DRAGON_DAMAGE = 10')&&worker.includes('const DRAGON_BURN_DAMAGE = 2.5')&&worker.includes('const DRAGON_BURN_TICK_MS = 1000'),
  'History dragon direct damage must be 10 and burn damage 2.5 per second');
assert(worker.includes('launchDragonFireball')&&worker.includes('flightState: "takeoff"')&&worker.includes('flightState = "flying"'),
  'History dragons must take off, fly and launch server-authoritative fireballs');
assert(worker.includes('now - this.lastBroadcastAt >= 50')&&worker.includes('}, 33);'),
  'History server must run a faster active simulation and snapshot cadence');


assert(html.includes('HISTORY_RENDER_DELAY_MIN_MS=35')&&html.includes('HISTORY_RENDER_DELAY_MAX_MS=80')&&html.includes('HISTORY_INPUT_KEEPALIVE_MS=50'),
  'History must use the lower latency interpolation/input profile');
assert(html.includes("pose:{x:me.x,y:me.y")&&worker.includes('applyClientPose(player, message.pose, inputSeq)'),
  'History must send a validated predicted client pose to reduce projectile/player mismatch');
assert(worker.includes('const DRAGON_SPEED = 97.5'),
  'History dragon speed must match PvP dragon speed');
assert(html.includes('historyApplyHitFeedback(e,data.impact,data.sourceId)')&&worker.includes('armKnockback(target'),
  'History must reuse hit reaction and authoritative knockback feedback');
assert(html.includes('startEntityDeath(e,Number(e.hitDirX)||0,Number(e.hitDirY)||0)')&&html.includes("!state.historyActive&&e.pvpMode"),
  'History deaths must use PvP death visuals without consuming PvP round lives');

assert(worker.includes('WARRIOR_COMBO_CHAIN_MS = 950')&&worker.includes('WARRIOR_COMBO_CONTINUE_MS = 460')&&
  worker.includes('const hitFractions = [.18, .50, .82]')&&worker.includes('type: "combat_sfx"'),
  'History warrior combo timing, hits and sound events must mirror PvP');
assert(worker.includes('WARRIOR_SPECIAL_DAMAGE_MIN = 50')&&worker.includes('WARRIOR_SPECIAL_DAMAGE_MAX = 70')&&
  worker.includes('WARRIOR_SPECIAL_DAMAGE_HITS = 5')&&worker.includes('WARRIOR_SPECIAL_HEAL = 30')&&
  worker.includes('const fractions = [0, .24, .49, .74, .96]'),
  'History warrior special must mirror PvP five-hit damage and healing rules');
assert(worker.includes('player.specialAngle = heading')&&worker.includes('WARRIOR_SPECIAL_KNOCK_FORCE = 560')&&
  worker.includes('WARRIOR_SPECIAL_KNOCK_TIME_MS = 340'),
  'History special must remain steerable and use PvP final knockback');
assert(html.includes('function historyApplyAuthoritativeAction')&&html.includes('function historySyncWarriorCombatSnapshot')&&
  html.includes('historyServerSpecialSerial')&&html.includes('historyServerComboSerial')&&html.includes('historyServerSingleSerial'),
  'History client must use authoritative Cloudflare action serials instead of reconstructing actions from jitter');
assert(html.includes("if(data.type==='combat_sfx'){historyApplyCombatSfx(data);return}")&&
  html.includes("pvpPlayEntitySfxNow(e,'history-warrior-combo',serial,'pvpWarriorSingle'")&&
  html.includes('function pvpEntitySfxMix(e)')&&html.includes('updatePvpCombatSfx(now)'),
  'History combat sounds must reuse PvP spatial audio and serial de-duplication');
assert(html.includes('soundAt:now+1000')&&html.includes('soundAt:arrival+1000')&&
  html.includes('Number(e.pendingDragonAttack.serial)!==attackSerial'),
  'History dragon attack SFX and GIF must share the PvP 1000 ms cue without snapshot restarts');
assert(html.includes('historyPreviewLocalAction(me,action,pvpControls.targetId)'),
  'History local previews must obey PvP attack activation gates');
assert(worker.includes('action === "combo_cancel"')&&worker.includes('"combo-cancel"')&&
  html.includes('sendComboCancel()')&&html.includes('if(state.historyActive)HistoryAdapter.sendComboCancel()')&&
  html.includes('const staleForLocal=e.controlled&&Number(e.attackSerial||0)>Number(data.attackSerial||0)'),
  'History must cancel held Warrior combos on Cloudflare immediately without letting a stale cancel overwrite a newer local attack');
assert(html.includes('function historyTickLocalWarriorComboVisual')&&
  html.includes('historyTickLocalWarriorComboVisual(me,now)')&&html.includes('if(repeat)return historyStartLocalWarriorCombo(e,now)'),
  'History must keep held local combo GIF cycles continuous without running local damage simulation');
assert(html.includes('if(!controlled)e.attackCooldown=')&&
  html.includes('if(!controlled&&authoritativeSingleNew&&!matchingSinglePreview)')&&
  html.includes('if(!controlled&&authoritativeComboNew&&!matchingComboPreview)'),
  'History snapshots must not overwrite the controlled player local attack/combo visual clock');
assert(html.includes("pvpFullGifDuration('pvpWarriorAttack',PVP_WARRIOR.singleFallbackMs)")&&
  html.includes("pvpFullGifDuration('pvpWarriorCombo',PVP_WARRIOR.comboFallbackMs)"),
  'Remote History Warrior attacks must render using the same full GIF duration logic as PvP');
assert(worker.includes('retaliatePending')&&worker.includes('retaliateImmediate')&&
  worker.includes('dragon.nextShotAt = 0')&&worker.includes('dragon.closeShotAt = 0')&&
  worker.includes('dragon.flightState === "flying"'),
  'History dragons must preserve the PvP first-hit retaliation behavior even while staggered');
assert(worker.includes('projectile.pvpHit = true')&&worker.includes('projectile.hitUntil = now + 400')&&
  worker.includes('105, 60')&&worker.includes('impact.tilt = 6')&&
  html.includes("if(data.type==='projectile_hit')")&&html.includes('p.pvpHit=true'),
  'History fireballs must preserve PvP impact knockback and the 400 ms collision linger');
assert(worker.includes('burnSourceX')&&worker.includes('burnSourceY')&&
  worker.includes('player, 4')&&worker.includes('"burn", player.burnSourceId, burnImpact'),
  'History burn ticks must use PvP-style light hit feedback without knockback');

console.log('History smoke checks passed.');

require('./history-combat-regression.cjs');
