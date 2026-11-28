#!/usr/bin/env node
// show-me CLI：零依赖。render 把内容 JSON 注入预编译渲染器写出单文件 HTML；decode 读取隐水印载荷；config 展示、读取、写入、删除配置
import { existsSync, mkdirSync, readFileSync, readdirSync, realpathSync, renameSync, writeFileSync } from "node:fs"
import { dirname, extname, isAbsolute, join, relative, resolve } from "node:path"
import { homedir } from "node:os"
import { spawn, spawnSync } from "node:child_process"
import { randomUUID } from "node:crypto"
import { inflateSync } from "node:zlib"
import { fileURLToPath } from "node:url"

const SKILL_DIR = resolve(dirname(fileURLToPath(import.meta.url)), "..")
export const TEMPLATE = join(SKILL_DIR, "assets", "renderer.html")
export const STYLES = ["paper", "sketch", "terminal"]
export const TYPES = ["research", "plan", "compare", "review", "explain", "report", "spec"]
export const MAX_BYTES = 1.5 * 1024 * 1024
const MARKER = '<script type="application/json" id="page-data"></script>'
const REPO_URL = "https://github.com/lazygophers/ccplugin"

export class UserError extends Error {}

// ---------- 配置 ----------
const bool = { t: "boolean" }, str = { t: "string" }
export const SCHEMA = { t: "object", keys: {
  style: { t: "enum", of: STYLES },
  byType: { t: "map", keyOf: TYPES, value: { t: "enum", of: STYLES } },
  outDir: str,
  open: bool,
  switcher: bool,
  author: { t: "object", keys: { name: str, url: { t: "url" } } },
  logo: str,
  watermark: { t: "object", keys: {
    visible: { t: "object", keys: { enabled: bool, text: str, opacity: { t: "number", min: 0, max: 1 } } },
    hidden: { t: "object", keys: { zeroWidth: bool, meta: bool, pattern: bool, images: bool } },
  } },
} }

export const DEFAULTS = {
  style: "paper", byType: {}, outDir: ".scratch/{topic}/reports", open: true, switcher: true,
  author: { name: "lazygophers/ccplugin", url: REPO_URL }, logo: null,
  watermark: {
    visible: { enabled: true, text: "{author} · {date}", opacity: 0.06 },
    hidden: { zeroWidth: true, meta: true, pattern: true, images: true },
  },
}

const kind = v => v === null ? "null" : Array.isArray(v) ? "array" : typeof v
const isObj = v => kind(v) === "object"
const want = s => s.t === "enum" ? s.of.join(" | ") : s.t === "map" ? "object" : s.t === "url" ? "http(s) URL 字符串" : s.t === "number" ? "number " + s.min + "–" + s.max : s.t

// null 在任意层表示「用下一层的值」，因此任何键都接受 null
export function validate(v, schema, path, file, errors) {
  if (v === null) return errors
  const at = file + ": " + (path || "<根>")
  const bad = () => errors.push(at + ": 期望 " + want(schema) + "，实际 " + kind(v) + (typeof v === "string" ? " " + JSON.stringify(v) : ""))
  switch (schema.t) {
    case "object":
      if (!isObj(v)) { bad(); break }
      for (const k of Object.keys(v)) {
        const p = path ? path + "." + k : k
        if (!(k in schema.keys)) errors.push(file + ": " + p + ": 未知键（可用：" + Object.keys(schema.keys).join(", ") + "）")
        else validate(v[k], schema.keys[k], p, file, errors)
      }
      break
    case "map":
      if (!isObj(v)) { bad(); break }
      for (const k of Object.keys(v)) {
        const p = path + "." + k
        if (!schema.keyOf.includes(k)) errors.push(file + ": " + p + ": 未知键（可用：" + schema.keyOf.join(", ") + "）")
        else validate(v[k], schema.value, p, file, errors)
      }
      break
    case "enum": if (!schema.of.includes(v)) bad(); break
    case "url": if (typeof v !== "string" || !/^https?:\/\/\S+$/.test(v)) bad(); break
    case "number": if (typeof v !== "number" || !Number.isFinite(v) || v < schema.min || v > schema.max) bad(); break
    default: if (typeof v !== schema.t) bad()
  }
  return errors
}

