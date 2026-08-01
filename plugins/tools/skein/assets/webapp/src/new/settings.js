// SKEIN 设置面板 — 页头齿轮按钮打开, 读/改/存 config.yaml (经 /__skein__/config 读写端点)。
//
// 🔒 hooks 字段的值是 shell 命令, 远程可写 = RCE (CFG_REMOTE_DENY, serve.py 已拒写) — 面板
//    不渲染任何 hooks 编辑控件, 且保存时显式 `delete payload.hooks`, 不依赖后端兜底 (纵深防御)。
// ponytail: 全量提交不做增量 diff (design.md §3 决策) — 提交负载 = 已加载的生效值深拷贝再覆盖
//   被编辑字段, 未渲染控件的分组子键 (如 spec.core_budget, deprecated) 原样带回, 免得后端把它
//   兜底成 CONFIG_DEFAULTS 硬编码值 (skeinlib/serve.py `_cfg_save`: 组内缺键 → 落回默认值)。
// 类型强制归后端唯一真值源 (_coerce_config) — 前端校验只做非法值即时拦截, 不重实现 coerce 规则。
import { h, alertDialog } from './app.js';
import * as api from './lib/api.js';

const INPUT_CLS = 'border border-brd/60 bg-card/60 rounded-lg px-2 py-1 text-sm outline-none focus:border-accent/50';

function field(label, inputEl, hint) {
  return h('label.flex.flex-col.gap-1.text-sm', [
    h('span.text-fg.font-medium', label),
    inputEl,
    hint ? h('span.text-xs.text-muted', hint) : null,
  ]);
}

function numInput(value) {
  return h('input', { type: 'number', step: '1', value: String(value), class: INPUT_CLS });
}
function textInput(value) {
  return h('input', { type: 'text', value: String(value), class: INPUT_CLS });
}
function checkbox(checked) {
  return h('input', { type: 'checkbox', class: 'antd-checkbox', checked: checked ? true : null });
}

export async function openSettingsPanel() {
  let cfg;
  try {
    cfg = await api.getConfig();
  } catch (e) {
    await alertDialog('读取配置失败: ' + ((e && e.message) || e), '错误');
    return;
  }

  const inMaxActive = numInput(cfg.max_active);
  const inAutoCommit = checkbox(cfg.auto_commit);
  const inRetainDays = numInput(cfg.retain_days);
  const inWtEnabled = checkbox(cfg.worktree && cfg.worktree.enabled);
  const inWtRoot = textInput((cfg.worktree && cfg.worktree.root) || '');
  const inWebServe = checkbox(cfg.web && cfg.web.serve);
  const inWebOpen = checkbox(cfg.web && cfg.web.board_open);
  const inSpecBudget = numInput((cfg.spec && cfg.spec.always_budget) || 0);

  const errBox = h('div.text-xs.min-h-[1em]', '');
  const saveBtn = h('button.antd-btn', { onclick: onSave }, '保存');

  let closed = false;
  const dlg = h('dialog.dag-modal', { onclose: () => close() },
    h('div.dag-modal-inner', [
      h('div.dag-modal-head', [
        h('h3.dag-modal-title', [h('i.fa.fa-cog'), '设置']),
        h('button.dag-modal-close', { onclick: () => close(), title: '关闭' }, '×'),
      ]),
      h('div.text-xs.text-muted',
        '下列为当前生效值 (可能含环境变量覆盖); 保存写入 config.yaml — 若某项被环境变量覆盖, '
        + '落盘值与展示的生效值可能不同, 属预期行为。'),
      h('div.grid.grid-cols-2.gap-3.mt-2', [
        field('并发上限', inMaxActive, 'max_active: 同时进行中的 task 数, ≥1 整数'),
        field('保留天数', inRetainDays, 'retain_days: 0=完成即归档, 负=永不自动归档'),
        field('自动提交', inAutoCommit, 'auto_commit: 仅原地模式(未启用 worktree)生效'),
        field('spec 全文预算', inSpecBudget, 'spec.always_budget: 字符数, 超出触发降级'),
        field('启用 worktree', inWtEnabled, 'worktree.enabled'),
        field('worktree 根目录', inWtRoot, 'worktree.root'),
        field('看板服务', inWebServe, 'web.serve'),
        field('自动开浏览器', inWebOpen, 'web.board_open: 仅 view 命令生效'),
      ]),
      errBox,
      h('div.flex.justify-end.gap-2.mt-2', [
        h('button.antd-btn.antd-btn-default', { onclick: () => close() }, '取消'),
        saveBtn,
      ]),
    ]));

  function close() {
    if (closed) return;
    closed = true;
    dlg.close();
    dlg.remove();
  }
  document.body.appendChild(dlg);
  dlg.showModal();

  async function onSave() {
    errBox.className = 'text-xs min-h-[1em]';
    errBox.textContent = '';

    const maxActive = parseInt(inMaxActive.value, 10);
    const retainDays = parseInt(inRetainDays.value, 10);
    const specBudget = parseInt(inSpecBudget.value, 10);
    const wtRoot = inWtRoot.value.trim();
    const problems = [];
    if (!Number.isInteger(maxActive) || maxActive < 1) problems.push('并发上限须为 ≥1 的整数');
    if (!Number.isInteger(retainDays)) problems.push('保留天数须为整数');
    if (!Number.isInteger(specBudget) || specBudget < 1) problems.push('spec 全文预算须为 ≥1 的整数');
    if (!wtRoot) problems.push('worktree 根目录不能为空');
    if (problems.length) {
      errBox.className = 'text-xs text-danger min-h-[1em]';
      errBox.textContent = problems.join('; ');
      return;   // 前端即时拦截: 用户输入原样保留在表单里, 不提交也不清空
    }

    // 深拷贝已加载的生效值再覆盖编辑字段 — hooks 及 spec.core_budget 等未渲染子键原样带回。
    const payload = JSON.parse(JSON.stringify(cfg));
    delete payload.hooks;   // 🔒 硬约束: 提交负载禁带 hooks 字段
    payload.max_active = maxActive;
    payload.auto_commit = !!inAutoCommit.checked;
    payload.retain_days = retainDays;
    payload.worktree = Object.assign({}, payload.worktree, { enabled: !!inWtEnabled.checked, root: wtRoot });
    payload.web = Object.assign({}, payload.web, { serve: !!inWebServe.checked, board_open: !!inWebOpen.checked });
    payload.spec = Object.assign({}, payload.spec, { always_budget: specBudget });

    saveBtn.disabled = true;
    saveBtn.textContent = '保存中…';
    try {
      const saved = await api.setConfig(payload);
      cfg = saved;   // 刷新基线, 面板内再次保存沿用最新生效值
      errBox.className = 'text-xs text-success min-h-[1em]';
      errBox.textContent = '已保存';
      inMaxActive.value = String(saved.max_active);
      inAutoCommit.checked = !!saved.auto_commit;
      inRetainDays.value = String(saved.retain_days);
      inWtEnabled.checked = !!(saved.worktree && saved.worktree.enabled);
      inWtRoot.value = (saved.worktree && saved.worktree.root) || '';
      inWebServe.checked = !!(saved.web && saved.web.serve);
      inWebOpen.checked = !!(saved.web && saved.web.board_open);
      inSpecBudget.value = String((saved.spec && saved.spec.always_budget) || 0);
    } catch (e) {
      errBox.className = 'text-xs text-danger min-h-[1em]';
      errBox.textContent = '保存失败: ' + ((e && e.message) || e) + ' — 已保留你的输入, 可重试。';
    } finally {
      saveBtn.disabled = false;
      saveBtn.textContent = '保存';
    }
  }
}
