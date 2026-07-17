// SKEIN Spec 页: 三栏 (导航树 / 文件列表 / 详情)。
// 详情: 预览 (md body 渲染) ↔ 编辑 (metadata frontmatter 表单 + 增强 textarea)。
// 保存必经 diff 确认 (全屏, 行级增删高亮), 确认才 api.specSave, 取消不写。
// page 契约: render(mount, params, ctx); ctx={api, md, onLive}; 响应式走 window.PetiteVue.createApp.

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
    .map(([k, v]) => (Array.isArray(v) ? `${k}: [${v.join(", ")}]` : `${k}: ${v}`));
  return `---\n${lines.join("\n")}\n---\n${body || ""}`;
}

const CATS = ["arch", "frontend", "ops", "style"];
const META_KEYS = ["title", "layer", "category", "keywords", "source", "authored-by", "created"];

const TPL = `
<div class="spec-3col">
  <!-- 第一栏: 导航树 (layer × category) -->
  <aside class="spec-nav card p-3">
    <div class="text-xs uppercase tracking-wide opacity-60 mb-2">Spec 记忆</div>
    <div class="text-[11px] opacity-60 mb-2">core {{ coreCount }} / recall {{ recallCount }}</div>
    <div v-if="loadErr" class="text-sm" style="color:var(--st-failed)">{{ loadErr }}</div>
    <div v-else-if="empty" class="text-sm text-muted py-8 text-center">
      <div class="empty-ico"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg></div>暂无 spec<div class="text-xs opacity-60 mt-1">.skein/spec/ 为空</div>
    </div>
    <div v-else>
      <div v-for="layer in layers" :key="layer.key" class="mt-1">
        <div class="mt-2 mb-1 text-[11px] font-semibold" style="color:var(--head)">{{ layer.label }}</div>
        <button v-for="cat in layer.cats" :key="cat.name"
          class="w-full text-left px-2 py-1 text-sm rounded flex items-center gap-2"
          :class="navSel(layer.key, cat.name) ? 'font-medium' : ''"
          :style="navSel(layer.key, cat.name) ? 'background:var(--line);color:var(--accent);border-left:2px solid var(--accent)' : 'border-left:2px solid transparent'"
          @click="pickCat(layer.key, cat.name)">
          <span class="truncate flex-1">{{ cat.name }}</span>
          <span class="text-[10px] opacity-50">{{ cat.files.length }}</span>
        </button>
      </div>
    </div>
  </aside>

  <!-- 第二栏: 文件列表 (当前 layer+category, 模糊过滤) -->
  <section class="spec-list card p-3">
    <input type="text" v-model="q" placeholder="搜索 title / keywords / 文件名"
      class="w-full mb-2 px-2 py-1 text-sm rounded"
      style="background:var(--bg);color:var(--fg);border:1px solid var(--brd)">
    <div v-if="!listFiles.length" class="text-sm text-muted py-8 text-center">
      <div v-if="!sel.layer">选左侧类目</div>
      <div v-else-if="q">无匹配</div>
    </div>
    <div v-else>
      <div v-for="f in listFiles" :key="f.path"
        class="px-2 py-1.5 rounded cursor-pointer text-sm"
        :style="isCurrentFile(f.path) ? 'background:var(--line);color:var(--accent)' : ''"
        @click="selectFile(f.path)">
        <div class="font-medium truncate">{{ fileTitle(f) }}</div>
        <div class="text-[11px] opacity-60 truncate">{{ f.path }}</div>
        <div v-if="f.kw && f.kw.length" class="mt-0.5 flex flex-wrap gap-1">
          <span v-for="k in f.kw.slice(0,4)" :key="k" class="spec-kw-chip">{{ k }}</span>
        </div>
      </div>
    </div>
  </section>

  <!-- 第三栏: 详情 -->
  <section class="spec-detail card p-4">
    <div v-if="!current.path" class="text-muted text-center py-24">选择文件查看</div>
    <div v-else>
      <!-- 面包屑 + chip + toggle -->
      <div class="flex items-center gap-2 mb-2 text-sm">
        <span class="opacity-60">{{ crumb }}</span>
        <span class="flex-1"></span>
        <span class="spec-kw-chip" :style="'color:var(--accent)'">{{ current.layer || '?' }}</span>
        <span class="spec-kw-chip">{{ current.category || '?' }}</span>
      </div>
      <div class="flex items-center gap-1 mb-3 p-0.5 rounded" style="background:var(--line);width:fit-content">
        <button class="px-3 py-1 text-xs rounded transition"
          :style="mode==='view' ? 'background:var(--card);color:var(--accent);font-weight:600' : 'color:var(--muted)'"
          @click="setMode('view')">预览</button>
        <button class="px-3 py-1 text-xs rounded transition"
          :style="mode==='edit' ? 'background:var(--card);color:var(--accent);font-weight:600' : 'color:var(--muted)'"
          @click="startEdit">编辑</button>
      </div>

      <div v-if="fileErr" class="text-sm" style="color:var(--st-failed)">{{ fileErr }}</div>

      <!-- 预览模式 -->
      <div v-else-if="mode==='view'" class="md-body" v-html="rendered"></div>

      <!-- 编辑模式 -->
      <div v-else>
        <!-- metadata 表单 -->
        <div class="spec-meta-form">
          <label class="full flex flex-col gap-1 text-xs">
            <span class="opacity-60">title</span>
            <input type="text" v-model="meta.title" spellcheck="false"
              class="px-2 py-1 text-sm rounded"
              style="background:var(--bg);color:var(--fg);border:1px solid var(--brd)">
          </label>
          <label class="flex flex-col gap-1 text-xs">
            <span class="opacity-60">layer</span>
            <select v-model="meta.layer"
              class="px-2 py-1 text-sm rounded"
              style="background:var(--bg);color:var(--fg);border:1px solid var(--brd)">
              <option value="core">core</option>
              <option value="recall">recall</option>
            </select>
          </label>
          <label class="flex flex-col gap-1 text-xs">
            <span class="opacity-60">category</span>
            <select v-model="meta.category"
              class="px-2 py-1 text-sm rounded"
              style="background:var(--bg);color:var(--fg);border:1px solid var(--brd)">
              <option v-for="c in catOptions" :key="c" :value="c">{{ c }}</option>
            </select>
          </label>
          <label class="flex flex-col gap-1 text-xs">
            <span class="opacity-60">source</span>
            <input type="text" v-model="meta.source" spellcheck="false"
              class="px-2 py-1 text-sm rounded"
              style="background:var(--bg);color:var(--fg);border:1px solid var(--brd)">
          </label>
          <label class="flex flex-col gap-1 text-xs">
            <span class="opacity-60">authored-by</span>
            <input type="text" v-model="meta['authored-by']" spellcheck="false"
              class="px-2 py-1 text-sm rounded"
              style="background:var(--bg);color:var(--fg);border:1px solid var(--brd)">
          </label>
          <label class="flex flex-col gap-1 text-xs">
            <span class="opacity-60">created (unix ts)</span>
            <input type="number" v-model.number="meta.created"
              class="px-2 py-1 text-sm rounded"
              style="background:var(--bg);color:var(--fg);border:1px solid var(--brd)">
          </label>
          <div class="full flex flex-col gap-1 text-xs">
            <span class="opacity-60">keywords (逗号/回车分隔, 退格删尾)</span>
            <div class="flex flex-wrap items-center gap-1 p-1 rounded"
              style="background:var(--bg);border:1px solid var(--brd);min-height:2rem">
              <span v-for="(k,i) in (meta.keywords||[])" :key="i" class="spec-kw-chip cursor-pointer"
                @click="removeKw(i)" :title="'删 ' + k">{{ k }} ✕</span>
              <input type="text" v-model="kwDraft" placeholder="回车或逗号添加"
                class="flex-1 min-w-[8rem] px-1 py-0.5 text-sm bg-transparent"
                style="color:var(--fg);border:none;outline:none"
                @keydown.enter.prevent="addKw()"
                @keydown.comma.prevent="addKw()"
                @keydown.delete="backKw()">
            </div>
          </div>
        </div>

        <!-- 正文 textarea + 行号槽 -->
        <div class="spec-editor-wrap">
          <div class="spec-gutter" :ref="'gutter'" v-html="gutterHtml"></div>
          <textarea ref="ta" v-model="bodyDraft" spellcheck="false"
            class="spec-editor w-full h-[60vh] p-3 rounded"
            style="background:var(--bg);color:var(--fg);border:1px solid var(--brd);resize:vertical"
            @scroll="syncGutter"
            @keydown.tab.prevent="onTab($event)"
            @keydown.meta.s.prevent="reviewSave"
            @keydown.ctrl.s.prevent="reviewSave"
            @keydown.escape="cancelEdit"></textarea>
        </div>

        <div class="flex justify-end gap-2 mt-2">
          <button class="px-3 py-1 text-sm rounded" style="border:1px solid var(--brd)" @click="cancelEdit">取消 (Esc)</button>
          <button class="px-3 py-1 text-sm rounded" :disabled="!dirty"
            :style="dirty ? 'background:var(--accent);color:#fff' : 'opacity:.5'"
            @click="reviewSave">保存… (⌘S)</button>
        </div>
      </div>
    </div>
  </section>
</div>

<!-- 全屏 diff 覆盖 (z-modal) -->
<div v-if="showDiff" class="fixed inset-0 flex flex-col" style="background:var(--bg);z-index:2000">
  <div class="px-5 py-3 flex items-center gap-2" style="border-bottom:1px solid var(--line)">
    <strong>确认保存改动</strong>
    <code class="text-xs opacity-70">{{ current.path }}</code>
    <span class="flex-1"></span>
    <span class="text-xs" style="color:var(--st-done)">+{{ addCount }}</span>
    <span class="text-xs" style="color:var(--st-failed)">-{{ delCount }}</span>
    <span class="opacity-60 text-xs ml-3">Esc 取消</span>
  </div>
  <div class="flex-1 overflow-auto font-mono text-[13px] leading-5">
    <div v-if="!diff.length" class="p-5 text-muted text-sm">无差异</div>
    <div v-for="(d,idx) in diff" :key="idx"
      class="px-3 whitespace-pre-wrap break-words flex"
      :style="d.t==='add' ? 'background:color-mix(in srgb,var(--st-done) 20%,transparent)'
            : d.t==='del' ? 'background:color-mix(in srgb,var(--st-failed) 20%,transparent)' : ''">
      <span class="inline-block w-6 select-none opacity-50 shrink-0">{{ d.t==='add'?'+':d.t==='del'?'-':' ' }}</span>
      <span>{{ d.s }}</span>
    </div>
  </div>
  <div class="px-5 py-3 flex justify-end gap-2" style="border-top:1px solid var(--line)">
    <button class="px-3 py-1 text-sm rounded" style="border:1px solid var(--brd)" @click="closeDiff">取消</button>
    <button class="px-3 py-1 text-sm rounded" :disabled="saving || !diff.length"
      style="background:var(--accent);color:#fff" @click="confirmSave">{{ saving ? '保存中…' : '确认落盘' }}</button>
  </div>
</div>

<!-- toast -->
<div v-if="toast" class="fixed bottom-6 left-1/2 -translate-x-1/2 z-[2100] px-4 py-2 rounded text-sm"
  :style="'background:var(--card);border:1px solid var(--brd);color:'+(toastErr?'var(--st-failed)':'var(--st-done)')">
  {{ toast }}
</div>`;

