# 读 ask-me 答案：先 Read 整个 stdout 文件，确认读到答案，再单独删，不与解析命令串联

ask-me 的 stdout.json 是用户答案的唯一副本：ask 返回后会自动清理 `.ask-me` 目录，
文件删了 resume 报 ENOENT，只能重问用户一次。

- 答案结构是 `answers` 对象下再套 `answers.answers`，不要凭印象写 `json.load` 取值路径。
  先 `Read` 整个 stdout 文件看结构，再取字段。
- 解析命令和 `rm` 不用 `;` 串联（`;` 在前一条失败时照样执行后一条）。分两次调用：
  第一次只读/解析，输出里确认拿到了答案；第二次才 `rm`。
- 确认读到之前，答案内容先记进任务状态文件「已确认」段，再删。

出处：2026-11-09 tracking-progress 任务状态文件路径 session：`python3 -c "…json.load…"; rm -f
<questions.json> <stdout.json>` 因取值路径猜错（答案在 answers.answers）报错，rm 照跑，
答案文件丢失，用户被重问一次。
