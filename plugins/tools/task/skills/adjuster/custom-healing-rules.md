# 用户自定义自愈规则

## 概述

支持用户在 `.claude/self-healing-rules.yaml` 定义自定义自愈规则。自定义规则优先级高于内置规则。

## 规则格式

```yaml
rules:
  - name: "Python模块缺失"
    pattern: "ModuleNotFoundError: No module named '(.+)'"
    action: "pip install $1"
    verify: "python -c 'import $1'"
    priority: high

  - name: "权限问题"
    pattern: "permission denied.*executable"
    action: "chmod +x $file"
    verify: "test -x $file"
    priority: medium
```

## 字段说明

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| name | string | 是 | 规则名称 |
| pattern | regex | 是 | 错误匹配正则（支持捕获组 $1-$9） |
| action | string | 是 | 修复命令 |
| verify | string | 否 | 验证命令 |
| priority | enum | 否 | high/medium/low |
| max_retries | int | 否 | 最大重试次数（默认 3） |

## 加载优先级

1. 用户自定义（.claude/self-healing-rules.yaml）
2. 项目级（.claude/project-healing-rules.yaml）
3. 内置（17 种）
