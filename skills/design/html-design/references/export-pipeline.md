# 导出管线 · HTML → 目标格式

HTML 先行，导出是机械步骤。所有导出合一键命令，禁让用户手动多步。

## 目标格式与方法

| 目标 | 方法 |
|------|------|
| PNG | headless Chrome / Puppeteer，固定 viewport 截图 |
| SVG | 内联 SVG 直接存盘，或从 HTML 抽出 `<svg>` |
| PDF | HTML print CSS + 浏览器打印 / Puppeteer `page.pdf()` |
| 幻灯片放映 | HTML 本身即放映物（全屏 + 键盘翻页） |
| 微信图文 | HTML 内联样式粘贴；外链转底部引用 |

## Puppeteer 截图（PNG）

```js
// screenshot.js — 单图导出
import puppeteer from 'puppeteer';
const [url, out, w, h] = process.argv.slice(2);
const browser = await puppeteer.launch();
const page = await browser.newPage();
await page.setViewport({ width: +w, height: +h, deviceScaleFactor: 2 });
await page.goto(url, { waitUntil: 'networkidle0' });
await page.screenshot({ path: out, clip: { x:0, y:0, width:+w, height:+h } });
await browser.close();
```

运行：`node screenshot.js file://./cover.html cover.png 1280 720`

## 批量截图（系列卡片 / 多图）

```js
// batch.js — 遍历目录批量截
import puppeteer from 'puppeteer';
import { glob } from 'glob';

const browser = await puppeteer.launch();
for (const f of await glob('cards/*.html')) {
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1440, deviceScaleFactor: 2 });
  await page.goto('file://' + process.cwd() + '/' + f, { waitUntil:'networkidle0' });
  await page.screenshot({ path: f.replace('.html','.png') });
  await page.close();
}
await browser.close();
```

复用同一个 browser 实例，比每次 launch 快数倍。

## PDF 导出

```js
import puppeteer from 'puppeteer';
const [url, out] = process.argv.slice(2);
const browser = await puppeteer.launch();
const page = await browser.newPage();
await page.goto(url, { waitUntil: 'networkidle0' });
await page.pdf({ path: out, format: 'A4', printBackground: true, margin: { top:'20mm', bottom:'20mm', left:'15mm', right:'15mm' } });
await browser.close();
```

需 `print-color-adjust: exact` 才能保留背景色。

## SVG 抽取

HTML 中的内联 SVG 可直接整段存为 `.svg` 文件（补 `xmlns`）：

```js
// 从 html 提取所有 <svg> 存盘
import fs from 'fs';
const html = fs.readFileSync('diagram.html','utf8');
const svgs = html.match(/<svg[\s\S]*?<\/svg>/g) || [];
svgs.forEach((s,i) => {
  const fixed = s.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"');
  fs.writeFileSync(`export-${i}.svg`, fixed);
});
```

## 等待策略

截图 / 导 PDF 前等页面就绪：

- 静态内容：`waitUntil: 'networkidle0'`（500ms 无请求）
- 有字体加载：加 `await page.evaluateHandle('document.fonts.ready')`
- 有动画：截图前 `await new Promise(r=>setTimeout(r, 500))` 让首帧定住
- 有异步数据：等特定元素 `await page.waitForSelector('.ready')`

## 一键命令约定

每个产物根目录给一个 `export.sh`（或 Makefile target），用户跑一条命令拿全部导出物：

```bash
#!/usr/bin/env bash
# export.sh — 系列卡片 + 封面 一键导出
set -e
node batch.js                    # cards/*.html → cards/*.png
node screenshot.js file://./cover.html cover.png 1280 720
echo "✅ 导出完成 → cards/*.png, cover.png"
```

规则：
- 导出脚本随产物一起交付，不依赖本 skill 目录的全局脚本
- 依赖（puppeteer）写进产物 `package.json`，`npm i` 即装
- 脚本幂等：重复跑不产生副作用
