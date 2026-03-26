#!/usr/bin/env node
/**
 * Claude Code Hooks 事件处理 - Node.js 版
 *
 * 支持全部 24 个官方 Hook 事件：
 * SessionStart, UserPromptSubmit, PreToolUse, PermissionRequest,
 * PostToolUse, PostToolUseFailure, Notification, SubagentStart,
 * SubagentStop, Stop, StopFailure, TeammateIdle, TaskCompleted,
 * InstructionsLoaded, ConfigChange, CwdChanged, FileChanged,
 * WorktreeCreate, WorktreeRemove, PreCompact, PostCompact,
 * Elicitation, ElicitationResult, SessionEnd
 *
 * 通知和 TTS 委托给 Python notify.py（跨平台 Swift/Tk overlay）
 */

import { readFileSync, existsSync, copyFileSync, mkdirSync } from 'fs';
import { join, basename, dirname } from 'path';
import { homedir } from 'os';
import { execFile } from 'child_process';

// ─── 环境变量 ───────────────────────────────────────────────────────────────────
const PLUGIN_ROOT = process.env.CLAUDE_PLUGIN_ROOT || process.cwd();
const PROJECT_DIR = process.env.CLAUDE_PROJECT_DIR || process.cwd();
const PLUGIN_NAME = process.env.PLUGIN_NAME || 'notify';

const PROJECT_PLUGINS_DIR = join(PROJECT_DIR, '.lazygophers', 'ccplugin');
const USER_PLUGINS_DIR = join(homedir(), '.lazygophers', 'ccplugin');

// ─── 日志 ────────────────────────────────────────────────────────────────────────
const DEBUG = process.env.DEBUG === '1' || process.argv.includes('--debug');
function log(level, msg) { process.stderr.write(`[${PLUGIN_NAME}][${level}] ${msg}\n`); }
function info(msg) { log('INFO', msg); }
function error(msg) { log('ERROR', msg); }
function debug(msg) { if (DEBUG) log('DEBUG', msg); }

// ─── YAML 解析（简化版，避免外部依赖）──────────────────────────────────────────
function parseYaml(text) {
  // 简化的 YAML 解析器，支持嵌套对象、字符串值、布尔值、多行文本
  const lines = text.split('\n');
  const root = {};
  const stack = [{ indent: -1, obj: root }];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    // 跳过空行和注释
    if (!line.trim() || line.trim().startsWith('#') || line.trim() === '---') continue;

    const match = line.match(/^(\s*)([\w_-]+)\s*:\s*(.*)/);
    if (!match) continue;

    const indent = match[1].length;
    const key = match[2];
    let value = match[3].trim();

    // 弹出栈中比当前缩进大或等于的层级
    while (stack.length > 1 && stack[stack.length - 1].indent >= indent) {
      stack.pop();
    }

    const parent = stack[stack.length - 1].obj;

    if (value === '' || value === null) {
      // 嵌套对象
      parent[key] = {};
      stack.push({ indent, obj: parent[key] });
    } else if (value === '|-' || value === '|') {
      // 多行文本块
      const blockLines = [];
      const blockIndent = indent + 2;
      let j = i + 1;
      while (j < lines.length) {
        const bline = lines[j];
        if (bline.trim() === '' || (bline.match(/^\s*/)[0].length >= blockIndent && !bline.match(/^\s*[\w_-]+\s*:/))) {
          blockLines.push(bline.slice(blockIndent) || '');
          j++;
        } else {
          break;
        }
      }
      parent[key] = blockLines.join('\n').trimEnd();
      i = j - 1;
    } else {
      // 处理引号字符串
      if ((value.startsWith('"') && value.endsWith('"')) ||
          (value.startsWith("'") && value.endsWith("'"))) {
        value = value.slice(1, -1);
      }
      // 布尔值
      if (value === 'true') parent[key] = true;
      else if (value === 'false') parent[key] = false;
      // 数字
      else if (/^\d+(\.\d+)?$/.test(value)) parent[key] = Number(value);
      else parent[key] = value;
    }
  }
  return root;
}

// ─── 配置加载 ────────────────────────────────────────────────────────────────────

/**
 * @typedef {Object} HookConfig
 * @property {boolean} enabled
 * @property {boolean} play_sound
 * @property {string|null} message
 */

function defaultHookConfig(overrides = {}) {
  return { enabled: false, play_sound: false, message: null, ...overrides };
}

