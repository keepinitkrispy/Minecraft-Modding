# Minecraft-Modding

An open-method effort to make Minecraft Bedrock creation feel like an AI creation tool: give the system art, an idea, or a plain-language description and get back a finished, testable `.mcaddon` with as little manual translation as possible.

The methodology is documented in [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md). Model-neutral agent rules live in [`AGENTS.md`](AGENTS.md).

## Product principle

**Service is convenience, not captivity.**

People who want to run or fork the process themselves should be able to inspect the methodology, schemas, validation rules, quality gates, failure modes, and learning system. People who want us to do the work for them can pay a small convenience/execution fee instead.

The economic target is tool-like pricing rather than consulting-style pricing: ordinary runs should ideally cost only a few dollars or less if the underlying economics allow it.

> The repository is public, but an explicit reuse license has not yet been selected. Do not describe the methodology as legally open-source/open-use until a license is added.

## North-star pipeline

`intent / art → structured spec → assets + behavior → validation → Bedrock runtime test → packaged .mcaddon → learned improvement`

The goal is not “files were generated.” The goal is a playable result verified at the strongest level available.

## Bedrock validation ladder

1. Structural/package check
2. Schema/static validation
3. Import test
4. Spawn/placement test
5. Behavior test
6. Visual test
7. Regression test

Never claim a higher level than was actually tested.

## Current build

The importable Junk Bunch add-on is `JunkBunch.mcaddon` at the repository root.

```bash
# validate source packs
python3 scripts/validate_packs.py

# validate, then build JunkBunch.mcaddon
python3 scripts/build_mcaddon.py
```

`build_mcaddon.py` refuses to package a pack that fails the validator.

The built archive should contain exactly:

```text
JunkBunch_BP/
JunkBunch_RP/
```

with no repo-root nesting or extra `packs/` prefix.

## Character workflow

A new character may begin with only a drawing/reference and intent. Extra fields such as personality, special ability, or summon item are useful when the creator has opinions, but they are not mandatory prerequisites for starting.

The system should infer reasonable defaults, surface only genuinely important creative choices, build the artifact, validate it, and then use Bedrock testing to decide what is actually learned.

See [`docs/WORKFLOW.md`](docs/WORKFLOW.md).

## Platform target

- Minecraft Bedrock Edition
- Android/mobile-first authoring and transfer
- Realms deployment
- PlayStation 5 play/testing
- Desktop tools are optional accelerators, not hidden hard dependencies

## Knowledge model

Project experience is split conceptually into:

- current state
- per-project state
- reusable verified Bedrock knowledge
- evidence/history

Reusable rules are promoted only after evidence supports them. Unknowns stay unknown; obsolete rules are marked superseded.

## Repository map

```text
AGENTS.md                  model-neutral agent rules
CLAUDE.md                  thin Claude-specific adapter
docs/METHODOLOGY.md        open methodology / product constitution
docs/WORKFLOW.md           character build/test workflow
docs/PS5_CONTROLS.md       PS5 interaction notes
packs/                     Bedrock behavior/resource packs
characters/                character state/data
scripts/                   validation/build automation
templates/                 reusable scaffolding
```

## Long-term direction

The end state should feel less like hiring a coder and more like using Meshy for Minecraft Bedrock:

1. provide art or intent
2. system retrieves relevant verified experience
3. system builds the content and mechanics
4. automated validation catches structural defects
5. Bedrock runtime/visual tests determine what actually works
6. successful patterns improve future runs
7. user receives an importable, understandable, editable result

The tool should get better because it has built and tested more things—not because users are forced into a proprietary black box.
