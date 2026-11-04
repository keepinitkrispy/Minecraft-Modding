import { test } from "node:test";
import assert from "node:assert/strict";
import * as C from "../packs/CourseCraft_BP/scripts/course.js";

test("formatTime", () => {
  assert.equal(C.formatTime(0), "0:00.00");
  assert.equal(C.formatTime(20), "0:01.00");
  assert.equal(C.formatTime(1201), "1:00.05");
});

test("registry add/rename/remove/round-trip", () => {
  let { list, created, course } = C.addCourse([], "minecraft:overworld", { x: 1.7, y: 64, z: -3.2 }, "Ryan");
  assert.ok(created);
  assert.deepEqual(course.pos, { x: 1, y: 64, z: -4 });
  assert.equal(C.addCourse(list, "minecraft:overworld", { x: 1, y: 64, z: -4 }, "x").created, false);
  list = C.renameCourse(list, course.id, "  §aSky Run  ");
  assert.equal(list[0].name, "Sky Run");
  const back = C.parseRegistry(C.serializeRegistry(list));
  assert.deepEqual(back, list);
  assert.equal(C.removeCourse(back, course.id).length, 0);
});

test("parseRegistry tolerates garbage", () => {
  assert.deepEqual(C.parseRegistry(undefined), []);
  assert.deepEqual(C.parseRegistry("{not json"), []);
  assert.deepEqual(C.parseRegistry('[{"id":1}]'), []);
});

test("recordFinish only records improvements", () => {
  let { list, course } = C.addCourse([], "d", { x: 0, y: 0, z: 0 }, "a");
  let r = C.recordFinish(list, course.id, 400, "a"); assert.ok(r.isRecord);
  r = C.recordFinish(r.list, course.id, 500, "b"); assert.equal(r.isRecord, false);
  r = C.recordFinish(r.list, course.id, 300, "b"); assert.ok(r.isRecord);
  assert.equal(r.list[0].bestBy, "b");
});

test("nearestCourse respects dimension and range", () => {
  let list = C.addCourse([], "o", { x: 0, y: 0, z: 0 }, "a").list;
  list = C.addCourse(list, "o", { x: 100, y: 0, z: 0 }, "a").list;
  list = C.addCourse(list, "n", { x: 1, y: 0, z: 0 }, "a").list;
  assert.equal(C.nearestCourse(list, "o", { x: 90, y: 0, z: 0 }).pos.x, 100);
  assert.equal(C.nearestCourse(list, "o", { x: 50, y: 0, z: 0 }, 10), null);
});

test("triggers priority: goal and spike short-circuit", () => {
  const B = C.BLOCKS;
  assert.deepEqual(C.triggers({ below: B.GOAL, feet: B.SHARD, head: undefined }), ["goal"]);
  assert.deepEqual(C.triggers({ below: B.SPIKE, feet: B.SHARD, head: undefined }), ["spike"]);
  assert.deepEqual(C.triggers({ below: B.SPRING, feet: B.SHARD, head: B.SHARD }), ["shard_feet", "shard_head", "spring"]);
  assert.deepEqual(C.triggers({ below: B.CHECKPOINT, feet: "minecraft:air", head: "minecraft:air" }), ["checkpoint"]);
});

test("dashVector normalises horizontal direction", () => {
  const v = C.dashVector({ x: 3, y: 5, z: 4 }, 2);
  assert.ok(Math.abs(Math.hypot(v.x, v.z) - 2) < 1e-9);
  assert.deepEqual(C.dashVector({ x: 0, y: 1, z: 0 }, 2), { x: 0, z: 0 });
});

test("KIT ids are all known blocks", () => {
  const known = new Set(Object.values(C.BLOCKS));
  for (const id of C.KIT) assert.ok(known.has(id), id);
});
