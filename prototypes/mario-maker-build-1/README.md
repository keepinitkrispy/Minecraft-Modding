# Mario Maker Bedrock — Build 1

A PS5-targeted Bedrock prototype derived from the Junk Bunch workflow.

## Included
- Compass-opened controller menu with 3D World, Mario 64, and Odyssey style selections.
- Castle, parkour, pipe pavilion, and a first short platform course with coin markers and a goal marker.
- Goomba/Koopa prototype placement and Mario brick placement.
- Follow-orbit camera preset and first-person switch.
- Optional speed/jump boost.

## Status
Package is generated locally as `MarioMaker_Build1_PROTOTYPE.mcaddon`. The script and JSON syntax have been checked. Minecraft import, entity behavior, camera operation, visual quality, Realm transfer, and PS5 runtime are not yet tested. Current enemy stand-ins use vanilla slime and turtle entities. Theme selection currently recolors generated structures only; the style-specific gameplay and polished texture pack remain future work.

## Build
Run `python3 build.py` in this directory. Generated pack sources are in `generated/`.
