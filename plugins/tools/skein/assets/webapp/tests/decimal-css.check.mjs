// 小数工具类自检: node plugins/tools/skein/assets/webapp/tests/decimal-css.check.mjs
// 背景 (board-overall-progress b3): 'div.w-28.sm\\:w-44.h-1\\.5.rounded-full...' 里的 h-1\.5
// 被 tailwind 静态扫描器漏掉 —— 它一被更长的 dot-chain 前后夹住就整段扫描失败, 不像 w-28/
// sm\:w-44 那样能被单独捞出。经验证: mb-0\.5/mt-1\.5 独立出现能扫到, 嵌在链中间就不行,
// 且复现与转义与否无关 (纯 unescape 版同样漏)。于是这类小数类沿用 design.css 里 w-2\.5/
// h-2\.5/mr-1\.5/mt-0\.5 已有的手写兜底惯例, 不指望 tailwind 扫描器。
// 这里反向断言: 源码里每个 h() 小数类 (形如 mb-0\.5) 都能在 design.css ∪ tailwind.css 里查到,
// 防止只加了源码用法却忘了在任一处补 CSS 定义 (即回归本 bug)。
import { readFileSync, readdirSync } from 'fs';

const base = new URL('../src/new/', import.meta.url);
const css = readFileSync(new URL('../src/design.css', import.meta.url), 'utf8')
  + readFileSync(new URL('../src/tailwind.css', import.meta.url), 'utf8');

const files = [];
const walk = (dir) => {
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const u = new URL(e.name + (e.isDirectory() ? '/' : ''), dir);
    if (e.isDirectory()) walk(u);
    else if (e.name.endsWith('.js')) files.push(u);
  }
};
walk(base);

// 源码里写作 'mb-0\\.5' (JS 字符串字面量里 \\ 转义成 1 个反斜杠), 但文件字节层面是两个反斜杠;
// 这里直接扫文件字节, 故按两个反斜杠匹配。
const RE = /\b([a-zA-Z][a-zA-Z0-9-]*-\d+)\\\\\.(\d+)\b/g;
const used = new Set();
for (const f of files) {
  const src = readFileSync(f, 'utf8');
  for (const m of src.matchAll(RE)) used.add(`${m[1]}.${m[2]}`);
}

const missing = [...used].filter((cls) => !css.includes('.' + cls.replace('.', '\\.') + '{') && !css.includes('.' + cls.replace('.', '\\.') + ' {'));

console.log(`扫到小数工具类 ${used.size} 个, 缺失 ${missing.length} 个`);
if (missing.length) {
  console.error('缺失(补进 src/design.css, 别指望 tailwind 扫描器):\n  ' + missing.sort().join('\n  '));
  process.exit(1);
}
console.log('OK');
