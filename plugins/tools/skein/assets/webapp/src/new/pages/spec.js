// SKEIN webapp · spec 规范页 (htm + 原生 DOM 重写版, 替 petite-vue)。
// 三栏: (1) 导航树 (layer × category) (2) 文件列表 (筛选) (3) 详情 (预览 ↔ 编辑)。
// 详情: 预览 (md body 渲染) ↔ 编辑 (metadata frontmatter 表单 + 增强 textarea)。
// 保存必经 diff 确认 (全屏, 行级增删高亮), 确认才 api.specSave, 取消不写。
// onLive 订阅 spec-changed 软刷当前文件 (无 task 订阅); 编辑态保守不软刷 (草稿不丢)。
//
// render(mount, params, ctx) 契约: core `[arch] SPA page 模块统一契约`
//   ctx = { api, md, h, onLive, navigate }
//   onLive(cb) 订阅 WS spec-changed; router 切页自动退订。

// ponytail: 朴素 LCS 行 diff, O(n*m) 内存 — spec 文件都不大, 够用; 需处理超大文件再换 Myers。
function diffLines(a, b) {
  const A = (a || "").split("\n"), B = (b || "").split("\n");
  const n = A.length, m = B.length;
  const dp = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
  for (let i = n - 1; i >= 0; i--)
    for (let j = m - 1; j >= 0; j--)
      dp[i][j] = A[i] === B[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
  const out = []; let i = 0, j = 0;
  while (i < n && j < m) {
    if (A[i] === B[j]) { out.push({ t: "ctx", s: A[i] }); i++; j++; }
    else if (dp[i + 1][j] >= dp[i][j + 1]) { out.push({ t: "del", s: A[i] }); i++; }
    else { out.push({ t: "add", s: B[j] }); j++; }
  }
  while (i < n) out.push({ t: "del", s: A[i++] });
  while (j < m) out.push({ t: "add", s: B[j++] });
  return out;
}

// ponytail: spec frontmatter 都是 flat YAML (key: val / key: [a,b,c]), 不引 yaml 库。
function parseFM(src) {
  const m = (src || "").match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/);
  if (!m) return { meta: {}, body: src || "" };
  const meta = {};
  m[1].split("\n").forEach((line) => {
    const i = line.indexOf(":");
    if (i < 0) return;
    const k = line.slice(0, i).trim(), v = line.slice(i + 1).trim();
    if (!k) return;
    if (v.startsWith("[") && v.endsWith("]")) meta[k] = v.slice(1, -1).split(",").map((s) => s.trim()).filter(Boolean);
    else meta[k] = v;
  });
  return { meta, body: m[2] };
}
function serializeFM(meta, body) {
  const lines = Object.entries(meta || {})
    .filter(([, v]) => v !== undefined && v !== null && v !== "")
    .map(([k, v]) => (Array.isArray(v) ? k + ": [" + v.join(", ") + "]" : k + ": " + v));
  return "---\n" + lines.join("\n") + "\n---\n" + (body || "");
}

const CATS = ["arch", "frontend", "ops", "style"];
const META_KEYS = ["title", "layer", "category", "keywords", "source", "authored-by", "created"];

