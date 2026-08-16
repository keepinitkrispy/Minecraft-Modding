# Rich & Shorty — Persistent Project State

**Branch:** `gpt/rich-and-shorty`

**Purpose:** Authoritative durable handoff. Read this before changing Rich & Shorty. Do not ask Ryan to reconstruct facts already recorded here. Newer retail observations beat older assumptions. Do not weaken regression gates just to make a build pass.

## CURRENT CANDIDATE — TEST 78

Code candidate:

`ee5edc9fc3ed2076a7247af1d2a3906e098a18be`

GitHub Actions **Rich & Shorty release gate #78** passed for this exact commit.

Mobile identity:

- TEST: **78**
- pack version: **0.3.78**
- BP UUID: `32fb4598-7ac1-5eb5-a7d3-b27aa25eef95`
- RP UUID: `8c6ea352-2df7-5d90-b6dc-ec1e5cfe0f0b`
- user-facing artifact: `Rich_and_Shorty_TEST78_SCI_FI_ENEMIES.mcaddon`
- SHA-256: `db7bc5c16f1112cbf5f86cb5ee509c017374d8b4e59552642e9ebdd9a4b065c1`
- size: **148,691 bytes**
- namespace: `keepinitkrispy_rs`

Release gate #78:

- deterministic validation: **1,376 checks PASS / 0 errors**
- JavaScript syntax: PASS
- archive integrity: PASS
- build-specific BP/RP identity: PASS
- visual regression suite: PASS
- Mojang Creator Tools: PASS under the existing narrowly documented Beta-manifest parser exception
- experimental custom-dimension boundary checks: PASS
- artifact/report upload: PASS

Vanilla BDS runtime stages remain intentionally skipped for this Beta custom-dimension candidate; retail Minecraft with Beta APIs is the decisive runtime test.

## RETAIL HISTORY — VERIFIED

### TEST 58

- True custom-dimension transport works on Android retail with Beta APIs enabled.
- Old destination content failed quality acceptance because it was tiny/plain.
- Old fine-layered character geometry failed visual acceptance and was replaced.

### TEST 71

- Glorp-9 was reachable.
- **FAIL:** immediate suffocation inside arrival geometry.
- Cause: player feet teleported into the authored central pad/lodestone collision volume.

### TEST 72

- **PASS:** repaired transport/arrival works in retail.
- **FAIL VISUAL/DESIGN ACCEPTANCE:** every dimension's sky presentation looked bad and the realities were poorly designed, very empty, and boring.
- TEST 72 is retired as a visual candidate.

### TEST 76

- Current atmosphere/density/landmark overhaul candidate before the enemy pass.
- It introduced reality-specific fog/volumetric atmosphere, dense vertical authoring, major landmarks and deliberate traversal composition.
- Retail result is not yet recorded here.

### TEST 77

- **REJECTED BEFORE RETAIL.** First custom-enemy build failed the release gate.
- Gate correctly caught legacy `minecraft:pushable` on all ten new enemies after Bedrock's 1.26.10 component split.
- Gate also caught Late-Fee Drone at 11 cubes, below the 12-cube enemy visual floor.
- No TEST 77 client artifact should be used.

### TEST 78

- Fixes TEST 77 without weakening gates.
- All ten enemies use `format_version: 1.26.10` plus `minecraft:pushable_by_block` and `minecraft:pushable_by_entity`.
- Late-Fee Drone gained a rear chronometer housing and now clears the visual floor.
- Full applicable release pipeline passes.

## TRUE CUSTOM DIMENSIONS

Five true custom void dimensions registered through experimental Bedrock `DimensionRegistry` / Beta APIs:

1. Glorp-9
2. Fizz Desert
3. Chrono Shelf
4. Scrap Moon
5. Citadel-ish

This is not the removed fake same-dimension Overworld teleport system.

Deployment path remains:

**Android local Beta world → Realm transfer bridge → PS5 download → local play**

Realm is a courier/bridge; experimental runtime is judged in the local/downloaded world.

## SKY / ATMOSPHERE BOUNDARY

The custom dimension registration path creates void-generator dimensions but does not expose Mojang's internal End-style skybox/cubemap control directly.

Current presentation strategy:

- per-player reality-specific fog stack
- `player.fogSettings` with `minecraft:player.fog` compatibility fallback
- five custom fog definitions
- distance fog + volumetric media where supported
- fog removed outside custom realities
- large celestial/horizon structures
- dense upper/lower silhouettes so realities do not read as flat islands in empty void

Do not claim a nonexistent direct custom-dimension skybox hook.

## REALITY ART / WORLD DESIGN — TEST 76+

Base generation:

- 40x40 authored sectors
- 3x3 initial district (~120x120) before first arrival
- adjacent sectors stream as players explore
- serialized ticking-area generation for mobile pressure
- persistent physical sector markers prevent unnecessary rebuilding

Every reality now has layered density: terraces, arches, hanging under-island masses, satellite platforms/islands, pylons/spires, upper/lower silhouettes and large horizon/celestial structures.

