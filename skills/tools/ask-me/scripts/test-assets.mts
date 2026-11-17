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

  // 中文路径链接：marked 对 href 做 encodeURI，rewriteLocalLinks 必须解码回文件系统
  // 原样；裸 % 不是编码串，解码抛 URIError 时保留原样（try/catch 兜底，不能裸调用）。
  assert.match(
    app,
    /try \{\s*target = decodeURIComponent\(target\);\s*\} catch \{\}/,
    'rewriteLocalLinks 必须解码 href 且带 URIError 兜底',
  );

  // 预览初始适配必须等图片加载完再算：img 未 complete 时 fitScale 量到旧尺寸，
  // 缩放会超出屏幕。图片 load 后补适配，用户已手动缩放/拖动（manuallyAdjusted）
  // 时不再覆盖其操作。
  assert.match(app, /image\.addEventListener\('load', fitLoadedImages, \{ once: true \}\)/, '克隆体里的 img 必须挂一次性 load 监听补适配');
  assert.match(app, /const fitLoadedImages = \(\) => \{/, '必须用 fitLoadedImages 统一初始与图片加载后的适配');
  assert.match(app, /if \(manuallyAdjusted \|\| images\.some\(\(image\) => !image\.complete\)\) return;/, 'fitLoadedImages 必须在用户手动操作后或图片未加载完时跳过');
  assert.match(app, /manuallyAdjusted = true;\s*const clamped = Math\.min\(8, Math\.max\(0\.2, next\)\);/, 'zoomTo 必须标记用户已手动缩放');
}
