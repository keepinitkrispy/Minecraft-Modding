# Rich & Shorty — Persistent Project State

**Branch:** `gpt/rich-and-shorty`

**Purpose:** Durable authoritative handoff for Rich & Shorty. Read this before changing the project. Do not ask Ryan to reconstruct information already recorded here. If this file conflicts with older chat context, this file wins unless a newer commit/test result proves otherwise.

## VERIFIED — Current Engineering/Test Baseline

Current code candidate:

`fd3000eb2bd7cbff273d3373e86d6fafcaf0ac29`

GitHub Actions **Rich & Shorty release gate #72** passed for that exact commit.

Current mobile test identity:

- TEST: **72**
- pack version: **0.3.72**
- BP UUID: `07bb49d8-a629-5abc-973f-c4345d8bb94b`
- RP UUID: `ce006551-520b-5cb9-b722-a22f1dcac76a`
- CI internal artifact name: `Rich_and_Shorty_v0.1.0.mcaddon`
- user-facing test artifact name: `Rich_and_Shorty_TEST72_SAFE_ARRIVAL.mcaddon`
- exact add-on SHA-256: `4bb718c2a267dc57cec9c17bcd23c59d454370be7e91477ab39dbad76d1e6218`
- exact add-on size: **113,620 bytes**
- final namespace: `keepinitkrispy_rs`

Release-gate #72 results:

- deterministic validation: **1,021 checks PASS / 0 errors**
- JavaScript syntax: PASS
- archive CRC/integrity: PASS
- exact build-specific BP/RP identity: PASS
- visual regression tests: PASS
- Mojang Minecraft Creator Tools: PASS under the documented Beta-runtime boundary
- experimental custom-dimension boundary checks: PASS
- artifact/report upload: PASS

Mojang Creator Tools 0.17.7 has one contradictory `CHKMANIF` parser behavior for `@minecraft/server: beta`: its script-module test recognizes the Beta dependency, while another manifest parser attempts numeric parsing. The CI wrapper allows only that exact known signature and still fails closed on every other error/warning. Do not broaden this allowlist.

## VERIFIED RETAIL RESULT — TEST 71

TEST 71 was imported and run on Android retail with Beta APIs enabled.

**FAIL:** entering **Glorp-9** immediately suffocated the player inside solid arrival geometry.

Root cause found in source:

- expanded central landing pad occupies `z.pos.y + 1`
- central lodestone occupies center at `z.pos.y + 2`
- TEST 71 teleport target placed player feet at `{x:z.pos.x+0.5, y:z.pos.y+1, z:z.pos.z+0.5}`
- this placed the player directly into the solid landing structure / center obstruction

This is a real retail-client failure, not a hypothetical/static concern. TEST 71 is retired as an acceptance candidate.

## TEST 72 FIX — SAFE CUSTOM-DIMENSION ARRIVAL

Part41 fixes arrival safety for **all five custom realities**, not only Glorp-9.

Before every portal teleport, including travel into already-authored worlds, the runtime now:

1. Uses an arrival point offset four blocks from the center lodestone.
2. Reasserts a **3x3 smooth-stone floor** at the landing point.
3. Clears a **3x3 x four-block-high air volume** above that floor immediately before teleport.
4. Places the player's feet at `floor + 1.01` (`y = z.pos.y + 2.01`).
5. Keeps marker lights outside the player's collision column.
6. Runs this repair on every portal trip, so a world originally authored by TEST 71 can be repaired in place rather than requiring a fresh world.

Regression gates added:

- `retail_test71_arrival_suffocation_regression`
- `safe_custom_dimension_arrival_clearance`
- `existing_world_arrival_repair`

**UNKNOWN until retail TEST 72:** whether the repaired arrival behaves correctly in the Android retail client. Static/Creator Tools validation does not prove collision behavior.

## VERIFIED — Dimension Architecture

Rich & Shorty uses **five true custom void dimensions** registered through the experimental Bedrock `DimensionRegistry` / Beta API path:

1. Glorp-9
2. Fizz Desert
3. Chrono Shelf
4. Scrap Moon
5. Citadel-ish

This is not the old fake same-dimension Overworld teleport architecture.

TEST 58 on Android retail proved that true custom-dimension transport works with Beta APIs enabled. TEST 58 also proved that the original destination content was too tiny/plain; that content has been replaced.

Required deployment path remains:

**Android local Beta world → Realm transfer bridge → PS5 download → local play**

Realm is a transfer bridge; experimental gameplay/runtime is evaluated in the downloaded local world.

## VERIFIED — Dimension Visual Overhaul

Current reality construction:

