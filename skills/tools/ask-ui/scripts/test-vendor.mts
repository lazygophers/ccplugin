// vendor module 的测试：缓存命中直接回文件路径，不联网。
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';

import { ensureVendor } from './vendor.mjs';
import { makeTempRoot } from './test-helpers.mjs';

export async function test() {
  const temporaryRoot = await makeTempRoot('vendor');
  try {
    const vendorDir = path.join(temporaryRoot, 'vendor');
    await fs.mkdir(vendorDir, { recursive: true });
    await fs.writeFile(path.join(vendorDir, 'marked-15.0.7.min.js'), 'cached-body');
    process.env.ASK_UI_VENDOR_DIR = vendorDir;
    try {
      const cacheFile = await ensureVendor('marked');
      assert.equal(cacheFile, path.join(vendorDir, 'marked-15.0.7.min.js'), '命中缓存应直接返回文件路径');
      assert.equal(await fs.readFile(cacheFile, 'utf8'), 'cached-body');
    } finally {
      delete process.env.ASK_UI_VENDOR_DIR;
    }


  {
    const emptyDir = path.join(temporaryRoot, 'vendor-empty');
    process.env.ASK_UI_VENDOR_DIR = emptyDir;
    const originalFetch = globalThis.fetch;
    const calls: string[] = [];
    globalThis.fetch = (async (url: unknown) => {
      calls.push(String(url));
      return { ok: true, arrayBuffer: async () => new TextEncoder().encode('downloaded-body').buffer };
    }) as typeof fetch;
    try {
      const downloaded = await ensureVendor('marked');
      assert.equal(downloaded, path.join(emptyDir, 'marked-15.0.7.min.js'));
      assert.equal(await fs.readFile(downloaded, 'utf8'), 'downloaded-body');
      assert.match(calls[0], /cdn\.jsdelivr\.net\/npm\/marked@15\.0\.7/);
      // 下载失败：非 2xx 抛错，下一次调用重新发起（失败不留缓存）。
      globalThis.fetch = (async () => ({ ok: false, status: 404 })) as unknown as typeof fetch;
      await assert.rejects(ensureVendor('mermaid'), /404/);
    } finally {
      globalThis.fetch = originalFetch;
      delete process.env.ASK_UI_VENDOR_DIR;
    }
  }

  } finally {
    await fs.rm(temporaryRoot, { recursive: true, force: true });
  }

  // 下载路径：stub 掉全局 fetch，不联网。缓存目录为空时落盘并回路径。
}
