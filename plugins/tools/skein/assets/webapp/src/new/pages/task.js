// ============================================================
//  Task — 任务详情
//  设计: 左元信息(基本信息/时间线/子任务列表/依赖/操作) + 右完整内容(描述/PRD/契约/子任务 DAG/设计/调研)
//  路由: /task/detail?id=<tid> — 参数一律 query, 禁 path 参数
//  状态: 规划中 / 待执行 / 执行中 / 验收中 / 已完成
// ============================================================

import { h, api, md, fmtRelative, fmtTime, normalizeTask, normalizeTasks,
         confirmDialog, alertDialog, buildTimeline, subTimelineView } from '../app.js';

const ST_LABEL = {
  planning: '规划中', ready: '待执行',
  active:   '执行中', check: '验收中',
  done:     '已完成', failed: '失败',
};
const ST_COLOR = {
  planning: 'st-planning', ready: 'st-ready',
  active:   'st-active',  check: 'st-check',
  done:     'st-done',    failed: 'st-failed',
};
const ST_ICON = {
  planning: 'fa-lightbulb-o', ready: 'fa-flag-o',
  active:   'fa-spinner fa-spin', check: 'fa-eye',
  done:     'fa-check-circle', failed: 'fa-times-circle',
};

// ---- 信息项 ----
function infoItem(label, value) {
  return h('div.flex.gap-3.py-2', [
    h('span.text-sm.text-muted.w-20.flex-shrink-0', label),
    h('div.text-sm.text-fg.flex-1', value || '—'),
  ]);
}

// ---- 时间线 (buildTimeline / subTimelineView 见 app.js, 与看板详情面板共用) ----

function timelineView(stages, task) {
  if (!stages || !stages.length) {
    return h('div.py-8.text-center.text-muted.text-sm', '暂无活动记录');
  }
  return h('div.tl-axis',
    stages.map((s, i) => {
      const stateClass = s.done ? 'done' : s.current ? 'cur' : '';
      const stClass = s.done ? 'done' : s.current ? 'cur' : 'pending';
      const stLabel = s.done ? '已完成' : s.current ? '当前' : '待执行';
      const dotStyle = (s.done || s.current) ? `--tl-c:${s.color}` : '';
      const stStyle = s.current ? `--tl-c:${s.color};--tl-c-bg:${s.color}26` : '';
      const timeStr = s.time ? fmtTime(s.time) : '—';

      // 子任务计数
      const subs = task && task.subtasks ? task.subtasks : [];
      let extraInfo = '';
      if (s.key === 'started' && subs.length) {
        const done = subs.filter(x => x.status === 'done').length;
        extraInfo = `${done}/${subs.length} 子任务`;
      }

      return h(`div.tl-node${stateClass ? '.' + stateClass : ''}`, [
        h(`span.tl-dot${stateClass ? '.' + stateClass : ''}`, { style: dotStyle }),
        h('div.flex.items-center.gap-2.mb-1', [
          h('span.tl-name', s.label),
          h(`span.tl-st.${stClass}`, { style: stStyle }, stLabel),
        ]),
        h('div.flex.items-center.gap-3', [
          h('span.tl-time', timeStr),
          extraInfo ? h('span.tl-dur', extraInfo) : null,
        ]),
        h('div.tl-desc', s.desc),
        s.key === 'started' && subs.length ? subTimelineView(subs) : null,
      ]);
    })
  );
}

// ---- 子任务 DAG 布局 ----
function layoutSubDAG(subs) {
  if (!subs || !subs.length) return { nodes: [], edges: [], width: 0, height: 0 };
  const byId = new Map(subs.map(s => [s.id || s.sid, s]));
  const ids = subs.map(s => s.id || s.sid);

  const layers = [];
  const remaining = new Set(ids);
  while (remaining.size) {
    const cur = [];
    for (const id of remaining) {
      const s = byId.get(id);
      const deps = s.deps || s.dependsOn || [];
      const depDone = deps.every(d => !remaining.has(d));
      if (depDone) cur.push(id);
    }
    if (!cur.length) { cur.push(...remaining); remaining.clear(); }
    for (const id of cur) remaining.delete(id);
    layers.push(cur);
  }

  const colW = 200, rowH = 72, padX = 20, padY = 16;
  const nodes = [];
  layers.forEach((layer, li) => {
    layer.forEach((id, ri) => {
      const s = byId.get(id);
      nodes.push({
        id, sub: s,
        x: padX + li * colW,
        y: padY + ri * rowH,
        w: colW - 16, h: rowH - 14,
      });
    });
  });

  const edges = [];
  for (const n of nodes) {
    const deps = n.sub.deps || n.sub.dependsOn || [];
    for (const depId of deps) {
      const src = nodes.find(x => x.id === depId);
      if (src) edges.push({ from: src, to: n });
    }
  }

  const width = padX * 2 + layers.length * colW;
  const height = padY * 2 + Math.max(1, ...layers.map(l => l.length)) * rowH;
  return { nodes, edges, width, height };
}

