// http-server module 的测试：路由（静态/vendor/local/api）、鉴权、代码版本换进程、
// 提交后的生命周期。vendor 的缓存命中与读失败也经 /vendor 路由覆盖。
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';

import { startHttpServer, ensureServer } from './http-server.mjs';
import { createAsk, loadAskBundle } from './store.mjs';
import { makeTempRoot, ASK_UI_SCRIPT, stopDetachedServer, serverPidAlive } from './test-helpers.mjs';

export async function test() {
  const temporaryRoot = await makeTempRoot('http');
  const dataRoot = path.join(temporaryRoot, 'data');
  let server;
  try {
    const first = await createAsk({
      title: 'HTTP 路由用例',
      questions: [
        {
          id: 'scope',
          type: 'single',
          text: '范围',
          options: [{ id: 'personal', text: '个人', recommended: true, reason: '先小后大。' }, { id: 'team', text: '团队' }],
        },
        { id: 'context', type: 'text', text: '补充', required: false },
      ],
    }, { dataDir: dataRoot, cwd: temporaryRoot });

    const started = await startHttpServer({
      dataRoot,
      token: 'self-test-token',
      persistServerInfo: false,
    });
    server = started.server;
    const base = `http://127.0.0.1:${started.info.port}`;
    const headers = {
      Authorization: 'Bearer self-test-token',
      'Content-Type': 'application/json',
    };

    // 正文里的本地文件链接：交给默认浏览器开新标签页。浏览器不让 http:// 页面跳 file://，
    // 所以点击由 /local 代办。真跑 `open` 会在测试机上弹出程序，换成一个空转的命令。
    {
      const workspace = path.dirname(dataRoot);
      await fs.writeFile(path.join(workspace, 'report.html'), '<h1>审计报告</h1>\n');
      await fs.writeFile(path.join(workspace, 'notes.md'), '# 结论\n\n第一条\n');
      await fs.writeFile(path.join(workspace, 'danger.sh'), '#!/bin/sh\necho nope\n');
      // node 自己就是跨平台都在的可执行文件，拿它当空转打开器：它解析不了 .html 会直接
      // 退出，stdio 又是 ignore，不留痕迹。用 `true` 的话 Windows 上没有这个命令。
      process.env.ASK_UI_OPENER = process.execPath;

      const local = (query) => fetch(`${base}/local?${query}`, { headers });

      const html = await local(`path=${encodeURIComponent('report.html')}`);
      assert.equal(html.status, 200, '工作区相对路径的 html 应能打开');
      assert.equal(
        (await html.json()).opened,
        path.join(workspace, 'report.html'),
        '响应要回报打开的是哪个绝对路径，相对路径按工作区解析',
      );

      const absolute = await local(`path=${encodeURIComponent(path.join(workspace, 'report.html'))}`);
      assert.equal(absolute.status, 200, '绝对路径同样要能打开');

      const fileUrl = await local(`path=${encodeURIComponent(`file://${path.join(workspace, 'report.html')}`)}`);
      assert.equal(fileUrl.status, 200, 'file:// 前缀要被剥掉后照常打开');

      const anchored = await local(
        `path=${encodeURIComponent('report.html')}&hash=${encodeURIComponent('#2-节点体系')}`,
      );
      assert.equal(anchored.status, 200, '带锚点的链接不能把 # 当成文件名的一部分');

      const markdown = await local(`path=${encodeURIComponent('notes.md')}`);
      assert.equal(markdown.status, 200, '.md 同样交给默认浏览器');

      // `open` 能启动 .app / .sh / .command，正文里的一条链接不该有本事跑程序。
      const executable = await local(`path=${encodeURIComponent('danger.sh')}`);
      assert.equal(executable.status, 403, '可执行文件必须被白名单挡下');

      const missing = await local(`path=${encodeURIComponent('nope.md')}`);
      assert.equal(missing.status, 404, '文件不存在要报 404，不能静默当作打开了');

      const noToken = await fetch(`${base}/local?path=report.html`);
      assert.equal(noToken.status, 401, '/local 必须在 token 之后：没 token 不能碰本机文件');

      delete process.env.ASK_UI_OPENER;
    }

    // 渲染组件命中缓存时必须直接回文件，绝不联网：这是离线可用的前提。
    const vendorDir = path.join(temporaryRoot, 'vendor');
    await fs.mkdir(vendorDir, { recursive: true });
    const cachedVendors = {
      mermaid: 'mermaid-11.16.1.min.js',
      marked: 'marked-15.0.7.min.js',
      purify: 'purify-3.2.4.min.js',
      highlight: 'highlight-11.11.1.min.js',
    };
    for (const [name, file] of Object.entries(cachedVendors)) {
      await fs.writeFile(path.join(vendorDir, file), `globalThis.${name} = "cached";`);
    }
    process.env.ASK_UI_VENDOR_DIR = vendorDir;
    for (const name of Object.keys(cachedVendors)) {
      const vendorResponse = await fetch(`${base}/vendor/${name}.min.js`);
      assert.equal(vendorResponse.status, 200, `${name} 应命中缓存`);
      assert.equal(vendorResponse.headers.get('content-type'), 'text/javascript; charset=utf-8');
      assert.equal(await vendorResponse.text(), `globalThis.${name} = "cached";`);
    }
    // 未登记的组件名不得变成任意文件读取。
    assert.equal((await fetch(`${base}/vendor/unknown.min.js`)).status, 401);

    // 缓存文件读不出来（权限不对、被别的东西占了名字）时，服务必须回一个错误状态码
    // 并继续跑。读文件的错误是异步从流里冒出来的，漏挂监听会让整个进程连同全部活跃
    // 会话一起退出——页面那边看到的是所有请求突然全部连不上，不只是这一个组件挂了。
    const brokenVendorDir = path.join(temporaryRoot, 'vendor-broken');
    await fs.mkdir(path.join(brokenVendorDir, cachedVendors.mermaid), { recursive: true });
    process.env.ASK_UI_VENDOR_DIR = brokenVendorDir;
    // 读到一半才失败时头已经发出去了，只能断开连接，所以这里既可能拿到错误状态码，
    // 也可能是 fetch 直接抛错——两种都算「这一个请求没成」，不影响下面的判据。
    let brokenVendorOk = false;
    try {
      brokenVendorOk = (await fetch(`${base}/vendor/mermaid.min.js`)).ok;
    } catch {
      brokenVendorOk = false;
    }
    assert.equal(brokenVendorOk, false, '读不出来的组件文件不该当成功返回');
    process.env.ASK_UI_VENDOR_DIR = vendorDir;
    // 服务还活着：同一个端口上别的请求照常。
    assert.equal((await fetch(`${base}/vendor/marked.min.js`)).status, 200, '一个组件读失败不该拖垮整个服务');
    delete process.env.ASK_UI_VENDOR_DIR;

    const bundleResponse = await fetch(`${base}/api/asks/${first.askId}`, { headers });
    assert.equal(bundleResponse.status, 200);
    const bundle = await bundleResponse.json();
    assert.equal(bundle.ask.status, 'waiting_for_user');
    assert.equal(bundle.questions.questions.length, 2);
    assert.equal(bundle.answers, null);

    // 填到一半就落盘：关页、刷新、服务重启都要能把答案接回来。
    const answers = [
      { questionId: 'scope', selectedOptionIds: ['personal'], customText: '', supplementaryText: '先覆盖个人高频场景。' },
      { questionId: 'context', selectedOptionIds: [], customText: '先做本地 Demo。' },
    ];
    const draftResponse = await fetch(
      `${base}/api/asks/${first.askId}/draft`,
      { method: 'PUT', headers, body: JSON.stringify({ answers }) },
    );
    assert.equal(draftResponse.status, 200, '草稿要能写进服务端');
    const draftFile = path.join(dataRoot, 'asks', first.askId, 'draft.json');
    assert.ok(await fs.stat(draftFile), '草稿要落成 draft.json');
    const reopened = await fetch(`${base}/api/asks/${first.askId}`, { headers });
    assert.equal(
      (await reopened.json()).draft.answers[0].supplementaryText,
      '先覆盖个人高频场景。',
      '重新打开页面要能把草稿读回来',
    );
    // sendBeacon 只会发 POST，关标签页那一下全靠它，所以两种方法都得收。
    const beacon = await fetch(
      `${base}/api/asks/${first.askId}/draft`,
      { method: 'POST', headers, body: JSON.stringify({ answers }) },
    );
    assert.equal(beacon.status, 200, 'sendBeacon 的 POST 也要收');

    const submitResponse = await fetch(
      `${base}/api/asks/${first.askId}/answers`,
      { method: 'POST', headers, body: JSON.stringify({ submissionId: 'http-test', answers }) },
    );
    assert.equal(submitResponse.status, 200);
    assert.equal((await submitResponse.json()).duplicate, false);

    assert.ok(
      !(await fs.stat(draftFile).catch(() => null)),
      '提交之后草稿要删掉，别留一份半成品在旁边',
    );

    // 校验失败走 422，错误信息带回调用方。
    const invalidOther = await createAsk({
      title: '非法选项验证',
      questions: [
        {
          id: 'restricted',
          type: 'single',
          text: '固定选项',
          options: [
            { id: 'one', text: '选项一' },
            { id: 'two', text: '选项二' },
          ],
        },
      ],
    }, { dataDir: dataRoot, cwd: temporaryRoot });
    const rejected = await fetch(
      `${base}/api/asks/${invalidOther.askId}/answers`,
      {
        method: 'POST',
        headers,
        body: JSON.stringify({ answers: [{ questionId: 'restricted', selectedOptionIds: ['nope'], customText: '' }] }),
      },
    );
    assert.equal(rejected.status, 422);

    // 常驻服务把代码读进内存就不再看磁盘：改完 skill 得换掉进程，否则页面拿的是新
    // 前端、服务端还是旧逻辑，新加的路由一律 404（这是真踩过的坑）。
    {
      const versionRoot = path.join(temporaryRoot, 'version-data');
      const firstServer = await ensureServer(versionRoot);
      assert.ok(firstServer.pid, '第一次调用应拉起一个服务');
      assert.equal(
        firstServer.codeVersion,
        (await fs.stat(ASK_UI_SCRIPT)).mtimeMs,
        'server.json 要记下脚本当时的修改时间',
      );

      const reused = await ensureServer(versionRoot);
      assert.equal(reused.pid, firstServer.pid, '代码没变就该复用，不许每次都重启');

      // 把脚本的修改时间往后拨，等同于「skill 被改过了」。
      const original = await fs.stat(ASK_UI_SCRIPT);
      await fs.utimes(ASK_UI_SCRIPT, original.atime, new Date(original.mtimeMs + 5000));
      try {
        const restarted = await ensureServer(versionRoot);
        assert.notEqual(restarted.pid, firstServer.pid, '代码变了必须换掉旧进程');
        assert.equal(serverPidAlive(firstServer.pid), false, '旧进程要被停掉，不能留着占端口');
        await stopDetachedServer(versionRoot);
      } finally {
        await fs.utimes(ASK_UI_SCRIPT, original.atime, original.mtime);
      }
    }
  } finally {
    if (server) await new Promise((resolve) => server.close(resolve));
    await fs.rm(temporaryRoot, { recursive: true, force: true });
  }
}