Every streamed sector gets one major deterministic landmark from a four-variant kit.

Glorp:
- Root Cathedral
- Bubble Bog
- Shard Grove
- Giant Cap

Fizz:
- Furnace Temple
- Impact Crater
- Basalt Ribs
- Suspended Smeltery

Chrono:
- Broken Hourglass
- Archive Stack
- Clock Face Plaza
- Frozen Switchyard

Scrap:
- Crashed Ship
- Crusher Pit
- Antenna Farm
- Factory Spine

Citadel outer districts:
- Records Tower
- Bureaucratic Plaza
- Customs Hall
- Transit Tower

Composition is deliberate rather than pure scatter:

- 5-wide north/south route from sector center to bridges
- 5-wide east/west route
- four blocks of headroom carved over routes
- route rhythm lighting
- clear central orientation node
- landmarks authored first, then routes carve readable entrances/sightlines

## SAFE ARRIVAL — LOCKED

TEST 71 regression fix is mandatory in all five realities.

Before every portal teleport:

1. Offset arrival from center lodestone.
2. Reassert 3x3 solid landing floor.
3. Clear 3x3 x four-block-high headroom pocket.
4. Place player feet just above floor.
5. Repair the pocket on every trip, including old authored worlds.

Never remove or weaken:

- `retail_test71_arrival_suffocation_regression`
- `safe_custom_dimension_arrival_clearance`
- `existing_world_arrival_repair`

## TEST 78 — TEN CUSTOM SCI-FI ENEMIES

Two original custom enemies per reality. These are custom entity stacks with unique geometry, textures, animations, behavior definitions, spawn eggs, combat effects and quips—not renamed vanilla mobs.

### Glorp-9

**Glorp Compliance Slug**
- broad alien slug/scanner silhouette
- applies brief Slowness
- quip: “Your moisture permit expired three molts ago.”

**Spore Taxman**
- mushroom-mech silhouette with oversized cap and machinery
- applies brief Poison
- quip: “This infection is deductible. Probably.”

### Fizz Desert

**Warranty Wasp**
- mechanical wasp silhouette with wings/stinger
- applies brief Weakness
- quip: “Damage detected. Warranty voided by damage.”

**Heat Repo Bot**
- heavy industrial repossession robot
- applies brief Hunger
- quip: “Repossessing approximately all of your warmth.”

### Chrono Shelf

**Late-Fee Drone**
- walking clock/drone body with clock hands and chronometer housing
- applies stronger short Slowness
- quip: “You are 3.7 seconds overdue.”

**Secondhand Assassin**
- tall clockwork killer with oversized time-hand silhouette
- applies brief Darkness
- quip: “Killing time. Professionally.”

### Scrap Moon

**Forklift Crab**
- wide six-legged forklift/crab chassis with twin forks
- physically knocks players back with an impulse
- quip: “Beep beep. OSHA has left this dimension.”

**Unlicensed Recycler**
- trash-compactor/recycler robot
- applies stronger brief Weakness
- quip: “You have been classified as mixed waste.”

### Citadel-ish

**Form 27-B**
- mobile bureaucratic printer/stamp robot
- applies brief Mining Fatigue
- quip: “Combat request denied. Combat will continue.”

**Queue Enforcement Unit**
- tall enforcement/stanchion robot
- applies brief Slowness
- quip: “Please remain violently in line.”

### Enemy integration

Glorp/Fizz/Chrono/Scrap Reality Contracts now use their two custom native enemies directly. The old vanilla contract rosters are removed.

Citadel has no resource-sector contract loop, so its two enemies spawn as capped patrols:

- max three Citadel patrol enemies around an occupied sector
- co-op players in the same sector do not independently multiply the patrol cap
- central portal arrival remains safe
- patrols do not activate in the central sector until a player moves at least 12 blocks away from the arrival center

Enemy quips are throttled per attacker so co-op combat does not become chat spam.

Current enemy regression gates include:

- `ten_custom_reality_enemies`
- `two_enemies_per_dimension`
- `no_vanilla_reality_contract_roster`
- `custom_enemy_geometry_stack`
- `custom_enemy_special_hits`
- `citadel_capped_enemy_patrols`
- `citadel_arrival_stays_safe`
- `reality_enemy_pushable_split_1_26_10`
- `late_fee_drone_minimum_visual_mass`

## REALITY CONTRACTS

Non-central Glorp/Fizz/Chrono/Scrap sectors retain persistent four-threat Reality Contracts:

- exact sector-tagged threats
- unrelated mobs do not count
- physical hidden-block kill-state persistence
- missing threats recover after unload/reload
- four kills permanently stabilize sector
- completion exposes reality-resource cache
- `keepinitkrispy_rs:reality_sectors_cleared` tracks stabilized sectors
- central landing sectors remain contract-safe

TEST 78 replaces the vanilla contract enemies with each reality's two custom enemies; persistence/reward mechanics remain unchanged.

