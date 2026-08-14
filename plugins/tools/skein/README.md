# SKEIN

**独立任务管理插件** — 零 trellis / trellisx 依赖, 自带 `.skein/` 工作区。名取「线团」(skein of yarn): 任务如纱线, 编织、调度、收束。

## 能做什么

| 能力 | 载体 | 说明 |
| --- | --- | --- |
| 初始化 / trellis 迁移 | `setup` skill + `skein setup` | 幂等 scaffold; 检测 `.trellis/` → 软链 spec + 派 `skein-setup` agent 语义迁移 (spec 重组 / task 重建 / 清残留); SessionStart 无 `.skein/` 自动 nudge |
| 强制 task 闭环 | `skein-flow` | 请求强制走 plan→exec→check→finish, 不 inline |
| 动态 DAG 编排调度 (双层) | `skein-flow exec 阶段` (`references/dag.md`) | main 作调度器, task 级 + subtask 级同构, 并行只看 `depends_on` DAG, 并发上限 2, 完成即派 (flow exec 委托) |
| worktree 隔离 | `skein` | 1 task 1 worktree, 主工作区零改动 |
| 看板 (文本 + 可视化) | `skein board` / `skein serve --open` | `.skein/task.md` 文本看板 + `.skein/task.html` 静态可视化页 (title/标题带项目名; 预估进度总览 + 预计执行顺序图 + 每 task 时间条, 4 主题 6 配色 深浅色, 页内切换器, `serve --open` 按需打开) |
| planning 入口 | `skein-flow plan 阶段` | 判新旧 + 登记 + brainstorm + grill 硬门 (必走) |
| **namespace×inclusion 规则记忆** | `skein-spec` | **差异化核心** (见下) |
| 对抗式审查 | `skein-grill` | 需求/工件对抗校对 (planning 硬门) |
| 破坏式重构 | `skein-flow plan 阶段` (heavy 档) | 不保兼容、全站点一次改齐的重构模式, 须任务显式授权 |
| 质量门 + 一致性核查 | `skein-flow check 阶段` | 派 `skein-checker` 验证 (lint/type/test/契约 + subtask 产物一致性核查), 未过派 `skein-executor` 修复重检; **孤立失败定点修, 跨 subtask 冲突/check 失败 → 深化拆分 (回 plan 拆新 subtask 逐条覆盖直到零冲突)** |
| 第 3 轮根因复盘 | `skein-flow check 阶段` (`references/flow-loop.md` §9.3) | check 第 3 轮仍 FAIL 时跨维度结构化根因复盘 (需求/设计/实现/环境/测试 5 维 + 预防措施), 出口回 exec 定向重修或停手转人工 |
| finish 收尾编排门 | `skein-flow finish 阶段` | check 全绿后被 flow 委托: 派 `skein-finisher` 收尾勘察 + 委托 `skein-spec` sediment + 清理悬挂 + `skein task finish` (commit→merge→销 worktree→标记完成, 异步 spec) |
| 冷启动播种 | `skein-spec` (`references/bootstrap-seeding.md`) | 空仓首次接入时扫既有代码库约定 (命名/错误处理/测试/架构边界/构建) 播种规则基线 (一次性, 默认多归 recall) |
| 主动清理 | `skein-clean` | [仅用户主动] 归档完成 task (保留期外) + 清孤儿 worktree / 悬挂分支 |

**exec 一律派 `skein-executor`** — main 对每个 subtask 派 `skein-executor`, dispatch 只给 tid + sid + 工作目录, 不再逐个挑选执行器 (改哪些文件自主决定, 完成前对照验收标准逐条自检, 每文件过写前硬门); 执行纪律 (递归护栏 + 读后写硬门 + 验收标准自检 + 输出格式) 经 dispatch prompt 硬性注入。共 9 个注册 agent = 1 执行器 + 8 工具受限具名 (均无 Agent/Task 工具, 递归护栏): `skein-executor` (唯一 exec 执行器) / `skein-checker` (只读验证 + 一致性核查) / `skein-researcher` (planning 调研 + 本地代码环境/API 文档 + 第三方平台 + 按需加载用户 research skills + bootstrap 扫描模式) / `skein-setup` (trellis→skein 语义迁移) / `skein-finisher` (finish 收尾勘察) / `skein-specer` (记忆写盘员: sediment 落盘 + reconstruct·maintain 重组 + prune 降索引) / `skein-recaller` (记忆召回员: recall 检索, 只读同步) / `skein-dedup` (查重 + DAG 编排, 异步后台) / `skein-clean` (主动清理, 仅用户经 `/skein-clean` 显式调用)。

