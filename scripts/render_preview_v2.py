#!/usr/bin/env python3
"""
Accurate Leafy preview based on actual drawing.
Pointed oval shape, taller, faithful to expression and proportions.
"""

from PIL import Image, ImageDraw
import math
import os

preview = Image.new('RGBA', (1200, 900), (250, 250, 250, 255))
draw = ImageDraw.Draw(preview)

def draw_pointed_leaf(img, draw, x_center, y_center, scale=1.0):
    """
    Draw Leafy as a pointed oval (elongated leaf shape).
    Wide at bottom, narrows to point at top.
    """

    # Proportions based on drawing: taller than wide, pointed top, wide bottom
    width = 50 * scale
    height = 120 * scale

    # Create pointed oval path points
    points = []

    # Bottom curve (wider)
    for angle in range(180, 360):
        rad = math.radians(angle)
        x = x_center + math.cos(rad) * width * 0.8
        y = y_center + height/2 + math.sin(rad) * (height * 0.3)
        points.append((x, y))

    # Right side taper to point
    for t in range(0, 11):
        ratio = t / 10.0  # 0 to 1
        x = x_center + width * (1 - ratio) * 0.8
        y = y_center + (height/2) * (1 - ratio * 1.5) - height/2
        points.append((x, y))

    # Top point (sharp)
    points.append((x_center, y_center - height/2))

    # Left side taper from point
    for t in range(10, -1, -1):
        ratio = t / 10.0  # 1 to 0
        x = x_center - width * (1 - ratio) * 0.8
        y = y_center + (height/2) * (1 - ratio * 1.5) - height/2
        points.append((x, y))

    # Draw filled leaf
    if len(points) > 2:
        draw.polygon(points, fill=(45, 134, 89, 255), outline=(26, 77, 46, 255))

    # Draw vein pattern (center line + side veins)
    # Main vein from top to bottom
    draw.line([(x_center, y_center - height/2 + 5), (x_center, y_center + height/2 - 10)],
              fill=(26, 77, 46, 200), width=2)

    # Side veins
    vein_count = 4
    for i in range(1, vein_count):
        ratio = i / vein_count
        x_offset = width * 0.6 * (1 - ratio * 0.5)
        start_y = y_center - height/2 + height * 0.1
        end_y = y_center + height/2 - height * 0.15

        # Left vein
        draw.line([(x_center - x_offset, start_y + (end_y - start_y) * ratio),
                   (x_center - x_offset * 0.7, start_y + (end_y - start_y) * (ratio + 0.15))],
                  fill=(26, 77, 46, 100), width=1)
        # Right vein
        draw.line([(x_center + x_offset, start_y + (end_y - start_y) * ratio),
                   (x_center + x_offset * 0.7, start_y + (end_y - start_y) * (ratio + 0.15))],
                  fill=(26, 77, 46, 100), width=1)

    # Draw highlight (lighter green on left side)
    highlight_points = []
    for angle in range(120, 240):
        rad = math.radians(angle)
        x = x_center - 15 + math.cos(rad) * 20
        y = y_center - 40 + math.sin(rad) * 15
        highlight_points.append((x, y))

    if len(highlight_points) > 2:
        draw.polygon(highlight_points, fill=(144, 238, 144, 100), outline=None)

    # Draw face (expressing personality)
    face_y = y_center - 20

    # Eyes - specific placement from drawing
    eye_distance = 15 * scale
    # Left eye
    draw.ellipse([x_center - eye_distance - 4, face_y - 8, x_center - eye_distance + 2, face_y - 2],
                 fill=(0, 0, 0, 255), outline=None)
    # Right eye
    draw.ellipse([x_center + eye_distance - 2, face_y - 8, x_center + eye_distance + 4, face_y - 2],
                 fill=(0, 0, 0, 255), outline=None)

    # Smile - curved expression (personality)
    draw.arc([(x_center - 18, face_y - 2), (x_center + 18, face_y + 14)], 0, 180,
             fill=(0, 0, 0, 255), width=2)

    # Draw stem antenna (curly)
    stem_x = x_center
    stem_y = y_center - height/2 - 5
    # Stem base
    draw.rectangle([stem_x - 2, stem_y - 25, stem_x + 2, stem_y],
                   fill=(45, 134, 89, 255), outline=(26, 77, 46, 255))
    # Curly top
    draw.arc([(stem_x - 8, stem_y - 40), (stem_x + 8, stem_y - 20)], 0, 180,
             fill=(45, 134, 89, 255), width=3)

    # Draw stick limbs
    # Left arm
    arm_y = y_center + 10
    draw.line([(x_center - width * 0.8, arm_y), (x_center - width * 1.5, arm_y - 5)],
              fill=(101, 67, 33, 255), width=3)
    # Right arm
    draw.line([(x_center + width * 0.8, arm_y), (x_center + width * 1.5, arm_y - 5)],
              fill=(101, 67, 33, 255), width=3)

    # Left leg
    leg_y = y_center + height * 0.35
    draw.line([(x_center - width * 0.6, leg_y), (x_center - width * 0.6, leg_y + 25)],
              fill=(101, 67, 33, 255), width=3)
    # Right leg
    draw.line([(x_center + width * 0.6, leg_y), (x_center + width * 0.6, leg_y + 25)],
              fill=(101, 67, 33, 255), width=3)

