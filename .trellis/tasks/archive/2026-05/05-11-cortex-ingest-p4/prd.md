# PRD — Cortex P4 Ingest Pipeline

## 背景

P1 落了 MCP 骨架 + search/save。当前 ingest 路径是 `cortex-ingest` skill 引导模型用 `WebFetch`/`defuddle`,**单路、仅 HTML、不支持本地文件**。

kioku 通过 `mcp/tools/ingest-{url,pdf,document}.mjs` + `mcp/lib/{readability,epub,html-to-markdown,url-fetch,llm-fallback}.mjs` 把 ingest 沉到 MCP,支持 PDF/EPUB/DOCX/URL,双路抽正文。

P4 把 ingest 也沉 MCP,新增 2 tool + extractor 层,P0 三过滤器自动串入。

## 目标

`plugins/tools/cortex/mcp/tools/` 加 2 tool,extractor 层落 `mcp/lib/extractors/`,P0 三过滤器(url_security/html_sanitize/masking)自动 wire 进流水线。新增 `cortex-ingest-bulk` skill 支持 urls.txt 批量。

## 范围

### 新增文件

```
plugins/tools/cortex/mcp/
├── tools/
│   ├── ingest_url.py        # cortex_ingest_url MCP tool
│   └── ingest_file.py       # cortex_ingest_file MCP tool
└── lib/
    └── extractors/
        ├── __init__.py
        ├── html.py          # readability stdlib-impl 备选, defuddle 主路
        ├── pdf.py           # pypdf 文本抽
        ├── epub.py          # ebooklib 章节抽
        └── docx.py          # python-docx 段落抽
plugins/tools/cortex/mcp/tests/
├── test_ingest_url.py
├── test_ingest_file.py
└── fixtures/
    ├── sample.pdf           # 小 PDF (公开 PD 文献片段, < 50KB)
    ├── sample.epub          # 小 EPUB (项目自己生成的)
    └── sample.docx          # 小 DOCX
plugins/tools/cortex/skills/cortex-ingest-bulk/
└── SKILL.md                 # urls.txt 批量 ingest 触发
```

### 修改文件

- `mcp/pyproject.toml` — 加 `pypdf>=4.0`、`ebooklib>=0.18`、`python-docx>=1.1`
- `mcp/server.py` — 注册 ingest_url + ingest_file
- `.claude-plugin/plugin.json` — `skills` 数组追加 `./skills/cortex-ingest-bulk`
- `skills/cortex-ingest/SKILL.md` — 加 §调用优先级 (P4),首选 `mcp__cortex__ingest_url`/`ingest_file`,defuddle 仅 fallback
- `AGENT.md` — §MCP 主路径 表追加 ingest_url / ingest_file / ingest-bulk 行

### 不在范围

- 不动 P0 三过滤器代码(只 wire)
- 不动 P1 search/save tool
- 不引 LLM-fallback(kioku 有,我们留 P5+)
- 不动 hooks .sh

## 详细规范

### 1. extractor 接口契约

所有 extractor 实现统一签名:

```python
def extract(source: bytes | str | Path) -> dict:
    """
    返回:
      {
        "title": str | None,
        "body": str,            # markdown 化的正文
        "meta": dict,           # 任意元信息 (author, lang, page_count, etc)
        "warnings": list[str],  # 非致命解析告警
      }
    raise:
      ValueError              # 输入格式不合法/不支持
      RuntimeError            # 抽取失败 (corrupt/encrypted)
    """
```

### 2. `mcp/lib/extractors/html.py`

主路:不实现,调用方传入已抽好的 markdown(由 WebFetch/defuddle 输出)
备选:**纯 stdlib readability**,基于评分(`<article>`/`<main>`/`<p>` 密度)挑主体节点,转 markdown
不引 `readability-lxml` / `beautifulsoup4` 等外部 dep

输出:`extract(html_str) -> {"title", "body", "meta": {"lang": ...}, "warnings"}`

### 3. `mcp/lib/extractors/pdf.py`

