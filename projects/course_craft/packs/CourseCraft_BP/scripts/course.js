// @ts-check
// Pure Course Craft logic. No @minecraft/server imports so it can be unit-tested in Node.

export const NS = "cc";

export const BLOCKS = Object.freeze({
  START: "cc:start_pad",
  GOAL: "cc:goal_block",
  CHECKPOINT: "cc:checkpoint",
  SPRING: "cc:spring_pad",
  DASH: "cc:dash_pad",
  SPIKE: "cc:spike_block",
  SHARD: "cc:shard",
  BRICK: "cc:bright_brick",
  GRASS: "cc:toon_grass",
  CLOUD: "cc:cloud_block",
});

export const WAND = "cc:maker_wand";

/** Items handed out by the "Course Kit" menu entry, in hotbar order. */
export const KIT = [
  BLOCKS.START, BLOCKS.GOAL, BLOCKS.CHECKPOINT, BLOCKS.SHARD, BLOCKS.SPRING,
  BLOCKS.DASH, BLOCKS.SPIKE, BLOCKS.BRICK, BLOCKS.GRASS, BLOCKS.CLOUD,
];

export const FALL_LIMIT = 48; // blocks below the start pad before a run respawns
export const PAD_COOLDOWN_TICKS = 8;

/**
 * @typedef {{x:number,y:number,z:number}} Vec3
 * @typedef {{id:string,name:string,dim:string,pos:Vec3,creator:string,bestTicks:number|null,bestBy:string|null,shards:number}} Course
 */

/** @param {number} n */
const fl = (n) => Math.floor(n);

/** @param {Vec3} p */
export function blockPos(p) {
  return { x: fl(p.x), y: fl(p.y), z: fl(p.z) };
}

/** @param {string} dim @param {Vec3} p */
export function courseId(dim, p) {
  const b = blockPos(p);
  return `${dim}|${b.x},${b.y},${b.z}`;
}

/** @param {Vec3} p */
export function posKey(p) {
  const b = blockPos(p);
  return `${b.x},${b.y},${b.z}`;
}

/** Ticks (20/s) -> "m:ss.cc" @param {number} ticks */
export function formatTime(ticks) {
  const t = Math.max(0, Math.round(ticks));
  const totalCs = t * 5; // 1 tick = 5 centiseconds
  const m = Math.floor(totalCs / 6000);
  const s = Math.floor((totalCs % 6000) / 100);
  const cs = totalCs % 100;
  return `${m}:${String(s).padStart(2, "0")}.${String(cs).padStart(2, "0")}`;
}

/** @param {unknown} raw @returns {Course[]} */
export function parseRegistry(raw) {
  if (typeof raw !== "string" || raw.length === 0) return [];
  try {
    const data = JSON.parse(raw);
    if (!Array.isArray(data)) return [];
    return data.filter(
      (c) => c && typeof c.id === "string" && typeof c.dim === "string" && c.pos &&
        Number.isFinite(c.pos.x) && Number.isFinite(c.pos.y) && Number.isFinite(c.pos.z)
    ).map((c) => ({
      id: c.id,
      name: typeof c.name === "string" && c.name ? c.name.slice(0, 32) : "Course",
      dim: c.dim,
      pos: blockPos(c.pos),
      creator: typeof c.creator === "string" ? c.creator : "?",
      bestTicks: Number.isFinite(c.bestTicks) ? c.bestTicks : null,
      bestBy: typeof c.bestBy === "string" ? c.bestBy : null,
      shards: Number.isFinite(c.shards) ? c.shards : 0,
    }));
  } catch {
    return [];
  }
}

/** @param {Course[]} list */
export function serializeRegistry(list) {
  return JSON.stringify(list);
}

