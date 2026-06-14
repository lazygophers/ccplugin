# Spec 执行 (阶段 4)

⛔ 前置: 进入本阶段前确认阶段 3 审批门已通过 (用户走 AskUserQuestion 明确批准)。未批准禁写盘。

一次写盘, 不分多轮。审批通过的变更全部写完才返回。

## 写盘原则

1. **一次写盘**: 所有改动收集后批量写, 避免中间状态被并发 hook / 其他 agent 看到
2. **原子性**: ⛔ 任一文件写失败 → 立即停止后续写盘, 全部回滚已写文件 (见末段回滚), 禁留半写状态
3. **frontmatter 必带**: 每个改动文件附 metadata
4. **同步 index**: 若有 index / 目录 / 导航文件, 同步更新锚点
5. **manifest 引用清单**: 输出受影响 `implement.jsonl` / `check.jsonl` 列表给用户, **本 skill 不直接动 task manifest**

## Frontmatter 模板

每个改动 / 新建文件顶部:

```yaml
---
updated: <ISO date>
rewrite-version: <N>          # 破坏式重写次数 (新建从 1 起, 每次 REWRITE +1)
supersedes:                   # MERGE / 改名时填; 否则空数组或省略
  - <被合并 / 替换的旧文件名>
authored-by: trellisx-spec
mode: init | optimize | sediment
---
```

## 写盘顺序

```
1. NEW 文件 (无依赖, 先写)
2. SPLIT 源 → 多个新文件, 再删除源 (除非源仍保留为 index)
3. MERGE 多源 → 1 新文件, 然后删除源
4. REWRITE (同名覆盖)
5. EXTRACT (短化引用版本覆盖)
6. PATCH (微调, 最快)
7. DELETE 文件最后 (避免中间引用断裂)
8. 同步 index / 锚点 / 导航
```

## 操作命令

| 变更类型 | 实操 |
| --- | --- |
| NEW | `Write` 工具直接建 |
| DELETE | `Bash` `rm <path>`; 删后跑 grep 检查无悬空引用 |
| REWRITE | `Write` 覆盖整文件 (而非 Edit 多次) |
| MERGE | `Write` 写 target, 再 `rm` 源文件 |
| SPLIT | `Write` 写各 split 文件, 再 `Edit` / `Write` 源文件 (留剪贴版 / 全删) |
| EXTRACT | `Write` / `Edit` 覆盖文件, 内容仅留 `参见: <路径>#锚点` + frontmatter |
| PATCH | `Edit` 单点改 |

## 同步 task manifest 引用

写完 spec 后, grep 所有 task manifest 找受影响项:

```bash
for f in .trellis/tasks/*/implement.jsonl .trellis/tasks/*/check.jsonl; do
    [ -f "$f" ] || continue
    while IFS= read -r line; do
        path=$(echo "$line" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(d.get('path',''))" 2>/dev/null)
        # 检查 path 是否在本次 DELETE / MERGE 源 / SPLIT 源 / 改名 列表中
        if grep -q "$path" /tmp/changed-spec-paths.txt; then
            echo "AFFECTED: $f → $path"
        fi
    done < "$f"
done
```

输出格式给用户:

```
受影响 task manifest (需用户决定是否同步)
─────────────────────────────────────────
.trellis/tasks/<task-a>/implement.jsonl
  - 旧 path: guides/code-reuse-thinking-guide.md
  - 新建议: 改为 guides/core-contracts.md#code-reuse (因 MERGE)

.trellis/tasks/<task-b>/check.jsonl
  - 旧 path: guides/legacy-x.md
  - 新建议: 移除该行 (因 DELETE)
```

**本 skill 不动 task manifest**, 仅列清单。用户自行决定何时同步, 或调 trellisx-orchestrate 在下一次 task planning 时处理。

## 回滚 (写盘失败时)

🛑 STOP: 写盘任一步失败立即触发回滚, 禁带半写状态返回主会话。

写盘前先存 backup (优先用 git, 没 git 则复制):

```bash
if git rev-parse --git-dir > /dev/null 2>&1; then
    git stash push -- .trellis/spec/   # backup
    # 成功时: git stash drop (丢弃 backup)
else
    cp -r .trellis/spec /tmp/spec-backup-$(date +%s)
fi
```

| 触发 | 一线修复 | 仍失败兜底 |
| --- | --- | --- |
| 写盘中途某文件失败 | git 仓库: `git stash pop` 恢复; 非 git: `rm -rf .trellis/spec && mv /tmp/spec-backup-X .trellis/spec` | 报告主会话"spec 回滚失败, backup 在 <stash 名 / 备份路径>", 禁继续后续步骤, 由用户手动恢复 |
| backup 创建失败 (磁盘满 / 权限) | 禁开始写盘, 先清理后重试一次 | 报告"无法创建 backup, 中止本次写盘, 0 变更" |

## 完成报告

返回主会话:

```
spec 变更执行报告
═════════════════
模式: <init | optimize | sediment>
范围: <$范围>
批准 N 项, 执行 M 项 (跳过 N-M 项)
新增文件: <list>
修改文件: <list>
删除文件: <list>

受影响 task manifest: <count> 个
  - <列出>

自检结果 (见 selfcheck.md):
  - 命令式比例: X%
  - 描述式残留: Y 处
  - 死链: Z 处
  全达标 ✓ / 未达标 ✗ <列项>
```
