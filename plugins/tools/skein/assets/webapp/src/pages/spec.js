// SKEIN Spec 页: 两层记忆 (core 常驻 / recall 召回) 树 → 看原文 (md) → 编辑 → diff 确认弹层 → 落盘。
// 编辑是敏感操作: 保存必经 diff 确认 (行级增删高亮), 确认才 api.specSave, 取消不写。
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

const TPL = `
<div class="flex gap-4 h-[calc(100vh-120px)]">
  <!-- 左: 两层 × 类目 × 文件 树 -->
  <aside class="w-64 shrink-0 overflow-auto card p-3">
    <div class="text-xs uppercase tracking-wide opacity-60 mb-2">Spec 记忆</div>
    <div v-if="loadErr" class="text-sm" style="color:var(--st-failed)">{{ loadErr }}</div>
    <div v-else-if="empty" class="text-sm text-muted py-8 text-center">
      <div class="empty-ico"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg></div>暂无 spec<div class="text-xs opacity-60 mt-1">.skein/spec/ 为空</div>
    </div>
    <div v-else>
    <div v-for="layer in layers" :key="layer.key">
      <div class="mt-2 mb-1 text-[11px] font-semibold" style="color:var(--head)">
        {{ layer.label }}
      </div>
      <div v-for="cat in layer.cats" :key="cat.name">
        <button class="w-full text-left px-1 py-0.5 text-sm rounded hover:bg-[var(--line)] flex items-center gap-1"
          @click="toggle(layer.key + '/' + cat.name)">
          <span class="inline-block w-3 opacity-60">{{ isOpen(layer.key+'/'+cat.name) ? '▾' : '▸' }}</span>
          <span class="truncate">{{ cat.name }}</span>
        </button>
        <div v-show="isOpen(layer.key+'/'+cat.name)" class="ml-4">
          <button v-for="f in cat.files" :key="f"
            class="w-full text-left px-1 py-0.5 text-sm rounded truncate hover:bg-[var(--line)]"
            :class="{ 'font-medium': isCurrent(layer.key, cat.name, f) }"
            :style="isCurrent(layer.key, cat.name, f) ? 'background:var(--line);color:var(--accent)' : ''"
            @click="select(layer.key, cat.name, f)">
            {{ f }}
          </button>
        </div>
      </div>
    </div>
    </div>
  </aside>

  <!-- 右: 原文 / 编辑 -->
  <section class="flex-1 min-w-0 overflow-auto card p-5">
    <div v-if="!current.path" class="text-muted text-center py-24">选择左侧文件查看</div>
    <div v-else>
      <div class="flex items-center gap-3 mb-3 pb-3" style="border-bottom:1px solid var(--line)">
        <code class="text-sm" style="color:var(--head)">{{ current.path }}</code>
        <span class="flex-1"></span>
        <button v-if="mode==='view'" class="px-3 py-1 text-sm rounded"
          style="background:var(--accent);color:#fff" @click="startEdit">编辑</button>
        <template v-else>
          <button class="px-3 py-1 text-sm rounded" style="border:1px solid var(--brd)" @click="cancelEdit">取消</button>
          <button class="px-3 py-1 text-sm rounded" style="background:var(--accent);color:#fff"
            :disabled="draft===current.content" @click="reviewSave">保存…</button>
        </template>
      </div>
      <div v-if="fileErr" class="text-sm" style="color:var(--st-failed)">{{ fileErr }}</div>
      <div v-else-if="mode==='view'" class="md-body" v-html="rendered"></div>
      <textarea v-else v-model="draft" spellcheck="false"
        class="w-full h-[70vh] p-3 text-sm rounded font-mono"
        style="background:var(--bg);color:var(--fg);border:1px solid var(--brd);resize:vertical"></textarea>
    </div>
  </section>

  <!-- diff 确认弹层 -->
  <div v-if="showDiff" class="fixed inset-0 z-50 flex items-center justify-center"
    style="background:rgba(0,0,0,.45)" @click.self="showDiff=false">
    <div class="w-[min(880px,92vw)] max-h-[86vh] flex flex-col rounded-lg overflow-hidden"
      style="background:var(--card);border:1px solid var(--brd);box-shadow:0 12px 40px rgba(0,0,0,.3)">
      <div class="px-5 py-3 flex items-center gap-2" style="border-bottom:1px solid var(--line)">
        <strong>确认保存改动</strong>
        <code class="text-xs opacity-70">{{ current.path }}</code>
        <span class="flex-1"></span>
        <span class="text-xs text-muted">+{{ addCount }} / -{{ delCount }}</span>
      </div>
      <div class="flex-1 overflow-auto p-0 font-mono text-[13px] leading-5">
        <div v-if="!diff.length" class="p-5 text-muted text-sm">无差异</div>
        <div v-for="(d,idx) in diff" :key="idx" class="px-3 whitespace-pre-wrap break-words"
          :style="d.t==='add' ? 'background:color-mix(in srgb,var(--st-done) 22%,transparent)'
                : d.t==='del' ? 'background:color-mix(in srgb,var(--st-failed) 22%,transparent)' : ''">
          <span class="inline-block w-4 select-none opacity-60">{{ d.t==='add'?'+':d.t==='del'?'-':' ' }}</span>{{ d.s }}
        </div>
      </div>
      <div class="px-5 py-3 flex justify-end gap-2" style="border-top:1px solid var(--line)">
        <button class="px-3 py-1 text-sm rounded" style="border:1px solid var(--brd)"
          @click="showDiff=false">取消</button>
        <button class="px-3 py-1 text-sm rounded" style="background:var(--accent);color:#fff"
          :disabled="saving || !diff.length" @click="confirmSave">{{ saving ? '保存中…' : '确认落盘' }}</button>
      </div>
    </div>
  </div>

  <!-- toast -->
  <div v-if="toast" class="fixed bottom-6 left-1/2 -translate-x-1/2 z-[60] px-4 py-2 rounded text-sm"
    :style="'background:var(--card);border:1px solid var(--brd);color:'+(toastErr?'var(--st-failed)':'var(--st-done)')">
    {{ toast }}
  </div>
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
  try { tree = await api.spec(); } catch (e) { loadErr = e && e.message || String(e); }

  const layers = toLayers(tree || {});
  mount.innerHTML = TPL;

  window.PetiteVue.createApp({
    layers,
    loadErr,
    empty: !loadErr && layers.length === 0,
    open: {},                                  // "layer/cat" → 展开态 (默认展开)
    current: { path: "", content: "" },
    mode: "view",
    draft: "",
    fileErr: "",
    showDiff: false,
    saving: false,
    toast: "",
    toastErr: false,

    get rendered() { return md.renderSafe(this.current.content); },
    get diff() { return diffLines(this.current.content, this.draft); },
    get addCount() { return this.diff.filter((d) => d.t === "add").length; },
    get delCount() { return this.diff.filter((d) => d.t === "del").length; },

    isOpen(k) { return this.open[k] !== false; },
    toggle(k) { this.open[k] = this.open[k] === false; },
    isCurrent(layer, cat, f) { return this.current.path === layer + "/" + cat + "/" + f; },

    async select(layer, cat, f) {
      const path = layer + "/" + cat + "/" + f;
      this.mode = "view"; this.fileErr = "";
      try {
        const r = await api.specFile(path);
        this.current = { path: r.path || path, content: r.content || "" };
      } catch (e) {
        this.current = { path, content: "" };
        this.fileErr = e && e.message || String(e);
      }
    },
    startEdit() { this.draft = this.current.content; this.mode = "edit"; },
    cancelEdit() { this.mode = "view"; this.draft = ""; },
    reviewSave() { if (this.draft !== this.current.content) this.showDiff = true; },

    async confirmSave() {
      if (this.saving) return;
      this.saving = true;
      try {
        await api.specSave(this.current.path, this.draft);
        this.current = { path: this.current.path, content: this.draft };
        this.showDiff = false; this.mode = "view";
        this.flash("已保存 " + this.current.path, false);
      } catch (e) {
        this.showDiff = false;
        this.flash("保存失败: " + (e && e.message || e), true);
      } finally { this.saving = false; }
    },
    flash(msg, isErr) {
      this.toast = msg; this.toastErr = isErr;
      clearTimeout(this._t);
      this._t = setTimeout(() => { this.toast = ""; }, 2600);
    },
  }).mount(mount);
}
