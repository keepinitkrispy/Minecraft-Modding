# Rich & Shorty — Persistent Project State

**Branch:** `gpt/rich-and-shorty`

**Purpose:** Durable handoff/state for any future AI or human contributor. Read this before changing Rich & Shorty. Do not ask Ryan to reconstruct information that is already recorded here.

## Current Result

Rich & Shorty is a Minecraft Bedrock parody adventure vertical slice with a stable/Realm-oriented architecture. The add-on is generated deterministically by `rich_shorty/build.py` and sealed as `Rich_and_Shorty_v0.1.0.mcaddon`.

The project is deliberately not using experimental custom dimensions. The four resource realities and Citadel-ish are authored pocket-world zones in the Overworld reached through a scripted Portal Remote. This preserves the multiverse loop without making experimental dimension APIs a hard dependency.

## VERIFIED — Current Green Baseline

As of the `Persist Citadel unlock and pace reality tools` release-gate run:

- deterministic local validation: PASS
- Mojang Minecraft Creator Tools full suite: PASS, fail-closed on warnings
- Mojang Minecraft Creator Tools Add-On suite: PASS, fail-closed on warnings
- real current Bedrock Dedicated Server boot: PASS
- custom Reality Fabricator block registry/placement: PASS
- all 20 featured custom entities summon on real Bedrock server: PASS
- archive integrity: PASS
- JavaScript syntax check: PASS
- final creator/pack namespace: `keepinitkrispy_rs`
- runtime regression gate exists for the Bedrock 1.26.10 `minecraft:pushable` split

Do not weaken these gates to make a build pass.

## VERIFIED — Visual Architecture

The first boxier visual pass was rejected internally before Ryan was asked to test it.

The current cast was rebuilt as high-detail voxel sculpture:

- 20 featured characters
- 10 articulated bones per character
- current generated character geometry is roughly 86–122 authored cubes per character
- rounded/stepped voxel head construction rather than one-box heads
- projected facial features
- tapered layered torsos
- segmented upper/lower arms and legs
- identity-specific hair, clothing and silhouette details
- Cucumber Rich is a genuinely non-humanoid custom rig

The exact shipping `.geo.json` + texture files are rendered into `previews/rich_shorty_cast_actual_geometry.png` by CI. This is not concept art.

The Reality Fabricator is a custom 48-cube machine with an asymmetrical silhouette and explicit dark-metal / portal-green / warning / screen material regions. It intentionally stays under Creator Tools' >50-cube custom-block performance warning threshold.

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
9. Side liabilities reward Citadel Tokens / special tools.
10. Three tokens permanently unlock Citadel-ish.
11. Citadel-ish contains the Evil Shorty multi-phase boss encounter.
12. Defeating Evil Shorty persists the epilogue state; the Fabricator loop remains replayable afterward.

## Reality Environments

The resource zones are not flat test pads anymore.

- **Glorp-9:** fungal/goo basin, warped stalks, luminous roots, slime stepping route, water basin
- **Fizz Desert:** red-sand caldera, basalt/terracotta chimneys, magma fractures
- **Chrono Shelf:** packed/blue-ice terraces, amethyst time pillars, broken clock motif
- **Scrap Moon:** tuff salvage field, copper/iron wreckage, cranes, rails and gantries
- **Citadel-ish:** central tower, satellite towers, bridges, civic ring, customs structure and council dais

## World Tool Pool

- Gravity Spanner
- Phase Pick
- Freeze Ray
- Time-Skip Watch
- Scaffold Printer
- Matter-Swap Glove
- Pocket Black Hole
- Chaos Bonker

The tools intentionally manipulate traversal/world state. Native Bedrock use cooldowns are now attached so the effects cannot be controller-spammed without pacing.

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

## Hard Quality Rules

- Never replace the sculpted cast with generic box people.
- Never claim a static/schema pass proves runtime behavior.
- Never hand Ryan a phone/Realm test build merely because JSON validates.
- Keep Mojang validation fail-closed on warnings.
- Keep a real Bedrock Dedicated Server boot/summon/placement gate.
- Keep exact shipping-geometry approval renders.
- Stable PS5/Realm behavior is preferred over experimental APIs.
- Preserve the Android/mobile-first deployment path; do not silently require Ryan to use a desktop.
- New generated content must use the creator-specific `keepinitkrispy_rs` namespace / namespaced asset paths.

## Current Verification Boundary

**VERIFIED:** structure, schema, archive, script syntax, server pack loading, custom-block registration/placement, all custom-entity server registration/summoning, exact generated-geometry offline render review.

**UNKNOWN until client/player test:** actual Bedrock client rendering, animation playback in the retail client, controller/touch UI behavior, real player-driven Portal Remote interaction, player-driven Fabricator custom component execution, full environment generation triggered through the UI, Realm → PS5 behavior.

Do not collapse UNKNOWN into PASS.

## Next Work

1. Add player-facing Tool Manual / per-tool usage feedback.
2. Add hard regression assertions for the locked recipe, Liability Ledger, high-detail character cube floor, and <=50-cube Fabricator.
3. Expand the real-server smoke gate to exercise every block ID used by authored reality environments.
4. Do one more exact visual review after those changes.
5. Produce the first client-test candidate `.mcaddon` for Ryan only after all automated/server gates are green.
6. After Ryan's actual Bedrock/Realm test, record observed behavior here as PASS/FAIL and fix from evidence.
