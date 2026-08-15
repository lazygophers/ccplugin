// md.ts XSS 防线测试 — esc 的引号实体化 + 链接/图片 URL 协议白名单。
//
// 运行 (从 nextjs 项目根目录):
//   npx tsc src/lib/md.ts src/lib/__tests__/md.test.ts \
//     --outDir /tmp/mdout --module commonjs --moduleResolution node --target es2020 --esModuleInterop --skipLibCheck
//   node /tmp/mdout/__tests__/md.test.js

import { renderMd, esc } from "../md";

let pass = 0, fail = 0;
function assert(cond: boolean, msg: string) {
  if (cond) { pass++; return; }
  fail++;
  console.error(`FAIL: ${msg}`);
}

// ── 用例 1: esc 补齐引号实体 — 属性上下文里 " 和 ' 不许裸出 ──
{
  assert(esc('<a title="x\'y">') === "&lt;a title=&quot;x&#39;y&quot;&gt;",
    `esc 应实体化引号, 实际: ${esc('<a title="x\'y">')}`);
}

// ── 用例 2: javascript: 链接整条当纯文本 — 不产 <a href="javascript:..."> ──
{
  const html = renderMd("[点我](javascript:alert(1))");
  assert(!html.includes("<a href"), `javascript: 链接不该生成 <a>, 实际: ${html}`);
  assert(html.includes("javascript:alert(1)"), "非白名单 URL 应以纯文本原样可见");
}

// ── 用例 3: 白名单 URL 正常成链 — http/https/#/相对路径 ──
{
  const html = renderMd("[a](https://example.com/x) [b](/abs) [c](#anchor) [d](./rel.md) [e](docs/guide.md)");
  assert(html.includes('href="https://example.com/x"'), `https 链接应放行, 实际: ${html}`);
  assert(html.includes('href="/abs"'), `绝对路径应放行, 实际: ${html}`);
  assert(html.includes('href="#anchor"'), `锚点应放行, 实际: ${html}`);
  assert(html.includes('href="./rel.md"'), `./ 相对路径应放行, 实际: ${html}`);
  assert(html.includes('href="docs/guide.md"'), `裸相对路径应放行, 实际: ${html}`);
}

// ── 用例 4: javascript: 图片同样拒, 正常图片放行 ──
{
  const bad = renderMd("![x](javascript:alert(1))");
  assert(!bad.includes("<img"), `javascript: 图片不该生成 <img>, 实际: ${bad}`);
  const ok = renderMd("![x](https://example.com/a.png)");
  assert(ok.includes('src="https://example.com/a.png"'), `https 图片应放行, 实际: ${ok}`);
}

// ── 用例 5: data: / vbscript: 等其他 scheme 一并拒 ──
{
  for (const u of ["data:text/html,<script>alert(1)</script>", "vbscript:msgbox(1)", "JAVASCRIPT:alert(1)"]) {
    const html = renderMd(`[x](${u})`);
    assert(!html.includes("<a href"), `scheme=${u.slice(0, 12)} 不该成链, 实际: ${html}`);
  }
}

// ── 用例 6: 正文 <script> / <img onerror> 仍被 esc 吃掉 (原有防线不回退) ──
{
  const html = renderMd('<script>alert(1)</script> <img src=x onerror="alert(1)">');
  assert(!html.includes("<script>") && !html.includes("<img"), `HTML 注入应被转义, 实际: ${html}`);
  assert(html.includes("lt;script"), "转义后的可见文本应在");
}

console.log(`${pass} passed, ${fail} failed`);
if (fail > 0) process.exit(1);
