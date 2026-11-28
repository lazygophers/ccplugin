// show-me 自测：node skills/tools/show-me/scripts/self-test.mjs
// 只写 os.tmpdir() 下的临时目录，结束删除；系统级配置经 SHOW_ME_HOME 重定向；不打开浏览器
import { test, after } from "node:test"
import assert from "node:assert/strict"
import { existsSync, mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync, realpathSync, statSync } from "node:fs"
import { tmpdir } from "node:os"
import { dirname, join } from "node:path"
import { execFile, spawnSync } from "node:child_process"
import { deflateSync, crc32 } from "node:zlib"
import { fileURLToPath } from "node:url"
import * as sm from "./show-me.mjs"

const CLI = join(dirname(fileURLToPath(import.meta.url)), "show-me.mjs")
const TMP = realpathSync(mkdtempSync(join(tmpdir(), "show-me-test-")))
after(() => rmSync(TMP, { recursive: true, force: true }))

let n = 0
// 每个用例一套独立的项目根与系统级目录
function sandbox({ system, project } = {}) {
  const base = join(TMP, "case" + ++n), root = join(base, "proj"), home = join(base, "home")
  mkdirSync(join(root, ".claude", ".show-me"), { recursive: true })
  mkdirSync(home, { recursive: true })
  writeFileSync(join(home, "config.json"), JSON.stringify({ open: false, ...system }))
  if (project) writeFileSync(join(root, ".claude", ".show-me", "config.json"), JSON.stringify(project))
  return { base, root, home, env: { ...process.env, SHOW_ME_HOME: home } }
}
const run = (sb, args) => spawnSync(process.execPath, [CLI, ...args], { cwd: sb.root, env: sb.env, encoding: "utf8" })

const CONTENT = {
  topic: "demo", type: "explain", title: "示例页", subtitle: "自测",
  summary: { point: "一句话结论", text: "摘要段落，用于检验零宽字符写入。", points: ["要点一"] },
  blocks: [
    { type: "heading", text: "第一节" },
    { type: "paragraph", text: "正文段落一。" },
    { type: "flow", caption: "流程", nodes: [{ id: "a", label: "甲", detail: "a" }, { id: "b", label: "乙", detail: "b" }] },
    { type: "table", caption: "表", columns: ["键", "值"], rows: [["k", "v"]] },
    { type: "chart", caption: "图", unit: "ms", series: [{ key: "p50", label: "P50" }], data: [{ stage: "x", p50: 1 }] },
    { type: "code", caption: "代码", lang: "bash", filename: "a.sh", code: "echo hi" },
    { type: "steps", items: [{ title: "一", detail: "做事" }] },
  ],
  references: [{ text: "规格", source: "spec-v2.md" }],
}
function writeContent(sb, patch = {}) {
  const f = join(sb.root, "content.json")
  writeFileSync(f, JSON.stringify({ ...CONTENT, ...patch }))
  return f
}
const pageData = html => JSON.parse(/<script type="application\/json" id="page-data">([\s\S]*?)<\/script>/.exec(html)[1])

test("配置：项目级 > 系统级 > 默认，对象逐键合并，数组/字符串整体替换", () => {
  const sb = sandbox({
    system: { style: "terminal", author: { name: "落心", url: "https://example.com/u" }, watermark: { visible: { text: "系统 · {date}" } } },
    project: { watermark: { visible: { text: "内部资料 · {date}" } }, byType: { explain: "sketch" } },
  })
  const { config, sources } = sm.loadConfig({ cwd: sb.root, env: sb.env })
  assert.equal(config.style, "terminal"); assert.equal(sources.style, "system")
  assert.equal(config.author.name, "落心"); assert.equal(sources["author.name"], "system")
  assert.equal(config.watermark.visible.text, "内部资料 · {date}"); assert.equal(sources["watermark.visible.text"], "project")
  assert.equal(config.watermark.visible.opacity, 0.06); assert.equal(sources["watermark.visible.opacity"], "default")
  assert.equal(config.byType.explain, "sketch"); assert.equal(sources["byType.explain"], "project")
  assert.equal(config.open, false)
})

