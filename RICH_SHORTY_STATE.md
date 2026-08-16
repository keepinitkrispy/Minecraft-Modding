# Rich & Shorty — Persistent Project State

**Branch:** `gpt/rich-and-shorty`

**Purpose:** Authoritative durable handoff. Read this before editing Rich & Shorty. Newer retail observations beat older assumptions. Do not ask Ryan to reconstruct facts already recorded here. Do not weaken regression gates merely to make a build pass.

## CURRENT CANDIDATE — TEST 79

Code candidate:

`4dbe01d6f16d0f66e9b9e52a37debcc7c334d464`

GitHub Actions **Rich & Shorty release gate #79** passed for this exact commit.

Mobile identity:

- TEST: **79**
- pack version: **0.3.79**
- user-facing artifact: `Rich_and_Shorty_TEST79_LIVING_REALITIES.mcaddon`
- SHA-256: `2c74e267ded06ddca064d66ff2dd5c476313650f0c559fd878543eaf0686f60a`
- size: **161,405 bytes**
- namespace: `keepinitkrispy_rs`

Release gate #79:

- deterministic validation: **1,505 checks PASS / 0 errors**
- JavaScript syntax: PASS
- archive CRC/integrity: PASS
- build-specific TEST identity: PASS
- visual regression suite: PASS
- Mojang Creator Tools: PASS under the existing narrow Beta-manifest parser exception
- experimental custom-dimension boundary checks: PASS
- artifact/report upload: PASS

Vanilla BDS stages remain intentionally skipped for the Beta custom-dimension candidate. Retail Minecraft with Beta APIs is the decisive runtime test.

## VERIFIED RETAIL HISTORY

### TEST 58
- True custom-dimension transport works on Android retail with Beta APIs enabled.
- Old destination content failed visual acceptance as too tiny/plain.
- Old fine-layered character geometry failed visual acceptance and was replaced.

### TEST 71
- Glorp-9 reachable.
- **FAIL:** immediate suffocation inside arrival geometry.
- Cause: player feet teleported into solid authored landing geometry.

### TEST 72
- **PASS:** arrival/transport repair works.
- **FAIL VISUAL/DESIGN ACCEPTANCE:** realities had bad sky presentation and felt poorly designed, empty and boring.

### TEST 76
- Major art-direction response to TEST 72: per-reality fog/volumetric atmosphere, denser vertical terrain, large horizon/celestial geometry, four landmark variants per reality and deliberate traversal/sightline routes.
- Retail acceptance not yet recorded.

### TEST 77
- **REJECTED BEFORE RETAIL.** First custom-enemy build failed CI because all ten new enemies used retired `minecraft:pushable` and Late-Fee Drone was below the 12-cube visual floor.

### TEST 78
- Fixed TEST 77 without weakening gates.
- Added ten custom sci-fi hostile enemies: two per custom dimension.
- Full applicable release pipeline passed.

### TEST 79
- Adds native non-hostile ambient life to every reality on top of TEST 78.
- Full applicable release pipeline passed.

## TRUE CUSTOM DIMENSION ARCHITECTURE

Five true custom void dimensions registered through experimental Bedrock `DimensionRegistry` / Beta APIs:

1. Glorp-9
2. Fizz Desert
3. Chrono Shelf
4. Scrap Moon
5. Citadel-ish

This is not the removed fake Overworld teleport architecture.

Deployment path remains:

**Android local Beta world → Realm transfer bridge → PS5 download → local play**

Realm is a transfer bridge; experimental gameplay is judged in the local/downloaded world.

## SKY / ATMOSPHERE BOUNDARY

Current custom-dimension registration does not expose Mojang's internal End-style skybox/cubemap control directly.

Current supported presentation strategy:

- per-player reality-specific fog stack
- `player.fogSettings` with `minecraft:player.fog` compatibility fallback
- five custom fog definitions
- distance fog + volumetric media where supported
- fog removed outside custom realities
- large celestial/horizon structures
- dense upper/lower silhouettes and hanging masses
- ambient native creature motion from TEST 79