```python
from pypdf import PdfReader

def extract(path: Path) -> dict:
    reader = PdfReader(str(path))
    body_parts = []
    for page in reader.pages:
        body_parts.append(page.extract_text() or "")
    return {
        "title": reader.metadata.title if reader.metadata else None,
        "body": "\n\n".join(p.strip() for p in body_parts if p.strip()),
        "meta": {
            "page_count": len(reader.pages),
            "author": reader.metadata.author if reader.metadata else None,
        },
        "warnings": ["scan-only pdf, text empty"] if not "".join(body_parts).strip() else [],
    }
```

PDF 加密时 raise `RuntimeError("encrypted PDF")`。

### 4. `mcp/lib/extractors/epub.py`

```python
from ebooklib import epub, ITEM_DOCUMENT

def extract(path: Path) -> dict:
    book = epub.read_epub(str(path))
    chapters = []
    for item in book.get_items_of_type(ITEM_DOCUMENT):
        # 章节 HTML → 用 html.extract 转 markdown
        html_doc = item.get_content().decode("utf-8", errors="replace")
        chapters.append(_html_to_markdown(html_doc))
    return {
        "title": book.get_metadata("DC", "title")[0][0] if book.get_metadata("DC", "title") else None,
        "body": "\n\n---\n\n".join(chapters),
        "meta": {
            "author": book.get_metadata("DC", "creator")[0][0] if book.get_metadata("DC", "creator") else None,
            "lang": book.get_metadata("DC", "language")[0][0] if book.get_metadata("DC", "language") else None,
            "chapter_count": len(chapters),
        },
        "warnings": [],
    }
```

### 5. `mcp/lib/extractors/docx.py`

```python
import docx  # python-docx

def extract(path: Path) -> dict:
    doc = docx.Document(str(path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return {
        "title": doc.core_properties.title or None,
        "body": "\n\n".join(paragraphs),
        "meta": {
            "author": doc.core_properties.author,
            "paragraph_count": len(paragraphs),
        },
        "warnings": [],
    }
```

### 6. `mcp/tools/ingest_url.py`

```python
INGEST_URL_TOOL = Tool(
    name="ingest_url",
    description="抓 URL 抽正文落档 cortex vault: url_security→fetch→html_sanitize→masking→save",
    inputSchema={
        "type": "object",
        "properties": {
            "url": {"type": "string", "format": "uri"},
            "kind": {"type": "string", "enum": ["concept", "domain", "log"]},
            "title": {"type": "string", "description": "可选, 缺则用 HTML <title>"},
            "host": {"type": "string"},
            "org": {"type": "string"},
            "repo": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["url", "kind"],
    },
)

async def handle_ingest_url(args: dict) -> list[TextContent]:
    # 1. url_security.is_safe(url) — fail-closed
    # 2. urllib.request.urlopen(url, timeout=10)  -- 不引 requests
    # 3. Content-Type 路由:
    #    - text/html → extractors.html.extract
    #    - application/pdf → 临时落盘 → extractors.pdf.extract
    #    - 其它 → raise ValueError
    # 4. html_sanitize.sanitize(body) 后置
    # 5. 复用 save tool 内部函数: 写盘前 masking + 路径解析 + frontmatter + block-id
    # 6. 返回 {path, source_url, block_ids, hits, warnings}
```

### 7. `mcp/tools/ingest_file.py`

```python
INGEST_FILE_TOOL = Tool(
    name="ingest_file",
    description="读本地文件抽正文落档 cortex vault: pdf/epub/docx → extract → masking → save",
    inputSchema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "绝对路径"},
            "kind": {"type": "string", "enum": ["concept", "domain", "log"]},
            "title": {"type": "string"},
            "host": {"type": "string"}, "org": {"type": "string"}, "repo": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["path", "kind"],
    },
)

async def handle_ingest_file(args: dict) -> list[TextContent]:
    # 1. Path(args["path"]).resolve() 必须存在 + readable
    # 2. 扩展名路由:
    #    .pdf → pdf.extract
    #    .epub → epub.extract
    #    .docx → docx.extract
    #    .md / .txt → 直读 (无 extractor)
    #    其它 → raise ValueError(f"unsupported: {ext}")
    # 3. masking.mask(body) 前置 save
    # 4. 复用 save 内部
    # 5. 返回 {path, source_file, block_ids, hits, warnings}
```

### 8. `mcp/tools/save.py` 重构(轻量)

