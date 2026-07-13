# 子任务拆分 + 调度 DAG (落 task.json)

exec 阶段的 DAG = task.json `subtasks[].depends_on`, **由 `skein subtask add` 登记, 不写 mermaid 图文件**。planning 未登记任何 subtask → `skein start` 硬拒。

拆分时先用一张表理清 subtask + 依赖 + 验收 + agent (agent 省略默认 `skein-executor`, skills 0-n 逗号分隔), 再逐行落盘:

| subtask | depends_on | 验收标准 (checklist) | agent | skills |
|---|---|---|---|---|
| st1 | - | 迁移可回滚; 新列有默认值 | skein-executor | db-migration |
| st2 | st1 | 新字段透传响应; 旧字段不删 | skein-executor | - |
| st3 | st1 | 覆盖新旧字段两条路径 | skein-executor | - |

落盘 (planning 执行, main 同步跑):

```bash
skein subtask add <tid> st1 --name "改 schema"   --desc "加迁移列并回填默认值" --agent skein-executor --skills db-migration --check "迁移可回滚; 新列有默认值"
skein subtask add <tid> st2 --name "改调用站点" --desc "调用站点透传新字段" --agent skein-executor --deps st1 --check "新字段透传响应; 旧字段不删"
skein subtask add <tid> st3 --name "加测试"     --desc "覆盖新旧字段两条路径" --agent skein-executor --deps st1 --check "覆盖新旧字段两条路径"
```

`sid`/`--name`/`--desc`/`--agent` 四者必填 (缺一 argparse 报错); `--deps`/`--check`/`--skills`/`--estimate` 选填。

- `depends_on` 是唯一显式边源: st2/st3 依赖 st1 → st1 未 done 前不 ready; st2/st3 互不依赖 → 可并行 (并发上限 2)。
- 并行与否只看这张 DAG, 不靠脚本猜写文件重叠 (拆分时把真正有序的关系写进 `--deps`)。
- 运行态看 `skein subtask list <tid>` (脚本落盘), 不看任何 md 文件。
