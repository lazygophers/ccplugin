# 步骤 3: spec/ 注入 (仅新增独立 worktree spec, 不动现有)

apply 对 spec 的**唯一动作** = 新增一个独立的 worktree 约定文件。**绝不变更/覆盖任何现有 spec** (包括 trellisx 之前写的)。

## 核心边界

- ✅ **仅当文件不存在时**新增 `.trellis/spec/guides/trellisx-worktree.md`
- ❌ 文件已存在 → **跳过, 一字不动** (保留用户可能的定制)
- ❌ **绝不**修改/覆盖/合并任何现有 spec 文件
- spec 的破坏式优化/重写是 `trellisx-spec` skill 的职责 (用户单独主动调), 与 apply 无关

> 即: 重复 apply 不会动 spec (文件已在则跳过)。spec 是只增不改。

## i18n

下方文档模板是中文语义参考。实际新增的 trellisx-worktree.md 用**目标语言** (设备/项目语言) 写, frontmatter key 保持英文。

## 新增文件: `.trellis/spec/guides/trellisx-worktree.md`

仅当不存在时创建:

```markdown
---
created: <ISO date>
authored-by: trellisx-apply
---

# trellisx worktree + subtask 约定

何时被读: trellis task 实施时 (sub-agent dispatch 注入)
谁读: main / 执行者 agent
不遵守的代价: worktree 污染主工作区 / subtask 无隔离

## worktree 隔离

- task.py start 后自动建 worktree (trellis 生命周期 hook after_start 自适应 3 布局: .trellis 同级 git / 微服务子目录 sparse / 多子仓读 task package 定位子仓 git); archive 触发 after_archive 销毁
- 多子仓 (.trellis 非 git 根, 子仓在下层如 go/node): task 须先 task.py set-scope <子仓> 标注, hook 才能定位
- 全部源码改动**必须**落 worktree 内, 主工作区保持干净
- main 可直接写源码 (trellis inline), 但目标路径必须在 worktree
- 复杂 / 并行 subtask → 派 sub-agent (isolation:worktree) 或 agent-team 成员
- task archive 时 worktree 干净 → 自动销毁; 脏 → 警告先合并

## subtask 拆分 + 异步并行

- task 拆 >= 2 subtask, 每 subtask 独立文件 `.trellis/tasks/<task>/subtask/<id>-<slug>.md`
- PRD 调度图显式标并行组 (无依赖 subtask 同批)
- 执行: 无依赖 subtask 同一消息一次性派多个 sub-agent (真并行); 禁串行逐个派
- parent-child 用 trellis 原生 `task.py add-subtask`
```

## 创建算法 (幂等 = 不存在才写)

```python
target = ".trellis/spec/guides/trellisx-worktree.md"
if os.path.exists(target):
    pass   # 已存在 → 跳过, 不动 (保留定制)
else:
    write(target, worktree_spec_content)   # 仅首次创建
```

## 不动现有 spec

apply 不读、不改、不覆盖任何已有 spec 文件。workflow.md 注入丢失时, 该 worktree spec 仍在 (持久); 但 apply 不会因 workflow 注入而重写 spec。
