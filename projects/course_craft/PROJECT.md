# Course Craft — Project State

**Concept:** An open-world course maker for Minecraft Bedrock. Place a Start Pad anywhere to create a course, build it with the platformer kit, then play it with a timer, checkpoints, shards and saved records. The project uses its own name and original art; players supply their own skins through the texture slots (see `TEXTURES.md`).

**Target:** Bedrock ≥ 1.21.90, stable Script API `@minecraft/server` 2.0.0 + `@minecraft/server-ui` 2.0.0. No experimental toggles. Mobile → Realm → PS5.

## Layout
- `packs/CourseCraft_BP`, `packs/CourseCraft_RP`: the add-on
- `packs/CourseCraft_BP/scripts/course.js`: pure logic (unit-tested)
- `packs/CourseCraft_BP/scripts/main.js`: Bedrock wiring (events, tick loop, menus)
- `tools/spec.py`: single source of truth for blocks, items, slots and UUIDs
- `tools/generate.py`, `import_textures.py`, `texture_kit.py`, `validate.py`, `build.py`
- `tests/`: Node logic and simulated-world tests, Python import/validator tests

## Commands
```
npm install                       # once; dev typings + TypeScript only
python3 tools/build.py            # generate → validate → typecheck → tests → bump → CourseCraft.mcaddon
npm test                          # logic + simulated world
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Validation ladder status (v1.0.x)
| Level | Status | Evidence |
|---|---|---|
| 1 Structural/package | PASS | `tools/validate.py`: manifests, UUIDs, deps, JSON, texture refs, lang |
| 2 Schema/static | PARTIAL | Script typechecked (`tsc --strict`) against official 2.0.0 typings. Block/item JSON **not** checked against an official schema |
| 3 Import | UNKNOWN | Not runtime-tested |
| 4 Placement | UNKNOWN | |
| 5 Behavior | UNKNOWN in Bedrock | Logic and wiring pass in a mock world (`tests/world_sim.test.js`). That is not Bedrock evidence |
| 6 Visual | UNKNOWN | Placeholder art only |
| 7 Regression | n/a | First version |

## Runtime unknowns to test first
1. The pack imports, and the blocks/item appear in the creative menu with names.
2. `itemUse` fires for the Maker Wand (a custom item with no use component) on touch and controller. **If it doesn't, the menu can't open; this is the highest risk.**
3. The first-join wand grant works on a Realm.
4. The Shard is walk-through, glows and shows transparency correctly.
5. Spring height (`applyKnockback` vertical 1.6) and dash strength (2.4) feel right. These are tuning guesses.
6. Pad detection while standing on block tops (samples y − 0.05).
7. The Script API is allowed on the target Realm with no experiments enabled (INFERRED from stable module use).

## Not built yet (candidate next features)
Moving platforms, enemies, power-ups, course sharing via structure export, a lives system and a course-clear check before publishing.
