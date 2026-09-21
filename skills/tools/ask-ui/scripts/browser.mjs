// 浏览器控制 module：打开表单、提交后关掉那一页。全平台差异（macOS AppleScript /
// LaunchServices、Windows rundll32、Linux xdg-open）都收在这里，调用方只拿 URL。
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { spawn } from 'node:child_process';

function runCapturing(command, args) {
  return new Promise((resolve) => {
    const child = spawn(command, args);
    let out = '';
    child.stdout.on('data', (chunk) => { out += chunk; });
    child.on('error', () => resolve(null));
    child.on('close', (code) => resolve(code === 0 ? out : null));
  });
}

// 本地文件一律进默认浏览器的新标签页：`.md` 之类扔给 `open` 会拉起编辑器，读一眼
// 报告还得等编辑器启动。顺带解决锚点——macOS 的 open 打开 file:// 时会把 `#锚点`
// 剥掉（`open`、`open -u`、`open -a <浏览器>` 三种写法实测都一样），唯一留得住的
// 是把整条 URL 直接投给浏览器 app，所以先问 LaunchServices 默认浏览器是谁，再用
// AppleScript 投给它。
async function defaultBrowserBundleId() {
  if (process.platform !== 'darwin') return null;
  const plist = path.join(
    os.homedir(),
    'Library/Preferences/com.apple.LaunchServices/com.apple.launchservices.secure.plist',
  );
  const raw = await runCapturing('plutil', ['-convert', 'json', '-o', '-', plist]);
  if (!raw) return null;
  try {
    return (JSON.parse(raw).LSHandlers || [])
      .find((handler) => handler.LSHandlerURLScheme === 'http')?.LSHandlerRoleAll || null;
  } catch {
    return null;
  }
}

// Chrome 系的 `open location` 只在「最前面那个窗口能收标签页」时才开标签页：前台是
// app 模式 / 弹出窗口、或窗口全被最小化时，它改开一整个新窗口。所以对 Chrome 系先自己
// 找一个 mode 为 normal 的普通窗口往里塞标签页，找不到才退回 `open location`。
const CHROMIUM_BUNDLE = /chrome|chromium|edgemac|brave|vivaldi|opera/i;

export async function openInBrowser(url) {
  const bundleId = await defaultBrowserBundleId();
  if (!bundleId) return false;
  // URL 要进 AppleScript 的字符串字面量，反斜杠和引号得转义。
  const quoted = url.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
  const script = CHROMIUM_BUNDLE.test(bundleId)
    ? `tell application id "${bundleId}"
  activate
  set target to missing value
  repeat with candidate in windows
    if mode of candidate is "normal" then
      set target to candidate
      exit repeat
    end if
  end repeat
  if target is missing value then
    open location "${quoted}"
  else
    tell target to make new tab with properties {URL:"${quoted}"}
    set index of target to 1
    set active tab index of target to (count of tabs of target)
  end if
end tell`
    : `tell application id "${bundleId}" to open location "${quoted}"`;
  return await runCapturing('osascript', ['-e', script]) !== null;
}

// 提交完这一页就没用了。浏览器只允许脚本关闭自己 window.open 出来的标签页，
// 而表单是 `open` 从外面打开的，所以 window.close() 必然失败，只能由服务端来关。
// 认页面靠 askId——它在 URL 路径里，天然唯一。只有 macOS 能这么关，其余平台
// 退回页面上那张「可以关闭这个标签页了」的终态卡。
export async function closeBrowserTab(askId) {
  const bundleId = await defaultBrowserBundleId();
  if (!bundleId) return false;
  const script = `tell application id "${bundleId}" to close (every tab of every window whose URL contains "${askId}")`;
  return await runCapturing('osascript', ['-e', script]) !== null;
}

// CLI 打开表单页用的兜底路径：不经 AppleScript，按平台直接投给系统打开器。
export function openBrowser(url) {
  let child;
  if (process.platform === 'win32') {
    child = spawn('rundll32.exe', ['url.dll,FileProtocolHandler', url], {
      detached: true,
      stdio: 'ignore',
      windowsHide: true,
    });
  } else if (process.platform === 'darwin') {
    child = spawn('open', [url], { detached: true, stdio: 'ignore' });
  } else {
    child = spawn('xdg-open', [url], { detached: true, stdio: 'ignore' });
  }
  child.unref();
}
