# PS5 Bedrock Junk Bunch Controls

All Junk Bunch characters use this standardized control scheme on PS5 Bedrock Edition.

---

## Button Mapping

| Action | Button | Behavior |
|--------|--------|----------|
| **Summon character** | Hold **L2** with summon item in hand or off-hand | Spawns character at your crosshair location |
| **Direct character** | Hold **R1** (after spawned) | Character pathfinds/walks to where you're looking (crosshair) |
| **Special ability** | Press **L1** (while character spawned) | Triggers character's unique ability (particles, effects, etc.) |
| **Despawn** (optional) | Release **L2** or walk away | Character stays spawned; can be re-summoned |
| **Switch to mining** | Press **R2** (mining unchanged) | Normal Minecraft mining works normally with character spawned |

---

## Standard Behaviors

### Summoning
- Hold the summon item in your hand
- Press and hold **ZR**
- Character appears at your crosshair location (slightly offset from you, in the direction you're looking)
- Character is now active in the world

### Directing
- Keep holding **ZR** while looking around
- Your crosshair shows where the character will go
- Character walks (or teleports, depending on distance) to that spot
- Release **ZR** when done directing

### Special Ability
- While character is spawned and you're within ~10 blocks
- Press **Y**
- Character performs its ability (spark emission, climb, glow, etc.)
- No cooldown by default; can spam if desired

### Despawn (Optional)
- Some characters may need to return to item form (for challenges, storage, etc.)
- Approach the character
- Crouch + press **ZR** on them
- Character returns to item
- This is not required for basic gameplay—characters can stay spawned

---

## Why This Control Scheme

**ZR for summon/direct:**
- ZR is the standard "use" button on Bedrock PS5
- Holding it is intuitive (like aiming)
- Works with any directional control method

**Y for ability:**
- Y is easy to reach while holding ZR (right hand thumb)
- Distinctive and doesn't conflict with movement
- Fits the "special action" concept

**No mouse/keyboard:**
- Everything works with controller only
- PS5 players expect button mapping, not M+KB emulation
- Crosshair aiming is native to Bedrock

---

## Implementation Details

### Summon (L2 Hold)
Each summon item is configured to:
- Trigger on **L2 hold** (not just press)
- Works from main hand OR off-hand
- Spawns the entity at the player's crosshair location
- Only one instance of each character can be active at a time

### Direct/Command (R1 Hold)
Characters use Bedrock's native pathfinding:
- When you hold **R1**, the entity pathfinds to where you're looking (crosshair)
- Recalculates path every tick
- Avoids obstacles automatically
- Release R1 to stop commanding (character stays in place)

### Special Ability (L1 Press)
Each character has a behavior event `trigger_ability` that fires when:
- Player presses **L1**
- Character is nearby (within ~16 blocks)
- Character is not on cooldown (default: no cooldown, can spam)

---

## Edge Cases

**Character falls off world:**
- If character despawns via void, it returns to item automatically
- If stuck in terrain, character teleports back to player

**Multiple summoned characters:**
- Only one instance of each character can be active at a time
- Summoning again despawns the previous one and spawns at your new location
- (Later: challenges can change this to allow multiple)

**Abilities with cooldown:**
- Some abilities have 10-30 second cooldowns (indicated in character description)
- Y press while on cooldown plays "fail" sound/animation
- Cooldown resets when character despawns and resummoned

---

## Testing Checklist

For each character, verify:

- [ ] L2 hold spawns character at crosshair
- [ ] L2 works from main hand and off-hand
- [ ] R1 hold moves character to where you're looking
- [ ] R1 pathfinding avoids obstacles
- [ ] L1 press triggers special ability
- [ ] R2 mining still works normally (no conflicts)
- [ ] No controller lag/delay (<1 frame response)
- [ ] Works in Realm (not just single player)
- [ ] Works on PS5 controller specifically

---

## Future: Multiplayer & Challenges

When challenges are added:

- Multiple players can summon different characters
- Challenge arena might override controls (e.g., auto-direct to arena)
- Challenge system will document any control changes per challenge
- Base summon/ability always works as documented here
