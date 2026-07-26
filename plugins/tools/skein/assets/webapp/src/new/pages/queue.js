// SKEIN webapp · queue 队列页 (htm 重写版, 替旧 petite-vue)。
// 三区只读视图: (1) 进行中 (activeTasks + runningSubs) (2) 就绪 task (3) 就绪 subtask (4) 待执行总览 (pendingQueue)。
// onLive 软刷 (无本地交互态可丢) → 整体重挂; cleanups 退订。
//
// page 契约: render(mount, params, ctx); ctx = { api, md, h, onLive, navigate }

const BADGE = {
  "待处理": "ocean", "就绪": "ocean", "进行中": "gold", "运行中": "gold",
  "检查中": "ocean", "已完成": "success", "失败": "danger",
};
const tagKind = (st) => BADGE[st] || "ocean";

const ERR_ICON = '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>';
const CLEAR_ICON = '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>';

function buildUI(h) {
  function emptyBox(icon, msg) {
    return h("div", { class: "antd-card p-10 text-center text-muted" },
      h("div", { class: "empty-ico opacity-60 mb-2", html: icon }),
      h("div", { class: "text-sm", style: { color: "var(--st-failed)" } }, msg)
    );
  }

  function sectionHead(color, label, count, hint) {
    return h("div", { class: "flex items-center gap-2 mb-3" },
      h("span", { class: "w-2 h-2 rounded-full", style: { background: color } }),
      h("h2", { class: "text-sm font-semibold", style: { color: "var(--head)" } }, label),
      h("span", { class: "text-xs text-muted" }, String(count || 0)),
      hint ? h("span", { class: "text-[11px] text-muted" }, hint) : null
    );
  }

  // active task 行 (进度条 + sdone/stotal + pct + elapsed)
  function activeTaskRow(t) {
    return h("a", {
      href: "/task?id=" + encodeURIComponent(t.id),
      class: "flex items-center gap-2 rounded p-2 hover:bg-[var(--line)] transition-colors text-sm",
      style: { border: "1px solid var(--line)" }
    },
      h("code", { class: "text-[11px] text-muted shrink-0" }, t.id),
      h("span", { class: "truncate flex-1", style: { color: "var(--head)" } }, t.name),
      h("span", { class: "antd-tag " + tagKind(t.status) + " text-[11px] shrink-0" }, t.status),
      h("div", { class: "flex-1 flex items-center gap-2 max-w-[200px]" },
        h("div", { class: "antd-progress-track flex-1" },
          h("div", { class: "antd-progress-fill", style: { width: (t.pct || 0) + "%" } })
        ),
        h("span", { class: "text-[11px] text-muted w-9 text-right" }, (t.pct || 0) + "%")
      ),
      h("span", { class: "text-[11px] text-muted shrink-0" }, (t.sdone || 0) + "/" + (t.stotal || 0)),
      h("span", { class: "text-[11px] text-muted shrink-0" }, t.elapsed != null ? t.elapsed + "m" : "-")
    );
  }

  // running subtask 行 (tid/sid + 名 + agent + elapsed)
  function runningSubRow(s) {
    return h("a", {
      href: "/task?id=" + encodeURIComponent(s.tid),
      class: "flex items-center gap-2 rounded p-2 hover:bg-[var(--line)] transition-colors text-sm",
      style: { border: "1px solid var(--line)" }
    },
      h("span", { class: "w-1.5 h-1.5 rounded-full shrink-0 pulse-dot", style: { background: "var(--st-active)" } }),
      h("code", { class: "text-[11px] text-muted shrink-0" }, s.tid + "/" + s.sid),
      h("span", { class: "text-sm truncate flex-1", style: { color: "var(--head)" } }, s.name),
      h("span", { class: "flex-1" }),
      h("span", { class: "text-[11px] text-muted shrink-0" }, s.agent || "skein-executor"),
      h("span", { class: "text-[11px] text-muted shrink-0" }, s.elapsed != null ? s.elapsed + "m" : "-")
    );
  }

  // 就绪 task 行
  function readyTaskRow(t) {
    return h("a", {
      href: "/task?id=" + encodeURIComponent(t.id),
      class: "flex items-center gap-2 rounded p-2 hover:bg-[var(--line)] transition-colors text-sm",
      style: { border: "1px solid var(--line)" }
    },
      h("code", { class: "text-[11px] text-muted shrink-0" }, t.id),
      h("span", { class: "truncate flex-1", style: { color: "var(--head)" } }, t.name),
      h("span", { class: "flex-1" }),
      (t.deps && t.deps.length)
        ? h("span", { class: "text-[11px] text-muted shrink-0" }, "依赖 " + t.deps.join(", "))
        : null,
      h("span", { class: "text-[11px] text-muted shrink-0" }, (t.spct || 0) + "%")
    );
  }

  // 就绪 subtask (有序号 1..N)
  function readySubRow(s, idx) {
    return h("li", {
      class: "flex items-center gap-2 rounded p-2 cursor-default text-sm",
      style: { border: "1px solid var(--line)" }
    },
      h("span", { class: "text-[11px] text-muted w-5 text-right shrink-0 select-none" }, String(idx + 1)),
      h("a", {
        href: "/task?id=" + encodeURIComponent(s.tid),
        class: "shrink-0"
      }, h("code", { class: "text-[11px] text-muted" }, s.tid + "/" + s.sid)),
      h("span", { class: "truncate flex-1", style: { color: "var(--head)" } }, s.name),
      h("span", { class: "flex-1" }),
      (s.depends_on && s.depends_on.length)
        ? h("span", { class: "text-[11px] text-muted shrink-0" }, "依赖 " + s.depends_on.join(", "))
        : null,
      h("span", { class: "text-[11px] text-muted shrink-0" }, s.agent || "skein-executor")
    );
  }

  // pendingQueue 项 (ready 点 + tid/sid + 名 + agent)
  function queueRow(q) {
    return h("a", {
      href: "/task?id=" + encodeURIComponent(q.tid),
      class: "flex items-center gap-2 rounded p-2 hover:bg-[var(--line)] transition-colors text-sm",
      style: { border: "1px solid var(--line)" }
    },
      h("span", { class: "w-1.5 h-1.5 rounded-full shrink-0",
        style: { background: q.ready ? "var(--st-active)" : "var(--st-pending)" },
        title: q.ready ? "就绪" : "排队中" }),
      h("code", { class: "text-[11px] text-muted shrink-0" }, q.tid + "/" + q.sid),
      h("span", { class: "truncate flex-1", style: { color: "var(--head)" } }, q.name),
      h("span", { class: "flex-1" }),
      h("span", { class: "text-[11px] text-muted shrink-0" }, q.agent || "skein-executor")
    );
  }

  // 空态提示
  function emptyHint(msg) {
    return h("div", { class: "text-muted text-center py-6 text-sm" }, msg);
  }

  return { emptyBox, sectionHead, activeTaskRow, runningSubRow, readyTaskRow, readySubRow, queueRow, emptyHint };
}

