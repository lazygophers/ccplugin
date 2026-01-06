---
name: plugin-testing
description: Claude Code 插件测试技能。当用户需要测试插件、验证 plugin.json、测试 commands/agents/skills 或本地安装插件时自动激活。提供插件测试策略、验证方法和调试技巧。
auto-activate: always:true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, TodoWrite
---

# Claude Code 插件测试

## 测试策略

### 测试层次

1. **格式验证**：验证配置文件格式
2. **结构检查**：验证目录结构
3. **功能测试**：测试插件功能
4. **集成测试**：测试与 Claude Code 集成

## 格式验证

### plugin.json 验证

```bash
# 使用 jq 验证 JSON 格式
cat .claude-plugin/plugin.json | jq .

# 验证必需字段
cat .claude-plugin/plugin.json | jq '.name' | grep -q ".*"
cat .claude-plugin/plugin.json | jq '.description' | grep -q ".*"
```

### marketplace.json 验证

```bash
# 验证 JSON 格式
cat .claude-plugin/marketplace.json | jq .

# 验证插件列表
cat .claude-plugin/marketplace.json | jq '.plugins[] | .name'
```

### SKILL.md 验证

```bash
# 检查 frontmatter
grep -q "^---" skills/*/SKILL.md
grep -q "^name:" skills/*/SKILL.md
grep -q "^description:" skills/*/SKILL.md
```

## 结构检查

### 目录结构验证

```bash
# 检查必需目录
ls -d .claude-plugin commands agents skills 2>/dev/null

# 检查必需文件
ls .claude-plugin/plugin.json
find commands/ -name "*.md"
find agents/ -name "*.md"
find skills/ -name "SKILL.md"
```

### 命名规范验证

```bash
# 检查插件名称（kebab-case）
cat .claude-plugin/plugin.json | jq '.name' | grep -E '^[a-z0-9-]+$'

# 检查 SKILL.md 文件名（大写）
find skills/ -name "SKILL.md"
```

### 完整性检查

```bash
# 检查所有配置的路径是否存在
for dir in commands agents skills; do
  if [ -d "$dir" ]; then
    echo "✓ $dir exists"
  else
    echo "✗ $dir missing"
  fi
done
```

## 本地安装测试

### 安装插件

```bash
# 从本地路径安装
/plugin install ./path/to/plugin

# 查看已安装插件
/plugin list

# 查看插件详情
/plugin info plugin-name
```

### 测试命令

```bash
# 列出可用命令
/help

# 执行自定义命令
/my-command arg1 arg2
```

### 测试技能

```bash
# 技能应该自动激活
# 触发技能条件，观察是否激活
```

### 测试代理

```bash
# 手动调用代理（如支持）
# 或通过命令触发
```

## 功能测试

### 命令测试

```markdown
# 测试用例：命令参数处理

## 输入
/my-command test arg1 arg2

## 预期输出
- 正确解析参数
- 执行相应操作
- 返回正确结果
```

### 技能测试

```markdown
# 测试用例：技能激活

## 触发条件
用户提问涉及技能主题

## 预期行为
- 技能自动激活
- 提供相关指导
- 遵循技能规范
```

### 代理测试

```markdown
# 测试用例：代理调用

## 触发条件
符合代理使用场景

## 预期行为
- 代理被正确调用
- 使用正确的工具
- 遵循代理指令
```

## 集成测试

### 端到端测试

```bash
# 1. 安装插件
/plugin install ./my-plugin

# 2. 使用命令
/my-command test

# 3. 验证结果
# 检查输出、副作用等
```

### � 兼容性测试

```bash
# 测试与其他插件的兼容性
/plugin install other-plugin
/my-command test
```

### 性能测试

```bash
# 测量命令执行时间
time /my-command test

# 测量技能加载时间
# 观察激活速度
```

## 调试技巧

### 启用详细日志

```bash
# 查看插件日志
export CLAUDE_DEBUG=1
/plugin install ./my-plugin
```

### 检查路径

```bash
# 验证插件路径
ls -la "${CLAUDE_PLUGIN_ROOT}"

# 检查文件权限
ls -l commands/ agents/ skills/
```

### 手动执行脚本

```bash
# 如果有 hooks 脚本
./hooks/script.sh

# 查看脚本输出
```

### 交互式调试

```bash
# 使用 Claude Code 对话
# 描述问题
# 观察响应
```

## 测试清单

### Pre-Release（发布前）

- [ ] plugin.json 格式正确
- [ ] 所有必需目录存在
- [ ] commands/agents/skills 格式正确
- [ ] 命名规范符合
- [ ] 本地安装成功
- [ ] 命令执行正确
- [ ] 技能激活正常
- [ ] 代理调用成功
- [ ] 无错误或警告
- [ ] 文档完整

### 功能测试

- [ ] 所有命令可执行
- [ ] 所有技能可激活
- [ ] 所有代理可调用
- [ ] 参数处理正确
- [ ] 错误处理完善
- [ ] 边界情况覆盖

### 集成测试

- [ ] 与 Claude Code 兼容
- [ ] 与其他插件兼容
- [ ] 性能可接受
- [ ] 资源占用合理

## 自动化测试

### 测试脚本

```bash
#!/bin/bash
# test-plugin.sh

set -e

echo "Testing plugin..."

# 验证格式
echo "Validating plugin.json..."
cat .claude-plugin/plugin.json | jq . > /dev/null

# 检查结构
echo "Checking structure..."
[ -d .claude-plugin ]
[ -d commands ] || echo "No commands directory"
[ -d agents ] || echo "No agents directory"
[ -d skills ] || echo "No skills directory"

# 检查命名
echo "Validating naming..."
NAME=$(cat .claude-plugin/plugin.json | jq -r '.name')
if [[ ! "$NAME" =~ ^[a-z0-9-]+$ ]]; then
  echo "Invalid plugin name: $NAME"
  exit 1
fi

echo "All tests passed!"
```

### CI/CD 集成

```yaml
# .github/workflows/test.yml
name: Test Plugin

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Validate plugin.json
        run: cat .claude-plugin/plugin.json | jq .
      - name: Check structure
        run: ./scripts/test-plugin.sh
```

## 常见问题排查

### 插件安装失败

1. 检查 plugin.json 格式
2. 验证路径正确
3. 查看错误日志

### 命令不工作

1. 验证命令格式
2. 检查 allowed-tools
3. 测试命令执行

### 技能不激活

1. 验证 auto-activate
2. 检查 description
3. 测试触发条件

### 代理调用失败

1. 验证代理格式
2. 检查权限设置
3. 测试代理指令

## 参考资源

- [官方插件测试指南](https://code.claude.com/docs/en/plugins.md)
- [plugin-development skill](../.claude/skills/plugin-development/SKILL.md)
- [plugin-review skill](../.claude/skills/plugin-review/SKILL.md)
