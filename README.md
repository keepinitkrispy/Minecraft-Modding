# Coiny Companion - Bedrock Add-on

A custom Minecraft Bedrock Edition companion entity featuring Coiny, a voxel-based coin character with an interactive slap attack mechanic.

## Project Structure

```
Minecraft-Modding/
├── behavior_pack/
│   ├── manifest.json              # Behavior pack metadata
│   ├── entities/
│   │   └── coiny.json             # Entity definition with components & events
│   └── items/
│       └── coiny_spawn_egg.json    # Spawn item definition
└── resource_pack/
    ├── manifest.json              # Resource pack metadata
    ├── models/
    │   └── entity/
    │       └── coiny.geo.json      # Voxel geometry (bones & cubes)
    ├── animations/
    │   └── coiny.animation.json    # Idle, walk, and slap animations
    ├── animation_controllers/
    │   └── coiny.animation_controllers.json  # Animation state machine
    ├── render_controllers/
    │   └── coiny.render_controllers.json     # Render logic
    └── entity/
        └── coiny.json             # Client-side entity definition
```

## Features

### Design Specification
- **Silhouette**: Cylindrical coin body (~12 units wide) with slanted interior embossing stripe
- **Structure**: 45-55 cubes forming cylindrical volume with gold/yellow highlights, dark rims, and angled stripe
- **Limbs**: 4-6 cube arms with skin-tone hands; 3-4 cube stubby legs with flat feet
- **Face**: Protruding black eye voxels, angular mouth expression, and central embossing stripe

### Behavior Components
- **Health**: 20 HP
- **Movement**: Wanders autonomously with follow_parent and look_at_player behaviors
- **Tameable**: Accepts wheat and apples as taming items
- **Rideable**: Can be ridden by the player

### Special Move: Slap Attack
- **Damage**: 2.0 damage per hit
- **Attack Radius**: 1.5 units
- **Cooldown**: 0.5 seconds
- **Effects**: 
  - Custom punch attack particle burst
  - Knockback force applied to target
  - 0.15s wind-up animation
  - Swift slap motion with body rotation

### Animations
- **Idle**: Gentle arm swaying at 1.5s loop
- **Walk**: Synchronized limb movement with 0.8s cycle
- **Slap Attack**: 0.5s attack sequence with windup, execution, and recovery

## Installation

1. **Compress both packs** into a .mcaddon file:
   ```bash
   # Create zip with behavior_pack and resource_pack at root level
   zip -r coiny-companion.mcaddon behavior_pack/ resource_pack/
   ```

2. **Import into Minecraft**: Place `.mcaddon` file in your Minecraft add-ons folder or double-click to import

3. **Enable in World**: 
   - Create new world → Add-ons → Select "Coiny Companion"
   - Toggle on both behavior and resource packs

## Spawning Coiny

Use the Coiny Spawn Egg (`coiny:coiny_spawn_egg`):
```
/give @s coiny:coiny_spawn_egg
```

Or summon directly:
```
/summon coiny:coiny_companion ~ ~ ~
```

## Events

### Custom Events
- `coiny:on_slap` - Triggers slap attack animation and particle effects
- `coiny:start_attack` - Activates melee attack component
- `coiny:stop_attack` - Deactivates melee attack component

## Texture Assets

The model expects texture file: `textures/entity/coiny/coiny.png` (64×64)
Current implementation uses palette-driven voxel shading (solid colors per cube).

## Notes

- All dimensions are in Minecraft units (1 unit = 1 block)
- Animation timings are in seconds
- Geometry uses stepped cube increments to form cylindrical edge profile
- Eyes and mouth are 1×1 protruding voxels at Z = -1 from main body
