#!/usr/bin/env python3
"""
Generate textures for Junk Bunch characters.
Requires: Pillow (PIL), numpy
"""

from PIL import Image, ImageDraw
import os

# Create textures directory if it doesn't exist
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(script_dir)
texture_dir = os.path.join(repo_root, "packs/JunkBunch_RP/textures/entity/characters")
item_dir = os.path.join(repo_root, "packs/JunkBunch_RP/textures/items")
os.makedirs(texture_dir, exist_ok=True)
os.makedirs(item_dir, exist_ok=True)

# Leafy texture (64x64)
leafy_texture = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
draw = ImageDraw.Draw(leafy_texture)

# Draw body (green leaf)
draw.ellipse([8, 4, 56, 48], fill=(45, 134, 89, 255), outline=(26, 77, 46, 255), width=2)

# Draw vein pattern (lines from top to bottom)
draw.line([(32, 8), (32, 44)], fill=(26, 77, 46, 200), width=1)
draw.line([(20, 16), (44, 40)], fill=(26, 77, 46, 200), width=1)
draw.line([(44, 16), (20, 40)], fill=(26, 77, 46, 200), width=1)

# Draw small accent veins
draw.line([(24, 20), (28, 36)], fill=(26, 77, 46, 100), width=1)
draw.line([(36, 20), (40, 36)], fill=(26, 77, 46, 100), width=1)

# Draw highlight (lighter green accent)
draw.ellipse([12, 8, 32, 24], fill=(144, 238, 144, 100), outline=None)

# Draw face (eyes and smile)
# Left eye
draw.ellipse([18, 18, 22, 22], fill=(0, 0, 0, 255), outline=None)
# Right eye
draw.ellipse([42, 18, 46, 22], fill=(0, 0, 0, 255), outline=None)
# Smile
draw.arc([(20, 22), (44, 38)], 0, 180, fill=(0, 0, 0, 255), width=2)

# Draw stem (top)
draw.rectangle([30, 0, 34, 6], fill=(45, 134, 89, 255), outline=(26, 77, 46, 255))

leafy_texture.save(f"{texture_dir}/leafy.png")
print("✓ Created leafy.png")

# Rake texture (16x16 for an item)
rake_texture = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
draw = ImageDraw.Draw(rake_texture)

# Rake handle (wood brown)
draw.rectangle([6, 4, 8, 15], fill=(101, 67, 33, 255), outline=(60, 40, 20, 255))

# Rake tines (iron gray)
# Top tine
draw.rectangle([2, 2, 4, 4], fill=(169, 169, 169, 255), outline=(100, 100, 100, 255))
# Middle-left tine
draw.rectangle([2, 4, 4, 6], fill=(169, 169, 169, 255), outline=(100, 100, 100, 255))
# Center tine
draw.rectangle([6, 2, 8, 4], fill=(169, 169, 169, 255), outline=(100, 100, 100, 255))
# Middle-right tine
draw.rectangle([10, 4, 12, 6], fill=(169, 169, 169, 255), outline=(100, 100, 100, 255))
# Right tine
draw.rectangle([12, 2, 14, 4], fill=(169, 169, 169, 255), outline=(100, 100, 100, 255))

rake_texture.save(f"{item_dir}/summon_rake.png")
print("✓ Created summon_rake.png")

print("\nAll textures generated successfully!")
