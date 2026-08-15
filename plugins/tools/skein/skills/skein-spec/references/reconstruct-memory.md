# 完全重构记忆 (reconstruct) — 从代码/项目内容重建规则库

**定位**: 把**既有**记忆 (全 namespace) 整体**可逆归档**后, 依据**当前代码库 + 项目内容**从零重建规则基线。区别于 bootstrap (仅空仓、纯增量) 与 finish sediment (单 task 踩坑增量)。

> **复用不新造**: 扫描仍用 `skein-researcher` (bootstrap 扫描模式), 写盘仍走 sediment 写盘流程。重构**只多两步**: 前置 `skein-spec archive` (可逆清库) + 后置按项目类型分型扫描。**唯一新脚本能力 = archive/restore**, 其余零改。

## 1. 何时重构 (vs bootstrap vs 增量)

| 场景 | 选 | 理由 |
|---|---|---|
| 首次用 SKEIN, spec 空 | **bootstrap** | 无旧规则可弃, 纯增量播种 |
| 单 task 踩坑/定契约 | **finish sediment** | 增量, 不动全局 |
| 大重构后规则大面积失效 (架构翻新/换技术栈/换语言) | **reconstruct** | 旧规则整体过期, 增量补不动 |
| 记忆漂移 (规则与代码现状矛盾, 累积陈旧) | **reconstruct** | 逐条修不如整体重建 |
| 接手成熟仓, 旧记忆来源不明/可疑 | **reconstruct** | 归档留证 + 按现状重建 |
| 记忆被误沉淀污染 (硬凑/inclusion 判错大量) | **reconstruct** | 一次清账好过逐条删 |

**触发硬门 (全满足才提议)**: ① 用户明确要重建 **或** 上述失效/漂移场景成立; ② 代码库有体量 (脚手架仓无约定可提 → 退回增量); ③ **`AskUserQuestion` 征同意** (归档虽可逆, 仍是全局动作, 禁自动)。

## 1.5 程度档位 (recall / low / full / deep / max / high)

`reconstruct --deep=<recall|low|full|deep|max|high>` —— 程度**不是脚本参数**, 落在 ②archive 范围 + ④扫描深度两处 (`skein-spec archive` 本身只认 `--namespace`, 六档由 skill 层决定何时带这个参数、何时全量归档)。默认 **full**; 用户未指定时按失效范围推荐并 `AskUserQuestion` 确认。

| 档 | ②archive 范围 | ④扫描 | ⑤旧规则比对 | 何时选 |
|---|---|---|---|---|
| **recall** | `archive --namespace <长尾 ns>` (其余 namespace 保留) | 五维基线 + **主类型**侧重 (§5) | 仅该 namespace 逐条比对 | 漂移/污染集中长尾, always 页仍可信 |
| **low** | `archive --namespace <长尾 ns>` (其余 namespace 保留) | 五维基线 (不加主类型侧重) | 仅该 namespace 逐条比对 | 轻量核查, 仅验证该 namespace 完整性, 比 recall 更省 |
| **full** | `archive` 全 namespace 归档 | 五维基线 + **主类型**侧重 (§5) | 全库逐条比对 | 换栈/架构翻新, always 页也过期 |
| **deep** | `archive` 全 namespace 归档 | 五维 + **全 8 型探针深扫** (§5 全表, 非仅主类型) + 项目内容全量 (§3) | 全库逐条比对 | 全面重建, 深挖长尾规则 |
| **max** | `archive` 全 namespace 归档 | 五维 + 全 8 型 + 项目内容全量 | 全库逐条 + 归档旧规则**逐条比对** | 彻底重建, 交叉验证新旧规则 |
| **high** | `archive` 全 namespace 归档 | 五维 + 全 8 型 + 项目内容全量 | 全库逐条 + 归档旧规则**全量核验 + 交叉验证** | 接手可疑成熟仓/来源不明, 从零核底 |

