// Minimal in-memory stand-in for the parts of @minecraft/server Course Craft uses.
export const GameMode = { Adventure: "Adventure", Creative: "Creative", Spectator: "Spectator", Survival: "Survival" };
const signal = () => { const subs = []; return { subs, subscribe: (f) => (subs.push(f), f), fire: (e) => subs.forEach((f) => f(e)) }; };
const key = (p) => `${Math.floor(p.x)},${Math.floor(p.y)},${Math.floor(p.z)}`;

export class ItemStack { constructor(typeId, amount = 1) { this.typeId = typeId; this.amount = amount; } }

class Dimension {
  constructor(id) { this.id = id; this.blocks = new Map(); }
  getBlock(p) {
    const dim = this; const k = key(p);
    return { location: { x: Math.floor(p.x), y: Math.floor(p.y), z: Math.floor(p.z) },
      get typeId() { return dim.blocks.get(k) ?? "minecraft:air"; },
      setType(t) { if (t === "minecraft:air") dim.blocks.delete(k); else dim.blocks.set(k, t); } };
  }
}
const dims = { "minecraft:overworld": new Dimension("minecraft:overworld") };

export class Player {
  constructor(name) {
    this.id = name; this.name = name; this.location = { x: 0.5, y: 65, z: 0.5 };
    this.dimension = dims["minecraft:overworld"]; this.mode = GameMode.Survival;
    this.items = []; this.props = {}; this.messages = []; this.titles = []; this.actionbar = ""; this.knock = []; this.sounds = [];
    const self = this;
    this.onScreenDisplay = { setTitle: (t, o) => self.titles.push([t, o?.subtitle]), setActionBar: (t) => (self.actionbar = t) };
  }
  getGameMode() { return this.mode; } setGameMode(m) { this.mode = m; }
  teleport(p, o) { this.location = { ...p }; if (o?.dimension) this.dimension = o.dimension; }
  clearVelocity() {} applyKnockback(h, v) { this.knock.push([h, v]); }
  getViewDirection() { return { x: 0, y: 0, z: 1 }; }
  playSound(s) { this.sounds.push(s); } sendMessage(m) { this.messages.push(m); }
  getDynamicProperty(k) { return this.props[k]; } setDynamicProperty(k, v) { this.props[k] = v; }
  getComponent(id) { const self = this; return id === "minecraft:inventory" ? { container: { addItem: (i) => self.items.push(i) } } : undefined; }
}

const props = {};
export const players = [];
export const world = {
  afterEvents: { playerPlaceBlock: signal(), playerBreakBlock: signal(), playerSpawn: signal(), playerLeave: signal(), itemUse: signal() },
  getAllPlayers: () => players,
  getDimension: (id) => dims[id],
  getDynamicProperty: (k) => props[k],
  setDynamicProperty: (k, v) => { props[k] = v; },
};

const intervals = []; const queued = [];
export const system = {
  currentTick: 0,
  runInterval(f) { intervals.push(f); return intervals.length; },
  run(f) { queued.push(f); return queued.length; },
};
export function tick(n = 1) {
  for (let i = 0; i < n; i++) {
    while (queued.length) queued.shift()();
    system.currentTick++;
    intervals.forEach((f) => f());
  }
}
export const overworld = dims["minecraft:overworld"];
