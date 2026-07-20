# 重设计 skein serve 为多页面管理平台 — PRD (主入口)

## 目标
把 `skein serve` 的单页看板扩展为**多页面完整管理平台**, 一处集中管理 SKEIN task 全生命周期:
- 用户价值: 不再只能看看板, 而能在浏览器里浏览队列 / 审阅 PRD / 查改 spec / 触发轻量命令
- 成功长相: 顶部导航切 5 个页面, 前端 SPA 路由无整页刷新, 复用现有主题系统, 视觉风格与现状一致

## 边界
**范围内:**
- 5 个页面: ① 看板 (现有, 保留为首页) ② 待执行队列 ③ Task/PRD 审阅 ④ Spec 查看编辑 ⑤ 命令面板
- FastAPI 加多个数据 endpoint + 前端 vanilla JS SPA 路由 (hash 路由) + 顶部导航
- spec 编辑: 页面可改, **保存前 diff 确认弹层**, 写盘走后端 API
- 命令执行: **只读命令** (list/ready/status/doctor/board/view/contract 查/subtask list) + **安全写** (create / subtask add)
- 复用现有资产体系 (base.css + 10 主题 + 令牌系统) 与热重载 (WS)

**范围外 (非目标):**
- 不含 start/finish/archive 等碰 git / 改 worktree 的破坏性命令按钮
- 不改 spec 两层记忆语义, 不改 task/subtask schema
- 不做用户鉴权 (仍仅绑 127.0.0.1 本地)
- 不做前端框架 (React/Vue), vanilla JS 足够

**已知约束:**
- 第三方包可引入, 启动时自动装 (`_install_serve_deps` 模式), 包内容不入 git (requirements.txt 追踪)
- spec 写盘是敏感操作 (记忆硬规), 必须 diff 确认 + 后端白名单校验路径
- 命令执行 endpoint 是全新面, 必须白名单命令 + 参数校验, 严防注入

## 验收标准
- [ ] 顶部导航 5 页可切换, 前端 hash 路由无整页刷新, 直接访问 `#/queue` 等能正确落地
- [ ] 看板页 (首页) 功能与现状一致 (卡片/DAG/主题/搜索/文档弹层不回归)
- [ ] 待执行队列页展示 ready task 批 + 各 task 内就绪 subtask 调度序 (数据来自 ready/pop 语义)
- [ ] Task/PRD 审阅页: 选 task 后渲染 prd.md/design.md/findings.md + subtask 列表 (md 渲染复用 doc.js)
- [ ] Spec 页: 树浏览 core/recall×类目, 点条目看内容, 编辑后保存弹 diff 确认, 确认才落盘
- [ ] 命令面板: 只读命令可跑并显示输出; create task / subtask add 表单可提交且校验必填
- [ ] 命令执行后端白名单严格 (非白名单命令拒绝), spec 保存路径校验 (越界拒绝)
- [ ] 全部主题在新页面下不破版; <900px 单列回落
- [ ] view (file://) 模式不因新增 endpoint 报错 (静态模式优雅降级或提示需 serve)

## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md) (现有实现勘察已并入 design)
- 任务/子任务/调度: task.json (`skein.py subtask list serve-platform-redesign`)
