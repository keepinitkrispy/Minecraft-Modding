# Rich & Shorty — Persistent Project State

**Branch:** `gpt/rich-and-shorty`

**Purpose:** Durable authoritative handoff for Rich & Shorty. Read this before changing the project. Do not ask Ryan to reconstruct information already recorded here. If this file conflicts with older chat context, this file wins unless a newer commit/test result proves otherwise.

## VERIFIED — Current Engineering/Test Baseline

The current code candidate is commit:

`7eb0a13e3817055c181952de38a44793a3b5213a`

GitHub Actions **Rich & Shorty release gate #71** passed for that exact commit.

Current mobile test identity:

- TEST: **71**
- pack version: **0.3.71**
- BP UUID: `87ef4c1a-6479-5dc4-a2a0-2d8a7edeaa6c`
- RP UUID: `b82b3fd2-c96b-5df4-a436-7c8e99208f32`
- artifact: `Rich_and_Shorty_v0.1.0.mcaddon`
- exact add-on SHA-256: `992fcdc4769bb295b1cd0c37835a44e9c0ec5c8f2f48554a5e75814119569616`
- exact add-on size: **113,124 bytes**
- final namespace: `keepinitkrispy_rs`

Release-gate #71 results:

- deterministic validation: **1,013 checks PASS / 0 errors**
- JavaScript syntax: PASS
- archive CRC/integrity: PASS
- exact build-specific BP/RP identity: PASS
- visual regression tests: PASS
- Mojang Minecraft Creator Tools: PASS under the documented Beta-runtime boundary below
- artifact/report upload: PASS

Mojang Creator Tools 0.17.7 has one contradictory `CHKMANIF` parser behavior for `@minecraft/server: beta`: its script-module test recognizes the Beta dependency, while another manifest parser attempts numeric parsing. The CI wrapper allows **only that exact known signature** and still fails closed on every other error/warning. Do not broaden this allowlist.

## VERIFIED — Dimension Architecture

Rich & Shorty now uses **five true custom void dimensions** registered through the experimental Bedrock `DimensionRegistry` / Beta API path:

1. Glorp-9
2. Fizz Desert
3. Chrono Shelf
4. Scrap Moon
5. Citadel-ish

This is **not** the old fake same-dimension Overworld teleport architecture.

TEST 58 on Android retail previously proved that the custom-dimension transport itself works with Beta APIs enabled. TEST 58 also proved that the old destination content was unacceptable: it was essentially a tiny/plain prototype. That old destination authoring has been replaced.

The current runtime requires the world **Beta APIs** experiment. The intended deployment path remains:

**Android local Beta world → Realm transfer bridge → PS5 download → local play**

Realm is a transfer bridge here; the experimental gameplay/runtime is validated in the downloaded local world.

## VERIFIED — Dimension Visual Overhaul (part37)

The old one-shot `49x49` prototype destination has been removed from the shipping custom-dimension route.

Current reality construction:

- each reality initially authors a **3x3 district of 40x40 sectors** before arrival
- initial authored footprint is approximately **120x120 blocks**
- neighboring 40x40 sectors stream in as the player explores
- sector work is serialized through ticking-area loading to limit mobile pressure
- each sector receives a persistent physical marker so it is not rebuilt every script session

Distinct visual grammar:

- **Glorp-9:** warped fungal archipelago, giant luminous stalks, slime/water features, floating amethyst shards, dark-prismarine/blackstone floating-island mass.
- **Fizz Desert:** broken red desert islands, basalt/terracotta towers, magma fissures, lava points, suspended blackstone furnace-rock.
- **Chrono Shelf:** quartz/calcite terraces, blue-ice seams, hovering amethyst clock structures, end-rod timing markers.
- **Scrap Moon:** dark industrial salvage field, iron/copper cranes, rails, gantries, machine carcasses and redstone-lit wreckage.
- **Citadel-ish:** central story Citadel plus streamed outer bureaucratic metropolis with towers, bridges, civic structures and beacons.