export async function render(mount, params, ctx) {
  const { api, onLive, h } = ctx;
  const ui = buildUI(h);

  async function fetchState() {
    try {
      const r = await api.queue();
      return {
        loadErr: "", readyTasks: r.readyTasks || [],
        readySubtasks: r.readySubtasks || [], pendingQueue: r.pendingQueue || [],
        activeTasks: r.activeTasks || [], runningSubs: r.runningSubs || [],
      };
    } catch (e) {
      return {
        loadErr: (e && e.message) || String(e),
        readyTasks: [], readySubtasks: [], pendingQueue: [],
        activeTasks: [], runningSubs: [],
      };
    }
  }

  async function mountApp() {
    const st = await fetchState();
    mount.innerHTML = "";

    if (st.loadErr) {
      mount.appendChild(ui.emptyBox(ERR_ICON, st.loadErr));
      return;
    }

    const allEmpty = !st.activeTasks.length && !st.runningSubs.length &&
                     !st.readyTasks.length && !st.readySubtasks.length && !st.pendingQueue.length;
    if (allEmpty) {
      mount.appendChild(h("div", { class: "px-7" },
        h("div", { class: "antd-card p-16 text-center text-muted" },
          h("div", { class: "empty-ico opacity-60 mb-2", html: CLEAR_ICON }),
          h("div", { class: "text-sm" }, "队列已清空 — 无就绪 task、无待派 subtask。")
        )
      ));
      return;
    }

    const sections = [];

    // (0) 进行中: active task 行 + running subtask 行
    if (st.activeTasks.length || st.runningSubs.length) {
      sections.push(h("section", { class: "antd-card p-5 mb-4" },
        ui.sectionHead("var(--st-active)", "进行中", st.activeTasks.length + st.runningSubs.length,
                       "活跃 task 实时进度 + 正在跑的 subtask"),
        st.activeTasks.length
          ? h("div", { class: "space-y-1.5 mb-3" }, st.activeTasks.map(ui.activeTaskRow))
          : null,
        st.runningSubs.length
          ? h("div", { class: "space-y-1.5" }, st.runningSubs.map(ui.runningSubRow))
          : null
      ));
    }

    // (1) 就绪 task 批
    sections.push(h("section", { class: "antd-card p-5 mb-4" },
      ui.sectionHead("var(--st-pending)", "就绪 task 批", st.readyTasks.length,
                     "依赖已满足, 可 skein start"),
      st.readyTasks.length
        ? h("div", { class: "space-y-1.5" }, st.readyTasks.map(ui.readyTaskRow))
        : ui.emptyHint("无就绪 task")
    ));

    // (2) 就绪 subtask 调度序
    sections.push(h("section", { class: "antd-card p-5 mb-4" },
      ui.sectionHead("var(--st-active)", "就绪 subtask", st.readySubtasks.length,
                     "active task 内可立即 claim (调度序)"),
      st.readySubtasks.length
        ? h("ol", { class: "space-y-1.5 list-none p-0" },
            st.readySubtasks.map((s, i) => ui.readySubRow(s, i)))
        : ui.emptyHint("无就绪 subtask")
    ));

    // (3) 待执行总览 (双层调度序)
    sections.push(h("section", { class: "antd-card p-5" },
      ui.sectionHead("var(--ocean-mid)", "待执行总览", st.pendingQueue.length,
                     "全部未完成 subtask, 双层调度序"),
      st.pendingQueue.length
        ? h("div", { class: "space-y-1.5" }, st.pendingQueue.map(ui.queueRow))
        : ui.emptyHint("队列为空 — 无待派 subtask")
    ));

    mount.appendChild(h("div", { class: "px-7" }, ...sections));
  }

  await mountApp();
  // ponytail: 软刷整体重挂 — queue 无本地交互态可丢, 无需精细 diff。
  onLive && onLive(mountApp);
}
