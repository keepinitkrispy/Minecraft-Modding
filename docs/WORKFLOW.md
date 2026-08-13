# Character Creation Workflow

This workflow implements the project methodology for Minecraft Bedrock characters and companions.

## Input contract

The minimum useful input is:

- a drawing/reference image, **or**
- a plain-language concept

Optional creator choices may include:

- name
- personality
- special ability
- summon/tame item
- backstory
- desired size/style

Do **not** force the creator to fill every field before work can start. Infer safe, reversible defaults and ask only when a missing choice materially changes the creative result.

## Non-negotiable build principle

**Do not engineer a polished gameplay system around bad geometry.**

For character work, technical validation order and development order are not the same thing. The static visual model must pass a fidelity gate before substantial rigging, animation, AI, scripting, recipes, special effects, or packaging work proceeds.

A technically valid but visually generic, lazy, or source-inaccurate model is a failed build stage.

## Build loop

1. **Interpret intent**
   - identify recognizable silhouette, proportions, palette, personality cues, material/substance, and gameplay intent
   - separate direct creator requirements from inferred defaults
   - identify the features that make the character unmistakably itself

2. **Retrieve relevant verified knowledge**
   - reuse known-good Bedrock patterns for packaging, geometry, UVs, rigging, animation, AI, interactions, scripts, and platform constraints
   - do not treat untested project code as a verified reusable rule
   - retrieve known visual failure modes for similar body types, scales, materials, or rigs

3. **Create a structured character spec**
   - entity identity/namespace
   - target height, width, and depth
   - silhouette/profile requirements
   - geometry strategy
   - materials/textures
   - intended rig/animation set
   - behavior contract
   - special move
   - interaction/tame/summon path
   - survival/creative access where appropriate

4. **Build and pass the static visual-fidelity gate**
   - author the naked static Bedrock geometry first
   - use deliberate width/depth shaping rather than the cheapest box-stack approximation
   - preserve rounded volume, taper, asymmetry, articulation, or other defining forms when the source requires them
   - apply enough base material/color treatment to judge whether the intended substance reads correctly
   - render the **actual geometry** from front, side, back, and 3/4 views
   - include an in-scale player comparison when scale matters
   - compare silhouette, width/depth profile, proportions, defining features, limb placement, color/material read, and source-art fidelity

   **FAIL the gate** if the model is technically valid but looks generic, blocky in the wrong way, flattened, incorrectly proportioned, visually cheap, or unlike the source.

   **Do not continue to substantial rigging/gameplay work until this gate passes.**

5. **Rig and finish character assets**
   - build the intended bone hierarchy
   - verify upper/lower limb segmentation and pivots where articulation is required
   - finish textures/UVs/materials
   - create idle/locomotion/action animations and controllers
   - render representative poses from the actual geometry/rig before declaring the rig visually acceptable

6. **Build gameplay behavior**
   - behavior-pack entity definitions
   - tame/follow/sit/stay/attack patterns as applicable
   - special move
   - items/recipes/loot/functions/scripts as needed
   - character tracking data
   - survival/creative access where appropriate

7. **Validate statically**
   - JSON parse
   - manifest/dependencies
   - references resolve
   - known Bedrock schema/legacy problems
   - archive layout
   - rig/bone references where applicable
   - run repository validators/build scripts where applicable

8. **Package**
   - produce an importable `.mcaddon`
   - bump versions when needed to avoid Realm/cache confusion

9. **Runtime test in Bedrock**
   - import/load
   - spawn/summon
   - movement/follow/sit/stay/attack as applicable
   - special move
   - visual/UV/animation/pivot check
   - target-platform interaction check
   - regression check against prior working content

10. **Record evidence**
   - what actually worked
   - what failed
   - exact observed symptoms
   - suspected cause versus established cause
   - fix applied
   - retest result

11. **Promote reusable learning**
   - only after evidence supports it
   - promote the smallest useful rule
   - mark conflicting older rules SUPERSEDED
   - apply the new rule automatically to future relevant builds

## Companion baseline

Unless the concept calls for something else, a polished companion should have a coherent subset of:

- recognizable source-art silhouette
- idle + locomotion animation
- tame/bond interaction
- follow
- sit/stay
- attack/defend behavior where appropriate
- one distinctive special move
- spawn egg or creative access
- survival-accessible summon/tame path where appropriate
- clear player feedback

This is a quality floor, not a requirement to force identical mechanics onto every character.

## Geometry / asset authoring

Use the best available method for the environment, but never let tool convenience dictate the character's shape.

A simple cuboid solution is acceptable only when it actually matches the intended form. If the source needs a rounded voxel body, stepped curvature, layered depth, tapered profile, unusual silhouette, or articulated appendage, deliberately build that geometry instead of substituting a cheaper generic approximation.

Small characters require extra care because a one-model-unit change can materially alter silhouette, apparent volume, and limb placement.

Desktop tools such as Blockbench may be useful accelerators, but they are **not** a required dependency for the project. Offline/generated geometry, image-assisted workflows, scripts, or future model-generation tools are acceptable if the output is valid and passes visual/runtime checks.

The target workflow remains Android/mobile-first with Realm → PS5 deployment.

## Validation ladder

The ladder reports verification strength; it is **not** a mandatory development sequence:

1. structural/package
2. schema/static
3. import
4. spawn/placement
5. behavior
6. visual
7. regression

For new character geometry, an offline/static **visual-fidelity preflight happens before the expensive engineering stages**, even though final in-game visual verification still occurs later.

A static PASS does not mean runtime VERIFIED, and a schema-valid model does not mean visually approved.

## Character state

Track each character with a status that reflects evidence, not optimism. Suggested states:

- `concept` — requirements/source being interpreted
- `visual_gate` — geometry/material is being authored or reviewed
- `visual_approved` — static geometry passed source-fidelity review
- `static_valid` — source/package checks pass, runtime untested
- `runtime_testing` — imported/spawned, behavior/visual testing incomplete
- `ready` — intended core behavior verified in Bedrock
- `stable` — repeated/regression testing passed
- `archived` — superseded/retired

Record known defects and next test separately from the status.

## Platform test path

Typical target path:

1. build/package the `.mcaddon`
2. import on Android Bedrock
3. apply/upload through Realm
4. join from PS5 and accept pack download
5. perform targeted in-world tests
6. report exact observations back into project evidence

## Iteration rule

Do not rebuild from scratch merely because one thing is wrong. Preserve known-good behavior, make the smallest correct change, retest the affected feature, then regression-test what previously worked.

But if a character has not yet passed the visual-fidelity gate, do not preserve a bad geometry foundation merely because engineering work has already been attached to it. Fix the foundation first.

## Definition of done

The character is not done because files exist.

It is done when the requested result exists at the strongest verification level available, with remaining untestable boundaries stated explicitly.
