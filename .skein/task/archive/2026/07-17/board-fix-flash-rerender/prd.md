# /board 软刷闪屏修复 — PRD

## 目标
/board 页每次 WS "data" 事件触发 refresh → `layout.innerHTML = buildLayoutHtml(data)` 全量替换, 赋值瞬间整个 .layout 清空再重建, 可见空白闪屏。消除闪屏: 数据不变跳过 + 原子替换消清空帧。

## 根因 (file:line)
- board.js L595 `ctx.onLive(cb)` 注册 refresh 为数据软刷回调
- board.js L589-592 `refresh()` 无条件 `await ctx.api.data()` + `renderLayout`
- board.js L427 `renderLayout` = `layout.innerHTML = buildLayoutHtml(data)` — 赋值 HTML 字符串时浏览器先清空旧子树再解析新串, 中间帧 .layout 区域空白 (尤其 43 task 全量 DAG/卡片重建)
- live.js L21 WS "data" 广播粒度粗 (任意 task 变都广播, board 数据可能没真变 → 无效全量刷加剧闪屏)

## 边界
- 范围内: board.js renderLayout 原子替换 + refresh 数据不变跳过
- 范围外: live.js WS 协议改 (后端加版本号属另 scope); 其他页 (queue/task/spec 用 petite-vue 响应式无此问题); buildLayoutHtml 本身逻辑; DAG 像素渲染
- 约束: 保滚动位复原 (现有 savedScroll/savedWin 逻辑不丢); 保 bindContent 事件重绑

## 改动
### renderLayout 原子替换 (board.js L420-440)
- 现状: `layout.innerHTML = buildLayoutHtml(data)` (清空+解析, 中间空白帧)
- 改: 用临时容器 parse HTML → DocumentFragment → `layout.replaceChildren(frag)` 一次性原子替换 (无中间空态)
- 保 savedScroll/savedWin 记录/复原逻辑 (移到 replaceChildren 前后)

### refresh 数据不变跳过 (board.js L589-592)
- 现状: 每次 onLive 触发都 fetch + 全量替换
- 改: refresh 内缓存上次 data 序列化串 (JSON.stringify), 新 data 串相同 → 跳过 renderLayout (不替换 DOM)
- 首次无缓存 → 正常渲染

## subtask
| sid | 名称 | agent | 改动 |
|---|---|---|---|
| atomic-render-skip-unchanged | renderLayout 原子替换 + refresh 数据不变跳过 | skein-executor | board.js |

## 验收标准
- [ ] WS data 事件触发但数据未变 → 不替换 DOM (无闪屏)
- [ ] 数据真变 → replaceChildren 原子替换, 无中间空白帧
- [ ] 滚动位复原正常 (左栏 DAG 滚动 + 窗口滚动)
- [ ] bindContent 事件正常 (状态筛选 / DAG 维度切换)
- [ ] board.js node -c 过
- [ ] chrome 实测: 触发 WS data (task 变更), 观察无空白闪屏

## 索引
- 任务/子任务/调度: task.json
