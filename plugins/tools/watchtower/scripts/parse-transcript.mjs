// 解析依据：.scratch/research/2026-10-22-transcript-task-entry-structure.md（实测报告）
// agent 返回值 = 后台 task-notification 的 <result> 全文；同步 Task 的 tool_result 直存正文。
// 主回复 = 主对话每轮最终 assistant 文本（轮界 = 其后出现真人 user 输入）。
// API 依据：transcript 内部格式无官方契约，改格式时先重跑实测。
// 本模块是纯函数、零 node:* 导入：hooks module 沙箱只许相对导入和 claude-code，
// 文件读写由调用方（register.ts 走引擎 $.fs.read）负责。

// 引擎读文件的边界（index.d.ts）：$.fs.read 单次上限 4194304 字节、无 offset；
// $.process.run 的 stdout 同上限。超限 transcript 由 register.ts 改走
// tail -c 取尾：取 4194000 字节，给 stdout 上限留 304 字节余量。
// 常量放这里供 register.ts 与单测共用（hooks 模块不可被测试 import）。
export const READ_CAP = 4194304;
export const TAIL_BYTES = 4194000;

const NOTIF = /^<task-notification>/;
const RESULT_RE = /<task-id>([\s\S]*?)<\/task-id>\s*<tool-use-id>([\s\S]*?)<\/tool-use-id>[\s\S]*?<result>([\s\S]*?)<\/result>/;
// harness 渲染的「Teammate @name finished」形态；单独取，避免与主正则的惰性量词争位
const SUMMARY_RE = /<summary>([\s\S]*?)<\/summary>/;
const ASYNC_LAUNCH = /^Async agent launched/;
const AGENT_TOOLS = new Set(['Task', 'Agent']);

// <home>/.claude/projects/<cwd 编码>/
// 编码规则（实测 ~/.claude/projects 全目录）：路径中每个非字母数字字符 → "-"
// （`/`、`.`、`-` 均如此；worktree 的 .claude/worktrees 即成 --claude-worktrees）
export function projectDirOf(cwd, home) {
  const slug = cwd.replace(/[^A-Za-z0-9]/g, '-');
  return `${home}/.claude/projects/${slug}`;
}

export function locateTranscript(cwd, sessionId, home) {
  return `${projectDirOf(cwd, home)}/${sessionId}.jsonl`;
}

// content 可能是块数组（对象/纯字符串）或本身就是纯字符串（本机实测三种都有）
const blocks = (content) => (Array.isArray(content) ? content : [content]);
const blockText = (b) => (typeof b === 'string' ? b : b?.text ?? '');

// 轮界：真人 user 输入——type user、content 是字符串或 text 块、无 tool_result、
// 非 task-notification、非 sidechain（tool_result / 附件 / 通知都不开新轮）
const isHumanUser = (o) =>
  o.isSidechain !== true &&
  o.origin?.kind !== 'task-notification' &&
  !blocks(o.message?.content).some((b) => b?.type === 'tool_result');

// 输入 transcript jsonl 文本，输出最近 limit 条（默认 50）返回条目，混池按
// transcript 行序（追加序即时间序）从新到旧：[{ kind: 'agent'|'main', time, taskId, id, text, summary?, title? }]
// agent 条目：id = tool-use-id；main 条目：id = assistant 行 uuid（pane 展开锚点，跨刷新稳定）、
// taskId = null、无 summary/title（头部回退正文首行）。
export function recentReturns(transcriptContent, limit = 50) {
  const lines = String(transcriptContent ?? '').split('\n');
  // shortcut: 先整读建 id→工具名 映射（同步 tool_result 的 id 在文件更早处出现，
  // 纯逆向扫拿不到映射）；transcript 1M 量级整读无压力，超大文件再改尾窗
  const idIsAgent = new Set();
  const idTitle = new Map();
  const parsed = [];
  for (const line of lines) {
    let o;
    try {
      o = JSON.parse(line);
    } catch {
      continue; // 空行/截断尾行
    }
    parsed.push(o);
    if (o.type !== 'assistant') continue; // 跳过 api-request-blob 等重放行
    for (const b of o.message?.content ?? []) {
      if (b.type !== 'tool_use' || !AGENT_TOOLS.has(b.name)) continue;
      idIsAgent.add(b.id);
      const d = b.input?.description;
      if (typeof d === 'string' && d.trim() !== '') idTitle.set(b.id, d.trim());
    }
  }

  // 正向单遍：收集两类条目 + 行号，最后按行号倒排取最近 limit 条
  const hits = [];
  let pending = null; // 当前主对话轮的最终 assistant 文本候选（后见覆盖先见 = 同轮只留最后一条）
  for (let i = 0; i < parsed.length; i++) {
    const o = parsed[i];
    if (o.type === 'user') {
      for (const b of blocks(o.message?.content)) {
        const t = blockText(b).trimStart();
        if (NOTIF.test(t)) {
          const m = t.match(RESULT_RE); // [\s\S] 即 DOTALL
          // task-notification 也发给 Bash 后台任务，按 tool-use-id 回查只留 agent 的
          if (m && idIsAgent.has(m[2])) {
            const summary = t.match(SUMMARY_RE)?.[1];
            const title = idTitle.get(m[2]);
            hits.push({ idx: i, entry: { kind: 'agent', time: o.timestamp, taskId: m[1], id: m[2], text: m[3], ...(summary !== undefined && { summary }), ...(title !== undefined && { title }) } });
          }
        } else if (b?.type === 'tool_result' && idIsAgent.has(b.tool_use_id)) {
          const text = typeof b.content === 'string' ? b.content : (b.content ?? []).filter((c) => c.type === 'text').map((c) => c.text).join('');
          // 后台 agent 的 tool_result 只是启动元数据（agentId + output_file），非返回值
          if (text && !ASYNC_LAUNCH.test(text)) {
            const title = idTitle.get(b.tool_use_id);
            hits.push({ idx: i, entry: { kind: 'agent', time: o.timestamp, taskId: null, id: b.tool_use_id, text, ...(title !== undefined && { title }) } });
          }
        }
      }
      if (isHumanUser(o) && pending) {
        hits.push({ idx: pending.idx, entry: pending.entry });
        pending = null;
      }
    } else if (o.type === 'assistant' && o.isSidechain !== true) {
      // 只认非空 text 块；一行多块时取最后一块，多行时整轮取最后一条（后见覆盖）
      const bs = o.message?.content ?? [];
      for (let j = bs.length - 1; j >= 0; j--) {
        const t = blockText(bs[j]).trim();
        if (t !== '') {
          pending = { idx: i, entry: { kind: 'main', time: o.timestamp, taskId: null, id: o.uuid ?? `main:${i}`, text: t } };
          break;
        }
      }
    }
  }
  if (pending) hits.push({ idx: pending.idx, entry: pending.entry }); // 末轮 Stop 回复（其后还没有 user 输入）
  return hits
    .sort((a, b) => b.idx - a.idx)
    .slice(0, limit)
    .map((h) => h.entry);
}
