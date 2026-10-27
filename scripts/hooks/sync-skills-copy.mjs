#!/usr/bin/env node
// PostToolUse(Write|Edit)：编辑 skills/** 后自动同步到 ~/.agents/skills/<name>/（副本已存在才同步）。
// rsync 失败只报一行不阻断编辑流程；ask-me 在 ~/.claude/skills 的第三份副本此处不动。
import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const repo = dirname(dirname(dirname(fileURLToPath(import.meta.url))));

let buf = '';
process.stdin.on('data', (c) => (buf += c));
process.stdin.on('end', () => {
  try {
    const { file_path: fp } = JSON.parse(buf).tool_input ?? {};
    if (typeof fp === 'string' && fp.startsWith(repo + '/')) {
      const m = fp.slice(repo.length + 1).match(/^skills\/(?:tools|git|project)\/([^/]+)\//);
      if (m) {
        const dest = join(homedir(), '.agents', 'skills', m[1]);
        if (existsSync(dest)) {
          try {
            execFileSync(
              'rsync',
              ['-a', '--delete', '--exclude', 'node_modules', '--exclude', '.ask-me',
               join(repo, m[0]) + '/', dest],
              { stdio: 'ignore' },
            );
            console.log(`synced ${m[1]} → ${dest}`);
          } catch {
            console.error(`sync-skills-copy: rsync 同步 ${m[1]} 失败，请手工跑 CLAUDE.md 里的 rsync 命令`);
          }
        }
      }
    }
  } catch {}
  process.exit(0);
});