function loadHookConfig(data) {
  if (!data || typeof data !== 'object') return defaultHookConfig();
  return defaultHookConfig({
    enabled: data.enabled === true,
    play_sound: data.play_sound === true,
    message: data.message || null,
  });
}

function loadConfig() {
  const examplePath = join(PLUGIN_ROOT, 'hooks.example.yaml');
  const projectPath = join(PROJECT_PLUGINS_DIR, PLUGIN_NAME, 'config.yaml');
  const homePath = join(USER_PLUGINS_DIR, PLUGIN_NAME, 'config.yaml');

  let configData = null;

  // 尝试加载项目配置
  if (existsSync(projectPath)) {
    try {
      configData = parseYaml(readFileSync(projectPath, 'utf-8'));
      debug(`加载项目配置: ${projectPath}`);
    } catch (e) {
      error(`加载项目配置失败: ${e.message}`);
    }
  } else if (existsSync(examplePath)) {
    // 从示例配置复制
    try {
      const dir = dirname(projectPath);
      mkdirSync(dir, { recursive: true });
      copyFileSync(examplePath, projectPath);
      configData = parseYaml(readFileSync(projectPath, 'utf-8'));
      debug(`从示例配置复制: ${examplePath} -> ${projectPath}`);
    } catch (e) {
      error(`复制示例配置失败: ${e.message}`);
    }
  }

  // 回退到用户配置
  if (!configData && existsSync(homePath)) {
    try {
      configData = parseYaml(readFileSync(homePath, 'utf-8'));
      debug(`加载用户配置: ${homePath}`);
    } catch (e) {
      error(`加载用户配置失败: ${e.message}`);
    }
  }

  return configData?.hooks || {};
}

// ─── 配置路由 ────────────────────────────────────────────────────────────────────

/**
 * 全部 24 个 Hook 事件的配置路由
 *
 * 事件分为三类：
 * 1. 简单事件（无 matcher）：stop, user_prompt_submit, permission_request, 等
 * 2. 工具事件（按 tool_name）：pre_tool_use, post_tool_use, post_tool_use_failure
 * 3. 子类型事件（按特定字段）：session_start/source, notification/type, 等
 */
function getHookConfig(config, eventName, hookData) {
  switch (eventName) {
    // ── 工具相关事件（按 tool_name 匹配）──
    case 'PreToolUse': {
      const toolName = (hookData.tool_name || '').toLowerCase();
      return loadHookConfig(config.pre_tool_use?.[toolName]);
    }
    case 'PostToolUse': {
      const toolName = (hookData.tool_name || '').toLowerCase();
      return loadHookConfig(config.post_tool_use?.[toolName]);
    }
    case 'PostToolUseFailure': {
      const toolName = (hookData.tool_name || '').toLowerCase();
      return loadHookConfig(config.post_tool_use_failure?.[toolName] || config.post_tool_use_failure);
    }
    case 'PermissionRequest': {
      const toolName = (hookData.tool_name || '').toLowerCase();
      // 支持按工具和通用配置
      return loadHookConfig(config.permission_request?.[toolName] || config.permission_request);
    }

    // ── 会话事件（按子类型匹配）──
    case 'SessionStart': {
      const source = hookData.source || 'startup';
      return loadHookConfig(config.session_start?.[source]);
    }
    case 'SessionEnd': {
      const reason = hookData.reason || 'other';
      return loadHookConfig(config.session_end?.[reason]);
    }

    // ── 通知事件（按通知类型匹配）──
    case 'Notification': {
      const type = hookData.notification_type || '';
      return loadHookConfig(config.notification?.[type]);
    }

    // ── Compact 事件（按触发方式匹配）──
    case 'PreCompact': {
      const trigger = hookData.trigger || 'manual';
      return loadHookConfig(config.pre_compact?.[trigger]);
    }
    case 'PostCompact': {
      const trigger = hookData.trigger || 'manual';
      return loadHookConfig(config.post_compact?.[trigger]);
    }

    // ── Subagent 事件（按代理类型匹配）──
    case 'SubagentStart': {
      const agentType = (hookData.agent_type || '').toLowerCase();
      return loadHookConfig(config.subagent_start?.[agentType] || config.subagent_start);
    }
    case 'SubagentStop': {
      const agentType = (hookData.agent_type || '').toLowerCase();
      return loadHookConfig(config.subagent_stop?.[agentType] || config.subagent_stop);
    }

    // ── 错误事件（按错误类型匹配）──
    case 'StopFailure': {
      const errType = (hookData.error || '').toLowerCase();
      return loadHookConfig(config.stop_failure?.[errType] || config.stop_failure);
    }

    // ── 配置变更事件（按配置源匹配）──
    case 'ConfigChange': {
      const source = hookData.source || '';
      return loadHookConfig(config.config_change?.[source] || config.config_change);
    }

    // ── 文件变更事件 ──
    case 'FileChanged':
      return loadHookConfig(config.file_changed);

    // ── 目录变更事件 ──
    case 'CwdChanged':
      return loadHookConfig(config.cwd_changed);

    // ── 指令加载事件（按加载原因匹配）──
    case 'InstructionsLoaded': {
      const reason = hookData.load_reason || '';
      return loadHookConfig(config.instructions_loaded?.[reason] || config.instructions_loaded);
    }

    // ── Team 事件 ──
    case 'TeammateIdle':
      return loadHookConfig(config.teammate_idle);
    case 'TaskCompleted':
      return loadHookConfig(config.task_completed);

    // ── Worktree 事件 ──
    case 'WorktreeCreate':
      return loadHookConfig(config.worktree_create);
    case 'WorktreeRemove':
      return loadHookConfig(config.worktree_remove);

    // ── Elicitation 事件（按 MCP 服务器名称匹配）──
    case 'Elicitation': {
      const server = hookData.mcp_server_name || '';
      return loadHookConfig(config.elicitation?.[server] || config.elicitation);
    }
    case 'ElicitationResult': {
      const server = hookData.mcp_server_name || '';
      return loadHookConfig(config.elicitation_result?.[server] || config.elicitation_result);
    }

    // ── 简单事件 ──
    case 'Stop':
      return loadHookConfig(config.stop);
    case 'UserPromptSubmit':
      return loadHookConfig(config.user_prompt_submit);

    default:
      debug(`未知事件: ${eventName}`);
      return null;
  }
}

