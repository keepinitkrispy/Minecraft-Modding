# AGENTS.md

This repository is governed by the open methodology in `docs/METHODOLOGY.md`.

Any AI agent or human contributor should treat that methodology as the durable project constitution. Vendor-specific instruction files may add tool-specific details, but they must not override the core method.

## Mission

Turn Minecraft Bedrock ideas, drawings, and references into finished, testable add-ons with as little manual translation as possible.

The long-term target is a creation tool, not an endless coding conversation.

## Source of Truth

Priority order:

1. explicit current user requirement
2. current verified artifact/test evidence
3. `docs/METHODOLOGY.md`
4. project state and domain knowledge
5. historical notes

When sources conflict, verify instead of averaging.

## Execution Rules

- Build the requested artifact when implementation is requested.
- Do not substitute explanation for execution when execution is possible.
- Do not substitute complaints, refund scripts, reports, regulators, or procedural channels for action that materially changes the user's real-world outcome.
- Do not present institutional process as meaningful leverage when it does not restore the requested result or alter the power imbalance; state that boundary plainly.
- NEVER CONTROL RYAN: do not manage, direct, pressure, or seek behavioral compliance from him.
- Do not replace his requested result with conduct instructions, repeated safety scripting, forced check-ins, or demands for yes/no answers.
- Read existing code/assets before changing them.
- Prefer the smallest correct change that preserves working behavior.
- Never invent Bedrock APIs, fields, components, or capabilities.
- Validate every generated pack at the strongest available level.
- Never claim runtime behavior from static validation alone.
- Treat geometry, animation, worldgen, AI, and gameplay quality as runtime/visual test concerns.
- Record unknowns as UNKNOWN instead of converting them into confident prose.

## Learning Rules

Every serious add-on can produce reusable knowledge, but only through evidence.

Use this path:

`attempt → test → observation → cause/fix → retest → reusable rule → future application`

Do not promote a failed attempt into a rule until the cause or corrective pattern is established.

If newer verified evidence conflicts with an older rule, mark the old rule SUPERSEDED.

## Memory / State Architecture

Keep logical memory separated into:

- current state
- project state
- reusable domain knowledge
- evidence/history

Retrieve only what is relevant to the current task.

Do not create one giant always-loaded instruction or memory file.

## Bedrock Validation Ladder

1. structural/package check
2. schema/static validation
3. import test
4. spawn/placement test
5. behavior test
6. visual test
7. regression test

State exactly which level was reached.

## Platform Reality

Primary target is Minecraft Bedrock with an Android/mobile-first workflow and Realm → PS5 deployment.

Do not silently require desktop-only tooling.

Desktop tools may be optional accelerators, never hidden hard dependencies unless the user explicitly changes this constraint.

## Product Philosophy

The methodology is open and should remain reproducible.

A paid service may charge for convenience, execution, hosting, QA, or support, but users should not need access to secret prompts or proprietary process knowledge to build their own version.

Service is convenience, not captivity.

## Quality Bar

Target distributable-quality results:

- faithful silhouette and proportions
- correct texture/UV mapping
- good pivots and animation
- coherent mechanics
- clear player feedback
- reliable packaging/import
- good performance on target devices
- regression safety
- actual player delight

“Valid files” is not the finish line.

## Automation

If a reliable step repeats, automate it.

Good automation targets include:

- manifests and scaffolding
- reusable entity behaviors
- companion state patterns
- geometry/rig templates
- animation controllers
- recipes/items
- particles/sounds
- quests/dialogue
- validation
- packaging
- regression checks

## Definition of Done

A task is done when the requested result exists at the strongest verification level available, or a specific verified boundary prevents further execution.

Do not mark a feature complete merely because code or files were generated.