- **recall/low** (档名沿用历史, 与 namespace 名无关): 最省, 只归档长尾 namespace, 手工维护的 always 页不动。low 比 recall 更轻 (跳过主类型侧重扫描), 只做完整性核查用。
- **full**: 标准重构。主类型侧重扫描 (§4 识别 → §5 该型探针), 复合仓逐包套单型。
- **deep/max/high**: 逐档加码。deep 不信任任何主类型判定, 跑全 8 型探针 (§5 全表) 交叉扫, 宁多勿漏; max 在 deep 基础上对归档旧规则逐条比对去留; high 最重, 旧规则全量核验 + 交叉验证, 适合来源不明的成熟仓 —— 多花 token 换彻底。

## 2. 总流程 (main 同步驱动, 7 步)

reconstruct/bootstrap 是 main 亲做的全局动作 (整库归档/重建属全局编排); skein-specer 的 reconstruct 模式仅承接其中的批量写盘片段 (⑥ sediment 落盘), 不拥有整条流程。

```
① 快照现状 → ② 可逆归档 → ③ 识别项目类型 → ④ 分型扫描 →
⑤ 逐条定 ns×inclusion → ⑥ sediment 自动写盘 → ⑦ 验证 + 保留归档(供回滚)
```

### ① 快照现状 (审计基线)
```
skein-spec list          # 记下重构前各 namespace 条数/文件
```
留一句话交代重构动机 (哪种失效/漂移), 便于日后审计。

### ② 可逆归档 (清库, 非删除)
```
skein-spec archive       # full/deep/max/high: 全 namespace 归档到 .skein/spec/.archive/<ts>/
skein-spec archive --namespace <ns>  # recall/low 档: 只归档指定 namespace, 其余保留
```
归档后被归档的 namespace 空, 索引自动重建。**旧规则未删, 全在 `.archive/<ts>/`**, 回滚一条命令。

### ③ 识别项目类型 (决定扫描侧重)
按 §4 文件指纹表判**主类型** (可复合, 如 monorepo 内含 backend+frontend → 逐包分型)。识别错 → 扫描侧重偏, 但不致命 (仍走审批门兜底)。**low 档只扫五维基线不判主类型; deep/max/high 档跳过主类型收窄, 直接跑全 8 型探针**。

### ④ 分型扫描 (派 skein-researcher, bootstrap 模式 + 类型侧重)
dispatch prompt「已知」段标 `mode=bootstrap` + `tid=reconstruct` + **扫描侧重 (按程度档): recall/full = §5 主类型探针清单; low = 仅五维基线, 不加主类型侧重; deep/max/high = §5 全 8 型探针交叉扫 + 项目内容全量**。researcher 只读, 候选落盘 `.skein/task/reconstruct/research/conventions.md`。
- 五维基线 (命名/错误处理/测试/架构边界/构建) **恒扫**, 类型侧重 = 在此之上加权 + 追加类型专属探针。
- 每条候选 MUST 附证据 (file:line, ≥2 处一致才算约定; 单处 `推测:` 或 drop)。

### ⑤ 逐条定 namespace × inclusion (main; 或 drop)
判据同 [sediment-workflow §2](sediment-workflow.md)。两个维度别混: **namespace** = 内容类型 (放哪个目录), **inclusion** = 加载策略 (frontmatter 字段, always 常驻注入 / auto 按需召回 / fileMatch 按 globs / manual 纯手动)。

重构证据来自静态扫描 (非踩坑实证), **从严控 always**: 默认 `auto`, 仅"违反必炸"硬约束给 `always` (见 §5 各型 always 倾向) —— always 页占 SessionStart 常驻预算, 每加一条都在花每轮对话的 token。与归档旧规则**逐条比对**: 现状仍成立 → 重沉淀; 已过期 → drop (留在归档); 现状新增 → 新沉淀。

