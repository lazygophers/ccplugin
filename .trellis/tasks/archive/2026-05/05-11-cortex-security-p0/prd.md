# PRD — Cortex P0 安全硬化

## 背景

cortex 插件当前 ingest 任意 URL / 模型输出直接落盘 vault,缺 3 类硬化:
1. **Secret 泄漏**:LLM 上下文里的 token/key 跟着 transcript 一起进 `log/YYYY-MM/`
2. **SSRF**:`cortex-ingest` 接受任意 URL → defuddle/WebFetch 可被诱导抓内网 (`127.0.0.1`、`169.254.169.254` AWS metadata)
3. **HTML 注入**:defuddle 输出的 markdown 可能含未剥的 `<script>` / `<iframe>` / `onerror=` 内联事件

对标 kioku `lib/masking.mjs` / `lib/url-security.mjs` / `lib/html-sanitize.mjs`。

## 目标

3 个 python module 落 `hooks/_lib/`,作纯函数式过滤器,被 skill 的 bash 入口前置调用。

## 范围

### 新增文件

- `plugins/tools/cortex/hooks/_lib/masking.py`
- `plugins/tools/cortex/hooks/_lib/url_security.py`
- `plugins/tools/cortex/hooks/_lib/html_sanitize.py`
- `plugins/tools/cortex/tests/python/test_masking.py`
- `plugins/tools/cortex/tests/python/test_url_security.py`
- `plugins/tools/cortex/tests/python/test_html_sanitize.py`

### 修改文件

- `plugins/tools/cortex/skills/cortex-ingest/SKILL.md` — 在 defuddle/WebFetch 后调 html_sanitize + masking,落档前调 url_security 拦截内网 URL
- `plugins/tools/cortex/skills/cortex-save/SKILL.md` — 写盘前调 masking
- `plugins/tools/cortex/hooks/_lib/save_session.py` — Stop hook 写 transcript 前调 masking
- `plugins/tools/cortex/AGENT.md` — 加 §安全声明 段(P0 硬化承诺)

### 不在范围

- 不动 `install.sh`
- 不动 `.claude-plugin/plugin.json`
- 不动其它 11 个 skill
- 不引外部 python pkg(纯 stdlib)

## 详细规范

### masking.py

```python
def mask(text: str) -> tuple[str, list[str]]:
    """返回 (masked_text, hit_list)。hit_list 记录命中规则名,不含原值。"""
```

命中规则(stdlib `re`):

| 规则名 | pattern | 替换 |
|---|---|---|
| `aws_akid` | `AKIA[0-9A-Z]{16}` | `<REDACTED:aws_akid>` |
| `openai_key` | `sk-[a-zA-Z0-9]{20,}` | `<REDACTED:openai_key>` |
| `anthropic_key` | `sk-ant-[a-zA-Z0-9-]{20,}` | `<REDACTED:anthropic_key>` |
| `github_pat` | `gh[pousr]_[A-Za-z0-9]{36,}` | `<REDACTED:github_pat>` |
| `jwt` | `eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+` | `<REDACTED:jwt>` |
| `pem_priv` | `-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]+?-----END [A-Z ]*PRIVATE KEY-----` | `<REDACTED:pem_priv>` |
| `slack_token` | `xox[abprs]-[A-Za-z0-9-]{10,}` | `<REDACTED:slack_token>` |

CLI 入口:`python3 masking.py < input > output`,stderr 打 hit 计数。

### url_security.py

```python
def is_safe(url: str) -> tuple[bool, str]:
    """返回 (safe, reason)。reason 含拒绝原因。"""
```

拒绝逻辑:
1. scheme 非 `http`/`https` → reject
2. 解析 host,DNS 解析(`socket.getaddrinfo`),命中以下任一即拒:
   - `127.0.0.0/8`、`10.0.0.0/8`、`172.16.0.0/12`、`192.168.0.0/16`
   - `169.254.0.0/16`(含 AWS/GCP metadata 端点)
   - `::1`、`fc00::/7`、`fe80::/10`
   - hostname == `localhost` / `metadata.google.internal` / `metadata`
