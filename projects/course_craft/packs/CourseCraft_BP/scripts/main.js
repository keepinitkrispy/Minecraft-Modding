// @ts-check
// Course Craft: build platformer courses anywhere in an open world, then play them.
import { world, system, ItemStack, GameMode, Player, BlockVolume } from "@minecraft/server";
import { ActionFormData, ModalFormData } from "@minecraft/server-ui";
import {
  BLOCKS, WAND, KIT, PAD_COOLDOWN_TICKS,
  parseRegistry, serializeRegistry, addCourse, removeCourse, renameCourse, recordFinish,
  nearestCourse, triggers, dashVector, fellOut, formatTime, parsePending, posKey, courseId,
  BARRIER, normBox, boxSize, boundsProblem, shellSlabs, outOfBounds, edgePoints, setBounds, courseInBox,
} from "./course.js";

const REG_PROP = "cc:courses";
const PENDING_PROP = "cc:pending_shards";
const GOT_WAND_PROP = "cc:got_wand";

/**
 * @typedef {import("./course.js").Course} Course
 * @typedef {import("./course.js").Vec3} Vec3
 * @typedef {import("./course.js").Box} Box
 * @typedef {{courseId:string,start:Vec3,dim:string,startTick:number,checkpoint:Vec3,shards:number,
 *   collected:Array<{dim:string,pos:Vec3}>,padCooldownUntil:number,prevMode:GameMode,lastCheckpointKey:string,bounds:Box|null}} Run
 * @typedef {{dim:string,a:Vec3,b:Vec3,dragging:boolean}} Selection
 */

/** @type {Map<string, Run>} */
const runs = new Map();
/** @type {Map<string, Selection>} */
const selections = new Map();
/** Tick of each player's last wand use on a block, so the air-use menu doesn't also open. @type {Map<string, number>} */
const lastBlockUse = new Map();
/** Pending barrier fills/clears, processed a few per tick. @type {Array<{dim:string,from:Vec3,to:Vec3,place:boolean,owner:string}>} */
const fillQueue = [];
const FILLS_PER_TICK = 4;
const DRAG_REACH = 48;
const BLOCKED_IN_RUN = new Set(["minecraft:ender_pearl", "minecraft:chorus_fruit"]);

// ---------- persistence ----------
/** @returns {Course[]} */
function loadCourses() { return parseRegistry(world.getDynamicProperty(REG_PROP)); }
/** @param {Course[]} list */
function saveCourses(list) { world.setDynamicProperty(REG_PROP, serializeRegistry(list)); }

function savePending() {
  const all = [];
  for (const r of runs.values()) all.push(...r.collected);
  world.setDynamicProperty(PENDING_PROP, JSON.stringify(all));
}

/** @param {Array<{dim:string,pos:Vec3}>} list */
function restoreShards(list) {
  for (const e of list) {
    try {
      const block = world.getDimension(e.dim).getBlock(e.pos);
      if (block && block.typeId === "minecraft:air") block.setType(BLOCKS.SHARD);
    } catch { /* chunk unloaded: stays in pending list on next save */ }
  }
}

// ---------- helpers ----------
/** @param {Vec3} p */
const above = (p) => ({ x: p.x + 0.5, y: p.y + 1, z: p.z + 0.5 });

/** @param {Player} p @param {string} msg */
const tell = (p, msg) => p.sendMessage(`§e[Course Craft]§r ${msg}`);

/** @param {Player} player @param {Vec3} pos */
function blockId(player, pos) {
  try { return player.dimension.getBlock(pos)?.typeId; } catch { return undefined; }
}

/** @param {Player} player */
function giveWand(player) {
  const inv = player.getComponent("minecraft:inventory");
  inv?.container?.addItem(new ItemStack(WAND, 1));
}

/** @param {Player} player */
function giveKit(player) {
  const inv = player.getComponent("minecraft:inventory");
  if (!inv?.container) return;
  for (const id of KIT) inv.container.addItem(new ItemStack(id, 64));
  tell(player, "Course Kit added to your inventory.");
}