/** @param {Course[]} list @param {string} dim @param {Vec3} pos @param {string} creator @returns {{list:Course[],course:Course,created:boolean}} */
export function addCourse(list, dim, pos, creator) {
  const id = courseId(dim, pos);
  const existing = list.find((c) => c.id === id);
  if (existing) return { list, course: existing, created: false };
  const course = {
    id, name: `Course ${list.length + 1}`, dim, pos: blockPos(pos), creator,
    bestTicks: null, bestBy: null, shards: 0,
  };
  return { list: [...list, course], course, created: true };
}

/** @param {Course[]} list @param {string} id */
export function removeCourse(list, id) {
  return list.filter((c) => c.id !== id);
}

/** @param {Course[]} list @param {string} id @param {string} name */
export function renameCourse(list, id, name) {
  const clean = name.replace(/§./g, "").trim().slice(0, 32);
  if (!clean) return list;
  return list.map((c) => (c.id === id ? { ...c, name: clean } : c));
}

/** Records a finish. Returns updated list and whether it was a new record. @param {Course[]} list @param {string} id @param {number} ticks @param {string} player */
export function recordFinish(list, id, ticks, player) {
  let isRecord = false;
  const next = list.map((c) => {
    if (c.id !== id) return c;
    if (c.bestTicks === null || ticks < c.bestTicks) {
      isRecord = true;
      return { ...c, bestTicks: ticks, bestBy: player };
    }
    return c;
  });
  return { list: next, isRecord };
}

/** Nearest course in the same dimension, within maxDist blocks. @param {Course[]} list @param {string} dim @param {Vec3} p @param {number} [maxDist] */
export function nearestCourse(list, dim, p, maxDist = Infinity) {
  let best = null;
  let bestD = maxDist * maxDist;
  for (const c of list) {
    if (c.dim !== dim) continue;
    const d = (c.pos.x - p.x) ** 2 + (c.pos.y - p.y) ** 2 + (c.pos.z - p.z) ** 2;
    if (d <= bestD) { bestD = d; best = c; }
  }
  return best;
}

/**
 * Decide what a playing player's surroundings trigger this tick.
 * @param {{below:string|undefined,feet:string|undefined,head:string|undefined}} t
 * @returns {Array<"goal"|"spike"|"spring"|"dash"|"checkpoint"|"shard_feet"|"shard_head">}
 */
export function triggers(t) {
  /** @type {Array<"goal"|"spike"|"spring"|"dash"|"checkpoint"|"shard_feet"|"shard_head">} */
  const out = [];
  if (t.below === BLOCKS.GOAL || t.feet === BLOCKS.GOAL) { out.push("goal"); return out; }
  if (t.below === BLOCKS.SPIKE || t.feet === BLOCKS.SPIKE) { out.push("spike"); return out; }
  if (t.feet === BLOCKS.SHARD) out.push("shard_feet");
  if (t.head === BLOCKS.SHARD) out.push("shard_head");
  if (t.below === BLOCKS.CHECKPOINT || t.feet === BLOCKS.CHECKPOINT) out.push("checkpoint");
  if (t.below === BLOCKS.SPRING) out.push("spring");
  else if (t.below === BLOCKS.DASH) out.push("dash");
  return out;
}

/** Horizontal dash impulse from a view direction. @param {Vec3} view @param {number} strength */
export function dashVector(view, strength) {
  const len = Math.hypot(view.x, view.z);
  if (len < 1e-6) return { x: 0, z: 0 };
  return { x: (view.x / len) * strength, z: (view.z / len) * strength };
}

/** @param {number} y @param {Vec3} start */
export function fellOut(y, start) {
  return y < start.y - FALL_LIMIT;
}

/** Pending shard restores (survives script reload). @param {unknown} raw @returns {Array<{dim:string,pos:Vec3}>} */
export function parsePending(raw) {
  if (typeof raw !== "string" || !raw) return [];
  try {
    const d = JSON.parse(raw);
    return Array.isArray(d) ? d.filter((e) => e && typeof e.dim === "string" && e.pos).map((e) => ({ dim: e.dim, pos: blockPos(e.pos) })) : [];
  } catch { return []; }
}
