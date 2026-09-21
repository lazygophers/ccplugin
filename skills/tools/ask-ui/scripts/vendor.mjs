// 渲染组件缓存 module：页面用到的第三方组件（Mermaid、marked、DOMPurify、
// highlight.js）不进仓库，首次用到时下载到公共缓存，之后所有项目共用同一份，
// 离线也能渲染。并发的同名组件请求只触发一次下载，后到的等同一个 promise。
import { existsSync } from 'node:fs';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';

export const VENDOR = {
  mermaid: {
    version: '11.16.1',
    url: (version) => `https://cdn.jsdelivr.net/npm/mermaid@${version}/dist/mermaid.min.js`,
  },
  marked: {
    version: '15.0.7',
    url: (version) => `https://cdn.jsdelivr.net/npm/marked@${version}/marked.min.js`,
  },
  purify: {
    version: '3.2.4',
    url: (version) => `https://cdn.jsdelivr.net/npm/dompurify@${version}/dist/purify.min.js`,
  },
  highlight: {
    version: '11.11.1',
    url: (version) => `https://cdn.jsdelivr.net/npm/@highlightjs/cdn-assets@${version}/highlight.min.js`,
  },
};

function vendorCacheRoot() {
  return process.env.ASK_UI_VENDOR_DIR || path.join(os.homedir(), '.agents', 'ask-ui', 'vendor');
}

function vendorCacheFile(name) {
  return path.join(vendorCacheRoot(), `${name}-${VENDOR[name].version}.min.js`);
}

const vendorDownloads = new Map();

export async function ensureVendor(name) {
  const cacheFile = vendorCacheFile(name);
  if (existsSync(cacheFile)) return cacheFile;
  if (!vendorDownloads.has(name)) {
    const url = VENDOR[name].url(VENDOR[name].version);
    vendorDownloads.set(name, (async () => {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Failed to download ${name}: ${response.status} ${url}`);
      }
      const body = Buffer.from(await response.arrayBuffer());
      await fs.mkdir(vendorCacheRoot(), { recursive: true });
      const temporary = `${cacheFile}.${process.pid}.tmp`;
      await fs.writeFile(temporary, body);
      await fs.rename(temporary, cacheFile);
      return cacheFile;
    })().finally(() => { vendorDownloads.delete(name); }));
  }
  return vendorDownloads.get(name);
}