### ⑥ sediment 写盘 (main)
逐条走 sediment 写盘 ([sediment-workflow.md](sediment-workflow.md)), 同主题规则并入同一 `<类目>/<主题>.md` (禁一规则一文件)。重构跑前 (②前) 已一次 `AskUserQuestion` 征同意 (归档虽可逆仍全局动作), 覆盖整轮 —— 内部候选**自动写盘, 不逐条再问用户**; main 逐项输出 trace 供审阅, 误沉淀可 `skein-spec restore` 回滚归档或后续改 inclusion 纠正。

### ⑦ 验证 + 保留归档
```
skein-spec list          # 对比重构前后条数 / ns×inclusion 分布合理性
```
- **归档目录保留** (不删), 作回滚锚点 + 审计证据。确认新库无误后可手动清 `.archive/<ts>/`。
- 回滚: `skein-spec restore <ts>` (撞名旧规则加 `restored-` 前缀并存, 不覆盖新库)。

## 3. 项目内容 (非代码) 也入扫描

"根据代码、项目内容重构" — 除源码, 下列**项目内容**同为约定来源, researcher 一并扫:

| 来源 | 提什么 |
|---|---|
| `README` / `CONTRIBUTING` / `docs/` | 显式约定、开发流程、发布规范 |
| `CLAUDE.md` / `AGENTS.md` / `.cursorrules` | 已成文的 AI 协作硬规 (常可直接升 always) |
| CI 配置 (`.github/workflows` / `.gitlab-ci`) | 构建/测试/lint 门禁 = 可验证契约 |
| linter/formatter 配置 (`.eslintrc`/`ruff.toml`/`.editorconfig`) | 风格硬规 (机器已强制的可入 always) |
| `package.json` scripts / `Makefile` / `justfile` | 规范命令 (build/test/lint 入口) |
| ADR (`docs/adr/`) / 设计文档 | 架构边界、选型决策 (跨任务复用 → auto/always) |
| commit 历史/PR 模板 | git 约定、评审门槛 |

**成文约定 (CLAUDE.md/CI/linter) 优先级高于代码推断** — 它们是显式声明, 证据强度 > 静态模式归纳。

## 4. 项目类型识别 (文件指纹)

| 类型 | 指纹 (命中即倾向) |
|---|---|
| **backend-service** | `src/{controllers,services,repositories}`, ORM (prisma/sqlalchemy/gorm/hibernate), migrations/, Dockerfile, OpenAPI/proto |
| **frontend-spa** | `package.json` 含 react/vue/svelte/angular, `components/`, `*.tsx/.vue`, vite/webpack, `public/index.html` |
| **cli-library** | `bin/`/`cmd/`, `setup.py`/`pyproject`/`cargo.toml`/`go.mod` 且无 web server, `__main__`/entrypoint, 无前端资源 |
| **monorepo** | `pnpm-workspace.yaml`/`lerna.json`/`nx.json`/`turbo.json`/`go.work`/cargo workspace, 顶层 `packages/`/`apps/` |
| **data-ml** | `notebooks/`, `*.ipynb`, `dvc.yaml`/`mlflow`, `data/`/`models/`, pandas/torch/sklearn, pipeline (airflow/dagster/prefect) |
| **infra-iac** | `*.tf`, `helm/`, `k8s/`/`*.yaml` manifests, `ansible/`, Pulumi, `Dockerfile` 群 |
| **mobile** | `android/`+`ios/`, `*.swift`/`*.kt`, `Podfile`/`build.gradle`, React Native/Flutter (`pubspec.yaml`) |
| **docs-content** | 主体 `*.md`/`*.mdx`, 静态站点 (docusaurus/rspress/hugo/astro), 少或无应用源码 |

复合仓 (如 monorepo 含 backend+frontend): 先按 monorepo 处理跨包约定, 再对每包套对应单型侧重。

## 5. 分型设计 (事无巨细)

每型给: **扫描侧重** (五维加权) · **类型专属探针** · **always 倾向** (什么进常驻) · **典型规则示例** · **陷阱**。

