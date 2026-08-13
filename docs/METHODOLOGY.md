# Open Minecraft Modding Methodology

## Mission

Build the Minecraft Bedrock equivalent of a modern AI creation tool: a person should be able to provide an idea, drawing, reference image, or plain-language description and receive a finished, testable Bedrock add-on with as little manual translation as possible.

The methodology is intentionally open. The service may charge for convenience, execution, hosting, support, custom work, or quality assurance, but the method itself should not depend on hidden prompts, secret instructions, undocumented tricks, or vendor lock-in.

**Service is convenience, not captivity.**

If somebody wants the finished result without learning the pipeline, we can do the work for them cheaply. If they want to build it themselves, they should be able to use the same documented methodology, validation rules, state model, and quality gates.

## Product Philosophy

We are not trying to maximize extraction from users. We are trying to make Minecraft Bedrock mod creation dramatically easier.

The preferred economic model is low-friction and low-cost:

- a generated character or small add-on should be inexpensive enough to feel like a tool invocation, not a consulting engagement
- where practical, a run should cost only a few dollars or less
- very small character-generation jobs may reasonably be priced around the cost of a trivial digital purchase rather than a premium creative service
- users should not be forced to pay merely to understand how the system works
- people with time and technical interest should be able to self-run the open methodology
- people who value convenience should be able to pay us to execute the same process for them

Revenue should come from useful execution at scale, optional convenience, support, infrastructure, and quality—not from withholding the method.

## North Star Pipeline

**Intent / art → structured specification → assets + behavior → validation → Bedrock runtime test → packaged `.mcaddon` → learned improvement.**

The goal is not “generate files.” The goal is a playable result that survives the strongest verification available.

## Core Principles

### 1. External state, not model memory

Long-lived project state and learned implementation knowledge live outside any one model or chat. Models are workers over the state, not the source of truth.

### 2. Evidence before promotion

A plausible implementation is not automatically a lesson. A reusable rule is promoted only when the evidence supports it.

Use explicit labels:

- **VERIFIED** — established enough to reuse within its stated scope
- **UNKNOWN** — not yet established
- **INFERRED** — supported by evidence but not directly observed
- **HYPOTHESIS** — proposed explanation to test
- **DISPROVEN** — tested and found wrong
- **SUPERSEDED** — replaced by newer verified knowledge

### 3. Separate current state, projects, knowledge, and evidence

Do not keep one giant memory dump. Use four logical layers:

- **Current state** — what is true now and what is open
- **Projects** — artifact-specific goals, versions, defects, and next gates
- **Knowledge** — reusable verified Bedrock implementation rules
- **Evidence/history** — observations, test results, failed attempts, causes, fixes, and superseded states

Load only the pieces relevant to the current task.

### 4. Learn through execution

Every serious add-on is also a controlled learning source. The learning path is:

**attempt → test → observation → cause/fix → retest → reusable rule → future application**

A failed attempt with no established cause remains an observation, not a universal rule.

### 5. Model independence

The pipeline must not require one specific AI vendor. Claude, ChatGPT, Codex, Gemini, local models, or future agents may perform steps in the workflow.

The durable asset is the methodology, schemas, test suite, state, examples, and verified implementation knowledge—not a particular prompt or model.

### 6. Validation is a ladder

Use the strongest applicable gate and report exactly what was tested:

1. **Structural/package check** — paths, required files, JSON parse, manifest/dependencies
2. **Schema/static validation** — Bedrock definitions are valid for the claimed version
3. **Import test** — Minecraft Bedrock accepts and loads the pack
4. **Spawn/placement test** — entity/block/structure/biome can actually appear
5. **Behavior test** — mechanics, AI, interactions, and scripts behave correctly
6. **Visual test** — geometry, pivots, textures, materials, and animations look correct
7. **Regression test** — previous working behavior still works after the change

Never claim a higher verification level than was actually tested.

### 7. Runtime truth outranks generated confidence

A model saying “this should work” is not evidence. Clean JSON is not evidence of visual quality. A successful import is not evidence that worldgen works. A spawn is not evidence that AI feels good.

Use observed Bedrock behavior as the final authority for Bedrock runtime claims.

### 8. Small, reusable building blocks