// ---------- runs ----------
/** @param {Player} player @param {Course} course */
function startRun(player, course) {
  endRun(player, false);
  const prev = player.getGameMode();
  /** @type {Run} */
  const run = {
    courseId: course.id, start: course.pos, dim: course.dim, startTick: system.currentTick,
    checkpoint: course.pos, shards: 0, collected: [], padCooldownUntil: 0,
    prevMode: prev === GameMode.Adventure ? GameMode.Creative : prev, lastCheckpointKey: "",
    bounds: course.bounds,
  };
  runs.set(player.id, run);
  player.setGameMode(GameMode.Adventure);
  player.teleport(above(course.pos), { dimension: world.getDimension(course.dim) });
  player.clearVelocity();
  player.onScreenDisplay.setTitle("§aGO!", { fadeInDuration: 0, stayDuration: 20, fadeOutDuration: 10, subtitle: course.name });
  player.playSound("random.levelup");
}

/** @param {Player} player @param {boolean} restoreMode */
function endRun(player, restoreMode = true) {
  const run = runs.get(player.id);
  if (!run) return;
  runs.delete(player.id);
  restoreShards(run.collected);
  savePending();
  if (restoreMode) player.setGameMode(run.prevMode);
  player.onScreenDisplay.setActionBar("");
}

/** @param {Player} player @param {Run} run */
function respawnAtCheckpoint(player, run) {
  player.clearVelocity();
  player.teleport(above(run.checkpoint), { dimension: world.getDimension(run.dim) });
  player.playSound("mob.endermen.portal");
}

/** @param {Player} player @param {Run} run */
function finishRun(player, run) {
  const ticks = system.currentTick - run.startTick;
  const res = recordFinish(loadCourses(), run.courseId, ticks, player.name);
  saveCourses(res.list);
  const course = res.list.find((c) => c.id === run.courseId);
  player.onScreenDisplay.setTitle("§6COURSE CLEAR!", {
    fadeInDuration: 0, stayDuration: 60, fadeOutDuration: 20,
    subtitle: `${formatTime(ticks)}  ✦${run.shards}${res.isRecord ? "  §bNEW RECORD!" : ""}`,
  });
  player.playSound("random.totem");
  tell(player, `${course?.name ?? "Course"} cleared in ${formatTime(ticks)} with ${run.shards} shard(s).`);
  endRun(player, true);
}

// ---------- tick loop ----------
system.runInterval(() => {
  const now = system.currentTick;
  for (const player of world.getAllPlayers()) {
    const run = runs.get(player.id);
    if (!run) continue;
    if (player.dimension.id !== run.dim) { endRun(player, true); continue; }
    const loc = player.location;
    const feet = { x: Math.floor(loc.x), y: Math.floor(loc.y), z: Math.floor(loc.z) };
    // Standing on top of a full block puts feet exactly on its top face; sample just below.
    const below = { x: feet.x, y: Math.floor(loc.y - 0.05), z: feet.z };
    const belowId = below.y === feet.y ? blockId(player, { ...feet, y: feet.y - 1 }) : blockId(player, below);
    const t = triggers({ below: belowId, feet: blockId(player, feet), head: blockId(player, { ...feet, y: feet.y + 1 }) });

    for (const trig of t) {
      if (trig === "goal") { finishRun(player, run); break; }
      if (trig === "spike") { respawnAtCheckpoint(player, run); break; }
      if (trig === "shard_feet" || trig === "shard_head") {
        const pos = trig === "shard_feet" ? feet : { ...feet, y: feet.y + 1 };
        const block = player.dimension.getBlock(pos);
        if (block?.typeId === BLOCKS.SHARD) {
          block.setType("minecraft:air");
          run.collected.push({ dim: run.dim, pos });
          run.shards++;
          savePending();
          player.playSound("random.orb");
        }
      }
      if (trig === "checkpoint") {
        const cp = belowId === BLOCKS.CHECKPOINT ? { x: feet.x, y: feet.y - 1, z: feet.z } : feet;
        const key = posKey(cp);
        if (key !== run.lastCheckpointKey) {
          run.lastCheckpointKey = key;
          run.checkpoint = cp;
          player.onScreenDisplay.setTitle(" ", { fadeInDuration: 0, stayDuration: 20, fadeOutDuration: 5, subtitle: "§bCheckpoint!" });
          player.playSound("note.pling");
        }
      }
      if ((trig === "spring" || trig === "dash") && now >= run.padCooldownUntil) {
        run.padCooldownUntil = now + PAD_COOLDOWN_TICKS;
        if (trig === "spring") {
          player.applyKnockback({ x: 0, z: 0 }, 1.6);
          player.playSound("mob.slime.big");
        } else {
          player.applyKnockback(dashVector(player.getViewDirection(), 2.4), 0.35);
          player.playSound("mob.ghast.fireball");
        }
      }
    }
    if (!runs.has(player.id)) continue;

    if (run.bounds ? outOfBounds(run.bounds, loc) : fellOut(loc.y, run.start)) respawnAtCheckpoint(player, run);
    if (now % 2 === 0) {
      player.onScreenDisplay.setActionBar(`⏱ ${formatTime(now - run.startTick)}   ✦ ${run.shards}`);
    }
  }
}, 1);

