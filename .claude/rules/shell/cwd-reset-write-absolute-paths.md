# Bash 的 cwd 不保证跨调用保留：写文件一律绝对路径，生成后点名核对

agent / worktree 子会话里 harness 会把 Bash 的 cwd 重置回工作目录，与主对话「cwd 跨调用
保留」相反。heredoc、`>` 重定向、`npm install` 只认命令执行那一刻的 cwd，重置后全部写错
目录。

- 写文件（heredoc / `>` / `tee`）和装依赖（`npm --prefix <dir> install`）一律带绝对路径或
  `--prefix`，不依赖上一条命令留下的 cwd
- 内联脚本（`python3 - <<EOF`）里的 `open()` 读写路径同样写绝对路径：它吃的是脚本执行那一刻
  的 cwd，cwd 被重置后相对路径直接 FileNotFoundError，整段脚本报废重跑
- 生成一批文件后 `ls` 目标目录核对数目和文件名，不信退出码——后台任务会吞报错
- 误写仓库根的被跟踪文件，先 `git diff` 确认没有要保留的内容，再 `git checkout -- <path>`
  从 HEAD 恢复
