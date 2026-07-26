// SKEIN webapp · dashboard 概览页 (htm 重写版, 替旧 petite-vue)。
// 纯只读: api.dashboard() 拉全 → KPI 墙 + 状态分布 + 5 区 (subtask: 进行中/就绪; task: 执行中/检查中/就绪/待plan)。
// onLive 软刷 (无本地交互态可丢) → 整体重挂; cleanups 退订 (router 切页自动退订)。
//
// page 契约: render(mount, params, ctx); ctx = { api, md, h, onLive, navigate }
//   core `frontend/soft-refresh-pattern`: page 末尾 onLive(mountApp) 订阅, router 切页自动退订。

// 状态中文 → --st-* 色令牌 (与旧 dashboard 同映射)
const ST_VAR = {
  "待处理": "--st-pending", "就绪": "--st-pending", "进行中": "--st-active", "运行中": "--st-active",
  "检查中": "--st-check", "已完成": "--st-done", "失败": "--st-failed",
};
const stColor = (st) => `var(${ST_VAR[st] || "--st-pending"})`;
const DOT_CLS = {
  "待处理": "pending", "就绪": "pending", "进行中": "active", "运行中": "active",
  "检查中": "check", "已完成": "done", "失败": "failed",
};
// 固定状态序, 只留计数>0
const ST_ORDER = ["进行中", "运行中", "检查中", "就绪", "待处理", "已完成", "失败"];
function segments(dist) {
  const d = dist || {};
  const total = Object.values(d).reduce((a, b) => a + b, 0);
  const segs = ST_ORDER.filter((k) => d[k] > 0).map((k) => ({
    label: k, count: d[k], color: stColor(k), dot: DOT_CLS[k],
    pct: total ? (d[k] / total) * 100 : 0,
  }));
  return { total, segs };
}

const C = 2 * Math.PI * 26;  // 完成率环周长 (r=26)
const fmtDur = (mins) => mins == null ? "-" : (mins < 60 ? mins + "m" : Math.floor(mins / 60) + "h" + String(mins % 60).padStart(2, "0") + "m");

const ERR_ICON = '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>';
const EMPTY_ICON = '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="9" x2="20" y2="9"/><line x1="4" y1="15" x2="20" y2="15"/><line x1="10" y1="3" x2="8" y2="21"/><line x1="16" y1="3" x2="14" y2="21"/></svg>';

