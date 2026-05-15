# cortex-ingest — P0 安全过滤 (三过滤器, 顺序严格)

> SKILL.md §1.5 P0 安全过滤详细规范。详见 AGENT.md §安全声明。

按以下顺序调用, 任一拒绝即终止本条目摄取:

## 1. url_security — URL 入参前置, 拒内网 + metadata + 低端口 SSRF

```bash
python3 ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/hooks/_lib/url_security.py "$URL" \
  || { echo "rejected SSRF target: $URL" >&2; exit 1; }
```

拒绝清单:
- `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`
- IPv6 ULA / link-local
- 非 80/443 低端口

## 2. defuddle / WebFetch + html_sanitize

defuddle / WebFetch 拉取 markdown → 立即调 **html_sanitize** 剥 `<script>/<iframe>/onerror=/javascript:` 等注入向量 (fenced code block 内字面量保留):

```bash
CLEAN_MD="$(python3 ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/hooks/_lib/html_sanitize.py <<< "$RAW_MD")"
```

## 3. masking — 落档前最后一道, 脱敏 secret

```bash
SAFE_MD="$(python3 ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/hooks/_lib/masking.py <<< "$CLEAN_MD")"
```

脱敏目标: AWS / OpenAI / Anthropic key + GitHub PAT + JWT + PEM + Slack token。

## 绕过 (仅测试)

`CORTEX_SKIP_SANITIZE=1`,生产禁用。

## 集成点

- `cortex-ingest` URL 入参 + defuddle 输出
- `cortex-save` 写盘前
- `save_session.py` Stop hook transcript 落档

命中只记规则名 (不含原值), 实现位于 `hooks/_lib/{masking,url_security,html_sanitize}.py`, 纯 stdlib, 幂等纯函数。
