# setup 场景：trellis 迁移

仅当仓库原用 trellis (`.trellis/` 存在)。`skein.py setup` 的 manifest `trellis_present:true` 触发本路径。纯新仓 / 已初始化维护不走这里。

## 两模式 (main 定, 缺省兼容)

| 模式 | 命令 | `.trellis/` 数据 | 接线 (hooks/scripts/settings + `.claude/*trellis*`) |
| --- | --- | --- | --- |
| **兼容 (默认)** | `skein.py setup` | 留 (spec/task 给其它工具) | **无条件删** (避免 skein/trellis 双注入) |
| **完全** | `skein.py setup --full` | 整删 `.trellis/` | 无条件删 |

两模式都: 独立拷 spec 入 `.skein/spec` + 物理迁移 task + 删接线。差异仅 `.trellis/` 数据目录是否整删。**接线删除不分模式** (哪怕兼容也删, 否则 trellis hook 继续注入压过 skein)。另: setup 在 `.claude/settings.local.json` 禁 trellisx 插件 (`enabledPlugins.trellisx@ccplugin-market=false`), 防插件级双注入。

## 载体：派 skein-setup agent (语义迁移)

scaffold + spec 拷贝 + task 迁移 + 接线删除已由 `skein.py setup [--full]` 完成, 但 spec 重组 / task 重建 / settings hook 剔除需语义判断 → 派 `skein-setup` agent。dispatch prompt 6 字段自包含：

- **目标**: 把已拷入 `.skein/spec` 的规则语义重组为 core/recall×类目 + 重建 task + 剔 settings 里**残留 (非 canonical)** trellis hook 条目。
- **已知**: `skein.py setup [--full]` 已跑 (模式=<兼容|--full>), manifest = `<粘贴 JSON>`; spec 已 `copytree` 独立拷入 `.skein/spec` (trellis 零改动), 接线已删 (含 canonical trellis hook 条目 + 脚本已硬剔)。
- **工作目录与范围**: 仓库根; 改 `.skein/spec` (原地重组) + `.skein/task/` + `.claude/settings*.json` (JSON 语义剔残留 hook)。
- **输出格式**: 见 skein-setup agent 定义 (spec 层/类目分布 + task 迁移数 + 清理清单)。
- **验收标准**: `memory.py list` 有分层规则; `skein.py list` 有迁移 task; `.claude/settings*.json` 无 trellis hook (canonical 已脚本清, 残留已 agent 清); 兼容模式 `.trellis/` 数据仍在 / `--full` 已整删。
- **失败处理**: agent 标 `需要:` → main 用 `AskUserQuestion` 转达用户裁定分层/字段歧义。

## 铁律

- **spec 已独立拷入 `.skein/spec`** — setup 用 `copytree` 拷贝 (非软链), trellis 零改动。agent 在 `.skein/spec` 原地重组, 安全不碰 trellis。
- **接线删除无条件** — `skein.py setup` 已删接线文件/目录 + **硬剔 `.claude/settings*.json` 内 canonical trellis hook 条目** (command 引用 session-start / inject-subagent-context / guard-version / inject-workflow-state 的, 连脚本一并删; rust-fmt 等用户自有 hook 保留)。agent 只清脚本漏网的**残留** hook (command 含 `trellis` 子串但非 canonical 脚本名, 如 `trellis.sh`)。
- **`--full` 破坏性** — 整删 `.trellis/`; main 派发即视为授权 (用户调 `setup --full` = 同意完全移除)。spec/task 已拷入 `.skein`, 删的是残留数据目录。
- **task.md / task.json 禁手改** — 迁移经 `skein.py create` 等命令, 不直接写 (PreToolUse hook 硬阻)。