- each reality initially authors a **3x3 district of 40x40 sectors** before arrival
- initial authored footprint is approximately **120x120 blocks**
- neighboring 40x40 sectors stream in as the player explores
- sector work is serialized through ticking-area loading to limit mobile pressure
- sectors use persistent physical markers so they are not rebuilt each script session

Visual grammar:

- **Glorp-9:** warped fungal archipelago, giant luminous stalks, slime/water features, floating amethyst shards, dark-prismarine/blackstone floating-island mass.
- **Fizz Desert:** broken red desert islands, basalt/terracotta towers, magma fissures, lava points, suspended blackstone furnace-rock.
- **Chrono Shelf:** quartz/calcite terraces, blue-ice seams, hovering amethyst clock structures, end-rod timing markers.
- **Scrap Moon:** dark industrial salvage field, iron/copper cranes, rails, gantries, machine carcasses and redstone-lit wreckage.
- **Citadel-ish:** central story Citadel plus streamed outer bureaucratic metropolis with towers, bridges, civic structures and beacons.

## VERIFIED — Dimension Gameplay Overhaul

Non-central resource sectors contain persistent **Reality Contracts**.

For every non-central sector in Glorp/Fizz/Chrono/Scrap:

1. Themed encounter treatment frames the sector lodestone.
2. Entering activates a deterministic four-threat contract.
3. Each reality has a distinct enemy roster.
4. Contract mobs carry exact sector tags so unrelated mobs do not count.
5. Kill progress persists physically under the sector floor using a five-state hidden block marker.
6. Reload/unload recovery respawns only missing contract threats based on persisted progress.
7. Clearing all four threats permanently stabilizes that sector.
8. Completion exposes a physical cache using that reality's custom resource blocks.
9. `keepinitkrispy_rs:reality_sectors_cleared` records total stabilized sectors.
10. Central landing sectors remain contract-safe.

Encounter flavor:

- **Glorp:** slimes / cave spiders / spiders / zombies
- **Fizz:** husks / blazes / magma cubes / zombies
- **Chrono:** strays / skeletons / endermen
- **Scrap:** zombies / pillagers / skeletons / spiders

Current dimension regression gates include:

- `expanded_reality_120x120_initial`
- `streamed_reality_expansion`
- `distinct_reality_skylines`
- `sector_ticking_area_serialization`
- `beta_dimension_expanded_authoring_gate`
- `reality_sector_contracts`
- `persistent_sector_kill_state`
- `reload_recovery_threat_respawn`
- `sector_resource_cache_reward`
- `safe_central_landing_sectors`
- `reality_sector_creator_namespace`
- TEST 72 safe-arrival gates listed above

## Current Cast / Visual Profile

20 featured characters:

1. Rich
2. Shorty
3. Evil Shorty
4. Bess
5. Gerry
6. Sundae
7. Bird Dude
8. Scronchy
9. Mr. Needs-It
10. Professor Poop
11. Captain Drizzle
12. Nightmare Larry
13. Sprocket Face
14. Consensus
15. Cucumber Rich
16. Killer Krombo
17. Shorty Jr.
18. Validator Prime
19. Franky Lincolnstein
20. Council Rich

Current shipping character profile is `retail_clean_forms_v3`, designed to avoid the layered/wafer appearance rejected in TEST 58. Do not resurrect fine-layered geometry merely to increase cube count.

Current cube counts:

- Rich 76
- Shorty 54
- Evil Shorty 60
- Bess 56
- Gerry 55
- Sundae 55
- Bird Dude 51
- Scronchy 57
- Mr. Needs-It 55
- Professor Poop 53
- Captain Drizzle 68
- Nightmare Larry 63
- Sprocket Face 65
- Consensus 56
- Cucumber Rich 31
- Killer Krombo 60
- Shorty Jr. 55
- Validator Prime 74
- Franky Lincolnstein 58
- Council Rich 78

Reality Fabricator remains a custom **48-cube** machine, intentionally below the Creator Tools >50-cube custom-block warning threshold.

## Starter Base

Current profile:

`furnished_two_level_house_full_workshop_clear_driveway_lab_v2`

Includes furnished two-level house, garage/workshop, clear flush driveway, finished underground reality lab, Fabricator placement and persistent Home-coordinate recovery. Existing deployed TEST-58-era bases have an in-place visual migration path.

## Core Gameplay Loop