// 工厂: buildUI(h) 返回一组以 h 构造 DOM 的闭包函数 — 解决「h 经 ctx 注入但子函数要透传」噪声。
function buildUI(h) {
  function emptyBox(icon, msg, sub) {
    return h("div", { class: "antd-card p-10 text-center text-muted" },
      h("div", { class: "empty-ico opacity-60 mb-2", html: icon }),
      h("div", { class: "text-sm", style: { color: "var(--st-failed)" } }, msg),
      sub ? h("div", { class: "text-xs mt-1 opacity-70" }, sub) : null
    );
  }

  // KPI 卡 (完成率环 / 活跃数 / 任务总数 / 织入进度)
  function kpiCard(st) {
    const ring = C * (1 - (st.doneRate || 0) / 100);
    return h("section", { class: "grid grid-cols-2 md:grid-cols-4 gap-3 mb-4" },
      h("div", { class: "antd-card antd-card.hoverable flex items-center gap-3" },
        h("svg", { width: "64", height: "64", viewBox: "0 0 64 64", class: "shrink-0 -rotate-90" },
          h("circle", { cx: "32", cy: "32", r: "26", fill: "none", stroke: "var(--line)", "stroke-width": "7" }),
          h("circle", { cx: "32", cy: "32", r: "26", fill: "none", stroke: "var(--st-done)",
            "stroke-width": "7", "stroke-linecap": "round",
            "stroke-dasharray": String(C), "stroke-dashoffset": String(ring) })
        ),
        h("div", {},
          h("div", { class: "text-xl font-semibold", style: { color: "var(--head)" } }, (st.doneRate || 0) + "%"),
          h("div", { class: "text-xs text-muted" }, "完成率")
        )
      ),
      h("div", { class: "antd-card antd-card.hoverable" },
        h("div", { class: "text-2xl font-semibold stat-n", style: { color: "var(--st-active)" },
          "data-count": String(st.activeCount || 0) }, String(st.activeCount || 0)),
        h("div", { class: "text-xs text-muted mt-1" }, "编织中")
      ),
      h("div", { class: "antd-card antd-card.hoverable" },
        h("div", { class: "text-2xl font-semibold stat-n", style: { color: "var(--head)" },
          "data-count": String(st.taskCount || 0) }, String(st.taskCount || 0)),
        h("div", { class: "text-xs text-muted mt-1" }, "任务总数 (task)")
      ),
      // 织入进度: bg-wave-bar 蓝金流光 (design.css:251-263, 替旧 .skein-bar)
      h("div", { class: "antd-card antd-card.hoverable" },
        h("div", { class: "text-2xl font-semibold", style: { color: "var(--head)" } }, (st.combinedPct || 0) + "%"),
        h("div", { class: "text-xs text-muted mt-1" }, "织入进度"),
        h("div", { class: "mt-2 bg-wave-bar active" },
          h("div", { class: "fill", style: { width: (st.combinedPct || 0) + "%" } })
        )
      )
    );
  }

  // 状态分布: 任务级 + 子任务级分段条 + 状态点
  function distPanel(dists) {
    return h("section", { class: "antd-card p-5 mb-4" },
      h("div", { class: "text-sm font-semibold mb-3", style: { color: "var(--head)" } }, "状态分布 · 状态段分布"),
      ...dists.map((row) =>
        h("div", { class: "flex items-start gap-4 py-2 border-t first:border-t-0", style: { borderColor: "var(--line)" } },
          h("div", { class: "w-20 shrink-0" },
            h("div", { class: "text-xs font-semibold", style: { color: "var(--head)" } }, row.label),
            h("div", { class: "text-xs text-muted mt-0.5" }, row.total + " 项")
          ),
          h("div", { class: "flex-1" },
            row.total === 0
              ? h("div", { class: "text-xs text-muted py-1" }, "无数据")
              : h("div", {},
                  h("div", { class: "flex h-3 rounded overflow-hidden", style: { background: "var(--line)" } },
                    ...row.segs.map((s) =>
                      h("div", { title: s.label + " " + s.count,
                        style: { width: s.pct + "%", background: s.color } })
                    )
                  ),
                  h("div", { class: "flex flex-wrap gap-x-3 gap-y-1.5 mt-2.5" },
                    ...row.segs.map((s) =>
                      h("div", { class: "inline-flex items-center gap-1.5", title: s.label + " " + s.count },
                        h("span", { class: "dot dot-" + s.dot }),
                        h("span", { class: "text-xs text-muted" },
                          s.label + " ",
                          h("span", { style: { color: "var(--head)" } }, String(s.count))
                        )
                      )
                    )
                  )
                )
          )
        )
      )
    );
  }

  // 5 区列表 (subtask: 进行中+就绪; task: 执行中+检查中+就绪+待plan)
  function listsPanel(st) {
    const secLabel = (label, count) =>
      h("div", { class: "text-xs font-semibold text-muted mt-3 mb-1.5 flex items-center gap-2" },
        label, h("span", { class: "antd-tag ocean" }, String(count)));
    const emptyHint = (txt) =>
      h("div", { class: "text-xs text-muted py-1.5 opacity-70" }, txt);

    const subLink = (s, kind) => {
      const base = "block rounded px-3 py-2 hover:bg-[var(--line)] transition-colors text-sm";
      const cls = kind === "running" ? base + " border-l-2 border-[var(--st-active)]" :
                  kind === "ready" ? base + " border-l-2 border-[var(--st-pending)]" : base;
      return h("a", { href: "/task?id=" + encodeURIComponent(s.tid), class: cls },
        h("div", { class: "flex items-baseline gap-2" },
          h("span", { class: "truncate flex-1", style: { color: "var(--head)" } }, s.name || s.sid),
          h("code", { class: "text-[11px] text-muted shrink-0" }, s.tid + "/" + s.sid)
        ),
        h("div", { class: "text-[11px] text-muted mt-0.5 flex items-center gap-2" },
          h("span", {}, s.agent || "skein-executor"),
          kind === "running" ? h("span", {}, "耗时 " + fmtDur(s.elapsed)) : null,
          kind === "ready" ? h("span", { class: "antd-tag ocean text-[10px] py-0" }, "就绪") : null
        )
      );
    };

    const taskLink = (t, kind) => {
      const colorMap = { active: "var(--st-active)", check: "var(--st-check)",
                         ready: "var(--st-pending)", plan: "var(--st-pending)" };
      return h("a", { href: "/task?id=" + encodeURIComponent(t.id),
        class: "block rounded px-3 py-2 hover:bg-[var(--line)] transition-colors text-sm border-l-2",
        style: { borderLeftColor: colorMap[kind] || "var(--st-active)" } },
        h("div", { class: "flex items-baseline gap-2" },
          h("span", { class: "truncate flex-1", style: { color: "var(--head)" } }, t.name || t.id),
          h("code", { class: "text-[11px] text-muted shrink-0" }, t.id)
        ),
        h("div", { class: "text-[11px] text-muted mt-0.5 flex items-center gap-2 flex-wrap" },
          kind === "active" || kind === "check"
            ? h("span", {}, (t.sdone || 0) + "/" + (t.stotal || 0) + " · " + (t.pct || 0) + "% · 耗时 " + fmtDur(t.elapsed))
            : null,
          kind === "ready"
            ? h("span", {}, "前置 " + ((t.deps && t.deps.length) || "-"))
            : null,
          kind === "plan"
            ? h("span", {}, "subtask " + (t.subCount || 0))
            : null,
          kind === "plan" && !t.subCount
            ? h("span", { class: "antd-tag warning text-[10px] py-0" }, "未拆")
            : null
        )
      );
    };

    return h("section", { class: "grid grid-cols-1 md:grid-cols-2 gap-4" },
      h("div", { class: "antd-card p-5" },
        h("h2", { class: "text-sm font-semibold mb-2", style: { color: "var(--head)" } }, "Subtask"),
        secLabel("进行中", st.runningSubs.length),
        st.runningSubs.length ? st.runningSubs.map((s) => subLink(s, "running")) : emptyHint("无进行中"),
        secLabel("就绪", st.readySubs.length),
        st.readySubs.length ? st.readySubs.map((s) => subLink(s, "ready")) : emptyHint("无就绪")
      ),
      h("div", { class: "antd-card p-5" },
        h("h2", { class: "text-sm font-semibold mb-2", style: { color: "var(--head)" } }, "Task"),
        secLabel("执行中", st.activeTasks.length),
        st.activeTasks.length ? st.activeTasks.map((t) => taskLink(t, "active")) : emptyHint("无执行中"),
        secLabel("检查中", st.checkTasks.length),
        st.checkTasks.length ? st.checkTasks.map((t) => taskLink(t, "check")) : emptyHint("无检查中"),
        secLabel("就绪", st.readyTasks.length),
        st.readyTasks.length ? st.readyTasks.map((t) => taskLink(t, "ready")) : emptyHint("无就绪"),
        secLabel("待 plan", st.toPlanTasks.length),
        st.toPlanTasks.length ? st.toPlanTasks.map((t) => taskLink(t, "plan")) : emptyHint("无待 plan")
      )
    );
  }

  return { emptyBox, kpiCard, distPanel, listsPanel };
}

