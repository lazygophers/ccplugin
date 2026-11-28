import { useLayoutEffect, useRef, useState } from "react"
import rough from "roughjs"
import type { Drawable, Options } from "roughjs/bin/core"
import { BoxText, Code, CodePanes, StackFig, Wireframe, cellMono, circled, fitCols, fitGraph, layout, nodeBox, useWidth } from "@/figures"
import { MetaLine, WmImg } from "@/chrome"
import { measure, sections, SectionGrid, spanCls, type Item } from "@/layout"
import type { ChartBlock, FlowNode, GraphBlock, Page } from "@/types"

/* 手绘风：Excalidraw 白板（点阵画布、rough.js 马克笔描边与实色浅填充）+ xkcd 图表 + 视觉笔记（荧光笔、便利贴、编号圈） */

const gen = rough.generator()
const INK = "#1e1e1e"
// Excalidraw 调色板浅色档（excalidraw/excalidraw:packages/common/src/colors.ts）
export const FILLS = ["#ffec99", "#a5d8ff", "#b2f2bb", "#ffc9c9"]
const STRONG = ["#f08c00", "#1971c2", "#2f9e44", "#e03131"]
// 马克笔笔触：粗、圆润、弯曲小；填充一律实色，不用排线
const PEN: Options = { stroke: INK, strokeWidth: 2.2, roughness: 1.2, bowing: 0.6 }
// 手绘方框（流程节点、便利贴、表格框、代码框、步骤卡）：抖动与弯曲更大，线条更歪扭
const BOX: Options = { ...PEN, roughness: 2.2, bowing: 1.8 }
// 柱状图沿用 hachure 排线柱；两系列 P50 蓝、P95 红（调色板深色档）
const SERIES = [STRONG[1], STRONG[3]]
const bar = (seed: number, k: number): Options => ({ ...PEN, seed, fill: SERIES[k % 2], fillStyle: "hachure", hachureGap: 6, fillWeight: 1.6 })

function Paths({ d }: { d: Drawable[] }) {
  return d.flatMap((dr, k) => gen.toPaths(dr).map((p, j) => (
    <path key={`${k}-${j}`} d={p.d} stroke={p.stroke} strokeWidth={p.strokeWidth} fill={p.fill ?? "none"} />
  )))
}

function rrect(x: number, y: number, w: number, h: number, r = 12) {
  return `M${x + r},${y} L${x + w - r},${y} Q${x + w},${y} ${x + w},${y + r} L${x + w},${y + h - r} Q${x + w},${y + h} ${x + w - r},${y + h} L${x + r},${y + h} Q${x},${y + h} ${x},${y + h - r} L${x},${y + r} Q${x},${y} ${x + r},${y} Z`
}

function arrow(x1: number, y1: number, x2: number, y2: number, seed: number, o: Options = {}) {
  const a = Math.atan2(y2 - y1, x2 - x1), L = 12
  const head = (s: number) => gen.line(x2, y2, x2 - L * Math.cos(a + s), y2 - L * Math.sin(a + s), { ...PEN, seed, ...o })
  return [gen.line(x1, y1, x2, y2, { ...PEN, seed, bowing: 1, ...o }), head(0.5), head(-0.5)]
}

// 任意 HTML 块外套一层手绘框：按实际尺寸重绘，线条不随缩放变形
export function RoughBox({ children, className = "", seed = 1, fill, round = true, rotate = 0 }: {
  children: React.ReactNode; className?: string; seed?: number; fill?: string; round?: boolean; rotate?: number
}) {
  const ref = useRef<HTMLDivElement>(null)
  const [size, setSize] = useState({ w: 0, h: 0 })
  useLayoutEffect(() => {
    const el = ref.current!
    const ro = new ResizeObserver(() => setSize({ w: el.offsetWidth, h: el.offsetHeight }))
    ro.observe(el)
    return () => ro.disconnect()
  }, [])
  const o: Options = { ...BOX, seed, fill, fillStyle: "solid" }
  const { w, h } = size
  const shape = w && h ? [round ? gen.path(rrect(3, 3, w - 6, h - 6, 14), o) : gen.rectangle(3, 3, w - 6, h - 6, o)] : []
  return (
    <div ref={ref} className={`relative ${className}`} style={rotate ? { transform: `rotate(${rotate}deg)` } : undefined}>
      <svg className="pointer-events-none absolute inset-0 h-full w-full overflow-visible" aria-hidden><Paths d={shape} /></svg>
      <div className="relative">{children}</div>
    </div>
  )
}

