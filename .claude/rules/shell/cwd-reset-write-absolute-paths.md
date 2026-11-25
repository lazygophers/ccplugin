# Bash 的 cwd 不保证跨调用保留：写文件一律绝对路径，生成后点名核对

适用于 agent / worktree 子会话：Bash 的 cwd 每次调用后重置回工作目录。

- 写文件（heredoc / `>` / `tee`）和装依赖（`npm --prefix <dir> install`）一律带绝对路径或
  `--prefix`，不依赖上一条命令留下的 cwd
- 内联脚本（`python3 - <<EOF`）里的 `open()` 读写路径同样写绝对路径；出现 FileNotFoundError 时把相对路径改成绝对路径后重跑
- 生成一批文件后 `ls` 目标目录核对数目和文件名，不信退出码
- 误写仓库根的被跟踪文件，先 `git diff` 确认没有要保留的内容，再 `git checkout -- <path>`
  从 HEAD 恢复