## 差异化核心: 规则记忆库 (基于 `.skein/spec`, namespace × inclusion)

不同于 spec 式「按需沉淀单一文件」, SKEIN 记忆按两个正交维度组织:

- **namespace (内容类型目录)** — `rules/` (硬规/契约) / `product/` (业务领域知识) / `map/` (项目结构映像) / `external/` (外部引用) 四类, 按 `SPEC_NAMESPACES` 开放不校验白名单
- **inclusion (加载策略)** — `always` (常驻注入) / `auto` (按需召回) / `fileMatch` (按 globs 匹配注入正文) / `manual` (纯手动), 每条规则的 `inclusion` frontmatter 决定何时加载

**namespace × 类目**: namespace 内按类目 (git/test/arch/build/style/domain/ops...) 分子目录, 自由取名按需建。索引: 每个 `<namespace>/index.md` (带 inclusion 列) + 顶层 `index.md` 聚合, sediment 写盘后自动 reindex。**加载策略不看目录, 看 frontmatter 的 `inclusion`** —— 两者正交。

**sediment 判定门**: 每个 task finish 后, 按 checklist 判本次 learning 该落哪个 `namespace` (内容类型目录) × 哪种 `inclusion` (加载策略: `always` 常驻注入 / `auto` 按需召回 / `fileMatch` 按 globs / `manual` 纯手动), 或 `drop`, 经审批写盘。频率驱动的 always↔auto 自动升降级为可选演进 (按需再加; 当前靠 `maintain --apply` 在超预算时降级)。

## 工作区

```
.skein/
├── .gitignore         # init 生成: 忽略 task.md/task.html/board/ (自动渲染); 另补 worktree_root 到根 .gitignore
├── task.json          # {tasks:[{id,status,deps,worktree}]} 全未归档 task (脚本维护)
├── task.md            # 顶层看板 (task.json 渲染, git 忽略, 禁直接编辑)
├── task.html          # 静态可视化看板 (title/标题带项目名; task.json 渲染, git 忽略, `skein serve --open` 打开)
├── board/             # 主题/配色 CSS (从插件 assets 拷贝, git 忽略, html link 引入)
├── config.yaml        # pools.work:2 / pools.gate:3 / retain_days:7 / auto_commit:true (仅原地模式生效) / worktree_root:.worktrees / board_theme / board_palette / board_mode
└── task/
    ├── <id>/          # 活跃 + 完成保留期内 task: prd.md(主入口) / design.md(详细设计) / findings.md(调研收敛) / research/ + task.json/task.md(脚本渲染)
    └── archive/<年>/<月-日>/<id>/   # 按完成日期分层归档 (完成超 retain_days 天自动移入)
.skein/spec/
├── index.md                             # 顶层索引 (全 namespace 聚合概览)
├── rules/{<类目>/*.md,index.md}        # 硬规/契约 (按类目分子目录) + 层索引
├── product/{<类目>/*.md,index.md}      # 业务领域知识 (按类目分子目录) + 层索引
├── map/{<类目>/*.md,index.md}          # 项目结构映像 (按类目分子目录) + 层索引
└── external/{<类目>/*.md,index.md}    # 外部引用 (按类目分子目录) + 层索引
```

> SKEIN 自包含: `skein` 自身即引擎, `config.yaml` 是纯设置, start/finish 直接干活 (hook 只做注入 / 护栏, 不驱动生命周期)。


## 用法

```
复杂/多步/跨文件请求会自动触发 skein-flow skill。
```

也可以在请求里明确说明“走 skein-flow 闭环”。

## 完整文档

`docs/` 有完整文档 (从 [docs/README.md](docs/README.md) 起):

| 想 | 读 |
| --- | --- |
| 装好插件跑通第一个 task | [docs/getting-started.md](docs/getting-started.md) |
| 搞懂内部运转 (流程/调度/记忆) | [docs/workflow.md](docs/workflow.md) |
| 不同活儿分别怎么用 | [docs/scenarios.md](docs/scenarios.md) |
| 最佳实践 + 流程图 | [docs/best-practices.md](docs/best-practices.md) |
| CLI/skill/agent 速查 | [docs/reference.md](docs/reference.md) |

## License

AGPL-3.0-or-later
