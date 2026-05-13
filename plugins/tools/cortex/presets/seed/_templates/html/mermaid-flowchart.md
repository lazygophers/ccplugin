<!-- cortex-template-version: 2 -->
<!--
  mermaid-flowchart.md — Grok Live Artifacts 风 flowchart 模板
  变量占位:
    {{TITLE}}  图标题
    {{NODES}}  节点定义 (由 cortex-html 注入, 形如 A[开始] --> B{判断})
-->

---
template_version: 2
---

<div style="background:#ffffff;border:1px solid #eef0f2;border-radius:16px;padding:24px;margin:8px 0;box-shadow:0 10px 15px -3px rgba(0,0,0,0.1);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#1a202c;">
<h3 style="margin:0 0 12px 0;font-size:1.125rem;font-weight:700;border-left:4px solid #3182ce;padding-left:8px;">{{TITLE}}</h3>

```mermaid
flowchart TD
    {{NODES}}
    %% 示例:
    %% Start([开始]) --> Check{条件?}
    %% Check -->|是| DoA[操作 A]
    %% Check -->|否| DoB[操作 B]
    %% DoA --> End([结束])
    %% DoB --> End
```

</div>

<!-- TEMPLATE_END -->
