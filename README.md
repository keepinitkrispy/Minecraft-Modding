# Junk Bunch AI Adventure

Turn your child's drawings into playable Minecraft Bedrock characters in 1-2 hours, then build episodes and challenges around them.

---

## Quick Start

### For Creating Characters

1. **Prepare a character concept:**
   - Photo of your son's drawing
   - Character name (e.g., "Rusty", "Sparkle")
   - 3-5 personality traits (e.g., "sneaky, helpful, loyal")
   - Special ability in 1-2 sentences
   - Summon item (crafted, found, or creative)

2. **Send to Claude Code:**
   - Upload the image
   - Provide the details above
   - I'll create the full entity, textures, animations, and recipes

3. **Download & Test:**
   - Get the updated pack files
   - Download on your phone
   - Upload to Realm via Minecraft Mobile
   - PS5 auto-downloads when joining
   - Test with the summon item in-world

### For Uploading to Realm

See `/packs/README.md` for detailed upload instructions.

---

## Workflow Documentation

- **`/docs/WORKFLOW.md`** — How to create a character step-by-step
- **`/docs/PS5_CONTROLS.md`** — Button mapping and control scheme
- **`/CLAUDE.md`** — Project philosophy and engineering standards

---

## File Structure

```
Junk Bunch/
├── CLAUDE.md                 # Project guidance for Claude Code
├── README.md                 # This file
├── packs/
│   ├── JunkBunch_BP/         # Behavior Pack
│   │   ├── manifest.json
│   │   ├── entities/         # Character entity files
│   │   ├── animation_controllers/
│   │   ├── functions/
│   │   ├── recipes/
│   │   └── loot_tables/
│   │
│   ├── JunkBunch_RP/         # Resource Pack
│   │   ├── manifest.json
│   │   ├── textures/
│   │   │   ├── entity/characters/
│   │   │   └── items/
│   │   ├── models/entity/
│   │   └── animations/
│   │
│   └── README.md             # Pack upload & troubleshooting
│
├── characters/
│   ├── ROSTER.md             # Track all created characters
│   └── [character_name].json # Individual character data
│
└── docs/
    ├── WORKFLOW.md           # Character creation workflow
    ├── PS5_CONTROLS.md       # Control scheme & implementation
    └── (future: challenge docs, episode docs, etc.)
```

---

## Character Pipeline

Each character follows this process:

1. 📸 Photograph artwork
2. 🧠 Analyze drawing → concept
3. 🎨 Create textures faithful to drawing
4. 🤖 Build entity (behavior, animations, models)
5. 🎬 Add animations (idle, walk, run, special move)
6. 💡 Define personality & behaviors
7. 🔗 Add summon item & recipe
8. 🎮 Spawn into Realm
9. ✅ Ready for episodes/challenges

**Target time: ≤ 2 hours per character**

---

## Controls (PS5 Bedrock)

| Action | Button |
|--------|--------|
| Summon character | Hold **ZR** with summon item |
| Direct character | Hold **ZR**, look where to go |
| Special ability | Press **Y** (while spawned) |

Full details: `/docs/PS5_CONTROLS.md`

---

## Compatibility

- **Edition**: Minecraft Bedrock (PlayStation 5 primary)
- **Version**: 1.20.0+
- **Workflow**: PC development → phone download → Realm upload → PS5 play
- **Tools**: Blockbench (for modeling/animations), Realm with upload access

---

## Character Status Tracking

Each character in `/characters/ROSTER.md`:

- **draft** — Being designed
- **ready** — Tested in Realm
- **stable** — Ready for challenges
- **archived** — Retired

---

## Next Steps

1. Create the first character (send photo + name + traits + ability + item)
2. Download and test in Realm
3. Iterate on feedback
4. Once 3-5 characters are stable, start building challenges
5. Design episode narratives and arenas

---

## Support

- **How do I create a character?** → See `/docs/WORKFLOW.md`
- **How do controls work on PS5?** → See `/docs/PS5_CONTROLS.md`
- **How do I upload to my Realm?** → See `/packs/README.md`
- **Project philosophy?** → See `CLAUDE.md`

---

## Credits

- **Creative Director**: Your son's drawings & ideas
- **Manager/Producer**: You
- **Development Team**: Claude (all entity, texture, animation, and scripting work)
- **Platform**: Minecraft Bedrock Edition, PlayStation 5, Realm hosting