Do not claim a nonexistent direct custom-dimension skybox hook.

## REALITY WORLD DESIGN — TEST 76+

- 40x40 authored sectors
- initial 3x3 district (~120x120) before arrival
- adjacent sectors stream as players explore
- serialized ticking-area generation for mobile pressure
- persistent physical sector markers
- terraces, arches, hanging under-island masses, satellite platforms, pylons/spires and upper/lower silhouettes
- one major deterministic landmark per streamed sector
- 5-wide north/south and east/west traversal routes
- four-block headroom carved through dense landmark geometry
- route lighting and clear central orientation nodes

Landmark kits:

**Glorp:** Root Cathedral, Bubble Bog, Shard Grove, Giant Cap  
**Fizz:** Furnace Temple, Impact Crater, Basalt Ribs, Suspended Smeltery  
**Chrono:** Broken Hourglass, Archive Stack, Clock Face Plaza, Frozen Switchyard  
**Scrap:** Crashed Ship, Crusher Pit, Antenna Farm, Factory Spine  
**Citadel outer districts:** Records Tower, Bureaucratic Plaza, Customs Hall, Transit Tower

## SAFE ARRIVAL — LOCKED REGRESSION

Before every custom-reality teleport:

1. Offset arrival from center lodestone.
2. Reassert 3x3 solid landing floor.
3. Clear 3x3 x four-block-high headroom pocket.
4. Place player feet just above floor.
5. Repair the pocket every trip, including already-authored worlds.

Never remove/weaken:

- `retail_test71_arrival_suffocation_regression`
- `safe_custom_dimension_arrival_clearance`
- `existing_world_arrival_repair`

## TEST 78 — TEN CUSTOM SCI-FI ENEMIES

Two custom hostile enemies per reality, each with custom geometry, texture, animation, behavior, special hit and a throttled joke line.

### Glorp-9
- **Glorp Compliance Slug** — brief Slowness. “Your moisture permit expired three molts ago.”
- **Spore Taxman** — brief Poison. “This infection is deductible. Probably.”

### Fizz Desert
- **Warranty Wasp** — brief Weakness. “Damage detected. Warranty voided by damage.”
- **Heat Repo Bot** — brief Hunger. “Repossessing approximately all of your warmth.”

### Chrono Shelf
- **Late-Fee Drone** — stronger short Slowness. “You are 3.7 seconds overdue.”
- **Secondhand Assassin** — brief Darkness. “Killing time. Professionally.”

### Scrap Moon
- **Forklift Crab** — knockback impulse. “Beep beep. OSHA has left this dimension.”
- **Unlicensed Recycler** — stronger brief Weakness. “You have been classified as mixed waste.”

### Citadel-ish
- **Form 27-B** — brief Mining Fatigue. “Combat request denied. Combat will continue.”
- **Queue Enforcement Unit** — brief Slowness. “Please remain violently in line.”

Glorp/Fizz/Chrono/Scrap Reality Contracts now use their two native custom enemies instead of vanilla mobs.

Citadel enemies are capped patrols:
- max three near an occupied sector
- co-op players in the same sector do not multiply the cap
- patrols do not activate in the central sector until a player is at least 12 blocks from arrival

Enemy behavior format is pinned to Bedrock `1.26.10` and uses the current `minecraft:pushable_by_block` + `minecraft:pushable_by_entity` split.

## TEST 79 — AMBIENT LIFE / ATMOSPHERE

One harmless native species now inhabits each custom reality. These have no attack behavior, no progression value and no required drops. They exist to make exploration feel inhabited rather than like an enemy arena.

### Glorp-9 — Bubble Peeper
- small floating alien peeper/blob
- true Bedrock flight stack (`can_fly`, `movement.fly`, `navigation.fly`, `behavior.random_fly`)
- drifts around local islands and structures

### Fizz Desert — Radiator Beetle
- squat heat-resistant industrial beetle
- ground wandering AI
- fire immune

### Chrono Shelf — Minute Moth
- small clock-reality moth
- true flight AI
- moves through open space around shelves/clock structures

