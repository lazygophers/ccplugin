# 读 GitHub issue 用 `gh issue view <N> --json title,body,comments`，不用 `--comments`

出现 `gh issue view <N> --comments` EXIT=0、0 行时改用固定写法。固定写法：`gh issue view <N> --json title,body,comments`（要精简再加 `--jq`）。