// 手写编号圈
function NumCircle({ n, seed, color = INK, size = 44 }: { n: number | string; seed: number; color?: string; size?: number }) {
  return (
    <span className="relative inline-flex shrink-0 items-center justify-center font-heading text-xl" style={{ width: size, height: size, color }}>
      <svg viewBox="0 0 44 44" className="absolute inset-0 overflow-visible" aria-hidden>
        <Paths d={[gen.circle(22, 22, 38, { ...PEN, stroke: color, seed })]} />
      </svg>
      <span className="relative">{n}</span>
    </span>
  )
}

// 手绘图标：对勾、星号、灯泡式感叹
function Icon({ kind, seed, className = "size-7" }: { kind: "check" | "star" | "bang"; seed: number; className?: string }) {
  const o: Options = { ...PEN, seed }
  const d = kind === "check" ? [gen.linearPath([[4, 16], [11, 23], [24, 6]], o)]
    : kind === "star" ? [gen.polygon([[14, 2], [17, 10], [26, 10], [19, 15], [22, 24], [14, 19], [6, 24], [9, 15], [2, 10], [11, 10]], { ...o, fill: FILLS[0], fillStyle: "solid" })]
    : [gen.line(14, 3, 14, 17, o), gen.circle(14, 23, 3, { ...o, fill: INK, fillStyle: "solid" })]
  return <svg viewBox="0 0 28 28" className={`shrink-0 overflow-visible ${className}`} aria-hidden><Paths d={d} /></svg>
}

const Mark = ({ children, c = FILLS[0] }: { children: React.ReactNode; c?: string }) => (
  <mark className="box-decoration-clone px-1 text-inherit" style={{ background: `linear-gradient(104deg, transparent 0.4em, ${c} 0.5em, ${c} 92%, transparent)`, backgroundSize: "100% 62%", backgroundPosition: "0 78%", backgroundRepeat: "no-repeat" }}>{children}</mark>
)

function SketchFlow({ nodes }: { nodes: FlowNode[] }) {
  const box = nodeBox(nodes, { minW: 200, maxW: 300, h: 92, fs: [21, 14], lh: [26, 19], pad: 16 }), { w, h } = box
  const [ref, cw] = useWidth<HTMLDivElement>()
  const { pos, edges, width, height } = layout(nodes.length, fitCols(nodes.length, w, 64, cw, 12 / 14), w, h, 64, 60)
  return (
    <div ref={ref} className="flex flex-col">
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full overflow-visible" role="img" aria-label={nodes.map(n => n.label).join(" → ")}>
      {pos.map((p, i) => (
        <g key={i}>
          <Paths d={[gen.path(rrect(p.x, p.y, w, h, 16), { ...BOX, seed: 11 + i, fill: FILLS[i % 4], fillStyle: "solid" })]} />
          <BoxText b={box} i={i} cx={p.x + w / 2} y={p.y} y0={40} gap={28} fs={[21, 14]} labelProps={{ fill: INK, className: "font-heading" }} detailProps={{ fill: INK }} />
          <circle cx={p.x + 8} cy={p.y + 8} r={13} fill="#fff" />
          <Paths d={[gen.circle(p.x + 8, p.y + 8, 26, { ...PEN, strokeWidth: 2, seed: 40 + i })]} />
          <text x={p.x + 8} y={p.y + 14} textAnchor="middle" fontSize={16} fill={INK}>{i + 1}</text>
        </g>
      ))}
      {edges.map((e, i) => <Paths key={i} d={arrow(e.x1 + 4, e.y1, e.x2 - 4, e.y2, 70 + i)} />)}
    </svg>
    </div>
  )
}