test("风格决定顺序：--style > 内容 style > byType[type] > style > paper", () => {
  const sb = sandbox({ system: { style: "terminal" }, project: { byType: { explain: "sketch" } } })
  const f = writeContent(sb)
  const r1 = JSON.parse(run(sb, ["render", f, "--no-open"]).stdout); assert.equal(r1.style, "sketch")
  writeContent(sb, { type: "report" })
  assert.equal(JSON.parse(run(sb, ["render", f, "--no-open"]).stdout).style, "terminal")
  writeContent(sb, { style: "paper" })
  assert.equal(JSON.parse(run(sb, ["render", f, "--no-open"]).stdout).style, "paper")
  assert.equal(JSON.parse(run(sb, ["render", f, "--no-open", "--style", "terminal"]).stdout).style, "terminal")
  const bare = sandbox()
  assert.equal(JSON.parse(run(bare, ["render", writeContent(bare), "--no-open"]).stdout).style, "paper")
})

test("null 表示用下一层的值", () => {
  const sb = sandbox({ system: { style: "terminal", author: { name: "系统署名" } }, project: { style: null, author: { name: null } } })
  const { config, sources } = sm.loadConfig({ cwd: sb.root, env: sb.env })
  assert.equal(config.style, "terminal"); assert.equal(sources.style, "system")
  assert.equal(config.author.name, "系统署名")
})

test("未知键、类型不符：报错含文件路径、键名、期望类型，退出码非 0", () => {
  const sb = sandbox({ project: { colour: "red", open: "yes", watermark: { visible: { opacity: 2 } }, byType: { blog: "paper" } } })
  const r = run(sb, ["render", writeContent(sb), "--no-open"])
  assert.equal(r.status, 2)
  const pf = join(sb.root, ".claude", ".show-me", "config.json")
  assert.match(r.stderr, new RegExp(pf.replace(/[.*+?^$()|[\]\\{}]/g, "\\$&") + ": colour: 未知键"))
  assert.match(r.stderr, /: open: 期望 boolean，实际 string/)
  assert.match(r.stderr, /: watermark\.visible\.opacity: 期望 number 0–1/)
  assert.match(r.stderr, /: byType\.blog: 未知键/)
  const s2 = sandbox({ system: { style: "neon" } })
  const r2 = run(s2, ["config"])
  assert.equal(r2.status, 2); assert.match(r2.stderr, /config\.json: style: 期望 paper \| sketch \| terminal，实际 string "neon"/)
})

test("项目级路径越界拒绝：logo 在项目根外、outDir 指向项目根外", () => {
  const sb = sandbox({ project: { logo: "../outside.png" } })
  writeFileSync(join(sb.base, "outside.png"), "x")
  const r = run(sb, ["render", writeContent(sb), "--no-open"])
  assert.equal(r.status, 2); assert.match(r.stderr, /logo: 路径必须在项目根/)
  const s2 = sandbox({ project: { logo: "missing.png" } })
  assert.match(run(s2, ["config"]).stderr, /logo: 文件不存在/)
  const s3 = sandbox({ project: { outDir: "../../out/{topic}" } })
  const r3 = run(s3, ["render", writeContent(s3), "--no-open"])
  assert.equal(r3.status, 2); assert.match(r3.stderr, /outDir: 不得指向项目根/)
})

test("版本递增：同目录已有 v1..vN 写 vN+1，v≥2 带上一版文件名与变更块", () => {
  const sb = sandbox()
  const f = writeContent(sb, { changes: ["改了一处"] })
  const r1 = JSON.parse(run(sb, ["render", f, "--no-open"]).stdout)
  assert.equal(r1.version, 1); assert.equal(r1.path, join(sb.root, ".scratch", "demo", "reports", "demo-v1.html"))
  const p1 = pageData(readFileSync(r1.path, "utf8"))
  assert.equal(p1.showme.prev, undefined); assert.equal(p1.changes, undefined)
  const r2 = JSON.parse(run(sb, ["render", f, "--no-open"]).stdout)
  assert.equal(r2.version, 2); assert.match(r2.path, /demo-v2\.html$/)
  const p2 = pageData(readFileSync(r2.path, "utf8"))
  assert.equal(p2.showme.prev, "demo-v1.html"); assert.deepEqual(p2.changes, ["改了一处"]); assert.equal(p2.meta.version, 2)
})

