import { DurableObject } from "cloudflare:workers";
import "../../assets/history/rules.js";
import { HISTORY_MAP_ID, HISTORY_MAP_WORLD, HISTORY_MAP_SPAWN, HISTORY_MAP_PLAY_BOUNDS, HISTORY_MAP_COLLIDERS, HISTORY_MAP_DOORS, HISTORY_MAP_EVENTS, HISTORY_MAP_OBJECTS } from "./map.js";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Allow-Methods": "GET,OPTIONS"
};

const SERVER_CATALOG = Object.freeze([
  { id: "history-1", name: "Servidor História 1", map: HISTORY_MAP_ID, maxPlayers: 8 }
]);

const HISTORY_SCHEMA_VERSION = 12;
const HistoryRules = globalThis.RampageHistoryRules;
const HISTORY_GEOMETRY = {width:HISTORY_MAP_WORLD.width,height:HISTORY_MAP_WORLD.height,colliders:HISTORY_MAP_COLLIDERS,doors:HISTORY_MAP_DOORS,destructibles:HISTORY_MAP_OBJECTS};
const historyNavigation = HistoryRules.createNavigator(HISTORY_GEOMETRY);
function historyLineOfSight(a,b,doors,r=0,objects={}) { return HistoryRules.firstWallHit(HISTORY_GEOMETRY,doors,a.x,a.y,b.x,b.y,r,objects) === null; }
function pursueHistoryEnemy(enemy,target,dt,doors,now,objects={}) {
  const v=historyNavigation.direction(enemy,target,COMBAT_ENTITY_RADIUS,doors,now,objects);
  enemy.moving=moveHistoryEnemy(enemy,v.x*enemy.speed*dt,v.y*enemy.speed*dt,COMBAT_ENTITY_RADIUS,doors,objects);
  if(enemy.moving){enemy.heading=Math.atan2(v.y,v.x);if(Math.abs(v.x)>.01)enemy.facing=v.x<0?-1:1;}
  return enemy.moving;
}
const PVP_WORLD = HISTORY_MAP_WORLD;
const PVP_PLAY_BOUNDS = HISTORY_MAP_PLAY_BOUNDS;

const PLAYER_MAX_HP = 350;
const PLAYER_MAX_SHIELD = 250;
const PLAYER_SPEED = 195;
const PLAYER_RESPAWN_MS = 3000;

const WARRIOR_MELEE_RANGE = 112;
const WARRIOR_MELEE_COOLDOWN_MS = 300;
const WARRIOR_DAMAGE_MIN = 25;
const WARRIOR_DAMAGE_MAX = 40;
const WARRIOR_COMBO_CHAIN_MIN_MS = 120;
const WARRIOR_COMBO_CHAIN_MS = 950;
const WARRIOR_COMBO_CONTINUE_MS = 460;
const WARRIOR_COMBO_RANGE = 148;
const WARRIOR_SINGLE_VISUAL_MS = 1430;
const WARRIOR_COMBO_DURATION_MS = 3130;
const WARRIOR_SPECIAL_UNLOCK_HITS = 5;
const WARRIOR_SPECIAL_COOLDOWN_MS = 20000;
const WARRIOR_SPECIAL_DURATION_MS = 3900;
const WARRIOR_SPECIAL_SPEED_MULTIPLIER = 1.45;
const WARRIOR_SPECIAL_DAMAGE_MIN = 50;
const WARRIOR_SPECIAL_DAMAGE_MAX = 70;
const WARRIOR_SPECIAL_DAMAGE_HITS = 5;
const WARRIOR_SPECIAL_HEAL = 30;
const WARRIOR_SPECIAL_KNOCK_FORCE = 560;
const WARRIOR_SPECIAL_KNOCK_TIME_MS = 340;
const WARRIOR_SPECIAL_HIT_TILT = 20;
const COMBAT_ENTITY_RADIUS = 30;

const DRAGON_MAX_HP = 100;
const DRAGON_MAX_SHIELD = 50;
const DRAGON_SPEED = 97.5;
const DRAGON_TAKEOFF_MS = 1200;
const DRAGON_ATTACK_VISUAL_MS = 1800;
const DRAGON_SHOT_COOLDOWN_MS = 2000;
const DRAGON_CLOSE_SHOT_COOLDOWN_MS = 5000;
const DRAGON_CLOSE_RANGE = 175;
const DRAGON_FIREBALL_SPEED = 430;
const DRAGON_DAMAGE = 10;
const DRAGON_BURN_DAMAGE = 2.5;
const DRAGON_BURN_TICK_MS = 1000;
const DRAGON_BURN_DURATION_MS = 6000;
const HISTORY_KNOCK_FORCE = 95;
const HISTORY_KNOCK_TIME_MS = 100;
const HISTORY_HIT_TILT = 7;
const CLIENT_POSE_MAX_STEP_MS = 220;
const CLIENT_POSE_SPEED_FACTOR = 2.0;
const CLIENT_POSE_FIRST_ALLOWANCE_PX = 180;

const HISTORY_HEROES = Object.freeze({
  warrior: { id: "warrior", type: "warrior", clan: "warriors", variant: "male" },
  mageFemale: { id: "mageFemale", type: "mage", clan: "warriors", variant: "female" }
});
const HISTORY_ENEMY_STATS = Object.freeze({
  naja: Object.freeze({ hp: 300, shield: 250, speed: 117, damage: 25, range: 112, cooldown: 1450 }),
  poseidon: Object.freeze({ hp: 300, shield: 250, speed: 117, damage: 22, range: 255, cooldown: 1750 }),
  anubis: Object.freeze({ hp: 100, shield: 50, speed: 97.5, damage: 20, range: 285, cooldown: 1550 }),
  golem: Object.freeze({ hp: 150, shield: 100, speed: 117, damage: 30, range: 112, cooldown: 1800 }),
  dragon: Object.freeze({ hp: DRAGON_MAX_HP, shield: DRAGON_MAX_SHIELD, speed: DRAGON_SPEED, damage: DRAGON_DAMAGE, range: 285, cooldown: DRAGON_SHOT_COOLDOWN_MS }),
  seahorse: Object.freeze({ hp: 100, shield: 50, speed: 97.5, damage: 18, range: 120, cooldown: 1350 })
});
function pointInArea(x, y, area, pad = 0) {
  if (!area) return true;
  return x >= Number(area.x) + pad && x <= Number(area.x) + Number(area.w) - pad &&
    y >= Number(area.y) + pad && y <= Number(area.y) + Number(area.h) - pad;
}
function mapEvent(kind) { return HISTORY_MAP_EVENTS.find(event => event.kind === kind) || null; }
function mapEvents(kind) { return HISTORY_MAP_EVENTS.filter(event => event.kind === kind); }