function subDAGView(subs, onSubClick) {
  const { nodes, edges, width, height } = layoutSubDAG(subs);
  if (!nodes.length) return h('div.py-6.text-center.text-xs.text-muted', '暂无子任务');

  // SVG 连线
  const paths = edges.map(e => {
    const x1 = e.from.x + e.from.w;
    const y1 = e.from.y + e.from.h / 2;
    const x2 = e.to.x;
    const y2 = e.to.y + e.to.h / 2;
    const mx = (x1 + x2) / 2;
    const d = `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`;
    const st = e.to.sub.status || 'planning';
    return h('path', {
      d, fill: 'none',
      stroke: `var(--${ST_COLOR[st]})`,
      'stroke-width': '2', 'stroke-opacity': '0.5',
    });
  });

  // 外框宽度固定为列宽 (max-w-full + min-w-0), 图超宽则内部横向滚动, 不撑破左列
  return h('div.sub-dag-wrap.overflow-auto.max-w-full.min-w-0', [
    h('div.relative',
      { style: { width: width + 'px', height: height + 'px', minWidth: '100%' } },
      [
        h('svg.absolute.inset-0.pointer-events-none',
          { style: { width: '100%', height: '100%' } },
          paths
        ),
        ...nodes.map(n =>
          h(`div.sub-dag-node.absolute.glass-card.p-2.cursor-pointer.transition-all`,
            {
              style: { left: n.x + 'px', top: n.y + 'px', width: n.w + 'px', height: n.h + 'px' },
              onclick: (e) => { if (onSubClick) onSubClick(n.id); },
              title: n.sub.title || n.sub.name || n.id,
            },
            [
              h('div.flex.items-center.gap-2.mb-1', [
                h(`span.w-2.h-2.rounded-full.flex-shrink-0.bg-${ST_COLOR[n.sub.status || 'planning']}`),
                h('span.text-xs.font-medium.text-head.truncate', n.sub.title || n.sub.name || n.id),
              ]),
              h('div.text-xs.text-muted', ST_LABEL[n.sub.status || 'planning'] || n.sub.status),
            ]
          )
        ),
      ]
    ),
  ]);
}

// ---- PRD 章节渲染 ----
function prdSectionView(prd) {
  if (!prd || !prd.length) return [];
  const cards = prd.map(prdCard);
  // 大屏: 目标 / 验收标准 并排两 card; 其余章节仍整行
  const pair = [];
  const rest = [];
  prd.forEach((sec, i) => (sec.name === '目标' || sec.name === '验收标准' ? pair : rest).push(cards[i]));
  return [
    pair.length
      ? h('div.grid.grid-cols-1.xl\\:grid-cols-2.gap-6.items-start', pair)
      : null,
    ...rest,
  ].filter(Boolean);
}

function prdCard(sec) {
  const icon = sec.name === '目标' ? 'fa-bullseye' : sec.name === '验收标准' ? 'fa-check-square-o' : 'fa-file-text-o';
  const color = sec.name === '目标' ? 'st-planning' : sec.name === '验收标准' ? 'st-check' : 'st-active';
  return h('div.glass-card.p-5', [
    h('h3.section-title', [
      h(`i.fa.${icon}.text-${color}`),
      sec.name + (sec.badge ? ` (${sec.badge[0]}/${sec.badge[1]})` : ''),
    ]),
    sec.items && sec.items.length
      ? h('div.space-y-2',
          sec.items.map(item =>
            h('div.flex.items-start.gap-3.text-sm', [
              // 目标同验收标准, 一律 todo (checkbox) 样式
              item.kind === 'check' || sec.name === '目标'
                ? h(`i.fa.${item.done ? 'fa-check-square' : 'fa-square-o'}.${item.done ? 'text-st-done' : 'text-muted'}.mt-0.5.flex-shrink-0`)
                : h('span.w-1.5.h-1.5.rounded-full.bg-muted.mt-2.flex-shrink-0'),
              h('span.text-fg.leading-relaxed' + (item.done ? '.line-through.text-muted' : ''), item.text),
            ])
          )
        )
      : h('p.text-sm.text-muted', '—'),
  ]);
}

