# 演示排版模式

HTML 即放映物。幻灯片、PDF 报告、微信图文都是 HTML 的不同导出形态。

## 幻灯片

每页 1920×1080，键盘翻页，可全屏当 PPT。

### 骨架

```html
<div class="deck">
  <section class="slide">...</section>  <!-- 每页一个 section -->
  <section class="slide">...</section>
</div>
<script>
  // ← / → / Space 翻页，F 全屏
  let i=0; const slides=document.querySelectorAll('.slide');
  document.addEventListener('keydown',e=>{
    if(e.key==='ArrowRight'||e.key===' ')i=Math.min(i+1,slides.length-1);
    if(e.key==='ArrowLeft')i=Math.max(i-1,0);
    slides.forEach((s,n)=>s.hidden=n!==i);
  });
</script>
```

### 页型

| 页型 | 用途 |
|------|------|
| 标题页 | 破题、定调、大留白 |
| 观点页 | 一句核心论点 + 支撑 |
| 概览墙 | 多卡格栅，信息密度高的综合页 |
| 数据页 | 一张图表 + 结论先行 |
| 引述页 | 大字引用，节奏调剂 |
| 对比页 | 左右 / 前后对比 |
| 收尾页 | CTA / 总结 / 联系方式 |

### 要点

- 一页一观点，禁塞满
- 字号阶梯：标题 72+ / 正文 32+ / 标注 20+
- 结论先行：每页顶部一句话结论，下面是支撑
- 数据页：先放结论文字，再放图（观众先读结论再看证据）
- 全屏背景大图 / 大色块 > 小图碎排

### 概览墙模板

信息密度高的页用多卡格栅：

```css
.slide.wall { display:grid; grid-template-columns:repeat(3,1fr); gap:32px; }
.wall .card { background:var(--card); padding:24px; border-radius:12px; }
```

## PDF 报告

HTML + print CSS，浏览器打印或 Puppeteer 导 PDF。

```css
@page { size: A4; margin: 20mm; }
.page-break { break-after: page; }
@media print {
  .no-print { display:none; }
  body { font-size: 12pt; }
}
```

要点：
- `@page` 控纸张大小与边距
- `break-after: page` 手动分页（避免标题孤悬页底）
- 打印字号用 pt（pt 是绝对单位，屏幕用 rem / px）
- 背景色需 `-webkit-print-color-adjust: exact` 才能保留
- 表格 / 图表避免跨页断开（`break-inside: avoid`）

导出：Puppeteer `page.pdf({format:'A4', printBackground:true})`。

## 微信图文

微信限制：外链不能跳、样式需内联、部分 CSS 不支持。

要点：
- 样式全内联（`style="..."`），微信会剥 `<style>` 与 class
- 外链转底部引用编号（正文标 `[1]`，尾部列链接）
- 图片用微信图床或 base64（外站图可能防盗链）
- 字号、行高、段距比 Web 放宽（手机阅读）
- 代码块微信渲染差，转图片或简化

## 导出

详见 [export-pipeline.md](export-pipeline.md)：HTML 幻灯片无需导出（本身就是放映物），PDF 走 print / Puppeteer，微信图文走内联 HTML 粘贴。
