# 目录结构规范

## 标准结构

每个 Skill 必须是一个以 `SKILL.md` 为入口点的目录：

```
skill-name/
├── SKILL.md           # 入口文件（必需）
├── topic.md          # 支持文件（可选）
├── examples/
│   └── sample.md     # 示例（可选）
└── scripts/
    └── helper.py     # 脚本（可选）
```

## 文件角色

| 文件 | 必需 | 用途 |
|------|------|------|
| `SKILL.md` | ✅ | 入口文件，包含 YAML frontmatter + 主要指令 |
| `*.md` | ❌ | 支持文档，包含详细参考 |
| `scripts/*.py` | ❌ | 可执行脚本，通过 bash 运行 |
| `templates/*.md` | ❌ | 模板文件 |

## 命名约定

### Skill 目录名

```bash
# ✅ 正确
python-coding
git-workflow
security-review
deploy-process

# ❌ 避免
PythonCoding      # 大写
git_workflow      # 下划线
DeployProcess     # 驼峰
```

### frontmatter name

```yaml
---
name: python-coding      # 与目录名对应
description: ...
---
```

### 支持文件

```bash
# ✅ 正确
coding-standards.md
examples.md
troubleshooting.md

# ❌ 避免
CodingStandards.md     # 大写
examples               # 无扩展名
```

## 嵌套目录

支持子目录组织：

```
security-review/
├── SKILL.md              # 主要指令
├── checklist/
│   ├── owasp-top10.md
│   ├── authentication.md
│   └── authorization.md
└── templates/
    ├── vulnerability-report.md
    └── security-review.md
```

## 资源文件

### 脚本文件

```bash
# 位置
skill-name/scripts/

# 命名
helper.py
validate.py
generate.py

# 调用方式
Claude 通过 bash 运行：`bash scripts/helper.py`
脚本代码不进入上下文，仅输出进入
```

### 模板文件

```bash
# 位置
skill-name/templates/

# 命名
report.md
checklist.md

# 使用方式
在指令中引用：参考模板 [report.md](templates/report.md)
```

## 结构示例

### 简单 Skill

```
explain-code/
├── SKILL.md      # 单一文件
```

### 中等复杂度 Skill

```
python-coding/
├── SKILL.md
├── type-hints.md
├── imports.md
└── testing.md
```

### 复杂 Skill

```
security-review/
├── SKILL.md
├── owasp/
│   ├── top10.md
│   └── injection-attacks.md
├── auth/
│   ├── authentication.md
│   └── authorization.md
├── templates/
│   └── review-report.md
└── scripts/
    ├── scan-dependencies.py
    └── validate-config.py
```

## 规范要点

1. **保持 SKILL.md < 500行**
2. **详细参考移至支持文件**
3. **使用清晰的文件名**
4. **按主题组织子目录**
