// Runs the real main.js against an in-memory mock of @minecraft/server.
// Proves wiring/logic only; it is NOT evidence of Bedrock runtime behaviour.
import { test } from "node:test";
import assert from "node:assert/strict";
import * as S from "./mock/server.mjs";
import { shown } from "./mock/server-ui.mjs";

await import("../packs/CourseCraft_BP/scripts/main.js");

const p = new S.Player("Ryan");
S.players.push(p);
const ow = S.overworld;
const place = (pos, id) => { ow.blocks.set(`${pos.x},${pos.y},${pos.z}`, id); S.world.afterEvents.playerPlaceBlock.fire({ block: ow.getBlock(pos), dimension: ow, player: p }); };
const stand = (x, y, z) => { p.location = { x: x + 0.5, y, z: z + 0.5 }; };

test("first spawn gives the Maker Wand once", () => {
  S.world.afterEvents.playerSpawn.fire({ player: p, initialSpawn: true });
  S.world.afterEvents.playerSpawn.fire({ player: p, initialSpawn: true });
  assert.equal(p.items.filter((i) => i.typeId === "cc:maker_wand").length, 1);
});

test("placing a start pad registers a course", () => {
  place({ x: 0, y: 64, z: 0 }, "cc:start_pad");
  const list = JSON.parse(S.world.getDynamicProperty("cc:courses"));
  assert.equal(list.length, 1);
  assert.equal(list[0].creator, "Ryan");
});

test("full run: play, shard, spring, checkpoint, spike respawn, goal", async () => {
  place({ x: 0, y: 64, z: 3 }, "cc:shard");
  place({ x: 0, y: 64, z: 5 }, "cc:spring_pad");
  place({ x: 0, y: 64, z: 7 }, "cc:checkpoint");
  place({ x: 0, y: 64, z: 9 }, "cc:spike_block");
  place({ x: 0, y: 64, z: 11 }, "cc:goal_block");
  p.mode = S.GameMode.Creative;

  S.world.afterEvents.itemUse.fire({ itemStack: { typeId: "cc:maker_wand" }, source: p });
  S.tick(1);
  const menu = shown.at(-1);
  assert.match(menu.buttons[0], /^§aPlay: Course 1/);
  menu._resolve({ canceled: false, selection: 0 });
  await new Promise((r) => setImmediate(r));
  assert.equal(p.mode, S.GameMode.Adventure);
  assert.deepEqual([p.location.x, p.location.y, p.location.z], [0.5, 65, 0.5]);

  stand(0, 64, 3); S.tick(1);                     // walk into shard
  assert.equal(ow.getBlock({ x: 0, y: 64, z: 3 }).typeId, "minecraft:air");
  stand(0, 65, 5); S.tick(1);                     // on spring pad
  assert.equal(p.knock.at(-1)[1], 1.6);
  stand(0, 65, 7); S.tick(1);                     // on checkpoint
  assert.ok(p.titles.some(([, sub]) => sub === "§bCheckpoint!"));
  stand(0, 65, 9); S.tick(1);                     // on spike -> back to checkpoint
  assert.deepEqual([p.location.x, p.location.y, p.location.z], [0.5, 65, 7.5]);
  stand(0, 30, 0); S.tick(1);                     // y=30 is within 48 of start: no respawn
  assert.equal(p.location.y, 30);
  stand(0, 10, 0); S.tick(1);                     // fell out -> checkpoint
  assert.equal(p.location.z, 7.5);
  S.tick(40);
  stand(0, 65, 11); S.tick(1);                    // goal
  assert.ok(p.titles.some(([t, sub]) => t === "§6COURSE CLEAR!" && /✦1/.test(sub) && /NEW RECORD/.test(sub)));
  assert.equal(p.mode, S.GameMode.Creative, "previous game mode restored");
  assert.equal(ow.getBlock({ x: 0, y: 64, z: 3 }).typeId, "cc:shard", "shard restored after run");
  const c = JSON.parse(S.world.getDynamicProperty("cc:courses"))[0];
  assert.ok(c.bestTicks > 40 && c.bestBy === "Ryan");
});

test("leaving mid-run restores collected shards", async () => {
  S.world.afterEvents.itemUse.fire({ itemStack: { typeId: "cc:maker_wand" }, source: p });
  S.tick(1);
  shown.at(-1)._resolve({ canceled: false, selection: 0 });
  await new Promise((r) => setImmediate(r));
  stand(0, 64, 3); S.tick(1);
  assert.equal(ow.getBlock({ x: 0, y: 64, z: 3 }).typeId, "minecraft:air");
  S.world.afterEvents.playerLeave.fire({ playerId: p.id });
  assert.equal(ow.getBlock({ x: 0, y: 64, z: 3 }).typeId, "cc:shard");
});

test("breaking the start pad removes the course", () => {
  S.world.afterEvents.playerBreakBlock.fire({ brokenBlockPermutation: { type: { id: "cc:start_pad" } }, block: ow.getBlock({ x: 0, y: 64, z: 0 }), dimension: ow, player: p });
  assert.equal(JSON.parse(S.world.getDynamicProperty("cc:courses")).length, 0);
});

