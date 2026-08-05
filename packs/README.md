# Junk Bunch Packs

Behavior Pack and Resource Pack for Minecraft Bedrock Junk Bunch characters.

---

## Structure

```
JunkBunch_BP/  (Behavior Pack)
  manifest.json
  entities/          → Entity files for each character
  animation_controllers/  → Animation logic
  functions/         → Command functions (summon, ability, etc.)
  loot_tables/       → Drop tables if needed
  recipes/           → Crafting recipes for summon items

JunkBunch_RP/  (Resource Pack)
  manifest.json
  textures/
    entity/characters/     → Character textures
    items/                 → Summon item textures
  models/entity/     → Blockbench .geo.json models
  animations/        → Blockbench .animation.json animations
  entity/            → Entity client definitions
```

---

## How to Upload to Realm

### From Phone (Minecraft Mobile)

1. Download both `JunkBunch_BP` and `JunkBunch_RP` folders as `.zip` or individual files
2. Open Minecraft Mobile
3. Go to **Settings** → **Global Resources**
4. Tap **+** to add a pack
5. Navigate to the downloaded files
6. Select both BP and RP
7. Go to your Realm
8. In Realm settings, make sure both packs are activated
9. PS5 will auto-download when joining

### Folder Structure on Phone

After downloading, they should look like:
```
JunkBunch_BP/
  manifest.json
  entities/
  animation_controllers/
  functions/
  recipes/
  loot_tables/

JunkBunch_RP/
  manifest.json
  textures/
  models/
  animations/
  entity/
```

---

## Pack Order

When uploading multiple packs to a Realm, order matters:

1. **JunkBunch_BP** (behavior first—defines entities)
2. **JunkBunch_RP** (resource pack—applies textures/models)
3. Any other packs you use (vanilla tweaks, etc.)

Junk Bunch should be **at the top** of the stack so characters render correctly.

---

## Compatibility

- **Minecraft Version**: Bedrock Edition (regular, not preview)
- **Min Engine Version**: 1.20.0+
- **Platform**: PS5, PC, Mobile (tested on PS5)
- **Format Version**: 2 (manifests), 1.20.50 (entity JSON)

---

## Adding a New Character

When I create a new character, files are added to:

```
JunkBunch_BP/entities/[character_name].json
JunkBunch_BP/animation_controllers/[character_name].json
JunkBunch_BP/functions/characters/[character_name]/

JunkBunch_RP/textures/entity/characters/[character_name].png
JunkBunch_RP/models/entity/[character_name].geo.json
JunkBunch_RP/animations/[character_name].animation.json
```

Re-upload the updated packs to your Realm, and the new character is live.

---

## Testing Locally

Before uploading to Realm, you can test on PC:

1. Copy both `JunkBunch_BP` and `JunkBunch_RP` to:
   - Windows: `%APPDATA%\\.minecraft\\development_behavior_packs` and `development_resource_packs`
   - Mac/Linux: Follow Bedrock docs
2. Create a test world, enable the packs
3. Verify entity spawning, textures, animations
4. Once confirmed, upload to Realm for PS5 testing

---

## Troubleshooting

**Character doesn't spawn:**
- Check entity identifier spelling in entity file vs. function
- Ensure BP pack is loaded before RP pack
- Verify Realm has latest pack versions downloaded

**Textures missing (pink/purple blocks):**
- Resource pack didn't load
- Check texture path spelling in entity client definition
- Make sure RP is activated in Realm settings

**Animations don't play:**
- Animation controller file may have syntax errors
- Check animation identifiers match in entity file
- Verify geometry model name matches entity definition

**Summon item doesn't appear:**
- Check recipe in BP/recipes/
- If using creative, verify item definition exists
- Try /give command to debug: `/give @s junkbunch:summon_[name]`

---

## References

- [Minecraft Bedrock Entity Documentation](https://learn.microsoft.com/en-us/minecraft/creator/reference/content/entityreference/)
- [Blockbench (for models/animations)](https://blockbench.net/)
- [PS5 Realm Upload Process](https://help.minecraft.net/hc/en-us/articles/360058746271)
