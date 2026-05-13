<!-- cortex-template-version: 2 -->
<!--
  mermaid-sankey.md — Grok Live Artifacts 风桑基图 (用于固化流 L4→L3→L2→L1→L0)
  变量占位:
    {{TITLE}}  图标题
    {{FLOWS}}  流量定义, 每行形如 `源,目标,权重`
-->

---
template_version: 2
---

<div style="background:#ffffff;border:1px solid #eef0f2;border-radius:16px;padding:24px;margin:8px 0;box-shadow:0 10px 15px -3px rgba(0,0,0,0.1);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#1a202c;">
<h3 style="margin:0 0 12px 0;font-size:1.125rem;font-weight:700;border-left:4px solid #3182ce;padding-left:8px;">{{TITLE}}</h3>

```mermaid
sankey-beta

{{FLOWS}}
%% 示例 (L4 → L0 固化流):
%% L4-流水账,L3-情节,120
%% L3-情节,L2-语义,45
%% L2-语义,L1-长期,12
%% L1-长期,L0-核心,2
```

</div>

<!-- TEMPLATE_END -->