test("页脚左段锁定：版本取 SKILL.md，仓库地址在模板内写死，配置无对应键", () => {
  const ver = /^version:\s*(\S+)/m.exec(readFileSync(join(dirname(CLI), "..", "SKILL.md"), "utf8"))[1]
  const sb = sandbox()
  const r = JSON.parse(run(sb, ["render", writeContent(sb), "--no-open"]).stdout)
  const html = readFileSync(r.path, "utf8")
  assert.equal(pageData(html).showme.version, ver)
  const tpl = readFileSync(sm.TEMPLATE, "utf8")
  assert.match(tpl, /name:\s*[`"']show-me[`"'],\s*repo:\s*[`"']github\.com\/lazygophers\/ccplugin[`"']/, "模板写死 skill 名与仓库地址")
  for (const k of ["footer", "skill", "repo"]) {
    const s = sandbox({ project: { [k]: "x" } })
    assert.match(run(s, ["config"]).stderr, new RegExp(k + ": 未知键"))
  }
})

test("零宽字符编码解码往返；产物在关闭 meta 时仍可从零宽字符解出", () => {
  const p = { id: "x-1", author: "落心", version: 3, time: "2026-11-28T00:00:00.000Z" }
  const zw = sm.zwEncode(JSON.stringify(p))
  assert.match(zw, /^[⁠​‌]+$/)
  assert.deepEqual(sm.zwDecode("前文" + zw + "后文"), p)
  const sb = sandbox({ system: { watermark: { hidden: { meta: false } } } })
  const r = JSON.parse(run(sb, ["render", writeContent(sb), "--no-open"]).stdout)
  const html = readFileSync(r.path, "utf8")
  assert.ok(!html.includes('name="show-me:id"'))
  const para = pageData(html).blocks.find(b => b.type === "paragraph").text
  const d = sm.decode(Buffer.from(para))
  assert.equal(d.via, "zero-width"); assert.equal(d.payload.version, 1)
  const full = sandbox()
  const r2 = JSON.parse(run(full, ["render", writeContent(full), "--no-open"]).stdout)
  const dec = run(full, ["decode", r2.path])
  assert.equal(dec.status, 0)
  const out = JSON.parse(dec.stdout)
  assert.equal(out.via, "meta"); assert.equal(out.payload.author, "lazygophers/ccplugin"); assert.equal(out.payload.version, 1)
})

// 测试用 PNG 编码器：按行轮换五种滤波，覆盖解码器全部分支
function encodePng(w, h, rgba, withAlpha) {
  const bpp = withAlpha ? 4 : 3, stride = w * bpp, raw = Buffer.alloc(h * (stride + 1))
  const px = Buffer.alloc(h * stride)
  for (let i = 0; i < w * h; i++) for (let k = 0; k < bpp; k++) px[i * bpp + k] = rgba[i * 4 + k]
  for (let y = 0; y < h; y++) {
    const f = y % 5, o = y * (stride + 1)
    raw[o] = f
    for (let i = 0; i < stride; i++) {
      const x = px[y * stride + i], a = i >= bpp ? px[y * stride + i - bpp] : 0, b = y ? px[(y - 1) * stride + i] : 0, c = y && i >= bpp ? px[(y - 1) * stride + i - bpp] : 0
      const pa = Math.abs(b - c), pb = Math.abs(a - c), pc = Math.abs(a + b - 2 * c)
      const pred = [0, a, b, (a + b) >> 1, pa <= pb && pa <= pc ? a : pb <= pc ? b : c][f]
      raw[o + 1 + i] = (x - pred) & 255
    }
  }
  const chunk = (type, data) => {
    const len = Buffer.alloc(4); len.writeUInt32BE(data.length)
    const td = Buffer.concat([Buffer.from(type, "latin1"), data]), crc = Buffer.alloc(4); crc.writeUInt32BE(crc32(td) >>> 0)
    return Buffer.concat([len, td, crc])
  }
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4); ihdr[8] = 8; ihdr[9] = withAlpha ? 6 : 2
  return Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), chunk("IHDR", ihdr), chunk("IDAT", deflateSync(raw)), chunk("IEND", Buffer.alloc(0))])
}

test("PNG 最低位编码解码往返（RGBA 含半透明像素、RGB）", () => {
  const p = { id: "png-1", author: "落心", version: 2, time: "2026-11-28T00:00:00.000Z" }
  for (const withAlpha of [true, false]) {
    const w = 40, h = 30, px = Buffer.alloc(w * h * 4)
    for (let i = 0; i < w * h; i++) { px[i * 4] = (i * 7) & 255; px[i * 4 + 1] = (i * 13) & 255; px[i * 4 + 2] = (i * 29) & 255; px[i * 4 + 3] = withAlpha && i % 9 === 0 ? 128 : 255 }
    assert.ok(sm.embedLsb(px, JSON.stringify(p)))
    const png = encodePng(w, h, px, withAlpha)
    const dec = sm.decodePng(png)
    assert.equal(dec.width, w); assert.equal(dec.height, h)
    assert.deepEqual(sm.decode(png), { via: "png-lsb", payload: p })
    const f = join(TMP, "lsb-" + withAlpha + ".png"); writeFileSync(f, png)
    const sb = sandbox()
    const r = run(sb, ["decode", f])
    assert.equal(r.status, 0); assert.deepEqual(JSON.parse(r.stdout).payload, p)
  }
  assert.equal(sm.embedLsb(Buffer.alloc(4 * 4, 255), "x".repeat(100)), false, "容量不足时返回 false")
})

