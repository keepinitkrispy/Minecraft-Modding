#!/usr/bin/env python3
"""Render the exact generated Bedrock voxel geometry into approval sheets.

This renderer reads the same .geo.json and PNG files that ship in the mcaddon.
No concept art and no alternate model source are involved.
"""
from __future__ import annotations

import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
RP = DIST / "RichShorty_RP"
OUT = DIST / "previews"
OUT.mkdir(parents=True, exist_ok=True)
ENTITY_TEX = RP / "textures/entity/keepinitkrispy/rich_shorty"
BLOCK_TEX = RP / "textures/blocks/keepinitkrispy/rich_shorty"

NAMES = {
    "rich":"Rich", "shorty":"Shorty", "evil_shorty":"Evil Shorty", "bess":"Bess", "gerry":"Gerry",
    "sundae":"Sundae", "bird_dude":"Bird Dude", "scronchy":"Scronchy", "mr_needs_it":"Mr. Needs-It",
    "professor_poop":"Professor Poop", "captain_drizzle":"Captain Drizzle", "nightmare_larry":"Nightmare Larry",
    "sprocket_face":"Sprocket Face", "consensus":"Consensus", "cucumber_rich":"Cucumber Rich",
    "killer_krombo":"Killer Krombo", "shorty_jr":"Shorty Jr.", "validator_prime":"Validator Prime",
    "franky_lincolnstein":"Franky Lincolnstein", "council_rich":"Council Rich"
}


def shade(rgb, factor):
    return tuple(max(0, min(255, int(v * factor))) for v in rgb)


def cube_color(texture, uv):
    x = max(0, min(texture.width - 1, int(uv[0]) + 2))
    y = max(0, min(texture.height - 1, int(uv[1]) + 2))
    return texture.getpixel((x, y))[:3]


def project(p, scale):
    x, y, z = p
    return ((x - z) * scale, (x + z) * scale * 0.50 - y * scale)


def render_model(model_path: Path, texture_path: Path, size=(250, 280), pad=18):
    geo = json.loads(model_path.read_text(encoding="utf-8"))["minecraft:geometry"][0]
    texture = Image.open(texture_path).convert("RGBA")
    cubes = []
    all_pts = []
    for bone in geo.get("bones", []):
        for c in bone.get("cubes", []):
            ox, oy, oz = map(float, c["origin"])
            sx, sy, sz = map(float, c["size"])
            corners = [(ox+dx, oy+dy, oz+dz) for dx in (0,sx) for dy in (0,sy) for dz in (0,sz)]
            all_pts.extend(corners)
            cubes.append((c, (ox,oy,oz), (sx,sy,sz)))
    if not cubes:
        return Image.new("RGBA", size, (0,0,0,0))

    raw = [project(p, 1.0) for p in all_pts]
    minx=min(p[0] for p in raw); maxx=max(p[0] for p in raw)
    miny=min(p[1] for p in raw); maxy=max(p[1] for p in raw)
    scale=min((size[0]-2*pad)/max(1,maxx-minx),(size[1]-2*pad)/max(1,maxy-miny))
    pts=[project(p,scale) for p in all_pts]
    minx=min(p[0] for p in pts); maxx=max(p[0] for p in pts)
    miny=min(p[1] for p in pts); maxy=max(p[1] for p in pts)
    offx=(size[0]-(maxx-minx))/2-minx
    offy=(size[1]-(maxy-miny))/2-miny

    im=Image.new("RGBA", size, (20,24,29,0)); d=ImageDraw.Draw(im)
    cubes.sort(key=lambda q: (q[1][0]+q[1][2]+q[1][1]))
    for c,(x,y,z),(sx,sy,sz) in cubes:
        col=cube_color(texture,c.get("uv",[0,0]))
        def P(v):
            px,py=project(v,scale); return (px+offx,py+offy)
        top=[P((x,y+sy,z)),P((x+sx,y+sy,z)),P((x+sx,y+sy,z+sz)),P((x,y+sy,z+sz))]
        right=[P((x+sx,y,z)),P((x+sx,y+sy,z)),P((x+sx,y+sy,z+sz)),P((x+sx,y,z+sz))]
        left=[P((x,y,z+sz)),P((x+sx,y,z+sz)),P((x+sx,y+sy,z+sz)),P((x,y+sy,z+sz))]
        d.polygon(left, fill=shade(col,.72)+(255,), outline=shade(col,.45)+(255,))
        d.polygon(right, fill=shade(col,.86)+(255,), outline=shade(col,.48)+(255,))
        d.polygon(top, fill=shade(col,1.10)+(255,), outline=shade(col,.55)+(255,))
    return im


def sheet():
    cols, rows = 5, 4
    cw, ch = 270, 340
    canvas=Image.new("RGB",(cols*cw,rows*ch+90),(18,22,27)); d=ImageDraw.Draw(canvas)
    d.text((32,22),"RICH & SHORTY — ACTUAL PACK GEOMETRY / VISUAL GATE",fill=(235,240,232))
    d.text((32,50),"Rendered directly from generated .geo.json + shipped namespaced textures",fill=(142,211,183))
    for i,name in enumerate(NAMES):
        x=(i%cols)*cw; y=90+(i//cols)*ch
        d.rounded_rectangle((x+8,y+8,x+cw-8,y+ch-8),radius=12,fill=(28,34,40),outline=(61,75,82),width=2)
        model=RP/f"models/entity/{name}.geo.json"
        tex=ENTITY_TEX/f"{name}.png"
        r=render_model(model,tex,(cw-28,ch-62),12)
        canvas.paste(r,(x+14,y+10),r)
        label=NAMES[name]
        box=d.textbbox((0,0),label); tw=box[2]-box[0]
        d.text((x+(cw-tw)/2,y+ch-39),label,fill=(232,234,226))
    path=OUT/"cast_actual_geometry.png"; canvas.save(path,optimize=True); return path


def machine():
    model=RP/"models/blocks/reality_fabricator.geo.json"
    tex=BLOCK_TEX/"reality_fabricator.png"
    canvas=Image.new("RGB",(760,680),(17,21,26)); d=ImageDraw.Draw(canvas)
    d.text((28,24),"REALITY FABRICATOR — ACTUAL SHIPPING BLOCK GEOMETRY",fill=(235,240,232))
    d.text((28,50),"Same custom voxel model and material used by the add-on",fill=(142,211,183))
    r=render_model(model,tex,(700,570),24); canvas.paste(r,(30,82),r)
    path=OUT/"fabricator_actual_geometry.png"; canvas.save(path,optimize=True); return path


if __name__ == "__main__":
    a=sheet(); b=machine(); print(a); print(b)
