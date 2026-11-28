import hljs from "highlight.js/lib/core"
import typescript from "highlight.js/lib/languages/typescript"
import bash from "highlight.js/lib/languages/bash"
import json from "highlight.js/lib/languages/json"
import { useLayoutEffect, useRef, useState } from "react"
import type { ChartBlock, FlowNode, GraphBlock } from "@/types"

hljs.registerLanguage("typescript", typescript)
hljs.registerLanguage("bash", bash)
hljs.registerLanguage("json", json)

// 3 列蛇形布局：奇数行反向，箭头在行尾折下
const W = 180, H = 64, GX = 70, GY = 60, M = 20
export function layout(n: number, COLS = 3, w = W, h = H, gx = GX, gy = GY) {
  const pos = Array.from({ length: n }, (_, i) => {
    const r = Math.floor(i / COLS), c = i % COLS
    const col = r % 2 ? COLS - 1 - c : c
    return { x: M + col * (w + gx), y: M + r * (h + gy) }
  })
  const rows = Math.ceil(n / COLS)
  const edges = pos.slice(1).map((b, i) => {
    const a = pos[i]
    if (a.y === b.y) {
      const dir = b.x > a.x ? 1 : -1
      const x1 = dir > 0 ? a.x + w : a.x, x2 = dir > 0 ? b.x : b.x + w
      return { x1: x1 + dir * 6, y1: a.y + h / 2, x2: x2 - dir * 6, y2: b.y + h / 2 }
    }
    return { x1: a.x + w / 2, y1: a.y + h + 6, x2: b.x + w / 2, y2: b.y - 6 }
  })
  return { pos, edges, width: M * 2 + Math.min(COLS, n) * w + (Math.min(COLS, n) - 1) * gx, height: M * 2 + rows * h + (rows - 1) * gy }
}

// 列数：按可用宽度 avail 取缩放比不低于 minScale（说明字号 × minScale ≥ 12px）的最大列数，再把节点均分到各排；未测得宽度时单排
export function fitCols(n: number, w: number, gx: number, avail: number, minScale: number) {
  if (!(avail > 0)) return n
  const c = Math.max(1, Math.min(n, Math.floor((avail / minScale - M * 2 + gx) / (w + gx))))
  return Math.ceil(n / Math.ceil(n / c))
}

// 有向图：LR 横排缩放后说明字号低于 12px 时改为 TB 竖排
export function fitGraph(block: GraphBlock, w: number, h: number, gMain: number, gCross: number, avail: number, minScale: number) {
  const g = graphLayout(block, w, h, gMain, gCross)
  return block.direction !== "TB" && avail > 0 && avail / g.width < minScale ? graphLayout({ ...block, direction: "TB" }, w, h, gMain, gCross) : g
}

// 文字宽度估算：CJK 与全角符号按 1em，其余按 0.62em（等宽字体 0.6em，留余量）
const charW = (ch: string, fs: number) => (/[\u2e80-\uffef]/.test(ch) ? fs : fs * 0.62)
export const textW = (s: string, fs: number) => [...s].reduce((a, ch) => a + charW(ch, fs), 0)

// 按宽度折行：ASCII 词整体换行，CJK 逐字可断；单词超宽时按字符硬断
export function wrap(text: string, maxW: number, fs: number): string[] {
  const lines: string[] = []
  let cur = ""
  const push = () => { if (cur.trim()) lines.push(cur.trim()); cur = "" }
  for (const tok of text.match(/[\u2e80-\uffef]|\s+|[^\s\u2e80-\uffef]+/g) ?? []) {
    // 行首避头：句读标点超宽也留在上一行末
    if (textW(cur + tok, fs) <= maxW || /^[，。、；：！？）」』,.;:!?)]$/.test(tok)) { cur += tok; continue }
    if (/^\s+$/.test(tok)) { push(); continue }
    push()
    for (const ch of tok) { if (textW(cur + ch, fs) > maxW) push(); cur += ch }
  }
  push()
  return lines.length ? lines : [""]
}