export async function render(mount, params, ctx) {
  const { api, onLive, h } = ctx;
  const ui = buildUI(h);

  async function fetchState() {
    try {
      const r = await api.dashboard();
      return {
        loadErr: "", proj: r.proj || "", taskCount: r.taskCount || 0, doneRate: r.doneRate || 0,
        activeCount: r.activeCount || 0, combinedPct: r.combinedPct || 0,
        runningSubs: r.runningSubs || [], readySubs: r.readySubs || [],
        readyTasks: r.readyTasks || [], toPlanTasks: r.toPlanTasks || [],
        activeTasks: r.activeTasks || [], checkTasks: r.checkTasks || [],
        dists: [
          Object.assign({ key: "task", label: "任务级" }, segments(r.statusDist)),
          Object.assign({ key: "sub", label: "子任务级" }, segments(r.subStatusDist)),
        ],
      };
    } catch (e) {
      return {
        loadErr: (e && e.message) || String(e), proj: "", taskCount: 0, doneRate: 0,
        activeCount: 0, combinedPct: 0,
        runningSubs: [], readySubs: [], readyTasks: [], toPlanTasks: [],
        activeTasks: [], checkTasks: [], dists: [],
      };
    }
  }

  async function mountApp() {
    const st = await fetchState();
    mount.innerHTML = "";
    let body;
    if (st.loadErr) {
      body = ui.emptyBox(ERR_ICON, st.loadErr);
    } else if (!st.taskCount) {
      body = ui.emptyBox(EMPTY_ICON, "空", "用 skein create 创建第一个任务。");
    } else {
      body = h("div", {},
        ui.kpiCard(st),
        ui.distPanel(st.dists),
        ui.listsPanel(st)
      );
    }
    mount.appendChild(h("div", { class: "wrap px-7" },
      h("div", { class: "eyebrow" }, "总览"),
      h("div", { class: "page-head mb-4" },
        h("h1", { class: "text-lg font-semibold", style: { color: "var(--head)" } },
          (st.proj || "SKEIN") + " 总览"),
        h("p", { class: "text-xs text-muted mt-0.5" }, "完成进度 · 实时统计")
      ),
      body
    ));
  }

  await mountApp();
  // ponytail: 软刷整体重挂 — dashboard 无本地交互态可丢, 无需精细 diff。
  onLive && onLive(mountApp);
}