// 对象逐键合并；数组与字符串等叶子整体替换；null / 缺省取下一层；sources 记录每个叶子键的来源层
export function merge(schema, layers, path = "", sources = {}) {
  if (schema.t === "object" || schema.t === "map") {
    const keys = schema.t === "object" ? Object.keys(schema.keys)
      : [...new Set(layers.flatMap(l => isObj(l.v) ? Object.keys(l.v) : []))]
    const out = {}
    for (const k of keys) {
      const sub = schema.t === "object" ? schema.keys[k] : schema.value
      const v = merge(sub, layers.map(l => ({ name: l.name, v: isObj(l.v) ? l.v[k] : undefined })), path ? path + "." + k : k, sources)
      if (v !== undefined) out[k] = v
    }
    return out
  }
  for (let i = layers.length - 1; i >= 0; i--) {
    const v = layers[i].v
    if (v !== undefined && v !== null) { sources[path] = layers[i].name; return v }
  }
  if (layers.some(l => l.v === null)) { sources[path] = "default"; return null }
  return undefined
}

const inside = (root, p) => { const r = relative(root, p); return r === "" || (!r.startsWith("..") && !isAbsolute(r)) }
const real = p => { try { return realpathSync(p) } catch { return resolve(p) } }

export function projectRoot(cwd) {
  const r = spawnSync("git", ["rev-parse", "--show-toplevel"], { cwd, encoding: "utf8" })
  return real(r.status === 0 && r.stdout.trim() ? r.stdout.trim() : cwd)
}

function readJson(file) {
  try { return JSON.parse(readFileSync(file, "utf8")) }
  catch (e) { throw new UserError(file + ": JSON 解析失败：" + e.message) }
}

export function configFiles({ cwd = process.cwd(), env = process.env } = {}) {
  const root = projectRoot(cwd)
  const sysDir = env.SHOW_ME_HOME ? resolve(env.SHOW_ME_HOME) : join(homedir(), ".claude", ".show-me")
  return { root, sysDir, files: { system: join(sysDir, "config.json"), project: join(root, ".claude", ".show-me", "config.json") } }
}

export function loadConfig({ cwd = process.cwd(), env = process.env } = {}) {
  const { root, sysDir, files } = configFiles({ cwd, env })
  const layers = [{ name: "default", v: DEFAULTS }]
  const errors = []
  for (const name of ["system", "project"]) {
    if (!existsSync(files[name])) continue
    const v = readJson(files[name])
    validate(v, SCHEMA, "", files[name], errors)
    layers.push({ name, v })
  }
  if (errors.length) throw new UserError(errors.join("\n"))
  const sources = {}
  const config = merge(SCHEMA, layers, "", sources)
  // 项目级配置按不可信输入处理：logo 必须在项目根内且存在；outDir 不得指向项目根之外
  if (config.logo !== null) {
    const base = sources.logo === "project" ? root : sysDir
    const p = resolve(base, config.logo)
    const f = files[sources.logo]
    if (!existsSync(p)) throw new UserError(f + ": logo: 文件不存在：" + p)
    if (sources.logo === "project" && !inside(root, real(p))) throw new UserError(f + ": logo: 路径必须在项目根 " + root + " 内，实际 " + real(p))
    if (![".png", ".svg"].includes(extname(p).toLowerCase())) throw new UserError(f + ": logo: 只支持 .png / .svg，实际 " + p)
    config.logo = p
  }
  if (sources.outDir === "project") checkOutDir(root, config.outDir, "_", files.project)
  return { root, sysDir, files, config, sources }
}

// shortcut: 按词法路径判断（不解析尚未创建目录上的符号链接），outDir 需防符号链接逃逸时再升级
function checkOutDir(root, tpl, topic, file) {
  const dir = resolve(root, tpl.replaceAll("{topic}", topic))
  if (!inside(root, dir)) throw new UserError(file + ": outDir: 不得指向项目根 " + root + " 之外，实际 " + dir)
  return dir
}