3. port < 1024 且不在 {80, 443} → reject(防 22/3306 等)

用 `ipaddress` stdlib 判段。CLI:`python3 url_security.py <url>`,exit 0 通过,exit 1 拒绝,stderr 打 reason。

### html_sanitize.py

```python
def sanitize(markdown: str) -> str:
    """剥危险 HTML,保留普通文本/合法 markdown。"""
```

规则:
- 删 `<script[^>]*>[\s\S]*?</script>` (含闭合)
- 删 `<iframe[^>]*>[\s\S]*?</iframe>`
- 删 `<object>`、`<embed>`、`<svg onload=...>`
- 剥所有 `on[a-z]+="..."` / `on[a-z]+='...'` 内联事件属性
- 删 `javascript:` / `data:text/html` 协议链接(替换为 `#`)

不破坏合法 markdown 表格、代码块、wikilink、callout。

CLI:`python3 html_sanitize.py < input > output`。

### AGENT.md 增段

在 "## Skills 设计原则" 前加:

```markdown
## 安全声明 (P0)

cortex v2 对 ingest/save 流加 3 层过滤:
- **masking**: AWS/OpenAI/Anthropic key, GitHub PAT, JWT, PEM, Slack token → `<REDACTED:*>`
- **url-security**: 拒 `127/10/172.16-31/192.168/169.254` 网段 + IPv6 ULA/link-local + 非 80/443 低端口,防 SSRF
- **html-sanitize**: 剥 `<script>/<iframe>/onerror=/javascript:` 等注入向量

集成点: `cortex-ingest` (URL 入参 + defuddle 输出),`cortex-save` (写盘前),`save_session.py` (Stop hook transcript 落档)。
绕过: 测试场景 `CORTEX_SKIP_SANITIZE=1`,生产严禁。
```

## 验收标准

1. 3 个 python module + 3 个 pytest 文件存在,`pytest tests/python/` 全绿
2. masking: 命中 7 个规则各 ≥ 1 用例,无误伤普通文本
3. url_security: 9 个内网网段 + metadata host + 低端口各 1 拒绝用例,2 个 public URL 通过用例
4. html_sanitize: script/iframe/onerror/javascript: 各 1 拦截用例,合法 markdown(表格/代码块/wikilink) 1 保留用例
5. `cortex-ingest/SKILL.md` 工作流文档明示三过滤器调用点
6. `cortex-save/SKILL.md` 明示 masking 前置
7. `save_session.py` 调 `masking.mask()`,Stop hook 落档 transcript 已脱敏
8. AGENT.md §安全声明 段已加
9. 验证 AI 理解(CLAUDE.md §代码质量检查规范):
   ```bash
   claude --settings ~/.claude/settings.glm-4.7-flash.json -p "$(cat plugins/tools/cortex/skills/cortex-ingest/SKILL.md)" --output-format stream-json | jq -r 'select(.type=="result" and .subtype=="success") | .result'
   ```
   返回须明示三过滤器执行顺序

## 不变量

- 纯 stdlib,不引 `bleach`/`requests`/`yarl`
- 所有 module 幂等 + 纯函数,无文件 IO 副作用(CLI 入口除外)
- 命中规则只记规则名,不写原始 secret 入任何日志

## 风险

- regex 误伤:openai key 规则可能命中 `sk-` 开头的普通字符串。**缓解**:length ≥ 20 边界 + 单元测试覆盖普通文本
- DNS 解析阻塞:`getaddrinfo` 同步,慢 DNS 拖 ingest。**缓解**:`socket.setdefaulttimeout(2.0)`
- html_sanitize 误删合法代码块里的 `<script>` 字面量。**缓解**:跳过 fenced code block (` ``` ` 之间内容)