test("wand drag selection -> invisible walls, pit and escape respawn, removal", async () => {
  S.tick(5);
  place({ x: 20, y: 64, z: 20 }, "cc:start_pad");
  ow.blocks.set("27,66,20", "minecraft:stone");           // a build sitting where a wall will go
  p.held = "cc:maker_wand"; p.mode = S.GameMode.Creative; stand(20, 65, 20);

  // Creative punch: break is cancelled and becomes corner A.
  const brk = { itemStack: { typeId: "cc:maker_wand" }, player: p, block: ow.getBlock({ x: 14, y: 60, z: 14 }), cancel: false };
  S.world.beforeEvents.playerBreakBlock.fire(brk);
  assert.equal(brk.cancel, true);
  S.tick(1);
  // Drag: box follows the look target.
  p.lookAt = { x: 26, y: 72, z: 26 };
  S.tick(4);
  assert.match(p.actionbar, /^Dragging 13×13×13/);
  assert.ok(S.particles.includes("minecraft:villager_happy"));
  // Use in the air while dragging drops corner B at the look target (menu must NOT open).
  const menus = shown.length;
  S.world.afterEvents.itemUse.fire({ itemStack: { typeId: "cc:maker_wand" }, source: p });
  S.tick(1);
  assert.equal(shown.length, menus);

  // Menu -> Set course bounds.
  S.world.afterEvents.itemUse.fire({ itemStack: { typeId: "cc:maker_wand" }, source: p });
  S.tick(1);
  const menu = shown.at(-1);
  const idx = menu.buttons.findIndex((b) => b.includes("Set course bounds"));
  assert.ok(idx >= 0, menu.buttons.join(" | "));
  menu._resolve({ canceled: false, selection: idx });
  await new Promise((r) => setImmediate(r));
  S.tick(10);
  assert.equal(ow.getBlock({ x: 13, y: 65, z: 20 }).typeId, "minecraft:barrier", "west wall");
  assert.equal(ow.getBlock({ x: 20, y: 73, z: 20 }).typeId, "minecraft:barrier", "ceiling");
  assert.equal(ow.getBlock({ x: 20, y: 59, z: 20 }).typeId, "minecraft:air", "floor open");
  assert.equal(ow.getBlock({ x: 27, y: 66, z: 20 }).typeId, "minecraft:stone", "existing build kept");
  assert.equal(ow.getBlock({ x: 20, y: 66, z: 20 }).typeId, "minecraft:air", "interior untouched");

  // Play it: pit below floor and escaping past a wall both reset to the checkpoint (start).
  p.held = undefined;
  S.world.afterEvents.itemUse.fire({ itemStack: { typeId: "cc:maker_wand" }, source: p });
  S.tick(1);
  const m2 = shown.at(-1);
  m2._resolve({ canceled: false, selection: m2.buttons.findIndex((b) => b.startsWith("§aPlay:")) });
  await new Promise((r) => setImmediate(r));
  stand(20, 59, 20); S.tick(1);
  assert.deepEqual([p.location.x, p.location.y, p.location.z], [20.5, 65, 20.5], "pit -> start");
  stand(30, 65, 20); S.tick(1);
  assert.deepEqual([p.location.x, p.location.z], [20.5, 20.5], "escape -> start");
  const pearl = { itemStack: { typeId: "minecraft:ender_pearl" }, source: p, cancel: false };
  S.world.beforeEvents.itemUse.fire(pearl);
  assert.equal(pearl.cancel, true, "pearls blocked during a run");

  // Breaking the start pad clears the walls (barriers only).
  S.world.afterEvents.playerBreakBlock.fire({ brokenBlockPermutation: { type: { id: "cc:start_pad" } }, block: ow.getBlock({ x: 20, y: 64, z: 20 }), dimension: ow, player: p });
  S.tick(10);
  assert.equal(ow.getBlock({ x: 13, y: 65, z: 20 }).typeId, "minecraft:air");
  assert.equal(ow.getBlock({ x: 27, y: 66, z: 20 }).typeId, "minecraft:stone");
  assert.ok([...ow.blocks.values()].every((t) => t !== "minecraft:barrier"), "no barriers left");
});

test("use on a block sets a corner and does not open the menu", () => {
  p.held = "cc:maker_wand";
  const before = shown.length;
  const ev = { itemStack: { typeId: "cc:maker_wand" }, player: p, block: ow.getBlock({ x: 1, y: 64, z: 1 }), isFirstEvent: true, cancel: false };
  S.world.beforeEvents.playerInteractWithBlock.fire(ev);
  assert.equal(ev.cancel, true);
  S.tick(1);
  S.world.afterEvents.itemUse.fire({ itemStack: { typeId: "cc:maker_wand" }, source: p });
  S.tick(1);
  assert.equal(shown.length, before);
});