// ---- 依赖链接 (前置依赖 / 被依赖共用) ----
function depLink(d) {
  const desc = d.desc || d.description || '';
  return h('a.flex.items-start.gap-2.p-2.rounded-lg.hover\\:bg-card\\/40.transition-colors',
    { href: `/task/detail?id=${d.id}`, 'data-nav': '' },
    [
      h(`span.w-2.h-2.mt-1.5.flex-shrink-0.rounded-full.bg-${ST_COLOR[d.status || 'planning']}`),
      h('div.min-w-0.flex-1', [
        h('div.text-sm.text-fg', d.title || d.name || d.id),
        desc ? h('div.text-xs.text-muted.mt-0.5.leading-relaxed', desc) : null,
      ]),
    ]
  );
}

// ---- 契约 ----
function contractsView(contracts) {
  if (!contracts || !contracts.length) return null;
  return h('div.glass-card.p-5', [
    h('h3.section-title', [
      h('i.fa.fa-handshake-o.text-st-check'),
      `契约 (${contracts.length})`,
    ]),
    h('div.space-y-3',
      contracts.map((c, i) =>
        h('div.p-3.rounded-lg.bg-surface/50.border.border-brd/30', [
          // 契约落盘为字符串 (skein contract --add); 对象形态仅作兼容
          h('div.text-sm.font-semibold.text-head.leading-relaxed',
            typeof c === 'string' ? c : (c.name || c.title || `契约 ${i + 1}`)),
          typeof c !== 'string' && (c.desc || c.description)
            ? h('div.text-xs.text-muted.mt-1.leading-relaxed', c.desc || c.description) : null,
        ])
      )
    ),
  ]);
}

const docEmpty = md.isPlaceholder;   // 模板占位 (只有标题 + 提示句) 视为空, 整块不渲染

// ---- 详细设计 ----
function designView(design) {
  if (docEmpty(design)) return null;
  return h('div.glass-card.p-5', [
    h('h3.section-title', [
      h('i.fa.fa-sitemap.text-st-active'),
      '详细设计',
    ]),
    docBody(design),
  ]);
}

// ---- 文档正文 (design.md / findings.md / research/*.md 都是 md) ----
function docBody(text) {
  // lib/md.js 渲染 (normalize 先自动修常见瑕疵) + sanitize; .md-body 承载排版样式
  return h('div.md-body', { html: md.renderSafe(text) });
}

function researchView(findings, research) {
  const notes = Object.entries(research || {}).filter(([, body]) => !docEmpty(body));
  const hasFindings = !docEmpty(findings);
  if (!hasFindings && !notes.length) return null;   // 全是模板占位 → 整卡不渲染
  return h('div.glass-card.p-5', [
    h('h3.section-title', [
      h('i.fa.fa-flask.text-st-planning'),
      `调研${notes.length ? ` (结论 + ${notes.length} 篇过程笔记)` : ' 结论'}`,
    ]),
    hasFindings ? docBody(findings) : h('p.text-sm.text-muted', '无收敛结论 (findings.md 未生成)'),
    notes.length
      ? h('div.space-y-2.mt-4',
          notes.map(([name, body]) =>
            h('details.rounded-lg.bg-surface/30.border.border-brd/30', [
              h('summary.cursor-pointer.px-3.py-2.text-sm.text-head.select-none', name),
              h('div.px-3.pb-3', docBody(body)),
            ])
          )
        )
      : null,
  ]);
}

// ---- 子任务列表 ----
function subtaskListView(subs) {
  if (!subs || !subs.length) return null;
  const done = subs.filter(s => s.status === 'done').length;
  return h('div.glass-card.p-5', [
    h('h3.section-title', [
      h('i.fa.fa-tasks.text-accent'),
      `子任务列表`,
      h('span.ml-2.text-xs.text-muted', `(${done}/${subs.length})`),
    ]),
    h('div.space-y-2',
      subs.map(s => {
        const st = s.status || 'planning';
        const desc = s.desc || s.description || '';
        return h('div.flex.items-start.gap-3.p-3.rounded-lg.hover\\:bg-card/40.transition-colors', [
          h(`span.w-2.5.h-2.5.mt-1.5.rounded-full.flex-shrink-0.bg-${ST_COLOR[st]}`),
          h('div.flex-1.min-w-0', [
            h('div.text-sm.text-fg', s.title || s.name || s.sid || s.id),
            // desc 落盘在 task.json 的 subtask 里 (skein subtask add --desc), 原文直出不截断
            desc ? h('div.text-xs.text-fg.mt-1.whitespace-pre-wrap.leading-relaxed', desc) : null,
            h('div.text-xs.text-muted.mt-1', ST_LABEL[st] || st),
          ]),
          s.progress != null
            ? h('span.text-xs.text-muted', s.progress + '%')
            : null,
        ]);
      })
    ),
  ]);
}

