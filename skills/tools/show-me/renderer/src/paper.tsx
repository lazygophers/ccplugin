import { Code, CodePanes, Flow, Graph, StackFig, Wireframe, cellMono, circled } from "@/figures"
import { MetaLine, WmImg } from "@/chrome"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { kpis, measure, sections, SectionGrid, spanCls, type Item } from "@/layout"
import type { ChartBlock, Page } from "@/types"

/* 科研风：海报横幅 + Distill 署名块 → 看板 KPI → Nature 摘要 → Tufte 正文与旁注 → Distill 宽图 → 编号参考文献 */

function Spark({ values, className }: { values: number[]; className?: string }) {
  const max = Math.max(...values), w = 6, g = 3
  return (
    <svg viewBox={`0 0 ${values.length * (w + g)} 24`} className={className} aria-hidden>
      {values.map((v, i) => {
        const h = Math.max(1, (v / max) * 22)
        return <rect key={i} x={i * (w + g)} y={24 - h} width={w} height={h} className={v === max ? "fill-primary" : "fill-foreground/70"} />
      })}
    </svg>
  )
}

// Tufte 式极简图：每个阶段一行，各系列为点，点间连线表示区间，数值直接标注，无网格、无图例框
function RangeChart({ block }: { block: ChartBlock }) {
  const max = Math.max(...block.data.flatMap(d => block.series.map(s => Number(d[s.key]))))
  const L = 110, R = 60, W = 640, row = 34, top = 30
  const x = (v: number) => L + (v / max) * (W - L - R)
  const H = top + block.data.length * row + 10
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full max-w-[52rem]" role="img" aria-label={block.caption}>
      {block.series.map((s, k) => (
        <text key={s.key} x={L + k * 90} y={14} fontSize={12} className={k ? "fill-primary" : "fill-foreground"}>● {s.label}</text>
      ))}
      {block.data.map((d, i) => {
        const y = top + i * row + row / 2
        const vs = block.series.map(s => Number(d[s.key]))
        return (
          <g key={i}>
            <text x={L - 12} y={y + 4} textAnchor="end" fontSize={13} className="fill-foreground">{String(d.stage)}</text>
            <line x1={x(Math.min(...vs))} x2={x(Math.max(...vs))} y1={y} y2={y} className="stroke-foreground/40" strokeWidth={2} />
            {vs.map((v, k) => (
              <g key={k}>
                <circle cx={x(v)} cy={y} r={4.5} className={k ? "fill-primary" : "fill-foreground"} />
                {k === vs.length - 1 && <text x={x(v) + 9} y={y + 4} fontSize={12} className="fill-primary">{v}</text>}
                {k === 0 && vs.length > 1 && <text x={x(v) - 8} y={y - 8} textAnchor="middle" fontSize={11} className="fill-muted-foreground">{v}</text>}
              </g>
            ))}
          </g>
        )
      })}
      <text x={W - R} y={H - 2} textAnchor="end" fontSize={11} className="fill-muted-foreground">单位：{block.unit}</text>
    </svg>
  )
}

function Caption({ label, title, mark, children }: { label: string; title: string; mark?: number; children?: React.ReactNode }) {
  return (
    <figcaption className="text-[15px] leading-6">
      <b>{label}</b> | <b>{title}</b>{mark ? <sup className="text-primary">{mark}</sup> : null}{children ? <>　{children}</> : null}
    </figcaption>
  )
}

// 一行 = 主栏 + 边栏旁注（Tufte）；宽屏下旁注在右侧栏，窄屏下旁注落到主栏下方
function Row({ main, note, mark, full }: { main: React.ReactNode; note?: React.ReactNode; mark?: number; full?: boolean }) {
  return (
    <div className={full ? "flex flex-col gap-3" : "grid grid-cols-1 gap-x-8 gap-y-2 md:grid-cols-[minmax(0,1fr)_14em]"}>
      <div className="min-w-0">{main}</div>
      {note && (
        <aside className="border-l border-foreground/20 pl-3 text-[13px] leading-5 text-muted-foreground">
          {mark ? <sup className="mr-1 text-primary">{mark}</sup> : null}{note}
        </aside>
      )}
    </div>
  )
}

