# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Junk Bunch AI Adventure

### Mission

This project creates an original Minecraft Bedrock adventure series called **The Junk Bunch**.

The goal is to build a repeatable pipeline that turns a child's drawings into Minecraft characters in 1–2 hours, then use them for ongoing episodes.

Every decision should make future characters and episodes easier.

### Platform Constraints

- Minecraft **Bedrock Edition ONLY**
- Primary platform: PlayStation 5
- Distribution: Minecraft Realms
- Development on PC → upload to Realm → play on PS5

Never recommend unsupported platforms, mods, or Java-only tools.

Everything must work in the PC → Realm → PS5 workflow.

### Core Philosophy

Optimize for:

1. Reliability
2. Speed
3. Polish
4. Reusability
5. Player delight

Never prioritize cleverness over usability.

### Character Pipeline

1. Photograph artwork
2. Analyze drawing
3. Create Minecraft version
4. Build textures/models
5. Implement entity
6. Add animations
7. Define personality & behavior
8. Add interactions
9. Spawn in Realm
10. Ready for episodes

Automate every step over time.

### Character Standard

Each character must feel like it exists in the world and can be discovered or summoned.

Include:

- **Personality**: simple behavior type
- **Follow ability**: can follow player or others
- **Special move**: unique ability or action
- **Summon item**: item that spawns the character
- **Spawn methods**: spawn egg + survival item version
- **World origin**: 1–2 sentence environmental backstory

### Episode Pipeline

Characters exist to support episodes.

Everything should reduce episode production time.

### Engineering Standards

- Read before changing code
- Make minimal correct changes
- Don't invent Bedrock features
- Avoid unnecessary refactors
- Match existing style
- Verify compatibility

### Architecture

Prefer:

- Modular systems
- Data-driven design
- Reusable components
- Behavior + Resource Packs
- Script API

Avoid duplication and one-off logic.

### Automation First

If repeated more than twice, automate it.

Focus on reusable systems for:

- animations
- dialogue
- personalities
- interactions
- quests
- cutscenes
- assets

### Performance

Must run smoothly on PS5 via Realms.

Prefer event-driven systems over constant ticking.

### Success Criteria

- New character: ≤ 2 hours
- Update: ≤ 15 minutes
- Episode setup: ≤ 30 minutes

If exceeded, improve the workflow.

### Communication

Be direct.

If unsure:

- check code
- don't guess
- state uncertainty

Explain major changes.

### Definition of Done

- Works in Bedrock
- Compatible with Realm → PS5
- No broken existing features
- Docs updated if needed
- Improves or maintains production speed
