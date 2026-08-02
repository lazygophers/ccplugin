# 看板实时性 + serve 崩溃修复 — PRD (主入口)

## 目标
- [ ] task 详情页在 task 变更时实时更新数据, 无需手动刷新
- [ ] 访问 `/` 自动跳转到 `/board`, 不再显示脚手架占位页
- [ ] serve 不再莫名退出, 有错误信息时能看到日志
- [ ] 跨 task 调度在看板上可见 (哪些 task 在等、等什么)
- [ ] 子任务 DAG 图支持悬浮高亮上下游关联 subtask

## 边界
- [ ] 范围内: 前端 nextjs 源码 (`assets/nextjs/src/`) + 后端 serve.py/boardsource.py + dist 重建
- [ ] 范围内: `/` → `/board` 重定向
- [ ] 范围内: serve 进程生命周期管理 + 日志
- [ ] 范围外: 改 WS 协议本身 (已有 task-changed 消息, 只是详情页没订阅)
- [ ] 范围外: 后端调度逻辑改动 (只改前端展示)
- [ ] 约束: dist 需整体重建 (Next.js 随机 buildId)

## User Stories
1. As a 看板用户, I want task 详情页自动刷新数据, so that 我不需要手动 F5
2. As a 新用户, I want 访问 `/` 直接看到看板, so that 我不会看到空的脚手架页困惑
3. As a 用户, I want serve 不莫名退出, so that 看板不会突然变空白
4. As a 用户, I want 看到 serve 退出时的错误日志, so that 我知道发生了什么
5. As a 看板用户, I want 看到哪些 task 在等待调度, so that 我了解整体进度
6. As a 看板用户, I want 子任务 DAG 悬浮高亮上下游, so that 我快速理解依赖关系
7. (边界) As a 用户, I want serve 崩溃后自动重启 (或至少有明确报错), so that 我不需要手动重启

## 验收标准
- [ ] task 详情页收到 WS `task-changed` 消息后自动更新对应数据 (不整页刷新)
- [ ] 访问 `/` 返回 302/301 跳转到 `/board` (或客户端 redirect)
- [ ] `/` 页面不再显示「SKEIN Dashboard 脚手架已就绪」
- [ ] serve 进程退出时在 stderr 或日志文件留下退出原因
- [ ] serve 在非主动关闭时自动重启 (或至少在 board UI 显示断连状态)
- [ ] 子任务 DAG 图悬浮某节点时, 该节点的所有上游和下游节点高亮
- [ ] dist 重建, 引用完整性 0 missing
- [ ] 全量 pytest 不低于基线 425

## Testing Decisions
- [ ] 详情页实时更新: 验证 WS task-changed 消息被详情页订阅 (grep `taskId` 在详情页组件)
- [ ] `/` 重定向: 验证 page.tsx 用 redirect() 而非静态内容
- [ ] serve 崩溃: 模拟 SIGTERM/SIGKILL 或异常退出, 验证日志或重启
- [ ] DAG 高亮: 验证 depdag.ts 有 hover 状态 + 高亮逻辑

## 索引
- 详细设计: [design.md](design.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list board-realtime-fix`)
