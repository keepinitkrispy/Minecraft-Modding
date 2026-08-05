#!/usr/bin/env python3
"""
Simple oval leaf Leafy - just like a real leaf that fell off a tree.
Oval shape, point at top, center spine. Natural and clean.
"""

from PIL import Image, ImageDraw
import math
import os

preview = Image.new('RGBA', (1200, 900), (250, 250, 250, 255))
draw = ImageDraw.Draw(preview)

def draw_simple_oval_leaf(img, draw, x_center, y_center, scale=1.0):
    """
    Draw Leafy as a simple oval leaf.
    Wider in the middle, pointed at top, smooth curves.
    Like a real leaf from a tree.
    """

    width = 50 * scale   # Max width at middle
    height = 110 * scale  # Total height

    # Draw the leaf body as an oval with point at top
    # Using ellipse math to create smooth natural curves

    points = []

    # Create smooth oval shape
    # Bottom rounded part
    for angle in range(180, 360):
        rad = math.radians(angle)
        x = x_center + math.cos(rad) * (width / 2)
        y = y_center + height/2 + math.sin(rad) * (height * 0.25)
        points.append((x, y))

    # Right side curving to point
    for t in range(0, 11):
        ratio = t / 10.0
        curve_factor = math.sin(ratio * math.pi)  # Smooth S-curve
        x = x_center + (width / 2) * (1 - ratio) * curve_factor
        y = y_center + (height/2) * (1 - ratio * 2)
        points.append((x, y))

    # Top point
    points.append((x_center, y_center - height/2))

    # Left side curving from point
    for t in range(10, -1, -1):
        ratio = t / 10.0
        curve_factor = math.sin(ratio * math.pi)
        x = x_center - (width / 2) * (1 - ratio) * curve_factor
        y = y_center + (height/2) * (1 - ratio * 2)
        points.append((x, y))

    # Draw filled leaf
    if len(points) > 2:
        draw.polygon(points, fill=(45, 134, 89, 255), outline=(26, 77, 46, 255))

    # Draw center spine/vein (main vein down the middle)
    draw.line([(x_center, y_center - height/2 + 5), (x_center, y_center + height/2 - 10)],
              fill=(26, 77, 46, 200), width=2)

    # Draw subtle secondary veins
    for i in range(1, 4):
        ratio = i / 4.0
        x_pos = x_center + (width / 3) * (1 - ratio * 0.5)
        y_pos = y_center - height/2 + height * ratio
        draw.line([(x_pos, y_pos), (x_pos + 10, y_pos + 5)],
                  fill=(26, 77, 46, 80), width=1)
        draw.line([(x_center - (width / 3) * (1 - ratio * 0.5), y_pos),
                   (x_center - (width / 3) * (1 - ratio * 0.5) - 10, y_pos + 5)],
                  fill=(26, 77, 46, 80), width=1)

    # Draw highlight (lighter green on one side)
    highlight_width = width * 0.3
    highlight_points = []
    for angle in range(120, 240):
        rad = math.radians(angle)
        x = x_center - highlight_width + math.cos(rad) * highlight_width
        y = y_center - 20 + math.sin(rad) * (height * 0.15)
        highlight_points.append((x, y))

    if len(highlight_points) > 2:
        draw.polygon(highlight_points, fill=(144, 238, 144, 120), outline=None)

    # Draw face (personality)
    face_y = y_center - 15

    # Eyes - simple dots
    eye_distance = 12 * scale
    eye_size = 4
    # Left eye
    draw.ellipse([x_center - eye_distance - eye_size, face_y - eye_size,
                  x_center - eye_distance + eye_size, face_y + eye_size],
                 fill=(0, 0, 0, 255), outline=None)
    # Right eye
    draw.ellipse([x_center + eye_distance - eye_size, face_y - eye_size,
                  x_center + eye_distance + eye_size, face_y + eye_size],
                 fill=(0, 0, 0, 255), outline=None)

    # Smile - friendly curved line
    draw.arc([(x_center - 16, face_y), (x_center + 16, face_y + 16)], 0, 180,
             fill=(0, 0, 0, 255), width=2)

    # Draw stem
    stem_y = y_center - height/2 - 8
    draw.rectangle([x_center - 2, stem_y - 18, x_center + 2, stem_y],
                   fill=(45, 134, 89, 255), outline=(26, 77, 46, 255))
    # Curly top of stem
    draw.arc([(x_center - 6, stem_y - 28), (x_center + 6, stem_y - 16)], 0, 180,
             fill=(45, 134, 89, 255), width=2)

    # Stick limbs (thin, simple)
    arm_y = y_center + 5
    # Left arm
    draw.line([(x_center - width/2 - 3, arm_y), (x_center - width - 8, arm_y - 3)],
              fill=(101, 67, 33, 255), width=2)
    # Right arm
    draw.line([(x_center + width/2 + 3, arm_y), (x_center + width + 8, arm_y - 3)],
              fill=(101, 67, 33, 255), width=2)

    # Left leg
    leg_y = y_center + height * 0.3
    draw.line([(x_center - width/2.5, leg_y), (x_center - width/2.5, leg_y + 22)],
              fill=(101, 67, 33, 255), width=2)
    # Right leg
    draw.line([(x_center + width/2.5, leg_y), (x_center + width/2.5, leg_y + 22)],
              fill=(101, 67, 33, 255), width=2)