### 5.1 backend-service (后端服务 / API)
- **侧重**: 架构边界 ★★★ · 错误处理 ★★★ · 测试 ★★ · 命名 ★ · 构建 ★
- **专属探针**: 分层依赖方向 (controller→service→repository, 禁反向/跨层); DB 访问位置 (禁 service 裸 SQL); 事务边界; API 契约 (DTO 校验、错误响应结构、状态码约定、版本策略); 鉴权/权限拦截点; 幂等性; 日志/追踪注入点; 配置来源 (env vs 硬编码); migration 规范。
- **always 倾向**: 分层禁令 (跨层访问必炸)、DB 层禁裸 SQL、密钥禁硬编码、事务边界规则 → `always`。命名/日志格式 → `auto`。
- **规则示例**: `MUST: 数据访问只经 repository, service/controller 禁直接建 SQL/ORM query` (always); `API 错误统一 {code,message,traceId}, 禁裸抛栈` (always); `新端点必附 OpenAPI 条目` (auto)。
- **product 产物**: 按 API 分组/领域模块产现状页 (端点清单 + 各自职责 + 鉴权要求), anchors 指向 controller/route 定义处。
- **陷阱**: 把某个具体 endpoint 的实现细节当约定 (一次性, drop); 把框架默认行为写成规则 (语言/框架通识, drop)。

### 5.2 frontend-spa (前端 / Web UI)
- **侧重**: 命名/目录 ★★★ · 架构边界 (状态/数据流) ★★★ · 风格 ★★ · 构建 ★★ · 错误处理 ★
- **专属探针**: 组件划分 (容器/展示、原子设计层级); 状态管理边界 (全局 store vs 局部 state, 禁组件直连 API?); 数据获取层 (hooks/service 封装); 路由约定; 样式方案 (CSS-in-JS/module/tailwind, 禁内联?); 设计 token/主题变量 (禁硬编码色值 — 呼应本仓 board 主题化); i18n; 可访问性基线; 类型边界 (props/API 类型来源)。
- **always 倾向**: 数据流硬约束 (禁组件内直接 fetch、状态必经 store)、禁硬编码设计值 → always (若团队强约束)。多数前端约定弹性大 → auto。
- **规则示例**: `组件禁直接调 API, 数据获取统一走 hooks/<domain>` (always/auto 视强度); `颜色/间距禁硬编码, 走 CSS 变量/token` (auto); `页面组件放 pages/, 复用组件放 components/` (auto)。
- **product 产物**: 按页面/功能域产现状页 (路由 → 页面 → 主要交互流程), anchors 指向 pages/routes 定义处。
- **陷阱**: 前端惯例主观且演进快, 极易硬凑 — 无 ≥2 处一致证据一律 drop; 勿把单个组件写法当全局约定。

### 5.3 cli-library (CLI 工具 / 库)
- **侧重**: 公共 API 面 ★★★ · 命名 ★★★ · 测试 ★★ · 错误处理 ★★ · 构建/发布 ★★
- **专属探针**: 公共 vs 私有边界 (`__all__`/export 约定、`_private`); 语义化版本/破坏性变更政策; 参数解析约定 (argparse/click/cobra 模式); 退出码约定; stdout/stderr 分工 (数据 vs 日志); 无副作用/纯函数倾向; 依赖最小化 (禁重依赖?); 文档字符串/示例规范; 打包/发布命令。
- **always 倾向**: 公共 API 稳定性契约 (禁破坏性变更不升 major)、退出码/流分工 → always。命名/docstring → auto。
- **规则示例**: `公共 API 破坏性变更 MUST 升 major + CHANGELOG` (always); `错误走 stderr + 非零退出码, stdout 只出结构化结果` (always); `新命令必附 --help 示例` (auto)。
- **product 产物**: 命令/API 清单现状页 (子命令树 + 各命令用途), anchors 指向 CLI 入口/dispatch 表。
- **陷阱**: 库的内部实现自由度高, 只锁公共契约; 勿把内部 helper 写法上升为规则。