抽出 `_save_internal(kind, title, body, host, org, repo, tags, source_meta) -> dict` 给 ingest tool 复用。原 `handle_save` 仅 wrap inputSchema + 调 `_save_internal`。

### 9. `skills/cortex-ingest-bulk/SKILL.md`

```markdown
---
name: cortex-ingest-bulk
description: 批量摄取 urls.txt 文件到 cortex vault. 触发: "批量摄取" / "bulk ingest" / "ingest urls.txt"
allowed-tools: Read Bash mcp__cortex__ingest_url
disable-model-invocation: false
---

# cortex-ingest-bulk

读取用户提供的 `urls.txt`(每行一个 URL,`#` 开头注释跳过),对每行调用 `mcp__cortex__ingest_url`。

## 工作流

1. Read urls.txt
2. 解析行,过滤空行/注释
3. 循环调 mcp__cortex__ingest_url(url=..., kind="log"),并发 ≤ 2
4. 失败行(url_security 拒、抽取失败)写 `urls.txt.failed`
5. 汇总:成功数 / 失败数 / 总耗时

## 失败处理

- url_security 拒 → 不重试,记 failed
- 网络超时 → 重试 1 次
- 抽取失败 → 记 failed
```

### 10. `AGENT.md` §MCP 主路径 表扩

```markdown
| skill | MCP tool | 回退 |
|-------|---------|------|
| cortex-search | `mcp__cortex__search` | L1-L5 |
| cortex-save | `mcp__cortex__save` | L1-L3 |
| cortex-ingest | `mcp__cortex__ingest_url` / `ingest_file` | WebFetch + defuddle |
| cortex-ingest-bulk | 循环调 `mcp__cortex__ingest_url` | 手动逐条 |
```

## 验收标准

1. `pytest plugins/tools/cortex/mcp/tests/test_ingest_*.py` 全绿:
   - ingest_url: HTTP 200 HTML / PDF / 拒 SSRF / 404 / Content-Type 错 各 1
   - ingest_file: pdf / epub / docx / md / 不支持扩展名 / 不存在路径 / 路径逃逸 各 1
2. extractor 单元测试覆盖 4 个 extractor 各 ≥1 正例 + 1 异常 (encrypted/corrupt/empty)
3. pipx 重装 (`pipx install --force plugins/tools/cortex/mcp/`) 成功,新 dep 装入 venv
4. `python3 -c "from mcp.tools import ingest_url, ingest_file; print('ok')"` 在 mcp dir cwd 下成功
5. plugin.json `skills` 数组包含 `cortex-ingest-bulk`,JSON 合法
6. AGENT.md MCP 主路径表新行有效
7. P0/P1 不回归:`pytest plugins/tools/cortex/mcp/tests/` + `bash plugins/tools/cortex/tests/run.sh` 全绿
8. 安全:
   - ingest_url 拒内网 URL 早于 fetch (test 验证)
   - ingest_file 拒 `path="../../etc/passwd"` (resolve 后非系统敏感目录? 至少 OSError on permission)
   - 所有 ingest 后 body 经 masking,fixture 故意含 `AKIAIOSFODNN7EXAMPLE` 验证 `<REDACTED:*>`

## 不变量

- 纯 stdlib + 4 个 ingest dep (`pypdf`, `ebooklib`, `python-docx`, `mcp`),**禁** beautifulsoup4 / lxml / readability-lxml / requests
- 所有 ingest 流必经 P0 三过滤器(`url_security`/`html_sanitize`/`masking`),wire 顺序固定
- extractor 纯函数,无文件 IO 副作用(读自己的 path 不算副作用)
- save 内部抽函数后,handle_save 行为不变

## 风险

- **pypdf 解析慢/卡死**:大 PDF 阻塞。**缓解**:`signal.alarm(30)` 或 ProcessPoolExecutor timeout(留 backlog)
- **ebooklib 老 epub2 编码错乱**:`decode(errors="replace")` 不丢段
- **python-docx 不支持 doc**:仅 docx,test 覆盖错扩展名
- **html.extract 自研 readability 召回低**:文档说明"可降级到 defuddle/WebFetch fallback"
- **批量 ingest 写并发**:save 已有 flock 防御,但 hot/index patch 仍可能 race。**缓解**:bulk skill 串行 (并发 ≤ 1 写 hot/index)
