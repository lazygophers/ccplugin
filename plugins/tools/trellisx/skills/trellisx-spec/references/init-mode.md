# init 模式 (从零建 spec)

`.trellis/spec/` 空或仅 `index.md` 时触发。跳过诊断, 直接从模板生成首版提案。

## 首版结构 (推荐起点)

```
.trellis/spec/
├── index.md                    # 导航 + 锚点目录
├── guides/
│   ├── core-contracts.md       # 跨层 / 跨模块契约硬规
│   ├── code-reuse.md           # 重用 / 防重复造轮子硬规
│   ├── testing.md              # 测试硬规 (覆盖率 / 边界 / 主路径)
│   ├── error-handling.md       # 错误处理 / 失败回退硬规
│   └── naming-conventions.md   # 命名 / 文件结构硬规
└── workflows/
    ├── pre-commit.md           # commit 前必跑
    └── code-review.md          # review checklist
```

实际建什么节按项目特点定; 不一定全建, 但每个建的文件都要满足 `rewrite-style.md` 命令式标准。

## index.md 模板

```markdown
---
updated: <ISO>
rewrite-version: 1
authored-by: trellisx-spec
mode: init
---

# spec 目录

何时被读: sub-agent dispatch 时按 `implement.jsonl` / `check.jsonl` 引用加载
谁读: trellis-implement / trellis-check / 任何走 .trellis 任务编排的 sub-agent
不遵守的代价: 规则失效 = 项目契约层崩塌, 跨任务一致性丧失

## guides (跨任务硬规)

- [core-contracts](guides/core-contracts.md) — 跨层 / 跨模块契约
- [code-reuse](guides/code-reuse.md) — 重用与防重复
- [testing](guides/testing.md) — 测试覆盖与边界
- [error-handling](guides/error-handling.md) — 错误处理与回退
- [naming-conventions](guides/naming-conventions.md) — 命名与文件结构

## workflows (流程硬规)

- [pre-commit](workflows/pre-commit.md) — commit 前必跑
- [code-review](workflows/code-review.md) — review checklist
```

## guides/core-contracts.md 模板

```markdown
---
updated: <ISO>
rewrite-version: 1
authored-by: trellisx-spec
mode: init
---

# 核心契约硬规

何时被读: 改跨层 / 跨模块 / 跨包代码时
谁读: trellis-implement sub-agent
不遵守的代价: 跨层耦合泄漏 → 测试无法独立 / 局部回滚不可行 / 连锁修改

## 跨层调用

- 改 ≥ 2 层 (e.g. controller + service) 必须先列每层契约边界, 缺一不改
- 跨层调用必须走显式接口, 禁直接读对方实现字段
- 验证: `grep -rE '<对方实现字段>' src/ | grep -v <允许目录>` 必须 0 行

## 接口契约

- 公共接口必须有 schema / 类型签名 / OpenAPI 定义, 禁纯文字描述
- 改动公共接口必须先改 schema 文件, 再改实现 (TDD-spec)
- 验证: `<schema-lint-cmd>` 退出码 0

## 数据流

- 数据流必须有方向, 禁循环依赖
- 若必要打破循环必须用 event / DI / interface, 不准直接 import
- 验证: `<deps-check-cmd>` 退出码 0
```

## guides/code-reuse.md 模板

```markdown
---
...
---

# 代码重用硬规

何时被读: 写新函数 / 新模块 / 新组件前
谁读: trellis-implement sub-agent
不遵守的代价: 重复造轮子 → 维护双份代码 → bug 修一份漏一份

## 写新代码前

- 写新函数前必须 grep 项目同名 / 同语义函数
- grep 模式: `<具体词列表>` 在 `src/**` `packages/**`
- 命中则用旧, 禁新写
- 若旧实现 ≥ 3 调用站点, 必须改造旧实现而非旁路新写

## 工具与抽象

- 共享逻辑必须抽到 `<utils-dir>` / `<shared-dir>`, 禁散在业务代码
- 抽取阈值: 同语义代码出现 ≥ 3 处时必抽
- 验证: 抽取后跑 `<duplicate-check-cmd>` 重复块 ≤ 5%
```

## 起步建议

- init 时仅建 3-5 个最关键 spec 文件, 不要全建
- 内容来自用户对话提到的硬规 + 项目根 CLAUDE.md / AGENTS.md / README.md 抽提
- 每个文件 ≤ 50 行起步, 后续 sediment 模式增量补
- index.md 是必建项

## 提案输出

阶段 2 propose 输出形如:

```
init 模式首版提案 (共 N 项 NEW)

#1 NEW .trellis/spec/index.md (~30 行)
   导航 + 锚点目录

#2 NEW .trellis/spec/guides/core-contracts.md (~50 行)
   跨层 / 接口 / 数据流 3 节, 每节 3 条 MUST + 1 验证

#3 NEW .trellis/spec/guides/code-reuse.md (~40 行)
   写新代码前 + 工具与抽象 2 节
...

预计影响: 后续所有 task dispatch 时按 jsonl 引用读
```

进入审批门, 用户批准后执行。
