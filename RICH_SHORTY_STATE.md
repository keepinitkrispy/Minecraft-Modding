# Rich & Shorty — Persistent Project State

**Branch:** `gpt/rich-and-shorty`

**Purpose:** Durable handoff/state for any future AI or human contributor. Read this before changing Rich & Shorty. Do not ask Ryan to reconstruct information that is already recorded here.

## Current Result

Rich & Shorty is a Minecraft Bedrock parody adventure vertical slice with a stable/Realm-oriented architecture. The add-on is generated deterministically by `rich_shorty/build.py` and sealed as `Rich_and_Shorty_v0.1.0.mcaddon`.

The project is deliberately not using experimental custom dimensions. The four resource realities and Citadel-ish are authored pocket-world zones in the Overworld reached through a scripted Portal Remote. This preserves the multiverse loop without making experimental dimension APIs a hard dependency.

## VERIFIED — Current Client-Test Candidate

The authoritative artifact approved to leave automated/server testing is the candidate built from branch commit `7a9ef901dc2bbe29bf7290b05936296f6dd99fb2`.

Exact tested add-on SHA-256:

`637b8e07930f924e72bb9ca5483afd461efebc4a254d7dadf3d46cd9fa9a3bcf`

Exact tested add-on size: **171,270 bytes**.

Release-gate results for that exact artifact:

- deterministic local validation: **537 checks PASS / 0 errors**
- Mojang Minecraft Creator Tools full suite: **PASS / 0 errors / 0 warnings / 0 recommendations**
- Mojang Minecraft Creator Tools Add-On suite: **PASS / 0 errors / 0 warnings / 0 recommendations**
- real current Bedrock Dedicated Server **1.26.44.3** boot: PASS
- custom Reality Fabricator block registry/placement: PASS
- real-server smoke of every vanilla block ID used by authored reality construction/world tools: PASS
- all 20 featured custom entities summon on real Bedrock server: **20/20 PASS**
- archive CRC/integrity: PASS
- JavaScript syntax check: PASS
- final creator/pack namespace: `keepinitkrispy_rs`
- runtime regression gate exists for the Bedrock 1.26.10 `minecraft:pushable` split

This is now the authoritative baseline. Do not weaken these gates to make a later build pass.

## VERIFIED — Visual Architecture

The first boxier visual pass was rejected internally before Ryan was asked to test it.

The current cast was rebuilt as high-detail voxel sculpture:

- 20 featured characters
- 10 articulated bones per character
- generated character geometry spans **86–122 authored cubes per character**
- rounded/stepped voxel head construction rather than one-box heads
- projected facial features
- tapered layered torsos
- segmented upper/lower arms and legs
- identity-specific hair, clothing and silhouette details
- Cucumber Rich is a genuinely non-humanoid custom rig

Exact current cube counts:

- Rich 120
- Shorty 96
- Evil Shorty 102
- Bess 106
- Gerry 97
- Sundae 98
- Bird Dude 86
- Scronchy 99
- Mr. Needs-It 95
- Professor Poop 93
- Captain Drizzle 112
- Nightmare Larry 105
- Sprocket Face 107
- Consensus 96
- Cucumber Rich 90
- Killer Krombo 102
- Shorty Jr. 97
- Validator Prime 116
- Franky Lincolnstein 100
- Council Rich 122

The exact shipping `.geo.json` + texture files are rendered into `previews/rich_shorty_cast_actual_geometry.png` by CI. This is not concept art. The client-candidate cast sheet was manually inspected after the full green run and retained.

The Reality Fabricator is a custom **48-cube** machine with an asymmetrical silhouette and explicit dark-metal / portal-green / warning / screen material regions. It intentionally stays under Creator Tools' >50-cube custom-block performance warning threshold. The client-candidate Fabricator render was manually inspected after the full green run and retained.

## Current Cast

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

The intent is obvious affectionate sci-fi-cartoon parody, not direct asset copying.

## Core Gameplay Loop

1. Player receives a Busted Portal Remote and Reality Fabricator on first spawn.
2. Home/garage coordinates are persisted so the player can always return.
3. Portal Remote reaches four authored resource realities:
   - Glorp-9 — Glorp Crystal
   - Fizz Desert — Fizzium
   - Chrono Shelf — Chronodust
   - Scrap Moon — Scrap Fragment
4. Reality Fabricator rolls one random recipe using at least two reality resources.
5. **The recipe remains locked while the player travels and gathers it.** It does not reroll on every interaction.
6. Completing the recipe consumes the materials and produces one random world-manipulation tool.
7. The immediately previous tool is excluded so consecutive fabrication results do not repeat.
8. A new different recipe is pre-rolled only after successful fabrication.
9. Side liabilities reward Citadel Tokens / special tools and leave persistent physical consequences in their realities.
10. Three tokens permanently unlock Citadel-ish.
11. Citadel-ish is a story hub. Evil Shorty does **not** auto-spawn on arrival.
12. Interacting with Council Rich begins the Council hearing and stages the Evil Shorty encounter in the central chamber.
13. Evil Shorty has a multi-phase boss fight.
14. Defeating Evil Shorty persists the epilogue state; the Fabricator loop remains replayable afterward.

## Reality Environments

The resource zones are not flat test pads.

- **Glorp-9:** fungal/goo basin, warped stalks, luminous roots, slime stepping route, water basin. The old `lily_pad` command identifier was rejected by current Bedrock and deliberately replaced with server-verified slime stepping pads.
- **Fizz Desert:** red-sand caldera, basalt/orange-terracotta chimneys, magma fractures. Generic `terracotta` was rejected by current Bedrock and replaced with the server-verified `orange_terracotta` ID.
- **Chrono Shelf:** packed/blue-ice terraces, amethyst time pillars, broken clock motif.
- **Scrap Moon:** tuff salvage field, copper/iron wreckage, cranes, rails and gantries.
- **Citadel-ish:** central tower, satellite towers, bridges, civic ring, customs structure and council dais.

