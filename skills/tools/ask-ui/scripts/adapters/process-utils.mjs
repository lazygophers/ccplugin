import { existsSync } from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';

function findWindowsScript(command) {
  const pathEntries = (process.env.PATH || '').split(path.delimiter);
  for (const entry of pathEntries) {
    for (const extension of ['.ps1', '.cmd', '.exe']) {
      const candidate = path.join(entry, `${command}${extension}`);
      if (existsSync(candidate)) return candidate;
    }
  }
  return command;
}

export function spawnCli(command, args, options = {}) {
  if (process.platform !== 'win32') {
    return spawn(command, args, { ...options, shell: false });
  }

  const executable = findWindowsScript(command);
  if (executable.toLowerCase().endsWith('.ps1')) {
    return spawn(
      'powershell.exe',
      [
        '-NoLogo',
        '-NoProfile',
        '-NonInteractive',
        '-ExecutionPolicy',
        'Bypass',
        '-File',
        executable,
        ...args,
      ],
      { ...options, shell: false, windowsHide: true },
    );
  }

  return spawn(executable, args, {
    ...options,
    shell: executable.toLowerCase().endsWith('.cmd'),
    windowsHide: true,
  });
}

export function collectProcess(child, { timeoutMs = 600_000 } = {}) {
  return new Promise((resolve, reject) => {
    let stdout = '';
    let stderr = '';
    const timer = setTimeout(() => {
      child.kill();
      reject(new Error(`Agent adapter timed out after ${timeoutMs}ms`));
    }, timeoutMs);

    child.stdout?.on('data', (chunk) => {
      if (stdout.length < 5_000_000) stdout += chunk.toString();
    });
    child.stderr?.on('data', (chunk) => {
      if (stderr.length < 1_000_000) stderr += chunk.toString();
    });
    child.on('error', (error) => {
      clearTimeout(timer);
      reject(error);
    });
    child.on('close', (code) => {
      clearTimeout(timer);
      if (code === 0) resolve({ code, stdout, stderr });
      else reject(new Error(stderr || `Agent adapter exited with code ${code}`));
    });
  });
}

