# Rich & Shorty — Persistent Project State

**Branch:** `gpt/rich-and-shorty`

**Purpose:** Durable authoritative handoff. Read this before changing Rich & Shorty. Do not ask Ryan to reconstruct information already recorded here. If older chat context conflicts with this file, this file wins unless a newer commit or retail observation proves otherwise.

## CURRENT TARGET — TEST 76

Current code candidate:

`c19ec10b64f1ab8d707ae85154dccab807699fc9`

GitHub Actions **Rich & Shorty release gate #76** passed for that exact commit.

Current mobile identity:

- TEST: **76**
- pack version: **0.3.76**
- BP UUID: `c85f1b6c-cd5a-54e2-a71b-7e7becd00d83`
- RP UUID: `309f7ec9-2311-562b-8d8b-f296d326b65e`
- user-facing artifact: `Rich_and_Shorty_TEST76_REALITY_OVERHAUL.mcaddon`
- SHA-256: `5e13d57012aa125376ac2ed0fbd2aae1a502c31ae29feaf99399ae88540556dc`
- size: **121,340 bytes**
- namespace: `keepinitkrispy_rs`

Release gate #76:

- deterministic validation: **1,100 checks PASS / 0 errors**
- JavaScript syntax: PASS
- archive CRC/integrity: PASS
- build-specific BP/RP identity: PASS
- visual regression suite: PASS
- Mojang Creator Tools: PASS under the existing narrow Beta-manifest parser exception
- experimental custom-dimension boundary checks: PASS
- artifact/report upload: PASS

The dedicated-server runtime stages remain intentionally skipped for the Beta custom-dimension candidate because vanilla BDS is not decisive proof of the required Beta APIs experiment.

## VERIFIED RETAIL HISTORY

### TEST 58

- True custom-dimension transport works on Android retail with Beta APIs enabled.
- Original destination content failed quality acceptance: too tiny/plain.
- Original fine-layered character geometry also failed visual acceptance and was replaced.

### TEST 71

- Expanded Glorp-9 could be reached.
- **FAIL:** player immediately suffocated inside arrival geometry.
- Root cause: teleport feet were placed at `y+1`, while the central pad occupied `y+1` and the center lodestone occupied `y+2`.

### TEST 72

- **PASS:** transport / arrival repair works in retail.
- **FAIL VISUAL/DESIGN ACCEPTANCE:** Ryan reported that every dimension's skybox looked bad and the dimensions were poorly designed, very empty, and boring.
- This is a real retail quality failure. TEST 72 is retired as a visual acceptance candidate.

## TRUE CUSTOM DIMENSION ARCHITECTURE

Rich & Shorty uses five true custom void dimensions registered with experimental Bedrock `DimensionRegistry` / Beta APIs:

1. Glorp-9
2. Fizz Desert
3. Chrono Shelf
4. Scrap Moon
5. Citadel-ish

This is not the old fake Overworld teleport architecture.

Required deployment path remains:

**Android local Beta world → Realm transfer bridge → PS5 download → local play**

Realm is a transfer bridge; the experimental runtime is judged in the downloaded/local world.

## SKY / ATMOSPHERE BOUNDARY

Current Bedrock `DimensionRegistry.registerCustomDimension(typeId)` creates a void-generator custom dimension but does not expose a per-dimension vanilla skybox/cubemap parameter like Mojang's internal End rendering.

Do not claim otherwise.

TEST 76 therefore uses the supported controllable layers available to this add-on:

- per-player reality-specific fog stack
- current `player.fogSettings` API, with `minecraft:player.fog` compatibility fallback
- five custom fog definitions
- distance fog plus volumetric air scattering/absorption where the renderer supports it
- fog is removed when the player leaves a custom reality
- large celestial/horizon geometry to break up the default void-sky presentation

The End having a black/special sky does not prove that the custom-dimension registration API exposes the End's internal renderer controls.

## TEST 76 REALITY ART OVERHAUL

TEST 76 is a major response to the TEST 72 visual/design failure, not a small decoration pass.

### Base world scale

- 40x40 authored sectors
- 3x3 initial district before first arrival (~120x120 blocks)
- neighboring sectors stream as the player explores
- serialized ticking-area work to reduce mobile pressure
- persistent physical sector markers prevent needless rebuilding

### Atmosphere

Five distinct fog treatments:

- Glorp: deep teal/green atmosphere
- Fizz: hot red/brown atmosphere
- Chrono: cold indigo atmosphere
- Scrap: industrial gray atmosphere
- Citadel: cool cyan/teal atmosphere

Volumetric air density/media coefficients are included in addition to distance fog.

### Density / vertical depth

Part42 added multi-level terrain and skyline enrichment throughout every reality:

- terraces
- arches
- hanging under-island masses
- satellite islands/platforms
- dense pylons/spires
- large celestial rings/horizon objects
- additional upper and lower silhouettes so the world does not read as a single flat platform in empty void

### Signature landmarks

Every streamed sector now receives **one major deterministic authored focal landmark**, selected from four variants for its reality.

Glorp landmark kit:

- Root Cathedral
- Bubble Bog
- Shard Grove
- Giant Cap

Fizz landmark kit:

- Furnace Temple
- Impact Crater
- Basalt Ribs
- Suspended Smeltery

Chrono landmark kit:

- Broken Hourglass
- Archive Stack
- Clock Face Plaza
- Frozen Switchyard

Scrap landmark kit:

- Crashed Ship
- Crusher Pit
- Antenna Farm
- Factory Spine

Citadel outer-district kit:

- Records Tower
- Bureaucratic Plaza
- Customs Hall
- Transit Tower

The Citadel central sector remains owned by the existing story Citadel instead of being overwritten by an outer-district landmark.

### Composition / traversal

Density is not allowed to become random clutter.

Every sector now has deliberate four-way composition:

- 5-wide north/south route from center to bridges
- 5-wide east/west route from center to bridges
- four blocks of cleared headroom above those routes
- rhythm lighting along the routes
- clear central orientation node
- landmarks are authored first, then traversal spines carve readable entrances/sightlines through them

The intent is that each sector has a visible destination and a readable way to reach the next sector rather than being a pile of decorative blocks.

### Ambient motion

A lightweight reality-only ambient particle loop adds local motion around players without spawning permanent entities or adding a heavy mob system.

## SAFE ARRIVAL — LOCKED REGRESSION

The TEST 71 suffocation fix remains mandatory for all five dimensions.

Before every portal teleport the runtime:

1. Uses an arrival point offset from the center lodestone.
2. Reasserts a 3x3 solid floor.
3. Clears a 3x3 x four-block-high headroom pocket.
4. Places player feet just above the floor.
5. Repairs already-authored dimensions on every trip.

Do not remove or weaken:

- `retail_test71_arrival_suffocation_regression`
- `safe_custom_dimension_arrival_clearance`
- `existing_world_arrival_repair`

## REALITY CONTRACT GAMEPLAY

Non-central Glorp/Fizz/Chrono/Scrap sectors contain persistent Reality Contracts.

- deterministic four-threat contract
- exact sector-tagged mobs
- unrelated mobs do not count
- physical hidden-block kill-state persistence
- missing threats recover after unload/reload
- four kills permanently stabilize the sector
- stabilization exposes a physical reality-resource cache
- `keepinitkrispy_rs:reality_sectors_cleared` tracks stabilized sectors
- central landing sectors are safe from contracts

Current combat rosters remain vanilla-themed and are a future quality target:

- Glorp: slimes / cave spiders / spiders / zombies
- Fizz: husks / blazes / magma cubes / zombies
- Chrono: strays / skeletons / endermen
- Scrap: zombies / pillagers / skeletons / spiders

Unique reality creatures are not yet implemented.

## CORE ADD-ON CONTENT

20 featured custom characters remain:

Rich, Shorty, Evil Shorty, Bess, Gerry, Sundae, Bird Dude, Scronchy, Mr. Needs-It, Professor Poop, Captain Drizzle, Nightmare Larry, Sprocket Face, Consensus, Cucumber Rich, Killer Krombo, Shorty Jr., Validator Prime, Franky Lincolnstein, Council Rich.

Current geometry profile: `retail_clean_forms_v3`. Do not restore TEST-58 fine-layered/wafer geometry.

Reality Fabricator remains a custom 48-cube machine.

Starter property profile remains:

`furnished_two_level_house_full_workshop_clear_driveway_lab_v2`

Core loop remains:

1. Busted Portal Remote + Reality Fabricator.
2. Persistent Home coordinates.
3. Travel to four resource realities.
4. Fabricator rolls a multi-resource recipe.
5. Recipe remains locked until fulfilled.
6. UI shows have/need counts and suggested route.
7. Successful fabrication awards one of eight world-manipulation tools.
8. Immediate previous tool cannot repeat.
9. Side liabilities award tokens/tools and create persistent world consequences.
10. Three Citadel Tokens permanently unlock Citadel-ish.
11. Council Rich interaction stages Evil Shorty.
12. Evil Shorty is multi-phase.
13. Epilogue persists while the Fabricator loop remains replayable.
14. Streamed Reality Contracts add repeatable exploration/combat.

World tools:

- Gravity Spanner
- Phase Pick
- Freeze Ray
- Time-Skip Watch
- Scaffold Printer
- Matter-Swap Glove
- Pocket Black Hole
- Chaos Bonker

