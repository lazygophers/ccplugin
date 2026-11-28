import { useEffect, useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { Code, CodePanes, DataChart, Flow, Graph, StackFig, Wireframe, cellMono, circled } from "@/figures"
import { MetaLine, PageFooter, PatternMark, Watermark, WmImg } from "@/chrome"
import { PaperPage } from "@/paper"
import { SketchPage } from "@/sketchy"
import { measure, sections, SectionGrid, spanCls, type Item } from "@/layout"
import { STYLES, type ChartBlock, type Page, type Style } from "@/types"

function readStyle(fallback: Style): Style {
  const m = /style=(paper|sketch|terminal)/.exec(location.hash)
  return (m?.[1] as Style) ?? fallback
}

// v≥2 且内容提供 changes 时，在正文前插入「与上一版的变更」节
function withChanges(page: Page): Page {
  if (!page.changes?.length) return page
  return { ...page, blocks: [{ type: "heading", text: "与上一版的变更", num: "Δ" }, { type: "list", items: page.changes.map(text => ({ text })) }, ...page.blocks] }
}

function DataTable({ columns, rows, caption, mono }: { columns: string[]; rows: (string | number)[][]; caption?: string; mono?: Set<number> }) {
  return (
    <Table>
      {caption && <TableCaption>{caption}</TableCaption>}
      <TableHeader>
        <TableRow>{columns.map(c => <TableHead key={c}>{c}</TableHead>)}</TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((r, i) => (
          <TableRow key={i}>{r.map((v, j) => <TableCell key={j} className={mono ? "whitespace-normal align-top" : undefined}>{mono?.has(j) ? <code className="text-primary">{v}</code> : v}</TableCell>)}</TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

function chartRows(b: ChartBlock) {
  return b.data.map(d => [String(d.stage), ...b.series.map(s => `${d[s.key]} ${b.unit}`)])
}

function ChartTabs({ block, chartLabel }: { block: ChartBlock; chartLabel: string }) {
  return (
    <Tabs defaultValue="chart" className="w-full">
      <TabsList>
        <TabsTrigger value="chart">{chartLabel}</TabsTrigger>
        <TabsTrigger value="data">数据</TabsTrigger>
      </TabsList>
      <TabsContent value="chart"><DataChart block={block} /></TabsContent>
      <TabsContent value="data">
        <DataTable columns={["阶段", ...block.series.map(s => s.label)]} rows={chartRows(block)} />
      </TabsContent>
    </Tabs>
  )
}

/* ---------- 程序员风：技术文档 + 终端 / 编辑器配色 ---------- */
function Window({ title, badge, children }: { title: string; badge?: string; children: React.ReactNode }) {
  return (
    <Card className="gap-0 py-0">
      <CardHeader className="flex items-center gap-2 border-b py-2">
        <span className="size-3 rounded-full bg-destructive" />
        <span className="size-3 rounded-full bg-muted-foreground" />
        <span className="size-3 rounded-full bg-primary" />
        <CardTitle className="ml-2 text-xs text-muted-foreground">{title}</CardTitle>
        {badge && <Badge variant="outline" className="ml-auto">{badge}</Badge>}
      </CardHeader>
      <CardContent className="p-0">{children}</CardContent>
    </Card>
  )
}

function DevPage({ page }: { page: Page }) {
  const secs = sections(page.blocks)
  const block = ({ b, n }: Item) => {
    switch (b.type) {
      case "heading": return null
      case "paragraph": return <p className={`text-muted-foreground ${measure}`}>{b.text}</p>
      case "flow": return (
        <Window title={`fig.${n} — ${b.caption}`} badge="architecture">
          <div className="p-4"><Flow nodes={b.nodes} style="terminal" cols={b.nodes.length} /></div>
        </Window>)
      case "graph": return (
        <Window title={`fig.${n} — ${b.caption}`} badge="graph">
          <div className="flex justify-center p-4"><Graph block={b} style="terminal" /></div>
        </Window>)
      case "list": return (
        <ul className={`flex flex-col gap-1 ${measure}`}>
          {b.items.map((x, j) => <li key={j} className="flex gap-3"><span className="text-primary">{b.ordered ? String(j + 1).padStart(2, "0") : "-"}</span><span>{x.title && <span className="font-bold">{x.title}: </span>}<span className="text-muted-foreground">{x.text}</span></span></li>)}
        </ul>)
      case "kv":
      case "table": return (
        <Window title={`table.${n} — ${b.caption}`} badge={b.type === "kv" ? "config" : "compare"}>
          <DataTable columns={b.columns} rows={b.rows} mono={b.type === "kv" || b.mono ? cellMono(b) : undefined} />
        </Window>)
      case "stack": return (
        <Window title={`fig.${n} — ${b.caption}`} badge="layers">
          <div className="p-4"><StackFig layers={b.layers} note={b.note} /></div>
        </Window>)
      case "wireframe": return (
        <Window title={`fig.${n} — ${b.caption}`} badge="layout">
          <div className="grid grid-cols-1 items-center gap-6 p-4 md:grid-cols-[minmax(0,26rem)_minmax(0,1fr)]">
            <Wireframe regions={b.regions} />
            <ol className="flex flex-col gap-1">{b.regions.map((r, j) => <li key={j}><span className="text-primary">{circled(j)} </span><span className="font-bold">{r.label}</span> <span className="text-muted-foreground">{r.detail}</span></li>)}</ol>
          </div>
        </Window>)
      case "codes": return (
        <CodePanes panes={b.panes} wrap={(t, l, body) => <Window title={t} badge={l}><div className="[&_pre]:whitespace-pre-wrap [&_pre]:break-all">{body}</div></Window>} />)
      case "chart": return (
        <Window title={`fig.${n} — ${b.caption} (${b.unit})`} badge="sample data">
          <div className="flex flex-col gap-2 p-4">
            <ChartTabs block={b} chartLabel="chart" />
            {b.note && <p className="text-xs text-muted-foreground">// {b.note}</p>}
          </div>
        </Window>)
      case "image": return (
        <Window title={`fig.${n} — ${b.caption}`} badge="image">
          <div className="flex justify-center p-4"><WmImg page={page} src={b.src} alt={b.alt ?? b.caption} className="max-h-[36rem] max-w-full" /></div>
        </Window>)
      case "code": return (
        <Window title={b.filename} badge={b.lang}>
          <Code code={b.code} lang={b.lang} />
        </Window>)
      case "steps": return (
        <ol className="flex flex-col gap-1">
          {b.items.map((s, j) => (
            <li key={s.title} className="flex gap-3">
              <span className="text-primary">{String(j + 1).padStart(2, "0")}</span>
              <span className="font-bold">{s.title}</span>
              <span className="text-muted-foreground">{s.detail}</span>
            </li>
          ))}
        </ol>)
    }
  }
  return (
    <article className="flex flex-col gap-6 px-8 py-10 text-sm leading-7">
      <header className="flex flex-col gap-1">
        <p className="text-muted-foreground">~/docs/{page.topic ?? "show-me"} <span className="text-primary">v{page.meta.version ?? 1}</span> $ cat {page.topic ?? "index"}.md</p>
        <h1 className="font-heading text-2xl font-bold"><span className="text-primary"># </span>{page.title}</h1>
        <p className="text-muted-foreground">{page.subtitle} · {page.meta.date}</p>
        <MetaLine page={page} className="text-xs text-muted-foreground" />
      </header>
      <Window title="TL;DR" badge="summary">
        <div className="flex flex-col gap-2 p-4">
          <p className={measure}><span className="text-primary">&gt; </span>{page.summary.text}</p>
          <ul className="flex flex-col">
            {page.summary.points.map(p => <li key={p}><span className="text-primary">✓ </span>{p}</li>)}
          </ul>
        </div>
      </Window>
      <SectionGrid>
        {secs.map((s, si) => (
          <section key={si} className={`flex flex-col gap-4 ${spanCls(s)}`}>
            {s.title && <h2 className="mt-4 font-heading text-lg font-bold"><span className="text-primary">## </span>{s.title}</h2>}
            {s.items.map(it => <div key={it.i}>{block(it)}</div>)}
          </section>
        ))}
      </SectionGrid>
      {page.conclusion && <>
        <h2 className="mt-4 font-heading text-lg font-bold"><span className="text-primary">## </span>结论</h2>
        <p className={measure}>{page.conclusion}</p>
      </>}
      <Separator />
      <section className="flex flex-col text-xs text-muted-foreground">
        {page.references.map((r, i) => <p key={i}>[{i + 1}] {r.text} — {r.source}</p>)}
      </section>
    </article>
  )
}

export default function App({ page: raw }: { page: Page }) {
  const page = withChanges(raw)
  const fallback = page.showme?.style ?? "paper"
  const [style, setStyle] = useState<Style>(() => readStyle(fallback))
  useEffect(() => {
    document.documentElement.dataset.style = style
    history.replaceState(null, "", `#style=${style}`)
  }, [style])
  useEffect(() => {
    const onHash = () => setStyle(readStyle(fallback))
    addEventListener("hashchange", onHash)
    return () => removeEventListener("hashchange", onHash)
  }, [fallback])
  return (
    <div className="min-h-svh bg-background font-sans text-foreground">
      {page.showme?.switcher !== false && <nav className="sticky top-0 z-10 flex justify-center border-b bg-background/90 py-2 backdrop-blur">
        <ToggleGroup variant="outline" size="sm" value={[style]} onValueChange={v => v[0] && setStyle(v[0] as Style)} aria-label="页面风格">
          {STYLES.map(s => <ToggleGroupItem key={s.value} value={s.value}>{s.label}</ToggleGroupItem>)}
        </ToggleGroup>
      </nav>}
      {style === "paper" && <PaperPage page={page} />}
      {style === "sketch" && <SketchPage page={page} />}
      {style === "terminal" && <DevPage page={page} />}
      <PageFooter page={page} />
      <PatternMark page={page} style={style} />
      <Watermark page={page} style={style} />
    </div>
  )
}
