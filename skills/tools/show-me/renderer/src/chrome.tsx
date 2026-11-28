import { Fragment, useEffect, useState } from "react"
import { patternUrl, watermarkImage } from "@/watermark"
import { cn } from "@/lib/utils"
import type { Page, Style } from "@/types"

/* 三种风格共用的页面外壳：页头元信息行、固定页脚、显性水印 */

// 页脚左段锁定：名称与仓库地址写死，版本取 CLI 注入的 SKILL.md version；配置无对应键，无法移除
const SKILL = { name: "show-me", repo: "github.com/lazygophers/ccplugin", url: "https://github.com/lazygophers/ccplugin" }
const DEFAULT_BYLINE = { name: "lazygophers/ccplugin", url: SKILL.url }
export const byline = (page: Page) => page.meta.byline ?? DEFAULT_BYLINE

const link = "underline decoration-current/40 underline-offset-2 hover:decoration-current"

export function MetaLine({ page, className }: { page: Page; className?: string }) {
  const m = page.meta, by = byline(page)
  const items = [
    <a href={by.url} className={link}>{by.name}</a>,
    m.generated && <span>生成于 <time>{m.generated}</time></span>,
    m.version && <span>文档 v{m.version}</span>,
    page.showme?.prev && <a href={page.showme.prev} className={link}>上一版 {page.showme.prev}</a>,
    m.kind && <span>产物类型 {m.kind}</span>,
    m.status && <span className="rounded-sm border border-current/40 px-1.5 leading-5">{m.status}</span>,
  ].filter(Boolean)
  return (
    <p className={cn("flex flex-wrap items-center gap-x-2 gap-y-1", className)}>
      {m.logo && <WmImg page={page} src={m.logo} className="mr-1 h-6 w-auto" />}
      {items.map((x, i) => <Fragment key={i}>{i > 0 && <span aria-hidden className="opacity-50">·</span>}{x}</Fragment>)}
    </p>
  )
}

export function PageFooter({ page }: { page: Page }) {
  const m = page.meta, by = byline(page)
  return (
    <footer className="grid grid-cols-1 gap-1 border-t border-current/20 px-8 py-4 text-xs text-muted-foreground sm:grid-cols-3">
      <span>{SKILL.name} v{page.showme?.version ?? "0.0.0"} · <a href={SKILL.url} className={link}>{SKILL.repo}</a></span>
      <span className="sm:text-center">文档 v{m.version ?? 1} · 生成于 {m.generated ?? m.date}</span>
      <span className="sm:text-right"><a href={by.url} className={link}>{by.name}</a></span>
    </footer>
  )
}

// 隐水印背景编码图案：约 1% 不透明度平铺，不拦截点击
export function PatternMark({ page, style }: { page: Page; style: Style }) {
  const s = page.showme
  if (!s?.payload || !s.pattern) return null
  return <div aria-hidden data-pattern className="pointer-events-none fixed inset-0 z-40 select-none" style={{ backgroundImage: patternUrl(s.payload, style === "terminal"), backgroundRepeat: "repeat", printColorAdjust: "exact", WebkitPrintColorAdjust: "exact" }} />
}

// 位图渲染期写入最低位水印后替换 src；SVG 的 <metadata> 由 CLI 写入
export function WmImg({ page, src, alt, className }: { page: Page; src: string; alt?: string; className?: string }) {
  const [s, setS] = useState(src)
  const p = page.showme
  useEffect(() => {
    if (p?.payload && p.images) watermarkImage(src, p.payload).then(setS)
    else setS(src)
  }, [src, p?.payload, p?.images])
  return <img src={s} alt={alt ?? ""} className={className} data-wm={s !== src ? "lsb" : undefined} />
}

// 全页 -30° 平铺文字，透明度 0.06；不拦截点击与选中；打印保留（print-color-adjust: exact）
export function Watermark({ page, style }: { page: Page; style: Style }) {
  if (page.watermark === null) return null
  const text = page.watermark ?? `${byline(page).name} · ${page.meta.date}`
  const color = style === "terminal" ? "#ffffff" : "#000000"
  const opacity = page.showme?.watermarkOpacity ?? 0.06
  const esc = text.replace(/&/g, "&amp;").replace(/</g, "&lt;")
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="420" height="240"><text x="210" y="120" text-anchor="middle" dominant-baseline="middle" transform="rotate(-30 210 120)" font-family="sans-serif" font-size="18" fill="${color}" fill-opacity="${opacity}">${esc}</text></svg>`
  return (
    <div aria-hidden data-watermark className="pointer-events-none fixed inset-0 z-50 select-none"
      style={{ backgroundImage: `url("data:image/svg+xml,${encodeURIComponent(svg)}")`, backgroundRepeat: "repeat", printColorAdjust: "exact", WebkitPrintColorAdjust: "exact" }} />
  )
}
