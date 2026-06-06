# 上下文变体

## 概述

`llms.txt` 可展开为两种 LLM 上下文文件，由 `llms_txt2ctx` 工具生成。

## 变体对比

| 文件 | Optional 部分 | 用途 |
|---|---|---|
| `llms.txt` | 原始索引，链接不展开 | 导航/索引 |
| `llms-ctx.txt` | **排除** | 紧凑上下文，适合小窗口 |
| `llms-ctx-full.txt` | **包含** | 完整上下文，适合大窗口 |

## 生成方式

### CLI

```bash
pip install llms-txt

# 紧凑版（排除 Optional）
llms_txt2ctx llms.txt > llms-ctx.txt

# 完整版（包含 Optional）
llms_txt2ctx llms.txt --optional True > llms-ctx-full.txt
```

### Python API

```python
from llms_txt import parse_llms_file, create_ctx

# 解析
parsed = parse_llms_file(text)

# 紧凑上下文
ctx = create_ctx(text)

# 完整上下文
ctx_full = create_ctx(text, optional=True)
```

## 输出格式（XML）

`create_ctx` 生成 XML 结构，链接内容被实际抓取并内联：

```xml
<project title="FastHTML" summary='FastHTML is a python library...'>
Important notes:
- ...

<docs>
<doc title="FastHTML quick start" url="https://...">
[抓取的页面内容]
</doc>
</docs>

<examples>
<doc title="Todo list application" url="https://...">
[抓取的页面内容]
</doc>
</examples>
</project>
```

## 完整解析器（< 20 行，无依赖）

```python
from pathlib import Path
import re, itertools

def chunked(it, chunk_sz):
    it = iter(it)
    return iter(lambda: list(itertools.islice(it, chunk_sz)), [])

def parse_llms_txt(txt):
    "Parse llms.txt file contents in `txt` to a `dict`"
    def _p(links):
        link_pat = r'-\s*\[(?P<title>[^\]]+)\]\((?P<url>[^\)]+)\)(?::\s*(?P<desc>.*))?'
        return [re.search(link_pat, l).groupdict()
                for l in re.split(r'\n+', links.strip()) if l.strip()]
    start, *rest = re.split(fr'^##\s*(.*?$)', txt, flags=re.MULTILINE)
    sects = {k: _p(v) for k, v in dict(chunked(rest, 2)).items()}
    pat = r'^#\s*(?P<title>.+?$)\n+(?:^>\s*(?P<summary>.+?$)$)?\n+(?P<info>.*)'
    d = re.search(pat, start.strip(), (re.MULTILINE | re.DOTALL)).groupdict()
    d['sections'] = sects
    return d
```