export type NodeBox = { w: number; h: number; label: string[][]; detail: string[][]; lh: [number, number] }
// 节点统一尺寸：宽度按最长标题加宽（上限 maxW），标题与说明超宽折行，高度取各节点最多行数
// 说明文字只把宽度撑到 detailCap（缺省 minW × 1.25），再长就折行，避免节点过宽把整图缩小
export function nodeBox(items: { label: string; detail?: string }[], o: { minW: number; maxW: number; h: number; fs: [number, number]; lh: [number, number]; pad: number; detailCap?: number }): NodeBox {
  const cap = o.detailCap ?? o.minW * 1.25
  const need = (n: { label: string; detail?: string }) => Math.max(textW(n.label, o.fs[0]), Math.min(textW(n.detail ?? "", o.fs[1]), cap - o.pad * 2)) + o.pad * 2
  const w = Math.min(o.maxW, Math.max(o.minW, ...items.map(need)))
  const label = items.map(n => wrap(n.label, w - o.pad * 2, o.fs[0]))
  const detail = items.map(n => (n.detail ? wrap(n.detail, w - o.pad * 2, o.fs[1]) : []))
  const L = Math.max(...label.map(l => l.length)), D = Math.max(1, ...detail.map(d => d.length))
  return { w, h: o.h + (L - 1) * o.lh[0] + (D - 1) * o.lh[1], label, detail, lh: o.lh }
}

// 节点文字：标题首行基线 y0，说明首行基线在标题末行下 gap 处
export function BoxText({ b, i, cx, y, y0, gap, fs, labelProps, detailProps }: {
  b: NodeBox; i: number; cx: number; y: number; y0: number; gap: number; fs: [number, number]
  labelProps?: React.SVGProps<SVGTextElement>; detailProps?: React.SVGProps<SVGTextElement>
}) {
  const L = b.label[i].length, dy = y + y0 + (L - 1) * b.lh[0] + gap
  return <>
    <text x={cx} y={y + y0} textAnchor="middle" fontSize={fs[0]} {...labelProps}>
      {b.label[i].map((t, k) => <tspan key={k} x={cx} dy={k ? b.lh[0] : 0}>{t}</tspan>)}
    </text>
    {b.detail[i].length > 0 && <text x={cx} y={dy} textAnchor="middle" fontSize={fs[1]} {...detailProps}>
      {b.detail[i].map((t, k) => <tspan key={k} x={cx} dy={k ? b.lh[1] : 0}>{t}</tspan>)}
    </text>}
  </>
}

