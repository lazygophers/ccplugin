// adapters + wake 成功路径的测试：用 PATH 上的假 CLI（claude / codex）替代真宿主，
// 不碰真实会话。process-utils 的 win32 分支用 platform 改写覆盖，跑完还原。
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import { collectProcess, spawnCli } from './adapters/process-utils.mjs';
import { triggerWake } from './wake.mjs';
import { createAsk, loadAskBundle } from './store.mjs';
import { makeTempRoot } from './test-helpers.mjs';
export async function test() {
    const temporaryRoot = await makeTempRoot('adapters');
    const dataRoot = path.join(temporaryRoot, 'data');
    const binDir = path.join(temporaryRoot, 'bin');
    await fs.mkdir(binDir, { recursive: true });
    const originalPath = process.env.PATH;
    process.env.PATH = `${binDir}${path.delimiter}${originalPath}`;
    try {
        // 假 claude：吃掉 -p --resume …，回一行 JSON。
        await fs.writeFile(path.join(binDir, 'claude'), '#!/bin/sh\necho \'{"subtype":"success","result":"done"}\'\n', { mode: 0o755 });
        // 假 codex：app-server stdio 协议，按 id 回 result，最后主动播 turn/completed。
        await fs.writeFile(path.join(binDir, 'codex'), [
            '#!/usr/bin/env node',
            'const lines = [];',
            'process.stdin.setEncoding("utf8");',
            'let buffer = "";',
            'process.stdin.on("data", (chunk) => {',
            '  buffer += chunk;',
            '  let index;',
            '  while ((index = buffer.indexOf("\\n")) >= 0) {',
            '    const line = buffer.slice(0, index); buffer = buffer.slice(index + 1);',
            '    if (!line.trim()) continue;',
            '    const message = JSON.parse(line);',
            '    if (message.id !== undefined) process.stdout.write(`${JSON.stringify({ id: message.id, result: { ok: true } })}\\n`);',
            '    if (message.method === "turn/start") {',
            '      process.stdout.write(`${JSON.stringify({ method: "turn/completed", params: { turn: "done" } })}\\n`);',
            '      process.exit(0);',
            '    }',
            '  }',
            '});',
        ].join('\n'), { mode: 0o755 });
        // ---- wake 成功：claude-code ----
        const claudeAsk = await createAsk({
            title: 'claude 唤醒',
            wake: { mode: 'auto', provider: 'claude-code', sessionRef: 'session-abc' },
            questions: [{ id: 'q1', type: 'text', text: '甲' }],
        }, { dataDir: dataRoot, cwd: temporaryRoot });
        const claudeResult = await triggerWake(dataRoot, claudeAsk.askId);
        assert.equal(claudeResult.status, 'succeeded');
        const claudeBundle = await loadAskBundle(dataRoot, claudeAsk.askId);
        assert.equal(claudeBundle.ask.wakeState?.status, 'succeeded');
        assert.match(String(claudeBundle.ask.wakeState?.logFile), /wake\/\d+-claude-code\.json$/);
        // ---- wake 成功：codex-app-server（JSON-RPC 全流程）----
        const codexAsk = await createAsk({
            title: 'codex 唤醒',
            wake: { mode: 'auto', provider: 'codex-app-server', sessionRef: 'thread-xyz' },
            questions: [{ id: 'q1', type: 'text', text: '甲' }],
        }, { dataDir: dataRoot, cwd: temporaryRoot });
        const codexResult = await triggerWake(dataRoot, codexAsk.askId);
        assert.equal(codexResult.status, 'succeeded');
        assert.equal((await loadAskBundle(dataRoot, codexAsk.askId)).ask.wakeState?.status, 'succeeded');
        // ---- wake 失败：claude 非零退出 ----
        await fs.writeFile(path.join(binDir, 'claude'), '#!/bin/sh\necho "boom" >&2; exit 3\n', { mode: 0o755 });
        const failedAsk = await createAsk({
            title: '唤醒失败',
            wake: { mode: 'auto', provider: 'claude-code', sessionRef: 'session-abc' },
            questions: [{ id: 'q1', type: 'text', text: '甲' }],
        }, { dataDir: dataRoot, cwd: temporaryRoot });
        const failed = await triggerWake(dataRoot, failedAsk.askId);
        assert.equal(failed.status, 'failed');
        assert.match(failed.error, /boom|code 3/);
        assert.equal((await loadAskBundle(dataRoot, failedAsk.askId)).ask.wakeState?.status, 'failed');
        // ---- wake 失败：codex 握手前退出 ----
        await fs.writeFile(path.join(binDir, 'codex'), '#!/bin/sh\nexit 7\n', { mode: 0o755 });
        const codexDead = await createAsk({
            title: 'codex 直接死',
            wake: { mode: 'auto', provider: 'codex-app-server', sessionRef: 'thread-xyz' },
            questions: [{ id: 'q1', type: 'text', text: '甲' }],
        }, { dataDir: dataRoot, cwd: temporaryRoot });
        const dead = await triggerWake(dataRoot, codexDead.askId);
        assert.equal(dead.status, 'failed');
        // ---- collectProcess：超时与非零退出 ----
        const slow = spawnCli(process.execPath, ['-e', 'setTimeout(() => {}, 100000)'], { stdio: ['ignore', 'pipe', 'pipe'] });
        await assert.rejects(collectProcess(slow, { timeoutMs: 300 }), /timed out/);
        const noisy = spawnCli(process.execPath, ['-e', 'console.error("noise"); process.exit(2)'], { stdio: ['ignore', 'pipe', 'pipe'] });
        await assert.rejects(collectProcess(noisy), /noise|code 2/);
        const clean = spawnCli(process.execPath, ['-e', 'console.log("out")'], { stdio: ['ignore', 'pipe', 'pipe'] });
        assert.deepEqual(await collectProcess(clean), { code: 0, stdout: 'out\n', stderr: '' });
        // ---- process-utils：spawn 失败走 error 事件 ----
        await assert.rejects(collectProcess(spawnCli('/nonexistent/definitely-missing-cli', [])), /ENOENT|spawn/);
        // ---- win32 分支：改写 platform 后 findWindowsScript / powershell / cmd 路径都走到 ----
        const platform = Object.getOwnPropertyDescriptor(process, 'platform');
        Object.defineProperty(process, 'platform', { value: 'win32', configurable: true });
        try {
            // .ps1 命中：findWindowsScript 找到 fake.ps1，再 spawn powershell.exe（macOS 上 ENOENT，
            // 走 child error 事件，行覆盖已达）。
            const winBin = path.join(temporaryRoot, 'winbin');
            await fs.mkdir(winBin, { recursive: true });
            await fs.writeFile(path.join(winBin, 'tool.ps1'), '', { mode: 0o755 });
            await fs.writeFile(path.join(winBin, 'tool.cmd'), '', { mode: 0o755 });
            process.env.PATH = `${winBin}${path.delimiter}${binDir}${path.delimiter}${originalPath}`;
            await assert.rejects(collectProcess(spawnCli('tool', ['x'])), /ENOENT|powershell/);
            // .cmd 命中：spawn(.cmd) 在 macOS 上报错，同样只求行覆盖。
            await fs.unlink(path.join(winBin, 'tool.ps1'));
            await assert.rejects(collectProcess(spawnCli('tool', ['x'])));
            // 都不命中：原样返回命令名。
            await assert.rejects(collectProcess(spawnCli('missing-tool', ['x'])));
        }
        finally {
            Object.defineProperty(process, 'platform', platform);
        }
    }
    finally {
        process.env.PATH = originalPath;
        await fs.rm(temporaryRoot, { recursive: true, force: true });
    }
}
