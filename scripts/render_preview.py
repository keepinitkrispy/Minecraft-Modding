#!/usr/bin/env python3
"""
Render a character preview image showing design, animations, and details.
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Create preview
preview = Image.new('RGBA', (1024, 768), (240, 240, 240, 255))
draw = ImageDraw.Draw(preview)

# Helper function to draw Leafy in different states
def draw_leafy_state(img, draw, x_offset, y_offset, state_name, scale=1.0):
    """Draw Leafy in a specific animation state."""

    scale_x = x_offset
    scale_y = y_offset

    # Draw body (green leaf)
    body_x = scale_x + 80
    body_y = scale_y + 60

    if state_name == "idle":
        draw.ellipse([body_x - 30, body_y - 35, body_x + 30, body_y + 30],
                     fill=(45, 134, 89, 255), outline=(26, 77, 46, 255), width=2)
        bob_offset = 0
    elif state_name == "walking":
        draw.ellipse([body_x - 30, body_y - 30, body_x + 30, body_y + 25],
                     fill=(45, 134, 89, 255), outline=(26, 77, 46, 255), width=2)
        bob_offset = -5
    else:  # floating/ability
        draw.ellipse([body_x - 30, body_y - 40, body_x + 30, body_y + 35],
                     fill=(45, 134, 89, 255), outline=(26, 77, 46, 255), width=2)
        bob_offset = -15

    # Draw vein pattern
    draw.line([(body_x, body_y - 30), (body_x, body_y + 20)],
              fill=(26, 77, 46, 200), width=2)
    draw.line([(body_x - 15, body_y - 10), (body_x + 15, body_y + 15)],
              fill=(26, 77, 46, 150), width=1)
    draw.line([(body_x + 15, body_y - 10), (body_x - 15, body_y + 15)],
              fill=(26, 77, 46, 150), width=1)

    # Draw highlight
    draw.ellipse([body_x - 15, body_y - 25, body_x + 5, body_y - 10],
                 fill=(144, 238, 144, 120), outline=None)

    # Draw stem
    if state_name == "floating":
        stem_rot = 20
    elif state_name == "walking":
        stem_rot = 5
    else:
        stem_rot = 0
    draw.rectangle([body_x - 2, body_y - 45, body_x + 2, body_y - 40],
                   fill=(45, 134, 89, 255), outline=(26, 77, 46, 255))

    # Draw face
    # Eyes
    draw.ellipse([body_x - 10, body_y - 5, body_x - 6, body_y + 1],
                 fill=(0, 0, 0, 255), outline=None)
    draw.ellipse([body_x + 6, body_y - 5, body_x + 10, body_y + 1],
                 fill=(0, 0, 0, 255), outline=None)
    # Smile
    draw.arc([(body_x - 12, body_y + 2), (body_x + 12, body_y + 16)], 0, 180,
             fill=(0, 0, 0, 255), width=2)

    # Draw limbs (stick arms and legs)
    arm_y = body_y - 5
    leg_y = body_y + 30

    if state_name == "walking":
        # Arms swinging
        draw.line([(body_x - 30, arm_y), (body_x - 50, arm_y - 15)],
                  fill=(101, 67, 33, 255), width=3)
        draw.line([(body_x + 30, arm_y), (body_x + 50, arm_y + 15)],
                  fill=(101, 67, 33, 255), width=3)
    else:
        # Arms resting
        draw.line([(body_x - 30, arm_y), (body_x - 45, arm_y)],
                  fill=(101, 67, 33, 255), width=3)
        draw.line([(body_x + 30, arm_y), (body_x + 45, arm_y)],
                  fill=(101, 67, 33, 255), width=3)

    # Legs
    draw.line([(body_x - 15, body_y + 30), (body_x - 15, body_y + 50)],
              fill=(101, 67, 33, 255), width=3)
    draw.line([(body_x + 15, body_y + 30), (body_x + 15, body_y + 50)],
              fill=(101, 67, 33, 255), width=3)

    # Add floating particles for ability state
    if state_name == "floating":
        for i in range(5):
            px = body_x + (i - 2) * 20
            py = body_y - 60 + i * 10
            draw.ellipse([px - 2, py - 2, px + 2, py + 2],
                         fill=(144, 238, 144, 150), outline=None)

    # Draw state label
    try:
        title_font = ImageFont.load_default()
        draw.text((scale_x + 30, scale_y + 180), state_name.upper(),
                  fill=(26, 77, 46, 255), font=title_font)
    except:
        pass

# Draw three animation states
draw_leafy_state(preview, draw, 50, 100, "idle")
draw_leafy_state(preview, draw, 350, 100, "walking")
draw_leafy_state(preview, draw, 650, 100, "floating")

# Draw the rake item (larger, standalone)
rake_x = 100
rake_y = 450

# Rake handle
draw.rectangle([rake_x + 40, rake_y + 20, rake_x + 50, rake_y + 100],
               fill=(101, 67, 33, 255), outline=(60, 40, 20, 255), width=2)

# Rake tines (head)
tine_y = rake_y + 20
for i, offset in enumerate([-30, -15, 0, 15, 30]):
    draw.rectangle([rake_x + 45 + offset - 5, tine_y - 20, rake_x + 45 + offset + 5, tine_y],
                   fill=(169, 169, 169, 255), outline=(100, 100, 100, 255), width=1)

# Item label
try:
    title_font = ImageFont.load_default()
    draw.text((rake_x - 20, rake_y + 120), "RAKE ITEM",
              fill=(60, 40, 20, 255), font=title_font)
except:
    pass

# Draw title and info
try:
    title_font = ImageFont.load_default()

    # Title
    draw.text((30, 20), "LEAFY - CHARACTER PREVIEW", fill=(26, 77, 46, 255), font=title_font)

    # Info box
    draw.rectangle([30, 330, 300, 420], outline=(26, 77, 46, 255), width=2)
    draw.text((40, 340), "Name: Leafy", fill=(0, 0, 0, 255), font=title_font)
    draw.text((40, 355), "Personality: Fun, Helpful, Shy", fill=(0, 0, 0, 255), font=title_font)
    draw.text((40, 370), "Ability: Slow Float", fill=(0, 0, 0, 255), font=title_font)
    draw.text((40, 385), "Item: Rake (craft)", fill=(0, 0, 0, 255), font=title_font)

    # Color palette
    draw.text((350, 330), "Colors:", fill=(26, 77, 46, 255), font=title_font)
    draw.rectangle([350, 350, 370, 370], fill=(45, 134, 89, 255), outline=(26, 77, 46, 255), width=1)
    draw.text((375, 350), "Primary Green", fill=(0, 0, 0, 255), font=title_font)

    draw.rectangle([350, 375, 370, 395], fill=(144, 238, 144, 255), outline=(26, 77, 46, 255), width=1)
    draw.text((375, 375), "Accent/Highlight", fill=(0, 0, 0, 255), font=title_font)

    draw.rectangle([350, 400, 370, 420], fill=(101, 67, 33, 255), outline=(60, 40, 20, 255), width=1)
    draw.text((375, 400), "Wood/Limbs", fill=(0, 0, 0, 255), font=title_font)

except Exception as e:
    print(f"Font error (non-critical): {e}")

# Save
output_path = os.path.join(os.path.dirname(__file__), "..", "characters", "leafy_preview.png")
os.makedirs(os.path.dirname(output_path), exist_ok=True)
preview.save(output_path)
print(f"✓ Preview saved to: {output_path}")
print(f"  Size: {preview.size}")
