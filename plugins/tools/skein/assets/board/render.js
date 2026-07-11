// SKEIN 看板渲染器: 运行时 fetch task.json + task/<id>/task.json 客户端渲染。
// 需经 http 访问 (skein view 起本地 server); file:// 双击 fetch 被 CORS 拦。
// 逻辑对齐 skein.py 旧 _board_html (状态/进度/DAG/子表一一对应)。
(function () {
  var S_PENDING = "待处理", S_ACTIVE = "进行中", S_CHECK = "检查中", S_DONE = "已完成";
  var SS_DONE = "已完成", SS_RUNNING = "运行中", SS_FAILED = "失败";
  var stCls = {}; stCls[S_PENDING] = "s-pending"; stCls[S_ACTIVE] = "s-active"; stCls[S_CHECK] = "s-check"; stCls[S_DONE] = "s-done";
  var ssCls = {}; ssCls["待处理"] = "ss-pending"; ssCls[SS_RUNNING] = "ss-running"; ssCls[SS_DONE] = "ss-done"; ssCls[SS_FAILED] = "ss-failed";
  var nodeVar = {}; nodeVar[S_PENDING] = "--st-pending"; nodeVar[S_ACTIVE] = "--st-active"; nodeVar[S_CHECK] = "--st-check"; nodeVar[S_DONE] = "--st-done"; nodeVar[SS_RUNNING] = "--st-active"; nodeVar[SS_FAILED] = "--st-failed";

  function esc(s) { return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
  function badge(text, map) { return '<span class="badge ' + (map[text] || "") + '">' + esc(text) + '</span>'; }
  function fmtDur(m) { if (m == null) return "-"; return m < 60 ? m + "m" : Math.floor(m / 60) + "h" + String(m % 60).padStart(2, "0") + "m"; }
  function bar(pct, sub, cls) {
    var c = "bar" + (sub ? " sub" : "") + (cls ? " " + cls : "");
    return '<div class="' + c + '"><div class="fill" style="width:' + Math.min(pct, 100) + '%"></div><span class="pct">' + pct + '%</span></div>';
  }

  function dagHtml(nodes) {
    if (nodes.length < 2) return "";
    var ids = {}, order = {}, smap = {};
    nodes.forEach(function (n, k) { ids[n[0]] = 1; order[n[0]] = k; smap[n[0]] = n; });
    var dep = {};
    nodes.forEach(function (n) { dep[n[0]] = n[3].filter(function (d) { return ids[d]; }); });
    var layer = {};
    function depth(i, seen) {
      if (layer[i] != null) return layer[i];
      if (seen[i]) return 0;
      var s2 = Object.assign({}, seen); s2[i] = 1;
      var mx = -1; dep[i].forEach(function (p) { mx = Math.max(mx, depth(p, s2)); });
      layer[i] = 1 + mx; return layer[i];
    }
    Object.keys(ids).forEach(function (i) { depth(i, {}); });
    var layers = {};
    Object.keys(layer).forEach(function (i) { (layers[layer[i]] = layers[layer[i]] || []).push(i); });
    Object.keys(layers).forEach(function (d) { layers[d].sort(function (a, b) { return order[a] - order[b]; }); });
    var COL = 170, ROW = 56, NW = 140, NH = 40, pos = {};
    Object.keys(layers).forEach(function (d) { layers[d].forEach(function (i, r) { pos[i] = [d * COL + 10, r * ROW + 10]; }); });
    var lNums = Object.keys(layers).map(Number);
    var W = (Math.max.apply(null, lNums) + 1) * COL + 10;
    var H = Math.max.apply(null, Object.keys(layers).map(function (d) { return layers[d].length; })) * ROW + 10;
    var lines = "", boxes = "";
    Object.keys(ids).forEach(function (i) {
      var x2 = pos[i][0], y2 = pos[i][1], ey = y2 + NH / 2;
      dep[i].forEach(function (p) {
        var x1 = pos[p][0], y1 = pos[p][1], sx = x1 + NW, sy = y1 + NH / 2, mx = (sx + x2) / 2;
        lines += '<path d="M' + sx + ',' + sy + ' C' + mx + ',' + sy + ' ' + mx + ',' + ey + ' ' + (x2 - 2) + ',' + ey + '" fill="none" stroke="var(--muted)" stroke-width="1.5"/>'
          + '<polygon points="' + (x2 - 8) + ',' + (ey - 4) + ' ' + x2 + ',' + ey + ' ' + (x2 - 8) + ',' + (ey + 4) + '" fill="var(--muted)"/>';
      });
    });
    Object.keys(ids).forEach(function (i) {
      var x = pos[i][0], y = pos[i][1], n = smap[i], nm = n[1], stt = n[2];
      var nm2 = nm.length > 10 ? nm.slice(0, 9) + "…" : nm;
      boxes += '<g><rect x="' + x + '" y="' + y + '" width="' + NW + '" height="' + NH + '" rx="6" fill="var(--bg)" stroke="var(--brd)"/>'
        + '<rect x="' + x + '" y="' + y + '" width="4" height="' + NH + '" rx="2" fill="var(' + (nodeVar[stt] || "--muted") + ')"/>'
        + '<text x="' + (x + 12) + '" y="' + (y + 17) + '" font-size="12" fill="var(--fg)">' + esc(n[0]) + '</text>'
        + '<text x="' + (x + 12) + '" y="' + (y + 31) + '" font-size="10" fill="var(--muted)">' + esc(nm2) + '</text></g>';
    });
    return '<svg class="dag" viewBox="0 0 ' + W + ' ' + H + '" width="' + W + '" height="' + H + '" xmlns="http://www.w3.org/2000/svg">' + lines + boxes + '</svg>';
  }

  function render(tasks) {
    var tnow = Math.floor(Date.now() / 1000);
    var nameOf = {}; tasks.forEach(function (t) { nameOf[t.id] = t.name || t.id; });
    function elapsedOf(t) { return Math.round(((t.updated == null ? tnow : t.updated) - (t.created == null ? tnow : t.created)) / 60); }

    var cnt = {}, fracs = [], estTotal = 0, elapsedTotal = 0, wsum = 0, wdone = 0, remainEst = 0;
    tasks.forEach(function (t) {
      cnt[t.status] = (cnt[t.status] || 0) + 1;
      var frac;
      if (t.status === S_DONE) frac = 1;
      else { var subs = t.subtasks || []; frac = subs.length ? subs.filter(function (s) { return s.status === SS_DONE; }).length / subs.length : 0; }
      fracs.push(frac);
      var est = t.estimate || 0;
      estTotal += est; elapsedTotal += elapsedOf(t);
      var w = est || 60; wsum += w; wdone += w * frac; remainEst += est * (1 - frac);
    });
    var overall = fracs.length ? Math.round(fracs.reduce(function (a, b) { return a + b; }, 0) / fracs.length * 100) : 0;
    var weighted = wsum ? Math.round(wdone / wsum * 100) : overall;
    var chips = Object.keys(cnt).map(function (k) { return badge(k, stCls) + " " + cnt[k]; }).join(" ") || "-";
    var taskNodes = tasks.map(function (t) { return [t.id, t.name || t.id, t.status, t.deps || []]; });
    var overview = '<section class="card"><h2>任务进展</h2>'
      + '<p class="meta">' + tasks.length + ' task · ' + chips + '</p>'
      + '<p class="meta">预期合计 ' + fmtDur(estTotal || null) + ' · 已耗 ' + fmtDur(elapsedTotal || null) + ' · 剩余预估 ' + fmtDur(Math.round(remainEst) || null) + '</p>'
      + '<p class="meta">综合完成率</p>' + bar(overall)
      + '<p class="meta">预估加权完成率</p>' + bar(weighted, false, "est")
      + dagHtml(taskNodes) + '</section>';

    var cards = tasks.map(function (t) {
      var subs = t.subtasks || [];
      var snameOf = {}; subs.forEach(function (s) { snameOf[s.sid] = s.name || s.sid; });
      var sdone = subs.filter(function (s) { return s.status === SS_DONE; }).length;
      var spct = subs.length ? Math.round(sdone / subs.length * 100) : 0;
      var elapsed = elapsedOf(t), est = t.estimate;
      var timeBar = est ? '<p class="meta">时间 ' + fmtDur(elapsed) + '/' + fmtDur(est) + '</p>' + bar(Math.round(elapsed / est * 100), false, "time" + (elapsed > est ? " over" : "")) : "";
      var snodes = subs.map(function (s) { return [s.sid, s.name || s.sid, s.status, s.depends_on || []]; });
      var srows = subs.map(function (s) {
        return '<tr><td>' + esc(s.sid) + '</td><td>' + esc(s.name) + '</td>'
          + '<td>' + badge(s.status, ssCls) + '</td>'
          + '<td>' + esc(fmtDur(s.estimate == null ? null : s.estimate)) + '</td>'
          + '<td>' + esc(s.agent || "general-purpose") + '</td>'
          + '<td>' + esc((s.skills || []).join(",") || "-") + '</td>'
          + '<td>' + esc((s.depends_on || []).map(function (d) { return snameOf[d] || d; }).join(", ") || "-") + '</td>'
          + '<td>' + esc((s.write || []).join(",") || "-") + '</td>'
          + '<td>' + esc(s.reason || "-") + '</td></tr>';
      }).join("");
      var subtable = subs.length
        ? '<table><thead><tr><th>sid</th><th>名称</th><th>状态</th><th>预期</th><th>agent</th><th>skills</th><th>依赖</th><th>写文件</th><th>reason</th></tr></thead><tbody>' + srows + '</tbody></table>'
        : '<p class="empty">无 subtask</p>';
      return '<section class="card"><h2>' + esc(t.id) + ' ' + badge(t.status, stCls) + '</h2>'
        + '<p class="name">' + esc(t.name || "") + '</p>'
        + '<p class="meta">前置: ' + esc((t.deps || []).map(function (d) { return nameOf[d] || d; }).join(", ") || "-") + ' · '
        + 'worktree: ' + esc(t.worktree || "-") + ' · '
        + '耗时 ' + fmtDur(elapsed) + ' / 预期 ' + fmtDur(est == null ? null : est) + '</p>'
        + timeBar
        + '<p class="meta">子任务 ' + sdone + '/' + subs.length + '</p>' + bar(spct, true)
        + dagHtml(snodes)
        + subtable + '</section>';
    });
    document.getElementById("board").innerHTML = overview + (cards.length ? cards.join("") : '<p class="empty">无 task</p>');
  }

  // 默认主题: 若用户未在 switcher 里选过 (无 localStorage), 用 view-config.json 的配置作默认
  fetch("board/view-config.json").then(function (r) { return r.json(); }).then(function (c) {
    ["theme", "palette", "mode"].forEach(function (k) {
      if (!localStorage.getItem("skein-" + k) && c[k]) {
        document.documentElement.setAttribute("data-" + k, c[k]);
        var sel = document.getElementById("sw-" + k); if (sel) sel.value = c[k];
      }
    });
  }).catch(function () {});

  fetch("task.json").then(function (r) { return r.json(); }).then(function (idx) {
    return Promise.all((idx.tasks || []).map(function (t) {
      return fetch("task/" + encodeURIComponent(t.id) + "/task.json").then(function (r) { return r.json(); });
    }));
  }).then(render).catch(function (e) {
    document.getElementById("board").innerHTML = '<p class="empty">加载失败: ' + esc(e.message) + '<br>需经 <code>skein view</code> 起本地 http server 访问 (file:// 双击 fetch 被浏览器拦)。</p>';
  });
})();