# Draw title
try:
    from PIL import ImageFont
    default_font = ImageFont.load_default()
except:
    default_font = None

draw.text((40, 20), "LEAFY - DESIGN REFERENCE (V2)", fill=(26, 77, 46, 255))
draw.text((40, 45), "Pointed oval shape (taller, narrow at top) - Faithful to drawing", fill=(100, 100, 100, 255))

# Draw three views
draw.text((80, 80), "FRONT VIEW (Idle)", fill=(26, 77, 46, 255))
draw_pointed_leaf(preview, draw, 150, 250, scale=1.5)

draw.text((430, 80), "3D PERSPECTIVE", fill=(26, 77, 46, 255))
draw_pointed_leaf(preview, draw, 520, 250, scale=1.3)
# Add slight shading to show 3D
draw.line([(520 - 35, 140), (520 - 35, 380)], fill=(0, 0, 0, 50), width=8)

draw.text((780, 80), "WITH LIMBS", fill=(26, 77, 46, 255))
draw_pointed_leaf(preview, draw, 920, 250, scale=1.2)

# Information box
draw.rectangle([40, 500, 400, 650], outline=(26, 77, 46, 255), width=2, fill=(240, 250, 240, 255))
draw.text((50, 510), "DESIGN SPECS:", fill=(26, 77, 46, 255))
draw.text((50, 535), "Shape: Pointed oval (leaf)", fill=(0, 0, 0, 255))
draw.text((50, 555), "Height: Tall (2:1 ratio)", fill=(0, 0, 0, 255))
draw.text((50, 575), "Expression: Friendly smile", fill=(0, 0, 0, 255))
draw.text((50, 595), "Eyes: Placed for personality", fill=(0, 0, 0, 255))
draw.text((50, 615), "3D: Curved form, dimension", fill=(0, 0, 0, 255))

# Color palette
draw.rectangle([450, 500, 800, 650], outline=(26, 77, 46, 255), width=2, fill=(240, 250, 240, 255))
draw.text((460, 510), "COLOR PALETTE:", fill=(26, 77, 46, 255))

# Primary green
draw.rectangle([460, 540, 490, 570], fill=(45, 134, 89, 255), outline=(26, 77, 46, 255), width=1)
draw.text((500, 545), "Primary: #2d8659", fill=(0, 0, 0, 255))

# Accent green
draw.rectangle([460, 580, 490, 610], fill=(144, 238, 144, 255), outline=(26, 77, 46, 255), width=1)
draw.text((500, 585), "Highlight: #90ee90", fill=(0, 0, 0, 255))

# Wood brown
draw.rectangle([460, 620, 490, 650], fill=(101, 67, 33, 255), outline=(60, 40, 20, 255), width=1)
draw.text((500, 625), "Limbs: #654321", fill=(0, 0, 0, 255))

# Personality note
draw.rectangle([850, 500, 1150, 650], outline=(45, 134, 89, 255), width=2, fill=(240, 250, 240, 255))
draw.text((860, 510), "PERSONALITY IN FACE:", fill=(26, 77, 46, 255))
draw.text((860, 535), "● Eyes: Simple, expressive", fill=(0, 0, 0, 255))
draw.text((860, 555), "● Smile: Curved & friendly", fill=(0, 0, 0, 255))
draw.text((860, 575), "● Overall: Shy but warm", fill=(0, 0, 0, 255))
draw.text((860, 595), "● Stem: Whimsical detail", fill=(0, 0, 0, 255))
draw.text((860, 615), "(Faithful to drawing)", fill=(100, 100, 100, 255))

# Save
output_path = os.path.join(os.path.dirname(__file__), "..", "characters", "leafy_preview_v2.png")
preview.save(output_path)
print(f"✓ Preview v2 saved: {output_path}")
