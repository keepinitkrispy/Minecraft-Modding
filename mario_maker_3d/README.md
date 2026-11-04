# Mario Maker 3D — Bedrock / PS5 Course Builder (v0.1 prototype)

A first playable implementation layered on our Junk Bunch Bedrock workflow. Target: Minecraft Bedrock Android, with Realm → PS5 after on-device validation. This is not a Java mod or a PS5 jailbreak.

## Includes
- Build mode (Creative) and Play mode (Adventure), with course object creation allowed only in Build.
- Set Corner A and Corner B to define MAIN and SUB course boundaries (96×96 maximum per area).
- Editor placement: start pad, writable vanilla sign, two-way pipe pairs, three green star markers, coins, hearts, checkpoints, goal, enemies, boss arena, Yoshi, platform, tower, arch.
- Real two-way sub-area pipes: two bounded regions and independent exit coordinates, persistent pipe IDs and links. No fake teleport scene.
- Mario 64–style eight-segment power meter, hit counter, five lives, invulnerability period, checkpoint respawn. 100 coins grants one life.
- First-person, Minecraft third-person and five overhead/diagonal camera options.
- Yoshi: modeled, texture-atlased rideable creature using Bedrock ground controls.
- Grass, snow, desert, castle texture themes with original beveled 64×64 texture art.
- First course is a tutorial: start pad → star 1 → checkpoint → pipe to SUB → star 2 → Yoshi → second pipe to MAIN → star 3 → enemy and boss → goal.

## Load and play
1. Open MarioMaker3D.mcaddon on Android with Minecraft.
2. Activate both packs in a NEW TEST WORLD; enable cheats for script events.
3. Enter the world. The script attempts to give you the Course Editor Wand.
4. Use the wand, tap the cyan start pad, or enter /scriptevent m3d:menu.
5. Choose Create Tutorial Course 1 in a blank course. This creates a separate MAIN and SUB area above your current location.
6. Switch to PLAY, crouch at or interact with a pipe to enter, collect all three stars, defeat the boss, reach the goal.
7. For custom courses: Build → set A/B bounds for MAIN and SUB → add two pipes to pair them → place objects → Play.

Avoid use in a valuable existing world: tutorial creation modifies terrain above the player.

## Source and state
- Build script: python3 generate_pack.py (Pillow required).
- Script: bp/scripts/main.js; Yoshi entity under bp/entities and rp/entity.
- Archive/JSON/JS syntax static checks passed on 2026-11-04; this is not proof of in-game functioning.
- Android 17 ADB cannot write directly to Minecraft private app folders; archive copied to Android Downloads pending import verification.
- World dynamic property stores one course globally; multiplayer authoring is not yet synchronized.
- The HUD is the action bar, not a textured radial overlay. Yoshi lacks a tongue attack.
- Course objects and enemies are authored through editor actions, not vanilla crafting-table recipes.