// 手绘有向图：节点按车道取浅色实填充（主线黄、分支蓝…），连线为手绘曲线 + 手绘箭头
function SketchGraph({ block }: { block: GraphBlock }) {
  const box = nodeBox(block.nodes, { minW: 140, maxW: 300, h: 92, fs: [21, 14], lh: [26, 19], pad: 16 }), { w, h } = box
  const [ref, cw] = useWidth<HTMLDivElement>()
  const g = fitGraph(block, w, h, 72, 36, cw, 12 / 14)
  return (
    <div ref={ref} className="flex flex-col">
    <svg viewBox={`0 0 ${g.width} ${g.height}`} className="w-full overflow-visible" style={{ maxWidth: g.width * 1.25 }} role="img" aria-label={block.edges.map(e => `${e.from} → ${e.to}`).join("，")}>
      {g.edges.map((e, i) => {
        const a = e.tb ? Math.PI / 2 : 0, L = 12
        const head = (s: number) => gen.line(e.x2, e.y2, e.x2 - L * Math.cos(a + s), e.y2 - L * Math.sin(a + s), { ...PEN, seed: 80 + i })
        return <g key={i}>
          <Paths d={[gen.path(e.d, { ...PEN, seed: 70 + i }), head(0.5), head(-0.5)]} />
          {e.label && <text x={e.mx} y={e.bend || e.tb ? e.my + 5 : e.my - 10} dx={e.bend || e.tb ? 10 : 0} textAnchor={e.bend || e.tb ? "start" : "middle"} fontSize={15} fill={INK}>{e.label}</text>}
        </g>
      })}
      {block.nodes.map((n, i) => {
        const p = g.pos[i]
        return (
          <g key={n.id}>
            <Paths d={[gen.path(rrect(p.x, p.y, w, h, 16), { ...BOX, seed: 11 + i, fill: FILLS[g.lane[i] % 4], fillStyle: "solid" })]} />
            <BoxText b={box} i={i} cx={p.x + w / 2} y={p.y} y0={box.detail[i].length ? 40 : h / 2 + 7 - (box.label[i].length - 1) * box.lh[0] / 2} gap={28} fs={[21, 14]} labelProps={{ fill: INK, className: "font-heading" }} detailProps={{ fill: INK }} />
          </g>
        )
      })}
    </svg>
    </div>
  )
}

// xkcd 风格柱状图：rough.js 自绘坐标轴、实色填充柱、手写标签
function XkcdBars({ block }: { block: ChartBlock }) {
  const W = 640, H = 330, L = 56, B = 52, T = 40, R = 16
  const max = Math.max(...block.data.flatMap(d => block.series.map(s => Number(d[s.key])))) * 1.1
  const gw = (W - L - R) / block.data.length, bw = (gw * 0.7) / block.series.length
  const y = (v: number) => H - B - (v / max) * (H - B - T)
  const ax: Options = { ...PEN, seed: 3 }
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full max-w-[56rem] overflow-visible" role="img" aria-label={block.caption}>
      <Paths d={[...arrow(L, H - B, W - R + 6, H - B, 5), ...arrow(L, H - B, L, T - 18, 6)]} />
      <text x={L - 8} y={T - 22} textAnchor="end" fontSize={14} fill={INK}>{block.unit}</text>
      {block.data.map((d, i) => (
        <g key={i}>
          {block.series.map((s, k) => {
            const v = Number(d[s.key]), x = L + i * gw + gw * 0.15 + k * bw
            return (
              <g key={s.key}>
                <Paths d={[gen.rectangle(x, y(v), bw - 4, H - B - y(v), bar(100 + i * 7 + k, k))]} />
                <text x={x + (bw - 4) / 2} y={y(v) - 6} textAnchor="middle" fontSize={13} fill={INK}>{v}</text>
              </g>
            )
          })}
          <text x={L + i * gw + gw / 2} y={H - B + 22} textAnchor="middle" fontSize={15} fill={INK}>{String(d.stage)}</text>
        </g>
      ))}
      {block.series.map((s, k) => (
        <g key={s.key} transform={`translate(${W - R - 170 + k * 84}, ${T - 22})`}>
          <Paths d={[gen.rectangle(0, -12, 18, 14, bar(200 + k, k))]} />
          <text x={26} y={0} fontSize={15} fill={INK}>{s.label}</text>
        </g>
      ))}
    </svg>
  )
}

function Point({ text, i }: { text?: string; i: number }) {
  if (!text) return null
  return <p className="flex items-center gap-2 font-heading text-2xl"><Icon kind="bang" seed={300 + i} className="size-6" /><Mark c={FILLS[i % 4]}>{text}</Mark></p>
}

