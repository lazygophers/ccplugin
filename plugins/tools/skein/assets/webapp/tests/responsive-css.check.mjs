// 响应式类自检: node plugins/tools/skein/assets/webapp/tests/responsive-css.check.mjs
// 源码里 h() 的响应式类写作 'div.lg\\:grid-cols-3'; tailwind 扫描器按字面看不认 → 需 config 的
// content.transform 脱转义。这里反向断言: 源码用到的每个断点类都在预构建 src/tailwind.css 里。
import { readFileSync, readdirSync } from 'fs';

const base = new URL('../src/new/', import.meta.url);
const css = readFileSync(new URL('../src/tailwind.css', import.meta.url), 'utf8');

const files = [];
const walk = (dir) => {
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const u = new URL(e.name + (e.isDirectory() ? '/' : ''), dir);
    if (e.isDirectory()) walk(u);
    else if (e.name.endsWith('.js')) files.push(u);
  }
};
walk(base);

// 'div.lg\\:grid-cols-3.gap-6' → 源码文本是 lg\\:grid-cols-3
const RE = /\b(sm|md|lg|xl|2xl)\\+:([a-zA-Z0-9\-[\]/%_]+)/g;
const used = new Set();
for (const f of files) {
  const src = readFileSync(f, 'utf8');
  for (const m of src.matchAll(RE)) used.add(`${m[1]}:${m[2]}`);
}

const missing = [...used].filter((cls) => {
  // CSS 里 : 与 / 转义为 \: \/
  const esc = '.' + cls.replace(/[:/.]/g, (c) => '\\' + c);
  return !css.includes(esc);
});

console.log(`扫到响应式类 ${used.size} 个, 缺失 ${missing.length} 个`);
if (missing.length) {
  console.error('缺失(重跑 tailwind 生成):\n  ' + missing.sort().join('\n  '));
  process.exit(1);
}
console.log('OK');
