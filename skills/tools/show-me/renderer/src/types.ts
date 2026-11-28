export type Style = "paper" | "sketch" | "terminal"
export const STYLES: { value: Style; label: string }[] = [
  { value: "paper", label: "科研风" },
  { value: "sketch", label: "手绘风" },
  { value: "terminal", label: "程序员风" },
]
export type FlowNode = { id: string; label: string; detail: string }
// 有向图：支持分叉与合并，自动分层；direction 缺省 LR（左→右），TB 为上→下
export type GraphBlock = {
  type: "graph"; point?: string; caption: string; direction?: "LR" | "TB"
  nodes: { id: string; label: string; detail?: string }[]
  edges: { from: string; to: string; label?: string }[]
}
// data 每行：stage 为分类名，其余键与 series[].key 对应；total 给出时科研风附合计公式 T_total = Σ
export type ChartBlock = {
  type: "chart"; point?: string; caption: string; unit: string; note?: string; total?: string
  series: { key: string; label: string }[]
  data: Record<string, string | number>[]
}
// 表格与键值配置表同形；kv 默认第 0 列等宽显示，mono 指定等宽列
export type TableBlock = { type: "table" | "kv"; point?: string; caption: string; columns: string[]; rows: string[][]; mono?: number[] }
export type CodePane = { title: string; lang: string; code: string }
export type Block =
  // level 1 为分部标题（横跨整行、不带正文）；num 覆盖自动节号，如 "3.1"；wide 强制横跨两列
  | { type: "heading"; text: string; num?: string; level?: 1 | 2; wide?: boolean }
  | { type: "paragraph"; text: string }
  | { type: "list"; ordered?: boolean; items: { title?: string; text: string }[] }
  | { type: "flow"; point?: string; caption: string; nodes: FlowNode[] }
  | GraphBlock
  | TableBlock
  | ChartBlock
  | { type: "code"; point?: string; caption: string; lang: string; filename: string; code: string }
  // 多栏并排代码块
  | { type: "codes"; point?: string; caption: string; panes: CodePane[] }
  | { type: "steps"; point?: string; items: { title: string; detail: string }[] }
  // 叠放图：layers[0] 为最上层（优先级最高）
  | { type: "stack"; point?: string; caption: string; note?: string; layers: { label: string; detail: string }[] }
  // 整页线框示意：regions 依次对应 页头、结论区、指标卡、正文面板网格、需要你做的事、出处、页脚、显性水印
  | { type: "wireframe"; point?: string; caption: string; regions: { label: string; detail: string }[] }
  // 图片：src 由 CLI 内联为 data: URI；位图在渲染时写入最低位水印
  | { type: "image"; point?: string; caption: string; src: string; alt?: string }
export type Kpi = { label: string; value: string; unit?: string; note: string; spark?: number[] }
export type Page = {
  title: string; subtitle: string
  meta: {
    author: string; date: string
    byline?: { name: string; url: string }   // 署名链接，缺省 lazygophers/ccplugin
    logo?: string                            // 已内联的 data: URI
    generated?: string; version?: number; kind?: string; status?: string
  }
  summary: { point: string; text: string; points: string[] }
  kpis?: Kpi[]                               // 缺省时由内容推导；[] 表示不显示
  watermark?: string | null                  // 缺省「署名 · 日期」；null 关闭
  blocks: Block[]; conclusion?: string
  changes?: string[]                         // 与上一版的变更，v≥2 时显示在正文前
  references: { text: string; source: string }[]
  topic?: string; type?: string; style?: Style
  showme?: ShowMe                            // 由 CLI 写入，内容 JSON 不提供
}
export type ShowMe = {
  version: string                            // SKILL.md 的 version，页脚左段
  style: Style; switcher: boolean
  prev?: string                              // 上一版文件名
  watermarkOpacity: number
  payload?: string                           // 隐水印载荷 JSON；缺省表示四种隐水印均不在渲染期写入
  pattern: boolean; images: boolean
}