const SPEC_CSS = `
.spec-3col{display:grid;grid-template-columns:224px 288px 1fr;gap:1rem;height:calc(100vh - 120px)}
.spec-3col>aside,.spec-3col>section{overflow:auto}
.spec-meta-form{display:grid;grid-template-columns:1fr 1fr;gap:.5rem .75rem;padding:.75rem;border:1px solid var(--line);border-radius:.5rem;margin-bottom:.75rem}
.spec-meta-form .full{grid-column:1/-1}
.spec-editor-wrap{position:relative}
.spec-gutter{position:absolute;left:0;top:0;width:2.5rem;height:100%;overflow:hidden;font-family:var(--font-mono,monospace);font-size:13px;line-height:1.5rem;color:var(--muted);text-align:right;padding:.75rem .5rem 0 0;pointer-events:none;box-sizing:border-box;white-space:pre}
.spec-editor{padding-left:2.75rem;font-family:var(--font-mono,monospace);font-size:13px;line-height:1.5rem;tab-size:2;box-sizing:border-box}
.spec-kw-chip{display:inline-flex;align-items:center;gap:.25rem;padding:.1rem .4rem;border-radius:.25rem;background:var(--line);font-size:.75rem;cursor:pointer}
.md-body{font-size:14px;line-height:1.7;word-wrap:break-word}
.md-body>:first-child{margin-top:0}.md-body>:last-child{margin-bottom:0}
.md-body h1,.md-body h2,.md-body h3,.md-body h4{color:var(--head);font-weight:650;line-height:1.3;margin:1.2em 0 .5em}
.md-body h1{font-size:1.5em;padding-bottom:.25em;border-bottom:1px solid var(--line)}
.md-body h2{font-size:1.25em;padding-bottom:.2em;border-bottom:1px solid var(--line)}
.md-body p{margin:.6em 0}
.md-body ul,.md-body ol{margin:.6em 0;padding-left:1.6em}
.md-body li::marker{color:var(--muted)}
.md-body code{background:color-mix(in srgb,var(--muted) 18%,transparent);border-radius:5px;padding:.12em .35em;font-size:.88em;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.md-body pre{background:color-mix(in srgb,var(--fg) 6%,transparent);border:1px solid var(--line);border-radius:9px;padding:12px 14px;overflow-x:auto;margin:.8em 0;line-height:1.5}
.md-body pre code{background:none;padding:0;font-size:.86em}
.md-body blockquote{border-left:3px solid var(--accent);margin:.8em 0;padding:.2em 0 .2em 14px;color:var(--muted)}
.md-body hr{border:none;border-top:2px solid var(--line);margin:1.2em 0}
.md-body a{color:var(--accent);text-decoration:none}
.md-body a:hover{text-decoration:underline}
.md-body strong{color:var(--head);font-weight:650}
.md-body table{border-collapse:collapse;margin:.8em 0;width:auto;max-width:100%;display:block;overflow-x:auto;font-size:.92em}
.md-body th,.md-body td{border:1px solid var(--brd);padding:6px 11px;text-align:left}
.md-body th{background:color-mix(in srgb,var(--muted) 8%,transparent);color:var(--head);font-weight:600}
.spec-skel{padding:64px 24px;text-align:center;color:var(--muted)}
.spec-skel .spin{font-size:28px;color:var(--accent)}
`;

// 后端 tree: {core:{类目:[文件]}, recall:{类目:[文件]}} → 规整为可迭代 layers
function toLayers(tree) {
  const meta = [["core", "CORE · 常驻硬规"], ["recall", "RECALL · 按需召回"]];
  return meta.map(([key, label]) => ({
    key, label,
    cats: Object.keys(tree[key] || {}).sort().map((name) => ({ name, files: (tree[key][name] || []).slice() })),
  })).filter((l) => l.cats.length);
}

