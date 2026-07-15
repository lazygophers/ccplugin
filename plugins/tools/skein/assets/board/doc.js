// 规划文档浮层: 点 .doc-link → fetch task/<id>/<f>.md → marked 渲染 → 弹层显示。
// 仅 serve (http) 下可用 (静态托管 .skein/); file:// 下 fetch 抛错 → 显示提示。
(function () {
  var modal = document.getElementById("doc-modal");
  if (!modal) return;
  var titleEl = modal.querySelector(".doc-title");
  var bodyEl = modal.querySelector(".doc-body");
  var copyBtn = modal.querySelector(".doc-copy");
  var lastSrc = "";  // 当前浮层 md 原文, 供复制按钮取用

  // marked 配置: GFM (表格/删除线/任务列表) + 换行即 <br>
  if (window.marked && marked.setOptions) {
    marked.setOptions({ gfm: true, breaks: false });
  }
  function render(src) {
    if (window.marked) {
      return marked.parse ? marked.parse(src) : marked(src);
    }
    // 兜底: marked 未加载则纯文本转义 (不该发生)
    return "<pre>" + src.replace(/&/g, "&amp;").replace(/</g, "&lt;") + "</pre>";
  }
  // 轻量 sanitize: 本地可信文件, 只清 script / on* 事件 / javascript: href — 防意外脚本
  function sanitize(root) {
    root.querySelectorAll("script").forEach(function (n) { n.remove(); });
    root.querySelectorAll("*").forEach(function (el) {
      for (var i = el.attributes.length - 1; i >= 0; i--) {
        var a = el.attributes[i];
        if (/^on/i.test(a.name)) el.removeAttribute(a.name);
        else if ((a.name === "href" || a.name === "src") && /^\s*javascript:/i.test(a.value)) el.removeAttribute(a.name);
      }
    });
    root.querySelectorAll("a[href]").forEach(function (a) {
      a.setAttribute("target", "_blank");
      a.setAttribute("rel", "noopener");
    });
  }

  function open(path, title) {
    titleEl.textContent = title;
    lastSrc = "";
    if (copyBtn) copyBtn.disabled = true;
    bodyEl.innerHTML = '<p class="doc-loading">载入中…</p>';
    modal.hidden = false;
    fetch(path, { cache: "no-store" }).then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.text();
    }).then(function (t) {
      lastSrc = t;
      if (copyBtn) copyBtn.disabled = false;
      bodyEl.innerHTML = render(t);
      sanitize(bodyEl);
    }).catch(function (e) {
      bodyEl.textContent = "";
      var p = document.createElement("p");
      p.className = "doc-err";
      p.textContent = "读取失败: " + path + " (" + e.message + ") — 需经 serve (http) 访问, file:// 直接打开无法读取文件。";
      bodyEl.appendChild(p);
    });
  }
  function close() { modal.hidden = true; bodyEl.innerHTML = ""; lastSrc = ""; }

  // 一键复制 md 原文到剪贴板; navigator.clipboard 不可用 (非 https / file://) 时回落 execCommand
  function copySrc() {
    if (!lastSrc || !copyBtn) return;
    var flash = function (ok) {
      copyBtn.textContent = ok ? "✓ 已复制" : "✕ 复制失败";
      setTimeout(function () { copyBtn.textContent = "⧉ 复制"; }, 1400);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(lastSrc).then(function () { flash(true); }, function () { flash(fallbackCopy(lastSrc)); });
      return;
    }
    flash(fallbackCopy(lastSrc));
  }
  function fallbackCopy(text) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    return ok;
  }

  document.addEventListener("click", function (e) {
    var b = e.target.closest(".doc-link");
    if (b) { open(b.getAttribute("data-doc"), b.getAttribute("data-title") || ""); return; }
    if (e.target.closest(".doc-copy")) { copySrc(); return; }
    if (e.target.closest(".doc-close") || e.target.classList.contains("doc-backdrop")) close();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !modal.hidden) close();
  });
})();
