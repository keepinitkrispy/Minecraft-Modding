import { world, system, GameMode, ItemStack } from "@minecraft/server";
import { ActionFormData } from "@minecraft/server-ui";

const NS = "m3d";
const CFG = "m3d:course_v1";
const MODES = new Map();
const RUNTIME = new Map();
const CAM = new Map();
const PIPE_COOLDOWN = new Map();
const THEME = {
  grass: { floor: "m3d:grass_tile", trim: "m3d:pipe_green", detail: "m3d:coin_gold" },
  snow: { floor: "m3d:snow_tile", trim: "m3d:stone_tile", detail: "minecraft:packed_ice" },
  desert: { floor: "m3d:desert_tile", trim: "m3d:brick_red", detail: "m3d:coin_gold" },
  castle: { floor: "m3d:castle_tile", trim: "m3d:stone_tile", detail: "m3d:coin_gold" }
};
const CAMERA_MODES = ["third", "first", "top", "nw", "ne", "sw", "se"];

function say(p, message) { try { p.sendMessage("§a[Mario Maker 3D]§r " + message); } catch (_) {} }
function log(message) { console.warn("[M3D] " + message); }
function pos(v) { return {x: Math.floor(v.x), y: Math.floor(v.y), z: Math.floor(v.z)}; }
function clone(v) { return JSON.parse(JSON.stringify(v)); }
function dist(a,b) { const dx=a.x-b.x,dy=a.y-b.y,dz=a.z-b.z; return Math.sqrt(dx*dx+dy*dy+dz*dz); }
function vadd(v, dx=0, dy=0, dz=0) { return { x:v.x+dx,y:v.y+dy,z:v.z+dz }; }
function between(p,b) { return b && p.x>=b.min.x && p.x<=b.max.x && p.y>=b.min.y-3 && p.y<=b.max.y+12 && p.z>=b.min.z && p.z<=b.max.z; }
function inside2d(p,b) { return b && p.x>=b.min.x && p.x<=b.max.x && p.z>=b.min.z && p.z<=b.max.z; }
function newConfig() { return {v:1,theme:"grass",area:"main",areas:{main:null,sub:null},corners:{main:null,sub:null},start:null,objects:[],nextId:1}; }
function config() {
  try { const raw=world.getDynamicProperty(CFG); if (raw) return JSON.parse(raw); }
  catch(e) { log("configuration read "+e); }
  return newConfig();
}
function save(c) { world.setDynamicProperty(CFG, JSON.stringify(c)); }
function mode(p) { return MODES.get(p.id) || "editor"; }
function runtime(p) {
  if (!RUNTIME.has(p.id)) RUNTIME.set(p.id, {health:8,lives:5,damage:0,coins:0,stars:[],checkpoint:null,bossCleared:false,completed:false,inside:null,invulnUntil:0});
  return RUNTIME.get(p.id);
}
function editorOnly(p) { if(mode(p)!=="editor"){say(p,"Only the editor can create or modify course objects. Switch to Build mode.");return false;} return true; }
function setBlock(d,p,id) { try { const b=d.getBlock(pos(p)); if(b) b.setType(id); } catch(e) { log("block at "+JSON.stringify(pos(p))+": "+e); } }
function createBlock(d,p,id) { setBlock(d,p,id); }
function placeable(p) {
  const v=p.getViewDirection();
  return {x:Math.floor(p.location.x+v.x*4), y:Math.floor(p.location.y-1), z:Math.floor(p.location.z+v.z*4)};
}
function placeObject(p,type,extra={}) {
  if(!editorOnly(p)) return;
  const c=config(),loc=placeable(p),area=c.area;
  if(!inside2d(loc,c.areas[area])) {say(p,"Set this area's boundary corners before placing objects, or stand within its bounds.");return;}
  if(type==="star" && c.objects.filter(o=>o.type==="star").length>=3){say(p,"Exactly three green stars per course; remove an existing one to move it.");return;}
  if(type==="start") c.objects=c.objects.filter(o=>o.type!=="start");
  if(type==="boss") c.objects=c.objects.filter(o=>o.type!=="boss");
  const o={id:c.nextId++,type,area,loc,...extra};
  c.objects.push(o);
  if(type==="start")c.start=vadd(loc,0,2,0);
  save(c); drawObject(p.dimension,o,c);say(p,type+" placed at "+[loc.x,loc.y,loc.z].join(", "));
}
function drawObject(d,o,c) {
  const l=o.loc, theme=THEME[c.theme] || THEME.grass;
  switch(o.type) {
    case "start":
      for(let x=-1;x<=1;x++)for(let z=-1;z<=1;z++)setBlock(d,vadd(l,x,0,z),"minecraft:cyan_concrete");
      setBlock(d,vadd(l,0,1,0),"minecraft:light_weighted_pressure_plate");
      setBlock(d,vadd(l,-2,0,0),"minecraft:oak_sign"); break;
    case "sign": setBlock(d,l,"minecraft:oak_sign");break;
    case "pipe":
      for(let x=-1;x<=1;x++)for(let z=-1;z<=1;z++)for(let y=0;y<=2;y++) {
        if(Math.abs(x)===1||Math.abs(z)===1) setBlock(d,vadd(l,x,y,z), "m3d:pipe_green");
        else setBlock(d,vadd(l,x,y,z),"minecraft:air");
      }
      setBlock(d,vadd(l,0,0,0),"m3d:pipe_green");break;
    case "star":
      setBlock(d,l,"m3d:star_green");
      setBlock(d,vadd(l,0,1,0),"minecraft:lime_stained_glass");break;
    case "coin": setBlock(d,l,"m3d:coin_gold");break;
    case "heart": setBlock(d,l,"minecraft:red_concrete");break;
    case "checkpoint":setBlock(d,l,"minecraft:yellow_concrete");setBlock(d,vadd(l,0,1,0),"minecraft:torch");break;
    case "goal": for(let y=0;y<4;y++)setBlock(d,vadd(l,0,y,0),"m3d:coin_gold");break;
    case "enemy":setBlock(d,l,"m3d:brick_red");break;
    case "boss": for(let x=-1;x<=1;x++)for(let z=-1;z<=1;z++)setBlock(d,vadd(l,x,0,z),"minecraft:nether_bricks");break;
    case "yoshi":setBlock(d,l,"minecraft:green_wool");break;
    case "platform":
      for(let x=-3;x<=3;x++)for(let z=-3;z<=3;z++)setBlock(d,vadd(l,x,0,z),theme.floor);break;
    case "tower":
      for(let y=0;y<7;y++)for(let x=-2;x<=2;x++)for(let z=-2;z<=2;z++)
        setBlock(d,vadd(l,x,y,z),(Math.abs(x)===2||Math.abs(z)===2)?theme.trim:"minecraft:air");
      for(let x=-3;x<=3;x++)for(let z=-3;z<=3;z++)setBlock(d,vadd(l,x,7,z),theme.detail);break;
    case "arch":
      for(let x=-3;x<=3;x++)for(let y=0;y<5;y++)
        if(Math.abs(x)===3||y===4)setBlock(d,vadd(l,x,y,0),theme.trim);
      break;
  }
}
function drawAll(p) { const c=config();for(const o of c.objects)drawObject(p.dimension,o,c); }
function makePipe(p) {
  if(!editorOnly(p))return;
  const c=config(),pipes=c.objects.filter(o=>o.type==="pipe");
  const unpaired=pipes.find(o=>!o.to);
  const l=placeable(p);
  if(!inside2d(l,c.areas[c.area])){say(p,"Select a valid bounded area first.");return;}
  const o={id:c.nextId++,type:"pipe",area:c.area,loc:l,to:null};
  if(unpaired) {o.to=unpaired.id;unpaired.to=o.id;}
  c.objects.push(o);save(c);drawObject(p.dimension,o,c);
  say(p,unpaired?"Linked pipe #"+unpaired.id+" ⇄ #"+o.id+". Both directions active.":"Entrance pipe #"+o.id+" placed. Place the partner in the sub-area (or another region).");
}
function toggleArea(p) {
  if(!editorOnly(p))return;
  const c=config();c.area=c.area==="main"?"sub":"main";save(c);
  say(p,"Editing "+c.area.toUpperCase()+" area. Both areas have independent boundaries and paired pipes.");
  const b=c.areas[c.area];if(b) p.teleport({x:b.min.x+3,y:b.min.y+3,z:b.min.z+3});
}
function setCorner(p,which) {
  if(!editorOnly(p))return;
  const c=config(),area=c.area;
  if(!c.corners[area])c.corners[area]={};
  c.corners[area][which]=pos(p.location); 
  const co=c.corners[area];
  if(co.a&&co.b) {
    c.areas[area]={min:{x:Math.min(co.a.x,co.b.x),y:Math.min(co.a.y,co.b.y)-2,z:Math.min(co.a.z,co.b.z)},max:{x:Math.max(co.a.x,co.b.x),y:Math.max(co.a.y,co.b.y)+6,z:Math.max(co.a.z,co.b.z)}};
    const b=c.areas[area];
    if(b.max.x-b.min.x>96||b.max.z-b.min.z>96){say(p,"Course limits are 96×96 per area. Set nearer corners.");return;}
    say(p,area+" bounds established "+JSON.stringify(b.min)+" to "+JSON.stringify(b.max));
  } else say(p,"Saved corner "+which.toUpperCase()+" in "+area+". Set the other corner.");
  save(c);
}
function safeSpawn(d,id,at,tag) {
  try {const e=d.spawnEntity(id,vadd(at,0,2,0));if(tag)e.addTag(tag);return e;} catch(err){log("spawn "+id+": "+err);return undefined;}
}
function clearRunEnemies(d) {
  try { for(const e of d.getEntities({tags:["m3d_generated"]})) e.remove(); } catch(e){log("cleanup "+e);}
}
function setMode(p,m) {
  const c=config();
  if(m==="play" && (!c.start||!c.areas.main||c.objects.filter(x=>x.type==="star").length!==3)) {
    say(p,"Play requires a main boundary, a start pad, and exactly 3 placed green stars.");return;
  }
  MODES.set(p.id,m);
  if(m==="play"){
    const r={health:8,lives:5,damage:0,coins:0,stars:[],checkpoint:clone(c.start),bossCleared:!c.objects.some(o=>o.type==="boss"),completed:false,inside:"main",invulnUntil:0};
    RUNTIME.set(p.id,r);
    clearRunEnemies(p.dimension);
    for(const o of c.objects) {
      if(o.type==="enemy")safeSpawn(p.dimension,o.mob||"minecraft:zombie",o.loc,"m3d_generated");
      if(o.type==="boss")safeSpawn(p.dimension,"minecraft:ravager",o.loc,"m3d_generated")?.addTag("m3d_boss");
      if(o.type==="yoshi")safeSpawn(p.dimension,"m3d:yoshi",o.loc,"m3d_generated");
    }
    try { p.setGameMode(GameMode.Adventure); } catch(e) { log("play gamemode "+e); }
    try {p.camera.clear();}catch(_){}
    p.teleport(vadd(c.start,0,1,0));
    say(p,"PLAY MODE: 5 lives | 8 health | collect 3 green stars | defeat the boss | reach the goal.");
  }else{
    clearRunEnemies(p.dimension);
    try{p.setGameMode(GameMode.Creative);}catch(e){log("editor gamemode "+e);}
    say(p,"BUILD MODE: editor-only enemies, structures, stars, and Yoshi. Tap the cyan start pad or use your Maker Wand.");
  }
}
function camera(p,m) {
  CAM.set(p.id,m);if(m==="first"||m==="third")try{p.camera.setCamera("minecraft:"+ (m==="first"?"first_person":"third_person"));}catch(e){log("camera "+e);}
  say(p,"Camera "+m);
}
function updateCamera(p) {
  const kind=CAM.get(p.id)||"third";
  if(kind==="first"||kind==="third")return;
  const l=p.location;
  const offsets={top:[0,24,0,90,0],nw:[-12,15,-12,53,45],ne:[12,15,-12,53,-45],sw:[-12,15,12,53,135],se:[12,15,12,53,-135]};
  const o=offsets[kind];if(!o)return;
  try{p.camera.setCamera("minecraft:free",{location:{x:l.x+o[0],y:l.y+o[1],z:l.z+o[2]},rotation:{x:o[3],y:o[4]}});}
  catch(e){log("free camera "+e); CAM.set(p.id,"third");}
}
function enterPipe(p,pipe,c) {
  const tick=system.currentTick;if((PIPE_COOLDOWN.get(p.id)||0)>tick)return;
  if(!pipe.to){say(p,"This pipe has no linked partner. Add its exit in Build mode.");return;}
  const exit=c.objects.find(o=>o.type==="pipe"&&o.id===pipe.to);
  if(!exit){say(p,"Broken pipe link #"+pipe.to);return;}
  if(!c.areas[exit.area]){say(p,"Pipe destination area has no boundary.");return;}
  PIPE_COOLDOWN.set(p.id,tick+45);
  const r=runtime(p);r.inside=exit.area;
  p.teleport(vadd(exit.loc,0,3,2));
  say(p,"PIPE → "+exit.area.toUpperCase()+" (two-way portal #"+pipe.id+" ↔ #"+exit.id+")");
}
function hit(p,event) {
  if(mode(p)!=="play")return;
  const r=runtime(p),t=system.currentTick;
  if(t<r.invulnUntil)return;
  r.invulnUntil=t+22;
  r.health=Math.max(0,r.health-1);r.damage++;
  // Bedrock's native 20-point health is held up; the custom eight-segment meter owns lives.
  if(r.health>0) try{p.getComponent("minecraft:health")?.setCurrentValue(20);}catch(_){}
  if(r.health===0)loseLife(p);
}
function loseLife(p) {
  const c=config(),r=runtime(p);
  r.lives--;r.health=8;r.invulnUntil=system.currentTick+65;
  if(r.lives<=0) {
    say(p,"GAME OVER. Returning to Build mode.");
    setMode(p,"editor");return;
  }
  const cp=r.checkpoint||c.start;
  if(cp) {p.teleport(vadd(cp,0,2,0));try{p.getComponent("minecraft:health")?.setCurrentValue(20);}catch(_){}}
  say(p,"Lost a life. Remaining: "+r.lives);
}
function checkObjects(p,c,r) {
  const here=p.location;
  let area="main";for(const [name,b] of Object.entries(c.areas)){if(between(here,b)){area=name;break;}}
  if(!between(here,c.areas.main)&&!between(here,c.areas.sub)) {
    if(r.checkpoint) {p.teleport(vadd(r.checkpoint,0,2,0));say(p,"Returned inside course boundaries.");}
    return;
  }
  r.inside=area;
  for(const o of c.objects){
    if(o.area!==area||dist(here,vadd(o.loc,0,1,0))>2.4)continue;
    if(o.type==="star"&&!r.stars.includes(o.id)){
      r.stars.push(o.id);say(p,"GREEN STAR "+r.stars.length+"/3!");
    }
    if(o.type==="coin"&&!r["coin_"+o.id]){
      r["coin_"+o.id]=true;r.coins++;
      if(r.coins>=100){r.lives++;r.coins-=100;say(p,"1-UP!");}
    }
    if(o.type==="heart"&&!r["heart_"+o.id]){
      r["heart_"+o.id]=true;r.health=Math.min(8,r.health+2);say(p,"Health restored!");
    }
    if(o.type==="checkpoint"&&!r["checkpoint_"+o.id]){
      r["checkpoint_"+o.id]=true;r.checkpoint=vadd(o.loc,0,2,0);say(p,"Checkpoint set!");
    }
    if(o.type==="goal"&&!r.completed){
      if(r.stars.length===3&&r.bossCleared) {r.completed=true;say(p,"COURSE CLEAR! Three green stars recovered. Lives "+r.lives+" | Damage "+r.damage);}
      else sayOnce(p,"Need 3 green stars and defeat the boss to finish.",80);
    }
    if(o.type==="pipe" && p.isSneaking)enterPipe(p,o,c);
  }
}
const NOTICE = new Map();
function sayOnce(p,s,interval){const key=p.id+":"+s; if((NOTICE.get(key)||0)>system.currentTick)return;NOTICE.set(key,system.currentTick+interval);say(p,s);}
function showHUD(p) {
  if(mode(p)!=="play")return;
  const r=runtime(p);
  const fill="◆".repeat(r.health),empty="◇".repeat(8-r.health);
  try{p.onScreenDisplay.setActionBar("§aPOWER "+fill+"§7"+empty+" §f| §e×"+r.lives+" §f| §a★ "+r.stars.length+"/3 §f| §cHITS "+r.damage+" §f| §eCOINS "+r.coins+" §f| "+(r.inside||"MAIN").toUpperCase());}catch(e){log("HUD "+e);}
}
function createTutorial(p) {
  if(!editorOnly(p))return;
  const old=config(); if(old.start||old.objects.length>0){say(p,"Existing course detected. Tutorial generation is only offered for a blank course to protect work.");return;}
  const x=Math.floor(p.location.x),z=Math.floor(p.location.z),y=Math.max(88,Math.min(225,Math.floor(p.location.y)+28));
  const c=newConfig(),orig={x,y,z},sub={x:x+72,y,z};
  c.areas.main={min:vadd(orig,-2,-3,-2),max:vadd(orig,38,11,26)};
  c.areas.sub={min:vadd(sub,-2,-3,-2),max:vadd(sub,24,11,24)};
  c.start=vadd(orig,4,3,4);
  const items=[
    ["start","main",4,0,4],["sign","main",8,0,3],["star","main",12,1,5],
    ["checkpoint","main",17,1,8],["platform","main",20,0,8],["pipe","main",31,0,5],
    ["pipe","sub",4,0,5],["star","sub",9,1,8],["yoshi","sub",14,1,9],
    ["tower","sub",15,0,15],["pipe","sub",5,0,18],["pipe","main",31,0,19],
    ["star","main",23,1,19],["enemy","main",26,1,19],["boss","main",31,1,22],["goal","main",35,1,22],
    ["coin","main",7,1,4],["coin","main",15,1,8],["heart","sub",11,1,11]
  ];
  for(const [type,area,dx,dy,dz] of items) {
    const o={id:c.nextId++,type,area,loc:vadd(area==="main"?orig:sub,dx,dy,dz)};
    c.objects.push(o);
  }
  const pipes=c.objects.filter(o=>o.type==="pipe");
  pipes[0].to=pipes[1].id;pipes[1].to=pipes[0].id;
  pipes[2].to=pipes[3].id;pipes[3].to=pipes[2].id;
  save(c);
  p.teleport(vadd(orig,4,3,4));
  const d=p.dimension;
  function* build() {
    for(const [area,offset,sx,sz] of [["main",orig,38,26],["sub",sub,24,24]]) {
      if(area==="sub") {p.teleport(vadd(sub,4,3,4));for(let i=0;i<6;i++)yield;}
      for(let xx=0;xx<=sx;xx++)for(let zz=0;zz<=sz;zz++) {
        const block=(xx===0||zz===0||xx===sx||zz===sz)?"m3d:pipe_green":(xx%8===0||zz%8===0)?"m3d:stone_tile":"m3d:grass_tile";
        setBlock(d,vadd(offset,xx,0,zz),block);yield;
      }
      for(let xx=0;xx<=sx;xx++)for(let zz of [0,sz]){setBlock(d,vadd(offset,xx,1,zz),"minecraft:green_stained_glass");yield;}
      for(let zz=0;zz<=sz;zz++)for(let xx of [0,sx]){setBlock(d,vadd(offset,xx,1,zz),"minecraft:green_stained_glass");yield;}
    }
    for(const o of c.objects) {drawObject(d,o,c);yield;}
    p.teleport(vadd(orig,4,3,4));
    say(p,"COURSE 1 READY. Tap the cyan start pad for controls. Two real sub-area pipe links, 3 green stars, Yoshi, and a boss are installed.");
    log("tutorial built main/sub objects="+c.objects.length);
  }
  say(p,"Generating Tutorial Course 1 above this location. Editor/Play accessible at the cyan start pad.");
  system.runJob(build());
}
function giveWand(p) {
  try {
    const inv=p.getComponent("minecraft:inventory")?.container;
    if(inv&&!Array.from({length:inv.size},(_,i)=>inv.getItem(i)?.typeId).includes("m3d:maker_wand"))
      inv.addItem(new ItemStack("m3d:maker_wand",1));
  }catch(e){log("wand "+e);}
}
function menu(p) {
  const c=config(),r=runtime(p),label=mode(p).toUpperCase();
  const actions=[
    ["Switch to "+(mode(p)==="editor"?"PLAY":"BUILD")+" mode",()=>setMode(p,mode(p)==="editor"?"play":"editor")],
    ["Create Tutorial Course 1 (blank courses only)",()=>createTutorial(p)],
    ["Edit "+(c.area==="main"?"SUB":"MAIN")+" area",()=>toggleArea(p)],
    ["Set boundary CORNER A at feet",()=>setCorner(p,"a")],
    ["Set boundary CORNER B at feet",()=>setCorner(p,"b")],
    ["Place START PAD + sign",()=>placeObject(p,"start")],
    ["Place PIPE / pair next pipe",()=>makePipe(p)],
    ["Place GREEN STAR ("+c.objects.filter(o=>o.type==="star").length+"/3)",()=>placeObject(p,"star")],
    ["Place YOSHI (rideable)",()=>placeObject(p,"yoshi")],
    ["Place ENEMY (editor only)",()=>placeObject(p,"enemy")],
    ["Place BOSS ARENA",()=>placeObject(p,"boss")],
    ["Place GOAL",()=>placeObject(p,"goal")],
    ["Place CHECKPOINT",()=>placeObject(p,"checkpoint")],
    ["Place COIN",()=>placeObject(p,"coin")],
    ["Place HEART",()=>placeObject(p,"heart")],
    ["Prefab PLATFORM",()=>placeObject(p,"platform")],
    ["Prefab TOWER",()=>placeObject(p,"tower")],
    ["Prefab ARCH",()=>placeObject(p,"arch")],
    ["Place editable SIGN",()=>placeObject(p,"sign")],
    ["Change THEME preset",()=>themeMenu(p)],
    ["Change CAMERA angle",()=>cameraMenu(p)],
    ["Restore all course objects",()=>{if(editorOnly(p))drawAll(p);}]
  ];
  const f=new ActionFormData().title("Mario Maker 3D • "+label).body("Area "+c.area.toUpperCase()+" | 3 Stars • "+c.objects.filter(x=>x.type==="star").length+" placed\nPipes "+c.objects.filter(x=>x.type==="pipe").length+" | Lives "+r.lives+"\nBuild-only objects. In Play crouch at a pipe to travel.");
  for(const [name] of actions) f.button(name);
  f.show(p).then(res=>{if(res.canceled||res.selection===undefined)return;system.run(()=>{try{actions[res.selection]?.[1]();}catch(e){log("menu action "+e);say(p,"Action failed: "+String(e));}});}).catch(e=>log("menu "+e));
}
function themeMenu(p) {
  if(!editorOnly(p))return;
  const names=Object.keys(THEME),f=new ActionFormData().title("3D World Theme Presets").body("Themes affect newly placed prefabs and course materials.");
  names.forEach(n=>f.button(n.toUpperCase()));
  f.show(p).then(r=>{if(r.canceled||r.selection===undefined)return;const c=config();c.theme=names[r.selection];save(c);say(p,"Theme "+c.theme);}).catch(e=>log("theme UI "+e));
}
function cameraMenu(p) {
  const f=new ActionFormData().title("Course Camera").body("Third person, first person, top-down, and four diagonal overhead angles.");
  CAMERA_MODES.forEach(n=>f.button(n.toUpperCase()));
  f.show(p).then(r=>{if(!r.canceled&&r.selection!==undefined)camera(p,CAMERA_MODES[r.selection]);}).catch(e=>log("camera UI "+e));
}
world.afterEvents.playerSpawn.subscribe(e=>{
  system.runTimeout(()=>{const p=e.player; if(!p.isValid)return;giveWand(p);if(e.initialSpawn)say(p,"Tap the cyan START PAD or use the Maker Wand. Backup: /scriptevent m3d:menu");},30);
});
world.afterEvents.itemUse.subscribe(e=>{if(e.itemStack?.typeId==="m3d:maker_wand")system.run(()=>menu(e.source));});
world.afterEvents.playerInteractWithBlock.subscribe(e=>{
  const p=e.player,block=e.block;
  if(block.typeId==="minecraft:cyan_concrete") {system.run(()=>menu(p));return;}
  if(mode(p)==="play") {
    const c=config();
    const pipe=c.objects.find(o=>o.type==="pipe"&&dist(o.loc,block.location)<3);
    if(pipe)system.run(()=>enterPipe(p,pipe,c));
  }
});
world.afterEvents.entityHurt.subscribe(e=>{if(e.hurtEntity?.typeId==="minecraft:player")system.run(()=>hit(e.hurtEntity,e));});
world.afterEvents.entityDie.subscribe(e=>{
  if(e.deadEntity?.hasTag("m3d_boss"))for(const p of world.getPlayers())if(mode(p)==="play"){runtime(p).bossCleared=true;say(p,"BOSS DEFEATED! Reach the goal with all three green stars.");}
});
world.afterEvents.playerSpawn.subscribe(e=>{if(!e.initialSpawn&&mode(e.player)==="play")system.runTimeout(()=>loseLife(e.player),5);});
system.afterEvents.scriptEventReceive.subscribe(e=>{
  if(e.id==="m3d:menu"&&e.sourceEntity?.typeId==="minecraft:player")system.run(()=>menu(e.sourceEntity));
  if(e.id==="m3d:tutorial"&&e.sourceEntity?.typeId==="minecraft:player")system.run(()=>createTutorial(e.sourceEntity));
  if(e.id==="m3d:build"&&e.sourceEntity?.typeId==="minecraft:player")system.run(()=>setMode(e.sourceEntity,"editor"));
  if(e.id==="m3d:play"&&e.sourceEntity?.typeId==="minecraft:player")system.run(()=>setMode(e.sourceEntity,"play"));
});
system.runInterval(()=>{
  const c=config();
  for(const p of world.getPlayers()) {
    try {
      updateCamera(p);
      if(mode(p)==="play"){checkObjects(p,c,runtime(p));showHUD(p);}
    }catch(e){log("tick "+e);}
  }
},10);
log("script started v0.1.0");