## CORE ADD-ON CONTENT

20 featured parody characters remain:

Rich, Shorty, Evil Shorty, Bess, Gerry, Sundae, Bird Dude, Scronchy, Mr. Needs-It, Professor Poop, Captain Drizzle, Nightmare Larry, Sprocket Face, Consensus, Cucumber Rich, Killer Krombo, Shorty Jr., Validator Prime, Franky Lincolnstein, Council Rich.

Character geometry profile remains `retail_clean_forms_v3`; never restore TEST-58 wafer/layer-cake geometry.

Reality Fabricator remains a custom 48-cube machine.

Starter property remains `furnished_two_level_house_full_workshop_clear_driveway_lab_v2` with furnished two-level house, full garage/workshop, clear driveway, finished underground lab, Fabricator and persistent Home recovery.

Core loop remains:

1. Busted Portal Remote + Reality Fabricator.
2. Persistent Home coordinates.
3. Travel through four resource realities.
4. Fabricator rolls multi-resource recipe.
5. Recipe stays locked until fulfilled.
6. UI shows have/need + suggested route.
7. Fabrication awards one of eight world-manipulation tools.
8. Immediate previous tool cannot repeat.
9. Side liabilities award tokens/tools and persistent world consequences.
10. Three Citadel Tokens unlock Citadel-ish permanently.
11. Council Rich stages Evil Shorty encounter.
12. Evil Shorty is multi-phase.
13. Epilogue persists; Fabricator loop remains replayable.
14. Streamed Reality Contracts provide repeatable combat/exploration.

World tools:

- Gravity Spanner
- Phase Pick
- Freeze Ray
- Time-Skip Watch
- Scaffold Printer
- Matter-Swap Glove
- Pocket Black Hole
- Chaos Bonker

## HARD QUALITY RULES

- Read current branch head and this file before editing.
- Never regress to fake Overworld dimensions.
- Never regress realities to tiny pads, sparse scenery, flat resource rooms or procedural clutter without composition.
- Never replace retail-clean cast with generic box people or TEST-58 wafer geometry.
- Never claim schema/static validation proves Beta runtime behavior.
- Never collapse UNKNOWN retail behavior into PASS.
- Keep Mojang validation fail-closed except the exact documented Beta parser contradiction.
- Preserve build-specific TEST identities so Android imports coexist.
- Preserve Android/mobile-first deployment.
- Use `keepinitkrispy_rs` for new content/state.
- Every retail failure must be recorded exactly, repaired from evidence and protected by a regression gate.
- User-facing downloadable candidates must include their TEST number in the filename.
- Failed CI test numbers are retired; do not hand them to Ryan as client candidates.

## CURRENT VERIFICATION BOUNDARY

**VERIFIED by retail observation:**

- true custom-dimension transport works
- TEST 71 arrival geometry was unsafe
- TEST 72 arrival/transport repair works
- TEST 72 visual/world design was unacceptable: bad sky presentation, poorly designed, empty, boring

**VERIFIED automatically for TEST 78:**

- 1,376 checks / 0 errors
- JS syntax
- archive integrity
- exact TEST 78 BP/RP identity
- current hard regression suite
- Creator Tools under documented Beta boundary
- custom dimension registration/transport signatures
- safe-arrival regression logic
- TEST 76 atmosphere/density/landmark/traversal systems retained
- ten complete custom enemy asset stacks
- two enemies per dimension
- resource contracts contain no old vanilla enemy roster
- ten custom hostile behavior definitions
- custom enemy special-hit dispatch and quips
- Citadel capped patrol logic + safe-arrival exclusion
- 1.26.10 pushability split on all ten enemies
- Late-Fee Drone >=12-cube visual floor

**UNKNOWN until retail/co-op TEST 78:**

- whether all ten custom enemies render/animate correctly in retail
- whether all ten pathfind and attack correctly in actual custom dimensions
- whether special hit effects feel fun rather than annoying in two-player combat
- whether Reality Contract counting works correctly when either co-op player gets a kill
- whether Citadel patrol density feels right with two players
- whether TEST 76 atmosphere/landmark overhaul is visually acceptable in retail
- Android performance with denser realities plus custom enemies
- full two-player portal/Fabricator/story progression behavior
- Realm transfer → PS5 local co-op behavior

## NEXT PLAYTHROUGH

Use **TEST 78** for Ryan + Ollie's first co-op playthrough.

Do not turn the playthrough into formal QA. Play normally and record concrete observations when something breaks, looks bad, feels boring, feels unfair, or is especially fun.

High-value observations:

- both players can portal safely
- both players see the intended reality atmosphere
- custom enemies visibly match their names/silhouettes
- custom enemies do not overwhelm arrival areas
- Reality Contracts work when either player lands kills
- resource caches appear after contract completion
- Citadel patrols stay capped and do not spawn directly on arrival
- no player gets stranded by the other's travel/progression state
- Fabricator and story progression remain usable in co-op
