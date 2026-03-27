# 快速开始

## 安装

Statusline 模块是项目的一部分，无需额外安装。

## 基本配置

### 使用默认配置

```python
from scripts.statusline.config.manager import get_default_config

config = get_default_config()
```

### 自定义配置

```python
from scripts.statusline.config.manager import Config

config = Config(
    layout_mode="compact",
    theme="dark",
    layout_width=80,
)
```

### 从文件加载配置

```python
from scripts.statusline.core.compat import load_config_from_file
from pathlib import Path

config = load_config_from_file(Path("config.json"))
```

## 第一个 Statusline

### 简单示例

```python
from scripts.statusline.config.manager import get_default_config
from scripts.statusline.core.loop import StatuslineLoop

# 创建配置和主循环
config = get_default_config()
loop = StatuslineLoop(config)

# 处理 transcript
transcript = '{"role": "user", "content": "Hello, world!"}'
result = loop.process(transcript)

print(result)  # 输出: [空闲] | [░░░░░░░░░░░░] 0% | [0 tokens] | [0ms]
```

### 处理多轮对话

```python
import json

transcripts = [
    {"role": "user", "content": "First message"},
    {"role": "assistant", "content": "Response"},
]

for transcript in transcripts:
    result = loop.process(json.dumps(transcript))
    print(result)
```

## 选择布局模式

### 扩展布局

显示完整信息，适合宽屏。

```python
config.layout_mode = "expanded"
```

输出示例：
```
[思考中] | [████████░░] 80% | [12.5K tokens] | [2:30] | [0 errors]
```

### 紧凑布局

优化空间利用，适合窄屏。

```python
config.layout_mode = "compact"
```

输出示例：
```
● | 80% | 12.5K
```

## 选择主题

### 可用主题

- `default`: 默认主题
- `minimal`: 极简主题（无颜色）
- `colorful`: 彩色主题
- `dark`: 深色主题
- `light`: 浅色主题

### 应用主题

```python
config.theme = "dark"
```

## 下一步

- 查看 [API 参考](api-reference.md) 了解详细接口
- 查看 [配置指南](configuration.md) 了解更多配置选项
- 查看 [主题定制](themes.md) 学习自定义主题