export function SketchPage({ page }: { page: Page }) {
  const secs = sections(page.blocks)

  const block = ({ b, i, n }: Item) => {
    switch (b.type) {
      case "heading": return null
      case "paragraph": return <p className={`${measure} text-lg leading-8`}>{b.text}</p>
      case "flow": return (
        <figure className="flex flex-col gap-4">
          <Point text={b.point} i={i} />
          <SketchFlow nodes={b.nodes} />
          <figcaption className="text-center text-base opacity-70">图 {n} · {b.caption}</figcaption>
        </figure>)
      case "graph": return (
        <figure className="flex flex-col gap-4">
          <Point text={b.point} i={i} />
          <SketchGraph block={b} />
          <figcaption className="text-center text-base opacity-70">图 {n} · {b.caption}</figcaption>
        </figure>)
      case "list": return (
        <ul className={`flex flex-col gap-2 ${measure} text-lg leading-8`}>
          {b.items.map((x, j) => (
            <li key={j} className="flex items-start gap-3">
              {b.ordered ? <NumCircle n={j + 1} seed={120 + j} size={32} /> : <Icon kind="check" seed={130 + j} className="mt-1 size-6" />}
              <span>{x.title && <Mark c={FILLS[j % 4]}>{x.title}</Mark>}{x.title && "："}{x.text}</span>
            </li>
          ))}
        </ul>)
      case "stack": return (
        <figure className="flex flex-col gap-4">
          <Point text={b.point} i={i} />
          <StackFig layers={b.layers} note={b.note} />
          <figcaption className="text-center text-base opacity-70">图 {n} · {b.caption}</figcaption>
        </figure>)
      case "wireframe": return (
        <figure className="flex flex-col gap-4">
          <Point text={b.point} i={i} />
          <div className="grid grid-cols-1 items-center gap-8 md:grid-cols-[minmax(0,26rem)_minmax(0,1fr)]">
            <Wireframe regions={b.regions} />
            <ol className="flex flex-col gap-2 text-lg leading-7">
              {b.regions.map((r, j) => <li key={j}><span className="font-heading">{circled(j)} <Mark c={FILLS[j % 4]}>{r.label}</Mark></span>　{r.detail}</li>)}
            </ol>
          </div>
          <figcaption className="text-center text-base opacity-70">图 {n} · {b.caption}</figcaption>
        </figure>)
      case "codes": return (
        <figure className="flex flex-col gap-4">
          <Point text={b.point} i={i} />
          <CodePanes panes={b.panes} wrap={(t, _l, body, k) => (
            <RoughBox seed={140 + k} className="h-full overflow-hidden p-2">
              <p className="px-3 pt-1 font-heading text-base opacity-70">{t}</p>
              <div className="[&_pre]:whitespace-pre-wrap [&_pre]:break-all">{body}</div>
            </RoughBox>)} />
          <figcaption className="text-center text-base opacity-70">清单 {n} · {b.caption}</figcaption>
        </figure>)
      case "kv":
      case "table": return (
        <figure className="flex flex-col gap-4">
          <Point text={b.point} i={i} />
          <RoughBox seed={i + 1} round={false} className="px-4 py-3">
            <table className="w-full border-collapse text-left text-lg">
              <thead><tr>{b.columns.map((c, k) => <th key={c} className="border-b-2 border-dashed border-[#1e1e1e] px-3 py-2 font-heading font-normal">{k ? <Mark c={FILLS[k % 4]}>{c}</Mark> : c}</th>)}</tr></thead>
              <tbody>{b.rows.map((r, j) => <tr key={j} className="border-b border-dashed border-[#1e1e1e]/40 last:border-0">{r.map((v, k) => <td key={k} className="px-3 py-2 align-top">{cellMono(b).has(k) ? <code className="font-mono text-[0.85em]">{v}</code> : v}</td>)}</tr>)}</tbody>
            </table>
          </RoughBox>
          <figcaption className="text-center text-base opacity-70">表 {n} · {b.caption}</figcaption>
        </figure>)
      case "chart": return (
        <figure className="flex flex-col items-center gap-4">
          <div className="self-start"><Point text={b.point} i={i} /></div>
          <XkcdBars block={b} />
          <figcaption className="text-center text-base opacity-70">图 {n} · {b.caption}</figcaption>
          {b.note && <RoughBox seed={i + 9} fill={FILLS[3]} rotate={-1} className="max-w-[40em] px-5 py-3 text-base"><span className="flex gap-2"><Icon kind="bang" seed={i} className="size-5" />{b.note}</span></RoughBox>}
        </figure>)
      case "image": return (
        <figure className="flex flex-col gap-4">
          <Point text={b.point} i={i} />
          <RoughBox seed={i + 6} className="flex justify-center p-4"><WmImg page={page} src={b.src} alt={b.alt ?? b.caption} className="max-h-[36rem] max-w-full" /></RoughBox>
          <figcaption className="text-center text-base opacity-70">图 {n} · {b.caption}</figcaption>
        </figure>)
      case "code": return (
        <figure className="flex flex-col gap-4">
          <Point text={b.point} i={i} />
          <RoughBox seed={i + 4} className="overflow-hidden p-2">
            <p className="px-3 pt-1 font-heading text-base opacity-70">{b.filename}</p>
            <Code code={b.code} lang={b.lang} />
          </RoughBox>
          <figcaption className="text-center text-base opacity-70">清单 {n} · {b.caption}</figcaption>
        </figure>)
      case "steps": return (
        <figure className="flex flex-col gap-4">
          <Point text={b.point} i={i} />
          <ol className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {b.items.map((s, j) => (
              <li key={s.title}>
                <RoughBox seed={50 + j} fill={FILLS[j % 4]} rotate={j % 2 ? 1 : -1} round={false} className="h-full px-4 py-3">
                  <div className="flex items-start gap-3">
                    <NumCircle n={j + 1} seed={60 + j} />
                    <div className="flex flex-col"><span className="font-heading text-xl">{s.title}</span><span className="text-base leading-6">{s.detail}</span></div>
                  </div>
                </RoughBox>
              </li>
            ))}
          </ol>
        </figure>)
    }
  }

  return (
    <main className="flex flex-col gap-12 px-8 pb-16 pt-10 text-lg">
      <header className="grid grid-cols-1 items-center gap-8 min-[1440px]:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <div className="flex flex-col gap-4">
          <h1 className="font-heading text-5xl leading-tight min-[1440px]:text-6xl"><Mark>{page.title}</Mark></h1>
          <p className="text-2xl opacity-80">{page.subtitle}</p>
          <p className={`${measure} text-lg leading-8`}>{page.summary.text}</p>
          <p className="text-sm opacity-60">{page.meta.author} · {page.meta.date}</p>
          <MetaLine page={page} className="text-sm opacity-70" />
        </div>
        <div className="flex flex-col gap-5">
          <RoughBox seed={7} fill={FILLS[0]} rotate={-1.5} round={false} className="self-start px-6 py-4">
            <p className="flex items-center gap-3 font-heading text-4xl"><Icon kind="star" seed={8} className="size-10" />{page.summary.point}</p>
          </RoughBox>
          <ul className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {page.summary.points.map((p, j) => (
              <li key={p}>
                <RoughBox seed={20 + j} fill={FILLS[(j + 1) % 4]} rotate={[1.2, -0.8, 0.6][j % 3]} round={false} className="h-full px-4 py-3">
                  <span className="flex gap-2 text-base leading-6"><Icon kind="check" seed={30 + j} className="size-6" />{p}</span>
                </RoughBox>
              </li>
            ))}
          </ul>
        </div>
      </header>

      <SectionGrid className="gap-x-12 gap-y-14">
        {secs.map((s, si) => (
          <section key={si} className={`flex flex-col gap-5 ${spanCls(s)}`}>
            {s.title && <h2 className="flex items-center gap-3 font-heading text-3xl"><NumCircle n={s.n} seed={90 + si} color={STRONG[si % 4]} size={48} />{s.title}</h2>}
            {s.items.map(it => <div key={it.i}>{block(it)}</div>)}
          </section>
        ))}
      </SectionGrid>

      {page.conclusion && <RoughBox seed={99} fill={FILLS[0]} rotate={-0.6} round={false} className="mx-auto w-full max-w-[60em] px-8 py-6">
        <p className="flex items-start gap-3 text-2xl leading-relaxed"><Icon kind="star" seed={98} className="mt-1 size-8" /><span><span className="font-heading">一句话：</span>{page.conclusion}</span></p>
      </RoughBox>}

      <footer className="flex flex-col gap-1 text-sm opacity-70">
        {page.references.map((r, i) => <p key={i}>[{i + 1}] {r.text} — <span className="font-mono">{r.source}</span></p>)}
      </footer>
    </main>
  )
}
