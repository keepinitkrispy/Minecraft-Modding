# Rich & Shorty — Infinite Liability

A Minecraft Bedrock parody adventure built around a repeatable multiverse resource loop.

## Non-negotiable release gates

- No generic box-person placeholders. Cast members use authored multi-cube voxel silhouettes, sculpted heads/faces, identity-specific details, and articulated upper/lower limbs.
- The player does not test a release candidate until static validation, archive validation, image integrity checks, JavaScript syntax checking, and Mojang Creator Tools validation pass.
- Custom dimensions are not used in the stable/Realm build while the official Custom Dimension API remains experimental. Stable builds use authored pocket-realities at remote coordinates behind the portal remote.
- Re-importable packs keep deterministic UUIDs and bump semantic versions for releases.

## v0.1 vertical slice

**Core loop:** Portal Remote → harvest Glorp/Fizzium/Chronodust/Scrap → Reality Fabricator rolls a guaranteed-new random recipe → machine consumes resources → guaranteed-not-the-same world tool → use tools to alter traversal/world state → side quests reward Citadel Tokens → enter Citadel-ish → multi-phase Evil Shorty boss.

### Cast in v0.1

Rich, Shorty, Evil Shorty, Bess, Gerry, Sundae, Bird Dude, Scronchy, Mr. Needs-It, Professor Poop.

### World-manipulation tool pool

Gravity Spanner, Phase Pick, Freeze Ray, Time-Skip Watch, Scaffold Printer, Matter-Swap Glove, Pocket Black Hole, Chaos Bonker.

### Side quests

Mr. Needs-It (Scrap), Bird Dude (Chronodust), Sundae (Glorp + Fizzium), Gerry (mixed-resource joke quest). Three Citadel Tokens unlock Citadel-ish.

## Build

```bash
python -m pip install pillow
python rich_shorty/build.py
```

Output: `rich_shorty/dist/Rich_and_Shorty_v0.1.0.mcaddon`