### 5.4 monorepo (多包 / 工作区)
- **侧重**: 架构边界 (包依赖图) ★★★ · 构建 ★★★ · 命名 ★★ · 测试 ★★
- **专属探针**: 包依赖方向 (禁循环、禁上层被下层依赖); 共享类型/工具的归属包; 跨包 import 规则 (禁深路径 import, 走包入口); 版本策略 (fixed/independent); 构建编排 (turbo/nx pipeline、affected 检测); 各包独立 lint/test 还是统一; 顶层 vs 包级配置继承。
- **always 倾向**: 包依赖禁令 (循环/反向必炸)、跨包 import 边界 → `always`。全局约定进通用类目, 包专属约定归 `domain`/包名类目 (`auto`)。
- **规则示例**: `包间禁循环依赖; 共享逻辑提到 packages/shared` (always); `跨包只从包入口 import, 禁 packages/x/src/internal 深路径` (always); `新包必挂 turbo pipeline` (auto)。
- **product 产物**: 包依赖图现状页 (各包职责 + 依赖方向), anchors 指向各包 package.json/入口。
- **陷阱**: 别把一个包的局部约定当全仓规则 — 标清适用范围 (类目/关键词带包名); 复合仓需对每包再套单型侧重, 勿一刀切。

### 5.5 data-ml (数据 / ML pipeline)
- **侧重**: 可复现性 ★★★ · 架构边界 (数据契约) ★★★ · 构建/环境 ★★ · 测试 ★
- **专属探针**: 数据契约 (schema、数据来源/版本、DVC/lakeFS); 随机种子/确定性约定; 实验追踪 (mlflow/wandb 记录规范); notebook vs 生产代码边界 (禁 notebook 入生产?); 特征/模型版本化; pipeline 步骤幂等/可重跑; 环境锁定 (conda/requirements lock); 数据脱敏/隐私 (敏感数据禁入库/日志)。
- **always 倾向**: 可复现硬约束 (种子固定、数据版本锁)、数据隐私禁令 → always。实验记录格式 → auto。
- **规则示例**: `训练 MUST 固定 seed + 记录数据版本/超参到 mlflow` (always); `notebook 禁直接进生产 pipeline, 逻辑下沉 src/` (always/auto); `敏感字段禁入日志/中间产物` (always)。
- **product 产物**: pipeline 现状页 (数据来源 → 特征 → 模型 → 产出), anchors 指向 pipeline 定义/DAG 文件。
- **陷阱**: 探索性 notebook 写法多变, 不当约定源; 只锁"可复现 + 隐私 + 数据契约"三硬骨, 余下 drop。

### 5.6 infra-iac (基础设施 / IaC / DevOps)
- **侧重**: 声明式约定 ★★★ · 架构边界 (模块/环境) ★★★ · 命名 ★★ · 安全 ★★★
- **专属探针**: 模块化 (terraform module 边界、复用); 环境分离 (dev/staging/prod 隔离、禁跨环境引用); 状态管理 (remote state、锁); 命名/标签规范 (资源 tag 强制); 密钥管理 (禁明文、走 vault/secrets manager); 幂等性; 变更审查 (plan 必审、禁手动改线上); 最小权限。
- **always 倾向**: 安全硬规 (禁明文密钥、最小权限)、环境隔离禁令、状态锁 → always。命名/标签 → auto (除非合规强制)。
- **规则示例**: `密钥禁明文入 tf/yaml, 走 secrets manager 引用` (always); `禁手动改线上, 一切变更经 plan+apply 审查` (always); `资源必带 owner/env/cost-center 标签` (auto/always 视合规)。
- **product 产物**: 环境/模块拓扑现状页 (dev/staging/prod 各环境资源清单), anchors 指向 module/环境目录。
- **陷阱**: IaC 安全项优先级最高, 宁可多问用户也别漏 always 安全规则; 别把某模块参数当全局约定。