export function Flow({ nodes, style, cols = 3 }: { nodes: FlowNode[]; style: "paper" | "terminal"; cols?: number }) {
  const tag = (i: number, n: FlowNode) => (style === "terminal" ? `[${String(i + 1).padStart(2, "0")}] ${n.label}` : n.label)
  const box = nodeBox(nodes.map((n, i) => ({ label: tag(i, n), detail: n.detail })), { minW: W, maxW: 280, h: H, fs: [15, 12], lh: [19, 16], pad: 12 })
  const [ref, cw] = useWidth<HTMLDivElement>()
  const { pos, edges, width, height } = layout(nodes.length, Math.min(cols, fitCols(nodes.length, box.w, GX, cw, 1)), box.w, box.h)
  const stroke = style === "terminal" ? "var(--primary)" : "var(--foreground)"
  return (
    <div ref={ref}>
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full" role="img" aria-label={nodes.map(n => n.label).join(" → ")}>
      <defs>
        <marker id={`arrow-${style}`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" fill={stroke} />
        </marker>
      </defs>
      <g>
          {pos.map((p, i) => (
            <rect key={i} x={p.x} y={p.y} width={box.w} height={box.h} rx={style === "terminal" ? 0 : 2}
              fill={style === "terminal" ? "var(--card)" : "none"} stroke={stroke} strokeWidth={1} strokeDasharray={style === "terminal" && i % 2 ? "4 3" : undefined} />
          ))}
          {edges.map((e, i) => (
            <line key={i} {...e} stroke={stroke} strokeWidth={1.2} markerEnd={`url(#arrow-${style})`} />
          ))}
      </g>
      {nodes.map((n, i) => (
        <g key={n.id}>
          <BoxText b={box} i={i} cx={pos[i].x + box.w / 2} y={pos[i].y} y0={28} gap={20} fs={[15, 12]}
            labelProps={{ className: "fill-foreground", fontWeight: style === "terminal" ? 600 : 500 }} detailProps={{ className: "fill-muted-foreground" }} />
        </g>
      ))}
    </svg>
    </div>
  )
}

// 有向图分层：层号 = 最长前驱链长度；层内按「车道」排布，节点优先沿用第一个（车道最小的）前驱的车道，被占则取最小空闲车道。
// shortcut: 跨层的长边不绕开中间节点，同车道跨层边可能穿过中间节点；需要时再引入虚拟节点做绕行。
export function graphLayout(block: GraphBlock, w: number, h: number, gMain: number, gCross: number, m = 20) {
  const ids = block.nodes.map(n => n.id), idx = new Map(ids.map((id, i) => [id, i]))
  const es = block.edges.filter(e => idx.has(e.from) && idx.has(e.to)).map(e => ({ ...e, a: idx.get(e.from)!, b: idx.get(e.to)! }))
  const layer = ids.map(() => 0)
  for (let k = 0; k < ids.length; k++) for (const e of es) if (layer[e.a] + 1 > layer[e.b] && layer[e.a] + 1 < ids.length) layer[e.b] = layer[e.a] + 1
  const lane = ids.map(() => -1), used = new Map<number, Set<number>>()
  const order = ids.map((_, i) => i).sort((p, q) => layer[p] - layer[q] || p - q)
  for (const v of order) {
    const taken = used.get(layer[v]) ?? new Set<number>()
    const pre = es.filter(e => e.b === v && lane[e.a] >= 0).map(e => lane[e.a]).sort((p, q) => p - q)
    let l = pre.find(x => !taken.has(x)) ?? 0
    while (taken.has(l)) l++
    lane[v] = l; taken.add(l); used.set(layer[v], taken)
  }
  const tb = block.direction === "TB"
  const pos = ids.map((_, i) => tb
    ? { x: m + lane[i] * (w + gCross), y: m + layer[i] * (h + gMain) }
    : { x: m + layer[i] * (w + gMain), y: m + lane[i] * (h + gCross) })
  const nL = Math.max(...layer) + 1, nC = Math.max(...lane) + 1
  const width = m * 2 + (tb ? nC * w + (nC - 1) * gCross : nL * w + (nL - 1) * gMain)
  const height = m * 2 + (tb ? nL * h + (nL - 1) * gMain : nC * h + (nC - 1) * gCross)
  // 连线：LR 从右边中点到左边中点，TB 从下边中点到上边中点；不同车道用三次贝塞尔，切线沿主方向
  const edges = es.map(e => {
    const p = pos[e.a], q = pos[e.b], g = 6
    const [x1, y1, x2, y2] = tb ? [p.x + w / 2, p.y + h + g, q.x + w / 2, q.y - g] : [p.x + w + g, p.y + h / 2, q.x - g, q.y + h / 2]
    const d = tb ? `M${x1},${y1} C${x1},${(y1 + y2) / 2} ${x2},${(y1 + y2) / 2} ${x2},${y2}` : `M${x1},${y1} C${(x1 + x2) / 2},${y1} ${(x1 + x2) / 2},${y2} ${x2},${y2}`
    // bend：跨车道的弯曲边，标签放在曲线中点旁，避免压线
    return { d, x1, y1, x2, y2, mx: (x1 + x2) / 2, my: (y1 + y2) / 2, label: e.label, tb, bend: tb ? x1 !== x2 : y1 !== y2 }
  })
  return { pos, lane, layer, edges, width, height }
}

// 科研风 / 程序员风有向图：科研风细线框，程序员风绿色框线、卡片底色
export function Graph({ block, style }: { block: GraphBlock; style: "paper" | "terminal" }) {
  const box = nodeBox(block.nodes, { minW: 120, maxW: 260, h: H, fs: [15, 12], lh: [19, 16], pad: 12 })
  const [ref, cw] = useWidth<HTMLDivElement>()
  const g = fitGraph(block, box.w, box.h, 64, 28, cw, 1)
  const stroke = style === "terminal" ? "var(--primary)" : "var(--foreground)"
  const id = `garrow-${style}`
  return (
    <div ref={ref} className="flex w-full justify-center">
    <svg viewBox={`0 0 ${g.width} ${g.height}`} className="w-full" style={{ maxWidth: g.width * 1.25 }} role="img" aria-label={block.edges.map(e => `${e.from} → ${e.to}`).join("，")}>
      <defs>
        <marker id={id} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" fill={stroke} />
        </marker>
      </defs>
      {g.edges.map((e, i) => <path key={i} d={e.d} fill="none" stroke={stroke} strokeWidth={1.2} markerEnd={`url(#${id})`} />)}
      {g.edges.map((e, i) => e.label && (
        <text key={i} x={e.mx} y={e.bend || e.tb ? e.my + 4 : e.my - 6} dx={e.bend || e.tb ? 8 : 0} textAnchor={e.bend || e.tb ? "start" : "middle"} fontSize={12} className="fill-muted-foreground">{e.label}</text>
      ))}
      {block.nodes.map((n, i) => (
        <g key={n.id}>
          <rect x={g.pos[i].x} y={g.pos[i].y} width={box.w} height={box.h} rx={style === "terminal" ? 0 : 2}
            fill={style === "terminal" ? "var(--card)" : "var(--background)"} stroke={stroke} strokeWidth={1} />
          <BoxText b={box} i={i} cx={g.pos[i].x + box.w / 2} y={g.pos[i].y} y0={box.detail[i].length ? 28 : box.h / 2 + 5 - (box.label[i].length - 1) * box.lh[0] / 2} gap={20} fs={[15, 12]}
            labelProps={{ className: "fill-foreground", fontWeight: style === "terminal" ? 600 : 500 }} detailProps={{ className: "fill-muted-foreground" }} />
        </g>
      ))}
    </svg>
    </div>
  )
}

// 刻度：0 起，约 4 段，步长取 1 / 2 / 2.5 / 5 × 10^k（与 recharts 默认刻度一致）
export function niceTicks(max: number, count = 4) {
  if (!(max > 0)) return [0, 1]
  const raw = max / count, mag = 10 ** Math.floor(Math.log10(raw))
  const step = [1, 2, 2.5, 5, 10].map(s => s * mag).find(s => s >= raw)!
  return Array.from({ length: Math.ceil(max / step - 1e-9) + 1 }, (_, i) => +(i * step).toPrecision(12))
}

export function useWidth<T extends HTMLElement>() {
  const ref = useRef<T>(null)
  const [w, setW] = useState(0)
  useLayoutEffect(() => {
    const el = ref.current!
    // 首帧前同步取宽：ResizeObserver 回调异步，到达前宽度为 0 会让 flow/graph 按单排缩成小字
    setW(el.clientWidth)
    const ro = new ResizeObserver(() => setW(el.clientWidth))
    ro.observe(el)
    return () => ro.disconnect()
  }, [])
  return [ref, w] as const
}

// 程序员风分组柱状图（替代 recharts）：横向网格、无轴线、柱圆角 2、底部图例、悬停显示分类提示框
export function DataChart({ block }: { block: ChartBlock }) {
  const [ref, cw] = useWidth<HTMLDivElement>()
  const [hover, setHover] = useState<{ i: number; x: number; y: number } | null>(null)
  const H = 288 - 28, top = 8, L = 8 + 64, R = 8, axisH = 30
  const plotB = H - axisH, ticks = niceTicks(Math.max(...block.data.flatMap(d => block.series.map(s => Number(d[s.key])))))
  const vmax = ticks[ticks.length - 1], y = (v: number) => plotB - (v / vmax) * (plotB - top)
  const band = Math.max(0, cw - L - R) / Math.max(1, block.data.length), gap = 4, k = block.series.length
  const bw = Math.max(1, (band * 0.8 - (k - 1) * gap) / k)
  const color = (j: number) => `var(--chart-${j + 1})`
  return (
    <div ref={ref} data-slot="chart" className="relative flex h-72 w-full flex-col text-xs">
      {cw > 0 && <svg width={cw} height={H} className="overflow-visible" role="img" aria-label={block.caption}
        onMouseLeave={() => setHover(null)}
        onMouseMove={e => {
          const r = e.currentTarget.getBoundingClientRect(), px = e.clientX - r.left, i = Math.floor((px - L) / band)
          setHover(i >= 0 && i < block.data.length && e.clientY - r.top <= plotB ? { i, x: px, y: e.clientY - r.top } : null)
        }}>
        {ticks.map(t => <line key={t} x1={L} x2={cw - R} y1={y(t)} y2={y(t)} className="stroke-border/50" />)}
        {ticks.map(t => <text key={t} x={L - 8} y={y(t)} dy="0.355em" textAnchor="end" className="fill-muted-foreground">{t} {block.unit}</text>)}
        {hover && <rect x={L + hover.i * band} y={top} width={band} height={plotB - top} className="fill-muted" />}
        {block.data.map((d, i) => (
          <g key={i}>
            {block.series.map((s, j) => {
              const v = Number(d[s.key]), x = L + i * band + band * 0.1 + j * (bw + gap), h = plotB - y(v)
              return <path key={s.key} d={`M${x},${plotB} V${plotB - h + Math.min(2, h)} Q${x},${plotB - h} ${x + Math.min(2, bw / 2)},${plotB - h} H${x + bw - Math.min(2, bw / 2)} Q${x + bw},${plotB - h} ${x + bw},${plotB - h + Math.min(2, h)} V${plotB} Z`} fill={color(j)} />
            })}
            <text x={L + i * band + band / 2} y={plotB + 8} dy="0.71em" textAnchor="middle" className="fill-muted-foreground">{String(d.stage)}</text>
          </g>
        ))}
      </svg>}
      <div className="flex items-center justify-center gap-4 pt-3">
        {block.series.map((s, j) => (
          <div key={s.key} className="flex items-center gap-1.5"><div className="h-2 w-2 shrink-0 rounded-[2px]" style={{ backgroundColor: color(j) }} />{s.label}</div>
        ))}
      </div>
      {hover && (
        <div className="pointer-events-none absolute grid min-w-32 items-start gap-1.5 rounded-lg border border-border/50 bg-background px-2.5 py-1.5 text-xs shadow-xl"
          style={{ left: Math.min(hover.x + 10, cw - 140), top: hover.y + 10 }}>
          <div className="font-medium">{String(block.data[hover.i].stage)}</div>
          <div className="grid gap-1.5">
            {block.series.map((s, j) => (
              <div key={s.key} className="flex w-full items-center gap-2">
                <div className="h-2.5 w-2.5 shrink-0 rounded-[2px]" style={{ backgroundColor: color(j) }} />
                <div className="flex flex-1 items-center justify-between leading-none">
                  <span className="text-muted-foreground">{s.label}</span>
                  <span className="font-mono font-medium text-foreground tabular-nums">{Number(block.data[hover.i][s.key]).toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export function Code({ code, lang }: { code: string; lang: string }) {
  const html = lang === "text" ? code.replace(/&/g, "&amp;").replace(/</g, "&lt;")
    : hljs.getLanguage(lang) ? hljs.highlight(code, { language: lang }).value : hljs.highlightAuto(code).value
  return (
    <pre className="overflow-x-auto bg-(--code-bg) p-4 font-mono text-[13px] leading-relaxed">
      <code dangerouslySetInnerHTML={{ __html: html }} />
    </pre>
  )
}

// 叠放图：上层压住下层，最上层（layers[0]）用强调色描边；右侧箭头标注覆盖方向
export function StackFig({ layers, note }: { layers: { label: string; detail: string }[]; note?: string }) {
  const n = layers.length, w = 460, h = 64, step = 48, dx = 28, top = 34
  const arrowX = 20 + (n - 1) * dx + w + 36, H = top + (n - 1) * step + h + 12
  return (
    <svg viewBox={`0 0 ${arrowX + 30} ${H}`} className="w-full max-w-[44rem]" role="img" aria-label={layers.map(l => l.label).join(" > ")}>
      {layers.map((_, k) => n - 1 - k).map(i => {
        const x = 20 + i * dx, y = top + i * step
        return (
          <g key={i}>
            <rect x={x} y={y} width={w} height={h} rx={3} className="fill-background" stroke={i ? "var(--foreground)" : "var(--primary)"} strokeWidth={i ? 1 : 2} />
            <text x={x + 14} y={y + 36} fontSize={15} fontWeight={600} className={i ? "fill-foreground" : "fill-primary"}>{layers[i].label}</text>
            <text x={x + 14} y={y + 55} fontSize={12} className="fill-muted-foreground">{layers[i].detail}</text>
          </g>
        )
      })}
      <defs>
        <marker id="stack-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" fill="var(--foreground)" />
        </marker>
      </defs>
      <line x1={arrowX} y1={H - 14} x2={arrowX} y2={top + 4} stroke="var(--foreground)" strokeWidth={1.2} markerEnd="url(#stack-arrow)" />
      {note && <text x={arrowX} y={18} textAnchor="middle" fontSize={12} className="fill-muted-foreground">{note}</text>}
    </svg>
  )
}

export const circled = (i: number) => String.fromCodePoint(0x2460 + i)

// 整页线框示意：八个区域按页面结构固定排布，编号 ①–⑧ 与图例一一对应
export function Wireframe({ regions }: { regions: { label: string; detail: string }[] }) {
  const W = 380, H = 500
  const box = (x: number, y: number, w: number, h: number, k: number) =>
    <rect key={`${k}-${x}-${y}`} x={x} y={y} width={w} height={h} rx={2} className="fill-muted" stroke="var(--foreground)" strokeOpacity={0.45} />
  const mark = (x: number, y: number, i: number) => i < regions.length && (
    <g key={`m${i}`}>
      <circle cx={x} cy={y} r={11} fill="var(--primary)" />
      <text x={x} y={y + 4.5} textAnchor="middle" fontSize={13} fontWeight={700} fill="var(--primary-foreground)">{i + 1}</text>
    </g>)
  return (
    <svg viewBox={`0 0 ${W + 30} ${H}`} className="w-full max-w-[26rem]" role="img" aria-label={regions.map((r, i) => circled(i) + r.label).join("，")}>
      <rect x={10} y={6} width={W} height={H - 12} rx={4} className="fill-background" stroke="var(--foreground)" strokeWidth={1.5} />
      {/* ⑧ 水印：斜向平铺 */}
      {[0, 1, 2, 3].map(r => (
        <text key={r} x={40} y={140 + r * 100} fontSize={14} className="fill-foreground" fillOpacity={0.12} transform={`rotate(-30 40 ${140 + r * 100})`}>watermark · watermark · watermark</text>
      ))}
      {box(26, 22, 348, 50, 0)}
      <rect x={38} y={34} width={26} height={26} rx={2} className="fill-background" stroke="var(--foreground)" strokeOpacity={0.45} />
      <rect x={74} y={36} width={170} height={10} className="fill-foreground" fillOpacity={0.55} />
      <rect x={74} y={52} width={230} height={6} className="fill-foreground" fillOpacity={0.25} />
      {box(26, 82, 348, 40, 1)}
      {[0, 1, 2, 3].map(k => box(26 + k * 89, 132, 81, 34, 2))}
      {box(26, 176, 170, 110, 3)}{box(204, 176, 170, 110, 3)}{box(26, 294, 348, 54, 3)}
      {box(26, 358, 348, 36, 4)}
      {box(26, 404, 348, 30, 5)}
      <line x1={10} y1={446} x2={W + 10} y2={446} stroke="var(--foreground)" strokeOpacity={0.45} />
      {[0, 1, 2].map(k => <rect key={k} x={26 + k * 120} y={458} width={100} height={8} className="fill-foreground" fillOpacity={0.3} />)}
      {[[374, 22], [374, 82], [374, 132], [374, 176], [374, 358], [374, 404], [W + 10, 446], [W + 10, 230]].map(([x, y], i) => mark(x, y, i))}
    </svg>
  )
}

// 多栏并排代码块：栏数 = 面板数，窄屏单列
export function CodePanes({ panes, wrap }: { panes: { title: string; lang: string; code: string }[]; wrap: (title: string, lang: string, body: React.ReactNode, i: number) => React.ReactNode }) {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-(--cols)" style={{ "--cols": `repeat(${panes.length}, minmax(0, 1fr))` } as React.CSSProperties}>
      {panes.map((p, i) => <div key={i} className="min-w-0">{wrap(p.title, p.lang, <Code code={p.code} lang={p.lang} />, i)}</div>)}
    </div>
  )
}

// 表格单元格：mono 列等宽显示（kv 缺省第 0 列）
export const cellMono = (b: { type: string; mono?: number[] }) => new Set(b.mono ?? (b.type === "kv" ? [0] : []))
