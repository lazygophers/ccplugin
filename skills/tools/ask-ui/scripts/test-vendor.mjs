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
  } finally {
    await fs.rm(temporaryRoot, { recursive: true, force: true });
  }
}
