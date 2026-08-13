# Character Creation Workflow

This workflow implements the open methodology in `docs/METHODOLOGY.md` for Minecraft Bedrock characters and companions.

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

## Build loop

1. **Interpret intent**
   - identify recognizable silhouette, proportions, palette, personality cues, and gameplay intent
   - separate direct creator requirements from inferred defaults

2. **Retrieve relevant verified knowledge**
   - reuse known-good Bedrock patterns for packaging, geometry, UVs, rigging, animation, AI, interactions, scripts, and platform constraints
   - do not treat untested project code as a verified reusable rule

3. **Create a structured character spec**
   - entity identity/namespace
   - geometry and scale
   - materials/textures
   - animation set
   - behavior contract
   - special move
   - interaction/tame/summon path
   - survival/creative access where appropriate

4. **Build the artifact**
   - behavior-pack files
   - resource-pack files
   - geometry
   - textures/UVs
   - animation/controller files
   - items/recipes/loot/functions/scripts as needed
   - character tracking data

5. **Validate statically**
   - JSON parse
   - manifest/dependencies
   - references resolve
   - known Bedrock schema/legacy problems
   - archive layout
   - run repository validators/build scripts where applicable

6. **Package**
   - produce an importable `.mcaddon`
   - bump versions when needed to avoid Realm/cache confusion

7. **Runtime test in Bedrock**
   - import/load
   - spawn/summon
   - movement/follow/sit/stay/attack as applicable
   - special move
   - visual/UV/animation/pivot check
   - target-platform interaction check
   - regression check against prior working content

8. **Record evidence**
   - what actually worked
   - what failed
   - exact observed symptoms
   - suspected cause versus established cause
   - fix applied
   - retest result

9. **Promote reusable learning**
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

Use the best available method for the environment.

Desktop tools such as Blockbench may be useful accelerators, but they are **not** a required dependency for the project. Offline/generated geometry, image-assisted workflows, scripts, or future model-generation tools are acceptable if the output is valid and passes visual/runtime checks.

The target workflow remains Android/mobile-first with Realm → PS5 deployment.

## Validation ladder

Report the highest level actually reached:

1. structural/package
2. schema/static
3. import
4. spawn/placement
5. behavior
6. visual
7. regression

A static PASS does not mean runtime VERIFIED.

## Character state

Track each character with a status that reflects evidence, not optimism. Suggested states:

- `draft` — being authored
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

## Definition of done

The character is not done because files exist.

It is done when the requested result exists at the strongest verification level available, with remaining untestable boundaries stated explicitly.
