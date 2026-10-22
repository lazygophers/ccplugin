import { readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

// 解析依据：.scratch/research/2026-10-22-transcript-task-entry-structure.md（实测报告）
// 返回值 = 后台 task-notification 的 <result> 全文；同步 Task 的 tool_result 直存正文。
// API 依据：transcript 内部格式无官方契约，改格式时先重跑实测。

const NOTIF = /^<task-notification>/;
const RESULT_RE = /<task-id>([\s\S]*?)<\/task-id>\s*<tool-use-id>([\s\S]*?)<\/tool-use-id>[\s\S]*?<result>([\s\S]*?)<\/result>/;
const ASYNC_LAUNCH = /^Async agent launched/;
const AGENT_TOOLS = new Set(['Task', 'Agent']);

// ~/.claude/projects/<cwd 编码>/
// 编码规则（实测 ~/.claude/projects 全目录）：路径中每个非字母数字字符 → "-"
// （`/`、`.`、`-` 均如此；worktree 的 .claude/worktrees 即成 --claude-worktrees）
export function projectDirOf(cwd) {
  const slug = cwd.replace(/[^A-Za-z0-9]/g, '-');
  return join(homedir(), '.claude/projects', slug);
}

export function locateTranscript(cwd, sessionId) {
  return join(projectDirOf(cwd), `${sessionId}.jsonl`);
}

// content 可能是块数组（对象/纯字符串）或本身就是纯字符串（本机实测三种都有）
const blocks = (content) => (Array.isArray(content) ? content : [content]);
const blockText = (b) => (typeof b === 'string' ? b : b?.text ?? '');

// 输入 transcript jsonl 路径，输出最近 limit 条（默认 10）agent 返回值，
// 按文件行序从新到旧：[{ time, taskId, text }]
export function recentAgentReturns(transcriptPath, limit = 10) {
  const lines = readFileSync(transcriptPath, 'utf8').split('\n');
  // shortcut: 先整读建 id→工具名 映射（同步 tool_result 的 id 在文件更早处出现，
  // 纯逆向扫拿不到映射）；transcript 1M 量级整读无压力，超大文件再改尾窗
  const idIsAgent = new Set();
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
      if (b.type === 'tool_use' && AGENT_TOOLS.has(b.name)) idIsAgent.add(b.id);
    }
  }
  const out = [];
  for (let i = parsed.length - 1; i >= 0 && out.length < limit; i--) {
    const o = parsed[i];
    if (o.type !== 'user') continue; // 只认 user/assistant，防 blob 重放重复计数
    for (const b of blocks(o.message?.content)) {
      const t = blockText(b).trimStart();
      if (NOTIF.test(t)) {
        const m = t.match(RESULT_RE); // [\s\S] 即 DOTALL
        // task-notification 也发给 Bash 后台任务，按 tool-use-id 回查只留 agent 的
        if (m && idIsAgent.has(m[2])) out.push({ time: o.timestamp, taskId: m[1], text: m[3] });
      } else if (b?.type === 'tool_result' && idIsAgent.has(b.tool_use_id)) {
        const text = typeof b.content === 'string' ? b.content : (b.content ?? []).filter((c) => c.type === 'text').map((c) => c.text).join('');
        // 后台 agent 的 tool_result 只是启动元数据（agentId + output_file），非返回值
        if (text && !ASYNC_LAUNCH.test(text)) out.push({ time: o.timestamp, taskId: null, text });
      }
      if (out.length >= limit) break;
    }
  }
  return out;
}
