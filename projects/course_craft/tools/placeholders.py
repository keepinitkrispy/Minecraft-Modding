"""Original 16x16 placeholder textures for Course Craft (replace via import_textures.py)."""
from PIL import Image, ImageDraw

INK = (30, 24, 40, 255)


def _base(fill, outline=True):
    im = Image.new("RGBA", (16, 16), fill)
    d = ImageDraw.Draw(im)
    if outline:
        d.rectangle([0, 0, 15, 15], outline=INK)
    return im, d


def _shade(d, light, dark):
    d.line([(1, 1), (14, 1)], fill=light); d.line([(1, 1), (1, 14)], fill=light)
    d.line([(1, 14), (14, 14)], fill=dark); d.line([(14, 1), (14, 14)], fill=dark)


def draw(slot):
    G, Gd, Gl = (72, 200, 90, 255), (40, 140, 60, 255), (150, 240, 150, 255)
    if slot == "cc_start_pad_top":
        im, d = _base(G); _shade(d, Gl, Gd)
        d.polygon([(4, 11), (8, 4), (12, 11)], fill=(255, 255, 255, 255), outline=INK)
        return im
    if slot == "cc_start_pad_side":
        im, d = _base(Gd); d.rectangle([1, 1, 14, 4], fill=G); return im
    if slot == "cc_goal_top":
        im, d = _base((255, 255, 255, 255))
        for y in range(1, 15, 2):
            for x in range(1 + (y // 2) % 2 * 2, 15, 4):
                d.rectangle([x, y, x + 1, y + 1], fill=INK)
        d.ellipse([5, 5, 10, 10], fill=(255, 205, 40, 255), outline=INK)
        return im
    if slot == "cc_goal_side":
        im, d = _base((255, 205, 40, 255)); _shade(d, (255, 240, 150, 255), (200, 140, 20, 255))
        d.rectangle([3, 6, 12, 9], fill=INK); return im
    if slot == "cc_checkpoint":
        im, d = _base((60, 140, 240, 255)); _shade(d, (150, 200, 255, 255), (30, 80, 170, 255))
        d.ellipse([4, 4, 11, 11], outline=(255, 255, 255, 255), width=2); return im
    if slot == "cc_spring_top":
        im, d = _base((235, 60, 60, 255)); _shade(d, (255, 150, 150, 255), (160, 30, 30, 255))
        for r in (6, 4, 2):
            d.ellipse([8 - r, 8 - r, 7 + r, 7 + r], outline=(255, 255, 255, 255))
        return im
    if slot == "cc_spring_side":
        im, d = _base((120, 120, 130, 255))
        for y in range(3, 14, 3):
            d.line([(2, y), (13, y + 1)], fill=(220, 220, 230, 255))
        return im
    if slot == "cc_dash_top":
        im, d = _base((255, 140, 30, 255))
        for y0 in (2, 8):
            d.line([(4, y0 + 4), (8, y0), (12, y0 + 4)], fill=(255, 255, 255, 255), width=2)
        return im
    if slot == "cc_dash_side":
        im, d = _base((200, 90, 20, 255)); d.rectangle([1, 1, 14, 3], fill=(255, 140, 30, 255)); return im
    if slot == "cc_spike_top":
        im, d = _base((90, 90, 100, 255))
        for cx in (4, 11):
            for cy in (4, 11):
                d.polygon([(cx - 3, cy + 3), (cx, cy - 3), (cx + 3, cy + 3)], fill=(220, 220, 230, 255), outline=INK)
        return im
    if slot == "cc_spike_side":
        im, d = _base((90, 90, 100, 255))
        for x in range(1, 15, 4):
            d.polygon([(x, 6), (x + 2, 1), (x + 4, 6)], fill=(220, 220, 230, 255), outline=INK)
        d.rectangle([1, 9, 14, 14], fill=(60, 60, 70, 255)); return im
    if slot == "cc_shard":
        im = Image.new("RGBA", (16, 16), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.polygon([(8, 2), (13, 8), (8, 14), (3, 8)], fill=(80, 230, 230, 255), outline=INK)
        d.polygon([(8, 4), (10, 8), (8, 9), (6, 8)], fill=(210, 255, 255, 255)); return im
    if slot == "cc_bright_brick":
        im, d = _base((230, 110, 50, 255), outline=False)
        for y in (0, 4, 8, 12):
            d.line([(0, y), (15, y)], fill=INK)
            off = 0 if (y // 4) % 2 == 0 else 4
            for x in range(off, 16, 8):
                d.line([(x, y), (x, y + 3)], fill=INK)
        return im
    if slot == "cc_toon_grass_top":
        im, d = _base(G, outline=False)
        for p in ((3, 4), (10, 2), (6, 10), (12, 12)):
            d.point(p, fill=Gl)
        return im
    if slot == "cc_toon_grass_side":
        im, d = _base((170, 110, 60, 255), outline=False)
        d.rectangle([0, 0, 15, 4], fill=G)
        for x in range(0, 16, 3):
            d.point((x, 5), fill=G)
        return im
    if slot == "cc_toon_dirt":
        im, d = _base((170, 110, 60, 255), outline=False)
        for p in ((3, 3), (11, 6), (6, 12)):
            d.point(p, fill=(120, 75, 40, 255))
        return im
    if slot == "cc_cloud":
        im, d = _base((245, 248, 255, 255), outline=False)
        for b in ([1, 6, 7, 12], [5, 3, 12, 10], [9, 7, 15, 13]):
            d.ellipse(b, outline=(190, 205, 230, 255))
        return im
    if slot == "cc_maker_wand":
        im = Image.new("RGBA", (16, 16), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.line([(3, 13), (10, 6)], fill=(140, 90, 50, 255), width=2)
        d.polygon([(11, 1), (12, 4), (15, 5), (12, 6), (11, 9), (10, 6), (7, 5), (10, 4)], fill=(255, 215, 60, 255), outline=INK)
        return im
    raise KeyError(slot)