// ---------- course registration ----------
world.afterEvents.playerPlaceBlock.subscribe((ev) => {
  if (ev.block.typeId !== BLOCKS.START) return;
  const res = addCourse(loadCourses(), ev.dimension.id, ev.block.location, ev.player.name);
  if (res.created) {
    saveCourses(res.list);
    tell(ev.player, `Start pad placed: §a${res.course.name}§r. Use the Maker Wand to rename or play it.`);
  }
});

world.afterEvents.playerBreakBlock.subscribe((ev) => {
  if (ev.brokenBlockPermutation.type.id !== BLOCKS.START) return;
  const id = courseId(ev.dimension.id, ev.block.location);
  const list = loadCourses();
  const gone = list.find((c) => c.id === id);
  if (gone) {
    if (gone.bounds) queueShell(gone.dim, gone.bounds, false, ev.player.name);
    saveCourses(removeCourse(list, id));
    tell(ev.player, "Course removed (its start pad was broken).");
  }
});

// ---------- spawn / leave ----------
world.afterEvents.playerSpawn.subscribe((ev) => {
  const player = ev.player;
  if (ev.initialSpawn && !player.getDynamicProperty(GOT_WAND_PROP)) {
    giveWand(player);
    player.setDynamicProperty(GOT_WAND_PROP, true);
    tell(player, "Welcome! Use the §dMaker Wand§r to build and play courses.");
  }
  const run = runs.get(player.id);
  if (run && !ev.initialSpawn) respawnAtCheckpoint(player, run);
});

world.afterEvents.playerLeave.subscribe((ev) => {
  const run = runs.get(ev.playerId);
  if (!run) return;
  runs.delete(ev.playerId);
  restoreShards(run.collected);
  savePending();
});

// Restore shards collected during runs interrupted by a reload/crash.
system.run(() => {
  const pending = parsePending(world.getDynamicProperty(PENDING_PROP));
  restoreShards(pending);
  world.setDynamicProperty(PENDING_PROP, "[]");
});

// ---------- wand menu ----------
world.afterEvents.itemUse.subscribe((ev) => {
  if (ev.itemStack.typeId !== WAND) return;
  const player = ev.source;
  const last = lastBlockUse.get(player.id);
  if (last !== undefined && system.currentTick - last <= 2) return; // that use was a corner click
  const sel = selections.get(player.id);
  if (sel?.dragging) { system.run(() => dropCorner(player, dragTarget(player))); return; }
  system.run(() => openMenu(player));
});

// ---------- wand selection (punch = corner A + start drag, use = drop corner B) ----------
/** @param {Player} player */
function holdingWand(player) {
  const inv = player.getComponent("minecraft:inventory");
  return inv?.container?.getItem(player.selectedSlotIndex)?.typeId === WAND;
}

/** @param {Player} player @returns {Vec3} */
function dragTarget(player) {
  const hit = player.getBlockFromViewDirection({ maxDistance: DRAG_REACH, includePassableBlocks: false });
  if (hit) return hit.block.location;
  const v = player.getViewDirection(), h = player.getHeadLocation();
  return { x: Math.floor(h.x + v.x * 8), y: Math.floor(h.y + v.y * 8), z: Math.floor(h.z + v.z * 8) };
}

/** @param {Player} player @param {Vec3} pos */
function startDrag(player, pos) {
  if (runs.has(player.id)) return;
  selections.set(player.id, { dim: player.dimension.id, a: pos, b: pos, dragging: true });
  player.playSound("random.click");
  tell(player, "Corner A set. Look to stretch the box, then use the wand to drop corner B.");
}