// ---------- 内容 JSON ----------
const TOP = ["topic", "type", "style", "title", "subtitle", "meta", "summary", "kpis", "blocks", "conclusion", "changes", "references"]
export const BLOCKS = {
  heading: ["text"], paragraph: ["text"], list: ["items"], flow: ["caption", "nodes"], graph: ["caption", "nodes", "edges"],
  table: ["caption", "columns", "rows"], kv: ["caption", "columns", "rows"], chart: ["caption", "unit", "series", "data"],
  code: ["caption", "lang", "filename", "code"], codes: ["caption", "panes"], steps: ["items"],
  stack: ["caption", "layers"], wireframe: ["caption", "regions"], image: ["caption", "src"],
}
export const TOPIC_RE = /^[\p{L}\p{N}][\p{L}\p{N}._-]{0,79}$/u

export function validateContent(c, file) {
  const e = []
  const at = k => file + ": " + k
  if (!isObj(c)) throw new UserError(at("<根>") + ": 期望 object")
  for (const k of Object.keys(c)) if (!TOP.includes(k)) e.push(at(k) + ": 未知键（可用：" + TOP.join(", ") + "）")
  if (typeof c.topic !== "string" || !TOPIC_RE.test(c.topic) || c.topic.includes("..")) e.push(at("topic") + ": 期望安全文件名（字母、数字、. _ -，不以符号开头，≤80 字符），实际 " + JSON.stringify(c.topic))
  if (!TYPES.includes(c.type)) e.push(at("type") + ": 期望 " + TYPES.join(" | ") + "，实际 " + JSON.stringify(c.type))
  if (c.style !== undefined && c.style !== null && !STYLES.includes(c.style)) e.push(at("style") + ": 期望 " + STYLES.join(" | ") + "，实际 " + JSON.stringify(c.style))
  if (typeof c.title !== "string" || !c.title) e.push(at("title") + ": 期望非空 string")
  if (c.subtitle !== undefined && typeof c.subtitle !== "string") e.push(at("subtitle") + ": 期望 string")
  if (c.meta !== undefined && !isObj(c.meta)) e.push(at("meta") + ": 期望 object")
  if (!isObj(c.summary) || typeof c.summary.text !== "string" || typeof c.summary.point !== "string") e.push(at("summary") + ": 期望 {point: string, text: string, points?: string[]}")
  else if (c.summary.points !== undefined && (!Array.isArray(c.summary.points) || c.summary.points.length > 3)) e.push(at("summary.points") + ": 期望最多 3 条的 string 数组")
  if (c.changes !== undefined && (!Array.isArray(c.changes) || c.changes.some(x => typeof x !== "string"))) e.push(at("changes") + ": 期望 string 数组")
  if (!Array.isArray(c.references) || c.references.some(r => !isObj(r) || typeof r.text !== "string" || typeof r.source !== "string")) e.push(at("references") + ": 期望 {text, source} 数组")
  if (!Array.isArray(c.blocks) || !c.blocks.length) e.push(at("blocks") + ": 期望非空数组")
  else c.blocks.forEach((b, i) => {
    const p = "blocks[" + i + "]"
    if (!isObj(b) || !(b.type in BLOCKS)) return e.push(at(p + ".type") + ": 期望 " + Object.keys(BLOCKS).join(" | ") + "，实际 " + JSON.stringify(b?.type))
    for (const k of BLOCKS[b.type]) if (b[k] === undefined || b[k] === null) e.push(at(p + "." + k) + ": " + b.type + " 块缺少必填字段")
    if (b.type === "graph") validateGraph(b, at(p), e)
  })
  if (e.length) throw new UserError(e.join("\n"))
}

// graph：节点 id 唯一，边两端引用已有节点，不成环（分层排布要求有向无环）
function validateGraph(b, p, e) {
  if (b.direction !== undefined && !["LR", "TB"].includes(b.direction)) e.push(p + ".direction: 期望 LR | TB，实际 " + JSON.stringify(b.direction))
  if (!Array.isArray(b.nodes) || !Array.isArray(b.edges)) return e.push(p + ": nodes 与 edges 期望数组")
  const ids = new Set()
  b.nodes.forEach((n, i) => {
    if (!isObj(n) || typeof n.id !== "string" || typeof n.label !== "string") e.push(p + ".nodes[" + i + "]: 期望 {id: string, label: string, detail?: string}")
    else if (ids.has(n.id)) e.push(p + ".nodes[" + i + "].id: 重复 id " + JSON.stringify(n.id))
    else ids.add(n.id)
  })
  const next = new Map([...ids].map(id => [id, []]))
  b.edges.forEach((x, i) => {
    if (!isObj(x) || !ids.has(x.from) || !ids.has(x.to)) return e.push(p + ".edges[" + i + "]: from / to 须引用 nodes 中的 id，实际 " + JSON.stringify(x))
    next.get(x.from).push(x.to)
  })
  const state = new Map()
  const cyclic = v => { if (state.get(v) === 1) return true; if (state.get(v) === 2) return false; state.set(v, 1); const r = next.get(v).some(cyclic); state.set(v, 2); return r }
  if ([...ids].some(cyclic)) e.push(p + ".edges: 存在环，graph 须为有向无环图")
}

