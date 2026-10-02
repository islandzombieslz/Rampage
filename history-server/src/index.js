import { DurableObject } from "cloudflare:workers";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Allow-Methods": "GET,OPTIONS"
};

const SERVER_CATALOG = Object.freeze([
  { id: "history-1", name: "Servidor História 1", map: "arena-pvp", maxPlayers: 8 }
]);

const HISTORY_SCHEMA_VERSION = 3;
const PVP_WORLD = Object.freeze({ width: 1850, height: 1542 });
const PVP_PLAY_BOUNDS = Object.freeze({ left: 300, right: 1550, top: 305, bottom: 1267 });

const PLAYER_MAX_HP = 350;
const PLAYER_MAX_SHIELD = 250;
const PLAYER_SPEED = 195;
const PLAYER_RESPAWN_MS = 3000;

const WARRIOR_SPECIAL_UNLOCK_HITS = 5;
const WARRIOR_SPECIAL_COOLDOWN_MS = 20000;
const WARRIOR_SPECIAL_DURATION_MS = 1800;
const WARRIOR_SPECIAL_SPEED_MULTIPLIER = 1.45;

const DRAGON_MAX_HP = 100;
const DRAGON_MAX_SHIELD = 50;
const DRAGON_SPEED = 195;
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

const HISTORY_HEROES = Object.freeze({
  warrior: { id: "warrior", type: "warrior", clan: "warriors", variant: "male" },
  mageFemale: { id: "mageFemale", type: "mage", clan: "warriors", variant: "female" }
});
function historyHero(id) { return HISTORY_HEROES[id] || HISTORY_HEROES.warrior; }

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", ...CORS }
  });
}
function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
function distance(a, b) { return Math.hypot(a.x - b.x, a.y - b.y); }
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
    this.room.dragons ||= this.spawnDragons(Number(this.room.dragonWave) || 1);
  }

  createRoom() {
    return {
      schemaVersion: HISTORY_SCHEMA_VERSION,
      seq: 0,
      startedAt: Date.now(),
      players: {},
      dragons: this.spawnDragons(1),
      projectiles: [],
      dragonWave: 1,
      respawnAt: 0
    };
  }

  spawnDragons(wave) {
    const now = Date.now();
    const make = (id, x, y, facing) => ({
      id, type: "dragon", x, y,
      hp: DRAGON_MAX_HP, maxHp: DRAGON_MAX_HP,
      shield: DRAGON_MAX_SHIELD, maxShield: DRAGON_MAX_SHIELD,
      alive: true, facing, heading: facing < 0 ? Math.PI : 0, moving: false, wave,
      flightState: "takeoff", takeoffSerial: wave, takeoffUntil: now + DRAGON_TAKEOFF_MS,
      attackSerial: 0, attackUntil: 0, nextShotAt: now + DRAGON_TAKEOFF_MS + 180,
      closeShotAt: now + DRAGON_TAKEOFF_MS + 180
    });
    return [
      make("history-dragon-a", 670, 760, 1),
      make("history-dragon-b", 1180, 760, -1)
    ];
  }

  async fetch(request) {
    await this.ready;
    const url = new URL(request.url);

    if (url.pathname === "/info") {
      return json({ players: this.clients.size, dragonsAlive: this.room.dragons.filter(d => d.alive).length });
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
      x: PVP_WORLD.width / 2, y: 1040,
      hp: PLAYER_MAX_HP, maxHp: PLAYER_MAX_HP,
      shield: PLAYER_MAX_SHIELD, maxShield: PLAYER_MAX_SHIELD,
      alive: true, respawnAt: 0, facing: 1, heading: 0, moving: false, input: { dx: 0, dy: 0 },
      lastInputSeq: 0, attackCooldownUntil: 0,
      specialHits: 0, specialUnlocked: false, specialCooldownUntil: 0,
      specialActiveUntil: 0, specialAngle: 0, specialHitIds: [],
      burnUntil: 0, burnNextTick: 0, burnSerial: 0, burnSourceId: null
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
    if (!this.clients.size) this.stopLoop();
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
      player.input = { dx, dy };
      player.lastInputSeq = Math.max(Number(player.lastInputSeq) || 0, Number(message.seq) || 0);
      if (len > 0.05 && Date.now() >= Number(player.specialActiveUntil || 0)) {
        player.heading = Math.atan2(dy, dx);
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

  emitDamage(targetKind, target, amount, kind, sourceId = null) {
    this.broadcast({
      type: "damage", targetKind, targetId: target.id, sourceId, amount,
      kind, hp: target.hp, shield: target.shield, alive: target.alive !== false,
      respawnAt: Number(target.respawnAt) || 0, at: Date.now()
    });
  }

  applyDamage(targetKind, target, amount, kind, sourceId = null) {
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
    if (dealt > 0) this.emitDamage(targetKind, target, dealt, kind, sourceId);
    return dealt;
  }

  defeatPlayer(player, now = Date.now()) {
    if (!player?.alive || player.hp > 0) return;
    player.alive = false;
    player.moving = false;
    player.respawnAt = now + PLAYER_RESPAWN_MS;
    player.input = { dx: 0, dy: 0 };
    player.burnUntil = 0; player.burnNextTick = 0; player.burnSourceId = null;
    this.broadcast({ type: "player_defeated", uid: player.id, respawnAt: player.respawnAt, at: now });
  }

  applyAction(player, action, message = {}) {
    const now = Date.now();
    if (!player?.alive) return;
    const living = this.room.dragons.filter(d => d.alive);
    if (!living.length) return;

    if (action === "special") {
      if (!player.specialUnlocked || now < Number(player.specialCooldownUntil || 0) || now < Number(player.specialActiveUntil || 0)) return;
      const requestedAngle = Number(message.angle);
      player.specialAngle = Number.isFinite(requestedAngle) ? requestedAngle : Number(player.heading) || 0;
      player.heading = player.specialAngle;
      player.facing = Math.cos(player.specialAngle) < 0 ? -1 : 1;
      player.specialCooldownUntil = now + WARRIOR_SPECIAL_COOLDOWN_MS;
      player.specialActiveUntil = now + WARRIOR_SPECIAL_DURATION_MS;
      player.specialHitIds = [];
      this.broadcast({ type: "action", uid: player.id, action: "special", angle: player.specialAngle, at: now });
      return;
    }

    if (now < Number(player.attackCooldownUntil || 0)) return;
    player.attackCooldownUntil = now + 300;
    const target = living.slice().sort((a, b) => distance(player, a) - distance(player, b))[0];
    let hit = false;
    if (target && distance(player, target) <= 135) {
      const dealt = this.damageDragon(target, 32, "melee", player.id);
      hit = dealt > 0;
      if (hit) {
        player.specialHits = Math.min(WARRIOR_SPECIAL_UNLOCK_HITS, (Number(player.specialHits) || 0) + 1);
        if (player.specialHits >= WARRIOR_SPECIAL_UNLOCK_HITS) player.specialUnlocked = true;
      }
    }
    this.broadcast({ type: "action", uid: player.id, action: "attack", targetId: target?.id || null, hit, at: now });
  }

  damageDragon(dragon, amount, kind = "player", sourceId = null) {
    if (!dragon?.alive) return 0;
    const dealt = this.applyDamage("dragon", dragon, amount, kind, sourceId);
    if (dragon.hp <= 0) {
      dragon.alive = false;
      dragon.moving = false;
    }
    if (this.room.dragons.every(d => !d.alive) && !this.room.respawnAt) {
      this.room.respawnAt = Date.now() + 2000;
      this.room.projectiles = [];
      this.broadcast({ type: "dragons_defeated", respawnAt: this.room.respawnAt });
    }
    return dealt;
  }

  igniteBurn(player, dragon, now) {
    if (!player?.alive) return;
    player.burnSerial = (Number(player.burnSerial) || 0) + 1;
    player.burnUntil = now + DRAGON_BURN_DURATION_MS;
    player.burnNextTick = now + DRAGON_BURN_TICK_MS;
    player.burnSourceId = dragon?.id || null;
    this.broadcast({
      type: "burn", targetId: player.id, sourceId: player.burnSourceId,
      serial: player.burnSerial, burnUntil: player.burnUntil, at: now
    });
  }

  launchDragonFireball(dragon, target, now, emergency = false) {
    if (!dragon?.alive || dragon.flightState !== "flying" || !target?.alive) return false;
    const gate = emergency ? Number(dragon.closeShotAt || 0) : Number(dragon.nextShotAt || 0);
    if (now < gate || now < Number(dragon.attackUntil || 0)) return false;

    const angle = Math.atan2(target.y - dragon.y, target.x - dragon.x);
    dragon.heading = angle;
    dragon.facing = target.x < dragon.x ? -1 : 1;
    dragon.moving = false;
    dragon.attackSerial = (Number(dragon.attackSerial) || 0) + 1;
    dragon.attackUntil = now + DRAGON_ATTACK_VISUAL_MS;

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
      if (now > Number(projectile.expireAt || 0)) { list.splice(i, 1); continue; }

      const sx = Number(projectile.x) || 0, sy = Number(projectile.y) || 0;
      const nx = sx + (Number(projectile.vx) || 0) * dt;
      const ny = sy + (Number(projectile.vy) || 0) * dt;
      const target = this.room.players[projectile.targetId];
      const hit = !!target?.alive && distanceToSegment(target.x, target.y, sx, sy, nx, ny) <= 44;
      projectile.x = nx; projectile.y = ny;

      if (hit) {
        this.applyDamage("player", target, DRAGON_DAMAGE, "fireball", projectile.sourceId);
        if (target.hp <= 0) this.defeatPlayer(target, now);
        else this.igniteBurn(target, this.room.dragons.find(d => d.id === projectile.sourceId), now);
        list.splice(i, 1);
        continue;
      }

      if (nx < -80 || nx > PVP_WORLD.width + 80 || ny < -80 || ny > PVP_WORLD.height + 80) list.splice(i, 1);
    }
  }

  updateBurns(now) {
    for (const player of Object.values(this.room.players)) {
      if (!player.alive || !player.burnUntil) continue;
      while (player.alive && player.burnNextTick && now >= player.burnNextTick && player.burnNextTick <= player.burnUntil) {
        this.applyDamage("player", player, DRAGON_BURN_DAMAGE, "burn", player.burnSourceId);
        player.burnNextTick += DRAGON_BURN_TICK_MS;
        if (player.hp <= 0) this.defeatPlayer(player, now);
      }
      if (!player.alive || now > Number(player.burnUntil || 0)) {
        player.burnUntil = 0; player.burnNextTick = 0; player.burnSourceId = null;
      }
    }
  }

  updateDragons(dt, now) {
    for (const dragon of this.room.dragons) {
      if (!dragon.alive) continue;

      if (dragon.flightState === "takeoff") {
        dragon.moving = false;
        if (now >= Number(dragon.takeoffUntil || 0)) {
          dragon.flightState = "flying";
          dragon.takeoffUntil = 0;
          dragon.nextShotAt = Math.max(Number(dragon.nextShotAt) || 0, now + 150);
        }
        continue;
      }

      const players = Object.values(this.room.players).filter(p => p.alive);
      if (!players.length) { dragon.moving = false; continue; }

      const target = players.reduce((best, p) => !best || distance(dragon, p) < distance(dragon, best) ? p : best, null);
      if (!target) { dragon.moving = false; continue; }

      const dx = target.x - dragon.x, dy = target.y - dragon.y, d = Math.hypot(dx, dy) || 1;
      dragon.heading = Math.atan2(dy, dx);
      dragon.facing = dx < 0 ? -1 : 1;

      if (now < Number(dragon.attackUntil || 0)) {
        dragon.moving = false;
        continue;
      }

      if (d < DRAGON_CLOSE_RANGE) {
        if (now >= Number(dragon.closeShotAt || 0) && this.launchDragonFireball(dragon, target, now, true)) continue;
        let mx = -dx / d, my = -dy / d;
        const edge = 125;
        if (dragon.x < edge) mx += .85; else if (dragon.x > PVP_WORLD.width - edge) mx -= .85;
        if (dragon.y < edge) my += .85; else if (dragon.y > PVP_WORLD.height - edge) my -= .85;
        const ml = Math.hypot(mx, my) || 1; mx /= ml; my /= ml;
        dragon.x = clamp(dragon.x + mx * DRAGON_SPEED * dt, PVP_PLAY_BOUNDS.left, PVP_PLAY_BOUNDS.right);
        dragon.y = clamp(dragon.y + my * DRAGON_SPEED * dt, PVP_PLAY_BOUNDS.top, PVP_PLAY_BOUNDS.bottom);
        dragon.moving = true;
        continue;
      }

      if (d >= 185 && d <= 285 && now >= Number(dragon.nextShotAt || 0)) {
        if (this.launchDragonFireball(dragon, target, now, false)) continue;
      }

      if (d > 285) {
        dragon.x = clamp(dragon.x + dx / d * DRAGON_SPEED * dt, PVP_PLAY_BOUNDS.left, PVP_PLAY_BOUNDS.right);
        dragon.y = clamp(dragon.y + dy / d * DRAGON_SPEED * dt, PVP_PLAY_BOUNDS.top, PVP_PLAY_BOUNDS.bottom);
        dragon.moving = true;
      } else if (d < 185) {
        dragon.x = clamp(dragon.x - dx / d * DRAGON_SPEED * dt, PVP_PLAY_BOUNDS.left, PVP_PLAY_BOUNDS.right);
        dragon.y = clamp(dragon.y - dy / d * DRAGON_SPEED * dt, PVP_PLAY_BOUNDS.top, PVP_PLAY_BOUNDS.bottom);
        dragon.moving = true;
      } else dragon.moving = false;
    }
  }

  tick() {
    const now = Date.now();
    const dt = clamp((now - this.lastTickAt) / 1000, 0, 0.08);
    this.lastTickAt = now;

    for (const player of Object.values(this.room.players)) {
      if (!player.alive) {
        player.moving = false;
        if (player.respawnAt && now >= player.respawnAt) {
          player.alive = true; player.respawnAt = 0;
          player.hp = player.maxHp; player.shield = player.maxShield;
          player.x = PVP_WORLD.width / 2; player.y = 1040;
          player.input = { dx: 0, dy: 0 };
          player.burnUntil = 0; player.burnNextTick = 0; player.burnSourceId = null;
          this.broadcast({ type: "player_respawned", uid: player.id, at: now });
        }
        continue;
      }

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
        player.x = clamp(player.x + dx * speed * dt, PVP_PLAY_BOUNDS.left, PVP_PLAY_BOUNDS.right);
        player.y = clamp(player.y + dy * speed * dt, PVP_PLAY_BOUNDS.top, PVP_PLAY_BOUNDS.bottom);
      }

      if (specialActive) {
        const hitIds = Array.isArray(player.specialHitIds) ? player.specialHitIds : (player.specialHitIds = []);
        for (const dragon of this.room.dragons) {
          if (!dragon.alive || hitIds.includes(dragon.id) || distance(player, dragon) > 105) continue;
          hitIds.push(dragon.id);
          this.damageDragon(dragon, 65, "special", player.id);
        }
      }
    }

    this.updateDragons(dt, now);
    this.updateProjectiles(dt, now);
    this.updateBurns(now);

    if (this.room.respawnAt && now >= this.room.respawnAt) {
      this.room.dragonWave++;
      this.room.dragons = this.spawnDragons(this.room.dragonWave);
      this.room.projectiles = [];
      this.room.respawnAt = 0;
      this.broadcast({ type: "dragons_respawned", wave: this.room.dragonWave, dragons: this.room.dragons });
    }

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
    return Object.values(this.room.players).map(({ input, specialHitIds, ...player }) => player);
  }

  snapshot() {
    return {
      seq: this.room.seq,
      serverTime: Date.now(),
      mode: "history",
      map: "arena-pvp",
      world: PVP_WORLD,
      playBounds: PVP_PLAY_BOUNDS,
      rounds: null,
      players: this.publicPlayers(),
      dragons: this.room.dragons,
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
