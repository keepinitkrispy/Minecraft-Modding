# PS5 Bedrock — Junk Bunch Controls

Every Junk Bunch character uses the **same one-button scheme** on a PS5 controller.
It never fights with mining, placing, or the hotbar.

## Button Mapping

| Action | Button | Behavior |
|--------|--------|----------|
| **Summon** | Aim at the ground, hold **L2** with the summon item | Places the character where you're looking |
| **Bond so it follows** | Hold **L2** on the character while holding its summon item | Bonds it; it then follows you like a tamed pet and stays loaded |
| **Special ability** | *automatic* | Passive — always on, no button needed |
| **Mine / place** | **R2 / L2 on blocks** | Unchanged; summoning only fires when the summon item is in hand |

**Why one button, and not R1/L1:** R1 and L1 scroll the hotbar on PS5, so binding
an action to them would fight normal play. L2 is the standard "use item" trigger
and works from the main hand **or** the off-hand, so you can keep a tool in your
main hand and the summon item in your off-hand. Each character's special ability is
**passive** (always on), so it never needs a button.

## Per-character notes

### Leafy
- **Summon item:** Leafy's Rake (craft: 3 iron nuggets on top, 2 sticks down the middle).
- **Summon:** hold the rake, aim at the ground, hold **L2** — Leafy appears.
- **Follow:** hold **L2** on Leafy while holding the rake to bond; he then follows you.
- **Passive ability — Slow Float:** Leafy drifts gently and never takes fall damage,
  so he can follow you off any ledge and float down safely.
- **Size:** about half a player's height (~0.9 blocks) — a small companion.

## Testing checklist

- [ ] Rake shows its icon in the inventory/hotbar
- [ ] Holding the rake + **L2** on the ground spawns Leafy
- [ ] Leafy is visible with his leaf body, face, arms, legs, and stem
- [ ] The auto-generated spawn egg (Creative) also spawns a visible Leafy
- [ ] Holding **L2** on Leafy with the rake bonds him and he follows
- [ ] Leafy takes no fall damage when following you off a drop
- [ ] Works in a Realm on PS5, not just single-player PC