// ---------- 隐水印 ----------
const ZW0 = "\u200b", ZW1 = "\u200c", ZWB = "\u2060"
const toBits = bytes => [...bytes].flatMap(x => [7, 6, 5, 4, 3, 2, 1, 0].map(k => (x >> k) & 1))
export const zwEncode = s => ZWB + toBits(Buffer.from(s, "utf8")).map(b => b ? ZW1 : ZW0).join("") + ZWB
export function zwDecode(text) {
  for (const m of text.matchAll(/\u2060([\u200b\u200c]{8,})\u2060/g)) {
    const bits = m[1], out = Buffer.alloc(bits.length >> 3)
    for (let i = 0; i < out.length * 8; i++) out[i >> 3] |= (bits[i] === ZW1 ? 1 : 0) << (7 - (i & 7))
    try { return JSON.parse(out.toString("utf8")) } catch { /* 下一处 */ }
  }
  return null
}
// 零宽串插在首字之后：复制段落任意包含首字的片段都携带载荷
const withZw = (t, zw) => typeof t === "string" && t ? [...t][0] + zw + [...t].slice(1).join("") : t

const b64 = s => Buffer.from(s, "utf8").toString("base64")
const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;")
const unesc = s => s.replace(/&quot;/g, '"').replace(/&gt;/g, ">").replace(/&lt;/g, "<").replace(/&amp;/g, "&")
const svgMeta = (svg, payload) => svg.replace(/<svg\b[^>]*>/i, m => m + "<metadata>show-me:" + b64(payload) + "</metadata>")

// 位图最低位：4 字节大端长度 + UTF-8 载荷，逐像素写 R、G、B 最低位，跳过 alpha < 255 的像素（与 renderer/src/watermark.ts 一致）
export function embedLsb(px, payload) {
  const data = Buffer.from(payload, "utf8"), all = Buffer.alloc(4 + data.length)
  all.writeUInt32BE(data.length, 0); data.copy(all, 4)
  const bits = all.length * 8
  let b = 0
  for (let p = 0; p < px.length && b < bits; p += 4) {
    if (px[p + 3] !== 255) continue
    for (let c = 0; c < 3 && b < bits; c++, b++) px[p + c] = (px[p + c] & 254) | ((all[b >> 3] >> (7 - (b & 7))) & 1)
  }
  return b === bits
}
export function extractLsb(px) {
  const it = (function* () { for (let p = 0; p < px.length; p += 4) if (px[p + 3] === 255) for (let c = 0; c < 3; c++) yield px[p + c] & 1 })()
  const byte = () => { let v = 0; for (let k = 0; k < 8; k++) { const n = it.next(); if (n.done) return -1; v = (v << 1) | n.value } return v }
  const head = [byte(), byte(), byte(), byte()]
  if (head.includes(-1)) return null
  const len = ((head[0] << 24) | (head[1] << 16) | (head[2] << 8) | head[3]) >>> 0
  if (!len || len > 65536) return null
  const out = Buffer.alloc(len)
  for (let i = 0; i < len; i++) { const v = byte(); if (v < 0) return null; out[i] = v }
  try { return JSON.parse(out.toString("utf8")) } catch { return null }
}

