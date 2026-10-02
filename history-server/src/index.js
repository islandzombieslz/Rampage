import { DurableObject } from "cloudflare:workers";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Allow-Methods": "GET,OPTIONS"
};

const SERVER_CATALOG = Object.freeze([
  { id: "history-1", name: "Servidor História 1", map: "arena-pvp", maxPlayers: 8 }
]);
const PVP_WORLD = Object.freeze({ width: 2200, height: 1400 });
const PVP_PLAY_BOUNDS = Object.freeze({ left: 300, right: 1900, top: 305, bottom: 1125 });

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", ...CORS }
  });
}

function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
function distance(a, b) { return Math.hypot(a.x - b.x, a.y - b.y); }

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      return json({ ok: true, service: "rampage-history", version: 1 });
    }

    if (url.pathname === "/servers") {
      const servers = await Promise.all(SERVER_CATALOG.map(async server => {
        try {
          const stub = env.HISTORY_ROOMS.getByName(server.id);
          const info = await stub.fetch(new Request("https://history.internal/info"));
          const runtime = info.ok ? await info.json() : {};
          return { ...server, online: true, players: Number(runtime.players) || 0 };
        } catch {
          return { ...server, online: true, players: 0 };
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
    this.ready = this.load();
  }

  async load() {
    const saved = await this.ctx.storage.get("room");
    this.room = saved || this.createRoom();
  }

  createRoom() {
    return {
      seq: 0,
      startedAt: Date.now(),
      players: {},
      dragons: this.spawnDragons(1),
      dragonWave: 1,
      respawnAt: 0
    };
  }

  spawnDragons(wave) {
    const hp = 1800;
    return [
      { id: "history-dragon-a", type: "dragon", x: 780, y: 720, hp, maxHp: hp, alive: true, facing: 1, heading: 0, wave },
      { id: "history-dragon-b", type: "dragon", x: 1620, y: 720, hp, maxHp: hp, alive: true, facing: -1, heading: Math.PI, wave }
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
    const pair = new WebSocketPair();
    const [client, server] = Object.values(pair);
    server.accept();

    this.clients.set(uid, server);
    const previous = this.room.players[uid];
    this.room.players[uid] = previous || {
      id: uid, name, x: 1200, y: 930, hp: 200, maxHp: 200,
      facing: 1, heading: 0, moving: false, input: { dx: 0, dy: 0 },
      attackCooldownUntil: 0, specialCooldownUntil: 0
    };
    this.room.players[uid].name = name;

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
    if (this.room?.players?.[uid]) {
      this.room.players[uid].moving = false;
      this.room.players[uid].input = { dx: 0, dy: 0 };
    }
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
      let dx = clamp(Number(message.dx) || 0, -1, 1);
      let dy = clamp(Number(message.dy) || 0, -1, 1);
      const len = Math.hypot(dx, dy);
      if (len > 1) { dx /= len; dy /= len; }
      player.input = { dx, dy };
      if (len > 0.05) {
        player.heading = Math.atan2(dy, dx);
        player.facing = dx < 0 ? -1 : dx > 0 ? 1 : player.facing;
      }
      return;
    }

    if (message.type === "action") {
      this.applyAction(player, String(message.action || "attack"));
      return;
    }

    if (message.type === "ping") {
      const ws = this.clients.get(uid);
      if (ws) this.send(ws, { type: "pong", t: message.t || 0, serverTime: Date.now() });
    }
  }

  applyAction(player, action) {
    const now = Date.now();
    const living = this.room.dragons.filter(d => d.alive);
    if (!living.length) return;

    if (action === "special") {
      if (now < player.specialCooldownUntil) return;
      player.specialCooldownUntil = now + 8000;
      for (const dragon of living) {
        if (distance(player, dragon) <= 260) this.damageDragon(dragon, 90);
      }
      this.broadcast({ type: "action", uid: player.id, action: "special", at: now });
      return;
    }

    if (now < player.attackCooldownUntil) return;
    player.attackCooldownUntil = now + 430;
    const target = living.sort((a, b) => distance(player, a) - distance(player, b))[0];
    if (target && distance(player, target) <= 125) this.damageDragon(target, 32);
    this.broadcast({ type: "action", uid: player.id, action: "attack", targetId: target?.id || null, at: now });
  }

  damageDragon(dragon, amount) {
    if (!dragon?.alive) return;
    dragon.hp = Math.max(0, Number(dragon.hp) - Math.max(0, Number(amount) || 0));
    if (dragon.hp <= 0) dragon.alive = false;
    if (this.room.dragons.every(d => !d.alive) && !this.room.respawnAt) {
      this.room.respawnAt = Date.now() + 2000;
      this.broadcast({ type: "dragons_defeated", respawnAt: this.room.respawnAt });
    }
  }

  tick() {
    const now = Date.now();
    const dt = clamp((now - this.lastTickAt) / 1000, 0, 0.1);
    this.lastTickAt = now;

    for (const player of Object.values(this.room.players)) {
      const dx = Number(player.input?.dx) || 0, dy = Number(player.input?.dy) || 0;
      const moving = Math.hypot(dx, dy) > 0.05;
      player.moving = moving;
      if (moving) {
        const speed = 225;
        player.x = clamp(player.x + dx * speed * dt, PVP_PLAY_BOUNDS.left, PVP_PLAY_BOUNDS.right);
        player.y = clamp(player.y + dy * speed * dt, PVP_PLAY_BOUNDS.top, PVP_PLAY_BOUNDS.bottom);
      }
    }

    for (const dragon of this.room.dragons) {
      if (!dragon.alive) continue;
      const players = Object.values(this.room.players);
      if (!players.length) continue;
      const target = players.reduce((best, p) => !best || distance(dragon, p) < distance(dragon, best) ? p : best, null);
      if (!target) continue;
      const dx = target.x - dragon.x, dy = target.y - dragon.y, len = Math.hypot(dx, dy) || 1;
      dragon.heading = Math.atan2(dy, dx);
      dragon.facing = dx < 0 ? -1 : 1;
      if (len > 155) {
        const speed = 92;
        dragon.x = clamp(dragon.x + dx / len * speed * dt, PVP_PLAY_BOUNDS.left, PVP_PLAY_BOUNDS.right);
        dragon.y = clamp(dragon.y + dy / len * speed * dt, PVP_PLAY_BOUNDS.top, PVP_PLAY_BOUNDS.bottom);
      }
    }

    if (this.room.respawnAt && now >= this.room.respawnAt) {
      this.room.dragonWave++;
      this.room.dragons = this.spawnDragons(this.room.dragonWave);
      this.room.respawnAt = 0;
      this.broadcast({ type: "dragons_respawned", wave: this.room.dragonWave, dragons: this.room.dragons });
    }

    this.room.seq++;
    if (now - this.lastBroadcastAt >= 100) {
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
    }, 50);
  }

  stopLoop() {
    if (this.loop) clearInterval(this.loop);
    this.loop = null;
    this.ctx.storage.put("room", this.room).catch(() => {});
  }

  publicPlayers() {
    return Object.values(this.room.players).map(({ input, ...player }) => player);
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