The real-Bedrock release gate smoke-tests the full vanilla block palette used by reality construction and world-tool rewrites so invalid command identifiers cannot silently reach the client candidate.

## Side-Quest World Consequences

Completed side liabilities now leave one-shot persistent landmarks instead of existing only as tags/menu entries:

- **Sundae:** Glorp-9 gains a luminous coolant garden beside the landing pad.
- **Bird Dude:** Chrono Shelf gains a calcite/amethyst ceremonial time-roost.
- **Mr. Needs-It:** Scrap Moon gains an iron/copper receiver tower.
- **Gerry:** Scrap Moon gains the actual multiversal shelf he requested resources to stabilize.

Each consequence has a per-player persistent effect flag to prevent repeated rebuilding/message spam. The construction palette is covered by the real-Bedrock block parser/placement smoke gate. Actual player-triggered quest completion remains part of the retail-client test boundary.

## World Tool Pool

- Gravity Spanner
- Phase Pick
- Freeze Ray
- Time-Skip Watch
- Scaffold Printer
- Matter-Swap Glove
- Pocket Black Hole
- Chaos Bonker

The tools intentionally manipulate traversal/world state. Native Bedrock use cooldowns are attached so the effects cannot be controller-spammed without pacing.

The Portal Remote includes a **Reality Tool Manual**, and each tool gives first-use help describing whether it is used in the air or on a target block and what it changes.

## Story / Progression

### Act I — Warranty Void
Complete the first locked Fabricator recipe.

### Act II — Side Effects
Side liabilities become mechanically completable after the first fabrication.

Current side liabilities:

- Sundae — 8 Glorp Crystals + 8 Fizzium → Citadel Token
- Bird Dude — 10 Chronodust → Citadel Token
- Mr. Needs-It — 12 Scrap Fragments → Citadel Token
- Gerry — 4 of every reality resource → Chaos Bonker

### Act III — The Least Democratic Citadel
Three Citadel Tokens permanently unlock the Citadel-ish route. The unlock is persistent and does not disappear if tokens are later dropped/lost/stored.

Arrival is not an immediate boss ambush. The player reaches the Citadel hub, interacts with Council Rich to begin the Council hearing, and that interaction stages Evil Shorty in the central chamber as the final liability.

### Epilogue — Randomness Wins
Evil Shorty defeated; endless Fabricator/resource/tool loop remains available.

## Liability Ledger

The Portal Remote includes an in-world Liability Ledger. It reports:

- current act
- current objective
- fabrication count
- Citadel token count
- persistent Citadel unlock state
- current locked Fabricator recipe
- side-liability completion
- Evil Shorty completion state

The player should not need an external wiki to understand the main progression loop.

## Hard Regression Gates

Current validation explicitly rejects regressions in:

- `locked_recipe_until_fulfilled`
- `liability_ledger`
- `persistent_citadel_unlock`
- `tool_manual`
- `sculpted_cast_min_80_cubes`
- `fabricator_max_50_cubes`
- `world_tool_native_cooldown`
- `staged_citadel_hearing_boss`
- `persistent_sidequest_world_changes`
- Bedrock 1.26.10 pushability component split

## Hard Quality Rules

- Never replace the sculpted cast with generic box people.
- Never claim a static/schema pass proves runtime behavior.
- Never hand Ryan a phone/Realm test build merely because JSON validates.
- Keep Mojang validation fail-closed on warnings.
- Keep a real Bedrock Dedicated Server boot/summon/custom-block/environment-palette gate.
- Keep exact shipping-geometry approval renders.
- Stable PS5/Realm behavior is preferred over experimental APIs.
- Preserve the Android/mobile-first deployment path; do not silently require Ryan to use a desktop.
- New generated content must use the creator-specific `keepinitkrispy_rs` namespace / namespaced asset paths.

## Current Verification Boundary

**VERIFIED:** structure, schema, archive, script syntax, server pack loading, custom-block registration/placement, full authored vanilla block identifier palette on current real Bedrock, all custom-entity server registration/summoning, exact generated-geometry offline render review, and the hard gameplay/visual regression signatures listed above.

**UNKNOWN until client/player test:** actual Bedrock retail-client rendering, animation playback in the retail client, controller/touch UI behavior, real player-driven Portal Remote interaction, real player-driven Fabricator custom component execution, full reality generation triggered through the UI, side-quest turn-ins and their persistent world changes under real play, staged Council hearing under real player interaction, and Realm → PS5 behavior.

Do not collapse UNKNOWN into PASS.

## Next Work

1. **Ryan client test:** import the exact SHA-256-pinned current client candidate into Bedrock/Realm using the existing Android/mobile-first path.
2. Record actual observed retail-client behavior here as PASS/FAIL, especially:
   - RP model/texture rendering
   - animations
   - Portal Remote ActionForms/controller interaction
   - home/reality travel
   - Reality Fabricator interaction and locked recipe persistence
   - one full resource → fabrication loop
   - Liability Ledger and Tool Manual
   - environment construction
   - one side-quest turn-in plus persistent world landmark
   - Citadel unlock and Council hearing
3. Fix only from observed evidence; rerun all automated/server gates for every repair.
4. After the retail-client/Realm pass is clean, bump out of `v0.1.0` and package the next distributable candidate.