// 最小 PNG 解码：仅 8 位 RGB / RGBA、非隔行；输出 RGBA
export function decodePng(buf) {
  if (buf.length < 8 || buf.readUInt32BE(0) !== 0x89504e47) throw new UserError("不是 PNG 文件")
  let pos = 8, w = 0, h = 0, depth = 0, ct = 0, il = 0
  const idat = []
  while (pos + 8 <= buf.length) {
    const len = buf.readUInt32BE(pos), type = buf.toString("latin1", pos + 4, pos + 8), d = buf.subarray(pos + 8, pos + 8 + len)
    if (type === "IHDR") { w = d.readUInt32BE(0); h = d.readUInt32BE(4); depth = d[8]; ct = d[9]; il = d[12] }
    else if (type === "IDAT") idat.push(d)
    else if (type === "IEND") break
    pos += 12 + len
  }
  if (depth !== 8 || (ct !== 2 && ct !== 6) || il !== 0) throw new UserError("仅支持 8 位 RGB/RGBA 非隔行 PNG（实际 位深 " + depth + "，颜色类型 " + ct + "，隔行 " + il + "）")
  const bpp = ct === 6 ? 4 : 3, stride = w * bpp, raw = inflateSync(Buffer.concat(idat)), out = Buffer.alloc(w * h * 4)
  let prev = Buffer.alloc(stride)
  for (let y = 0; y < h; y++) {
    const f = raw[y * (stride + 1)], line = Buffer.from(raw.subarray(y * (stride + 1) + 1, (y + 1) * (stride + 1)))
    for (let i = 0; i < stride; i++) {
      const a = i >= bpp ? line[i - bpp] : 0, b = prev[i], c = i >= bpp ? prev[i - bpp] : 0
      if (f === 1) line[i] += a
      else if (f === 2) line[i] += b
      else if (f === 3) line[i] += (a + b) >> 1
      else if (f === 4) { const p = a + b - c, pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c); line[i] += pa <= pb && pa <= pc ? a : pb <= pc ? b : c }
    }
    for (let x = 0; x < w; x++) for (let k = 0; k < 4; k++) out[(y * w + x) * 4 + k] = k < bpp ? line[x * bpp + k] : 255
    prev = line
  }
  return { width: w, height: h, data: out }
}

export function decode(buf) {
  if (buf.length >= 8 && buf.readUInt32BE(0) === 0x89504e47) {
    const p = extractLsb(decodePng(buf).data)
    return p && { via: "png-lsb", payload: p }
  }
  const s = buf.toString("utf8")
  const m = {}
  for (const [, k, v] of s.matchAll(/<meta name="show-me:(\w+)" content="([^"]*)"/g)) m[k] = unesc(v)
  if (m.id) return { via: "meta", payload: { id: m.id, author: m.author, version: Number(m.version), time: m.time } }
  for (const [via, re] of [["comment", /<!-- show-me:([A-Za-z0-9+/=]+) -->/], ["svg-metadata", /<metadata>show-me:([A-Za-z0-9+/=]+)<\/metadata>/]]) {
    const x = re.exec(s)
    if (x) try { return { via, payload: JSON.parse(Buffer.from(x[1], "base64").toString("utf8")) } } catch { /* 继续 */ }
  }
  const z = zwDecode(s)
  return z && { via: "zero-width", payload: z }
}

