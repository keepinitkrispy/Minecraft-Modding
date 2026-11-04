import { test } from "node:test";
import assert from "node:assert/strict";
import * as C from "../packs/CourseCraft_BP/scripts/course.js";

const box = C.normBox({ x: 10, y: 70, z: -5 }, { x: 0, y: 60, z: 5 });

test("normBox orders corners and boxSize is inclusive", () => {
  assert.deepEqual(box, { min: { x: 0, y: 60, z: -5 }, max: { x: 10, y: 70, z: 5 } });
  assert.deepEqual(C.boxSize(box), { x: 11, y: 11, z: 11 });
});

test("boundsProblem: start inside with headroom, size limits", () => {
  assert.equal(C.boundsProblem(box, { x: 5, y: 61, z: 0 }), null);
  assert.match(C.boundsProblem(box, { x: 50, y: 61, z: 0 }), /Start Pad/);
  assert.match(C.boundsProblem(box, { x: 5, y: 69, z: 0 }), /headroom/);
  assert.match(C.boundsProblem(C.normBox({ x: 0, y: 0, z: 0 }, { x: 500, y: 10, z: 10 }), { x: 1, y: 1, z: 1 }), /Too big/);
  assert.match(C.boundsProblem(C.normBox({ x: 0, y: 0, z: 0 }, { x: 1, y: 10, z: 10 }), { x: 1, y: 1, z: 1 }), /Too small/);
});

test("outOfBounds: pit below floor, escape past walls/ceiling", () => {
  assert.equal(C.outOfBounds(box, { x: 5.5, y: 60, z: 0.5 }), null);
  assert.equal(C.outOfBounds(box, { x: 5.5, y: 59.9, z: 0.5 }), "pit");
  assert.equal(C.outOfBounds(box, { x: 11.2, y: 65, z: 0.5 }), "escape");
  assert.equal(C.outOfBounds(box, { x: 5, y: 72, z: 0 }), "escape");
  assert.equal(C.outOfBounds(box, { x: 5, y: 71, z: 0 }), null, "standing in the ceiling layer is not an escape");
});

/** Expand slabs to a set of block keys. */
function cells(slabs) {
  const set = new Set();
  for (const { from, to } of slabs)
    for (let x = from.x; x <= to.x; x++) for (let y = from.y; y <= to.y; y++) for (let z = from.z; z <= to.z; z++) {
      const k = `${x},${y},${z}`; assert.ok(!set.has(k), `overlap at ${k}`); set.add(k);
    }
  return set;
}

test("shellSlabs: exact shell (4 walls + ceiling, open floor), no overlap, slab size cap", () => {
  const s = cells(C.shellSlabs(box));
  // Expected count: walls on 13x13 ring (perimeter 48) over y 60..71 (12 layers) + ceiling interior 11x11.
  assert.equal(s.size, 48 * 12 + 11 * 11);
  assert.ok(s.has("-1,60,0") && s.has("11,71,5") && s.has("5,71,0"));
  assert.ok(!s.has("5,59,0") && !s.has("5,60,0"), "floor open, interior empty");
  const big = C.normBox({ x: 0, y: 0, z: 0 }, { x: 159, y: 127, z: 159 });
  const slabs = C.shellSlabs(big);
  for (const { from, to } of slabs)
    assert.ok((to.x - from.x + 1) * (to.y - from.y + 1) * (to.z - from.z + 1) <= C.SLAB_MAX);
  // Ring around 160x160 interior = 162*2 + 160*2 = 644 columns, y 0..128 = 129 layers; ceiling 160x160.
  assert.equal(cells(slabs).size, 644 * 129 + 160 * 160);
});

test("edgePoints respects particle cap", () => {
  const big = C.normBox({ x: 0, y: 0, z: 0 }, { x: 159, y: 127, z: 159 });
  assert.ok(C.edgePoints(big).length <= 260);
  assert.ok(C.edgePoints(C.normBox({ x: 0, y: 0, z: 0 }, { x: 2, y: 2, z: 2 })).length >= 12);
});

test("registry keeps bounds through serialize/parse", () => {
  let { list, course } = C.addCourse([], "o", { x: 5, y: 61, z: 0 }, "a");
  list = C.setBounds(list, course.id, box);
  assert.deepEqual(C.parseRegistry(C.serializeRegistry(list))[0].bounds, box);
  assert.equal(C.courseInBox(list, "o", box)?.id, course.id);
  assert.equal(C.courseInBox(list, "n", box), null);
});
