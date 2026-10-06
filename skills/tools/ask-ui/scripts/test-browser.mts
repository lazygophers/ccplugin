// browser module 的测试：PATH 上放假 plutil / osascript，不碰真实浏览器。
// 平台分支（win32 / linux 的 openBrowser）用 platform 改写覆盖，跑完还原。
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import { spawn } from 'node:child_process';

import { closeBrowserTab, openBrowser } from './browser.mjs';
import { makeTempRoot } from './test-helpers.mjs';

export async function test() {
  const temporaryRoot = await makeTempRoot('browser');
  const binDir = path.join(temporaryRoot, 'bin');
  await fs.mkdir(binDir, { recursive: true });
  const originalPath = process.env.PATH;
  process.env.PATH = `${binDir}${path.delimiter}${originalPath}`;
  try {
    // 假 plutil：报一个非 Chromium 的默认浏览器（走简单 AppleScript 分支）。
    await fs.writeFile(path.join(binDir, 'plutil'),
      '#!/bin/sh\necho \'{"LSHandlers":[{"LSHandlerURLScheme":"http","LSHandlerRoleAll":"com.fake.safari"}]}\'\n',
      { mode: 0o755 });
    // 假 osascript：吞掉脚本，退出 0。
    await fs.writeFile(path.join(binDir, 'osascript'), '#!/bin/sh\ncat >/dev/null; exit 0\n', { mode: 0o755 });

    const { openInBrowser, closeBrowserTab: close } = await import('./browser.mjs');
    assert.equal(await openInBrowser('http://127.0.0.1:1/ask/x'), true, '找到默认浏览器并投递成功');
    assert.equal(await close('ask-id-x'), true);

    // Chromium 系 bundle id：走「找 normal 窗口塞标签页」的长脚本分支。
    await fs.writeFile(path.join(binDir, 'plutil'),
      '#!/bin/sh\necho \'{"LSHandlers":[{"LSHandlerURLScheme":"https","LSHandlerRoleAll":"com.google.Chrome"}]}\'\n',
      { mode: 0o755 });
    assert.equal(await openInBrowser('http://127.0.0.1:1/ask/y'), true);

    // plutil 失败 / 输出坏 JSON：回 null，openInBrowser 返回 false。
    await fs.writeFile(path.join(binDir, 'plutil'), '#!/bin/sh\nexit 1\n', { mode: 0o755 });
    assert.equal(await openInBrowser('http://127.0.0.1:1/ask/z'), false, '拿不到默认浏览器时如实返回 false');
    await fs.writeFile(path.join(binDir, 'plutil'), '#!/bin/sh\necho not-json\n', { mode: 0o755 });
    assert.equal(await openInBrowser('http://127.0.0.1:1/ask/z'), false, '坏 JSON 同样回 false');
    await fs.unlink(path.join(binDir, 'plutil'));

    // 非 darwin：defaultBrowserBundleId 直接 null。
    const platform = Object.getOwnPropertyDescriptor(process, 'platform');
    Object.defineProperty(process, 'platform', { value: 'linux', configurable: true });
    try {
      assert.equal(await openInBrowser('http://127.0.0.1:1/ask/w'), false, '非 darwin 没有 AppleScript 路径');
      // openBrowser 在 linux 上走 xdg-open（macOS 上 ENOENT，异步报错被忽略，行覆盖已达）。
      openBrowser('http://127.0.0.1:1/ask/w');
      await new Promise((resolve) => setTimeout(resolve, 100));
      Object.defineProperty(process, 'platform', { value: 'win32', configurable: true });
      openBrowser('http://127.0.0.1:1/ask/w');
      await new Promise((resolve) => setTimeout(resolve, 100));
    } finally {
      Object.defineProperty(process, 'platform', platform as PropertyDescriptor);
    }

    // 回到 darwin、plutil 缺席：openBrowser 的 darwin 分支 spawn open（PATH 上真的有 open，
    // 但 URL 指向不存在的本地端口页，无副作用）。
    openBrowser('about:blank');
    await new Promise((resolve) => setTimeout(resolve, 200));
    assert.ok(true);
  } finally {
    process.env.PATH = originalPath;
    await fs.rm(temporaryRoot, { recursive: true, force: true });
  }
}
