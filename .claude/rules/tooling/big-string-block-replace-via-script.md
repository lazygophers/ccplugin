# 大块字符串常量整段替换：标记拼接脚本，不用 Edit

「HTML 页面长在 Python 字符串里」的文件（如 tracking-progress 的
tracking_progress.py，1600+ 行），CSS/JS 是几百行的拼接字符串常量。对这种块用
Edit 整段替换，要原文匹配几百行——缩进、引号转义任何一处对不上就 fail，或锚到
错误位置错位替换；整文件重写又超出外科手术范围。

改法：写一次性 python 脚本做标记拼接——以稳定的起止标记（赋值语句边界、
`<script>`/`</script>`、`def` 行）定位旧块，其余字节原样保留，只插入新块；跑完
对 JS 块 `node --check`、对整文件跑既有 pytest 回归。

适用判断：替换块 > ~50 行且在字符串常量里 → 标记拼接脚本；小片段仍用 Edit。

出处：2026-10-23 tracking-progress 进度页重设计 session，重写 CSS 与 render()
（commits 2932d20、1ff1dfa3、08fc85ff）。
