# PS5 Bedrock Junk Bunch Controls

All Junk Bunch characters use this standardized control scheme on PS5 Bedrock Edition.

---

## Button Mapping

| Action | Button | Behavior |
|--------|--------|----------|
| **Summon character** | Hold **ZR** with summon item | Spawns character at crosshair |
| **Direct character** | Hold **ZR** while spawned | Character pathfinds to your crosshair |
| **Release** | Release **ZR** | Character stops following directions, remains spawned |
| **Special ability** | Press **Y** (while spawned) | Triggers character's unique ability |
| **Despawn** (optional) | Crouch + interact with character | Character returns to item (works if ability needs it) |

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

### On-Item Use
Each summon item is configured to:
- Trigger on **ZR hold** (not just press)
- Spawn the entity at the player's crosshair + offset
- Check if entity already spawned (prevent duplicates)

### Pathfinding
Characters use Bedrock's native pathfinding:
- When you hold ZR and look elsewhere, the entity recalculates path every tick
- Avoids obstacles automatically
- If path is blocked for 5+ seconds, teleport (optional, prevents soft-locks)

### Ability System
Each character has a behavior event `trigger_ability` that fires when:
- Player presses Y
- Character is nearby
- Character is not on cooldown (usually no cooldown)

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

- [ ] ZR spawns the character at crosshair
- [ ] ZR hold moves character to crosshair aim point
- [ ] Character navigates around obstacles
- [ ] Y triggers the special ability
- [ ] No controller lag/delay (should be <1 frame)
- [ ] Works in Realm (not just single player)
- [ ] Works on PS5 specifically (not just Bedrock PC)

---

## Future: Multiplayer & Challenges

When challenges are added:

- Multiple players can summon different characters
- Challenge arena might override controls (e.g., auto-direct to arena)
- Challenge system will document any control changes per challenge
- Base summon/ability always works as documented here
