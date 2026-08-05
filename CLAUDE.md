# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Junk Bunch AI Adventure

### Mission

This project creates an original Minecraft Bedrock adventure series called **The Junk Bunch**.

The goal is not to build a tech demo.

The goal is to build a repeatable production pipeline that allows a child's drawings to become polished, living Minecraft characters in approximately 1-2 hours, then use those characters to create ongoing episodes and adventures.

Every decision should make the next character and the next episode easier to produce.

### Platform Constraints

- Minecraft **Bedrock Edition ONLY**
- Primary platform: PlayStation 5
- Distribution: Minecraft Realms
- Development occurs on PC.
- Finished Behavior Packs and Resource Packs are uploaded to the Realm and played on PS5.

Never recommend:

- Java Edition
- Forge
- Fabric
- NeoForge
- Spigot
- Bukkit
- Mixins
- Java-only commands
- Bedrock Dedicated Server as a requirement
- PS5 mods or unsupported hacks

Everything must function through the PC → Realm → PS5 workflow.

### Core Philosophy

Optimize for:

1. Reliability
2. Production Speed
3. Polish
4. Reusability
5. Player Delight

Never optimize for cleverness over usability.

### Character Pipeline

Each Junk Bunch character follows a consistent workflow:

1. Photograph artwork.
2. Analyze the drawing.
3. Generate a polished Minecraft version faithful to the concept.
4. Create textures, models, and assets.
5. Build the Bedrock entity.
6. Add animations.
7. Define personality, dialogue, and behaviors.
8. Add interactions with other characters.
9. Spawn into the Realm.
10. Ready for filming.

Every stage should become more automated over time.

### Episode Pipeline

Characters are not the final product.

Episodes are.

Every tool, script, and system should make future episode production faster and easier.

If a feature doesn't help produce better episodes, reconsider it.

### Engineering Standards

- Read existing code before changing it.
- Understand the architecture first.
- Make the smallest correct change.
- Never invent APIs or Bedrock features.
- Verify compatibility before implementing.
- Never claim something is tested unless it has been tested.
- Avoid unnecessary refactors.
- Match the existing project style.

### Architecture

Favor:

- Modular systems
- Data-driven configuration
- Reusable components
- Behavior Packs
- Resource Packs
- Bedrock Script API
- Clear folder organization

Avoid duplicated logic and one-off solutions.

### Automation First

If a task will be repeated more than twice, automate it.

Create reusable systems for:

- animations
- dialogue
- personalities
- interactions
- quests
- cutscenes
- camera tools
- asset generation

The objective is to reduce production time with every new character.

### Performance

Optimize for stable performance on PS5 through Realms.

Prefer event-driven systems over constantly running loops.

Avoid unnecessary ticking entities and expensive scripts.

### Success Criteria

Target production times:

- New character: ≤ 2 hours
- Character update: ≤ 15 minutes
- Episode setup: ≤ 30 minutes

Whenever these goals are exceeded, recommend workflow improvements.

### Communication

Be direct and honest.

If uncertain:

- Inspect the code.
- Read the documentation.
- State what is unknown.
- Do not guess.

Explain the reasoning behind significant changes.

### Definition of Done

Work is complete only when:

- The feature works in Bedrock.
- It remains compatible with the Realm → PS5 workflow.
- Existing functionality is preserved.
- Documentation is updated if architecture changes.
- The solution improves or maintains the speed of producing future Junk Bunch characters and episodes.
