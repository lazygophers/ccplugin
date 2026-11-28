import type { Block, Kpi, Page } from "@/types"
import { cn } from "@/lib/utils"

// 图、表、清单各自编号；三种风格共用同一套编号
export function numbering(blocks: Block[]) {
  const c = { fig: 0, tab: 0, lst: 0, sec: 0 }
  return blocks.map(b =>
    b.type === "flow" || b.type === "graph" || b.type === "chart" || b.type === "stack" || b.type === "wireframe" || b.type === "image" ? ++c.fig
    : b.type === "table" || b.type === "kv" ? ++c.tab
    : b.type === "code" || b.type === "codes" ? ++c.lst
    : b.type === "heading" ? ++c.sec : 0)
}

export type Item = { b: Block; i: number; n: number }
export type Section = { title?: string; n: number | string; items: Item[]; wide: boolean; part?: boolean }
const WIDE = new Set<Block["type"]>(["flow", "graph", "codes", "wireframe"])

// 按 heading 切节；含流程图的节横跨整行（宽图），其余节在宽屏两两并排
export function sections(blocks: Block[]): Section[] {
  const nums = numbering(blocks)
  const out: Section[] = []
  blocks.forEach((b, i) => {
    if (b.type === "heading") out.push({ title: b.text, n: b.num ?? nums[i], items: [], wide: !!b.wide || b.level === 1, part: b.level === 1 })
    else {
      if (!out.length) out.push({ n: 0, items: [], wide: false })
      out[out.length - 1].items.push({ b, i, n: nums[i] })
    }
  })
  for (const s of out) s.wide ||= s.items.some(x => WIDE.has(x.b.type))
  // 落单的普通节（下一节横跨或已到末尾）也横跨整行，避免两列网格留空洞
  let run = 0
  out.forEach((s, i) => {
    if (!s.wide) { run++; return }
    if (run % 2) out[i - 1].wide = true
    run = 0
  })
  if (run % 2) out[out.length - 1].wide = true
  return out
}

// 窗口 ≥1440px 两列，窄于 1440px 单列；只限制面板网格的列数，不限制宽度
export function SectionGrid({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn("grid grid-cols-1 gap-8 min-[1440px]:grid-cols-2", className)}>{children}</div>
}
export const spanCls = (s: Section) => (s.wide ? "min-[1440px]:col-span-2" : "")

// 正文段落行长约 80 个汉字
export const measure = "max-w-[80em]"

// 指标卡只取内容显式给出的 kpis；缺省或 [] 不显示
export const kpis = (page: Page): Kpi[] => page.kpis ?? []