function esc(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

// ── 主 render 入口 ──
export async function render(mount, params, ctx) {
  const { api, md, h, onLive } = ctx;

  const styleEl = h("style", { html: SPEC_CSS });
  const skel = h("div", { class: "spec-skel" },
    h("div", { class: "spin", "aria-hidden": "true" }, "◐"),
    h("div", { class: "mt-2 text-sm" }, "加载 spec 树…")
  );
  mount.append(styleEl, skel);

  // 拉树
  let tree = {}, loadErr = "";
  try { tree = await api.spec(); } catch (e) { loadErr = (e && e.message) || String(e); }
  if (skel.parentNode) skel.remove();

  const layers = toLayers(tree || {});
  // 文件级索引: path → {path, title, kw, layer, category}, 供中栏搜索过滤与展示
  const index = {};
  layers.forEach((l) => l.cats.forEach((c) => c.files.forEach((f) => {
    const p = l.key + "/" + c.name + "/" + f;
    index[p] = { path: p, layer: l.key, category: c.name, title: f, kw: [] };
  })));

  // 页内状态 (非响应式, 手动重渲染)
  const state = {
    layers,
    index,
    loadErr,
    empty: !loadErr && layers.length === 0,
    sel: { layer: "", category: "" },    // 中栏当前筛选
    q: "",                                // 中栏搜索
    current: { path: "", content: "", layer: "", category: "" },
    mode: "view",                         // view | edit
    bodyDraft: "",
    meta: {},
    kwDraft: "",
    fileErr: "",
    showDiff: false,
    saving: false,
    toast: "",
    toastErr: false,
    toastTimer: null,
  };

  const coreCount = (layers.find((l) => l.key === "core") || { cats: [] }).cats.reduce((a, c) => a + c.files.length, 0);
  const recallCount = (layers.find((l) => l.key === "recall") || { cats: [] }).cats.reduce((a, c) => a + c.files.length, 0);

  // ponytail: 错误态 — 直接 innerHTML 注入错误框, 不进入三栏渲染。
  if (loadErr) {
    mount.append(h("div", { class: "px-7" },
      h("div", { class: "antd-card p-10 text-center text-muted" },
        h("div", { class: "empty-ico", style: { color: "var(--st-failed)" }, html: '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>' }),
        h("div", { class: "text-sm", style: { color: "var(--st-failed)" } }, loadErr)
      )
    ));
    return;
  }
  if (state.empty) {
    mount.append(h("div", { class: "px-7" },
      h("div", { class: "antd-card p-16 text-center text-muted" },
        h("div", { class: "empty-ico", html: '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>' }),
        h("div", { class: "text-sm" }, "暂无 spec"),
        h("div", { class: "text-xs opacity-60 mt-1" }, ".skein/spec/ 为空")
      )
    ));
    return;
  }

  // 三栏容器 + diff 全屏覆盖 + toast
  const nav = h("aside", { class: "spec-nav antd-card p-3" });
  const list = h("section", { class: "spec-list antd-card p-3" });
  const detail = h("section", { class: "spec-detail antd-card p-4" });
  const diffOverlay = h("div", { class: "fixed inset-0 flex flex-col", style: { background: "var(--bg)", zIndex: "2000", display: "none" } });
  const toastEl = h("div", { class: "fixed bottom-6 left-1/2 -translate-x-1/2 z-[2100] px-4 py-2 rounded text-sm", style: { display: "none" } });
  const layout = h("div", { class: "spec-3col px-7" }, nav, list, detail);
  mount.append(layout, diffOverlay, toastEl);

  // ── 渲染函数 (基于 state 手动重渲) ──

  function renderNav() {
    nav.innerHTML =
      '<div class="text-xs uppercase tracking-wide opacity-60 mb-2">Spec 记忆</div>' +
      '<div class="text-[11px] opacity-60 mb-2">core ' + coreCount + " / recall " + recallCount + "</div>" +
      layers.map((l) =>
        '<div class="mt-1">' +
        '<div class="mt-2 mb-1 text-[11px] font-semibold" style="color:var(--head)">' + esc(l.label) + "</div>" +
        l.cats.map((c) => {
          const on = state.sel.layer === l.key && state.sel.category === c.name;
          return '<button type="button" class="w-full text-left px-2 py-1 text-sm rounded flex items-center gap-2" ' +
            'data-pick-layer="' + esc(l.key) + '" data-pick-cat="' + esc(c.name) + '" ' +
            'style="' + (on ? "background:var(--line);color:var(--accent);border-left:2px solid var(--accent);font-weight:500" : "border-left:2px solid transparent") + '">' +
            '<span class="truncate flex-1">' + esc(c.name) + "</span>" +
            '<span class="text-[10px] opacity-50">' + c.files.length + "</span>" +
            "</button>";
        }).join("") +
        "</div>"
      ).join("");
  }

  function renderList() {
    // 当前 layer+category 下文件 (无 sel → 空), 按 q 模糊过滤 title/keywords/path
    let all = [];
    if (state.sel.layer) {
      const layer = state.layers.find((l) => l.key === state.sel.layer);
      const cat = layer && layer.cats.find((c) => c.name === state.sel.category);
      if (cat) {
        all = cat.files.map((f) => state.index[state.sel.layer + "/" + state.sel.category + "/" + f]).filter(Boolean);
      }
    }
    const q = (state.q || "").trim().toLowerCase();
    if (q) {
      all = all.filter((f) => {
        const t = ((f && f.title) || "").toLowerCase();
        const k = ((f && f.kw) || []).join(" ").toLowerCase();
        const p = (f && f.path || "").toLowerCase();
        return t.indexOf(q) >= 0 || k.indexOf(q) >= 0 || p.indexOf(q) >= 0;
      });
    }

    let body;
    if (!all.length) {
      body = '<div class="text-sm text-muted py-8 text-center">' +
        (state.sel.layer ? (state.q ? "无匹配" : "选左侧类目") : "选左侧类目") + "</div>";
    } else {
      body = all.map((f) => {
        const on = state.current.path === f.path;
        return '<div class="px-2 py-1.5 rounded cursor-pointer text-sm" data-select="' + esc(f.path) + '" ' +
          'style="' + (on ? "background:var(--line);color:var(--accent)" : "") + '">' +
          '<div class="font-medium truncate">' + esc(f.title || f.path.split("/").pop()) + "</div>" +
          '<div class="text-[11px] opacity-60 truncate">' + esc(f.path) + "</div>" +
          (f.kw && f.kw.length
            ? '<div class="mt-0.5 flex flex-wrap gap-1">' + f.kw.slice(0, 4).map((k) => '<span class="spec-kw-chip">' + esc(k) + "</span>").join("") + "</div>"
            : "") +
          "</div>";
      }).join("");
    }

    list.innerHTML =
      '<input type="text" id="spec-q" placeholder="搜索 title / keywords / 文件名" value="' + esc(state.q) + '" ' +
      'class="w-full mb-2 px-2 py-1 text-sm rounded" style="background:var(--bg);color:var(--fg);border:1px solid var(--brd)">' +
      body;
  }

  function renderDetail() {
    if (state.fileErr) {
      detail.innerHTML = '<div class="text-sm" style="color:var(--st-failed)">' + esc(state.fileErr) + "</div>";
      return;
    }
    if (!state.current.path) {
      detail.innerHTML = '<div class="text-muted text-center py-24">选择文件查看</div>';
      return;
    }

    const parts = (state.current.path || "").split("/");
    const crumb = [state.current.layer, state.current.category, parts[parts.length - 1]].filter(Boolean).join(" / ");

    let body;
    if (state.mode === "view") {
      const fm = parseFM(state.current.content);
      body = '<div class="md-body" id="spec-preview">' + md.renderSafe(fm.body) + "</div>";
    } else {
      // 编辑模式: metadata 表单 + 正文 textarea
      const gutterN = (state.bodyDraft || "").split("\n").length;
      let gutter = "";
      for (let i = 1; i <= gutterN; i++) gutter += i + "\n";

      body =
        '<div class="spec-meta-form">' +
        renderMetaField("title", "title", "text", state.meta.title, false) +
        renderMetaSelect("layer", "layer", [{ v: "core", l: "core" }, { v: "recall", l: "recall" }], state.meta.layer) +
        renderMetaSelect("category", "category", CATS.map((c) => ({ v: c, l: c })), state.meta.category) +
        renderMetaField("source", "source", "text", state.meta.source, false) +
        renderMetaField("authored-by", "authored-by", "text", state.meta["authored-by"], false) +
        // created: datetime-local
        '<label class="flex flex-col gap-1 text-xs"><span class="opacity-60">created (unix ts)</span>' +
        '<input type="datetime-local" step="1" id="spec-meta-created" class="field" value="' + esc(createdLocal()) + '"></label>' +
        // keywords
        '<div class="full flex flex-col gap-1 text-xs"><span class="opacity-60">keywords (逗号/回车分隔, 退格删尾)</span>' +
        '<div class="flex flex-wrap items-center gap-1 p-1 rounded" style="background:var(--bg);border:1px solid var(--brd);min-height:2rem">' +
        (state.meta.keywords || []).map((k, i) =>
          '<span class="spec-kw-chip" data-kw-remove="' + i + '" title="删 ' + esc(k) + '">' + esc(k) + " ✕</span>"
        ).join("") +
        '<input type="text" id="spec-kw-draft" placeholder="回车或逗号添加" value="' + esc(state.kwDraft) + '" ' +
        'class="flex-1 min-w-[8rem] px-1 py-0.5 text-sm bg-transparent" style="color:var(--fg);border:none;outline:none">' +
        "</div></div>" +
        "</div>" +
        // 正文 textarea + 行号槽
        '<div class="spec-editor-wrap">' +
        '<div class="spec-gutter" id="spec-gutter">' + esc(gutter) + "</div>" +
        '<textarea id="spec-ta" class="spec-editor w-full h-[60vh] p-3 rounded" spellcheck="false" ' +
        'style="background:var(--bg);color:var(--fg);border:1px solid var(--brd);resize:vertical">' +
        esc(state.bodyDraft) + "</textarea>" +
        "</div>" +
        '<div class="flex justify-end gap-2 mt-2">' +
        '<button type="button" id="spec-cancel" class="px-3 py-1 text-sm rounded" style="border:1px solid var(--brd)">取消 (Esc)</button>' +
        '<button type="button" id="spec-save" class="px-3 py-1 text-sm rounded" ' + (dirty() ? "" : "disabled") +
        ' style="' + (dirty() ? "background:var(--accent);color:#fff" : "opacity:.5") + '">保存… (⌘S)</button>' +
        "</div>";
    }

    // 面包屑 + chip + view/edit toggle
    const toggleHtml =
      '<div class="flex items-center gap-1 mb-3 p-0.5 rounded" style="background:var(--line);width:fit-content">' +
      '<button type="button" id="spec-mode-view" class="px-3 py-1 text-xs rounded transition" ' +
      'style="' + (state.mode === "view" ? "background:var(--card);color:var(--accent);font-weight:600" : "color:var(--muted)") + '">预览</button>' +
      '<button type="button" id="spec-mode-edit" class="px-3 py-1 text-xs rounded transition" ' +
      'style="' + (state.mode === "edit" ? "background:var(--card);color:var(--accent);font-weight:600" : "color:var(--muted)") + '">编辑</button>' +
      "</div>";

    detail.innerHTML =
      '<div class="flex items-center gap-2 mb-2 text-sm">' +
      '<span class="opacity-60">' + esc(crumb) + "</span>" +
      '<span class="flex-1"></span>' +
      '<span class="spec-kw-chip" style="color:var(--accent)">' + esc(state.current.layer || "?") + "</span>" +
      '<span class="spec-kw-chip">' + esc(state.current.category || "?") + "</span>" +
      "</div>" +
      toggleHtml +
      body;

    // 绑定编辑模式事件 (仅 mode==edit)
    if (state.mode === "edit") bindEditEvents();
  }

  function renderMetaField(name, label, type, val, full) {
    return '<label class="' + (full ? "full " : "") + 'flex flex-col gap-1 text-xs">' +
      '<span class="opacity-60">' + esc(label) + "</span>" +
      '<input type="' + type + '" id="spec-meta-' + esc(name) + '" class="field" value="' + esc(val || "") + '" spellcheck="false"></label>';
  }
  function renderMetaSelect(name, label, options, val) {
    return '<label class="flex flex-col gap-1 text-xs"><span class="opacity-60">' + esc(label) + "</span>" +
      '<select id="spec-meta-' + esc(name) + '" class="field">' +
      options.map((o) => '<option value="' + esc(o.v) + '"' + (o.v === val ? " selected" : "") + ">" + esc(o.l) + "</option>").join("") +
      "</select></label>";
  }

  function createdLocal() {
    const ts = Number(state.meta.created);
    if (!ts) return "";
    const d = new Date(ts * 1000);
    const p = (n) => String(n).padStart(2, "0");
    return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate()) +
           "T" + p(d.getHours()) + ":" + p(d.getMinutes()) + ":" + p(d.getSeconds());
  }

  function draftSerialized() {
    return serializeFM(state.meta, state.bodyDraft);
  }
  function dirty() {
    return draftSerialized() !== state.current.content;
  }

  // ── 编辑模式事件绑定 ──
  function bindEditEvents() {
    // meta 字段双向绑定: input/change → state.meta
    META_KEYS.forEach((k) => {
      const el = detail.querySelector("#spec-meta-" + k);
      if (!el) return;
      if (k === "created") {
        el.addEventListener("input", (e) => {
          const v = e.target.value;
          state.meta.created = v ? Math.floor(new Date(v).getTime() / 1000) : "";
        });
      } else {
        el.addEventListener("input", (e) => {
          state.meta[k] = e.target.value;
        });
      }
    });

    // keywords 输入: 回车/逗号添加, 退格删尾
    const kwEl = detail.querySelector("#spec-kw-draft");
    if (kwEl) {
      kwEl.addEventListener("input", (e) => { state.kwDraft = e.target.value; });
      kwEl.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === ",") { e.preventDefault(); addKw(); }
        else if (e.key === "Backspace" && !state.kwDraft && (state.meta.keywords || []).length) {
          const cur = state.meta.keywords.slice();
          cur.pop();
          state.meta.keywords = cur;
          renderDetail();
          setTimeout(focusKwDraft, 0);
        }
      });
    }
    // keywords chip 点击删除
    detail.querySelectorAll("[data-kw-remove]").forEach((el) => {
      el.addEventListener("click", () => {
        const i = parseInt(el.getAttribute("data-kw-remove"), 10);
        const cur = (state.meta.keywords || []).slice();
        cur.splice(i, 1);
        state.meta.keywords = cur;
        renderDetail();
        setTimeout(focusKwDraft, 0);
      });
    });

    // textarea: 双向 bodyDraft + 行号同步滚动 + tab/saved/esc 快捷键
    const ta = detail.querySelector("#spec-ta");
    const gutter = detail.querySelector("#spec-gutter");
    if (ta) {
      ta.addEventListener("input", (e) => {
        state.bodyDraft = e.target.value;
        // 重算行号 (异步, 不阻塞输入)
        const n = (state.bodyDraft || "").split("\n").length;
        let g = ""; for (let i = 1; i <= n; i++) g += i + "\n";
        if (gutter) gutter.textContent = g;
      });
      ta.addEventListener("scroll", () => {
        if (gutter) gutter.scrollTop = ta.scrollTop;
      });
      ta.addEventListener("keydown", (e) => {
        if (e.key === "Tab") {
          e.preventDefault();
          const s = ta.selectionStart, en = ta.selectionEnd;
          state.bodyDraft = state.bodyDraft.slice(0, s) + "  " + state.bodyDraft.slice(en);
          ta.value = state.bodyDraft;
          ta.selectionStart = ta.selectionEnd = s + 2;
          // 重算行号
          const n = state.bodyDraft.split("\n").length;
          let g = ""; for (let i = 1; i <= n; i++) g += i + "\n";
          if (gutter) gutter.textContent = g;
        } else if ((e.metaKey || e.ctrlKey) && e.key === "s") {
          e.preventDefault();
          reviewSave();
        } else if (e.key === "Escape") {
          e.preventDefault();
          cancelEdit();
        }
      });
    }

    // 取消 / 保存按钮
    const cancelBtn = detail.querySelector("#spec-cancel");
    if (cancelBtn) cancelBtn.addEventListener("click", cancelEdit);
    const saveBtn = detail.querySelector("#spec-save");
    if (saveBtn) saveBtn.addEventListener("click", reviewSave);

    // view/edit toggle (编辑模式内切回 view)
    const viewBtn = detail.querySelector("#spec-mode-view");
    if (viewBtn) viewBtn.addEventListener("click", () => { if (!state.showDiff) setMode("view"); });
    const editBtn = detail.querySelector("#spec-mode-edit");
    if (editBtn) editBtn.addEventListener("click", startEdit);
  }

  function focusKwDraft() {
    const el = detail.querySelector("#spec-kw-draft");
    if (el) el.focus();
  }

  function addKw() {
    const v = (state.kwDraft || "").replace(/,$/, "").trim();
    if (!v) return;
    const cur = Array.isArray(state.meta.keywords) ? state.meta.keywords.slice() : [];
    if (cur.indexOf(v) < 0) cur.push(v);
    state.meta.keywords = cur;
    state.kwDraft = "";
    renderDetail();
    setTimeout(focusKwDraft, 0);
  }

  // ── mode 切换 ──
  function setMode(m) {
    state.mode = m;
    if (m === "view") { state.bodyDraft = ""; state.meta = {}; state.kwDraft = ""; }
    renderDetail();
  }
  function startEdit() {
    const fm = parseFM(state.current.content);
    // 深拷贝 meta 防 v-model 直接改原对象引用; keywords 新数组触发响应式
    state.meta = META_KEYS.reduce((o, k) => {
      o[k] = Array.isArray(fm.meta[k]) ? fm.meta[k].slice() : (fm.meta[k] != null ? fm.meta[k] : (k === "keywords" ? [] : ""));
      return o;
    }, {});
    // 从路径回填 layer/category (无 frontmatter 也能给默认)
    if (!state.meta.layer) state.meta.layer = state.current.layer;
    if (!state.meta.category) state.meta.category = state.current.category;
    state.bodyDraft = fm.body;
    state.kwDraft = "";
    state.mode = "edit";
    renderDetail();
  }
  function cancelEdit() {
    if (state.showDiff) { state.showDiff = false; renderDiffOverlay(); return; }
    state.mode = "view"; state.bodyDraft = ""; state.meta = {}; state.kwDraft = "";
    renderDetail();
  }

  // ── diff 覆盖层 ──
  function renderDiffOverlay() {
    if (!state.showDiff) {
      diffOverlay.style.display = "none";
      diffOverlay.innerHTML = "";
      return;
    }
    const d = diffLines(state.current.content, draftSerialized());
    const addCount = d.filter((x) => x.t === "add").length;
    const delCount = d.filter((x) => x.t === "del").length;
    diffOverlay.innerHTML =
      '<div class="px-5 py-3 flex items-center gap-2" style="border-bottom:1px solid var(--line)">' +
      "<strong>确认保存改动</strong>" +
      '<code class="text-xs opacity-70">' + esc(state.current.path) + "</code>" +
      '<span class="flex-1"></span>' +
      '<span class="text-xs" style="color:var(--st-done)">+' + addCount + "</span>" +
      '<span class="text-xs" style="color:var(--st-failed)">-' + delCount + "</span>" +
      '<span class="opacity-60 text-xs ml-3">Esc 取消</span>' +
      "</div>" +
      '<div class="flex-1 overflow-auto font-mono text-[13px] leading-5">' +
      (d.length === 0
        ? '<div class="p-5 text-muted text-sm">无差异</div>'
        : d.map((x) =>
          '<div class="px-3 whitespace-pre-wrap break-words flex" ' +
          'style="' + (x.t === "add" ? "background:color-mix(in srgb,var(--st-done) 20%,transparent)"
                   : x.t === "del" ? "background:color-mix(in srgb,var(--st-failed) 20%,transparent)" : "") + '">' +
          '<span class="inline-block w-6 select-none opacity-50 shrink-0">' + (x.t === "add" ? "+" : x.t === "del" ? "-" : " ") + "</span>" +
          "<span>" + esc(x.s) + "</span>" +
          "</div>"
        ).join("")) +
      "</div>" +
      '<div class="px-5 py-3 flex justify-end gap-2" style="border-top:1px solid var(--line)">' +
      '<button type="button" id="spec-diff-cancel" class="px-3 py-1 text-sm rounded" style="border:1px solid var(--brd)">取消</button>' +
      '<button type="button" id="spec-diff-confirm" class="px-3 py-1 text-sm rounded" ' + (state.saving || !d.length ? "disabled" : "") +
      ' style="background:var(--accent);color:#fff">' + (state.saving ? "保存中…" : "确认落盘") + "</button>" +
      "</div>";
    diffOverlay.style.display = "flex";
    const cancelBtn = diffOverlay.querySelector("#spec-diff-cancel");
    if (cancelBtn) cancelBtn.addEventListener("click", () => { state.showDiff = false; renderDiffOverlay(); });
    const confirmBtn = diffOverlay.querySelector("#spec-diff-confirm");
    if (confirmBtn) confirmBtn.addEventListener("click", confirmSave);
  }

  function reviewSave() {
    if (state.mode !== "edit") return;
    if (dirty()) { state.showDiff = true; renderDiffOverlay(); }
    else flash("无改动", false);
  }

  async function confirmSave() {
    if (state.saving) return;
    state.saving = true;
    renderDiffOverlay();  // 更新按钮文案
    try {
      const draft = draftSerialized();
      await api.specSave(state.current.path, draft);
      state.current = Object.assign({}, state.current, { content: draft });
      // 同步索引展示
      if (state.index[state.current.path]) {
        state.index[state.current.path].title = (state.meta && state.meta.title) || state.current.path.split("/")[2] || "";
        state.index[state.current.path].kw = Array.isArray(state.meta.keywords) ? state.meta.keywords.slice() : [];
      }
      state.showDiff = false;
      state.mode = "view";
      renderDiffOverlay();
      renderList();  // title/kw 更新后刷新中栏
      renderDetail();
      flash("已保存 " + state.current.path, false);
    } catch (e) {
      state.showDiff = false;
      renderDiffOverlay();
      flash("保存失败: " + ((e && e.message) || e), true);
    } finally {
      state.saving = false;
    }
  }

  function flash(msg, isErr) {
    state.toast = msg;
    state.toastErr = isErr;
    if (state.toastTimer) clearTimeout(state.toastTimer);
    toastEl.textContent = msg;
    toastEl.style.background = "var(--card)";
    toastEl.style.border = "1px solid var(--brd)";
    toastEl.style.color = isErr ? "var(--st-failed)" : "var(--st-done)";
    toastEl.style.display = "block";
    state.toastTimer = setTimeout(() => {
      state.toast = "";
      toastEl.style.display = "none";
    }, 2600);
  }

  // ── 选中文件 ──
  async function selectFile(path) {
    state.mode = "view";
    state.fileErr = "";
    state.bodyDraft = ""; state.meta = {}; state.kwDraft = "";
    try {
      const r = await api.specFile(path);
      const parts = (r.path || path).split("/");
      state.current = {
        path: r.path || path,
        content: r.content || "",
        layer: parts[0] || "",
        category: parts[1] || "",
      };
      // 同步索引元信息 (title/keywords) 供列表展示
      const fm = parseFM(r.content || "");
      if (state.index[path]) {
        state.index[path].title = fm.meta.title || parts[2] || "";
        state.index[path].kw = Array.isArray(fm.meta.keywords) ? fm.meta.keywords.slice() : [];
      }
    } catch (e) {
      state.current = { path, content: "", layer: "", category: "" };
      state.fileErr = (e && e.message) || String(e);
    }
    renderList();    // 选中态高亮更新
    renderDetail();
  }

  // ── 预览模式 spec-wl 跳转 (wiki link) ──
  function onPreviewClick(e) {
    const a = e.target.closest(".spec-wl");
    if (!a) return;
    const name = a.dataset.name;
    if (!name) return;
    const hit = Object.values(state.index).find((f) => f.path.endsWith("/" + name + ".md"));
    if (hit) selectFile(hit.path);
  }

  // ── 全局事件委托 (nav/list/detail 三栏共用) ──
  nav.addEventListener("click", (e) => {
    const b = e.target.closest("[data-pick-layer]");
    if (!b) return;
    state.sel = { layer: b.getAttribute("data-pick-layer"), category: b.getAttribute("data-pick-cat") };
    state.q = "";
    renderNav();
    renderList();
  });

  list.addEventListener("input", (e) => {
    if (e.target.id === "spec-q") {
      state.q = e.target.value;
      renderList();
      // 重新挂回光标: 重渲后 input 失焦, 重聚焦到尾部
      const q = list.querySelector("#spec-q");
      if (q) { q.focus(); q.setSelectionRange(q.value.length, q.value.length); }
    }
  });
  list.addEventListener("click", (e) => {
    const el = e.target.closest("[data-select]");
    if (!el) return;
    selectFile(el.getAttribute("data-select"));
  });

  detail.addEventListener("click", (e) => {
    // 预览模式 spec-wl 跳转
    if (state.mode === "view" && e.target.closest(".spec-wl")) {
      onPreviewClick(e);
      return;
    }
    // view/edit toggle (view 模式)
    const viewBtn = e.target.closest("#spec-mode-view");
    if (viewBtn) { if (!state.showDiff) setMode("view"); return; }
    const editBtn = e.target.closest("#spec-mode-edit");
    if (editBtn) { startEdit(); return; }
  });

  // ── ESC 关 diff 覆盖 (全局键) ──
  function onKey(e) {
    if (!document.body.contains(mount)) {
      document.removeEventListener("keydown", onKey);
      if (state.toastTimer) clearTimeout(state.toastTimer);
      return;
    }
    if (e.key === "Escape" && state.showDiff) {
      state.showDiff = false;
      renderDiffOverlay();
    }
  }
  document.addEventListener("keydown", onKey);

  // ── 首次渲染 ──
  renderNav();
  renderList();
  renderDetail();

  // ── onLive 软刷 (订阅 spec-changed, 无 task 订阅) ──
  // ponytail: 编辑态保守不软刷 — 草稿未保存, 重拉会丢; 仅 view 态 + diff 关闭时刷新当前文件。
  if (onLive) {
    const unsub = onLive(function () {
      if (state.mode === "edit" || state.showDiff) return;  // 编辑态跳过
      if (state.current.path) {
        // 重新拉取当前文件内容 (spec-changed 可能由其他编辑源触发)
        api.specFile(state.current.path).then((r) => {
          state.current = Object.assign({}, state.current, {
            path: r.path || state.current.path,
            content: r.content || "",
          });
          // 树可能也变了 (新文件/删除) — 重拉
          return api.spec();
        }).then((tree) => {
          const layers = toLayers(tree || {});
          state.layers = layers;
          // 重建索引
          state.index = {};
          layers.forEach((l) => l.cats.forEach((c) => c.files.forEach((f) => {
            const p = l.key + "/" + c.name + "/" + f;
            if (!state.index[p]) state.index[p] = { path: p, layer: l.key, category: c.name, title: f, kw: [] };
          })));
          renderNav();
          renderList();
          renderDetail();
        }).catch(() => {});
      } else {
        // 无选中文件: 只刷新树
        api.spec().then((tree) => {
          state.layers = toLayers(tree || {});
          renderNav();
          renderList();
        }).catch(() => {});
      }
    });
    return [unsub];
  }
}
