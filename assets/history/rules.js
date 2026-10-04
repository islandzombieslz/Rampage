/* Shared by the local History simulation and Cloudflare Worker. */
globalThis.RampageHistoryRules = (() => {
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  function obstacles(map, states = {}) {
    return [...(map.colliders || []), ...(map.doors || [])
      .filter(d => states[d.id]?.open ? d.openCollision : d.closedCollision !== false)
      .map(d => [d.x, d.y, d.w, d.h])];
  }
  // Swept intersection: a fast projectile cannot skip a thin wall between ticks.
  function rectHitTime(ax, ay, bx, by, rect, radius = 0) {
    let enter = 0, exit = 1;
    for (const [start, delta, low, high] of [
      [ax, bx - ax, rect[0] - radius, rect[0] + rect[2] + radius],
      [ay, by - ay, rect[1] - radius, rect[1] + rect[3] + radius]
    ]) {
      if (Math.abs(delta) < 1e-9) { if (start < low || start > high) return null; }
      else {
        let a = (low - start) / delta, b = (high - start) / delta;
        if (a > b) [a, b] = [b, a];
        enter = Math.max(enter, a); exit = Math.min(exit, b);
        if (enter > exit) return null;
      }
    }
    return enter;
  }
  function firstWallHit(map, states, ax, ay, bx, by, radius = 0) {
    let first = null;
    for (const rect of obstacles(map, states)) {
      const t = rectHitTime(ax, ay, bx, by, rect, radius);
      if (t !== null && (first === null || t < first)) first = t;
    }
    return first;
  }
  function circleHitTime(ax, ay, bx, by, cx, cy, radius) {
    const dx = bx - ax, dy = by - ay, ox = ax - cx, oy = ay - cy;
    const a = dx * dx + dy * dy, c = ox * ox + oy * oy - radius * radius;
    if (c <= 0) return 0;
    if (a < 1e-9) return null;
    const b = 2 * (ox * dx + oy * dy), disc = b * b - 4 * a * c;
    if (disc < 0) return null;
    const t = (-b - Math.sqrt(disc)) / (2 * a);
    return t >= 0 && t <= 1 ? t : null;
  }
  function spawnCount(event, type, enemies) {
    const desired = Math.max(0, Math.floor(Number(event.troops?.[type]) || 0));
    if (event.limitAlive === false) return desired;
    const alive = enemies.reduce((n, e) => n + (e.alive &&
      e.historySpawnEventId === event.id && e.type === type ? 1 : 0), 0);
    return Math.max(0, desired - alive);
  }
  function createNavigator(map) {
    const cell = 32, cols = Math.ceil(map.width / cell), rows = Math.ceil(map.height / cell);
    let gridKey = '', grid, rects = [];
    const grids = new Map();
    const point = id => ({x: (id % cols + .5) * cell, y: (Math.floor(id / cols) + .5) * cell});
    const areaContains = (p, area, r) => !area || (p.x >= area.x + r && p.x <= area.x + area.w - r &&
      p.y >= area.y + r && p.y <= area.y + area.h - r);
    function prepare(radius, states) {
      const r = Math.ceil(radius), key = r + ':' + (map.doors || []).map(d => states?.[d.id]?.open ? 1 : 0).join('');
      if (gridKey === key) return key;
      const cached = grids.get(key);
      if (cached) { gridKey = key; grid = cached.grid; rects = cached.rects; return key; }
      gridKey = key; rects = obstacles(map, states); grid = new Uint8Array(cols * rows);
      for (let id = 0; id < grid.length; id++) {
        const p = point(id);
        grid[id] = p.x < r || p.y < r || p.x > map.width - r || p.y > map.height - r ||
          rects.some(rect => rectHitTime(p.x, p.y, p.x, p.y, rect, r) !== null) ? 1 : 0;
      }
      grids.set(key, {grid, rects});
      if (grids.size > 16) grids.delete(grids.keys().next().value);
      return key;
    }
    function clear(a, b, r) {
      return !rects.some(rect => rectHitTime(a.x, a.y, b.x, b.y, rect, r) !== null);
    }
    function nearest(p, area, r, requireConnection) {
      const gx = clamp(Math.floor(p.x / cell), 0, cols - 1), gy = clamp(Math.floor(p.y / cell), 0, rows - 1);
      for (let ring = 0; ring <= 8; ring++) {
        let best = -1, distance = Infinity;
        for (let y = Math.max(0, gy - ring); y <= Math.min(rows - 1, gy + ring); y++) {
          for (let x = Math.max(0, gx - ring); x <= Math.min(cols - 1, gx + ring); x++) {
            if (Math.max(Math.abs(x - gx), Math.abs(y - gy)) !== ring) continue;
            const id = y * cols + x, q = point(id);
            if (grid[id] || !areaContains(q, area, r) || (requireConnection && !clear(p, q, r))) continue;
            const d = Math.hypot(q.x - p.x, q.y - p.y);
            if (d < distance) { best = id; distance = d; }
          }
        }
        if (best >= 0) return best;
      }
      return -1;
    }
    function path(start, goal, area, r) {
      const first = nearest(start, area, r, true), last = nearest(goal, area, r, true);
      if (first < 0 || last < 0) return [];
      const scores = new Float64Array(grid.length); scores.fill(Infinity);
      const parent = new Int32Array(grid.length); parent.fill(-1);
      const closed = new Uint8Array(grid.length), heap = [];
      const heuristic = id => Math.hypot(id % cols - last % cols, Math.floor(id / cols) - Math.floor(last / cols));
      function push(id, cost) {
        const item = {id, cost}; let i = heap.length; heap.push(item);
        while (i > 0) { const p = (i - 1) >> 1; if (heap[p].cost <= cost) break; heap[i] = heap[p]; i = p; }
        heap[i] = item;
      }
      function pop() {
        const root = heap[0], end = heap.pop();
        if (heap.length) {
          let i = 0;
          while (i * 2 + 1 < heap.length) {
            let c = i * 2 + 1;
            if (c + 1 < heap.length && heap[c + 1].cost < heap[c].cost) c++;
            if (end.cost <= heap[c].cost) break;
            heap[i] = heap[c]; i = c;
          }
          heap[i] = end;
        }
        return root.id;
      }
      scores[first] = 0; push(first, heuristic(first));
      let found = false;
      while (heap.length) {
        const id = pop(); if (closed[id]) continue; closed[id] = 1;
        if (id === last) { found = true; break; }
        const x = id % cols, y = Math.floor(id / cols), a = point(id);
        for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
          if ((!dx && !dy) || x + dx < 0 || x + dx >= cols || y + dy < 0 || y + dy >= rows) continue;
          const next = (y + dy) * cols + x + dx, b = point(next);
          if (grid[next] || closed[next] || !areaContains(b, area, r) || !clear(a, b, r)) continue;
          const score = scores[id] + (dx && dy ? Math.SQRT2 : 1);
          if (score >= scores[next]) continue;
          scores[next] = score; parent[next] = id; push(next, score + heuristic(next));
        }
      }
      if (!found) return [];
      const result = [goal];
      for (let id = last; id >= 0; id = parent[id]) { result.push(point(id)); if (id === first) break; }
      return result.reverse();
    }
    function direction(entity, target, radius, states, now = Date.now()) {
      const key = prepare(radius, states), area = entity.historyLeashArea;
      const goal = {x: clamp(target.x, area ? area.x + radius : radius, area ? area.x + area.w - radius : map.width - radius),
        y: clamp(target.y, area ? area.y + radius : radius, area ? area.y + area.h - radius : map.height - radius)};
      const norm = p => {const dx = p.x - entity.x, dy = p.y - entity.y, d = Math.hypot(dx, dy); return d > 1 ? {x: dx / d, y: dy / d} : {x: 0, y: 0};};
      if (clear(entity, goal, radius)) { entity.historyRoute = null; return norm(goal); }
      let route = entity.historyRoute;
      if (!route || route.key !== key || now >= route.until || Math.hypot(route.goal.x - goal.x, route.goal.y - goal.y) > cell * 2) {
        route = entity.historyRoute = {key, goal, until: now + 1000, points: path(entity, goal, area, radius)};
      }
      while (route.points.length && Math.hypot(route.points[0].x - entity.x, route.points[0].y - entity.y) < 8) route.points.shift();
      if (!route.points.length) return {x: 0, y: 0};
      let next = null;
      for (const p of route.points) { if (!clear(entity, p, radius)) break; next = p; }
      if (!next) { route.until = 0; return {x: 0, y: 0}; }
      return norm(next);
    }
    function spawnPoint(p, radius, states, area) {
      prepare(radius, states);
      if (areaContains(p, area, radius) && clear(p, p, radius)) return p;
      const id = nearest(p, area, radius, false);
      return id < 0 ? null : point(id);
    }
    return {direction, spawnPoint};
  }
  return {obstacles, rectHitTime, firstWallHit, circleHitTime, spawnCount, createNavigator};
})();
