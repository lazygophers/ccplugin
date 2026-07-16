// SKEIN Commands 页: 白名单命令面板 — 只经 api.exec 跑后端 enum 命令, 前端绝不拼 shell。
// 两区: (1) 只读命令 (list/ready/pop/current/doctor 无参; status/contract/subtask-list 带 id 输入),
//        点击 → api.exec → stdout(等宽块)+exit code, stderr 红字; (2) 安全写表单 (create/subtask-add),
//        前端必填校验非空才允提交, 提交后显结果。破坏性命令 (start/finish/archive/clean) 后端拒, 此处不出现。
// page 契约: render(mount, params, ctx); ctx={api, md, onLive}; 响应式走 window.PetiteVue.createApp.

// 只读: 无参直点 vs 带参 (字段列表 = 需填输入框, 首个必填其余选填 — 对齐后端 _exec_argv)
const READONLY = [
  { cmd: "list", label: "list", desc: "全部 task 列表" },
  { cmd: "ready", label: "ready", desc: "可执行队列" },
  { cmd: "pop", label: "pop", desc: "下一个待执行" },
  { cmd: "current", label: "current", desc: "当前进行中" },
  { cmd: "doctor", label: "doctor", desc: "健康自检" },
  { cmd: "status", label: "status", desc: "task/子任务态", fields: [
    { key: "id", label: "task id", req: true }, { key: "sid", label: "sid (选填)" }] },
  { cmd: "contract", label: "contract", desc: "契约", fields: [
    { key: "id", label: "task id", req: true }] },
  { cmd: "subtask-list", label: "subtask-list", desc: "子任务列表", fields: [
    { key: "id", label: "task id", req: true }] },
];

// 安全写表单 (对齐后端 create / subtask-add 必填集)
const FORMS = [
  { cmd: "create", label: "create · 新建 task", fields: [
    { key: "id", label: "id", req: true }, { key: "name", label: "name", req: true },
    { key: "desc", label: "desc", req: true, area: true }, { key: "deps", label: "deps (逗号分隔, 选填)" }] },
  { cmd: "subtask-add", label: "subtask-add · 加子任务", fields: [
    { key: "id", label: "task id", req: true }, { key: "sid", label: "sid", req: true },
    { key: "name", label: "name", req: true }, { key: "desc", label: "desc", req: true, area: true },
    { key: "deps", label: "deps (选填)" }, { key: "agent", label: "agent (选填)" }] },
];

const TPL = `
<div class="max-w-3xl mx-auto space-y-6">
  <!-- 只读命令区 -->
  <section class="card p-5">
    <div class="flex items-center gap-2 mb-1">
      <h2 class="text-sm font-semibold" style="color:var(--head)">只读命令</h2>
      <span class="text-xs text-muted">安全查询, 无副作用</span>
    </div>
    <div class="flex flex-wrap gap-2 mt-3">
      <div v-for="c in readonly" :key="c.cmd" class="rounded p-2 flex flex-col gap-2"
        style="border:1px solid var(--line)">
        <div class="flex items-center gap-2">
          <code class="text-xs font-semibold" style="color:var(--head)">{{ c.label }}</code>
          <span class="text-[11px] text-muted">{{ c.desc }}</span>
        </div>
        <div v-if="c.fields" class="flex flex-wrap gap-1.5">
          <input v-for="f in c.fields" :key="f.key" v-model.trim="ro[c.cmd][f.key]"
            :placeholder="f.label" class="px-2 py-1 text-xs rounded w-32"
            style="background:var(--bg);color:var(--fg);border:1px solid var(--brd)">
        </div>
        <button class="px-3 py-1 text-xs rounded self-start"
          style="background:var(--accent);color:#fff"
          :disabled="running===c.cmd || !roValid(c)" @click="runRead(c)">
          {{ running===c.cmd ? '运行中…' : '运行' }}
        </button>
      </div>
    </div>
    <div v-html="renderResult(roResult)"></div>
  </section>

  <!-- 安全写表单区 -->
  <section v-for="fm in forms" :key="fm.cmd" class="card p-5">
    <h2 class="text-sm font-semibold mb-3" style="color:var(--head)">{{ fm.label }}</h2>
    <div class="space-y-2">
      <label v-for="f in fm.fields" :key="f.key" class="block">
        <span class="text-xs text-muted">{{ f.label }}<span v-if="f.req" style="color:var(--st-failed)"> *</span></span>
        <textarea v-if="f.area" v-model.trim="wr[fm.cmd][f.key]" rows="2"
          class="w-full mt-0.5 px-2 py-1 text-sm rounded font-mono"
          style="background:var(--bg);color:var(--fg);border:1px solid var(--brd);resize:vertical"></textarea>
        <input v-else v-model.trim="wr[fm.cmd][f.key]"
          class="w-full mt-0.5 px-2 py-1 text-sm rounded"
          style="background:var(--bg);color:var(--fg);border:1px solid var(--brd)">
      </label>
    </div>
    <button class="mt-3 px-4 py-1.5 text-sm rounded"
      style="background:var(--accent);color:#fff"
      :disabled="running===fm.cmd || !wrValid(fm)" @click="runWrite(fm)">
      {{ running===fm.cmd ? '提交中…' : '提交' }}
    </button>
    <span v-if="!wrValid(fm)" class="ml-2 text-[11px] text-muted">必填项 (*) 不能为空</span>
    <div v-html="renderResult(wrResult[fm.cmd])"></div>
  </section>
</div>`;