### Scrap Moon — Bolt Pigeon
- junk-metal pigeon
- true flight AI
- provides moving skyline life around wreckage and gantries

### Citadel-ish — Receipt Rat
- harmless bureaucratic rat carrying a paper-like panel
- ground wandering AI
- gives streets/plazas non-combat motion

Ambient population/runtime rules:

- local population target is capped at **6 nearby ambient natives**
- co-op players in the same occupied sector are deduplicated for spawn processing
- flying/ground spawn points check for open air / usable surfaces
- occasional small flock pulses add distant motion when local population is low
- ambient natives receive `keepinitkrispy_rs_ambient_native` tag
- entities farther than **58 blocks from every player** in their reality are removed
- cleanup prevents long exploration sessions from leaking an unbounded number of entities on phone/Realm-transfer worlds

New regression gates:

- `five_native_ambient_species`
- `ambient_nonhostile_entities`
- `ambient_flight_ai`
- `ambient_coop_sector_dedupe`
- `ambient_local_population_cap`
- `ambient_distance_cleanup`

## REALITY CONTRACTS

Non-central Glorp/Fizz/Chrono/Scrap sectors retain persistent four-threat Reality Contracts:

- exact sector-tagged threats
- unrelated mobs do not count
- physical hidden-block kill-state persistence
- missing threats recover after unload/reload
- four kills permanently stabilize the sector
- completion exposes a reality-resource cache
- `keepinitkrispy_rs:reality_sectors_cleared` tracks stabilized sectors
- central landing sectors remain contract-safe

## CORE ADD-ON CONTENT

20 featured parody characters remain:

Rich, Shorty, Evil Shorty, Bess, Gerry, Sundae, Bird Dude, Scronchy, Mr. Needs-It, Professor Poop, Captain Drizzle, Nightmare Larry, Sprocket Face, Consensus, Cucumber Rich, Killer Krombo, Shorty Jr., Validator Prime, Franky Lincolnstein, Council Rich.

Character geometry profile remains `retail_clean_forms_v3`. Never restore TEST-58 wafer/layer-cake geometry.

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
14. Streamed Reality Contracts provide repeatable exploration/combat.

World tools: Gravity Spanner, Phase Pick, Freeze Ray, Time-Skip Watch, Scaffold Printer, Matter-Swap Glove, Pocket Black Hole, Chaos Bonker.

## HARD QUALITY RULES

- Read current branch head and this file before editing.
- Never regress to fake Overworld dimensions.
- Never regress realities to tiny pads, sparse scenery, flat resource rooms or random clutter without composition.
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
- TEST 72 visual/world design was unacceptable

**VERIFIED automatically for TEST 79:**
- 1,505 deterministic checks / 0 errors
- JS syntax
- archive integrity
- exact TEST identity
- Creator Tools under documented Beta boundary
- all TEST 76 world-art/atmosphere/traversal gates retained
- all TEST 78 enemy gates retained
- five complete ambient native entity stacks
- all ambient natives are non-hostile
- three flying species have complete current flight AI stack
- co-op sector spawn deduplication
- six-entity local ambient cap
- 58-block distance cleanup

**UNKNOWN until retail/co-op TEST 79:**
- how the five ambient species actually render/animate/pathfind in retail
- whether flying natives move naturally in custom void realities
- whether ambient density feels alive rather than distracting
- whether cleanup/caps behave correctly during long co-op exploration
- whether all ten hostile enemies render/attack as intended
- whether Reality Contracts count either co-op player's kills correctly
- whether TEST 76 sky/fog/world-design overhaul is visually acceptable
- Android performance with dense realities + enemies + ambient life
- full two-player portal/Fabricator/story progression
- Realm transfer → PS5 local co-op behavior

## NEXT PLAYTHROUGH

Use **TEST 79** for Ryan + Ollie's first co-op playthrough.

Do not turn the playthrough into formal QA. Play normally. Record concrete observations when something breaks, looks bad, feels boring/unfair, or is especially fun.
