# Blockbench MCP — model authoring for the pipeline

The character pipeline's "build model + texture + animation" step (steps 4–6) can be
driven directly in [Blockbench](https://blockbench.net/) by Claude through the
[blockbench-mcp-plugin](https://github.com/jasonjgardner/blockbench-mcp-plugin).
Blockbench is a real Bedrock modeling tool, so models authored there export as
engine-correct `.geo.json`, `.png`, and `.animation.json` — this removes the class
of bug where a hand-written skin doesn't line up with the geometry's UVs.

## One-time setup

1. Install the plugin in **desktop** Blockbench: `File > Plugins > Load Plugin from URL`,
   paste:
   ```
   https://jasonjgardner.github.io/blockbench-mcp-plugin/mcp.js
   ```
2. In `Blockbench > Settings > General`, confirm the MCP server:
   - **Port:** `3000`
   - **Endpoint:** `/bb-mcp`
   - **Transport:** HTTP
3. Register the running Blockbench server with Claude Code (from the repo root):
   ```bash
   claude mcp add --transport http blockbench http://localhost:3000/bb-mcp
   ```
   VS Code users can instead use the checked-in `.vscode/mcp.json` in this repo.

Blockbench must be **open with a project loaded** for the tools to respond — the MCP
server drives the live app.

## How it changes the workflow

Old (hand-authored) step → new (Blockbench MCP) step:

| Pipeline step | Before | With Blockbench MCP |
|---|---|---|
| 4. Model/texture | `scripts/build_leafy_assets.py` paints boxes + UVs by hand | Claude builds the cube model and paints the texture live in Blockbench, sees it in 3D, and exports |
| 5. Geometry file | script emits `.geo.json` | Blockbench exports `geometry.<name>.main` to `packs/JunkBunch_RP/models/entity/` |
| 6. Animations | script/handwritten molang | authored on the Blockbench timeline, exported to `packs/JunkBunch_RP/animations/` |

The rest of the pipeline is unchanged. After exporting from Blockbench into the
`packs/JunkBunch_RP/...` folders, always run:

```bash
python3 scripts/validate_packs.py     # geometry<->texture agreement, UVs, opacity, refs
python3 scripts/build_mcaddon.py      # validates, then repackages JunkBunch.mcaddon
```

`scripts/build_leafy_assets.py` stays as the offline fallback for when Blockbench
isn't running (e.g. this cloud session, where the local Blockbench app is not
reachable). Either path must pass the same validator before shipping.

## Export settings (must match the pack)

- Geometry format: **Bedrock** entity geometry, identifier `geometry.<character>.main`,
  texture size **64×64**.
- Texture: exported to `textures/entity/characters/<character>.png`, **fully opaque**
  (entity skins render invisible under `entity_alphatest` where they're transparent).
- Animations: Bedrock `.animation.json`, ids `animation.<character>.<name>`, exported to
  `animations/<character>.animation.json`.

The validator enforces the 64×64 size, opacity, and that every exported id is
actually referenced by the client entity — so a bad export fails locally instead of
in-game.