const GRAPH = { type: "graph", caption: "分叉", nodes: [{ id: "a", label: "A" }, { id: "b", label: "B", detail: "分叉点" }, { id: "c", label: "C" }, { id: "x", label: "X" }],
  edges: [{ from: "a", to: "b" }, { from: "b", to: "c" }, { from: "b", to: "x", label: "分支" }] }

test("三种风格都能渲染；外部资源引用为 0；无 @font-face 与 data:font；体积 ≤500 KiB；图片与 logo 内联", () => {
  const sb = sandbox({ project: { logo: "logo.svg" } })
  writeFileSync(join(sb.root, "logo.svg"), '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10"/></svg>')
  const px = Buffer.alloc(8 * 8 * 4, 200); writeFileSync(join(sb.root, "pic.png"), encodePng(8, 8, px, true))
  const f = writeContent(sb, { blocks: [...CONTENT.blocks, GRAPH, { type: "image", caption: "图片", src: "pic.png" }] })
  for (const style of sm.STYLES) {
    const r = run(sb, ["render", f, "--no-open", "--style", style])
    assert.equal(r.status, 0, r.stderr)
    const out = JSON.parse(r.stdout)
    assert.equal(out.style, style)
    const html = readFileSync(out.path, "utf8")
    const refs = html.match(/(?:\bsrc\s*=\s*["']?|<link\b[^>]*\bhref\s*=\s*["']?|url\(\s*["']?|@import\s+["']?)(?:https?:)?\/\//gi) ?? []
    assert.equal(refs.length, 0, "外部资源引用：" + refs.join(" "))
    assert.ok(!html.includes("@font-face"), "产物不得含 @font-face")
    assert.ok(!/data:font\//i.test(html), "产物不得含 data:font")
    assert.ok(statSync(out.path).size <= 500 * 1024, "体积 " + statSync(out.path).size + " 字节，超过 500 KiB")
    const page = pageData(html)
    assert.equal(page.showme.style, style)
    assert.match(page.meta.logo, /^data:image\/svg\+xml;base64,/)
    assert.ok(Buffer.from(page.meta.logo.split(",")[1], "base64").toString().includes("<metadata>show-me:"), "SVG 写入 metadata")
    assert.match(page.blocks.at(-1).src, /^data:image\/png;base64,/)
    assert.deepEqual(page.blocks.at(-2), GRAPH, "graph 块原样注入页面数据")
  }
  const tpl = readFileSync(sm.TEMPLATE, "utf8")
  assert.ok(tpl.includes("garrow-") && !tpl.includes("recharts"), "渲染器含 graph 绘制、不含 recharts")
  const bad = writeContent(sb, { blocks: [{ type: "image", caption: "远程", src: "https://example.com/a.png" }] })
  const r = run(sb, ["render", bad, "--no-open"])
  assert.equal(r.status, 2); assert.match(r.stderr, /页面须离线/)
})

// 长链 flow：8 个节点，取自 codemap 样例 fig.2
const LONG = { type: "flow", caption: "长链", nodes: [
  ["main(argv)", "parseArgs，log cli-start"], ["ensureDataRoot", "建 .ask-me/"], ["readInput + createAsk", "校验题集，写 questions.json / ask.json / index.json"],
  ["ensureServer", "复用或 spawn 后台 serve"], ["openBrowser(url)", "stderr 打印 URL 与 ask-me-id"], ["waitForSubmission", "每 250ms readAsk"],
  ["submittedAskResult", "读 questions + answers，写 stdout"], ["completeAsk + stopIdleServer", "删目录、停服务、清数据根"],
].map(([label, detail], i) => ({ id: "s" + i, label, detail })) }
const CHROME = process.env.CHROME ?? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
// 页内探针：每 250ms 把各图 svg 内文字的最小显示字号（font-size × svg 实际宽 / viewBox 宽）写进 body 属性
const PROBE = '<script>setInterval(()=>{const o=[];document.querySelectorAll("svg[viewBox][role=img]").forEach(s=>{const vb=s.viewBox.baseVal,k=s.getBoundingClientRect().width/vb.width;let m=1e9;s.querySelectorAll("text").forEach(t=>{if(t.textContent.trim())m=Math.min(m,parseFloat(getComputedStyle(t).fontSize)*k)});if(m<1e9)o.push({label:s.getAttribute("aria-label"),min:m})});document.body.setAttribute("data-probe",JSON.stringify(o))},250)</script>'

test("长链 flow 在 1920 宽下折行，节点文字显示字号 ≥12px（三种风格，headless Chrome DOM 断言）", { skip: !existsSync(CHROME) && "未找到 Chrome" }, async () => {
  const sb = sandbox()
  const f = writeContent(sb, { blocks: [LONG] })
  await Promise.all(sm.STYLES.map(async style => {
    const r = run(sb, ["render", f, "--no-open", "--style", style, "--out", join(sb.root, style + ".html")])
    assert.equal(r.status, 0, r.stderr)
    const p = join(sb.root, style + "-probe.html")
    writeFileSync(p, readFileSync(JSON.parse(r.stdout).path, "utf8").replace("</body>", PROBE + "</body>"))
    const dom = await new Promise((ok, no) => execFile(CHROME, ["--headless=new", "--disable-gpu", "--user-data-dir=" + join(sb.base, "chrome-" + style), "--window-size=1920,1080", "--virtual-time-budget=4000", "--dump-dom", "file://" + p],
      { timeout: 60000, maxBuffer: 64 << 20 }, (e, out) => (e ? no(e) : ok(out))))
    const m = /data-probe="([^"]*)"/.exec(dom)
    assert.ok(m, style + "：未取到探针结果")
    const fig = JSON.parse(m[1].replaceAll("&quot;", '"').replaceAll("&amp;", "&")).find(x => x.label.startsWith("main(argv)"))
    assert.ok(fig, style + "：未找到长链 flow")
    assert.ok(fig.min >= 12, style + "：最小显示字号 " + fig.min.toFixed(2) + "px < 12px")
  }))
})

test("内容 JSON 校验：topic 安全文件名、未知块类型、缺必填字段", () => {
  const sb = sandbox()
  for (const [patch, re] of [
    [{ topic: "../etc" }, /topic: 期望安全文件名/],
    [{ topic: "a/b" }, /topic: 期望安全文件名/],
    [{ blocks: [{ type: "video" }] }, /blocks\[0\]\.type: 期望/],
    [{ blocks: [{ type: "table", caption: "x" }] }, /blocks\[0\]\.columns: table 块缺少必填字段/],
    [{ extra: 1 }, /extra: 未知键/],
    [{ blocks: [{ ...GRAPH, edges: [{ from: "a", to: "zz" }] }] }, /blocks\[0\]\.edges\[0\]: from \/ to 须引用 nodes 中的 id/],
    [{ blocks: [{ ...GRAPH, edges: [...GRAPH.edges, { from: "x", to: "a" }] }] }, /blocks\[0\]\.edges: 存在环/],
    [{ blocks: [{ ...GRAPH, direction: "RL" }] }, /blocks\[0\]\.direction: 期望 LR \| TB/],
    [{ blocks: [{ ...GRAPH, nodes: [...GRAPH.nodes, { id: "a", label: "A2" }] }] }, /blocks\[0\]\.nodes\[4\]\.id: 重复 id/],
    [{ blocks: [{ type: "graph", caption: "x", nodes: [] }] }, /blocks\[0\]\.edges: graph 块缺少必填字段/],
  ]) {
    const r = run(sb, ["render", writeContent(sb, patch), "--no-open"])
    assert.equal(r.status, 2); assert.match(r.stderr, re)
  }
})

const sysFile = sb => join(sb.home, "config.json")
const projFile = sb => join(sb.root, ".claude", ".show-me", "config.json")
const ok = (sb, args) => { const r = run(sb, args); assert.equal(r.status, 0, r.stderr); return JSON.parse(r.stdout) }

test("config set → get 往返（系统级），保留文件中其他键，按类型解析值", () => {
  const sb = sandbox()
  assert.equal(ok(sb, ["config", "set", "watermark.visible.opacity", "0.1"]).layer, "system")
  ok(sb, ["config", "set", "switcher", "false"])
  ok(sb, ["config", "set", "author", '{"name":"落心","url":"https://example.com/u"}'])
  assert.deepEqual(ok(sb, ["config", "get", "watermark.visible.opacity"]), { key: "watermark.visible.opacity", value: 0.1, source: "system" })
  assert.equal(ok(sb, ["config", "get", "switcher"]).value, false)
  assert.equal(ok(sb, ["config", "get", "author.name"]).value, "落心")
  const f = JSON.parse(readFileSync(sysFile(sb), "utf8"))
  assert.equal(f.open, false, "原有键保留")
  assert.deepEqual(f.watermark, { visible: { opacity: 0.1 } })
})

test("config set --project 写到项目级，目录不存在时创建，系统级不变", () => {
  const sb = sandbox()
  rmSync(join(sb.root, ".claude"), { recursive: true, force: true })
  const before = readFileSync(sysFile(sb), "utf8")
  const r = ok(sb, ["config", "set", "byType.explain", "sketch", "--project"])
  assert.equal(r.layer, "project"); assert.equal(r.file, projFile(sb))
  assert.deepEqual(JSON.parse(readFileSync(projFile(sb), "utf8")), { byType: { explain: "sketch" } })
  assert.equal(readFileSync(sysFile(sb), "utf8"), before)
  assert.deepEqual(ok(sb, ["config", "get", "byType.explain"]), { key: "byType.explain", value: "sketch", source: "project" })
})

test("config set 非法值拒绝：退出码非 0、报错含键名与期望类型、文件不变", () => {
  const sb = sandbox()
  writeFileSync(join(sb.base, "outside.png"), "x")
  const before = readFileSync(sysFile(sb), "utf8")
  for (const [args, re] of [
    [["open", "yes"], /open: 期望 boolean，实际 "yes"/],
    [["watermark.visible.opacity", "2"], /watermark\.visible\.opacity: 期望 number 0–1/],
    [["style", "neon"], /style: 期望 paper \| sketch \| terminal/],
    [["byType.blog", "paper"], /byType\.blog: 未知键/],
    [["colour", "red"], /colour: 未知键/],
    [["author.url", "ftp://x"], /author\.url: 期望 http\(s\) URL/],
    [["author", "{bad json"], /author: 期望 object/],
  ]) {
    const r = run(sb, ["config", "set", ...args])
    assert.equal(r.status, 2, args.join(" ")); assert.match(r.stderr, re)
  }
  assert.equal(readFileSync(sysFile(sb), "utf8"), before, "系统级文件未改")
  const r = run(sb, ["config", "set", "logo", "../outside.png", "--project"])
  assert.equal(r.status, 2); assert.match(r.stderr, /logo: 路径必须在项目根/)
  assert.ok(!existsSync(projFile(sb)), "项目级文件未创建")
})

test("config unset：删除该层的键并清理空对象，之后回落到下一层", () => {
  const sb = sandbox({ system: { style: "terminal" } })
  ok(sb, ["config", "set", "style", "sketch", "--project"])
  ok(sb, ["config", "set", "watermark.hidden.meta", "false", "--project"])
  assert.equal(ok(sb, ["config", "get", "style"]).source, "project")
  assert.equal(ok(sb, ["config", "unset", "watermark.hidden.meta", "--project"]).removed, true)
  assert.deepEqual(JSON.parse(readFileSync(projFile(sb), "utf8")), { style: "sketch" }, "空对象一并清理")
  assert.equal(ok(sb, ["config", "unset", "style", "--project"]).removed, true)
  assert.deepEqual(ok(sb, ["config", "get", "style"]), { key: "style", value: "terminal", source: "system" })
  assert.equal(ok(sb, ["config", "unset", "style", "--project"]).removed, false)
})

test("config / config show：合并结果、每个键的来源层、两份配置文件路径与是否存在", () => {
  const sb = sandbox({ system: { author: { name: "系统署名" } }, project: { byType: { review: "terminal" } } })
  for (const args of [["config"], ["config", "show"]]) {
    const s = ok(sb, args)
    assert.equal(s.files.system.path, sysFile(sb)); assert.equal(s.files.system.exists, true)
    assert.equal(s.files.project.path, projFile(sb)); assert.equal(s.files.project.exists, true)
    assert.equal(s.config.author.name, "系统署名")
    assert.equal(s.sources["author.name"], "system")
    assert.equal(s.sources["byType.review"], "project")
    assert.equal(s.sources.style, "default")
  }
})