// ---------- render ----------
const MIME = { ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml" }
function inlineImage(p, payload, field) {
  const mime = MIME[extname(p).toLowerCase()]
  if (!mime) throw new UserError(field + ": 不支持的图片格式 " + p + "（可用：" + Object.keys(MIME).join(" ") + "）")
  if (!existsSync(p)) throw new UserError(field + ": 文件不存在：" + p)
  if (mime === "image/svg+xml") {
    const svg = readFileSync(p, "utf8")
    return "data:image/svg+xml;base64," + b64(payload ? svgMeta(svg, payload) : svg)
  }
  return "data:" + mime + ";base64," + readFileSync(p).toString("base64")
}

export function skillVersion() {
  const m = /^---\n[\s\S]*?^version:\s*["']?([^\s"']+)/m.exec(readFileSync(join(SKILL_DIR, "SKILL.md"), "utf8"))
  return m ? m[1] : "0.0.0"
}

const pad = n => String(n).padStart(2, "0")
const ymd = d => d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate())

// topic 已由 TOPIC_RE 限定为字母、数字与 . _ -，正则里只需转义点号
export function versions(dir, topic) {
  const re = new RegExp("^" + topic.replace(/\./g, "\\.") + "-v(\\d+)\\.html$", "u")
  return existsSync(dir) ? readdirSync(dir).map(f => re.exec(f)).filter(Boolean).map(m => Number(m[1])) : []
}

export function render(contentFile, { out, style: cliStyle, noOpen = false, cwd = process.cwd(), env = process.env, now = new Date() } = {}) {
  const cf = resolve(cwd, contentFile)
  const content = readJson(cf)
  validateContent(content, cf)
  if (cliStyle !== undefined && !STYLES.includes(cliStyle)) throw new UserError("--style: 期望 " + STYLES.join(" | ") + "，实际 " + JSON.stringify(cliStyle))
  const { root, files, config, sources } = loadConfig({ cwd, env })
  const topic = content.topic
  const style = cliStyle ?? content.style ?? config.byType[content.type] ?? config.style
  const dir = out ? dirname(resolve(cwd, out)) : sources.outDir === "project" ? checkOutDir(root, config.outDir, topic, files.project) : resolve(root, config.outDir.replaceAll("{topic}", topic))
  const prevN = Math.max(0, ...versions(dir, topic))
  const version = prevN + 1
  const file = out ? resolve(cwd, out) : join(dir, topic + "-v" + version + ".html")
  const prev = prevN && existsSync(join(dir, topic + "-v" + prevN + ".html")) ? topic + "-v" + prevN + ".html" : undefined

  const hid = config.watermark.hidden, vis = config.watermark.visible
  const date = ymd(now), generated = date + " " + pad(now.getHours()) + ":" + pad(now.getMinutes())
  const payloadObj = { id: randomUUID(), author: config.author.name, version, time: now.toISOString() }
  const payload = JSON.stringify(payloadObj)
  const zw = hid.zeroWidth ? zwEncode(payload) : ""
  const baseDir = dirname(cf)
  const blocks = content.blocks.map((b, i) => {
    if (b.type === "paragraph" && zw) return { ...b, text: withZw(b.text, zw) }
    if (b.type === "image") {
      if (/^data:/i.test(b.src)) return b
      if (/^[a-z][a-z0-9+.-]*:/i.test(b.src)) throw new UserError(cf + ": blocks[" + i + "].src: 页面须离线，只接受本地文件路径或 data: URI，实际 " + b.src)
      return { ...b, src: inlineImage(resolve(baseDir, b.src), hid.images ? payload : "", cf + ": blocks[" + i + "].src") }
    }
    return b
  })
  const page = {
    ...content,
    subtitle: content.subtitle ?? "",
    summary: { ...content.summary, points: content.summary.points ?? [], text: zw ? withZw(content.summary.text, zw) : content.summary.text },
    blocks,
    meta: {
      ...content.meta,
      author: content.meta?.author ?? config.author.name,
      date: content.meta?.date ?? date,
      generated, version, kind: content.type,
      byline: { name: config.author.name, url: config.author.url },
      logo: config.logo ? inlineImage(config.logo, hid.images ? payload : "", "logo") : undefined,
    },
    watermark: vis.enabled ? vis.text.replaceAll("{author}", config.author.name).replaceAll("{date}", date) : null,
    showme: {
      version: skillVersion(), style, switcher: config.switcher, prev, watermarkOpacity: vis.opacity,
      payload: hid.pattern || hid.images ? payload : undefined, pattern: hid.pattern, images: hid.images,
    },
  }
  if (!page.changes?.length || version < 2) delete page.changes

  const tpl = readFileSync(TEMPLATE, "utf8")
  if (tpl.split(MARKER).length !== 2) throw new Error("渲染器模板缺少唯一注入标记：" + TEMPLATE)
  const json = JSON.stringify(page).replace(/</g, "\\u003c")
  const head = "<title>" + esc(content.title) + "</title>" + (hid.meta
    ? Object.entries(payloadObj).map(([k, v]) => '<meta name="show-me:' + k + '" content="' + esc(v) + '">').join("") + "<!-- show-me:" + b64(payload) + " -->"
    : "")
  const html = tpl.replace(/<title>[^<]*<\/title>/, () => head).replace(MARKER, () => '<script type="application/json" id="page-data">' + json + "</script>")
  const bytes = Buffer.byteLength(html)
  if (bytes > MAX_BYTES) throw new UserError("产物 " + bytes + " 字节，超过上限 " + MAX_BYTES + "（1.5MB）；压缩或移除内容中的图片后重试")
  mkdirSync(dirname(file), { recursive: true })
  writeFileSync(file, html)
  if (!noOpen && config.open) openFile(file)
  return { path: file, style, version }
}

function openFile(file) {
  const cmd = process.platform === "darwin" ? "open" : process.platform === "win32" ? null : "xdg-open"
  if (!cmd) return
  const p = spawn(cmd, [file], { detached: true, stdio: "ignore" })
  p.on("error", () => {})
  p.unref()
}

// ---------- config 子命令 ----------
// 点路径 → 该键的 schema；未知键报错并列出可用键
export function schemaAt(key) {
  let sc = SCHEMA
  const parts = String(key ?? "").split(".")
  if (!key || parts.some(p => !p)) throw new UserError("config: 缺少键名或键名为空段：" + JSON.stringify(key))
  parts.forEach((p, i) => {
    const at = parts.slice(0, i + 1).join(".")
    if (sc.t === "object") {
      if (!(p in sc.keys)) throw new UserError(at + ": 未知键（可用：" + Object.keys(sc.keys).join(", ") + "）")
      sc = sc.keys[p]
    } else if (sc.t === "map") {
      if (!sc.keyOf.includes(p)) throw new UserError(at + ": 未知键（可用：" + sc.keyOf.join(", ") + "）")
      sc = sc.value
    } else throw new UserError(at + ": 未知键（" + parts.slice(0, i).join(".") + " 不是对象）")
  })
  return { schema: sc, parts }
}

// 按键的类型解析命令行值：null 表示沿用下一层；布尔、数字、对象按字面解析，其余按字符串
export function parseValue(raw, schema, key) {
  if (raw === "null") return null
  const fail = () => { throw new UserError(key + ": 期望 " + want(schema) + "，实际 " + JSON.stringify(raw)) }
  if (schema.t === "boolean") return raw === "true" ? true : raw === "false" ? false : fail()
  if (schema.t === "number") { const n = Number(raw); return raw.trim() !== "" && Number.isFinite(n) ? n : fail() }
  if (schema.t === "object" || schema.t === "map") { try { return JSON.parse(raw) } catch { return fail() } }
  return raw
}

const getIn = (o, parts) => parts.reduce((v, p) => (isObj(v) ? v[p] : undefined), o)
function setIn(o, parts, v) {
  let cur = o
  for (const p of parts.slice(0, -1)) { if (!isObj(cur[p])) cur[p] = {}; cur = cur[p] }
  cur[parts.at(-1)] = v
}
// 删除叶子后自下而上清掉变空的对象
function unsetIn(o, parts) {
  const chain = [o]
  for (const p of parts.slice(0, -1)) { const n = chain.at(-1)[p]; if (!isObj(n)) return false; chain.push(n) }
  const last = chain.at(-1)
  if (!(parts.at(-1) in last)) return false
  delete last[parts.at(-1)]
  for (let i = chain.length - 1; i > 0; i--) if (!Object.keys(chain[i]).length) delete chain[i - 1][parts[i - 1]]
  return true
}

function atomicWrite(file, obj) {
  mkdirSync(dirname(file), { recursive: true })
  const tmp = file + "." + process.pid + ".tmp"
  writeFileSync(tmp, JSON.stringify(obj, null, 2) + "\n")
  renameSync(tmp, file)
}

export function configSet(key, raw, { project = false, cwd = process.cwd(), env = process.env } = {}) {
  const { schema, parts } = schemaAt(key)
  if (raw === undefined) throw new UserError("config set: 缺少值")
  const value = parseValue(raw, schema, key)
  const { root, sysDir, files } = configFiles({ cwd, env })
  const file = project ? files.project : files.system
  const obj = existsSync(file) ? readJson(file) : {}
  if (!isObj(obj)) throw new UserError(file + ": <根>: 期望 object")
  setIn(obj, parts, value)
  const errors = validate(obj, SCHEMA, "", file, [])
  if (errors.length) throw new UserError(errors.join("\n"))
  // 写入前按 loadConfig 的同一规则检查路径
  if (key === "logo" && value !== null) {
    const p = resolve(project ? root : sysDir, value)
    if (!existsSync(p)) throw new UserError(file + ": logo: 文件不存在：" + p)
    if (project && !inside(root, real(p))) throw new UserError(file + ": logo: 路径必须在项目根 " + root + " 内，实际 " + real(p))
    if (![".png", ".svg"].includes(extname(p).toLowerCase())) throw new UserError(file + ": logo: 只支持 .png / .svg，实际 " + p)
  }
  if (key === "outDir" && value !== null && project) checkOutDir(root, value, "_", file)
  atomicWrite(file, obj)
  return { action: "set", layer: project ? "project" : "system", file, key, value }
}

export function configUnset(key, { project = false, cwd = process.cwd(), env = process.env } = {}) {
  const { parts } = schemaAt(key)
  const { files } = configFiles({ cwd, env })
  const file = project ? files.project : files.system
  if (!existsSync(file)) return { action: "unset", layer: project ? "project" : "system", file, key, removed: false }
  const obj = readJson(file)
  const removed = isObj(obj) && unsetIn(obj, parts)
  if (removed) atomicWrite(file, obj)
  return { action: "unset", layer: project ? "project" : "system", file, key, removed }
}

export function configShow(opts = {}) {
  const { root, files, config, sources } = loadConfig(opts)
  return { root, files: { system: { path: files.system, exists: existsSync(files.system) }, project: { path: files.project, exists: existsSync(files.project) } }, config, sources }
}

export function configGet(key, opts = {}) {
  const { parts } = schemaAt(key)
  const { config, sources } = loadConfig(opts)
  const sub = Object.fromEntries(Object.entries(sources).filter(([k]) => k === key || k.startsWith(key + ".")))
  return { key, value: getIn(config, parts) ?? null, source: key in sources ? sources[key] : sub }
}

// ---------- 入口 ----------
const USAGE = "用法：\n  show-me render <content.json> [--out <file>] [--no-open] [--style paper|sketch|terminal]\n  show-me decode <file | ->\n  show-me config [show | get <key> | set <key> <value> | unset <key>] [--project]"

export function main(argv) {
  const [cmd, ...rest] = argv
  if (cmd === "render") {
    const opts = {}, pos = []
    for (let i = 0; i < rest.length; i++) {
      const a = rest[i]
      if (a === "--no-open") opts.noOpen = true
      else if (a === "--out" || a === "--style") { if (rest[i + 1] === undefined) throw new UserError(a + " 缺少参数"); opts[a.slice(2)] = rest[++i] }
      else if (a.startsWith("--")) throw new UserError("未知参数 " + a + "\n" + USAGE)
      else pos.push(a)
    }
    if (pos.length !== 1) throw new UserError(USAGE)
    return JSON.stringify(render(pos[0], opts))
  }
  if (cmd === "decode") {
    if (rest.length !== 1) throw new UserError(USAGE)
    const r = decode(rest[0] === "-" ? readFileSync(0) : readFileSync(rest[0]))
    if (!r) throw new UserError("未找到 show-me 水印载荷")
    return JSON.stringify(r)
  }
  if (cmd === "config") {
    const project = rest.includes("--project")
    const args = rest.filter(a => a !== "--project")
    const bad = args.find(a => a.startsWith("--"))
    if (bad) throw new UserError("未知参数 " + bad + "\n" + USAGE)
    const [sub = "show", key, value, ...extra] = args
    const need = n => { if (args.length !== n) throw new UserError(USAGE) }
    if (sub === "show") { need(args.length ? 1 : 0); if (project) throw new UserError("config show 不接受 --project（总是展示两层合并结果）"); return JSON.stringify(configShow(), null, 2) }
    if (sub === "get") { need(2); return JSON.stringify(configGet(key)) }
    if (sub === "set") { need(3); return JSON.stringify(configSet(key, value, { project })) }
    if (sub === "unset") { need(2); return JSON.stringify(configUnset(key, { project })) }
    throw new UserError("未知 config 子命令 " + sub + "\n" + USAGE)
  }
  throw new UserError(USAGE)
}

if (process.argv[1] && real(process.argv[1]) === real(fileURLToPath(import.meta.url))) {
  try { process.stdout.write(main(process.argv.slice(2)) + "\n") }
  catch (e) {
    process.stderr.write("show-me: " + (e instanceof UserError ? e.message : e.stack) + "\n")
    process.exitCode = e instanceof UserError ? 2 : 1
  }
}