# Title
draw.text((40, 20), "LEAFY - SIMPLE OVAL LEAF (V3)", fill=(26, 77, 46, 255))
draw.text((40, 45), "Natural leaf shape: oval, smooth curves, pointed top, center spine", fill=(100, 100, 100, 255))

# Draw three views
draw.text((100, 80), "FRONT VIEW", fill=(26, 77, 46, 255))
draw_simple_oval_leaf(preview, draw, 150, 260, scale=1.5)

draw.text((420, 80), "3D FORM", fill=(26, 77, 46, 255))
draw_simple_oval_leaf(preview, draw, 520, 260, scale=1.4)
# Add shading for 3D
draw.line([(520 - 35, 155), (520 - 35, 365)], fill=(0, 0, 0, 40), width=6)

draw.text((800, 80), "WITH LIMBS", fill=(26, 77, 46, 255))
draw_simple_oval_leaf(preview, draw, 920, 260, scale=1.2)

# Info boxes
draw.rectangle([40, 500, 380, 650], outline=(26, 77, 46, 255), width=2, fill=(240, 250, 240, 255))
draw.text((50, 510), "SHAPE:", fill=(26, 77, 46, 255))
draw.text((50, 535), "• Simple oval", fill=(0, 0, 0, 255))
draw.text((50, 555), "• Wider in middle", fill=(0, 0, 0, 255))
draw.text((50, 575), "• Smooth natural curves", fill=(0, 0, 0, 255))
draw.text((50, 595), "• Point at top (stem)", fill=(0, 0, 0, 255))
draw.text((50, 615), "• Center spine vein", fill=(0, 0, 0, 255))

draw.rectangle([410, 500, 750, 650], outline=(26, 77, 46, 255), width=2, fill=(240, 250, 240, 255))
draw.text((420, 510), "EXPRESSION:", fill=(26, 77, 46, 255))
draw.text((420, 535), "• Simple dot eyes", fill=(0, 0, 0, 255))
draw.text((420, 555), "• Friendly smile", fill=(0, 0, 0, 255))
draw.text((420, 575), "• Shy personality", fill=(0, 0, 0, 255))
draw.text((420, 595), "• Curly stem antenna", fill=(0, 0, 0, 255))
draw.text((420, 615), "• Welcoming overall", fill=(0, 0, 0, 255))

draw.rectangle([780, 500, 1150, 650], outline=(26, 77, 46, 255), width=2, fill=(240, 250, 240, 255))
draw.text((790, 510), "COLORS:", fill=(26, 77, 46, 255))
draw.rectangle([790, 535, 820, 565], fill=(45, 134, 89, 255), outline=(26, 77, 46, 255), width=1)
draw.text((830, 540), "Leaf: Forest Green", fill=(0, 0, 0, 255))

draw.rectangle([790, 575, 820, 605], fill=(144, 238, 144, 255), outline=(26, 77, 46, 255), width=1)
draw.text((830, 580), "Highlight: Light Green", fill=(0, 0, 0, 255))

draw.rectangle([790, 615, 820, 645], fill=(101, 67, 33, 255), outline=(60, 40, 20, 255), width=1)
draw.text((830, 620), "Limbs: Wood Brown", fill=(0, 0, 0, 255))

# Save
output_path = os.path.join(os.path.dirname(__file__), "..", "characters", "leafy_preview_v3.png")
preview.save(output_path)
print(f"✓ Preview v3 saved: {output_path}")
