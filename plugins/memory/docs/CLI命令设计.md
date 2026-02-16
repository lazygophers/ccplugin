# CLI 命令设计

## 一、命令结构

```
uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py <command> [arguments] [options]
```

---

## 二、基础命令

### 2.1 read - 读取记忆

```bash
uv run ./scripts/main.py read <uri>
```

**示例**:
```bash
uv run ./scripts/main.py read project://structure
```

**输出**:
```
============================================================
URI: project://structure
优先级: 1 | 状态: active
访问次数: 42
触发条件: When navigating project files
------------------------------------------------------------
项目采用 monorepo 结构...
============================================================
```

### 2.2 create - 创建记忆

```bash
uv run ./scripts/main.py create <uri> <content> [options]
```

**选项**:
- `-p, --priority <level>` - 优先级 (0-10)，默认 5
- `-d, --disclosure <text>` - 触发条件

**示例**:
```bash
uv run ./scripts/main.py create project://dependencies "使用 uv 管理依赖" -p 1 -d "When checking dependencies"
```

### 2.3 update - 更新记忆

```bash
uv run ./scripts/main.py update <uri> [options]
```

**选项**:
- `-c, --content <text>` - 新内容
- `-p, --priority <level>` - 新优先级
- `-d, --disclosure <text>` - 新触发条件
- `--append` - 追加模式
- `--old <text>` - 替换前文本
- `--new <text>` - 替换后文本

**示例**:
```bash
uv run ./scripts/main.py update workflow://commands --append "新命令: npm run lint"
uv run ./scripts/main.py update project://config --old "旧配置" --new "新配置"
```

### 2.4 delete - 删除记忆

```bash
uv run ./scripts/main.py delete <uri> [options]
```

**选项**:
- `--force` - 硬删除（不可恢复）

**示例**:
```bash
uv run ./scripts/main.py delete task://todos/old
uv run ./scripts/main.py delete task://todos/old --force
```

### 2.5 search - 搜索记忆

```bash
uv run ./scripts/main.py search <query> [options]
```

**选项**:
- `-d, --domain <prefix>` - 限定 URI 前缀
- `-l, --limit <n>` - 结果数量限制，默认 10
- `--priority-min <n>` - 最小优先级
- `--priority-max <n>` - 最大优先级

**示例**:
```bash
uv run ./scripts/main.py search "dependencies" -d project
uv run ./scripts/main.py search "error" --priority-max 3
```

### 2.6 list - 列出记忆

```bash
uv run ./scripts/main.py list [options]
```

**选项**:
- `-d, --domain <prefix>` - 限定 URI 前缀
- `-l, --limit <n>` - 结果数量限制，默认 20
- `--priority-min <n>` - 最小优先级
- `--priority-max <n>` - 最大优先级
- `--status <status>` - 状态过滤

**示例**:
```bash
uv run ./scripts/main.py list -d project
uv run ./scripts/main.py list --priority-max 3 --status active
```

---

## 三、生命周期命令

### 3.1 priority - 设置优先级

```bash
uv run ./scripts/main.py priority <uri> <level>
```

**示例**:
```bash
uv run ./scripts/main.py priority project://core 1
```

### 3.2 deprecate - 废弃记忆

```bash
uv run ./scripts/main.py deprecate <uri> [options]
```

**选项**:
- `--reason <text>` - 废弃原因

**示例**:
```bash
uv run ./scripts/main.py deprecate project://old-config --reason "已迁移到新配置系统"
```

### 3.3 archive - 归档记忆

```bash
uv run ./scripts/main.py archive <uri>
```

### 3.4 restore - 恢复记忆

```bash
uv run ./scripts/main.py restore <uri>
```

---

## 四、版本控制命令

### 4.1 versions - 查看版本历史

```bash
uv run ./scripts/main.py versions <uri> [options]
```

**选项**:
- `-l, --limit <n>` - 版本数量限制，默认 10

**示例**:
```bash
uv run ./scripts/main.py versions workflow://commands
```

### 4.2 rollback - 回滚版本

```bash
uv run ./scripts/main.py rollback <uri> <version>
```

**示例**:
```bash
uv run ./scripts/main.py rollback user://preferences 2
```

### 4.3 diff - 版本对比

```bash
uv run ./scripts/main.py diff <uri> <version1> <version2>
```

**示例**:
```bash
uv run ./scripts/main.py diff workflow://commands 1 3
```

---

## 五、关系命令

### 5.1 relate - 创建关系

```bash
uv run ./scripts/main.py relate <source_uri> <target_uri> <relation_type> [options]
```

**关系类型**:
- `relates_to` - 相关
- `depends_on` - 依赖
- `contradicts` - 矛盾
- `evolves_from` - 演化自

**选项**:
- `-s, --strength <value>` - 关系强度 (0-1)，默认 0.5

**示例**:
```bash
uv run ./scripts/main.py relate project://config project://dependencies depends_on -s 0.8
```

### 5.2 relations - 查看关系

```bash
uv run ./scripts/main.py relations <uri> [options]
```

**选项**:
- `-d, --direction <dir>` - 关系方向：in/out/both，默认 both

**示例**:
```bash
uv run ./scripts/main.py relations project://config
```

---

## 六、管理命令

### 6.1 export - 导出记忆

```bash
uv run ./scripts/main.py export <output_file> [options]
```

**选项**:
- `-d, --domain <prefix>` - 限定 URI 前缀
- `--include-versions` - 包含版本历史
- `--include-relations` - 包含关系

**示例**:
```bash
uv run ./scripts/main.py export backup.json
uv run ./scripts/main.py export full-backup.json --include-versions --include-relations
```

### 6.2 import - 导入记忆

```bash
uv run ./scripts/main.py import <input_file> [options]
```

**选项**:
- `--strategy <strategy>` - 导入策略：skip/overwrite/merge，默认 skip

**示例**:
```bash
uv run ./scripts/main.py import backup.json
uv run ./scripts/main.py import backup.json --strategy merge
```

### 6.3 clean - 清理记忆

```bash
uv run ./scripts/main.py clean [options]
```

**选项**:
- `--unused-days <n>` - 清理未访问天数
- `--deprecated-days <n>` - 清理已废弃天数
- `--dry-run` - 仅预览，不执行

**示例**:
```bash
uv run ./scripts/main.py clean --unused-days 30 --dry-run
uv run ./scripts/main.py clean --deprecated-days 7
```

### 6.4 stats - 统计信息

```bash
uv run ./scripts/main.py stats
```

**输出**:
```
============================================================
记忆统计
============================================================

总数: 42
  活跃: 35
  已废弃: 5
  已归档: 2

按优先级分布:
  优先级 1: 5
  优先级 2: 8
  优先级 3: 12

按 URI 前缀分布:
  project://: 15
  workflow://: 10
  user://: 8

版本总数: 28
关系总数: 12
============================================================
```

### 6.5 preload - 预加载记忆

```bash
uv run ./scripts/main.py preload <uri> [options]
```

**选项**:
- `-l, --limit <n>` - 预加载数量，默认 5

---

## 七、Hook 命令

### 7.1 hooks - Hook 模式入口

```bash
uv run ./scripts/main.py hooks
```

从 stdin 读取 JSON 格式的 Hook 数据并处理。

---

## 八、通用选项

### 8.1 调试选项

- `--debug` - 启用 DEBUG 模式

**示例**:
```bash
uv run ./scripts/main.py --debug read project://structure
```
