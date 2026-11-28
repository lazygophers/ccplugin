import { createRoot } from "react-dom/client"
import App from "@/App"
import type { Page } from "@/types"
import "./index.css"

// 内容数据由 CLI 注入到 #page-data，渲染器本身不随内容重新构建
const raw = document.getElementById("page-data")?.textContent?.trim()
const root = createRoot(document.getElementById("root")!)
if (!raw) root.render(<p style={{ padding: 24 }}>缺少页面数据：#page-data 为空。</p>)
else {
  const page = JSON.parse(raw) as Page
  // 首帧前定风格（hash 优先，其次 CLI 决定的风格），避免先按默认风格绘制再切换引发颜色过渡
  document.documentElement.dataset.style = /style=(paper|sketch|terminal)/.exec(location.hash)?.[1] ?? page.showme?.style ?? "paper"
  if (page.title) document.title = page.title
  root.render(<App page={page} />)
}
