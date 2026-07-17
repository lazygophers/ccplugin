// SKEIN webapp 设置模态 (顶栏齿轮触发, 非 router 页 — 由 app.js 注入 api 后调用 wire())。
//   表单 + YAML 双 Tab 双向同步, 实时保存 (debounce 400ms, 无保存按钮)。
//   GET /__skein__/config 拿当前值; 改任一控件 → 更新内存 cfg → 同步另一 Tab → debounce → POST 全量 10 键。
//   toast 复用简易 div (spec.js 同款)。YAML 简易 dump/parse (flat, bool/int/str)。

// CONFIG_DEFAULTS 镜像 (scripts/skein.py:147) — 仅作类型/默认值/控件元信息; 实际值取自后端。
// 重启提示: 改了 board_theme/worktree_root 需重启 serve 生效 (前端只回写 config.yaml)。
const SCHEMA = [
  { k: "max_active", type: "int", label: "task 并发上限", hint: "同 session 同时 in_progress 的 task 数" },
  { k: "max_parallel", type: "int", label: "subtask 并行上限", hint: "单 task 内同时跑的 subtask 数" },
  { k: "auto_commit", type: "bool", label: "自动提交", hint: "变更自动提交暂存区" },
  { k: "use_worktree", type: "bool", label: "worktree 隔离", hint: "启用 git worktree 隔离执行" },
  { k: "worktree_root", type: "str", label: "worktree 根目录", hint: "改了需重启 serve 生效" },
  { k: "retain_days", type: "int", label: "task 保留天数", hint: "完成 task 保留天数 (0=立即归档, 负=永不)" },
  { k: "board_theme", type: "str", label: "看板主题", hint: "改了需重启 serve 生效", options: ["skein"] },
  { k: "web_serve", type: "bool", label: "http 服务", hint: "看板 http 服务总开关" },
  { k: "board_open", type: "bool", label: "view 自动开浏览器", hint: "仅 view 命令生效" },
];
const RESTART_KEYS = new Set(["worktree_root", "board_theme"]);
const DEBOUNCE_MS = 400;

// 简易 flat YAML dump: bool→true/false, str→原值, int→String(n)。
// ponytail: 不引 yaml 库 — config 全是 flat 标量, 与 spec.js parseFM 同款朴素实现。
function dumpYaml(cfg) {
  return SCHEMA.map((s) => {
    const v = cfg[s.k];
    const out = s.type === "bool" ? (v ? "true" : "false")
      : s.type === "int" ? String(Number(v) || 0)
      : String(v == null ? "" : v);
    return s.k + ": " + out;
  }).join("\n") + "\n";
}

// 简易 flat YAML parse: 行内首个 ":" 分割; val 按 SCHEMA 类型 coerce。
// 容错: 无冒号行跳过, 类型不合→undefined (调用方按默认兜底)。
function parseYaml(text) {
  const out = {};
  (text || "").split(/\r?\n/).forEach((line) => {
    const i = line.indexOf(":");
    if (i < 0) return;
    const k = line.slice(0, i).trim();
    const raw = line.slice(i + 1).trim();
    const s = SCHEMA.find((x) => x.k === k);
    if (!s) return;
    if (s.type === "bool") out[k] = /^(true|1|yes|on)$/i.test(raw);
    else if (s.type === "int") { const n = parseInt(raw, 10); if (!isNaN(n)) out[k] = n; }
    else out[k] = raw;
  });
  return out;
}

