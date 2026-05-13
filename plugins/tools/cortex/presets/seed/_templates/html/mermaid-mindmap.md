<!-- cortex-template-version: 2 -->
<!--
  mermaid-mindmap.md — Grok Live Artifacts 风思维导图
  变量占位:
    {{TITLE}}   图标题
    {{ROOT}}    根节点文本
    {{BRANCHES}} 分支节点 (缩进表示层级)
-->

---
lint-skip: true
template_version: 2
---

<div style="background:#ffffff;border:1px solid #eef0f2;border-radius:16px;padding:24px;margin:8px 0;box-shadow:0 10px 15px -3px rgba(0,0,0,0.1);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#1a202c;">
<h3 style="margin:0 0 12px 0;font-size:1.125rem;font-weight:700;border-left:4px solid #3182ce;padding-left:8px;">{{TITLE}}</h3>

```mermaid
mindmap
  root(({{ROOT}}))
    {{BRANCHES}}
    %% 示例:
    %% 知识库
    %%   项目
    %%   来源
    %%     代码仓库
    %%     网页
    %% 记忆
    %%   L0-核心
    %%   L1-长期
```

</div>

<!-- TEMPLATE_END -->
