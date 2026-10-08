/* Shared by the local History simulation and Cloudflare Worker. */
globalThis.RampageHistoryRules = (() => {
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  function obstacles(map, states = {}, objectStates = {}, ignoreId = null) {
    return [...(map.colliders || []), ...(map.doors || [])
      .filter(d => states?.[d.id]?.open ? d.openCollision : d.closedCollision !== false)
      .map(d => d.collisionRect || [d.x, d.y, d.w, d.h]), ...(map.destructibles || [])
      .filter(o => o.id !== ignoreId && o.collision && !(objectStates[o.id]?.broken && o.removeCollisionOnBreak))
      .map(o => [...(o.collisionRect || [o.x, o.y, o.w, o.h]), o.collisionShape])];
  }
  // Swept intersection: a fast projectile cannot skip a thin wall between ticks.
  function rectHitTime(ax, ay, bx, by, rect, radius = 0) {
    if (rect[4] === 'circle') {
      const rx = rect[2] / 2 + radius, ry = rect[3] / 2 + radius;
      return circleHitTime((ax-rect[0]-rect[2]/2)/rx, (ay-rect[1]-rect[3]/2)/ry,
        (bx-rect[0]-rect[2]/2)/rx, (by-rect[1]-rect[3]/2)/ry, 0, 0, 1);
    }
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
  function firstWallHit(map, states, ax, ay, bx, by, radius = 0, objectStates = {}, ignoreId = null) {
    let first = null;
    for (const rect of obstacles(map, states, objectStates, ignoreId)) {
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
  function initialObjects(map) {
    return Object.fromEntries((map.destructibles || []).map(o => [o.id,
      {hp:o.hp, shield:Number(o.shield)||0, broken:false, brokenAt:0, respawnAt:0}]));
  }
  function hitObject(map, o, runtime, attacker, damage, range, doors, states, now, hitIntervalMs = 0) {
    if (!runtime || runtime.broken || !(damage > 0)) return false;
    const rect=o.collisionRect || [o.x,o.y,o.w,o.h];
    const q={x:clamp(attacker.x,rect[0],rect[0]+rect[2]), y:clamp(attacker.y,rect[1],rect[1]+rect[3])};
    if(Math.hypot(q.x-attacker.x,q.y-attacker.y)>range ||
      firstWallHit(map,doors,attacker.x,attacker.y,q.x,q.y,0,states,o.id)!==null)return false;
    if(hitIntervalMs && o.kind==='boss') {
      const id=attacker.ownerId || attacker.id;
      runtime.lastSpecialHits ||= {};
      if(now < (runtime.lastSpecialHits[id] || 0) + hitIntervalMs)return false;
      runtime.lastSpecialHits[id]=now;
    }
    const absorbed=Math.min(Number(runtime.shield)||0,damage);
    runtime.shield=(Number(runtime.shield)||0)-absorbed;
    runtime.hp=Math.max(0,runtime.hp-(damage-absorbed));
    if(runtime.hp===0)Object.assign(runtime,{broken:true,brokenAt:now,
      respawnAt:o.respawn ? now+Math.max(1,Number(o.respawnSeconds)||10)*1000 : 0});
    return true;
  }
  function createNavigator(map) {
    const cell = 32, cols = Math.ceil(map.width / cell), rows = Math.ceil(map.height / cell);
    let gridKey = '', grid, rects = [];
    const grids = new Map();
    const point = id => ({x: (id % cols + .5) * cell, y: (Math.floor(id / cols) + .5) * cell});
    const areaContains = (p, area, r) => !area || (p.x >= area.x + r && p.x <= area.x + area.w - r &&
      p.y >= area.y + r && p.y <= area.y + area.h - r);
    function prepare(radius, states, objectStates) {
      const r = Math.ceil(radius), key = r + ':' + (map.doors || []).map(d => states?.[d.id]?.open ? 1 : 0).join('') + ':' +
        (map.destructibles || []).map(o=>objectStates?.[o.id]?.broken ? 1 : 0).join('');
      if (gridKey === key) return key;
      const cached = grids.get(key);
      if (cached) { gridKey = key; grid = cached.grid; rects = cached.rects; return key; }
      gridKey = key; rects = obstacles(map, states, objectStates); grid = new Uint8Array(cols * rows);
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
    function direction(entity, target, radius, states, now = Date.now(), objectStates = {}) {
      const key = prepare(radius, states, objectStates), area = entity.historyLeashArea;
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
    function spawnPoint(p, radius, states, area, objectStates = {}) {
      prepare(radius, states, objectStates);
      if (areaContains(p, area, radius) && clear(p, p, radius)) return p;
      const id = nearest(p, area, radius, false);
      return id < 0 ? null : point(id);
    }
    return {direction, spawnPoint};
  }
  function bossMoveArea(o, move) {
    if (move.areaMode === 'custom') return move.customArea;
    return move.areaMode === 'near' ? {x:o.x-50,y:o.y-40,w:o.w+100,h:o.h+80} : o;
  }
  function bossPush(o, move, player) {
    const dir=move.push?.direction || 'away', flow=move.areaFlow;
    let x=0,y=0;
    if(dir==='away') { x=player.x-o.x-o.w/2; y=player.y-o.y-o.h/2; }
    else {
      const d=dir==='flow' ? ({left_to_right:'right',right_to_left:'left',top_to_bottom:'down',bottom_to_top:'up'}[flow]) : dir;
      x=d==='right'?1:d==='left'?-1:0; y=d==='down'?1:d==='up'?-1:0;
    }
    const length=Math.hypot(x,y)||1,force=move.push?.enabled ? clamp(Number(move.push.force)||0,0,800) : 0;
    return {x:x/length*force,y:y/length*force};
  }
  // Both authorities use the editor sequence, hit schedule and actual GIF length.
  function updateBosses(map, states, doors, players, now, hit) {
    for(const o of (map.destructibles || []).filter(o=>o.kind==='boss')) {
      const rt=states[o.id]; if(!rt)continue;
      if(rt.broken) { rt.activeMoveId=null; continue; }
      const sequence=(o.pattern?.length ? o.pattern : ['attack','special','power'].flatMap(kind=>(o.moves[kind]||[]).map(m=>({kind,moveId:m.id,repeats:1}))))
        .flatMap(step=>Array.from({length:Math.max(1,Number(step.repeats)||1)},()=>o.moves[step.kind]?.find(m=>m.id===step.moveId))).filter(Boolean);
      if(!rt.activeMoveId && sequence.length && now>=(rt.nextAt||0) && players.some(p=>p.alive&&Math.hypot(p.x-o.x-o.w/2,p.y-o.y-o.h/2)<420)) {
        const move=sequence[(rt.moveIndex||0)%sequence.length]; rt.moveIndex=(rt.moveIndex||0)+1;
        const gif=Math.max(50,Number(move.gifDurationMs)||1000);
        const visual=move.effectDurationMode==='duration' ? Math.max(50,Number(move.effectDurationSec)*1000||1000) : gif;
        rt.actionStartedAt=now; rt.activeMoveId=move.id;
        rt.visualUntil=now+(move.preserveUntilGifEnd ? Math.max(visual,gif) : visual);
        rt.hitNextAt=now+(move.hitTiming==='delay' ? Math.max(0,Number(move.delaySec)||0)*1000 : 0);
        rt.hitEndAt=rt.hitNextAt+(move.damageMode==='constant' ? Math.max(50,Number(move.damageDurationSec)*1000||3000) : 0);
        rt.hitDone=false; rt.until=Math.max(rt.visualUntil,rt.hitEndAt); rt.nextAt=rt.until+1200;
        rt.hp=Math.min(o.hp,rt.hp+Math.max(0,Number(move.heal)||0));
      }
      const move=Object.values(o.moves).flat().find(m=>m.id===rt.activeMoveId);
      if(!move)continue;
      const area=bossMoveArea(o,move), rect=[area.x,area.y,area.w,area.h,move.areaMode==='custom'?move.areaShape:'rect'];
      if(!rt.hitDone && (move.damageMode!=='constant' || now<=rt.hitEndAt)) {
        let guard=0;
        while(now>=rt.hitNextAt && rt.hitNextAt<=rt.hitEndAt && guard++<8) {
          for(const player of players) {
            if(!player.alive || rectHitTime(player.x,player.y,player.x,player.y,rect,player.r||30)===null)continue;
            const body=o.collisionRect||[o.x,o.y,o.w,o.h];
            const x=clamp(player.x,body[0],body[0]+body[2]), y=clamp(player.y,body[1],body[1]+body[3]);
            if(firstWallHit(map,doors,x,y,player.x,player.y,0,states,o.id)!==null)continue;
            if(move.damage>0 || move.push?.enabled)hit(o,move,player,bossPush(o,move,player));
          }
          if(move.damageMode!=='constant') { rt.hitDone=true; break; }
          rt.hitNextAt+=Math.max(50,Number(move.damageIntervalSec)*1000||1000);
        }
      }
      if(now>rt.hitEndAt)rt.hitDone=true;
      if(now>=rt.until)rt.activeMoveId=null;
    }
  }
  function createCameraState() { return {events:{},queue:[],active:null,shake:null,held:null}; }
  function cameraFrame(map, rt, player, objects, now, base) {
    if(!player)return base;
    for(const event of (map.events||[]).filter(e=>e.kind==='camera')) {
      const c=event.camera, st=rt.events[event.id] ||= {fired:false,inside:false,defeated:false};
      const a=c.triggerArea,inside=c.trigger==='area' && player.alive && player.x>=a.x && player.x<=a.x+a.w && player.y>=a.y && player.y<=a.y+a.h;
      const defeated=c.trigger==='boss_defeated' && !!objects[c.bossId]?.broken;
      const trigger=inside&&!st.inside || defeated&&!st.defeated;
      st.inside=inside; st.defeated=defeated;
      if(trigger && (c.repeat==='always' || !st.fired)) {st.fired=true;rt.queue.push(event);}
    }
    const shake=(c)=> {if(c.shake?.enabled)rt.shake={until:now+Math.max(50,c.shake.durationSec*1000),intensity:clamp(c.shake.intensity,1,80)};};
    let pose=rt.held||base,scripted=!!(rt.active||rt.held);
    if(!rt.active && rt.queue.length) {
      scripted=true;
      const event=rt.queue.shift(), c=event.camera;
      const points=c.points.map(p=>({...p,zoom:p.zoom/100}));
      if(c.finish==='player')points.push({player:true,zoom:1,durationSec:c.returnSec});
      rt.active={event,points,index:0,from:{...pose},segStart:now}; rt.held=null;
      if(c.shake?.when==='start')shake(c);
    }
    if(rt.active) {
      const run=rt.active,c=run.event.camera;
      // Advance by segment deadlines, so a slow frame cannot stretch the path.
      while(run.index<run.points.length) {
        const to=run.points[run.index],target=to.player?{x:player.x,y:player.y,zoom:1}:to;
        const duration=Math.max(50,(Number(to.durationSec)||1)*1000),u=clamp((now-run.segStart)/duration,0,1),smooth=u*u*(3-2*u);
        pose={x:run.from.x+(target.x-run.from.x)*smooth,y:run.from.y+(target.y-run.from.y)*smooth,zoom:run.from.zoom+(target.zoom-run.from.zoom)*smooth};
        if(u<1)break;
        if(c.shake?.when==='each_point'&&!to.player)shake(c);
        run.from={...target};run.segStart+=duration;run.index++;
      }
      if(run.index===run.points.length) {
        rt.active=null;rt.held=c.finish==='player'?null:{...pose};
        if(c.shake?.when==='end')shake(c);
      }
    }
    return {...pose,scripted,shake:rt.shake&&now<rt.shake.until?rt.shake.intensity:0};
  }
  return {obstacles, rectHitTime, firstWallHit, circleHitTime, spawnCount, createNavigator, initialObjects, hitObject,
    bossMoveArea, updateBosses, createCameraState, cameraFrame};
})();
