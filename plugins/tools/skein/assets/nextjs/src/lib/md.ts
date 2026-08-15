// 极简 GFM markdown → HTML (从旧 md.js 移植, 无第三方依赖)

export function esc(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

// 链接/图片 URL 协议白名单: http(s)://、绝对路径 /、锚点 #、相对路径 (无 scheme)。
// javascript: / data: 等一律拒绝 (判定在 esc 之后、正则替换前, URL 已实体化)。
function okUrl(u: string): boolean {
  if (/^(https?:\/\/|\/|#|\.\.\/|\.\/)/i.test(u)) return true;
  return !/^[a-z][a-z0-9+.-]*:/i.test(u); // 无 scheme = 相对路径
}

function inline(s: string): string {
  const codes: string[] = [];
  s = s.replace(/`([^`]+)`/g, (_, c) => { codes.push(`<code>${esc(c)}</code>`); return ` §${codes.length - 1}§ `; });
  s = esc(s);
  s = s.replace(/!\[([^\]]*)\]\(([^)\s]+)\)/g,
    (m, alt, url) => okUrl(url) ? `<img alt="${alt}" src="${url}">` : m);
  s = s.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g,
    (m, text, url) => okUrl(url) ? `<a href="${url}">${text}</a>` : m);
  s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>").replace(/__([^_]+)__/g, "<strong>$1</strong>");
  s = s.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  s = s.replace(/~~([^~]+)~~/g, "<del>$1</del>");
  return s.replace(/§(\d+)§/g, (_, i) => codes[+i]);
}

function listBlock(lines: string[]): string {
  const ol = /^\s*\d+[.)]\s/.test(lines[0]);
  const items: string[] = [];
  let cur: string | null = null;
  for (const l of lines) {
    const m = l.match(/^\s*([-*+]|\d+[.)])\s+(.*)$/);
    if (m) { if (cur !== null) items.push(cur); cur = m[2]; }
    else if (cur !== null) cur += " " + l.trim();
  }
  if (cur !== null) items.push(cur);
  const tag = ol ? "ol" : "ul";
  return `<${tag}>${items.map(i => `<li>${inline(i)}</li>`).join("")}</${tag}>`;
}

export function renderMd(src: string): string {
  if (!src) return "";
  const lines = esc(src).replace(/&amp;/g, "&").split("\n");
  const out: string[] = [];
  let i = 0;
  let listLines: string[] = [];

  function flushList() {
    if (listLines.length) { out.push(listBlock(listLines)); listLines = []; }
  }

  while (i < lines.length) {
    const l = lines[i];
    // Task list item
    const taskM = l.match(/^\s*[-*+]\s+\[([ x])\]\s+(.*)$/);
    if (taskM) {
      flushList();
      out.push(`<li class="task"><input type="checkbox" ${taskM[1] === "x" ? "checked" : ""} disabled> ${inline(taskM[2])}</li>`);
      i++; continue;
    }
    // Heading
    const hM = l.match(/^(#{1,6})\s+(.*)$/);
    if (hM) { flushList(); out.push(`<h${hM[1].length}>${inline(hM[2])}</h${hM[1].length}>`); i++; continue; }
    // Code block
    if (/^```/.test(l)) {
      flushList();
      const code: string[] = [];
      i++;
      while (i < lines.length && !/^```/.test(lines[i])) { code.push(lines[i]); i++; }
      i++;
      out.push(`<pre><code>${esc(code.join("\n"))}</code></pre>`);
      continue;
    }
    // Blockquote
    if (/^>\s?/.test(l)) { flushList(); out.push(`<blockquote>${inline(l.replace(/^>\s?/, ""))}</blockquote>`); i++; continue; }
    // HR
    if (/^---+$/.test(l.trim())) { flushList(); out.push("<hr>"); i++; continue; }
    // List item
    if (/^\s*([-*+]|\d+[.)])\s+/.test(l)) { listLines.push(l); i++; continue; }
    // Table
    if (l.includes("|") && i + 1 < lines.length && /^\s*\|?[\s:|-]+\|?\s*$/.test(lines[i + 1])) {
      flushList();
      const hdr = l.split("|").map(c => c.trim()).filter(Boolean);
      i += 2;
      const rows: string[][] = [];
      while (i < lines.length && lines[i].includes("|")) {
        rows.push(lines[i].split("|").map(c => c.trim()).filter(Boolean));
        i++;
      }
      out.push(`<table><thead><tr>${hdr.map(h => `<th>${inline(h)}</th>`).join("")}</tr></thead><tbody>${rows.map(r => `<tr>${r.map(c => `<td>${inline(c)}</td>`).join("")}</tr>`).join("")}</tbody></table>`);
      continue;
    }
    // Empty line
    if (!l.trim()) { flushList(); i++; continue; }
    // Paragraph
    flushList();
    out.push(`<p>${inline(l)}</p>`);
    i++;
  }
  flushList();
  return out.join("\n");
}
