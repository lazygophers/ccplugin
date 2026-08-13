---
name: version
description: "SemVer 版本管理。Trigger: 'version show', 'version bump', 'version set', '版本号'"
argument-hint: <show|info|bump <level>|set <version>>
model: haiku
memory: project
---

# 版本管理

根据参数执行对应操作：

## show

```bash
cat .version
```

## info

```bash
echo "当前版本: $(cat .version)"
echo "Git 状态: $(git status --porcelain .version)"
```

## bump \<level\>

level 可选值：`build`、`patch`、`minor`、`major`。

```bash
PLUGIN_NAME=version uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py bump <level>
```

## set \<version\>

```bash
echo "<version>" > .version
```
