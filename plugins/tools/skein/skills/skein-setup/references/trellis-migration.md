# setup 场景：trellis 迁移

仅当仓库原用 trellis (`.trellis/` 存在)。`skein.py setup` 的 manifest `trellis_present:true` 触发本路径。纯新仓 / 已初始化维护不走这里。

## 载体：派 skein-setup agent (语义迁移)

scaffold 已由 `skein.py setup` 建好 (`.skein/` + `.skein/spec` 软链 `.trellis/spec`), 但 spec 重组 / task 重建 / 残留清理需语义判断 → 派 `skein-setup` agent。dispatch prompt 6 字段自包含：

- **目标**: 把 `.trellis/` (spec/task/.claude 接线) 语义迁移为 skein 结构并清残留。
- **已知**: `skein.py setup` 已跑, manifest = `<粘贴 JSON>`; 决策已定 — **软链保留 `.trellis/spec`** (不删), `.skein/spec` 已软链过去。
- **工作目录与范围**: 仓库根; 改 `.trellis/spec` (经软链原地重组) + `.skein/task/` + `.claude/` trellis 接线。
- **输出格式**: 见 skein-setup agent 定义 (spec 层/类目分布 + task 迁移数 + 清理清单)。
- **验收标准**: `memory.py list` 有分层规则; `skein.py list` 有迁移 task; `.claude/*trellis*` 与 `.trellis/task*` 已清; `.trellis/spec` 软链仍有效。
- **失败处理**: agent 标 `需要:` → main 用 `AskUserQuestion` 转达用户裁定分层/字段歧义。

## 铁律

- **spec 决策 (已拍板)**: `.skein/spec` **软链** → `../.trellis/spec`, 原地重组, **保留 `.trellis/spec`**。清理只删 `.trellis/task*` + `.claude/*trellis*`, 不碰 spec。
- **清理是破坏性操作** — `skein.py setup --purge` 由 agent 在内容迁走后调用; main 派发即视为授权 (用户调 setup = 同意迁移清理)。
- **task.md / task.json 禁手改** — 迁移经 `skein.py create` 等命令, 不直接写 (PreToolUse hook 硬阻)。
