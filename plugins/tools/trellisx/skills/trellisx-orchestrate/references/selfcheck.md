# Planning → Start 最终自检

`task.py start` 前跑一遍, 任一不过 = 不许启动。

## PRD

- [ ] 目标含可证伪结果对象 (动词 + 对象 + 结果)
- [ ] Deliverable 矩阵每条独立可验收
- [ ] Subtask 概览表与详情文件 ID 一致
- [ ] Mermaid 调度图含全部 subtask + 依赖箭头 + 并行/串行视觉区分
- [ ] 范围内 / 范围外 (out of scope) 显式列
- [ ] 验收标准每条可执行
- [ ] 风险列表每条配缓解
- [ ] 多 deliverable 且独立可交付 → 已走 parent/child

## Subtask 文件

每个 subtask 文件:
- [ ] frontmatter 字段全 (id / slug / deliverable / status / execution-layer / depends-on)
- [ ] 五要素填全 (目标 / 产出 / 验证 / 资源 / 依赖)
- [ ] 验证 = 可执行命令 + 期望输出
- [ ] 资源覆盖所有写入点
- [ ] 依赖用 ID 引用, 无模糊词
- [ ] 若 execution-layer = sub-agent, dispatch prompt 6 字段填全
- [ ] 写盘 sub-agent / workflow 的 isolation = worktree (仅纯只读可 none)
- [ ] 回滚步骤可执行

## Design

- [ ] 架构概览有图 (ASCII / Mermaid)
- [ ] 模块切分边界清晰
- [ ] 每模块标执行层 + 独占资源
- [ ] 接口契约可机器校验 (schema / 类型)
- [ ] 数据流无循环 (或循环有显式打破方案)
- [ ] 回滚形状存在
- [ ] 取舍留痕 (选了什么不选什么 + 理由)
- [ ] 风险 ≥ 3 条配缓解

## Implement

- [ ] Checklist 按依赖严格拓扑排序
- [ ] 每条 checklist 项可独立执行
- [ ] 验证 = 命令 + 期望输出
- [ ] 依赖用 S<id> 显式
- [ ] 资源标注覆盖所有写入
- [ ] Review gate 在不可回滚步骤前 / 跨层契约首次实现处
- [ ] 每条有 rollback

## Parent / Child (若适用)

- [ ] Parent PRD 含 Child Map 表
- [ ] Parent PRD 含跨 Child 集成验收
- [ ] 每个 Child 可独立 task.py start / complete
- [ ] Child 间依赖在 child 内部 prd / implement 写明
- [ ] Parent 知道自己是否要做直接工作

## jsonl

- [ ] `implement.jsonl` 所有 path 真实存在
- [ ] `check.jsonl` 所有 path 真实存在
- [ ] 仅含 spec / research, 不含代码文件
- [ ] 不含整个目录, 选具体文件
- [ ] 每条 purpose ≤ 60 字

## 资源 / 并行

- [ ] 并行 subtask 资源集合不交
- [ ] 共享资源 subtask 已加依赖串行化
- [ ] 用户审批槽位互斥已考虑

## 失败回退 / 回收

- [ ] 每个 subtask 有 rollback
- [ ] 不可回滚操作有 review gate 前置
- [ ] sub-agent dispatch prompt 含失败处理 4 条
- [ ] 完成后必跑 trellis Phase 3.1 / 3.3 / 3.4 已记入 implement.md

## Cross-check

- [ ] PRD subtask 概览 = 全部 subtask 文件 (无遗漏 / 无多余)
- [ ] PRD mermaid 图 depends-on 关系 = subtask frontmatter `depends-on` / `blocks`
- [ ] design 模块执行层 = subtask `execution-layer`
- [ ] implement.md 顺序 = mermaid 拓扑顺序
- [ ] design 资源边界 ⊇ subtask 资源
