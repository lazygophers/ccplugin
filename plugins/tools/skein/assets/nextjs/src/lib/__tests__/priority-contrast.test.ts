// 优先级色对比度回归 — 从 globals.css 实际解析四档 x 两主题终值, 按 WCAG 相对亮度公式算对比度。
// 不硬编码具体色值 (调色一次就红), 只钉住"可计算的外部属性":
//   1) 四档 x 两主题对比度均 >= 4.5 (WCAG AA 正文级)
//   2) 每个主题内四档色值两两不等 (不能出现两档撞色)
//   3) PRIORITY_COLOR_VAR (model.ts) 零处引用 --st-* (优先级色与状态色语义独立)
//
// 运行 (从 nextjs 项目根目录):
//   npx tsc src/lib/__tests__/priority-contrast.test.ts --outDir /tmp/pcout \
//     --module commonjs --moduleResolution node --target es2020 --esModuleInterop --skipLibCheck
//   node /tmp/pcout/priority-contrast.test.js

import * as fs from "fs";
import * as path from "path";
import { PRIORITY_COLOR_VAR } from "../model";

let pass = 0, fail = 0;
function assert(cond: boolean, msg: string) {
  if (cond) { pass++; return; }
  fail++;
  console.error(`FAIL: ${msg}`);
}

const CSS_PATH = path.join(process.cwd(), "src/app/globals.css");
const css = fs.readFileSync(CSS_PATH, "utf8");

// ── 解析 oc-* 色板 (--oc-xxx-nnn: #hex;) ──
const ocColors: Record<string, string> = {};
for (const m of css.matchAll(/--(oc-[\w-]+):\s*(#[0-9A-Fa-f]{6})/g)) {
  ocColors[m[1]] = m[2];
}

// ── 提取 :root 与 .dark 两个块的原文 (按大括号配对取第一层) ──
function extractBlock(selector: string): string {
  const idx = css.indexOf(selector);
  assert(idx !== -1, `globals.css 应含 ${selector} 选择器`);
  const braceStart = css.indexOf("{", idx);
  let depth = 1, i = braceStart + 1;
  while (depth > 0 && i < css.length) {
    if (css[i] === "{") depth++;
    else if (css[i] === "}") depth--;
    i++;
  }
  return css.slice(braceStart + 1, i - 1);
}

const rootBlock = extractBlock(":root");
const darkBlock = extractBlock(".dark {");

const PRI_KEYS = ["urgent", "high", "normal", "low"] as const;

// 解析某主题块内四档 --pri-xxx 的最终 hex (支持 var(--oc-xxx) 间接引用, 或直接 hex)
function resolvePriColors(block: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const key of PRI_KEYS) {
    const re = new RegExp(`--pri-${key}:\\s*([^;]+);`);
    const m = block.match(re);
    assert(!!m, `--pri-${key} 应在该主题块内定义`);
    if (!m) continue;
    const raw = m[1].trim();
    const varMatch = raw.match(/var\(--(oc-[\w-]+)\)/);
    if (varMatch) {
      const hex = ocColors[varMatch[1]];
      assert(!!hex, `--pri-${key} 引用的 ${varMatch[1]} 应在 oc 色板中存在`);
      out[key] = hex || "";
    } else {
      const hexMatch = raw.match(/#[0-9A-Fa-f]{6}/);
      assert(!!hexMatch, `--pri-${key} 的值应是 hex 或 var(--oc-*) 引用, 实际: ${raw}`);
      out[key] = hexMatch ? hexMatch[0] : "";
    }
  }
  return out;
}

const rootPri = resolvePriColors(rootBlock);
const darkPri = resolvePriColors(darkBlock);

// ── WCAG 相对亮度 / 对比度 ──
function hexToRgb(hex: string): [number, number, number] {
  const n = parseInt(hex.replace("#", ""), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
function relLuminance(hex: string): number {
  const [r, g, b] = hexToRgb(hex).map(v => v / 255);
  const lin = (c: number) => (c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
  const [rl, gl, bl] = [lin(r), lin(g), lin(b)];
  return 0.2126 * rl + 0.7152 * gl + 0.0722 * bl;
}
function contrastRatio(hexA: string, hexB: string): number {
  const la = relLuminance(hexA), lb = relLuminance(hexB);
  const [lighter, darker] = la >= lb ? [la, lb] : [lb, la];
  return (lighter + 0.05) / (darker + 0.05);
}

const LIGHT_BG = "#FFFFFF";
const DARK_BG = "#1A2E42";
const AA_MIN = 4.5;

// ── 断言 1: 四档 x 两主题对比度均达标 ──
for (const key of PRI_KEYS) {
  const lr = contrastRatio(rootPri[key], LIGHT_BG);
  assert(lr >= AA_MIN, `light/${key} 对比度 ${lr.toFixed(2)} 应 >= ${AA_MIN} (色值 ${rootPri[key]})`);
  const dr = contrastRatio(darkPri[key], DARK_BG);
  assert(dr >= AA_MIN, `dark/${key} 对比度 ${dr.toFixed(2)} 应 >= ${AA_MIN} (色值 ${darkPri[key]})`);
}

// ── 断言 2: 每个主题内四档色值两两不等 ──
for (const [label, priMap] of [["light", rootPri], ["dark", darkPri]] as const) {
  const values = PRI_KEYS.map(k => priMap[k]);
  const unique = new Set(values);
  assert(unique.size === values.length, `${label} 主题四档优先级色应两两不等, 实际: ${values.join(", ")}`);
}

// ── 断言 3: PRIORITY_COLOR_VAR 零处引用 --st-* ──
for (const [pri, varName] of Object.entries(PRIORITY_COLOR_VAR)) {
  assert(!varName.startsWith("--st-"), `PRIORITY_COLOR_VAR.${pri} 不应引用状态色变量 --st-*, 实际: ${varName}`);
  assert(varName.startsWith("--pri-"), `PRIORITY_COLOR_VAR.${pri} 应引用 --pri-* 变量, 实际: ${varName}`);
}

console.log(`${pass} passed, ${fail} failed`);
if (fail > 0) process.exit(1);
