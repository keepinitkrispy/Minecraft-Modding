#!/usr/bin/env python3
"""
FINAL: Simple oval leaf Leafy - done right.
Oval shape, eyes ON the leaf (not sinking in), simple smile, stick limbs.
"""

from PIL import Image, ImageDraw
import math
import os

preview = Image.new('RGBA', (1000, 800), (250, 250, 250, 255))
draw = ImageDraw.Draw(preview)

def draw_leafy_correct(img, draw, x_center, y_center, scale=1.0):
    """
    Leafy: Simple oval leaf with face ON the surface.
    """

    width = 48 * scale
    height = 105 * scale

    # Draw slightly more pointed oval leaf body
    draw.ellipse([x_center - width/2, y_center - height/2,
                  x_center + width/2, y_center + height/2],
                 fill=(45, 134, 89, 255), outline=(26, 77, 46, 255), width=2)

    # Point at top (stem connection)
    draw.line([(x_center, y_center - height/2), (x_center, y_center - height/2 - 15)],
              fill=(26, 77, 46, 255), width=3)

    # Center spine vein (down the middle)
    draw.line([(x_center, y_center - height/2 + 8), (x_center, y_center + height/2 - 8)],
              fill=(26, 77, 46, 200), width=2)

    # Highlight (light green area on left side)
    draw.ellipse([x_center - width/3.5, y_center - height/3,
                  x_center - width/8, y_center + height/5],
                 fill=(144, 238, 144, 150), outline=None)

    # EYES - positioned ON the leaf surface, not sinking in
    eye_y = y_center - height/6
    eye_dist = 10 * scale
    eye_radius = 4

    # Left eye
    draw.ellipse([x_center - eye_dist - eye_radius, eye_y - eye_radius,
                  x_center - eye_dist + eye_radius, eye_y + eye_radius],
                 fill=(0, 0, 0, 255), outline=None)

    # Right eye
    draw.ellipse([x_center + eye_dist - eye_radius, eye_y - eye_radius,
                  x_center + eye_dist + eye_radius, eye_y + eye_radius],
                 fill=(0, 0, 0, 255), outline=None)

    # SMILE - curved line on the leaf
    smile_y = eye_y + 8
    draw.arc([(x_center - 14, smile_y), (x_center + 14, smile_y + 12)], 0, 180,
             fill=(0, 0, 0, 255), width=2)

    # Stem (curly antenna at top)
    stem_top = y_center - height/2 - 15
    draw.rectangle([x_center - 1.5, stem_top - 12, x_center + 1.5, stem_top],
                   fill=(45, 134, 89, 255))
    # Curl at top
    draw.arc([(x_center - 5, stem_top - 22), (x_center + 5, stem_top - 12)], 0, 180,
             fill=(45, 134, 89, 255), width=2)

    # STICK LIMBS - extending from sides
    arm_y = y_center

    # Left arm
    draw.line([(x_center - width/2 - 2, arm_y), (x_center - width/2 - 35, arm_y)],
              fill=(101, 67, 33, 255), width=2)

    # Right arm
    draw.line([(x_center + width/2 + 2, arm_y), (x_center + width/2 + 35, arm_y)],
              fill=(101, 67, 33, 255), width=2)

    # Left leg
    leg_y = y_center + height/3
    draw.line([(x_center - width/3, leg_y), (x_center - width/3, leg_y + 32)],
              fill=(101, 67, 33, 255), width=2)

    # Right leg
    draw.line([(x_center + width/3, leg_y), (x_center + width/3, leg_y + 32)],
              fill=(101, 67, 33, 255), width=2)


# Draw the design
draw.text((40, 20), "LEAFY - FINAL (Simple Oval Leaf)", fill=(26, 77, 46, 255))

# Front view
draw.text((150, 70), "FRONT VIEW", fill=(26, 77, 46, 255))
draw_leafy_correct(preview, draw, 200, 240, scale=2.0)

# Side by side comparison
draw.text((500, 70), "WITH LIMBS", fill=(26, 77, 46, 255))
draw_leafy_correct(preview, draw, 650, 240, scale=1.8)

# Info
draw.rectangle([40, 500, 960, 780], outline=(26, 77, 46, 255), width=2, fill=(240, 250, 240, 255))

draw.text((50, 510), "DESIGN:", fill=(26, 77, 46, 255))
draw.text((50, 535), "✓ Simple oval leaf (like picking one up off the ground)", fill=(0, 0, 0, 255))
draw.text((50, 560), "✓ Eyes positioned ON the leaf surface (not sinking in)", fill=(0, 0, 0, 255))
draw.text((50, 585), "✓ Smile on the leaf", fill=(0, 0, 0, 255))
draw.text((50, 610), "✓ Center spine vein down the middle", fill=(0, 0, 0, 255))
draw.text((50, 635), "✓ Stem with curly antenna at top", fill=(0, 0, 0, 255))
draw.text((50, 660), "✓ Simple stick limbs extending from sides", fill=(0, 0, 0, 255))
draw.text((50, 685), "✓ No weird bottom pieces", fill=(0, 0, 0, 255))
draw.text((50, 710), "✓ Clean, simple, faithful to the drawing", fill=(0, 0, 0, 255))
draw.text((50, 735), "✓ Ready to be built in 3D for Minecraft", fill=(0, 0, 0, 255))

# Save
output_path = os.path.join(os.path.dirname(__file__), "..", "characters", "leafy_preview_final.png")
preview.save(output_path)
print(f"✓ Final preview saved: {output_path}")
