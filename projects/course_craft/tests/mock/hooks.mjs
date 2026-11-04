// Node module hook: redirect @minecraft/* imports to in-process mocks.
const map = {
  "@minecraft/server": new URL("./server.mjs", import.meta.url).href,
  "@minecraft/server-ui": new URL("./server-ui.mjs", import.meta.url).href,
};
export async function resolve(spec, ctx, next) {
  if (map[spec]) return { url: map[spec], shortCircuit: true };
  return next(spec, ctx);
}
