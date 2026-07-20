# 重设计 skein serve 为工程化多页面管理平台 — PRD (主入口)

## 目标
把 `skein serve` 单页看板重构为**工程化多页面完整管理平台**, 浏览器里集中管理 SKEIN task 全生命周期:
- 用户价值: 概览统计 / 队列 / PRD 审阅 / spec 查改 / 命令执行 / 归档回溯, 一处搞定
- 成功长相: 7 页顶栏导航 + 全局搜索, 前端 SPA(petite-vue)无整页刷新, buildless 工程化, 视觉与现状一致

## 边界
**范围内 — 7 页:**
1. `#/dashboard` 统计概览 (真首页): 完成率 / 活跃数 / subtask 进度 / 状态分布
2. `#/board` 看板 (现有渲染迁移到工程化)
3. `#/queue` 待执行队列 (ready/pop 语义)
4. `#/task/:id` Task/PRD 审阅 (prd/design/findings md + subtask 列表 + 契约)
5. `#/spec` Spec 查看编辑 (core/recall×类目树 + 编辑 diff 确认弹层)
6. `#/commands` 命令面板 (只读命令 + create/subtask add 安全写)
7. `#/archive` 已归档 task 浏览
- 全局搜索: 顶栏跨 task/subtask/spec/prd

**工程化 (buildless):**
- 新建 `plugins/tools/skein/assets/webapp/` 独立工程化目录 (与旧 board/ 并存)
- Tailwind standalone 单二进制 (启动拉, 不入 git) 编 css; petite-vue vendored; ES modules 分层 (router/app/lib/pages)
- 现有 oklch 令牌 + 状态色 + 10 主题 **映射进 Tailwind config**, 风格一致
- 第三方产物 (tailwind 二进制 / petite-vue / 编译 css) 启动时自动下载/构建/更新, gitignore

**后端:** FastAPI 加数据 endpoint (queue/task/spec/exec/archive/dashboard/search), serve/view 指向 webapp/

**范围外:**
- 不含 start/finish/archive/clean 等碰 git / worktree 的破坏性命令按钮
- 不改 spec 记忆语义 / task-subtask schema / 单实例锁 / WS 热重载机制
- 不做用户鉴权 (仍绑 127.0.0.1); 不引 node/npm (buildless)

**约束:**
- spec 写盘敏感: realpath 校验限 `.skein/spec/` 内 + 保存前 diff 确认
- exec endpoint 全新面: 白名单 enum + 固定 argv (不 shell 拼串) 防注入; 写命令仅 create/subtask add
- 旧 board/ 资产保留, 不回归 (view file:// 仍可用)

## 验收标准
- [ ] 7 页顶栏导航可切, hash 路由无整页刷新, 直接访问 `#/queue` 等能落地
- [ ] dashboard 展示完成率/活跃数/subtask进度/状态分布, 作默认首页
- [ ] board 页看板功能与现状一致 (卡片/DAG/主题/文档弹层不回归)
- [ ] queue 展示 ready task 批 + 各 task 就绪 subtask 调度序
- [ ] task 页渲染 prd/design/findings + subtask 列表 + 契约
- [ ] spec 页树浏览 core/recall×类目, 编辑保存弹 diff 确认才落盘, 取消不写
- [ ] commands 只读命令可跑显输出; create/subtask add 表单校验必填提交
- [ ] archive 页浏览已归档 task
- [ ] 全局搜索跨 task/subtask/spec/prd 出结果
- [ ] exec 白名单外命令被拒; spec-save 越界路径被拒
- [ ] Tailwind config 映射后 10 主题在新页不破版; <900px 单列回落
- [ ] 启动时 tailwind 二进制/petite-vue 缺失自动拉取, css 自动构建; 二次启动复用不重拉
- [ ] webapp 产物 (二进制/vendored/编译css) 已 gitignore, 不入库

## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md) (现有实现勘察 + 工程化选型并入 design)
- 任务/子任务/调度: task.json (`skein.py subtask list serve-webapp`)