1. Player receives Busted Portal Remote and Reality Fabricator.
2. Home/garage coordinates persist.
3. Player travels through true custom dimensions for Glorp Crystal, Fizzium, Chronodust and Scrap Fragment.
4. Fabricator rolls a recipe using multiple reality resources.
5. Recipe remains locked until fulfilled.
6. UI shows have/need counts and suggested route.
7. Fabrication consumes resources and awards one of eight world-manipulation tools.
8. Immediately previous tool is excluded from the next result.
9. Side liabilities award Citadel Tokens/special tools and leave persistent world consequences.
10. Three Citadel Tokens permanently unlock Citadel-ish.
11. Council Rich interaction stages Evil Shorty; Evil Shorty does not auto-ambush on arrival.
12. Evil Shorty is a multi-phase boss.
13. Epilogue persists while Fabricator/reality loop remains replayable.
14. Streamed Reality Contracts provide exploration/combat goals outside the main story.

## Side Liabilities

- Sundae — 8 Glorp Crystals + 8 Fizzium → Citadel Token; Glorp gains a luminous coolant garden.
- Bird Dude — 10 Chronodust → Citadel Token; Chrono gains a ceremonial time-roost.
- Mr. Needs-It — 12 Scrap Fragments → Citadel Token; Scrap gains a receiver tower.
- Gerry — 4 of every reality resource → Chaos Bonker; Scrap gains the requested multiversal shelf consequence.

## World Tool Pool

- Gravity Spanner
- Phase Pick
- Freeze Ray
- Time-Skip Watch
- Scaffold Printer
- Matter-Swap Glove
- Pocket Black Hole
- Chaos Bonker

Portal Remote includes Liability Ledger and Reality Tool Manual. Native Bedrock use cooldowns are retained.

## Hard Quality Rules

- Read current branch head and this state file before editing.
- Never regress to fake Overworld dimensions.
- Never regress realities to tiny flat pads or scenery-only resource rooms.
- Never replace retail-clean cast with generic box people or TEST-58 layered/wafer geometry.
- Never claim schema/static validation proves Beta runtime behavior.
- Never collapse UNKNOWN retail behavior into PASS.
- Keep Mojang validation fail-closed except the exact documented Creator Tools Beta parser contradiction.
- Preserve build-specific TEST identities so Android imports can coexist.
- Preserve Android/mobile-first workflow; do not silently require a desktop.
- Use `keepinitkrispy_rs` namespace for new content/state.
- When a retail test fails, record the exact observed behavior, repair from evidence, add a regression gate, and rerun applicable automated gates.
- User-facing downloadable candidates must be named with their TEST number. Do not hand Ryan another ambiguously named `v0.1.0` test artifact.

## Current Verification Boundary

**VERIFIED for TEST 72:**

- deterministic generation and validation: 1,021 checks / 0 errors
- JS syntax
- archive integrity
- exact test-pack identity
- current hard static/regression signatures
- Creator Tools validation under the narrowly documented Beta-manifest parser exception
- manifest Beta dependency
- startup custom-dimension registration code
- awaited destination ticking-area loading
- cross-dimension teleport target
- absence of old fake Overworld route
- safe-arrival helper and geometry-clearing path present on every portal trip
- exact shipping visual approval renders generated by CI

**Previously VERIFIED on Android retail:**

- TEST 58: true custom-dimension transport works with Beta APIs enabled
- TEST 71: Glorp-9 can be reached, but arrival collision caused immediate suffocation

**UNKNOWN until TEST 72 retail/player test:**

- safe Glorp-9 arrival in actual retail collision runtime
- safe arrival in Fizz, Chrono, Scrap and Citadel
- expanded 120x120 initial reality construction under actual Android retail runtime
- streamed sector generation while exploring
- current reality visual quality in retail renderer
- Reality Contract enemy spawning/tagging/death accounting
- persisted sector progress after unload/reload
- sector cache exposure after four kills
- performance of expanded streamed realities on phone
- current cast animation/rendering behavior in retail
- full controller/touch Portal Remote flow
- Fabricator custom-component interaction in real play
- side-liability turn-ins/world consequences in real play
- Council hearing/Evil Shorty staging in real play
- Realm transfer and PS5 local-world behavior for TEST 72

A vanilla Bedrock Dedicated Server CI world is not decisive runtime proof for this artifact because it does not run the required Beta APIs experiment. The decisive runtime gate is retail Minecraft with Beta APIs enabled.

## Next Work

1. Import exact **TEST 72** candidate on Android with Beta APIs enabled.
2. First test: enter Glorp-9. PASS requires standing freely on the offset landing pad with no suffocation, solid floor below and clear movement.
3. If Glorp arrival passes, check Fizz, Chrono, Scrap and Citadel arrival safety.
4. Then judge reality scale/visual identity and complete one non-central Reality Contract.
5. Verify Reality Contract progress survives leaving/re-entering and that the resource cache appears after completion.
6. Record every observed PASS/FAIL here and repair only from evidence.
7. After Android local runtime is clean, use Realm transfer path and test downloaded world on PS5.