function historyHero(id) { return HISTORY_HEROES[id] || HISTORY_HEROES.warrior; }

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", ...CORS }
  });
}
function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
function distance(a, b) { return Math.hypot(a.x - b.x, a.y - b.y); }
function historyCircleRectHit(cx, cy, r, rect) {
  const x = Number(rect?.[0]) || 0, y = Number(rect?.[1]) || 0;
  const w = Math.max(0, Number(rect?.[2]) || 0), h = Math.max(0, Number(rect?.[3]) || 0);
  const qx = Math.max(x, Math.min(cx, x + w)), qy = Math.max(y, Math.min(cy, y + h));
  const dx = cx - qx, dy = cy - qy;
  return dx * dx + dy * dy < r * r;
}
function historyDoorCollisionActive(door, doorState) {
  const open = !!doorState?.[door.id]?.open;
  return open ? !!door.openCollision : door.closedCollision !== false;
}
function historyPositionBlocked(x, y, r = COMBAT_ENTITY_RADIUS, doorState = null, objects = {}) {
  for(const rect of HistoryRules.obstacles(HISTORY_GEOMETRY,doorState||{},objects)) {
    if(rect[4]==='circle' ? HistoryRules.rectHitTime(x,y,x,y,rect,r)!==null : historyCircleRectHit(x,y,r,rect))return true;
  }
  return false;
}
function moveHistoryPlayer(player, dx, dy, r = COMBAT_ENTITY_RADIUS, doorState = null, objects = {}) {
  if (!player) return false;
  let moved = false;
  const nx = clamp((Number(player.x) || 0) + (Number(dx) || 0), PVP_PLAY_BOUNDS.left, PVP_PLAY_BOUNDS.right);
  if (!historyPositionBlocked(nx, Number(player.y) || 0, r, doorState, objects)) {
    moved = moved || Math.abs(nx - Number(player.x || 0)) > .001;
    player.x = nx;
  }
  const ny = clamp((Number(player.y) || 0) + (Number(dy) || 0), PVP_PLAY_BOUNDS.top, PVP_PLAY_BOUNDS.bottom);
  if (!historyPositionBlocked(Number(player.x) || 0, ny, r, doorState, objects)) {
    moved = moved || Math.abs(ny - Number(player.y || 0)) > .001;
    player.y = ny;
  }
  return moved;
}
function moveHistoryEnemy(enemy, dx, dy, r = COMBAT_ENTITY_RADIUS, doorState = null, objects = {}) {
  if (!enemy) return false;
  const area = enemy.historyLeashArea || null;
  let moved = false;
  let nx = clamp((Number(enemy.x) || 0) + (Number(dx) || 0), PVP_PLAY_BOUNDS.left, PVP_PLAY_BOUNDS.right);
  if (area) nx = clamp(nx, Number(area.x) + r, Number(area.x) + Number(area.w) - r);
  if (!historyPositionBlocked(nx, Number(enemy.y) || 0, r, doorState, objects)) { moved ||= Math.abs(nx - Number(enemy.x || 0)) > .001; enemy.x = nx; }
  let ny = clamp((Number(enemy.y) || 0) + (Number(dy) || 0), PVP_PLAY_BOUNDS.top, PVP_PLAY_BOUNDS.bottom);
  if (area) ny = clamp(ny, Number(area.y) + r, Number(area.y) + Number(area.h) - r);
  if (!historyPositionBlocked(Number(enemy.x) || 0, ny, r, doorState, objects)) { moved ||= Math.abs(ny - Number(enemy.y || 0)) > .001; enemy.y = ny; }
  return moved;
}


function warriorDamageForRange(d) {
  return WARRIOR_DAMAGE_MIN + (WARRIOR_DAMAGE_MAX - WARRIOR_DAMAGE_MIN) *
    clamp(1 - Number(d || 0) / WARRIOR_MELEE_RANGE, 0, 1);
}
function randomWarriorSpecialDamage() {
  return WARRIOR_SPECIAL_DAMAGE_MIN +
    Math.floor(Math.random() * (WARRIOR_SPECIAL_DAMAGE_MAX - WARRIOR_SPECIAL_DAMAGE_MIN + 1));
}
function normalizedImpact(from, to, tilt = HISTORY_HIT_TILT) {
  let dx = Number(to?.x || 0) - Number(from?.x || 0);
  let dy = Number(to?.y || 0) - Number(from?.y || 0);
  let len = Math.hypot(dx, dy);
  if (len < .001) { dx = Number(from?.facing) < 0 ? -1 : 1; dy = 0; len = 1; }
  return { dirX: dx / len, dirY: dy / len, force: 0, timeMs: 0, tilt };
}
function distanceToSegment(px, py, ax, ay, bx, by) {
  const abx = bx - ax, aby = by - ay, len2 = abx * abx + aby * aby;
  if (len2 <= 1e-9) return Math.hypot(px - ax, py - ay);
  const t = clamp(((px - ax) * abx + (py - ay) * aby) / len2, 0, 1);
  return Math.hypot(px - (ax + abx * t), py - (ay + aby * t));
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      return json({ ok: true, service: "rampage-history", version: HISTORY_SCHEMA_VERSION });
    }

    if (url.pathname === "/servers") {
      const servers = await Promise.all(SERVER_CATALOG.map(async server => {
        try {
          const stub = env.HISTORY_ROOMS.getByName(server.id);
          const info = await stub.fetch(new Request("https://history.internal/info"));
          const runtime = info.ok ? await info.json() : {};
          return { ...server, online: true, players: Number(runtime.players) || 0, pingHint: "websocket" };
        } catch {
          return { ...server, online: true, players: 0, pingHint: "websocket" };
        }
      }));
      return json({ servers });
    }

    if (url.pathname === "/ws") {
      if ((request.headers.get("Upgrade") || "").toLowerCase() !== "websocket") {
        return json({ error: "websocket_required" }, 426);
      }
      const serverId = url.searchParams.get("server") || SERVER_CATALOG[0].id;
      if (!SERVER_CATALOG.some(item => item.id === serverId)) return json({ error: "server_not_found" }, 404);
      return env.HISTORY_ROOMS.getByName(serverId).fetch(request);
    }

    return json({
      ok: true,
      endpoints: ["/health", "/servers", "/ws?server=history-1&uid=...&name=..."]
    });
  }
};

