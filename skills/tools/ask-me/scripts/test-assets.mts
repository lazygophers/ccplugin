// 前端资产回归：弹层底板配色与导航条目净化。跑不了真浏览器，断言关键代码存在——
// 真实渲染由 agent-browser 截图验收兜底（2026-11-06 预览弹层透明 session）。
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

export async function test() {
  const app = await fs.readFile(fileURLToPath(new URL('../assets/app/app.js', import.meta.url)), 'utf8');
  const css = await fs.readFile(fileURLToPath(new URL('../assets/app/fallback.css', import.meta.url)), 'utf8');

  // 弹层透明修复：canvas 必须挂 .rich-text，token 由 CSS 规则兜底出主题色，
  // 游离宿主（文件预览）getComputedStyle 拷不到 token 时不再透明。
  assert.match(app, /canvas\.classList\.add\('rich-text'\)/, 'openPreview 必须给 canvas 挂 rich-text class');

  // canvas 底板取 token：--rich-bg 由 .rich-text 规则定义（fallback.css .rich-text 块）。
  assert.match(css, /\.rich-text \{[^}]*--rich-bg:/s, '.rich-text 必须定义 --rich-bg token');
  assert.match(css, /\.preview-canvas \{[^}]*background: var\(--rich-bg\)/s, '.preview-canvas 底板必须取 --rich-bg');

  // 导航条目净化：question.title 里的 markdown 链接不再原样进左栏。
  assert.match(app, /function railTitleText\(/, 'fillRailNav 必须经 railTitleText 净化标题');
  assert.match(app, /railTitleText\(question\.title\)/, 'fillRailNav 必须调用 railTitleText');
}