/** @param {Player} player @param {Vec3} pos */
function dropCorner(player, pos) {
  const sel = selections.get(player.id);
  if (!sel || sel.dim !== player.dimension.id) { tell(player, "Punch a block with the wand to set corner A first."); return; }
  sel.b = pos; sel.dragging = false;
  const s = boxSize(normBox(sel.a, sel.b));
  player.playSound("random.click");
  tell(player, `Corner B set: §a${s.x}×${s.y}×${s.z}§r. Open the wand menu → §aSet course bounds§r.`);
}

// Punch (survival hit) with the wand: corner A.
world.afterEvents.entityHitBlock.subscribe((ev) => {
  const player = ev.damagingEntity;
  if (!(player instanceof Player) || !holdingWand(player)) return;
  startDrag(player, ev.hitBlock.location);
});

// Creative punch breaks instantly: cancel it and treat it as corner A instead.
world.beforeEvents.playerBreakBlock.subscribe((ev) => {
  if (ev.itemStack?.typeId !== WAND) return;
  ev.cancel = true;
  const player = ev.player, pos = ev.block.location;
  system.run(() => {
    const sel = selections.get(player.id);
    if (!(sel?.dragging && posKey(sel.a) === posKey(pos))) startDrag(player, pos);
  });
});

// Use on a block with the wand: corner B (or corner A if nothing is selected yet). Never places/opens.
world.beforeEvents.playerInteractWithBlock.subscribe((ev) => {
  if (ev.itemStack?.typeId !== WAND) return;
  ev.cancel = true;
  if (!ev.isFirstEvent) return;
  const player = ev.player, pos = ev.block.location;
  lastBlockUse.set(player.id, system.currentTick);
  system.run(() => {
    lastBlockUse.set(player.id, system.currentTick);
    if (selections.has(player.id)) dropCorner(player, pos); else startDrag(player, pos);
  });
});

// No teleport items during a run.
world.beforeEvents.itemUse.subscribe((ev) => {
  if (BLOCKED_IN_RUN.has(ev.itemStack.typeId) && runs.has(ev.source.id)) ev.cancel = true;
});

// Live drag + outlines, 5x per second.
system.runInterval(() => {
  for (const player of world.getAllPlayers()) {
    if (runs.has(player.id) || !holdingWand(player)) continue;
    const sel = selections.get(player.id);
    if (sel && sel.dim === player.dimension.id) {
      if (sel.dragging) sel.b = dragTarget(player);
      const box = normBox(sel.a, sel.b), s = boxSize(box);
      drawBox(player, box, "minecraft:villager_happy");
      player.onScreenDisplay.setActionBar(`${sel.dragging ? "Dragging" : "Selected"} ${s.x}×${s.y}×${s.z}`);
    }
    const near = nearestCourse(loadCourses(), player.dimension.id, player.location, 96);
    if (near?.bounds) drawBox(player, near.bounds, "minecraft:endrod");
  }
}, 4);

/** @param {Player} player @param {Box} box @param {string} particle */
function drawBox(player, box, particle) {
  for (const p of edgePoints(box)) {
    try { player.dimension.spawnParticle(particle, p); } catch { /* unloaded */ }
  }
}

// ---------- invisible walls ----------
/** @param {string} dim @param {Box} box @param {boolean} place @param {string} owner */
function queueShell(dim, box, place, owner) {
  for (const s of shellSlabs(box)) fillQueue.push({ dim, from: s.from, to: s.to, place, owner });
}

system.runInterval(() => {
  for (let i = 0; i < FILLS_PER_TICK && fillQueue.length; i++) {
    const job = /** @type {{dim:string,from:Vec3,to:Vec3,place:boolean,owner:string}} */ (fillQueue.shift());
    const dim = world.getDimension(job.dim);
    try {
      // Walls only replace air (never your builds); clearing only removes barriers.
      dim.fillBlocks(new BlockVolume(job.from, job.to), job.place ? BARRIER : "minecraft:air",
        { blockFilter: { includeTypes: [job.place ? "minecraft:air" : BARRIER] } });
    } catch {
      const p = world.getAllPlayers().find((x) => x.name === job.owner);
      if (p) tell(p, "§cPart of the boundary is in unloaded chunks.§r Stand nearer the course and set bounds again.");
    }
  }
}, 1);

