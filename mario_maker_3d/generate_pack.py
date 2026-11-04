#!/usr/bin/env python3
"""Generate Mario Maker 3D Bedrock BP/RP and original 3D-world-style texture art.
Version is stable across local rebuilds; bump intentionally for new releases.
"""
from __future__ import annotations
import json, uuid, pathlib, math, random, zipfile, shutil, subprocess
from PIL import Image, ImageDraw, ImageFilter
R=pathlib.Path(__file__).resolve().parent
BP=R/"bp"; RP=R/"rp"
V=[0,1,0]; ENGINE=[1,21,80]
def j(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n")
def uuid5(x): return str(uuid.uuid5(uuid.NAMESPACE_URL,"https://github.com/keepinitkrispy/Minecraft-Modding/m3d/"+x))
bp_uuid=uuid5("behavior-pack"); rp_uuid=uuid5("resource-pack")
j(BP/"manifest.json",{
    "format_version":2,
    "header":{"name":"Mario Maker 3D — Behavior","description":"Build/Play editor, two-way pipes, 3-star courses, Yoshi and life meter","uuid":bp_uuid,"version":V,"min_engine_version":ENGINE},
    "modules":[
        {"type":"data","uuid":uuid5("behavior-data"),"version":V},
        {"type":"script","language":"javascript","entry":"scripts/main.js","uuid":uuid5("behavior-script"),"version":V}
    ],
    "dependencies":[{"uuid":rp_uuid,"version":V},{"module_name":"@minecraft/server","version":"2.0.0"},{"module_name":"@minecraft/server-ui","version":"2.0.0"}]
})
j(RP/"manifest.json",{
    "format_version":2,
    "header":{"name":"Mario Maker 3D — Art","description":"Original polished course texture atlas and custom Yoshi","uuid":rp_uuid,"version":V,"min_engine_version":ENGINE},
    "modules":[{"type":"resources","uuid":uuid5("resource-module"),"version":V}]
})
j(BP/"items"/"maker_wand.json",{
    "format_version":"1.21.70",
    "minecraft:item":{"description":{"identifier":"m3d:maker_wand","menu_category":{"category":"equipment"}},
      "components":{
       "minecraft:icon":"maker_wand","minecraft:display_name":{"value":"Course Editor Wand"},
       "minecraft:max_stack_size":1,"minecraft:hand_equipped":True,
       "minecraft:use_modifiers":{"use_duration":0.2,"movement_modifier":1.0},
       "minecraft:interact_button":"Edit Course"
      }}
})
palettes={
"grass_tile":((45,185,72),(15,119,56),(128,238,103)),
"pipe_green":((23,167,54),(8,96,37),(95,241,115)),
"stone_tile":((161,170,180),(84,102,123),(219,227,228)),
"snow_tile":((226,249,249),(120,188,226),(255,255,255)),
"desert_tile":((235,195,102),(174,115,60),(255,238,148)),
"castle_tile":((115,112,139),(57,56,80),(195,188,215)),
"star_green":((41,255,107),(10,129,60),(218,255,153)),
"coin_gold":((255,196,36),(177,93,29),(255,243,123)),
"brick_red":((204,90,66),(121,50,43),(253,163,109)),
}
def mix(a,b,t):return tuple(round(a[k]*(1-t)+b[k]*t) for k in range(3))
random.seed(64)
def tile(name, colors):
    base,dark,light=colors
    im=Image.new("RGB",(64,64)); pix=im.load()
    for y in range(64):
      for x in range(64):
        # Beveled, slightly pearlescent cartoon tile with tile grout and tiny specular texture
        edge=min(x,y,63-x,63-y)
        noise=random.randrange(-9,10)
        t=max(0.0,min(1.0,0.14+(.23 if x+y<50 else 0.05)+(0.28 if edge>4 and (x%13 in (1,2)) else 0)))
        c=mix(base,light,t)
        if edge<=2:c=mix(c,dark,0.73)
        elif edge<=5:c=mix(c,dark,0.17)
        if x>52 or y>54:c=mix(c,dark,0.16)
        if (x*31+y*19)%173<3:c=mix(c,light,0.35)
        pix[x,y]=tuple(max(0,min(255,k+noise)) for k in c)
    # Subtle little geometry details, intentionally original rather than ripped assets
    d=ImageDraw.Draw(im)
    if name.endswith("tile"):
      d.line((8,8,54,8), fill=mix(light,base,0.38), width=2)
      d.line((9,8,9,54), fill=mix(light,base,0.55), width=2)
    if name=="pipe_green":
      d.rounded_rectangle((7,7,56,56),radius=7,outline=mix(light,base,0.25),width=3)
      d.line((12,20,12,42),fill=light,width=2)
    if name=="coin_gold":
      d.ellipse((9,9,54,54),fill=base,outline=dark,width=5)
      d.arc((17,17,45,45),-30,160,fill=light,width=5)
    if name=="star_green":
      points=[]
      for i in range(10):
        angle=-math.pi/2+i*math.pi/5;rad=26 if i%2==0 else 11
        points.append((round(31+math.cos(angle)*rad),round(32+math.sin(angle)*rad)))
      d.polygon(points,fill=base)
      d.line(points+[points[0]],fill=light,width=3,joint="curve")
      d.ellipse((19,25,23,29),fill=(4,63,25))
      d.ellipse((38,25,42,29),fill=(4,63,25))
    im.save(RP/"textures"/"blocks"/(name+".png"))
(RP/"textures"/"blocks").mkdir(parents=True,exist_ok=True)
for n,c in palettes.items(): tile(n,c)
j(RP/"textures"/"terrain_texture.json", {
    "resource_pack_name":"m3d","texture_name":"atlas.terrain",
    "texture_data":{n:{"textures":"textures/blocks/"+n} for n in palettes}
})
for n in palettes:
    j(BP/"blocks"/(n+".json"),{
        "format_version":"1.21.80",
        "minecraft:block":{"description":{"identifier":"m3d:"+n,"menu_category":{"category":"construction"}},
          "components":{
            "minecraft:geometry":"minecraft:geometry.full_block",
            "minecraft:material_instances":{"*":{"texture":n,"render_method":"opaque"}},
            "minecraft:destructible_by_mining":{"seconds_to_destroy":0.6},
            "minecraft:map_color":"#55c864"
          }}
    })
# Original small Yoshi-style dinosaur: recognizable snout, cheeks, belly, saddle, feet, eyes and dorsal plates
j(BP/"entities"/"yoshi.json",{
  "format_version":"1.21.0",
  "minecraft:entity":{
   "description":{"identifier":"m3d:yoshi","is_spawnable":True,"is_summonable":True,"is_experimental":False},
   "components":{
    "minecraft:type_family":{"family":["m3d_yoshi","animal","mob"]},
    "minecraft:collision_box":{"width":0.95,"height":1.65},
    "minecraft:health":{"value":20,"max":20},
    "minecraft:movement":{"value":0.34},
    "minecraft:movement.basic":{},
    "minecraft:jump.static":{},
    "minecraft:navigation.walk":{},
    "minecraft:physics":{},
    "minecraft:input_ground_controlled":{},
    "minecraft:rideable":{"seat_count":1,"family_types":["player"],"interact_text":"action.interact.mount","seats":[{"position":[0,1.42,-0.10]}]},
    "minecraft:pushable":{"is_pushable":True,"is_pushable_by_piston":True},
    "minecraft:behavior.float":{"priority":1}
   }
  }
})
j(RP/"entity"/"yoshi.entity.json",{
    "format_version":"1.10.0",
    "minecraft:client_entity":{"description":{
      "identifier":"m3d:yoshi",
      "materials":{"default":"entity_alphatest"},
      "textures":{"default":"textures/entity/yoshi"},
      "geometry":{"default":"geometry.m3d.yoshi"},
      "render_controllers":["controller.render.m3d.yoshi"],
      "spawn_egg":{"base_color":"#3ad560","overlay_color":"#ff9b32"}
    }}
})
j(RP/"render_controllers"/"yoshi.render.json",{
  "format_version":"1.8.0",
  "render_controllers":{"controller.render.m3d.yoshi":{"geometry":"Geometry.default","materials":[{"*":"Material.default"}],"textures":["Texture.default"]}}
})
# Atlas: face patches can each sample 4x4 through 24x24 pixels, with little dimples/highlights.
atlas=Image.new("RGBA",(128,128),(58,195,82,255)); d=ImageDraw.Draw(atlas)
d.rectangle((0,0,63,63),fill=(64,196,80,255))
d.rectangle((64,0,127,63),fill=(238,240,196,255))
d.rectangle((0,64,63,95),fill=(238,143,54,255))
d.rectangle((64,64,127,95),fill=(245,248,249,255))
d.rectangle((0,96,63,127),fill=(34,142,56,255))
d.rectangle((64,96,127,127),fill=(236,104,68,255))
for i in range(14):
    x=random.randrange(5,60);y=random.randrange(5,60)
    d.ellipse((x,y,x+3,y+3),fill=(94,226,112,255))
d.rectangle((80,67,91,86),fill=(17,22,23,255))
d.rectangle((104,67,115,86),fill=(17,22,23,255))
d.rectangle((80,68,85,72),fill=(255,255,255,255))
d.rectangle((104,68,109,72),fill=(255,255,255,255))
(RP/"textures"/"entity").mkdir(parents=True,exist_ok=True)
atlas.save(RP/"textures"/"entity"/"yoshi.png")
def cube(origin,size,uv): return {"origin":origin,"size":size,"uv":uv}
bones=[
 {"name":"body","pivot":[0,11,0],"cubes":[cube([-5,7,-4],[10,10,10],[0,0]),cube([-4,8,-5],[8,8,2],[64,0])]},
 {"name":"head","pivot":[0,18,-4],"cubes":[cube([-5,17,-9],[10,9,9],[0,0]),cube([-5,17,-14],[10,5,6],[0,0]),cube([-3,15,-12],[6,3,4],[64,0])]},
 {"name":"left_eye","pivot":[-3,24,-5],"cubes":[cube([-5,23,-10],[4,7,4],[64,64])]},
 {"name":"right_eye","pivot":[3,24,-5],"cubes":[cube([1,23,-10],[4,7,4],[64,64])]},
 {"name":"saddle","pivot":[0,16,1],"cubes":[cube([-5,17,0],[10,2,8],[0,64])]},
 {"name":"tail","pivot":[0,11,5],"cubes":[cube([-3,11,5],[6,5,8],[0,96])]},
 {"name":"left_arm","pivot":[-5,16,-3],"cubes":[cube([-8,10,-5],[4,8,5],[0,0])]},
 {"name":"right_arm","pivot":[5,16,-3],"cubes":[cube([4,10,-5],[4,8,5],[0,0])]},
 {"name":"left_leg","pivot":[-4,7,3],"cubes":[cube([-6,0,0],[5,8,8],[0,64])]},
 {"name":"right_leg","pivot":[4,7,3],"cubes":[cube([1,0,0],[5,8,8],[0,64])]},
]
for i in range(3):
 bones.append({"name":"spine"+str(i),"pivot":[0,16,1+i*2],
      "cubes":[cube([-1,17-i,2+i*2],[3,5,3],[64,96])]})
j(RP/"models"/"entity"/"yoshi.geo.json",{
 "format_version":"1.12.0","minecraft:geometry":[{
  "description":{"identifier":"geometry.m3d.yoshi","texture_width":128,"texture_height":128,"visible_bounds_width":3,"visible_bounds_height":3.2,"visible_bounds_offset":[0,1.5,0]},
  "bones":bones
 }]
})
# High-contrast wand icon
im=Image.new("RGBA",(64,64),(0,0,0,0));d=ImageDraw.Draw(im)
d.polygon([(11,43),(20,52),(52,16),(43,9)],fill=(242,198,80,255),outline=(120,67,20,255),width=2)
d.polygon([(45,2),(51,13),(63,16),(53,24),(53,37),(43,29),(31,31),(34,18),(27,9),(40,9)],fill=(53,246,91,255),outline=(19,119,52,255),width=2)
(RP/"textures"/"items").mkdir(parents=True,exist_ok=True);im.save(RP/"textures"/"items"/"maker_wand.png")
j(RP/"textures"/"item_texture.json",{
 "resource_pack_name":"m3d","texture_name":"atlas.items","texture_data":{"maker_wand":{"textures":"textures/items/maker_wand"}}
})
j(RP/"texts"/"languages.json",["en_US"])
(RP/"texts"/"en_US.lang").write_text("item.m3d:maker_wand.name=Course Editor Wand\nentity.m3d:yoshi.name=Yoshi\n")
# Create a reproducible, auditable zip.
OUT=R/"MarioMaker3D.mcaddon"
with zipfile.ZipFile(OUT,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for base,label in [(BP,"MarioMaker3D_BP"),(RP,"MarioMaker3D_RP")]:
    for path in sorted(base.rglob("*")):
      if path.is_file() and not path.name.startswith("."):
        z.write(path,str(path.relative_to(base.parent)).replace(base.name,label,1))
print(f"Built {OUT} ({OUT.stat().st_size} bytes, {len(zipfile.ZipFile(OUT).namelist())} entries)")
