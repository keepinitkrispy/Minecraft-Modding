// Validate Course Craft block/item JSON against Mojang's OFFICIAL schemas
// (github.com/Mojang/bedrock-samples, metadata/json_schemas).
//   git clone --depth 1 https://github.com/Mojang/bedrock-samples.git .cache/bedrock-samples
//   npm run schema
const Ajv = require("ajv"); const fs = require("fs"); const path = require("path");
const HERE = path.dirname(__dirname);
const ROOT = process.argv[2] || path.join(HERE, ".cache/bedrock-samples/metadata/json_schemas");
const PACKS = process.argv[3] || path.join(HERE, "packs");
if (!fs.existsSync(ROOT)) { console.log("Missing official schemas. Run:\n  git clone --depth 1 https://github.com/Mojang/bedrock-samples.git .cache/bedrock-samples"); process.exit(2); }
const ajv = new Ajv({ strict: false, allErrors: true, validateFormats: false, unicodeRegExp: false });
const walk = (d) => fs.readdirSync(d, { withFileTypes: true }).flatMap((e) => e.isDirectory() ? walk(path.join(d, e.name)) : e.name.endsWith(".json") ? [path.join(d, e.name)] : []);
let loaded = 0, bad = 0;
for (const f of walk(ROOT)) {
  try { const s = JSON.parse(fs.readFileSync(f, "utf8")); delete s.$schema;
    s.$id = "https://schemas.local/" + encodeURI(path.relative(ROOT, f).split(path.sep).join("/")).replace(/%25/g, "%");
    ajv.addSchema(s); loaded++; } catch { bad++; }
}
console.log(`loaded ${loaded} official schemas (${bad} skipped)`);
const tgt = [
  ["server/block/1.26.60/Blocks.json", "CourseCraft_BP/blocks"],
  ["server/item/1.26.50/ItemDocument.json", "CourseCraft_BP/items"],
];
let fail = 0;
for (const [sch, dir] of tgt) {
  const id = "https://schemas.local/" + encodeURI(sch);
  let v; try { v = ajv.getSchema(id); } catch (e) { console.log("COMPILE FAIL", sch, e.message.slice(0, 300)); fail++; continue; }
  if (!v) { console.log("MISSING", sch); fail++; continue; }
  for (const f of fs.readdirSync(path.join(PACKS, dir))) {
    const doc = JSON.parse(fs.readFileSync(path.join(PACKS, dir, f), "utf8")); const ok = v(doc["minecraft:block"] ?? doc["minecraft:item"]);
    console.log(ok ? "PASS" : "FAIL", dir + "/" + f);
    if (!ok) { fail++; for (const e of v.errors.slice(0, 8)) console.log("   ", e.instancePath, e.message, JSON.stringify(e.params).slice(0, 140)); }
  }
}
process.exit(fail ? 1 : 0);
