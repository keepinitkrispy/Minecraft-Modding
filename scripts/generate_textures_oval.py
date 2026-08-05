#!/usr/bin/env python3
"""
Generate textures for Leafy oval leaf design.
"""

from PIL import Image, ImageDraw
import os
import math

# Create textures directory if it doesn't exist
texture_dir = os.path.join(os.path.dirname(__file__), "..", "packs/JunkBunch_RP/textures/entity/characters")
os.makedirs(texture_dir, exist_ok=True)

# Leafy texture (64x64)
leafy_texture = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
draw = ImageDraw.Draw(leafy_texture)

# Draw main leaf body (oval shape in UV space)
# Top half of texture = front face
draw.ellipse([8, 4, 56, 50], fill=(45, 134, 89, 255), outline=(26, 77, 46, 255), width=1)

# Draw center spine vein
draw.line([(32, 8), (32, 48)], fill=(26, 77, 46, 200), width=1)

# Draw subtle secondary veins
for i in range(1, 4):
    ratio = i / 4.0
    y_pos = 8 + (40 * ratio)
    offset = 8 * (1 - ratio * 0.5)
    draw.line([(32 - offset, y_pos), (24 - offset, y_pos + 3)], fill=(26, 77, 46, 100), width=1)
    draw.line([(32 + offset, y_pos), (40 + offset, y_pos + 3)], fill=(26, 77, 46, 100), width=1)

# Draw highlight (light green on left side)
draw.ellipse([10, 8, 28, 28], fill=(144, 238, 144, 120), outline=None)

# Face texture (on top part of leaf)
# Left eye
draw.ellipse([18, 16, 22, 20], fill=(0, 0, 0, 255), outline=None)
# Right eye
draw.ellipse([42, 16, 46, 20], fill=(0, 0, 0, 255), outline=None)
# Smile
draw.arc([(20, 22), (44, 32)], 0, 180, fill=(0, 0, 0, 200), width=1)

# Stem area (top of texture, small brown stem)
draw.rectangle([30, 0, 34, 4], fill=(45, 134, 89, 255), outline=(26, 77, 46, 255))

# Bottom half of texture = back/side shading
draw.ellipse([8, 32, 56, 60], fill=(26, 77, 46, 100), outline=None)

leafy_texture.save(os.path.join(texture_dir, "leafy.png"))
print("✓ Created leafy.png")

# Rake item texture (16x16)
item_dir = os.path.join(os.path.dirname(__file__), "..", "packs/JunkBunch_RP/textures/items")
os.makedirs(item_dir, exist_ok=True)

rake_texture = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
draw = ImageDraw.Draw(rake_texture)

# Rake handle (wood brown)
draw.rectangle([6, 4, 8, 14], fill=(101, 67, 33, 255), outline=(60, 40, 20, 255), width=1)

# Rake tines (iron gray) - 5 tines spread out
tine_y = 4
tine_positions = [2, 4, 6, 8, 10, 12]
for x_pos in tine_positions:
    draw.rectangle([x_pos, tine_y - 2, x_pos + 1, tine_y + 2], fill=(169, 169, 169, 255), outline=(100, 100, 100, 255), width=1)

rake_texture.save(os.path.join(item_dir, "summon_rake.png"))
print("✓ Created summon_rake.png")

print("\nAll textures generated successfully!")