/** @param {Player} player */
function applySelectionAsBounds(player) {
  const sel = selections.get(player.id);
  if (!sel) return;
  const box = normBox(sel.a, sel.b);
  const list = loadCourses();
  const course = courseInBox(list, sel.dim, box);
  if (!course) { tell(player, "§cNo Start Pad inside the selection.§r"); return; }
  const problem = boundsProblem(box, course.pos);
  if (problem) { tell(player, `§c${problem}`); return; }
  if (course.bounds) queueShell(course.dim, course.bounds, false, player.name);
  queueShell(course.dim, box, true, player.name);
  saveCourses(setBounds(list, course.id, box));
  selections.delete(player.id);
  const s = boxSize(box);
  tell(player, `Bounds set for §a${course.name}§r: ${s.x}×${s.y}×${s.z}. Invisible walls and ceiling; the bottom is the pit.`);
}

/** @param {Player} player @param {Course} course */
function removeBounds(player, course) {
  if (!course.bounds) return;
  queueShell(course.dim, course.bounds, false, player.name);
  saveCourses(setBounds(loadCourses(), course.id, null));
  tell(player, `Bounds removed from §a${course.name}§r.`);
}

/** @param {Player} player */
function openMenu(player) {
  const list = loadCourses();
  const near = nearestCourse(list, player.dimension.id, player.location, 64);
  const inRun = runs.has(player.id);
  /** @type {Array<[string, () => void]>} */
  const entries = [];
  if (inRun) {
    entries.push(["§cQuit run", () => { endRun(player, true); tell(player, "Run ended."); }]);
    entries.push(["Restart run", () => {
      const c = loadCourses().find((x) => x.id === runs.get(player.id)?.courseId);
      if (c) startRun(player, c);
    }]);
  } else {
    if (near) entries.push([`§aPlay: ${near.name}`, () => startRun(player, near)]);
    entries.push(["Browse courses", () => browse(player)]);
    if (near) entries.push([`Rename: ${near.name}`, () => rename(player, near)]);
    entries.push([player.getGameMode() === GameMode.Creative ? "Builder mode: ON" : "Builder mode (creative)", () => {
      player.setGameMode(GameMode.Creative);
      tell(player, "Builder mode on.");
    }]);
    const sel = selections.get(player.id);
    if (sel && !sel.dragging) entries.push(["§aSet course bounds§r (from selection)", () => applySelectionAsBounds(player)]);
    if (sel) entries.push(["Clear selection", () => { selections.delete(player.id); player.onScreenDisplay.setActionBar(""); }]);
    if (near?.bounds) entries.push([`Remove bounds: ${near.name}`, () => removeBounds(player, near)]);
    entries.push(["Get Course Kit", () => giveKit(player)]);
  }
  const form = new ActionFormData().title("Course Craft").body(
    (near ? `Nearest: §a${near.name}§r  best ${near.bestTicks === null ? "—" : formatTime(near.bestTicks) + " by " + near.bestBy}` : "Place a §aStart Pad§r to create a course.") +
      "\n§7Bounds: punch a block with the wand, look to drag, use to drop the far corner."
  );
  for (const [label] of entries) form.button(label);
  form.show(player).then((r) => {
    if (r.canceled || r.selection === undefined) return;
    entries[r.selection]?.[1]();
  });
}

/** @param {Player} player */
function browse(player) {
  const list = loadCourses();
  if (list.length === 0) { tell(player, "No courses yet. Place a Start Pad."); return; }
  const form = new ActionFormData().title("Courses").body("Pick a course to play.");
  for (const c of list) {
    form.button(`${c.name}\n§8${c.creator} · ${c.bestTicks === null ? "no record" : formatTime(c.bestTicks)}`);
  }
  form.show(player).then((r) => {
    if (r.canceled || r.selection === undefined) return;
    const c = list[r.selection];
    if (c) startRun(player, c);
  });
}

/** @param {Player} player @param {Course} course */
function rename(player, course) {
  new ModalFormData().title("Rename course").textField("Name", "My Course", { defaultValue: course.name })
    .show(player).then((r) => {
      if (r.canceled || !r.formValues) return;
      const name = String(r.formValues[0] ?? "");
      saveCourses(renameCourse(loadCourses(), course.id, name));
      tell(player, `Renamed to §a${name}`);
    });
}