function esc(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

const FORM_TPL = SCHEMA.map((s) => {
  const lab = '<div class="cfg-label">' + esc(s.label) +
    (RESTART_KEYS.has(s.k) ? ' <span class="cfg-restart" title="需重启 serve 生效">⟳</span>' : "") +
    '</div><div class="cfg-hint">' + esc(s.hint) + "</div>";
  let ctrl;
  if (s.type === "bool") {
    ctrl = '<button type="button" class="cfg-switch" data-cfg="' + s.k + '" role="switch" :aria-checked="String(!!cfg[\'' + s.k + '\'])" ' +
      '@click="toggle(\'' + s.k + '\')"><span class="cfg-knob"></span></button>';
  } else if (s.options) {
    ctrl = '<select class="cfg-input" v-model="cfg[\'' + s.k + '\']" @change="onMutate()">' +
      s.options.map((o) => '<option value="' + esc(o) + '">' + esc(o) + "</option>").join("") + "</select>";
  } else if (s.type === "int") {
    ctrl = '<input type="number" class="cfg-input" v-model.number="cfg[\'' + s.k + '\']" @input="onMutate()">';
  } else {
    ctrl = '<input type="text" class="cfg-input" spellcheck="false" v-model="cfg[\'' + s.k + '\']" @input="onMutate()">';
  }
  return '<label class="cfg-row' + (s.type === "bool" ? " cfg-row-switch" : "") + '">' +
    '<span class="cfg-meta">' + lab + "</span>" + ctrl + "</label>";
}).join("");

const MODAL_TPL = `
<div class="cfg-mask" @click.self="close" @keydown.escape="close">
  <div class="cfg-modal card" role="dialog" aria-modal="true" aria-label="设置">
    <div class="cfg-head">
      <strong>设置</strong>
      <span class="cfg-sub">实时保存 · 改动即生效</span>
      <span class="flex-1"></span>
      <button type="button" class="cfg-x" aria-label="关闭" @click="close">✕</button>
    </div>
    <div class="cfg-tabs">
      <button type="button" :class="'cfg-tab' + (tab==='form' ? ' on' : '')" @click="tab='form'">表单</button>
      <button type="button" :class="'cfg-tab' + (tab==='yaml' ? ' on' : '')" @click="tab='yaml'">YAML</button>
    </div>
    <div class="cfg-body">
      <div v-if="loading" class="cfg-empty">加载中…</div>
      <div v-else-if="loadErr" class="cfg-empty cfg-err">{{ loadErr }}</div>
      <div v-else-if="tab==='form'" class="cfg-form">
        ${FORM_TPL}
      </div>
      <textarea v-else class="cfg-input cfg-yaml" spellcheck="false" wrap="off"
        :value="yamlText" @input="onYamlInput($event)" @change="onYamlInput($event)"></textarea>
    </div>
    <div v-if="restartHint" class="cfg-foot">⟳ 已改需重启 serve 生效的项</div>
  </div>
</div>`;

let _api = null;

// 注入 api (app.js 启动时调一次); 按钮点击 → open()。
export function wire(api) {
  _api = api;
  const btn = document.getElementById("config-btn");
  if (btn) btn.addEventListener("click", () => open());
}

let _open = false;            // 简单互斥: 已开则不重开 (避免叠多层)
function open() {
  if (_open || !_api) return;
  _open = true;
  const host = document.createElement("div");
  host.className = "cfg-host";
  document.body.appendChild(host);
  host.innerHTML = MODAL_TPL;

  const app = window.PetiteVue.createApp({
    cfg: {},
    tab: "form",
    loading: true,
    loadErr: "",
    yamlText: "",
    restartHint: false,

    get root() { return host.querySelector(".cfg-mask"); },

    async init() {
      try {
        const cfg = await _api.getConfig();
        // 仅取 SCHEMA 已知键 (后端可能多返 ENV override 同名键, 一并收纳)
        this.cfg = SCHEMA.reduce((o, s) => { o[s.k] = cfg[s.k]; return o; }, {});
        this.yamlText = dumpYaml(this.cfg);
      } catch (e) {
        this.loadErr = (e && e.message) || String(e);
      } finally { this.loading = false; }
    },

    toggle(k) { this.cfg[k] = !this.cfg[k]; this.onMutate(); },

    // 表单控件改 → 同步 YAML → debounce 保存
    onMutate() {
      this.yamlText = dumpYaml(this.cfg);
      this._checkRestart();
      this._schedule();
    },

    // YAML textarea 改 → parse → 回填表单 cfg (仅成功覆盖, 缺键保留); → debounce 保存
    onYamlInput(e) {
      const text = e.target.value;
      const parsed = parseYaml(text);
      this.yamlText = text;
      // 只回填 parse 命中的键, 未命中保留原值; 触发响应式用新对象
      const next = { ...this.cfg };
      SCHEMA.forEach((s) => { if (parsed[s.k] !== undefined) next[s.k] = parsed[s.k]; });
      this.cfg = next;
      this._checkRestart();
      this._schedule();
    },

    _checkRestart() {
      this.restartHint = SCHEMA.some((s) => RESTART_KEYS.has(s.k) && String(this.cfg[s.k]) !== String(this._savedCfg && this._savedCfg[s.k]));
    },

    _schedule() {
      clearTimeout(this._t);
      this._t = setTimeout(() => this._save(), DEBOUNCE_MS);
    },

    async _save() {
      try {
        const back = await _api.setConfig(this.cfg);
        // 用后端读回值 (含 ENV override) 校正内存 cfg
        this.cfg = SCHEMA.reduce((o, s) => { o[s.k] = back[s.k]; return o; }, {});
        this._savedCfg = { ...this.cfg };
        this.yamlText = dumpYaml(this.cfg);
        this._checkRestart();
        this._flash("已保存", false);
      } catch (e) {
        this._flash("保存失败: " + ((e && e.message) || e), true);
      }
    },

    _flash(msg, err) {
      clearTimeout(this._ft);
      this._toastMsg = msg; this._toastErr = err;
      this._renderToast();
      this._ft = setTimeout(() => { this._toastMsg = ""; this._renderToast(); }, 2400);
    },
    _renderToast() {
      let el = host.querySelector(".cfg-toast");
      if (!this._toastMsg) { if (el) el.remove(); return; }
      if (!el) { el = document.createElement("div"); el.className = "cfg-toast"; host.appendChild(el); }
      el.textContent = this._toastMsg;
      el.classList.toggle("err", !!this._toastErr);
    },

    close() {
      clearTimeout(this._t);
      // ponytail: 关闭前冲一次未落盘改动 (有 _savedCfg 且与内存不同 → 立即 POST, 不等 debounce)
      try { app.unmount(); } catch (_) {}
      host.remove();
      _open = false;
    },
  });

  app.mount(host);
}

// 自检 (ponytail): dump→parse 往返保真 — node --input type=module 跑时验证。
// ponytail: 不引框架, 一组 assert 验证双 Tab 同步核心逻辑不破。
export function _selftest() {
  const src = { max_active: 3, max_parallel: 1, auto_commit: false, use_worktree: true,
    worktree_root: ".wt", retain_days: 0, board_theme: "skein", web_serve: false, board_open: true };
  const y = dumpYaml(src);
  const back = parseYaml(y);
  const ok = SCHEMA.every((s) => Object.prototype.hasOwnProperty.call(back, s.k) && String(back[s.k]) === String(src[s.k]));
  console.log(ok ? "config-modal selftest OK" : "config-modal selftest FAIL");
  console.log(JSON.stringify(back));
  return ok;
}