Prefer reusable templates and generators for:

- manifests and pack scaffolding
- entity behavior families
- tame/follow/sit/stay/attack patterns
- special-move interfaces
- geometry skeletons and rig conventions
- texture/UV conventions
- animation controller patterns
- items and recipes
- particles and sounds
- quest/dialogue building blocks
- worldgen/structure templates
- validation and packaging

Avoid one-off code when the pattern is likely to recur.

### 9. Mobile and console reality matters

The methodology must account for actual user constraints, especially Android → Realm → PS5 Bedrock workflows.

Do not quietly design around desktop-only steps if the target user is mobile-first.

### 10. Open methodology means reproducibility

A useful public method should include enough information for another competent person or agent to reproduce the pipeline:

- schemas and data contracts
- directory conventions
- validation rules
- test gates
- state transitions
- example artifacts
- known failure modes
- promotion/supersession rules for learned knowledge
- quality criteria

“Use our AI and trust it” is not documentation.

## Persistent-State Architecture

The working state system is conceptually split into:

### Current State

Small, frequently updated, cross-project truth: active goals, blockers, waiting conditions, immediate next actions.

### Project State

Per-add-on facts: current artifact/version, desired result, verified successes, defects, untested claims, and next test.

### Domain Knowledge

Reusable Bedrock knowledge that has passed the evidence threshold for reuse.

### Evidence & History

Detailed test observations, failed attempts, suspected causes, fixes, retest outcomes, and superseded states.

This keeps high-value context retrievable without stuffing every historical detail into every model call.

## Knowledge Promotion Protocol

When a test produces a durable lesson:

1. Record the exact observation.
2. Separate observation from suspected cause.
3. Establish the cause/fix through comparison or successful retest where possible.
4. Promote the smallest reusable rule with a clear verification scope.
5. Mark conflicting older rules **SUPERSEDED** instead of leaving both active.
6. Apply the new rule automatically to future relevant builds.

This is how experience compounds across Junk Bunch, Dead Air, Rich & Shorty, and future projects.

## Character / Companion Minimum Product Contract

Unless the character concept intentionally calls for something different, a polished companion should support a coherent subset of:

- faithful recognizable silhouette
- correct texture/UV mapping
- idle and locomotion animation
- tame/bond interaction
- follow
- sit/stay
- attack or defensive behavior where appropriate
- one distinctive special move
- spawn egg or equivalent creative access
- survival-accessible summon/tame item where appropriate
- clear player feedback for important states
- no regressions to existing pack behavior

The concept should drive the exact mechanics; the contract exists to prevent hollow “character-shaped files.”

## Quality Standard

The target is distributable-quality work, not merely valid files.

Evaluate at least:

- silhouette and fidelity to source art
- proportion and readability at Minecraft scale
- texture quality and UV correctness
- animation quality and pivot placement
- mechanic coherence
- player feedback and discoverability
- packaging/import reliability
- performance on Bedrock/Realm/PS5 constraints
- regression safety
- delight: does this feel like a character or experience somebody would actually want to play with?

## Service Layer

An optional service can sit on top of this open method.

A user may choose:

**Self-run:** use the public workflow, tooling, examples, and validation rules.

**Assisted:** use the same workflow with AI guidance and partial automation.

**Done-for-you:** provide art/intent and pay a small amount for the system or operator to execute the pipeline, validate it, package it, and deliver the result.

These are different convenience levels over the same methodology, not different classes of access to hidden knowledge.

## What We Refuse to Optimize For

Do not optimize for:

- lock-in
- obscurity
- prompt secrecy as a moat
- inflated per-run pricing
- making users dependent on a human operator for routine builds
- hiding failure modes
- claiming success before runtime evidence exists
- preserving bad architecture because it creates billable work

## Long-Term Direction

The end state should feel like a creation tool rather than a coding session:

1. user gives art or intent
2. system asks only for genuinely missing creative choices
3. system retrieves relevant learned Bedrock knowledge
4. system builds the asset and gameplay package
5. validators catch structural/schema defects automatically
6. Bedrock test results feed back into project state and reusable knowledge
7. successful patterns improve the next run
8. user receives an importable, understandable, editable result

The system should become better because it has built and tested more things—not merely because a larger model was selected.