The realities are deliberately floating/impossible spaces rather than normal Overworld terrain with a palette swap.

## VERIFIED — Dimension Gameplay Overhaul (part39/part40)

Scale alone was not accepted as enough. Non-central resource sectors now contain persistent **Reality Contracts** instead of being scenery plus loose ore.

For every non-central sector in Glorp/Fizz/Chrono/Scrap:

1. A themed encounter arena/pylon treatment frames the sector lodestone.
2. Entering the sector activates a deterministic four-threat contract.
3. Each reality has a distinct enemy roster matching its terrain/combat feel.
4. Contract mobs carry exact sector tags so unrelated mobs do not count.
5. Kill progress persists physically under the sector floor using a five-state hidden block marker.
6. Reload/unload recovery respawns only missing contract threats based on persisted progress.
7. Clearing all four threats permanently stabilizes that sector.
8. Completion exposes an obvious physical cache around the lodestone using that reality's custom resource blocks.
9. A namespaced player counter records total stabilized sectors.
10. Central landing sectors remain safe so portal arrival is not an unavoidable ambush.

Current encounter flavor:

- **Glorp:** slimes / cave spiders / spiders / zombies; movement interacts with slime-heavy terrain.
- **Fizz:** husks / blazes / magma cubes / zombies; ranged/fire pressure around magma terrain.
- **Chrono:** strays / skeletons / endermen; ranged pressure on slippery ice/terrace layouts.
- **Scrap:** zombies / pillagers / skeletons / spiders; mixed ranged/melee combat through industrial structures.

Current sector-completion property is correctly namespaced:

`keepinitkrispy_rs:reality_sectors_cleared`

Hard gates now include:

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

## Current Cast / Visual Profile

20 featured characters remain in the pack:

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

The current shipping character profile is `retail_clean_forms_v3`: articulated custom geometry designed to avoid the layered/wafer look rejected in TEST 58. Do not resurrect the old fine-layered geometry merely to increase cube count.

Current shipping cube counts:

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

The Reality Fabricator remains a custom **48-cube** machine, intentionally below the Creator Tools >50-cube custom-block warning threshold.

## Starter Base

The starter property has already been rebuilt after the earlier visually rejected pass.

Current profile:

`furnished_two_level_house_full_workshop_clear_driveway_lab_v2`

It includes the furnished two-level house, full garage/workshop, clear flush driveway, finished underground reality lab, Fabricator placement and persistent Home-coordinate recovery. Existing deployed TEST-58-era bases have an in-place visual migration path rather than requiring a fresh world.

## Core Gameplay Loop

1. Player receives the Busted Portal Remote and Reality Fabricator.
2. Home/garage coordinates persist for return travel.
3. Player travels through true custom dimensions for Glorp Crystal, Fizzium, Chronodust and Scrap Fragment.
4. Reality Fabricator rolls a recipe using multiple reality resources.
5. The recipe remains locked until fulfilled; travel/interactions do not reroll it.
6. Recipe UI shows have/need inventory counts and a suggested reality route.
7. Successful fabrication consumes resources and awards one of eight world-manipulation tools.
8. The immediately previous tool is excluded to prevent consecutive duplicate results.
9. Side liabilities award Citadel Tokens/special tools and leave persistent physical world consequences.
10. Three Citadel Tokens permanently unlock Citadel-ish.
11. Council Rich interaction stages the Evil Shorty encounter; Evil Shorty does not auto-ambush the player on arrival.
12. Evil Shorty is a multi-phase boss encounter.
13. Epilogue state persists while the Fabricator/reality loop remains replayable.
14. Streamed Reality Contracts add repeatable exploration/combat goals outside the original story path.

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

The Portal Remote includes the Liability Ledger and Reality Tool Manual. Native Bedrock use cooldowns are retained for pacing.

## Important Existing Regression Gates

Do not weaken these to make future builds pass:

- `locked_recipe_until_fulfilled`
- `liability_ledger`
- `persistent_citadel_unlock`
- `tool_manual`
- `fabricator_max_50_cubes`
- `world_tool_native_cooldown`
- `staged_citadel_hearing_boss`
- `persistent_sidequest_world_changes`
- `recipe_have_need_and_route_ui`
- `mobile_coexisting_test_builds`
- `retail_animation_explicit_zero_keyframes`
- `manifest_format_version_2`
- `documented_mcaddon_mcpack_composite`
- `build_specific_test_pack_identity`
- `starter_house_garage_underground_lab`
- `garage_capsule_native_use_interaction`
- `no_fake_overworld_reality_travel`
- `home_explicit_overworld`
- `true_custom_dimensions_beta_api`
- `awaited_custom_dimension_chunk_loading`
- `cross_dimension_portal_transit`
- `retail_clean_character_forms`
- `no_layer_cake_heads`
- `no_layer_cake_torsos`
- `articulated_cast_preserved`
- `furnished_two_level_house`
- `full_garage_workshop`
- `clear_flush_driveway`
- `finished_reality_lab`
- `existing_base_visual_migration`
- all dimension visual/gameplay gates listed above
- Bedrock 1.26.10 pushability split regression gate

## Hard Quality Rules

- Read the current branch head and this state file before editing.
- Never regress to fake Overworld 'dimensions'.
- Never regress the realities to tiny flat pads or scenery-only resource rooms.
- Never replace the retail-clean cast with generic box people or TEST-58 layered/wafer geometry.
- Never claim schema/static validation proves Beta runtime behavior.
- Never collapse UNKNOWN retail behavior into PASS.
- Keep Mojang validation fail-closed except the exact documented Creator Tools Beta parser contradiction.
- Preserve build-specific TEST identities so Android imports can coexist.
- Preserve the Android/mobile-first workflow; do not silently require Ryan to use a desktop.
- Use the `keepinitkrispy_rs` creator namespace for new content/state.
- When a retail test fails, fix from observed evidence and rerun the full applicable gate set.

## Current Verification Boundary

**VERIFIED for TEST 71:**

- deterministic generation and validation (1,013 checks / 0 errors)
- JS syntax
- archive integrity
- exact test-pack identity
- all current hard static/regression signatures
- Creator Tools validation under the narrowly documented Beta-manifest parser exception
- manifest Beta dependency
- startup custom-dimension registration code
- awaited destination ticking-area loading
- cross-dimension teleport target
- absence of the old fake Overworld route
- exact shipping visual approval renders generated by CI

**Previously VERIFIED on Android retail in TEST 58:**

- true custom-dimension transport works with Beta APIs enabled

**UNKNOWN until TEST 71 retail/player test:**

- expanded 120x120 initial reality construction under actual Android retail runtime
- streamed sector generation while exploring
- current reality visual quality in the retail renderer
- Reality Contract enemy spawning/tagging/death accounting
- persisted sector progress after unload/reload
- sector cache exposure after four kills
- performance of the expanded streamed realities on phone
- current cast animation/rendering behavior in retail
- full controller/touch Portal Remote flow
- Fabricator custom-component interaction in real play
- side-liability turn-ins/world consequences in real play
- Council hearing/Evil Shorty staging in real play
- Realm transfer and PS5 local-world behavior for TEST 71

A vanilla Bedrock Dedicated Server CI world is **not** treated as decisive runtime proof for this artifact because it does not run the required Beta APIs experiment. The decisive runtime gate is a retail Minecraft world with Beta APIs enabled.

## Next Work

1. Import the exact **TEST 71** candidate on Android with Beta APIs enabled.
2. First priority: enter each reality and judge the new scale/visual identity, then move into at least one non-central sector and complete a Reality Contract.
3. Verify sector progress survives leaving/re-entering and that the resource cache appears on completion.
4. Record observed PASS/FAIL here; fix only from real evidence.
5. If Android local runtime is clean, use the existing Realm transfer path and test the downloaded world on PS5.
