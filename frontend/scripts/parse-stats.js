const fs = require('fs');
const statsPath = process.argv[2] || 'dist/ragatouille/stats.json';
if (!fs.existsSync(statsPath)) {
  console.error('stats.json not found at', statsPath);
  process.exit(2);
}
const raw = fs.readFileSync(statsPath, 'utf8');
let stats;
try {
  stats = JSON.parse(raw);
} catch (e) {
  console.error('Failed to parse JSON:', e.message);
  process.exit(2);
}
let modules = [];
if (Array.isArray(stats.modules)) {
  modules = stats.modules;
} else if (Array.isArray(stats.children)) {
  stats.children.forEach(child => {
    if (Array.isArray(child.modules)) modules = modules.concat(child.modules);
    if (Array.isArray(child.chunks)) {
      child.chunks.forEach(chunk => {
        if (Array.isArray(chunk.modules)) modules = modules.concat(chunk.modules);
      });
    }
  });
}
modules = modules.map(m => ({
  name: m.name || m.identifier || m.id || m.moduleName || '<unknown>',
  size: m.size || 0
}));
modules.sort((a, b) => b.size - a.size);
const top = modules.slice(0, 30);
console.log(`Top ${top.length} modules by size (approx, KB):`);
top.forEach((m, i) => console.log(`${i + 1}. ${(m.size / 1024).toFixed(2)} KB — ${m.name}`));

// Also print a quick summary of initial chunks if available
if (stats.chunks && Array.isArray(stats.chunks)) {
  const initialChunks = stats.chunks.filter(c => c.initial);
  const total = initialChunks.reduce((s, c) => s + (c.size || 0), 0);
  console.log(`\nInitial chunks: ${initialChunks.length}, total ~${(total/1024).toFixed(2)} KB`);
}

// Newer Angular output: some stats use an `inputs` map with `bytes` per input file.
if ((!modules || modules.length === 0) && stats.inputs && typeof stats.inputs === 'object') {
  const inputs = Object.entries(stats.inputs).map(([k, v]) => ({ name: k, size: v.bytes || v.size || 0 }));
  inputs.sort((a, b) => b.size - a.size);
  const topInputs = inputs.slice(0, 30);
  console.log(`\nTop ${topInputs.length} inputs by size (approx, KB):`);
  topInputs.forEach((m, i) => console.log(`${i + 1}. ${(m.size / 1024).toFixed(2)} KB — ${m.name}`));
  const totalBytes = inputs.reduce((s, x) => s + x.size, 0);
  console.log(`\nInputs total ~${(totalBytes/1024).toFixed(2)} KB`);
}