// 后端 tree: {core:{类目:[文件]}, recall:{类目:[文件]}} → 规整为可迭代 layers
function toLayers(tree) {
  const meta = [["core", "CORE · 常驻硬规"], ["recall", "RECALL · 按需召回"]];
  return meta.map(([key, label]) => ({
    key, label,
    cats: Object.keys(tree[key] || {}).sort().map((name) => ({ name, files: (tree[key][name] || []).slice() })),
  })).filter((l) => l.cats.length);
}

export async function render(mount, params, ctx) {
  const { api, md } = ctx;
  let tree = {};
  let loadErr = "";
  try { tree = await api.spec(); } catch (e) { loadErr = (e && e.message) || String(e); }

  const layers = toLayers(tree || {});
  // 文件级索引: path → {path, title, kw, layer, category}, 供中栏搜索过滤与展示
  const index = {};
  layers.forEach((l) => l.cats.forEach((c) => c.files.forEach((f) => {
    const p = l.key + "/" + c.name + "/" + f;
    index[p] = { path: p, layer: l.key, category: c.name, title: f, kw: [] };
  })));

  mount.innerHTML = TPL;

  const app = window.PetiteVue.createApp({
    layers,
    index,
    loadErr,
    empty: !loadErr && layers.length === 0,
    coreCount: (layers.find((l) => l.key === "core") || { cats: [] }).cats.reduce((a, c) => a + c.files.length, 0),
    recallCount: (layers.find((l) => l.key === "recall") || { cats: [] }).cats.reduce((a, c) => a + c.files.length, 0),
    catOptions: CATS,

    sel: { layer: "", category: "" },                 // 中栏当前筛选
    q: "",                                            // 中栏搜索
    current: { path: "", content: "", layer: "", category: "" },
    mode: "view",
    bodyDraft: "",
    meta: {},
    kwDraft: "",
    fileErr: "",
    showDiff: false,
    saving: false,
    toast: "",
    toastErr: false,

    get crumb() { return [this.current.layer, this.current.category, this.current.path.split("/").pop()].filter(Boolean).join(" / "); },
    get parsed() { return parseFM(this.current.content); },
    get rendered() { return md.renderSafe(this.parsed.body); },
    get draftSerialized() { return serializeFM(this.meta, this.bodyDraft); },
    get dirty() { return this.draftSerialized !== this.current.content; },
    get diff() { return diffLines(this.current.content, this.draftSerialized); },
    get addCount() { return this.diff.filter((d) => d.t === "add").length; },
    get delCount() { return this.diff.filter((d) => d.t === "del").length; },
    get gutterHtml() {
      const n = (this.bodyDraft || "").split("\n").length;
      let s = "";
      for (let i = 1; i <= n; i++) s += i + "\n";
      return s;
    },

    // 中栏: 当前 layer+category 下文件 (无 sel → 空), 按 q 模糊过滤 title/keywords/path
    get listFiles() {
      const all = this.sel.layer
        ? ((this.layers.find((l) => l.key === this.sel.layer) || { cats: [] }).cats
            .find((c) => c.name === this.sel.category) || { files: [] }).files
            .map((f) => this.index[this.sel.layer + "/" + this.sel.category + "/" + f])
            .filter(Boolean)
        : [];
      const q = (this.q || "").trim().toLowerCase();
      if (!q) return all;
      return all.filter((f) => {
        const t = ((f && f.title) || "").toLowerCase();
        const k = ((f && f.kw) || []).join(" ").toLowerCase();
        const p = (f && f.path || "").toLowerCase();
        return t.indexOf(q) >= 0 || k.indexOf(q) >= 0 || p.indexOf(q) >= 0;
      });
    },

    navSel(layer, cat) { return this.sel.layer === layer && this.sel.category === cat; },
    pickCat(layer, cat) {
      this.sel = { layer, category: cat };
      this.q = "";
    },
    isCurrentFile(p) { return this.current.path === p; },
    fileTitle(f) { return (f && f.title) || (f && f.path || "").split("/").pop() || ""; },

    async selectFile(path) {
      this.mode = "view"; this.fileErr = "";
      try {
        const r = await api.specFile(path);
        const parts = (r.path || path).split("/");
        this.current = {
          path: r.path || path,
          content: r.content || "",
          layer: parts[0] || "",
          category: parts[1] || "",
        };
        // 同步索引元信息 (title/keywords) 供列表展示
        const fm = parseFM(r.content || "");
        if (this.index[path]) {
          this.index[path].title = fm.meta.title || parts[2] || "";
          this.index[path].kw = Array.isArray(fm.meta.keywords) ? fm.meta.keywords.slice() : [];
        }
      } catch (e) {
        this.current = { path, content: "", layer: "", category: "" };
        this.fileErr = (e && e.message) || String(e);
      }
    },

    setMode(m) { this.mode = m; },
    startEdit() {
      const fm = parseFM(this.current.content);
      // ponytail: 深拷贝 meta 防 v-model 直接改原对象引用; keywords 新数组触发响应式
      this.meta = META_KEYS.reduce((o, k) => {
        o[k] = Array.isArray(fm.meta[k]) ? fm.meta[k].slice() : (fm.meta[k] != null ? fm.meta[k] : (k === "keywords" ? [] : ""));
        return o;
      }, {});
      // 从路径回填 layer/category (无 frontmatter 也能给默认)
      if (!this.meta.layer) this.meta.layer = this.current.layer;
      if (!this.meta.category) this.meta.category = this.current.category;
      this.bodyDraft = fm.body;
      this.kwDraft = "";
      this.mode = "edit";
    },
    cancelEdit() {
      if (this.showDiff) { this.showDiff = false; return; }
      this.mode = "view"; this.bodyDraft = ""; this.meta = {}; this.kwDraft = "";
    },
    addKw() {
      const v = (this.kwDraft || "").replace(/,$/, "").trim();
      if (!v) return;
      const cur = Array.isArray(this.meta.keywords) ? this.meta.keywords.slice() : [];
      if (cur.indexOf(v) < 0) cur.push(v);
      this.meta.keywords = cur;            // 新数组引用 → petite-vue 重渲染
      this.kwDraft = "";
    },
    removeKw(i) {
      const cur = (this.meta.keywords || []).slice();
      cur.splice(i, 1);
      this.meta.keywords = cur;
    },
    backKw() {
      if (!this.kwDraft && (this.meta.keywords || []).length) {
        const cur = this.meta.keywords.slice();
        cur.pop();
        this.meta.keywords = cur;
      }
    },
    onTab(e) {
      const ta = e.target;
      const s = ta.selectionStart, en = ta.selectionEnd;
      this.bodyDraft = this.bodyDraft.slice(0, s) + "  " + this.bodyDraft.slice(en);
      this.$nextTick(() => { ta.selectionStart = ta.selectionEnd = s + 2; });
    },
    syncGutter(e) {
      const g = this.$refs && this.$refs.gutter;
      if (g) g.scrollTop = e.target.scrollTop;
    },

    reviewSave() {
      if (this.mode !== "edit") return;
      if (this.dirty) this.showDiff = true;
      else this.flash("无改动", false);
    },
    closeDiff() { this.showDiff = false; },
    async confirmSave() {
      if (this.saving) return;
      this.saving = true;
      try {
        const draft = this.draftSerialized;
        await api.specSave(this.current.path, draft);
        this.current = { ...this.current, content: draft };
        // 同步索引展示
        if (this.index[this.current.path]) {
          this.index[this.current.path].title = (this.meta && this.meta.title) || this.current.path.split("/")[2] || "";
          this.index[this.current.path].kw = Array.isArray(this.meta.keywords) ? this.meta.keywords.slice() : [];
        }
        this.showDiff = false; this.mode = "view";
        this.flash("已保存 " + this.current.path, false);
      } catch (e) {
        this.showDiff = false;
        this.flash("保存失败: " + ((e && e.message) || e), true);
      } finally { this.saving = false; }
    },
    flash(msg, isErr) {
      this.toast = msg; this.toastErr = isErr;
      clearTimeout(this._t);
      this._t = setTimeout(() => { this.toast = ""; }, 2600);
    },
  });

  app.mount(mount);
}
