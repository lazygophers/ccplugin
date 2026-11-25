# 大块字符串常量整段替换：标记拼接脚本，不用 Edit

适用于「HTML 页面长在 Python 字符串里」的文件（如 tracking-progress 的
tracking_progress.py）。改法：写一次性 python 脚本做标记拼接——以稳定的起止标记（赋值语句边界、
`<script>`/`</script>`、`def` 行）定位旧块，其余字节原样保留，只插入新块；跑完
对 JS 块 `node --check`、对整文件跑既有 pytest 回归。

适用判断：替换块 > ~50 行且在字符串常量里 → 标记拼接脚本；小片段仍用 Edit。
