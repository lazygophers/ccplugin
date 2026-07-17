// SKEIN webapp PRD 章节解析: 按 `## ` 标题分割 prd.md, 抽 {标题: 内容} map。
// 供 task 详情页平铺展示「目标」「验收标准」等章节 (内容保持 markdown 原文, 由调用方 md.render)。
// 纯函数, 无副作用, 无 DOM 依赖。

// 按 `^## ` (行首两个#) 分割; 不识别 `###` 等更深层级 (归入上一节内容)。
// 标题行去除前导 `##` 与空白后作为 key; `# 标题` (h1) 与无标题前言被丢弃。
export function parsePrdSections(mdText) {
  const out = {};
  if (!mdText || typeof mdText !== "string") return out;
  let cur = null; // 当前章节标题 (string|null)
  const buf = {}; // 标题 → 行缓冲 []
  for (const line of mdText.split("\n")) {
    // ponytail: 简化匹配 — 只认行首恰好两个 # + 空格; ### 等不会被误判 (其行首是 ###)。
    const m = /^##[ \t]+(.*)$/.exec(line);
    if (m) {
      cur = m[1].trim();
      if (cur) buf[cur] = [];
    } else if (cur != null) {
      buf[cur].push(line);
    }
  }
  for (const k of Object.keys(buf)) out[k] = buf[k].join("\n").replace(/\n+$/, "");
  return out;
}

// 标题匹配容错: 「目标」「验收标准」「验收」「Acceptance Criteria」等变体。
// 返回传入 map 中第一个标题 startsWith / 包含任一 alias 的章节内容; 找不到 → ""。
export function findSection(sections, ...aliases) {
  if (!sections) return "";
  const keys = Object.keys(sections);
  for (const alias of aliases) {
    const hit = keys.find((k) => k === alias || k.startsWith(alias) || k.indexOf(alias) >= 0);
    if (hit) return sections[hit];
  }
  return "";
}

// ── 自检: node prd-parse.js 直接跑 (非 import 时) ──
// ponytail: 最小可运行校验, 断言关键路径; 无框架。
// 守卫须先判 process 存在 (浏览器无 process, 顶层访问即抛 ReferenceError)。
if (typeof process !== "undefined" && import.meta.url === `file://${process.argv[1]}`) {
  const sample = `# PRD — demo

## 目标
做一件事。

## 边界
- 含 A
- 不含 B

## 验收标准
- [ ] 项1
- [ ] 项2
`;
  const s = parsePrdSections(sample);
  console.log(JSON.stringify(s, null, 2));
  const goal = findSection(s, "目标");
  const accept = findSection(s, "验收标准", "验收");
  console.assert(goal === "做一件事。", "目标 mismatch: %o", goal);
  console.assert(accept.includes("项1") && accept.includes("项2"), "验收 mismatch: %o", accept);
  console.assert(Object.keys(parsePrdSections("")).length === 0, "空输入应返回 {}");
  console.assert(Object.keys(parsePrdSections("无标题纯文本")).length === 0, "无 ## 应返回 {}");
  console.assert(findSection(s, "不存在") === "", "缺失章节应返回空串");
  console.log("OK prd-parse self-check");
}