export function PaperPage({ page }: { page: Page }) {
  const secs = sections(page.blocks)
  const ks = kpis(page)
  let mark = 0
  const cite = `${page.meta.author}. ${page.title}：${page.subtitle}. ${page.meta.date}.`

  const block = ({ b, n }: Item) => {
    switch (b.type) {
      case "heading": return null
      case "paragraph": return <Row main={<p className={`indent-8 ${measure}`}>{b.text}</p>} />
      case "flow": {
        const m = ++mark
        return (
          <Row full main={
            <figure className="flex flex-col gap-3">
              <div className="border-y border-foreground/20 py-4"><Flow nodes={b.nodes} style="paper" cols={b.nodes.length} /></div>
              <Caption label={`图 ${n}`} title={b.caption} mark={m}>
                <span className="text-muted-foreground"><sup className="text-primary">{m}</sup> {b.point ? `${b.point}：` : ""}{b.nodes.map(x => x.label).join(" → ")}。</span>
              </Caption>
            </figure>} />)
      }
      case "graph": {
        const m = ++mark
        return (
          <Row full main={
            <figure className="flex flex-col gap-3">
              <div className="flex justify-center border-y border-foreground/20 py-4"><Graph block={b} style="paper" /></div>
              <Caption label={`图 ${n}`} title={b.caption} mark={b.point ? m : undefined}>
                {b.point && <span className="text-muted-foreground"><sup className="text-primary">{m}</sup> {b.point}。</span>}
              </Caption>
            </figure>} />)
      }
      case "list": {
        const Tag = b.ordered ? "ol" : "ul"
        return <Row main={
          <Tag className={`flex flex-col gap-1 ${measure}`}>
            {b.items.map((x, j) => (
              <li key={j} className="grid grid-cols-[2.5em_1fr]">
                <span className="text-primary">{b.ordered ? `(${j + 1})` : "•"}</span>
                <span>{x.title && <b>{x.title}：</b>}{x.text}</span>
              </li>
            ))}
          </Tag>} />
      }
      case "stack": {
        const m = ++mark
        return (
          <Row mark={b.point ? m : undefined} note={b.point} main={
            <figure className="flex flex-col gap-2">
              <div className="border-y border-foreground/20 py-3"><StackFig layers={b.layers} note={b.note} /></div>
              <Caption label={`图 ${n}`} title={b.caption} />
            </figure>} />)
      }
      case "wireframe": return (
        <Row full main={
          <figure className="flex flex-col gap-3">
            <div className="grid grid-cols-1 items-center gap-8 border-y border-foreground/20 py-4 md:grid-cols-[minmax(0,26rem)_minmax(0,1fr)]">
              <Wireframe regions={b.regions} />
              <ol className={`flex flex-col gap-1 ${measure}`}>
                {b.regions.map((r, j) => <li key={j} className="grid grid-cols-[2em_1fr]"><span className="text-primary">{circled(j)}</span><span><b>{r.label}：</b>{r.detail}</span></li>)}
              </ol>
            </div>
            <Caption label={`图 ${n}`} title={b.caption} />
          </figure>} />)
      case "codes": return (
        <Row full main={
          <figure className="flex flex-col gap-2">
            <Caption label={`清单 ${n}`} title={b.caption} />
            <CodePanes panes={b.panes} wrap={(t, _l, body) => (
              <div className="flex h-full flex-col border-y border-foreground/30">
                <p className="border-b border-foreground/15 px-4 py-1 text-sm font-semibold">{t}</p>
                <div className="flex-1 bg-(--code-bg) [&_pre]:whitespace-pre-wrap [&_pre]:break-all">{body}</div>
              </div>)} />
          </figure>} />)
      case "kv":
      case "table": {
        const m = ++mark
        const mono = cellMono(b)
        return (
          <Row mark={b.point ? m : undefined} note={b.point} main={
            <figure className="flex flex-col gap-2">
              <Caption label={`表 ${n}`} title={b.caption} mark={b.point ? m : undefined} />
              <Table>
                <TableHeader><TableRow>{b.columns.map(c => <TableHead key={c}>{c}</TableHead>)}</TableRow></TableHeader>
                <TableBody>{b.rows.map((r, j) => <TableRow key={j}>{r.map((v, k) => <TableCell key={k} className={`whitespace-normal align-top ${k ? "" : "font-semibold"}`}>{mono.has(k) ? <code className="font-mono text-[0.85em]">{v}</code> : v}</TableCell>)}</TableRow>)}</TableBody>
              </Table>
            </figure>} />)
      }
      case "chart": {
        const m = ++mark
        const last = b.series[b.series.length - 1]
        const vals = b.data.map(d => Number(d[last.key]))
        return (
          <>
            <Row mark={m} note={<><span>{[b.point, b.note].filter(Boolean).join("。")}</span><Spark values={vals} className="mt-2 h-6 w-24" /><span className="block">{last.label} 分布（深红 = 最大值）</span></>} main={
              <figure className="flex flex-col gap-2">
                <RangeChart block={b} />
                <Caption label={`图 ${n}`} title={b.caption} mark={m}><span className="text-muted-foreground">各阶段 {b.series.map(s => s.label).join(" 与 ")}，单位 {b.unit}。</span></Caption>
              </figure>} />
            {b.total && <Row main={
              <div className="flex items-baseline justify-between gap-4 py-1 text-[17px]">
                <span className="mx-auto italic">T<sub>{b.total}</sub> = Σ<sub>i</sub> {last.label}<sub>i</sub> = {vals.join(" + ")} = {vals.reduce((a, v) => a + v, 0)} {b.unit}</span>
                <span>(1)</span>
              </div>} />}
          </>)
      }
      case "image": {
        const m = ++mark
        return (
          <Row mark={b.point ? m : undefined} note={b.point} main={
            <figure className="flex flex-col gap-2">
              <div className="flex justify-center border-y border-foreground/20 py-3"><WmImg page={page} src={b.src} alt={b.alt ?? b.caption} className="max-h-[36rem] max-w-full" /></div>
              <Caption label={`图 ${n}`} title={b.caption} mark={b.point ? m : undefined} />
            </figure>} />)
      }
      case "code": {
        const m = ++mark
        return (
          <Row mark={m} note={<>{b.point}。文件 <code className="font-mono">{b.filename}</code>，语言 {b.lang}。</>} main={
            <figure className="flex flex-col gap-2">
              <Caption label={`清单 ${n}`} title={b.caption} mark={m} />
              <div className="border-y border-foreground/30"><Code code={b.code} lang={b.lang} /></div>
            </figure>} />)
      }
      case "steps": {
        const m = ++mark
        return (
          <Row mark={m} note={b.point} main={
            <ol className="flex flex-col gap-2">
              {b.items.map((s, j) => (
                <li key={s.title} className="grid grid-cols-[2.5em_1fr]">
                  <span className="text-primary">({j + 1})</span>
                  <span><b>{s.title}。</b>{s.detail}</span>
                </li>
              ))}
            </ol>} />)
      }
    }
  }

  return (
    <article className="flex flex-col gap-8 px-8 pb-16 pt-8 text-[17px] leading-8">
      {/* 海报式标题横幅 + Distill 署名块 */}
      <header className="border-b-2 border-t-[6px] border-b-foreground border-t-primary">
        <div className="flex flex-col gap-2 py-8">
          <p className="text-sm tracking-[0.3em] text-primary">TECHNICAL NOTE · 技术简报</p>
          <h1 className="font-heading text-4xl font-bold leading-tight min-[1440px]:text-5xl">{page.title}</h1>
          <p className="text-xl italic text-muted-foreground">{page.subtitle}</p>
          <MetaLine page={page} className="text-sm text-muted-foreground" />
        </div>
        <dl className="grid grid-cols-2 gap-x-8 gap-y-3 border-t border-foreground/20 py-4 text-sm md:grid-cols-4">
          <div><dt className="text-xs tracking-widest text-muted-foreground">作者</dt><dd>{page.meta.author}</dd></div>
          <div><dt className="text-xs tracking-widest text-muted-foreground">发布日期</dt><dd>{page.meta.date}</dd></div>
          <div><dt className="text-xs tracking-widest text-muted-foreground">章节</dt><dd>{secs.filter(s => s.title && !s.part).length + (page.conclusion ? 1 : 0)} 节 · 参考文献 {page.references.length} 条</dd></div>
          <div><dt className="text-xs tracking-widest text-muted-foreground">引用</dt><dd className="leading-5">{cite}</dd></div>
        </dl>
      </header>

      {/* 看板指标卡 */}
      {ks.length > 0 && <section aria-label="关键指标" className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {ks.map(k => (
          <div key={k.label} className="flex flex-col gap-1 border border-foreground/25 px-4 py-3">
            <span className="text-xs tracking-widest text-muted-foreground">{k.label}</span>
            <span className="flex items-end justify-between gap-2">
              <span className="text-4xl font-semibold tabular-nums">{k.value}<span className="ml-1 text-base font-normal text-muted-foreground">{k.unit}</span></span>
              {k.spark && <Spark values={k.spark} className="mb-1 h-8 w-20" />}
            </span>
            <span className="text-xs text-muted-foreground">{k.note}</span>
          </div>
        ))}
      </section>}

      {/* 期刊式摘要框 */}
      <section className={`grid grid-cols-1 gap-6 border-y border-foreground/60 bg-muted/60 px-6 py-5 ${page.summary.points.length ? "md:grid-cols-[minmax(0,1fr)_22em]" : ""}`}>
        <p className={measure}><b>摘要　</b>{page.summary.text}</p>
        {page.summary.points.length > 0 && <ol className="flex flex-col gap-1 text-[15px] leading-6">
          {page.summary.points.map((p, i) => <li key={p}><span className="text-primary">{i + 1}.</span> {p}</li>)}
        </ol>}
      </section>

      <SectionGrid className="gap-x-12 gap-y-10">
        {secs.map((s, si) => (
          <section key={si} className={`flex flex-col gap-4 ${spanCls(s)}`}>
            {s.title && (
              <h2 className="flex items-baseline gap-3 border-b border-foreground/80 pb-1 font-heading text-2xl font-bold">
                <span className="text-primary">{s.n}</span>{s.title}
              </h2>)}
            {s.items.map(it => <div key={it.i}>{block(it)}</div>)}
          </section>
        ))}
        {page.conclusion && <section className="flex flex-col gap-4 min-[1440px]:col-span-2">
          <h2 className="flex items-baseline gap-3 border-b border-foreground/80 pb-1 font-heading text-2xl font-bold"><span className="text-primary">{secs.length + 1}</span>结论</h2>
          <p className={`indent-8 ${measure}`}>{page.conclusion}</p>
        </section>}
      </SectionGrid>

      <footer className="grid grid-cols-1 gap-8 border-t-2 border-foreground pt-4 text-sm leading-6 md:grid-cols-[minmax(0,1fr)_28em]">
        <section className="flex flex-col gap-1">
          <h2 className="font-heading text-base font-bold">参考文献</h2>
          <ol className="flex flex-col gap-1">
            {page.references.map((r, i) => (
              <li key={i} className="grid grid-cols-[2em_1fr]"><span>{i + 1}.</span><span>{r.text}. <span className="font-mono text-xs text-muted-foreground">{r.source}</span></span></li>
            ))}
          </ol>
        </section>
        <section className="flex flex-col gap-1">
          <h2 className="font-heading text-base font-bold">引用本文</h2>
          <p className="text-muted-foreground">{cite}</p>
        </section>
      </footer>
    </article>
  )
}