// ---- 主渲染 ----
export async function render(mount, params, ctx) {
  const taskId = params.id;

  // 详情端点自足: prd / progress / stage / 依赖明细都内联返回, 不再拉 /data 全量看板
  const taskResp = await api.task(taskId).catch(() => null);

  // /task/<id> 返回 {task, docs, research, prd, ...}: 兄弟字段需合并进 task
  const taskRaw = taskResp
    ? (taskResp.task
        ? {
            ...taskResp.task,
            docs: taskResp.docs, research: taskResp.research,
            prd: taskResp.prd, progress: taskResp.progress, stage: taskResp.stage,
          }
        : (taskResp.card || taskResp))
    : null;
  const task = normalizeTask(taskRaw);
  const depTasks = normalizeTasks((taskResp && taskResp.depTasks) || []);
  const dependents = normalizeTasks((taskResp && taskResp.dependents) || []);

  if (!task) {
    mount.replaceChildren(
      h('div.glass-card.py-16.text-center', [
        h('i.fa.fa-exclamation-triangle.text-4xl.text-warning.mb-3'),
        h('h2.text-xl.font-semibold.text-head.mb-2', '任务不存在'),
        h('p.text-muted.mb-4', `ID: ${taskId}`),
        h('a.antd-btn.antd-btn-primary',
          { href: '/dashboard', 'data-nav': '' },
          '返回概览'),
      ])
    );
    return;
  }

  const st = task.status || 'planning';
  const timeline = buildTimeline(task);

  function onSubClick(sid) {
    console.log('subtask clicked:', sid);
  }

  // 删除任务: 软删进 .skein/trash/ (skein del), 删完回看板
  async function deleteTask() {
    const yes = await confirmDialog({
      title: '删除任务',
      message: `删除任务 #${task.id} ${task.title || task.name || ''}?\n软删进 .skein/trash/, 可从磁盘恢复; 在途 task 的 worktree/分支会一并销毁。`,
      ok: '删除',
      danger: true,
    });
    if (!yes) return;
    try {
      const r = await api.exec('del', { id: task.id });
      if (!r || !r.ok) throw new Error((r && (r.stderr || r.error)) || '删除失败');
    } catch (e) {
      await alertDialog('删除失败: ' + (e && e.message ? e.message : e), '删除失败');
      return;
    }
    if (ctx && ctx.navigate) ctx.navigate('/board');
    else window.location.href = '/board';
  }

  mount.replaceChildren(
    // 面包屑 + 标题
    h('div.mb-6', [
      h('nav.flex.items-center.gap-2.text-sm.text-muted.mb-3', [
        h('a.hover\\:text-accent.transition-colors', { href: '/dashboard', 'data-nav': '' }, '概览'),
        h('i.fa.fa-angle-right.text-xs'),
        h('a.hover\\:text-accent.transition-colors', { href: '/board', 'data-nav': '' }, '看板'),
        h('i.fa.fa-angle-right.text-xs'),
        h('span.text-head', task.title || task.name || task.id),
      ]),
      h('div.flex.items-start.justify-between.flex-wrap.gap-3', [
        h('div', [
          h('div.flex.items-center.gap-3.mb-2', [
            h(`i.fa.${ST_ICON[st]}.text-${ST_COLOR[st]}.text-xl`),
            h('h1.text-3xl.font-bold.text-head', task.title || task.name || '(未命名)'),
          ]),
          h('div.flex.items-center.gap-3.text-sm.text-muted', [
            h('span.font-mono', '#' + task.id),
            h('span·opacity-40', '·'),
            h('span', task.createdAt ? '创建于 ' + fmtRelative(task.createdAt) : ''),
            h('span·opacity-40', '·'),
            h('span', task.updatedAt ? '更新于 ' + fmtRelative(task.updatedAt) : ''),
          ]),
        ]),
        h(`span.antd-tag.antd-tag-${ST_COLOR[st].replace('st-', '')}.text-base.px-4.py-1`, ST_LABEL[st] || st),
      ]),
    ]),

    // 两列布局: 左 = 元信息 / 时间线 / 子任务 DAG; 右 = 完整内容
    h('div.grid.grid-cols-1.lg\\:grid-cols-5.gap-6', [
      // 左: 元信息面板 (min-w-0: grid item 默认 min-width:auto 会被 DAG 内容撑宽)
      h('div.space-y-6.min-w-0', [
        // 基本信息
        h('div.glass-card.p-5', [
          h('h3.section-title', '基本信息'),
          // 状态在页头徽标已有, 各时间点归时间线; 这里不重复
          infoItem('优先级',
            task.priority === 'high' ? '高' : task.priority === 'low' ? '低' : '中'
          ),
          infoItem('负责人', task.assignee || '未分配'),
          infoItem('预估工时', task.estimate ? task.estimate + ' 小时' : '—'),
          infoItem('进度', task.progress != null ? task.progress + '%' : '—'),
        ]),

        // 时间线
        h('div.glass-card.p-5', [
          h('h3.section-title', [
            h('i.fa.fa-history.text-accent'),
            '生命周期时间线',
          ]),
          timelineView(timeline, task),
        ]),

        // 子任务列表
        subtaskListView(task.subtasks),

        // 前置依赖 (空则整卡不渲染, 与「被依赖」一致)
        depTasks.length
          ? h('div.glass-card.p-5', [
              h('h3.section-title', [
                h('i.fa.fa-link.text-accent'),
                '前置依赖',
                ` (${depTasks.length})`,
              ]),
              h('div.space-y-2', depTasks.map(depLink)),
            ])
          : null,

        // 被依赖
        dependents.length
          ? h('div.glass-card.p-5', [
              h('h3.section-title', [
                h('i.fa.fa-share-alt.text-accent'),
                '被依赖',
                ` (${dependents.length})`,
              ]),
              h('div.space-y-2', dependents.map(depLink)),
            ])
          : null,

        // 操作
        h('div.glass-card.p-5', [
          h('h3.section-title', [
            h('i.fa.fa-cog.text-accent'),
            '操作',
          ]),
          h('div.flex.flex-wrap.gap-2', [
            h('button.antd-btn.antd-btn-primary.flex-1',
              { onclick: () => alertDialog('编辑功能开发中') },
              [h('i.fa.fa-pencil.mr-1.5'), '编辑']
            ),
            st === 'planning'
              ? h('button.antd-btn.antd-btn-default',
                  { onclick: () => alertDialog('状态变更开发中') },
                  [h('i.fa.fa-flag.mr-1.5'), '就绪'])
              : null,
            st === 'ready'
              ? h('button.antd-btn.antd-btn-default',
                  { onclick: () => alertDialog('状态变更开发中') },
                  [h('i.fa.fa-play.mr-1.5'), '开始'])
              : null,
            st === 'active'
              ? h('button.antd-btn.antd-btn-default',
                  { onclick: () => alertDialog('状态变更开发中') },
                  [h('i.fa.fa-check.mr-1.5'), '提交验收'])
              : null,
            h('button.antd-btn.antd-btn-danger.w-full',
              { onclick: deleteTask, title: '软删进 .skein/trash/, 可恢复' },
              [h('i.fa.fa-times-circle.mr-1.5'), '删除任务']),
          ]),
        ]),
      ]),

      // 右: 完整内容
      h('div.lg\\:col-span-4.space-y-6.min-w-0', [
        // 描述
        task.description
          ? h('div.glass-card.p-5', [
              h('h3.section-title', '任务描述'),
              h('div.text-sm.text-fg.leading-relaxed.whitespace-pre-wrap', task.description),
            ])
          : null,

        // 目标 / 验收标准 (来自 PRD)
        ...prdSectionView(task.prd),

        // 契约
        contractsView(task.contracts),

        // 子任务 DAG
        task.subtasks && task.subtasks.length >= 2
          ? h('div.glass-card.p-5', [
              h('h3.section-title', [
                h('i.fa.fa-sitemap.text-accent'),
                `子任务 DAG (${task.subtasks.length})`,
              ]),
              subDAGView(task.subtasks, onSubClick),
            ])
          : null,

        // 详细设计
        task.docs && task.docs.design ? designView(task.docs.design) : null,

        // 调研: findings.md 结论 + research/*.md 过程
        researchView(task.docs && task.docs.findings, task.research),
      ]),
    ]),
  );
}
