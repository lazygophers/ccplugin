# Bash 的 cwd 不保证跨调用保留：写文件一律绝对路径，生成后点名核对

agent / worktree 子会话里 harness 会把 Bash 的 cwd 重置回工作目录，与主对话「cwd 跨调用
保留」相反。heredoc、`>` 重定向、`npm install` 只认命令执行那一刻的 cwd，重置后全部写错
目录：2026-10-06 ask-ui 迁 TS 时 `log/vendor/browser.mts` 写到了仓库根，
package.json / tsconfig.json / .gitignore / package-lock.json / node_modules 一并落在根目录，
两个被跟踪文件（.gitignore、package-lock.json）被迫从 HEAD 恢复；目标子目录不存在的
`.d.ts` 生成，`cat` 报错还被后台任务吞掉，静默失败。

- 写文件（heredoc / `>` / `tee`）和装依赖（`npm --prefix <dir> install`）一律带绝对路径或
  `--prefix`，不依赖上一条命令留下的 cwd
- 生成一批文件后 `ls` 目标目录核对数目和文件名，不信退出码——后台任务会吞报错
- 误写仓库根的被跟踪文件，先 `git diff` 确认没有要保留的内容，再 `git checkout -- <path>`
  从 HEAD 恢复

出处：2026-10-06 ask-ui .mjs → TypeScript 迁移 session 实录（本文件即该 session 复盘产物）。
