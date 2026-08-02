# hooks.py 适配 + fileMatch 注入 + 修两现存 bug — 详细设计

架构 / 数据流 / 关键取舍 / 技术选型 (不含调度图, 调度归 task.json):

## 1. 两个现存 bug 的根因

| bug | 位置 | 根因 | 修 |
|---|---|---|---|
| `created` 误告警 | `hooks.py:177` `SPEC_REQUIRED` | `spec.py` 后来立了「时间类字段一律不写 (注入上下文无意义且费 token; 新旧判定走 git/文件系统 mtime)」的约定, 但 hook 的必填表没跟着改 | 从必填表移除 `created` |
| external 报非法 layer | `hooks.py:178` `SPEC_LAYERS = ("core","recall")` | `spec.py:48` `LAYERS` 后来加了 `external`, hook 的白名单没同步 | 白名单换成 `SPEC_INCLUSIONS` 四值 |

**共同根因**: hook 把 `spec.py` 的常量**复制**了一份而非引用, 两边漂移。

**本轮不做的**: 不改成 `from spec import ...` 跨模块引用 —— hook 是 5s timeout 的热路径, `spec.py` 顶部有 argparse 等 import, 拉进来会拖启动。**保持复制, 但在两处都留互指注释**标明必须同步改。

## 2. `cmd_spec_meta` 校验表

| 字段 | 规则 |
|---|---|
| `title` | 必填非空 |
| `namespace` | 必填非空; **不校验白名单** (开放可扩展) |
| `inclusion` | 必填且 ∈ `always\|auto\|fileMatch\|manual` |
| `keywords` | 必填非空 |
| `globs` | 仅当 `inclusion: fileMatch` 时必填 |
| `anchors` | 仅当 `namespace ∈ {product, map}` 时**建议** (缺则 warning) |
| ~~`created`~~ | **移除** — 与「时间类字段一律不写」约定冲突 |

全部非阻塞 warning, 经 `hookSpecificOutput.additionalContext` 输出。

## 3. fileMatch 注入 (挂 `cmd_guard`, 接线零改动)

```
PreToolUse (Edit|Write|MultiEdit|Read)
  → cmd_guard(d)
      ① 原职责: 硬阻 AI 直读写 .skein/ 的 task.json / task.md   ← 完全保留, 先跑
      ② 新增: file_path 匹配 fileMatch 页的 globs → 注入该页正文
```

**为什么挂 `cmd_guard` 而不新增 hook**: 接线已在, matcher 已覆盖 `Edit|Write|MultiEdit|Read`, `file_path` 已在手上。新增 hook 等于给 `plugin.json` 加一条做同一件事的接线。

**性能** (5s timeout 是硬约束):
- fileMatch 页的 `globs` 从 `<namespace>/index.md` 索引行读, **不逐个打开 md 文件** —— 索引已含 inclusion 列, 一次读一个文件就能筛出候选
- 只有 glob 命中后才打开对应页读正文
- 匹配用 `fnmatch.fnmatch` (stdlib), glob 相对工作区根解析

**为什么只做工作区级**: Kiro 的 fileMatch 在 `~/.kiro/steering/` 下静默不生效 (issues/9176), 根因是全局文件的 glob 没有 workspace root 可解析。skein 不做用户级 fileMatch, 直接绕开 —— 用户级需要条件加载时用 `auto` (语义召回)。

## 4. `cmd_stop_check` 跟随判据分表

现状: 调 `Spec._scan_findings` 拿问题项 → 有则写 `.pending-fix` → main 派 specer 自动修。

改: `product` namespace 的失效项**过滤掉不写标记**。理由 —— 需求真值不能自动删/改, `product` 的处置是「只报告」, 写了标记等于让 auto-fix 去自动改它。

`spec.py` 的 `_scan_findings` 若已按 namespace 分表返回 (归 `spec-model-core` s6), 此处只需按 namespace 过滤, 不重复判据逻辑。

## 5. 关键取舍

| 取舍 | 决定 | 理由 |
|---|---|---|
| hook 引用 `spec.py` 常量 vs 复制 | **保持复制 + 互指注释** | hook 是 5s 热路径, import `spec.py` 拖启动; 但要留注释防再次漂移 |
| fileMatch 新 hook vs 挂 `cmd_guard` | **挂 `cmd_guard`** | 接线已在, `file_path` 已在手上; 新增等于重复接线 |
| globs 来源 | **读 index.md 索引行** | 不逐个开 md 文件, 保住 5s timeout |
| 用户级 fileMatch | **不做** | Kiro 的同款设计在全局目录静默失效; 用户级要条件加载走 `auto` |
| 校验失败处置 | 全部非阻塞 warning | 阻断用户的 Write 是最差体验; spec 元数据不齐不影响正确性 |

## 6. 测试接缝 (seam)

**唯一接缝 = `cmd_*` 函数**, 直接喂构造的 hook 输入 dict (`{"tool_input": {"file_path": ...}}`), 断言返回码与 stdout JSON。

- 复用现有 hooks 测试的既有接缝, 不新建
- fileMatch 用例: `tmp_path` 造含 fileMatch 页的 spec 库 + 构造命中/未命中两种 `file_path`
- **回归用例是重点**: 无 fileMatch 页时 `cmd_guard` 输出与改前逐字节一致; guard 原有的 task.json 硬阻行为不变

## 7. 已知风险

| 风险 | 缓解 |
|---|---|
| `cmd_guard` 加逻辑后超 5s timeout | globs 从 index 读不开 md; 加规模用例 (50 页 < 1s) |
| 注入内容过大挤占上下文 | fileMatch 页也计入预算体检 (`maintain`); 单页超大在 `maintain` 报告里可见 |
| glob 写法歧义 (`*.py` vs `**/*.py`) | 文档明确按 `fnmatch` 语义, 相对工作区根; 用例覆盖两种写法 |
| `_scan_findings` 签名变更 (`spec-model-core` s6 在改) | 依赖 `spec-model-core` 先完成; 本 task 不改 `spec.py` |
