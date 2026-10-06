import process from 'node:process';
import { collectProcess, spawnCli } from './process-utils.mjs';

export interface WakeRequest {
  binding: { sessionRef?: string | null; cwd?: string | null };
  prompt: string;
}

export async function wakeClaudeCode({ binding, prompt }: WakeRequest) {
  if (!binding?.sessionRef) {
    throw new Error('Claude Code auto wake requires wake.sessionRef');
  }

  const child = spawnCli(
    'claude',
    [
      '-p',
      '--resume',
      binding.sessionRef,
      '--output-format',
      'json',
      prompt,
    ],
    {
      cwd: binding.cwd || process.cwd(),
      env: process.env,
      stdio: ['ignore', 'pipe', 'pipe'],
    },
  );

  const result = await collectProcess(child);
  let parsed: unknown = null;
  try {
    parsed = JSON.parse(result.stdout.trim());
  } catch {
    // Preserve raw output when a CLI version emits non-JSON diagnostics.
  }

  return { provider: 'claude-code', parsed, ...result };
}