// 建各命令的空输入态
function blankFields(items, key) {
  const o = {};
  for (const it of items) { o[it.cmd] = {}; for (const f of (it[key] || [])) o[it.cmd][f.key] = ""; }
  return o;
}

export async function render(mount, params, ctx) {
  const { api } = ctx;
  mount.innerHTML = TPL;

  // 跑一条命令 → 归一结果 {cmd, exit, stdout, stderr} 或 {cmd, err}
  async function exec(cmd, args) {
    try {
      const r = await api.exec(cmd, args);
      return { cmd: r.cmd || cmd, exit: r.exit, stdout: r.stdout || "", stderr: r.stderr || "" };
    } catch (e) {
      return { cmd, err: (e && e.message) || String(e) };
    }
  }

  window.PetiteVue.createApp({
    readonly: READONLY,
    forms: FORMS,
    ro: blankFields(READONLY, "fields"),
    wr: blankFields(FORMS, "fields"),
    roResult: null,
    wrResult: {},        // cmd → result
    running: "",

    roValid(c) { return !c.fields || c.fields.every((f) => !f.req || this.ro[c.cmd][f.key]); },
    wrValid(fm) { return fm.fields.every((f) => !f.req || this.wr[fm.cmd][f.key]); },

    async runRead(c) {
      if (this.running) return;
      this.running = c.cmd;
      this.roResult = await exec(c.cmd, this.ro[c.cmd]);
      this.running = "";
    },
    async runWrite(fm) {
      if (this.running || !this.wrValid(fm)) return;
      this.running = fm.cmd;
      this.wrResult[fm.cmd] = await exec(fm.cmd, this.wr[fm.cmd]);
      this.running = "";
    },

    // ponytail: 写表单结果块复用只读区同款模板, 以字符串内联渲染 (petite-vue 无 slot/子组件),
    // 免为两处各写一遍相同 pre/badge 结构。
    renderResult(r) {
      if (!r) return "";
      const head = r.err
        ? `<span style="color:var(--st-failed)">${esc(r.err)}</span>`
        : `<span>exit ${r.exit}</span><span class="badge text-[11px] ${r.exit === 0 ? "badge-done" : "badge-failed"}">${r.exit === 0 ? "ok" : "fail"}</span>`;
      const out = r.stdout ? `<pre class="px-3 py-2 overflow-auto text-[12px] leading-5 font-mono whitespace-pre-wrap break-words" style="background:var(--bg);color:var(--fg);max-height:340px">${esc(r.stdout)}</pre>` : "";
      const err = r.stderr ? `<pre class="px-3 py-2 overflow-auto text-[12px] leading-5 font-mono whitespace-pre-wrap break-words" style="background:var(--bg);max-height:220px;color:var(--st-failed)">${esc(r.stderr)}</pre>` : "";
      return `<div class="mt-3 rounded overflow-hidden text-sm" style="border:1px solid var(--line)">
        <div class="px-3 py-1.5 flex items-center gap-2 text-xs" style="background:var(--line);color:${r.exit === 0 && !r.err ? "var(--st-done)" : "var(--st-failed)"}"><code>${esc(r.cmd)}</code>${head}</div>${out}${err}</div>`;
    },
  }).mount(mount);
}

// html 转义 (renderResult 走 v-html, stdout/stderr 是命令输出须转义防注入)
function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