### 5.7 mobile (移动端)
- **侧重**: 架构边界 ★★★ · 命名/目录 ★★ · 平台约定 ★★ · 构建/发布 ★★
- **专属探针**: 架构模式 (MVVM/MVI/Redux); 平台差异隔离 (iOS/Android 分支约定); 导航约定; 状态/数据层边界; 资源管理 (图片/字符串/本地化); 权限申请规范; 网络层封装; 构建变体 (flavor/scheme); 发布/签名流程。
- **always 倾向**: 架构分层硬约束、权限/隐私合规 → `always`。平台惯例 → `auto`。
- **规则示例**: `业务逻辑禁入 View/Activity, 走 ViewModel` (always/auto); `字符串禁硬编码, 走本地化资源` (auto); `敏感权限申请必附说明文案 + 最小化` (always)。
- **product 产物**: 主要用户流程现状页 (页面/导航图 + 各屏职责), anchors 指向 screen/Activity/ViewController。
- **陷阱**: 跨平台 (RN/Flutter) 与原生约定差异大, 先判子类型再套; 平台 SDK 通识 drop。

### 5.8 docs-content (文档 / 内容仓)
- **侧重**: 结构/命名 ★★★ · 风格 ★★ · 构建 ★ · 其余 ✗
- **专属探针**: 目录/文件组织约定; frontmatter 规范 (必填字段); 写作风格 (术语表、语气、格式); 链接/引用规范 (禁死链); 图片/资源管理; 站点构建/发布命令; i18n/多版本。
- **always 倾向**: 极少进 always — 多为 auto。仅"发布前必过链接检查"类门禁可入 always。
- **规则示例**: `每文档 frontmatter 必含 title/description` (auto); `内链走相对路径, 发布前跑死链检查` (auto/always); `术语统一见 glossary, 禁同义混用` (auto)。
- **product 产物**: 站点结构现状页 (章节/目录组织 + 各章节定位), anchors 指向站点导航配置。
- **陷阱**: 内容仓约定轻, 别硬造技术型规则填库; 无信号老实播空。

## 6. 失败 & 回滚路径

| 情况 | 处理 |
|---|---|
| 归档后重建不满意 (漏规则/inclusion 判错) | `skein-spec restore <ts>` 恢复旧库, 撞名新规则加 `restored-` 前缀并存, 再手动取舍 |
| 项目类型识别不准 | 复合/存疑时按多型探针都扫 (宁多勿漏), 判定门兜底; 或问用户确认主类型 |
| researcher 缺信息/范围不清 | 回传标 `需要: <问题>`, main 补齐 dispatch 或转达用户 |
| 代码库无明显约定 (脚手架/极小仓) | 播空/少量, 禁硬凑; 老实说明"无约定可提", 退回增量积累 |
| `archive`/`restore` 报错 | 读 stderr 定位 (路径/权限); 归档为原子 rename, 半失败时 `.archive/<ts>/` 与原库并存, 手动核对后 restore 或续跑 |
| 用户只想弃部分 namespace | `archive --namespace <ns>` 只重建该 namespace, 其余保留 |

## 7. 反例

| 禁 | 改为 |
|---|---|
| 直接删旧规则再重建 | 先 `archive` (可逆), 确认后再清归档 |
| 自动跑重构不问用户 | `AskUserQuestion` 征同意 (归档虽可逆仍是全局动作) |
| 忽略项目类型一刀切扫描 | 按 §4 识别 + §5 分型侧重 |
| 只扫代码忽略项目内容 | CLAUDE.md/CI/linter/README 同为约定源, 且成文优先 |
| 静态扫描证据当踩坑实证塞满 always | 从严控 always, 默认 auto, 仅"违反必炸"进 always |
| 候选跳过判定门盲写 | 逐条走 sediment 判定门 (通过即自动写) |
| 无约定硬凑填库 | 播空/少量, 老实说明 |
| 重构完立即删归档 | 保留作回滚锚点 + 审计, 确认无误再清 |
| 为重构大改 skein-spec | 只用新增 archive/restore, 扫描/写盘复用 researcher + sediment |