export class HistoryRoom extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.ctx = ctx;
    this.env = env;
    this.clients = new Map();
    this.room = null;
    this.loop = null;
    this.lastTickAt = Date.now();
    this.lastBroadcastAt = 0;
    this.lastPersistAt = 0;
    this.projectileSeq = 0;
    this.ready = this.load();
  }

  async load() {
    const saved = await this.ctx.storage.get("room");
    if (!saved || Number(saved.schemaVersion) !== HISTORY_SCHEMA_VERSION) {
      this.room = this.createRoom();
      await this.ctx.storage.put("room", this.room);
      return;
    }
    this.room = saved;
    this.room.players ||= {};
    this.room.projectiles ||= [];
    this.room.dragons ||= [];
    this.room.spawnState ||= {};
    this.room.doorState ||= this.initialDoorState();
    this.room.objectState ||= this.initialObjectState();
    this.room.finished ||= false;
    this.room.enemySeq ||= 0;
  }

  createRoom() {
    return {
      schemaVersion: HISTORY_SCHEMA_VERSION,
      seq: 0,
      startedAt: Date.now(),
      players: {},
      dragons: [],
      projectiles: [],
      spawnState: {},
      doorState: this.initialDoorState(),
      objectState: this.initialObjectState(),
      enemySeq: 0,
      finished: false,
      victoryAt: 0,
      dragonWave: 1,
      respawnAt: 0
    };
  }

  initialObjectState() {
    return HistoryRules.initialObjects(HISTORY_GEOMETRY);
  }

  updateObjects(now) {
    for (const o of HISTORY_MAP_OBJECTS) {
      const state=this.room.objectState[o.id];
      if(state?.broken&&o.respawn&&now>=state.respawnAt)Object.assign(state,{hp:o.hp,broken:false,brokenAt:0,respawnAt:0});
    }
  }

  updateBosses(now) {
    HistoryRules.updateBosses(HISTORY_GEOMETRY,this.room.objectState,this.room.doorState,
      Object.values(this.room.players),now,(boss,move,player,push)=>{
        const protectedCharge=now<Number(player.specialActiveUntil||0);
        const steps=Math.max(1,Math.ceil(Math.hypot(push.x,push.y)/18));
        if(!protectedCharge)for(let i=0;i<steps;i++)moveHistoryPlayer(player,push.x/steps,push.y/steps,COMBAT_ENTITY_RADIUS,this.room.doorState,this.room.objectState);
        const origin={id:boss.id,x:boss.x+boss.w/2,y:boss.y+boss.h/2};
        this.applyDamage("player",player,protectedCharge&&move.damage>0?2:Number(move.damage)||0,"boss_attack",boss.id,
          move.hitEffect?.enabled===false?null:normalizedImpact(origin,player,6));
        this.defeatPlayer(player,now);
      });
  }

  hitMapObjects(player,damage,range,now=Date.now(),hitIntervalMs=0) {
    for(const o of HISTORY_MAP_OBJECTS) {
      const state=this.room.objectState[o.id];
      if(!HistoryRules.hitObject(HISTORY_GEOMETRY,o,state,player,damage,range,this.room.doorState,this.room.objectState,now,hitIntervalMs))continue;
      if(state.broken)player.historyObjectXP=(Number(player.historyObjectXP)||0)+(Number(o.xp)||0);
      this.broadcast({type:"history_object",objectId:o.id,state:{...state},uid:player.id,xp:Number(player.historyObjectXP)||0,at:now});
    }
  }

  initialDoorState() {
    return Object.fromEntries(HISTORY_MAP_DOORS.map(door => [door.id, { open: false, defeats: 0, openedAt: 0 }]));
  }

  doorRuntime(door) {
    this.room.doorState ||= this.initialDoorState();
    return this.room.doorState[door.id] ||= { open: false, defeats: 0, openedAt: 0 };
  }

  openDoor(door, now = Date.now()) {
    const state = this.doorRuntime(door);
    if (state.open) return false;
    state.open = true;
    state.openedAt = now;
    this.broadcast({ type: "history_door", doorId: door.id, open: true, defeats: Number(state.defeats) || 0, openedAt: now, at: now });
    return true;
  }

  updateDoors(now = Date.now()) {
    if (!HISTORY_MAP_DOORS.length) return;
    const players = Object.values(this.room.players || {}).filter(player => player.alive);
    for (const door of HISTORY_MAP_DOORS) {
      const state = this.doorRuntime(door);
      if (state.open) continue;
      const mode = String(door.openWhen || "proximity");
      const useProximity = mode === "proximity" || mode === "proximity_or_defeat" || mode === "proximity_and_defeat";
      const useDefeats = mode === "defeat_count" || mode === "proximity_or_defeat" || mode === "proximity_and_defeat";
      let near = false;
      if (useProximity) {
        const x = Number(door.x) || 0, y = Number(door.y) || 0, w = Math.max(0, Number(door.w) || 0), h = Math.max(0, Number(door.h) || 0);
        const range = Math.max(0, Number(door.proximity) || 0);
        near = players.some(player => {
          const qx = clamp(Number(player.x) || 0, x, x + w), qy = clamp(Number(player.y) || 0, y, y + h);
          return Math.hypot((Number(player.x) || 0) - qx, (Number(player.y) || 0) - qy) <= range;
        });
      }
      const enough = useDefeats && Number(state.defeats || 0) >= Math.max(1, Number(door.enemyCount) || 1);
      const shouldOpen =
        mode === "proximity" ? near :
        mode === "defeat_count" ? enough :
        mode === "proximity_and_defeat" ? near && enough :
        near || enough;
      if (shouldOpen) this.openDoor(door, now);
    }
  }

  registerDoorDefeat(enemy, now = Date.now()) {
    if (!enemy) return;
    for (const door of HISTORY_MAP_DOORS) {
      const mode = String(door.openWhen || "proximity");
      if (!(mode === "defeat_count" || mode === "proximity_or_defeat" || mode === "proximity_and_defeat")) continue;
      const state = this.doorRuntime(door);
      if (state.open || !door.enemyArea || !pointInArea(enemy.x, enemy.y, door.enemyArea)) continue;
      state.defeats = (Number(state.defeats) || 0) + 1;
    }
    this.updateDoors(now);
  }

  spawnDragons(wave) {
    // Kept as a compatibility method for old tests/state names. Gameplay spawns
    // now come entirely from the editor's enemy_spawn events.
    return [];
  }

  createEnemy(type, event, wave, index, now = Date.now()) {
    const stats = HISTORY_ENEMY_STATS[type] || HISTORY_ENEMY_STATS.naja;
    const angle = index * 2.399963229728653;
    const radius = index ? 34 + (index % 3) * 18 : 0;
    const area = event.area || null;
    let x = Number(event.x) + Math.cos(angle) * radius;
    let y = Number(event.y) + Math.sin(angle) * radius;
    if (area) {
      x = clamp(x, Number(area.x) + 34, Number(area.x) + Number(area.w) - 34);
      y = clamp(y, Number(area.y) + 34, Number(area.y) + Number(area.h) - 34);
    }
    const point=historyNavigation.spawnPoint({x,y},COMBAT_ENTITY_RADIUS,this.room.doorState,area,this.room.objectState);
    if(!point)return null;
    x=point.x;y=point.y;
    const id = "history-enemy-" + (++this.room.enemySeq) + "-" + String(event.id || "spawn");
    return {
      id, type, x, y, hp: stats.hp, maxHp: stats.hp, shield: stats.shield, maxShield: stats.shield,
      damage: stats.damage, speed: stats.speed, alive: true, facing: 1, heading: 0, moving: false,
      wave, historySpawnEventId: event.id, historyLeashArea: area ? { ...area } : null,
      attackSerial: 0, attackUntil: 0, npcNextAttackAt: now + 450,
      flightState: type === "dragon" ? "takeoff" : "ground",
      takeoffSerial: type === "dragon" ? wave : 0,
      takeoffUntil: type === "dragon" ? now + DRAGON_TAKEOFF_MS : 0,
      nextShotAt: type === "dragon" ? now + DRAGON_TAKEOFF_MS + 180 : 0,
      closeShotAt: type === "dragon" ? now + DRAGON_TAKEOFF_MS + 180 : 0,
      firstHitSeen: false, retaliatePending: false, retaliateImmediate: false, retaliateTargetId: null,
      knockUntil: 0, knockVX: 0, knockVY: 0, removeAt: 0
    };
  }

  spawnEditorWave(event, now = Date.now()) {
    const state = this.room.spawnState[event.id] || { count: 0, nextAt: now };
    const wave = state.count + 1;
    let offset = this.room.dragons.filter(e=>e.alive&&e.historySpawnEventId===event.id).length, spawned = 0;
    for (const [type, rawCount] of Object.entries(event.troops || {})) {
      const count = HistoryRules.spawnCount(event,type,this.room.dragons);
      if (!HISTORY_ENEMY_STATS[type]) continue;
      for (let i = 0; i < count; i++) {
        const enemy=this.createEnemy(type,event,wave,offset++,now);
        if(enemy){this.room.dragons.push(enemy);spawned++;}
      }
    }
    if(spawned)state.count = wave;
    state.nextAt = now + Math.max(200, Number(event.intervalMs) || 3000);
    this.room.spawnState[event.id] = state;
    if (spawned) this.broadcast({ type: "history_spawn", eventId: event.id, wave, spawned, at: now });
    return spawned;
  }

  updateSpawnEvents(now = Date.now()) {
    if (this.room.finished) return;
    for (const event of mapEvents("enemy_spawn")) {
      const state = this.room.spawnState[event.id] || { count: 0, nextAt: now };
      const endless = event.spawnMode === "endless";
      const maxWaves = Math.max(1, Number(event.waves) || 1);
      if ((!endless && state.count >= maxWaves) || now < Number(state.nextAt || 0)) {
        this.room.spawnState[event.id] = state;
        continue;
      }
      this.spawnEditorWave(event, now);
    }
  }

  checkpointForPlayer(player) {
    if (!player?.checkpointId) return HISTORY_MAP_SPAWN;
    const event = HISTORY_MAP_EVENTS.find(item => item.kind === "checkpoint" && item.id === player.checkpointId);
    return event?.respawn || event || HISTORY_MAP_SPAWN;
  }

  updateMapProgress(now = Date.now()) {
    if (this.room.finished) return;
    const checkpoints = mapEvents("checkpoint"), victory = mapEvent("victory");
    for (const player of Object.values(this.room.players)) {
      if (!player.alive) continue;
      for (const event of checkpoints) {
        if (!event.area || player.checkpointId === event.id || !pointInArea(player.x, player.y, event.area)) continue;
        player.checkpointId = event.id;
        const spawn = event.respawn || event;
        player.checkpointX = Number(spawn.x); player.checkpointY = Number(spawn.y);
        this.broadcast({ type: "history_checkpoint", uid: player.id, checkpointId: event.id, x: player.checkpointX, y: player.checkpointY, at: now });
      }
      if (victory?.area && pointInArea(player.x, player.y, victory.area)) {
        this.room.finished = true; this.room.victoryAt = now;
        this.broadcast({ type: "history_victory", reachedBy: player.id, eventId: victory.id, xp: 200, awards: Object.fromEntries(Object.values(this.room.players).map(p=>[p.id,200+(Number(p.historyObjectXP)||0)])), at: now });
        break;
      }
    }
  }

  updateGroundEnemy(enemy, dt, now) {
    if (!enemy?.alive) return;
    if (this.stepKnockback(enemy, dt, now)) return;
    const stats = HISTORY_ENEMY_STATS[enemy.type] || HISTORY_ENEMY_STATS.naja;
    const players = Object.values(this.room.players).filter(p => p.alive && pointInArea(p.x, p.y, enemy.historyLeashArea));
    if (!players.length) { enemy.moving = false; return; }
    const visible=players.filter(p=>historyLineOfSight(enemy,p,this.room.doorState,8,this.room.objectState));
    const target = (visible.length?visible:players).reduce((best, p) => !best || distance(enemy, p) < distance(enemy, best) ? p : best, null);
    if (!target) { enemy.moving = false; return; }
    const dx = target.x - enemy.x, dy = target.y - enemy.y, d = Math.hypot(dx, dy) || 1;
    enemy.heading = Math.atan2(dy, dx); enemy.facing = dx < 0 ? -1 : 1;
    if (now < Number(enemy.attackUntil || 0)) { enemy.moving = false; return; }
    if (d > stats.range || !historyLineOfSight(enemy,target,this.room.doorState,8,this.room.objectState)) {
      pursueHistoryEnemy(enemy,target,dt,this.room.doorState,now,this.room.objectState);
      return;
    }
    enemy.moving = false;
    if (now < Number(enemy.npcNextAttackAt || 0)) return;
    enemy.attackSerial = (Number(enemy.attackSerial) || 0) + 1;
    enemy.attackUntil = now + Math.min(1100, stats.cooldown);
    enemy.npcNextAttackAt = now + stats.cooldown;
    if(enemy.type === "anubis") {
      const angle=Math.atan2(dy,dx),start={x:enemy.x+Math.cos(angle)*40,y:enemy.y-14+Math.sin(angle)*16};
      if(!historyLineOfSight(enemy,start,this.room.doorState,8,this.room.objectState))return;
      enemy.attackKind="ranged";
      this.room.projectiles.push({id:"hap_"+(++this.projectileSeq)+"_"+now,kind:"anubis",serial:enemy.attackSerial,
        x:start.x,y:start.y,vx:Math.cos(angle)*430,vy:Math.sin(angle)*430,speed:430,damage:stats.damage,burn:false,
        targetId:target.id,team:"pvp-enemy",sourceId:enemy.id,createdAt:now,expireAt:now+4500});
      return;
    }
    const impact = this.armKnockback(target, dx, dy, enemy.type === "golem" ? 125 : 82, enemy.type === "golem" ? 120 : 75);
    this.applyDamage("player", target, stats.damage, enemy.type + "_attack", enemy.id, impact);
    if (target.hp <= 0) this.defeatPlayer(target, now);
  }

  async fetch(request) {
    await this.ready;
    const url = new URL(request.url);

    if (url.pathname === "/info") {
      return json({ players: this.clients.size, enemiesAlive: this.room.dragons.filter(d => d.alive).length });
    }

    if ((request.headers.get("Upgrade") || "").toLowerCase() !== "websocket") {
      return json({ error: "websocket_required" }, 426);
    }

    const uid = String(url.searchParams.get("uid") || crypto.randomUUID()).slice(0, 80);
    const name = String(url.searchParams.get("name") || "Player").slice(0, 24);
    const hero = historyHero(String(url.searchParams.get("hero") || "warrior"));
    if (!this.clients.has(uid) && this.clients.size >= 8) return json({ error: "server_full" }, 503);

    const pair = new WebSocketPair();
    const [client, server] = Object.values(pair);
    server.accept();

    this.clients.set(uid, server);
    const previous = this.room.players[uid];
    this.room.players[uid] = previous || {
      id: uid, name, hero: hero.id, type: hero.type, clan: hero.clan, variant: hero.variant,
      x: HISTORY_MAP_SPAWN.x, y: HISTORY_MAP_SPAWN.y,
      hp: PLAYER_MAX_HP, maxHp: PLAYER_MAX_HP,
      shield: PLAYER_MAX_SHIELD, maxShield: PLAYER_MAX_SHIELD,
      alive: true, respawnAt: 0, facing: 1, heading: 0, moving: false, input: { dx: 0, dy: 0 },
      lastInputSeq: 0, attackCooldownUntil: 0,
      attackSerial: 0, comboStep: 0,
      singleSerial: 0, singleUntil: 0, lastBasicAt: 0,
      comboSerial: 0, comboStartedAt: 0, comboUntil: 0, comboHitIndex: 0, comboSfxIndex: 0, comboRequestUntil: 0,
      specialHits: 0, specialUnlocked: false, specialCooldownUntil: 0,
      specialSerial: 0, specialStartedAt: 0, specialActiveUntil: 0, specialAngle: 0, specialHitState: {},
      regenSerial: 0,
      burnUntil: 0, burnNextTick: 0, burnSerial: 0, burnSourceId: null, burnSourceX: 0, burnSourceY: 0,
      knockUntil: 0, knockVX: 0, knockVY: 0,
      lastPoseSeq: 0, lastPoseAt: 0,
      checkpointId: null, checkpointX: HISTORY_MAP_SPAWN.x, checkpointY: HISTORY_MAP_SPAWN.y
    };
    Object.assign(this.room.players[uid], { name, hero: hero.id, type: hero.type, clan: hero.clan, variant: hero.variant });

    server.addEventListener("message", event => this.onMessage(uid, event.data));
    server.addEventListener("close", () => this.disconnect(uid));
    server.addEventListener("error", () => this.disconnect(uid));

    this.ensureLoop();
    this.send(server, { type: "hello", uid, serverTime: Date.now(), snapshot: this.snapshot() });
    this.broadcast({ type: "presence", uid, joined: true, players: this.publicPlayers() });

    return new Response(null, { status: 101, webSocket: client });
  }

  disconnect(uid) {
    this.clients.delete(uid);
    if (this.room?.players?.[uid]) delete this.room.players[uid];
    this.broadcast({ type: "presence", uid, joined: false, players: this.publicPlayers() });
    if (!this.clients.size) {
      this.stopLoop();
      this.room = this.createRoom();
      this.ctx.storage.put("room", this.room).catch(() => {});
    }
  }

  onMessage(uid, raw) {
    let message;
    try { message = JSON.parse(typeof raw === "string" ? raw : new TextDecoder().decode(raw)); }
    catch { return; }

    const player = this.room.players[uid];
    if (!player) return;

    if (message.type === "input") {
      if (!player.alive) return;
      let dx = clamp(Number(message.dx) || 0, -1, 1);
      let dy = clamp(Number(message.dy) || 0, -1, 1);
      const len = Math.hypot(dx, dy);
      if (len > 1) { dx /= len; dy /= len; }
      const inputSeq = Math.max(Number(player.lastInputSeq) || 0, Number(message.seq) || 0);
      this.applyClientPose(player, message.pose, inputSeq);
      player.input = { dx, dy };
      player.lastInputSeq = inputSeq;
      if (len > 0.05) {
        const heading = Math.atan2(dy, dx);
        if (Date.now() < Number(player.specialActiveUntil || 0)) player.specialAngle = heading;
        player.heading = heading;
        player.facing = dx < 0 ? -1 : dx > 0 ? 1 : player.facing;
      }
      return;
    }

    if (message.type === "action") {
      this.applyAction(player, String(message.action || "attack"), message);
      return;
    }

    if (message.type === "ping") {
      const ws = this.clients.get(uid);
      if (ws) this.send(ws, { type: "pong", t: message.t || 0, serverTime: Date.now() });
    }
  }

  applyClientPose(player, pose, seq) {
    const now = Date.now();
    if (!player?.alive || !pose || now < Number(player.knockUntil || 0) || now < Number(player.specialActiveUntil || 0)) return false;
    if (!Number.isFinite(Number(pose.x)) || !Number.isFinite(Number(pose.y)) || seq <= Number(player.lastPoseSeq || 0)) return false;

    const previousAt = Number(player.lastPoseAt) || now - 95;
    const stepMs = clamp(now - previousAt, 16, CLIENT_POSE_MAX_STEP_MS);
    let targetX = clamp(Number(pose.x), PVP_PLAY_BOUNDS.left, PVP_PLAY_BOUNDS.right);
    let targetY = clamp(Number(pose.y), PVP_PLAY_BOUNDS.top, PVP_PLAY_BOUNDS.bottom);
    const dx = targetX - player.x, dy = targetY - player.y, d = Math.hypot(dx, dy);
    const normalAllowance = PLAYER_SPEED * (stepMs / 1000) * CLIENT_POSE_SPEED_FACTOR + 22;
    const allowance = Number(player.lastPoseSeq) ? normalAllowance : Math.max(normalAllowance, CLIENT_POSE_FIRST_ALLOWANCE_PX);
    if (d > allowance && d > 0) {
      const scale = allowance / d;
      targetX = player.x + dx * scale;
      targetY = player.y + dy * scale;
    }
    moveHistoryPlayer(player, targetX - player.x, targetY - player.y, COMBAT_ENTITY_RADIUS, this.room.doorState,this.room.objectState);
    if (Number.isFinite(Number(pose.heading))) player.heading = Number(pose.heading);
    if (Number(pose.facing)) player.facing = Number(pose.facing) < 0 ? -1 : 1;
    player.lastPoseSeq = seq; player.lastPoseAt = now;
    return true;
  }

  armKnockback(target, dirX, dirY, force = HISTORY_KNOCK_FORCE, timeMs = HISTORY_KNOCK_TIME_MS) {
    if (!target?.alive || !(force > 0) || !(timeMs > 0)) return null;
    let dx = Number(dirX) || 0, dy = Number(dirY) || 0, len = Math.hypot(dx, dy);
    if (len < .001) { dx = Number(target.facing) < 0 ? -1 : 1; dy = 0; len = 1; }
    dx /= len; dy /= len;
    target.knockUntil = Date.now() + timeMs;
    target.knockVX = dx * force; target.knockVY = dy * force;
    target.moving = false;
    return { dirX: dx, dirY: dy, force, timeMs, tilt: HISTORY_HIT_TILT };
  }

  stepKnockback(target, dt, now) {
    if (!target?.alive || now >= Number(target.knockUntil || 0)) {
      if (target) { target.knockUntil = 0; target.knockVX = 0; target.knockVY = 0; }
      return false;
    }
    const knockDx = (Number(target.knockVX) || 0) * dt, knockDy = (Number(target.knockVY) || 0) * dt;
    if (this.room?.players?.[target.id] === target) moveHistoryPlayer(target, knockDx, knockDy, COMBAT_ENTITY_RADIUS, this.room.doorState,this.room.objectState);
    else moveHistoryEnemy(target, knockDx, knockDy, COMBAT_ENTITY_RADIUS, this.room.doorState,this.room.objectState);
    const damping = Math.pow(.16, dt);
    target.knockVX *= damping; target.knockVY *= damping; target.moving = false;
    return true;
  }

  emitDamage(targetKind, target, amount, kind, sourceId = null, impact = null) {
    this.broadcast({
      type: "damage", targetKind, targetId: target.id, sourceId, amount,
      kind, hp: target.hp, shield: target.shield, alive: target.alive !== false,
      respawnAt: Number(target.respawnAt) || 0, impact, at: Date.now()
    });
  }

  applyDamage(targetKind, target, amount, kind, sourceId = null, impact = null) {
    if (!target?.alive || !(amount > 0)) return 0;
    let remaining = Number(amount) || 0;
    const before = (Number(target.hp) || 0) + (Number(target.shield) || 0);
    if (target.shield > 0) {
      const absorbed = Math.min(target.shield, remaining);
      target.shield -= absorbed;
      remaining -= absorbed;
    }
    if (remaining > 0) target.hp = Math.max(0, Number(target.hp) - remaining);
    const after = (Number(target.hp) || 0) + (Number(target.shield) || 0);
    const dealt = Math.max(0, before - after);
    if (dealt > 0) this.emitDamage(targetKind, target, dealt, kind, sourceId, impact);
    return dealt;
  }

  defeatPlayer(player, now = Date.now()) {
    if (!player?.alive || player.hp > 0) return;
    player.alive = false;
    player.moving = false;
    player.respawnAt = now + PLAYER_RESPAWN_MS;
    player.input = { dx: 0, dy: 0 };
    player.burnUntil = 0; player.burnNextTick = 0; player.burnSourceId = null; player.burnSourceX = 0; player.burnSourceY = 0;
    player.singleUntil = 0; player.lastBasicAt = 0;
    player.comboStartedAt = 0; player.comboUntil = 0; player.comboHitIndex = 0; player.comboSfxIndex = 0; player.comboRequestUntil = 0;
    player.specialStartedAt = 0; player.specialActiveUntil = 0; player.specialHitState = {};
    this.broadcast({ type: "player_defeated", uid: player.id, respawnAt: player.respawnAt, at: now });
  }

  actionPayload(player, action, kind, extra = {}, now = Date.now()) {
    return {
      type: "action", uid: player.id, action, kind,
      attackSerial: Number(player.attackSerial) || 0,
      comboStep: Number(player.comboStep) || 0,
      singleSerial: Number(player.singleSerial) || 0,
      singleUntil: Number(player.singleUntil) || 0,
      comboSerial: Number(player.comboSerial) || 0,
      comboStartedAt: Number(player.comboStartedAt) || 0,
      comboUntil: Number(player.comboUntil) || 0,
      comboRequestUntil: Number(player.comboRequestUntil) || 0,
      specialSerial: Number(player.specialSerial) || 0,
      specialStartedAt: Number(player.specialStartedAt) || 0,
      specialActiveUntil: Number(player.specialActiveUntil) || 0,
      angle: Number(player.specialAngle) || Number(player.heading) || 0,
      heading: Number(player.heading) || 0,
      facing: Number(player.facing) < 0 ? -1 : 1,
      ...extra, at: now
    };
  }

  registerWarriorBasicHit(player) {
    if (!player || player.specialUnlocked) return;
    player.specialHits = Math.min(WARRIOR_SPECIAL_UNLOCK_HITS, (Number(player.specialHits) || 0) + 1);
    if (player.specialHits >= WARRIOR_SPECIAL_UNLOCK_HITS) player.specialUnlocked = true;
  }

  cancelWarriorCombo(player) {
    if (!player) return;
    player.comboStartedAt = 0;
    player.comboUntil = 0;
    player.comboHitIndex = 0;
    player.comboSfxIndex = 0;
    player.comboRequestUntil = 0;
    player.lastBasicAt = 0;
  }

  startWarriorCombo(player, now) {
    player.comboStartedAt = now;
    player.comboUntil = now + WARRIOR_COMBO_DURATION_MS;
    player.comboSerial = (Number(player.comboSerial) || 0) + 1;
    player.singleSerial = (Number(player.singleSerial) || 0) + 1;
    player.comboSfxIndex = 1;
    player.comboHitIndex = 0;
    player.comboRequestUntil = now + WARRIOR_COMBO_CONTINUE_MS;
    player.singleUntil = 0;
    player.lastBasicAt = 0;
    player.attackCooldownUntil = 0;
    player.attackSerial = (Number(player.attackSerial) || 0) + 1;
    this.broadcast({
      type: "combat_sfx", uid: player.id, event: "warrior-single",
      serial: player.singleSerial, volume: .38, at: now
    });
  }

  updateWarriorCombo(player, now) {
    if (!player?.alive || !(Number(player.comboUntil) > 0)) return false;
    const end = Number(player.comboUntil) || 0;
    const start = Number(player.comboStartedAt) || now;
    if (Number(player.comboRequestUntil) > 0 && now > Number(player.comboRequestUntil)) {
      this.cancelWarriorCombo(player);
      this.broadcast(this.actionPayload(player, "attack", "combo-cancel", {}, now));
      return false;
    }
    const duration = Math.max(1, end - start);
    const sfxFractions = [0, .50, .86];
    const sfxVolumes = [.38, .52, .38];
    while ((Number(player.comboSfxIndex) || 0) < sfxFractions.length &&
           now >= start + duration * sfxFractions[Number(player.comboSfxIndex) || 0]) {
      const index = Number(player.comboSfxIndex) || 0;
      player.singleSerial = (Number(player.singleSerial) || 0) + 1;
      this.broadcast({
        type: "combat_sfx", uid: player.id, event: "warrior-single",
        serial: player.singleSerial, volume: sfxVolumes[index], at: now
      });
      player.comboSfxIndex = index + 1;
    }

    const hitFractions = [.18, .50, .82];
    while ((Number(player.comboHitIndex) || 0) < hitFractions.length &&
           now >= start + duration * hitFractions[Number(player.comboHitIndex) || 0]) {
      const living = this.room.dragons.filter(d => d.alive && historyLineOfSight(player,d,this.room.doorState,0,this.room.objectState));
      const target = living.slice().sort((a, b) => distance(player, a) - distance(player, b))[0];
      if (target) {
        const d = distance(player, target);
        player.heading = Math.atan2(target.y - player.y, target.x - player.x);
        if (Math.abs(target.x - player.x) > 3) player.facing = target.x < player.x ? -1 : 1;
        if (d <= WARRIOR_COMBO_RANGE + COMBAT_ENTITY_RADIUS * .36) {
          const impact = this.armKnockback(target, target.x - player.x, target.y - player.y);
          const dealt = this.damageDragon(target, warriorDamageForRange(d), "melee", player.id, impact);
          if (dealt > 0) this.registerWarriorBasicHit(player);
        }
      }
      this.hitMapObjects(player,WARRIOR_DAMAGE_MAX,WARRIOR_COMBO_RANGE,now);
      player.comboHitIndex = (Number(player.comboHitIndex) || 0) + 1;
    }

    if (now < end) return true;
    const repeat = Number(player.comboRequestUntil) >= now;
    this.cancelWarriorCombo(player);
    if (repeat) {
      this.startWarriorCombo(player, now);
      this.broadcast(this.actionPayload(player, "attack", "combo", {}, now));
    } else {
      this.broadcast(this.actionPayload(player, "attack", "combo-cancel", {}, now));
    }
    return false;
  }

  applyAction(player, action, message = {}) {
    const now = Date.now();
    if (!player?.alive) return;

    if (action === "combo_cancel") {
      this.cancelWarriorCombo(player);
      this.broadcast(this.actionPayload(player, "attack", "combo-cancel", {}, now));
      return;
    }

    const living = this.room.dragons.filter(d => d.alive && historyLineOfSight(player,d,this.room.doorState,0,this.room.objectState));
    // Empty space still permits attacking editor destructibles.


    if (action === "special") {
      if (!player.specialUnlocked || now < Number(player.specialCooldownUntil || 0) ||
          now < Number(player.specialActiveUntil || 0) || now < Number(player.knockUntil || 0)) return;
      this.cancelWarriorCombo(player);
      player.singleUntil = 0;
      player.lastBasicAt = 0;
      const requestedAngle = Number(message.angle);
      player.specialAngle = Number.isFinite(requestedAngle) ? requestedAngle : Number(player.heading) || 0;
      player.heading = player.specialAngle;
      player.facing = Math.cos(player.specialAngle) < 0 ? -1 : 1;
      player.specialCooldownUntil = now + WARRIOR_SPECIAL_COOLDOWN_MS;
      player.specialStartedAt = now;
      player.specialActiveUntil = now + WARRIOR_SPECIAL_DURATION_MS;
      player.specialSerial = (Number(player.specialSerial) || 0) + 1;
      player.specialHitState = {};
      player.knockUntil = 0; player.knockVX = 0; player.knockVY = 0;
      const before = Number(player.hp) || 0;
      player.hp = Math.min(Number(player.maxHp) || PLAYER_MAX_HP, before + WARRIOR_SPECIAL_HEAL);
      if (player.hp > before) player.regenSerial = (Number(player.regenSerial) || 0) + 1;
      this.broadcast(this.actionPayload(player, "special", "special", {}, now));
      return;
    }

    if (now < Number(player.specialActiveUntil || 0) || now < Number(player.knockUntil || 0)) return;

    if (Number(player.comboUntil) > now) {
      player.comboRequestUntil = now + WARRIOR_COMBO_CONTINUE_MS;
      player.attackSerial = (Number(player.attackSerial) || 0) + 1;
      this.broadcast(this.actionPayload(player, "attack", "combo-continue", {}, now));
      return;
    }

    const sinceLast = now - Number(player.lastBasicAt || 0);
    if (Number(player.lastBasicAt) > 0 && sinceLast >= WARRIOR_COMBO_CHAIN_MIN_MS && sinceLast <= WARRIOR_COMBO_CHAIN_MS) {
      this.startWarriorCombo(player, now);
      this.broadcast(this.actionPayload(player, "attack", "combo", {}, now));
      return;
    }

    if (now < Number(player.attackCooldownUntil || 0)) return;
    player.attackCooldownUntil = now + WARRIOR_MELEE_COOLDOWN_MS;
    player.attackSerial = (Number(player.attackSerial) || 0) + 1;
    player.comboStep = ((Number(player.comboStep) || 0) % 2) + 1;
    player.lastBasicAt = now;
    player.singleSerial = (Number(player.singleSerial) || 0) + 1;
    player.singleUntil = now + WARRIOR_SINGLE_VISUAL_MS;

    const target = living.slice().sort((a, b) => distance(player, a) - distance(player, b))[0];
    let hit = false;
    if (target) {
      const d = distance(player, target);
      player.heading = Math.atan2(target.y - player.y, target.x - player.x);
      if (Math.abs(target.x - player.x) > 3) player.facing = target.x < player.x ? -1 : 1;
      if (d <= WARRIOR_MELEE_RANGE + COMBAT_ENTITY_RADIUS * .36) {
        const impact = this.armKnockback(target, target.x - player.x, target.y - player.y);
        const dealt = this.damageDragon(target, warriorDamageForRange(d), "melee", player.id, impact);
        hit = dealt > 0;
        if (hit) this.registerWarriorBasicHit(player);
      }
    }
    this.hitMapObjects(player,WARRIOR_DAMAGE_MAX,WARRIOR_MELEE_RANGE,now);
    this.broadcast(this.actionPayload(player, "attack", "single", { targetId: target?.id || null, hit }, now));
  }

  damageDragon(dragon, amount, kind = "player", sourceId = null, impact = null) {
    if (!dragon?.alive) return 0;
    const dealt = this.applyDamage("enemy", dragon, amount, kind, sourceId, impact);
    if (dragon.type === "dragon" && dealt > 0 && dragon.alive && dragon.hp > 0 && sourceId) {
      const first = !dragon.firstHitSeen;
      dragon.firstHitSeen = true; dragon.retaliatePending = true; dragon.retaliateTargetId = sourceId;
      if (first) {
        dragon.retaliateImmediate = true; dragon.npcNextAttackAt = 0; dragon.nextShotAt = 0; dragon.closeShotAt = 0;
      }
    }
    if (dragon.hp <= 0) {
      const defeatedAt = Date.now();
      dragon.alive = false; dragon.moving = false; dragon.removeAt = defeatedAt + 1400;
      this.registerDoorDefeat(dragon, defeatedAt);
    }
    return dealt;
  }

  igniteBurn(player, dragon, now) {
    if (!player?.alive) return;
    player.burnSerial = (Number(player.burnSerial) || 0) + 1;
    player.burnUntil = now + DRAGON_BURN_DURATION_MS;
    player.burnNextTick = now + DRAGON_BURN_TICK_MS;
    player.burnSourceId = dragon?.id || null;
    player.burnSourceX = Number(dragon?.x) || Number(player.x) || 0;
    player.burnSourceY = Number(dragon?.y) || Number(player.y) || 0;
    this.broadcast({
      type: "burn", targetId: player.id, sourceId: player.burnSourceId,
      serial: player.burnSerial, burnUntil: player.burnUntil, at: now
    });
  }

  launchDragonFireball(dragon, target, now, emergency = false) {
    if (!dragon?.alive || dragon.flightState !== "flying" || !target?.alive) return false;
    const gate = emergency ? Number(dragon.closeShotAt || 0) : Number(dragon.nextShotAt || 0);
    if (now < gate || now < Number(dragon.attackUntil || 0)) return false;

    if(!historyLineOfSight(dragon,target,this.room.doorState,8,this.room.objectState))return false;
    const muzzleAngle=Math.atan2(target.y-dragon.y,target.x-dragon.x);
    if(!historyLineOfSight(dragon,{x:dragon.x+Math.cos(muzzleAngle)*42,y:dragon.y-16+Math.sin(muzzleAngle)*18},this.room.doorState,8,this.room.objectState))return false;
    const angle = Math.atan2(target.y - dragon.y, target.x - dragon.x);
    dragon.heading = angle;
    dragon.facing = target.x < dragon.x ? -1 : 1;
    dragon.moving = false;
    dragon.attackSerial = (Number(dragon.attackSerial) || 0) + 1;
    dragon.attackUntil = now + DRAGON_ATTACK_VISUAL_MS;
    dragon.npcNextAttackAt = now + Math.max(2000, DRAGON_ATTACK_VISUAL_MS);

    if (emergency) {
      dragon.closeShotAt = now + DRAGON_CLOSE_SHOT_COOLDOWN_MS;
      dragon.nextShotAt = Math.max(Number(dragon.nextShotAt) || 0, now + DRAGON_SHOT_COOLDOWN_MS);
    } else {
      dragon.nextShotAt = now + DRAGON_SHOT_COOLDOWN_MS;
      dragon.closeShotAt = Math.max(Number(dragon.closeShotAt) || 0, now + DRAGON_CLOSE_SHOT_COOLDOWN_MS);
    }

    const startX = dragon.x + Math.cos(angle) * 42;
    const startY = dragon.y - 16 + Math.sin(angle) * 18;
    const projectile = {
      id: "hdf_" + (++this.projectileSeq) + "_" + now.toString(36),
      kind: "dragon", serial: dragon.attackSerial,
      x: startX, y: startY,
      vx: Math.cos(angle) * DRAGON_FIREBALL_SPEED,
      vy: Math.sin(angle) * DRAGON_FIREBALL_SPEED,
      speed: DRAGON_FIREBALL_SPEED, damage: DRAGON_DAMAGE, burn: true,
      targetId: target.id, team: "pvp-enemy", sourceId: dragon.id,
      createdAt: now, expireAt: now + 4500
    };
    this.room.projectiles.push(projectile);
    this.broadcast({
      type: "dragon_attack", dragonId: dragon.id, targetId: target.id,
      serial: dragon.attackSerial, attackUntil: dragon.attackUntil, projectile, at: now
    });
    return true;
  }

  updateProjectiles(dt, now) {
    const list = this.room.projectiles;
    for (let i = list.length - 1; i >= 0; i--) {
      const projectile = list[i];
      if (projectile.pvpHit) {
        if (now >= Number(projectile.hitUntil || 0)) list.splice(i, 1);
        continue;
      }
      if (now > Number(projectile.expireAt || 0)) { list.splice(i, 1); continue; }

      const sx = Number(projectile.x) || 0, sy = Number(projectile.y) || 0;
      const nx = sx + (Number(projectile.vx) || 0) * dt;
      const ny = sy + (Number(projectile.vy) || 0) * dt;
      const wall=HistoryRules.firstWallHit(HISTORY_GEOMETRY,this.room.doorState,sx,sy,nx,ny,8,this.room.objectState);
      let target=null,hitTime=Infinity;
      for(const p of Object.values(this.room.players)) {
        if(!p.alive)continue;
        const t=HistoryRules.circleHitTime(sx,sy,nx,ny,p.x,p.y,COMBAT_ENTITY_RADIUS+8);
        if(t!==null&&t<hitTime){target=p;hitTime=t;}
      }
      if(wall!==null&&wall<=hitTime) {
        list.splice(i,1);
        this.broadcast({type:"projectile_blocked",projectileId:projectile.id,at:now});
        continue;
      }
      const hit=!!target;
      projectile.x = nx; projectile.y = ny;

      if (hit) {
        projectile.x = nx; projectile.y = ny;
        projectile.vx = 0; projectile.vy = 0;
        projectile.pvpHit = true; projectile.hitUntil = now + 400;
        this.broadcast({
          type: "projectile_hit", projectileId: projectile.id, x: projectile.x, y: projectile.y,
          hitUntil: projectile.hitUntil, targetId: target.id, at: now
        });
        const impact = this.armKnockback(target, Number(nx - sx) || 0, Number(ny - sy) || 0, 105, 60);
        if (impact) impact.tilt = 6;
        this.applyDamage("player", target, Number(projectile.damage)||DRAGON_DAMAGE, projectile.kind==="anubis"?"anubis_projectile":"fireball", projectile.sourceId, impact);
        if (target.hp <= 0) this.defeatPlayer(target, now);
        else if(projectile.burn!==false)this.igniteBurn(target, this.room.dragons.find(d => d.id === projectile.sourceId), now);
        continue;
      }

      if (nx < -80 || nx > PVP_WORLD.width + 80 || ny < -80 || ny > PVP_WORLD.height + 80) list.splice(i, 1);
    }
  }

  updateBurns(now) {
    for (const player of Object.values(this.room.players)) {
      if (!player.alive || !player.burnUntil) continue;
      while (player.alive && player.burnNextTick && now >= player.burnNextTick && player.burnNextTick <= player.burnUntil) {
        const burnImpact = normalizedImpact(
          { x: Number(player.burnSourceX) || player.x, y: Number(player.burnSourceY) || player.y, facing: 1 },
          player, 4
        );
        this.applyDamage("player", player, DRAGON_BURN_DAMAGE, "burn", player.burnSourceId, burnImpact);
        player.burnNextTick += DRAGON_BURN_TICK_MS;
        if (player.hp <= 0) this.defeatPlayer(player, now);
      }
      if (!player.alive || now > Number(player.burnUntil || 0)) {
        player.burnUntil = 0; player.burnNextTick = 0; player.burnSourceId = null; player.burnSourceX = 0; player.burnSourceY = 0;
      }
    }
  }

  updateDragons(dt, now) {
    for (const dragon of this.room.dragons) {
      if (!dragon.alive) continue;
      if (dragon.type !== "dragon") { this.updateGroundEnemy(dragon, dt, now); continue; }

      if (dragon.flightState === "takeoff") {
        dragon.moving = false;
        if (now >= Number(dragon.takeoffUntil || 0)) {
          dragon.flightState = "flying";
          dragon.takeoffUntil = 0;
          dragon.nextShotAt = Math.max(Number(dragon.nextShotAt) || 0, now + 150);
        }
        continue;
      }

      const players = Object.values(this.room.players).filter(p => p.alive && pointInArea(p.x, p.y, dragon.historyLeashArea));
      if (dragon.retaliatePending && dragon.flightState === "flying" && now >= Number(dragon.attackUntil || 0) &&
          (dragon.retaliateImmediate || now >= Number(dragon.npcNextAttackAt || 0))) {
        const retaliationTarget = this.room.players[dragon.retaliateTargetId];
        const target = retaliationTarget?.alive && pointInArea(retaliationTarget.x, retaliationTarget.y, dragon.historyLeashArea)
          ? retaliationTarget
          : players.reduce((best, p) => !best || distance(dragon, p) < distance(dragon, best) ? p : best, null);
        if (target) {
          if (dragon.retaliateImmediate) { dragon.nextShotAt = 0; dragon.closeShotAt = 0; }
          const emergency = distance(dragon, target) < DRAGON_CLOSE_RANGE;
          if (this.launchDragonFireball(dragon, target, now, emergency)) {
            dragon.retaliatePending = false; dragon.retaliateImmediate = false;
            dragon.nextShotAt = Math.max(Number(dragon.nextShotAt) || 0, Number(dragon.npcNextAttackAt) || 0);
            dragon.closeShotAt = Math.max(Number(dragon.closeShotAt) || 0, Number(dragon.npcNextAttackAt) || 0);
            continue;
          }
        }
      }

      if (this.stepKnockback(dragon, dt, now)) continue;
      if (!players.length) { dragon.moving = false; continue; }

      const visible=players.filter(p=>historyLineOfSight(dragon,p,this.room.doorState,8,this.room.objectState));
      const target = (visible.length?visible:players).reduce((best, p) => !best || distance(dragon, p) < distance(dragon, best) ? p : best, null);
      if (!target) { dragon.moving = false; continue; }

      const dx = target.x - dragon.x, dy = target.y - dragon.y, d = Math.hypot(dx, dy) || 1;
      dragon.heading = Math.atan2(dy, dx);
      dragon.facing = dx < 0 ? -1 : 1;

      if (now < Number(dragon.attackUntil || 0)) {
        dragon.moving = false;
        continue;
      }

      if(!historyLineOfSight(dragon,target,this.room.doorState,8,this.room.objectState)) {
        pursueHistoryEnemy(dragon,target,dt,this.room.doorState,now,this.room.objectState);continue;
      }
      if (d < DRAGON_CLOSE_RANGE) {
        if (now >= Number(dragon.closeShotAt || 0) && this.launchDragonFireball(dragon, target, now, true)) continue;
        let mx = -dx / d, my = -dy / d;
        const edge = 125;
        if (dragon.x < edge) mx += .85; else if (dragon.x > PVP_WORLD.width - edge) mx -= .85;
        if (dragon.y < edge) my += .85; else if (dragon.y > PVP_WORLD.height - edge) my -= .85;
        const ml = Math.hypot(mx, my) || 1; mx /= ml; my /= ml;
        moveHistoryEnemy(dragon, mx * DRAGON_SPEED * dt, my * DRAGON_SPEED * dt, COMBAT_ENTITY_RADIUS, this.room.doorState,this.room.objectState);
        dragon.moving = true;
        continue;
      }

      if (d >= 185 && d <= 285 && now >= Number(dragon.nextShotAt || 0)) {
        if (this.launchDragonFireball(dragon, target, now, false)) continue;
      }

      if (d > 285) {
        pursueHistoryEnemy(dragon,target,dt,this.room.doorState,now,this.room.objectState);
      } else if (d < 185) {
        moveHistoryEnemy(dragon, -dx / d * DRAGON_SPEED * dt, -dy / d * DRAGON_SPEED * dt, COMBAT_ENTITY_RADIUS, this.room.doorState,this.room.objectState);
        dragon.moving = true;
      } else dragon.moving = false;
    }
  }

  tick() {
    const now = Date.now();
    const dt = clamp((now - this.lastTickAt) / 1000, 0, 0.08);
    this.lastTickAt = now;
    this.updateDoors(now);

    for (const player of Object.values(this.room.players)) {
      if (!player.alive) {
        player.moving = false;
        if (player.respawnAt && now >= player.respawnAt) {
          player.alive = true; player.respawnAt = 0;
          player.hp = player.maxHp; player.shield = player.maxShield;
          const respawn = this.checkpointForPlayer(player);
          player.x = Number(respawn.x) || HISTORY_MAP_SPAWN.x; player.y = Number(respawn.y) || HISTORY_MAP_SPAWN.y;
          player.input = { dx: 0, dy: 0 };
          player.attackCooldownUntil = 0; player.singleUntil = 0; player.lastBasicAt = 0;
          player.comboStartedAt = 0; player.comboUntil = 0; player.comboHitIndex = 0; player.comboSfxIndex = 0; player.comboRequestUntil = 0;
          player.specialStartedAt = 0; player.specialActiveUntil = 0; player.specialHitState = {};
          player.burnUntil = 0; player.burnNextTick = 0; player.burnSourceId = null; player.burnSourceX = 0; player.burnSourceY = 0;
          this.broadcast({ type: "player_respawned", uid: player.id, at: now });
        }
        continue;
      }

      this.updateWarriorCombo(player, now);
      if (this.stepKnockback(player, dt, now)) continue;
      const specialActive = now < Number(player.specialActiveUntil || 0);
      let dx = Number(player.input?.dx) || 0, dy = Number(player.input?.dy) || 0;
      if (specialActive) {
        const angle = Number(player.specialAngle) || 0;
        dx = Math.cos(angle); dy = Math.sin(angle);
      }
      const moving = specialActive || Math.hypot(dx, dy) > 0.05;
      player.moving = moving;
      if (moving) {
        const speed = PLAYER_SPEED * (specialActive ? WARRIOR_SPECIAL_SPEED_MULTIPLIER : 1);
        moveHistoryPlayer(player, dx * speed * dt, dy * speed * dt, COMBAT_ENTITY_RADIUS, this.room.doorState,this.room.objectState);
      }

      if (specialActive) {
        this.hitMapObjects(player,WARRIOR_SPECIAL_DAMAGE_MAX,65,now,WARRIOR_SPECIAL_DURATION_MS/WARRIOR_SPECIAL_DAMAGE_HITS);
        const hitState = player.specialHitState && typeof player.specialHitState === "object"
          ? player.specialHitState : (player.specialHitState = {});
        const fractions = [0, .24, .49, .74, .96];
        for (const dragon of this.room.dragons) {
          if (!dragon.alive) continue;
          const contact = distance(player, dragon) <= COMBAT_ENTITY_RADIUS * 2 + 10;
          if (contact && !hitState[dragon.id]) {
            hitState[dragon.id] = { count: 0, startedAt: now, endAt: Number(player.specialActiveUntil) || now };
          }
          const sequence = hitState[dragon.id];
          if (!sequence || Number(sequence.count) >= WARRIOR_SPECIAL_DAMAGE_HITS) continue;
          const count = Number(sequence.count) || 0;
          const seqStart = Number(sequence.startedAt) || now;
          const seqEnd = Math.max(seqStart + 1, Number(sequence.endAt) || Number(player.specialActiveUntil) || now);
          const dueAt = seqStart + (seqEnd - seqStart) * fractions[count];
          if (now < dueAt) continue;

          sequence.count = count + 1;
          const finalHit = sequence.count >= WARRIOR_SPECIAL_DAMAGE_HITS;
          let impact;
          if (finalHit) {
            const angle = Number(player.specialAngle) || 0;
            const sideAxisX = -Math.sin(angle), sideAxisY = Math.cos(angle);
            const sideDot = (dragon.x - player.x) * sideAxisX + (dragon.y - player.y) * sideAxisY;
            const side = sideDot === 0 ? (String(dragon.id).endsWith("a") ? 1 : -1) : (sideDot > 0 ? 1 : -1);
            let knockX = sideAxisX * side, knockY = sideAxisY * side;
            if (Math.abs(knockX) < .20) knockX = .20 * side;
            const knockLen = Math.hypot(knockX, knockY) || 1;
            impact = this.armKnockback(
              dragon, knockX / knockLen, knockY / knockLen,
              WARRIOR_SPECIAL_KNOCK_FORCE, WARRIOR_SPECIAL_KNOCK_TIME_MS
            );
            if (impact) impact.tilt = WARRIOR_SPECIAL_HIT_TILT;
          } else {
            impact = normalizedImpact(player, dragon, 4);
          }
          this.damageDragon(dragon, randomWarriorSpecialDamage(), "special", player.id, impact);
        }
      }
    }

    this.updateObjects(now);
    this.updateBosses(now);
    this.updateSpawnEvents(now);
    this.updateDragons(dt, now);
    this.updateProjectiles(dt, now);
    this.updateBurns(now);
    this.updateMapProgress(now);
    this.room.dragons = this.room.dragons.filter(enemy => enemy.alive || now < Number(enemy.removeAt || 0));

    this.room.seq++;
    if (now - this.lastBroadcastAt >= 50) {
      this.lastBroadcastAt = now;
      this.broadcast({ type: "snapshot", snapshot: this.snapshot() });
    }
    if (now - this.lastPersistAt >= 1000) {
      this.lastPersistAt = now;
      this.ctx.storage.put("room", this.room).catch(() => {});
    }
  }

  ensureLoop() {
    if (this.loop) return;
    this.lastTickAt = Date.now();
    this.loop = setInterval(() => {
      try { this.tick(); } catch (error) { console.error("History tick", error); }
    }, 33);
  }

  stopLoop() {
    if (this.loop) clearInterval(this.loop);
    this.loop = null;
    this.ctx.storage.put("room", this.room).catch(() => {});
  }

  publicPlayers() {
    return Object.values(this.room.players).map(({ input, specialHitState, ...player }) => player);
  }

  snapshot() {
    return {
      seq: this.room.seq,
      serverTime: Date.now(),
      mode: "history",
      map: HISTORY_MAP_ID,
      world: PVP_WORLD,
      playBounds: PVP_PLAY_BOUNDS,
      rounds: null,
      players: this.publicPlayers(),
      enemies: this.room.dragons.map(({historyRoute,...enemy})=>enemy),
      dragons: this.room.dragons.filter(enemy => enemy.type === "dragon").map(({historyRoute,...enemy})=>enemy),
      finished: !!this.room.finished,
      victoryAt: Number(this.room.victoryAt) || 0,
      spawnState: this.room.spawnState,
      doorState: this.room.doorState,
      objectState: this.room.objectState,
      projectiles: this.room.projectiles.map(p => ({
        id: p.id, kind: p.kind, serial: p.serial, x: p.x, y: p.y, vx: p.vx, vy: p.vy,
        speed: p.speed, damage: p.damage, burn: p.burn, targetId: p.targetId, team: p.team, sourceId: p.sourceId,
        expireAt: p.expireAt
      })),
      dragonWave: this.room.dragonWave,
      respawnAt: this.room.respawnAt
    };
  }

  send(ws, payload) {
    try { ws.send(JSON.stringify(payload)); } catch {}
  }

  broadcast(payload) {
    const raw = JSON.stringify(payload);
    for (const ws of this.clients.values()) {
      try { ws.send(raw); } catch {}
    }
  }
}
