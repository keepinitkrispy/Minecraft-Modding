# Course Craft — Texture Slots

You make the skins; the tools do the wiring. Every texture is one PNG named after its slot.

## Rules
- PNG, square: **16, 32, 64 or 128 px** (keep them all the same size for the cleanest look).
- Transparency allowed (needed for `cc_shard`; other blocks render opaque).
- File name = slot name. Case doesn't matter. Unknown names are skipped and reported.

## Easiest path
1. Start from the kit: `texture_kit/CourseCraft_texture_kit.zip` (every slot, correctly named) and `texture_kit/TEXTURE_GUIDE.png` (labelled preview).
2. Repaint any files you want. You can leave the others alone.
3. Put the PNGs, or a zip of them, into `projects/course_craft/textures_in/`.
4. Run:
   ```
   python3 tools/import_textures.py            # or: python3 tools/import_textures.py path/to/skins.zip
   python3 tools/build.py                      # -> CourseCraft.mcaddon
   ```
Rejected files (wrong size or format) are listed, and the slot keeps its old art.

## Slots
| File | What it is |
|---|---|
| `cc_start_pad_side.png` | Start Pad sides |
| `cc_start_pad_top.png` | Start Pad top: 'begin here' marker |
| `cc_goal_side.png` | Goal Block sides |
| `cc_goal_top.png` | Goal Block top: finish marker |
| `cc_checkpoint.png` | Checkpoint (all faces) |
| `cc_spring_side.png` | Spring Pad sides |
| `cc_spring_top.png` | Spring Pad top: bounce surface |
| `cc_dash_side.png` | Dash Pad sides |
| `cc_dash_top.png` | Dash Pad top: speed arrows |
| `cc_spike_side.png` | Spike Block sides |
| `cc_spike_top.png` | Spike Block top: hazard |
| `cc_shard.png` | Shard collectible (transparent background allowed) |
| `cc_bright_brick.png` | Bright Brick (all faces) |
| `cc_toon_grass_side.png` | Toon Grass sides |
| `cc_toon_grass_top.png` | Toon Grass top |
| `cc_toon_dirt.png` | Toon Grass bottom |
| `cc_cloud.png` | Cloud Block (all faces) |
| `cc_maker_wand.png` | Maker Wand inventory icon (item) |

Slots are defined in `tools/spec.py`. To add a block, add it there and rerun `tools/generate.py`.
