# 读 GitHub issue 用 `gh issue view <N> --json title,body,comments`，不用 `--comments`

agent 的 Bash 不是 TTY。非 TTY 下 `gh issue view <N> --comments` 只输出评论、不输出
正文；issue 没有评论时输出 0 行、退出码 0，看起来像「读到了空 issue」。`--help`
写的「includes the issue details and comments」只对终端输出成立。

固定写法：`gh issue view <N> --json title,body,comments`（要精简再加 `--jq`）。
