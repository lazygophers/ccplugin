// SKEIN webapp · archive 归档页 (htm 重写版, 替旧 petite-vue)。
// 纯只读历史: api.archive() 拉归档列表 → 卡片列表 + 搜索/状态筛选 (本地态, 不需服务端)。
// onLive 仅订阅 reload (整页刷) — 归档是历史快照, task-changed 与本页无关。
//
// page 契约: render(mount, params, ctx); ctx = { api, md, h, onLive, navigate }

const BADGE = {
  "待处理": "ocean", "就绪": "ocean", "进行中": "gold", "运行中": "gold",
  "检查中": "ocean", "已完成": "success", "失败": "danger",
};
const tagKind = (st) => BADGE[st] || "ocean";
const STATUSES = ["", "已完成", "失败", "待处理", "进行中", "检查中"];

const ERR_ICON = '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>';
const EMPTY_ICON = '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="5" rx="1"/><path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8"/><line x1="10" y1="12" x2="14" y2="12"/></svg>';
const NO_MATCH_ICON = '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>';

// finished: Unix epoch 秒 → 本地日期串; 无则回落 archivedAt
function finishedLabel(a) {
  if (a.finished) {
    const d = new Date(a.finished * 1000);
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  }
  return a.archivedAt || "—";
}

export async function render(mount, params, ctx) {
  const { api, onLive, h } = ctx;

  let items = [];
  let loadErr = "";
  let q = "";
  let statusFilter = "";
  let unsub = null;

  async function fetchList() {
    try {
      const list = (await api.archive()) || [];
      // finished 倒序 (最近归档在前); 无 finished 沉底
      list.sort((x, y) => (y.finished || 0) - (x.finished || 0));
      items = list;
      loadErr = "";
    } catch (e) {
      items = [];
      loadErr = (e && e.message) || String(e);
    }
  }

  function filtered() {
    const ql = q.trim().toLowerCase();
    return items.filter((a) => {
      if (statusFilter && a.status !== statusFilter) return false;
      if (!ql) return true;
      return String(a.id).toLowerCase().includes(ql) ||
             (a.name || "").toLowerCase().includes(ql) ||
             (a.desc || "").toLowerCase().includes(ql);
    });
  }

  function emptyBox(icon, msg) {
    return h("div", { class: "antd-card p-10 text-center text-muted" },
      h("div", { class: "empty-ico opacity-60 mb-2", html: icon }),
      h("div", { class: "text-sm", style: { color: "var(--st-failed)" } }, msg)
    );
  }

  function bigEmpty(icon, msg) {
    return h("div", { class: "antd-card p-16 text-center text-muted" },
      h("div", { class: "empty-ico opacity-60 mb-2", html: icon }),
      h("div", { class: "text-sm" }, msg)
    );
  }

  // 归档卡片
  function archiveCard(a) {
    return h("a", {
      href: "/task?id=" + encodeURIComponent(a.id),
      class: "antd-card antd-card.hoverable block hover:bg-[var(--line)] transition-colors"
    },
      h("div", { class: "flex items-center gap-2 flex-wrap" },
        h("code", { class: "text-xs px-1.5 py-0.5 rounded",
          style: { background: "var(--line)", color: "var(--head)" } }, a.id),
        h("span", { class: "text-sm font-medium", style: { color: "var(--head)" } }, a.name || a.id),
        h("span", { class: "antd-tag " + tagKind(a.status) + " text-[11px]" }, a.status || "已完成"),
        h("span", { class: "antd-tag success text-[11px] opacity-70" }, "已归档"),
        h("span", { class: "flex-1" }),
        h("span", { class: "text-[11px] text-muted shrink-0" }, finishedLabel(a))
      ),
      a.desc
        ? h("p", { class: "text-xs text-muted mt-1.5 whitespace-pre-wrap line-clamp-2" }, a.desc)
        : null,
      h("div", { class: "text-[11px] text-muted mt-2" }, (a.subs || 0) + " 个子任务")
    );
  }

  function renderBody() {
    mount.innerHTML = "";

    if (loadErr) {
      mount.appendChild(h("div", { class: "px-7" }, emptyBox(ERR_ICON, loadErr)));
      return;
    }

    if (!items.length) {
      mount.appendChild(h("div", { class: "px-7" },
        bigEmpty(EMPTY_ICON, "暂无归档 — 完成的 task 超保留期后会自动归档到这里。")
      ));
      return;
    }

    const flt = filtered();

    // 头部: 标题 + 计数
    const header = h("div", { class: "flex items-center gap-2 mb-4 px-1" },
      h("h1", { class: "text-lg font-semibold", style: { color: "var(--head)" } }, "归档"),
      h("span", { class: "text-xs text-muted" }, flt.length + "/" + items.length)
    );

    // 搜索 + 状态筛选 (事件直接绑 input → 重渲染列表区, 头/控件不重渲染保焦点)
    const searchInput = h("input", {
      type: "search", placeholder: "搜索 id / 名称 / 描述…", value: q,
      class: "antd-input flex-1 min-w-[12rem] py-1.5",
      oninput: (e) => { q = e.target.value; rerenderList(); }
    });
    const sel = h("select", {
      class: "antd-select py-1.5 w-auto",
      onchange: (e) => { statusFilter = e.target.value; rerenderList(); }
    }, ...STATUSES.map((s) => {
      const opt = document.createElement("option");
      opt.value = s;
      opt.textContent = s || "全部状态";
      if (s === statusFilter) opt.selected = true;
      return opt;
    }));
    const controls = h("div", { class: "flex items-center gap-2 mb-3 px-1 flex-wrap" },
      searchInput, sel);

    // 列表容器 (后续 rerenderList 只刷这里, 保搜索/筛选焦点)
    const listWrap = h("div", { class: "space-y-2" });
    function rerenderList() {
      listWrap.innerHTML = "";
      const flt = filtered();
      // 同步头/控件计数
      const counter = header.querySelector("span.text-muted");
      if (counter) counter.textContent = flt.length + "/" + items.length;

      if (!flt.length) {
        listWrap.appendChild(bigEmpty(NO_MATCH_ICON, "无匹配结果 — 调整搜索词或状态筛选后重试。"));
        return;
      }
      flt.forEach((a) => listWrap.appendChild(archiveCard(a)));
    }
    rerenderList();

    mount.appendChild(h("div", { class: "px-7" }, header, controls, listWrap));
  }

  await fetchList();
  renderBody();

  // ponytail: archive 是只读历史快照 — 仅订阅 reload (资产变更 → 整页重拉), 不订 task-changed。
  // 软刷 = 重拉数据 + 重渲染 (搜索/筛选本地态不持久, 用户可重新输入, 接受)。
  if (onLive) {
    unsub = onLive(async () => {
      await fetchList();
      renderBody();
    });
  }
}