// ─── 模板渲染 ────────────────────────────────────────────────────────────────────

/**
 * 简化的 Jinja2 风格模板渲染
 * 支持 {{ var }}, {{ var | default('') }}, {{ obj.key }}
 */
function renderTemplate(template, context) {
  if (!template) return '';

  return template.replace(/\{\{(.+?)\}\}/g, (_, expr) => {
    expr = expr.trim();

    // 处理 filter: var | default('xxx')
    const filterMatch = expr.match(/^(.+?)\s*\|\s*default\(['"](.+?)['"]\)\s*$/);
    if (filterMatch) {
      const val = resolveValue(filterMatch[1].trim(), context);
      return val != null && val !== '' ? String(val) : filterMatch[2];
    }

    // 处理 filter: var | length
    const lengthMatch = expr.match(/^(.+?)\s*\|\s*length\s*$/);
    if (lengthMatch) {
      const val = resolveValue(lengthMatch[1].trim(), context);
      if (Array.isArray(val)) return String(val.length);
      if (typeof val === 'string') return String(val.length);
      return '0';
    }

    const val = resolveValue(expr, context);
    return val != null ? String(val) : '';
  });
}

function resolveValue(path, context) {
  // 支持 obj.key.subkey 和 obj.get('key', [])
  const getMatch = path.match(/^(.+?)\.get\(['"](.+?)['"](?:,\s*(.+?))?\)$/);
  if (getMatch) {
    const obj = resolveValue(getMatch[1], context);
    if (obj && typeof obj === 'object') {
      return obj[getMatch[2]] ?? (getMatch[3] ? eval(getMatch[3]) : undefined);
    }
    return getMatch[3] ? eval(getMatch[3]) : undefined;
  }

  const parts = path.split('.');
  let val = context;
  for (const part of parts) {
    if (val == null || typeof val !== 'object') return undefined;
    val = val[part];
  }
  return val;
}

// ─── 上下文提取 ──────────────────────────────────────────────────────────────────

function extractContext(hookData) {
  const context = { ...hookData };

  // 提取 file_path
  if (hookData.tool_input?.file_path) {
    context.file_path = hookData.tool_input.file_path;
    context.file_name = basename(hookData.tool_input.file_path);
  }

  // 时间
  const now = new Date();
  context.time_now = `${now.getFullYear()}年${String(now.getMonth() + 1).padStart(2, '0')}月${String(now.getDate()).padStart(2, '0')}日 ${String(now.getHours()).padStart(2, '0')}点${String(now.getMinutes()).padStart(2, '0')}分`;
  context.timestamp = now.getTime() / 1000;

  // 项目名
  context.plugin_name = PLUGIN_NAME;
  context.project_name = basename(PROJECT_DIR);
  if (hookData.cwd && typeof hookData.cwd === 'string') {
    context.project_name = basename(hookData.cwd);
  }

  // tool_response success
  if (hookData.tool_response?.success != null) {
    context.success = hookData.tool_response.success ? '成功' : '失败';
  }

  // last_assistant_message（从 hookData 直接读取，Claude Code 新版本会提供此字段）
  if (!context.last_assistant_message) {
    context.last_assistant_message = hookData.last_assistant_message || '';
  }

  return context;
}

// ─── 通知执行（委托给 Python notify.py）─────────────────────────────────────────

function executeNotification(hookConfig, eventName, context) {
  if (!hookConfig || !hookConfig.enabled) {
    debug(`Hook ${eventName} 未启用`);
    return;
  }

  const message = renderTemplate(
    hookConfig.message || `${eventName} 事件已触发`,
    context
  );

  if (!message.trim()) {
    debug(`Hook ${eventName} 消息为空`);
    return;
  }

  info(`弹出提示: ${message.slice(0, 100)}...`);

  // 调用 Python notify.py 执行通知和 TTS（跨平台 Swift/Tk overlay）
  const notifyPy = join(PLUGIN_ROOT, 'scripts', 'notify_cli.py');

  // 异步执行，不阻塞主流程
  try {
    const args = [
      'run', '--directory', PLUGIN_ROOT,
      notifyPy,
      '--message', message,
      '--event', eventName,
    ];
    if (hookConfig.play_sound) args.push('--play-sound');

    const child = execFile('uv', args, {
      env: {
        ...process.env,
        PLUGIN_NAME,
        CLAUDE_PLUGIN_ROOT: PLUGIN_ROOT,
        CLAUDE_PROJECT_DIR: PROJECT_DIR,
      },
      timeout: 30000,
    }, (err, stdout, stderr) => {
      if (err) debug(`notify 执行错误: ${err.message}`);
      if (stderr) debug(`notify stderr: ${stderr}`);
    });
    child.unref();
  } catch (e) {
    error(`启动通知失败: ${e.message}`);
  }
}

// ─── SessionStart AGENT.md 处理 ─────────────────────────────────────────────────

function handleSessionStartAgentMd() {
  const agentMdPath = join(PLUGIN_ROOT, 'AGENT.md');
  if (existsSync(agentMdPath)) {
    const content = readFileSync(agentMdPath, 'utf-8');
    process.stdout.write(content.replace(/\$\{CLAUDE_PLUGIN_ROOT\}/g, PLUGIN_ROOT));
  }
}

// ─── 主入口 ──────────────────────────────────────────────────────────────────────

function main() {
  let input = '';

  process.stdin.setEncoding('utf-8');
  process.stdin.on('data', chunk => { input += chunk; });
  process.stdin.on('end', () => {
    try {
      const hookData = JSON.parse(input);
      if (!hookData || typeof hookData !== 'object') {
        error('Hook 数据必须是 JSON 对象');
        process.exit(1);
      }

      const eventName = (hookData.hook_event_name || '').trim();
      if (!eventName) {
        error('缺少必需的 hook_event_name 字段');
        process.exit(1);
      }

      info(`处理 Hook 事件: ${eventName}`);
      debug(`Hook 数据: ${JSON.stringify(hookData).slice(0, 500)}`);

      // SessionStart 特殊处理：输出 AGENT.md
      if (eventName === 'SessionStart') {
        handleSessionStartAgentMd();
      }

      // Stop 事件忽略 subagent（SubagentStop 有专门的事件）
      if (eventName === 'Stop' && hookData.subagent_type) {
        debug('Stop 事件来自 subagent，跳过（由 SubagentStop 处理）');
        return;
      }

      const config = loadConfig();
      const context = extractContext(hookData);
      const hookConfig = getHookConfig(config, eventName, hookData);

      if (!hookConfig) {
        debug(`未找到 ${eventName} 的 Hook 配置`);
        return;
      }

      executeNotification(hookConfig, eventName, context);

      info(`Hook 事件 ${eventName} 处理完成`);

      // 输出 JSON 结果（不阻断 Claude Code）
      const output = JSON.stringify({ continue: true });
      process.stdout.write(output);

    } catch (e) {
      if (e instanceof SyntaxError) {
        error(`JSON 解析失败: ${e.message}`);
      } else {
        error(`Hook 处理失败: ${e.message}`);
      }
      process.exit(1);
    }
  });
}

main();
