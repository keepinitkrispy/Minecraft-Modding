# Junk Bunch Character Creation Workflow

## Overview

This is the pipeline for creating a new Junk Bunch character from concept to in-game.

**Timeline**: ~1-2 hours per character from image upload to ready-to-test.

---

## What You Provide

When creating a new character, send me:

1. **Photo of the drawing**
   - Upload as image file from your phone
   - Shows your son's character design
   - I'll analyze the style, colors, proportions, and personality from the artwork

2. **Character name**
   - What the character is called
   - Example: "Rusty", "Sparkle", "Chomper"

3. **Personality traits** (3-5 words)
   - How the character behaves
   - Example: "sneaky, mischievous, loyal"
   - Example: "happy, clumsy, helpful"
   - I use this to determine animations and idle behaviors

4. **Special ability** (1-2 sentences)
   - What makes this character unique
   - Example: "Can climb walls and crawl on ceilings"
   - Example: "Glows brightly in the dark and lights up dark areas"
   - I turn this into an animation and mechanics

5. **Summon item** (1-2 words)
   - What item summons/directs this character
   - Example: "Wooden sword", "Pumpkin", "Music disc"
   - Can be crafted, found, or taken from creative mode
   - I'll design the recipe and textures

---

## What I Create & Deliver

For each character, I generate:

### Model authoring (Blockbench MCP)
- Models, textures, and animations are authored in Blockbench, which Claude can
  drive directly via the Blockbench MCP plugin. See `docs/BLOCKBENCH_MCP.md` for
  setup. When Blockbench isn't running (e.g. a cloud session), the offline
  fallback is `scripts/build_leafy_assets.py`. Either way the output must pass
  `scripts/validate_packs.py` before it ships.

### Entity Files
- Behavior component (personality, follow system, ability trigger)
- Geometry model (based on your son's drawing style)
- Animation controller (idle, walk, run, special ability, interact)

### Textures & Models
- Character texture (faithful to the drawing)
- Summon item texture
- Spawn egg variant

### Item & Crafting
- Summon item definition with PS5-compatible controls
- Crafting recipe (or creative/survival spawn method)
- Loot table entries if applicable

### Documentation
- Animation reference (what triggers what)
- Behavior file with personality implementation
- Integration notes (where files go in the packs)

### Character Data File
- Stored at `/characters/[character_name].json`
- Contains all properties for tracking and future updates
- Used by scripts if challenge system is added later

---

## PS5 Control System

**Summoning the character (L2):**
- Have the summon item in your hand (main or off-hand)
- Hold **L2** (left trigger)
- Character appears at your crosshair location
- Release L2 when done

**Follow / bond (L2 on the character):**
- With the summon item in hand, hold **L2** on the character to bond with it
- Once bonded it follows you like a tamed pet and stays loaded (persistent)

**Special ability (passive):**
- Abilities are automatic — no button press
- R1/L1 are intentionally unused because they scroll the hotbar on PS5

**Mining (R2):**
- Normal Minecraft mining works unchanged; summoning only fires when the
  summon item is in hand

---

## Workflow Steps

1. **You send**: Photo + Name + Traits + Ability + Summon Item
2. **I analyze** the photo and design the entity
3. **I create**:
   - Entity JSON files
   - Texture from drawing inspiration
   - Animations (idle, walk, run, ability)
   - Summon item + recipe
   - Character data file
4. **You receive**: All pack files ready to upload
5. **You download** on your phone, upload to Realm via Minecraft mobile
6. **PS5 joins** Realm, auto-downloads packs
7. **Test in world**: Summon item exists, character spawns, can direct and use ability
8. **If good**: Mark character as "ready"; if issues, describe and I iterate

---

## File Structure

After I create a character, files go here:

```
packs/JunkBunch_BP/
  entities/[character_name].json
  animation_controllers/[character_name].json
  functions/characters/[character_name]/

packs/JunkBunch_RP/
  textures/entity/characters/[character_name].png
  textures/items/summon_[character_name].png
  models/entity/[character_name].geo.json
  animations/[character_name].animation.json

characters/
  [character_name].json  (data file for tracking)
```

---

## Example: Creating "Rusty"

**You send:**
- Photo of a red-brown robot-like creature drawing
- Name: "Rusty"
- Traits: "loyal, curious, clumsy"
- Ability: "Can emit sparks when jumping"
- Summon Item: "Wrench"

**I create:**
- Entity that follows player (loyal)
- Walks with a stumbling animation (clumsy)
- Spark particle effect on jump (ability)
- Wrench item with crafting recipe
- All textures matching the robot aesthetic

**You get:**
- Updated packs ready to upload
- Rusty spawns with wrench in survival
- Summon with L2; bond with L2 to have him follow
- Passive ability always on

---

## Iteration

If something needs tweaking:
- "Make Rusty faster"
- "Add a different color variant"
- "Change the ability to glow instead"

Just tell me and I update and redeliver the files. No re-upload needed if it's just an entity file change; you can test locally first.

---

## Character Status Tracking

Each character lives in `/characters/[name].json` with a status field:
- `draft` — being designed, not finalized
- `ready` — tested and working in Realm
- `stable` — multiple tests passed, ready for challenges
- `archived` — old version, replaced by new one

This helps track what's ready for the reality show challenges later.