Side liabilities:

- Sundae: 8 Glorp + 8 Fizzium → Citadel Token + Glorp coolant-garden consequence
- Bird Dude: 10 Chronodust → Citadel Token + time-roost consequence
- Mr. Needs-It: 12 Scrap → Citadel Token + receiver-tower consequence
- Gerry: 4 of every reality resource → Chaos Bonker + shelf consequence

## IMPORTANT HARD GATES

Do not weaken existing gates merely to make a build pass. Current gates include, among others:

- locked recipe until fulfilled
- Liability Ledger
- persistent Citadel unlock
- Tool Manual
- Fabricator <=50 cubes
- world-tool native cooldown
- staged Council hearing / Evil Shorty boss
- persistent sidequest world changes
- recipe have/need + route UI
- build-specific mobile TEST identities
- true custom dimensions
- awaited destination chunk loading
- no fake Overworld reality route
- retail-clean character forms
- no layer-cake heads/torsos
- starter house/garage/lab
- existing-base migration
- expanded 120x120 initial realities
- streamed reality expansion
- distinct reality skylines
- sector ticking-area serialization
- Reality Contracts
- persistent contract kill state
- reload recovery
- sector cache reward
- safe central landing sectors
- TEST 71 suffocation regression
- per-reality fog atmosphere
- fog removal outside realities
- dense vertical reality authoring
- celestial/horizon landmarks
- current Player fogSettings API
- volumetric reality atmosphere
- signature landmark every sector
- four landmark variants per reality
- ambient reality motion
- generated-JS finalization
- authored traversal spines
- four-bridge sightlines
- dense-geometry headroom carve

## HARD QUALITY RULES

- Read current branch head and this file before editing.
- Never regress to fake Overworld dimensions.
- Never regress realities to tiny pads, sparse scenery, or flat resource rooms.
- Never treat "more blocks" as a substitute for composition/readable traversal.
- Never replace retail-clean cast with generic box people or TEST-58 wafer geometry.
- Never claim schema/static validation proves Beta runtime behavior.
- Never collapse UNKNOWN retail behavior into PASS.
- Keep Mojang validation fail-closed except the exact documented Beta parser contradiction.
- Preserve build-specific TEST identities so Android imports coexist.
- Preserve Android/mobile-first deployment.
- Use `keepinitkrispy_rs` for new content/state.
- Every retail failure must be recorded exactly, repaired from evidence, and protected by a regression gate.
- User-facing downloadable candidates must include their TEST number in the filename.

## CURRENT VERIFICATION BOUNDARY

**VERIFIED by retail observation:**

- custom-dimension transport works
- TEST 71 arrival geometry was unsafe
- TEST 72 arrival/transport repair works
- TEST 72 reality sky/presentation/design quality was unacceptable: bad skybox presentation, poorly designed, empty, boring

**VERIFIED automatically for TEST 76:**

- 1,100 deterministic checks / 0 errors
- JS syntax
- archive integrity
- exact TEST identity
- Creator Tools under documented Beta boundary
- true custom-dimension registration and cross-dimension target signatures
- safe-arrival regression logic
- five custom fog definitions
- Player fog stack application/removal signatures
- volumetric fog definitions
- dense vertical-environment authoring signatures
- signature landmark kits
- deterministic landmark selection
- four-way traversal composition
- current hard regression suite

**UNKNOWN until TEST 76 retail:**

- whether custom fog visibly improves the retail sky/atmosphere enough
- whether volumetric fog is active on Ryan's device/render mode
- whether TEST 76 looks materially less empty/boring in retail
- whether landmark density is attractive rather than cluttered
- whether initial 3x3 generation remains performant on Android after the density increase
- whether streamed sector generation remains smooth enough during exploration
- Reality Contract actual runtime behavior and persistence
- current cast rendering/animation quality in retail
- Fabricator/player UI runtime behavior
- side-liability runtime completion
- Council hearing/Evil Shorty runtime
- Realm transfer → PS5 local behavior for TEST 76

## NEXT TEST

Import **TEST 76** on Android with Beta APIs enabled.

First acceptance target is not story progression. It is the reality overhaul itself:

1. Enter Glorp, Fizz, Chrono and Scrap.
2. Judge atmosphere/sky presentation immediately.
3. Look across the initial district: there should be multiple large silhouettes/landmarks and vertical layers, not mostly empty void.
4. Walk a sector route to a bridge and into a neighboring sector; paths should be readable and headroom should remain clear.
5. Judge landmark quality: authored focal structures should feel intentional, not random block scatter.
6. Watch phone performance while the initial district and one streamed sector generate.
7. Report observed failures exactly; fix from retail evidence before expanding scope.
