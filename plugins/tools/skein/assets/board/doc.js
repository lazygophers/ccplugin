// 规划文档浮层: 点 .doc-link → fetch task/<id>/<f>.md → 离线渲染 markdown-lite → 弹层显示。
// 仅 serve (http) 下可用 (静态托管 .skein/); file:// 下 fetch 抛错 → 显示提示。
(function () {
  var modal = document.getElementById("doc-modal");
  if (!modal) return;
  var titleEl = modal.querySelector(".doc-title");
  var bodyEl = modal.querySelector(".doc-body");

  function esc(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function inline(s) {
    return esc(s)
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>")
      .replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, function (m, txt, url) {
        // 仅放行 http/https/相对路径/锚点; 挡 javascript: 等危险 scheme
        return /^(https?:\/\/|\/|\.|#)/.test(url)
          ? '<a href="' + url + '" target="_blank" rel="noopener">' + txt + "</a>"
          : txt;
      });
  }
  // markdown-lite: 标题/列表/任务勾选/代码块/引用/分隔线/段落 — 够看规划文档, 不追求全 CommonMark
  function md(src) {
    var lines = src.replace(/\r\n?/g, "\n").split("\n"), out = [], list = null, code = false, buf = [];
    function closeList() { if (list) { out.push("</" + list + ">"); list = null; } }
    for (var i = 0; i < lines.length; i++) {
      var ln = lines[i];
      if (/^```/.test(ln)) {
        if (code) { out.push("<pre><code>" + esc(buf.join("\n")) + "</code></pre>"); buf = []; code = false; }
        else { closeList(); code = true; }
        continue;
      }
      if (code) { buf.push(ln); continue; }
      var h = ln.match(/^(#{1,4})\s+(.*)$/);
      if (h) { closeList(); var n = h[1].length; out.push("<h" + n + ">" + inline(h[2]) + "</h" + n + ">"); continue; }
      var task = ln.match(/^\s*[-*]\s+\[([ xX])\]\s+(.*)$/);
      if (task) {
        if (list !== "ul") { closeList(); out.push('<ul class="task">'); list = "ul"; }
        var done = task[1] !== " ";
        out.push('<li class="' + (done ? "done" : "todo") + '"><span class="chk">' + (done ? "☑" : "☐") + "</span> " + inline(task[2]) + "</li>");
        continue;
      }
      if (/^\s*[-*]\s+/.test(ln)) {
        if (list !== "ul") { closeList(); out.push("<ul>"); list = "ul"; }
        out.push("<li>" + inline(ln.replace(/^\s*[-*]\s+/, "")) + "</li>"); continue;
      }
      if (/^\s*\d+\.\s+/.test(ln)) {
        if (list !== "ol") { closeList(); out.push("<ol>"); list = "ol"; }
        out.push("<li>" + inline(ln.replace(/^\s*\d+\.\s+/, "")) + "</li>"); continue;
      }
      if (/^>\s?/.test(ln)) { closeList(); out.push("<blockquote>" + inline(ln.replace(/^>\s?/, "")) + "</blockquote>"); continue; }
      if (/^(-{3,}|\*{3,})\s*$/.test(ln)) { closeList(); out.push("<hr>"); continue; }
      if (/^\s*$/.test(ln)) { closeList(); continue; }
      closeList(); out.push("<p>" + inline(ln) + "</p>");
    }
    if (code) out.push("<pre><code>" + esc(buf.join("\n")) + "</code></pre>");
    closeList();
    return out.join("");
  }

  function open(path, title) {
    titleEl.textContent = title;
    bodyEl.innerHTML = '<p class="doc-loading">载入中…</p>';
    modal.hidden = false;
    fetch(path, { cache: "no-store" }).then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.text();
    }).then(function (t) {
      bodyEl.innerHTML = md(t);
    }).catch(function (e) {
      bodyEl.innerHTML = '<p class="doc-err">读取失败: ' + esc(path) + " (" + esc(String(e.message)) +
        ")<br>需经 serve (http) 访问, file:// 直接打开无法读取文件。</p>";
    });
  }
  function close() { modal.hidden = true; bodyEl.innerHTML = ""; }

  document.addEventListener("click", function (e) {
    var b = e.target.closest(".doc-link");
    if (b) { open(b.getAttribute("data-doc"), b.getAttribute("data-title") || ""); return; }
    if (e.target.closest(".doc-close") || e.target.classList.contains("doc-backdrop")) close();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !modal.hidden) close();
  });
})();
