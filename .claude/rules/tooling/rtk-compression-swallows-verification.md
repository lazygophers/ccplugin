# RTK 压缩输出吞验证信息：被压掉的不算结论；rtk proxy 下别用 `echo ===`

RTK hook 自动把命令包进 `rtk` 代理并压缩输出。两个坑：

1. **压缩吞验证信息**：输出被折成 `[N low-information segments omitted]` / `[full
   output: sqz expand <id>]`。测试计数（`# pass / # fail`）、票面勾选状态、报错
   原文恰是低频词，最容易被折叠。被压掉的内容不下结论：跑 `sqz expand <id>`
   取全文，或把命令重定向到文件再 Read 文件。
2. **`rtk proxy` 破坏 shell 分隔符**：`cat a; echo ===; ls b` 这类命令里裸 `===`
   会被 zsh 当成模式匹配报 `(eval):1: == not found`，整条命令 exit 1、输出丢失。
   分隔符用 `echo '---'`，或干脆拆成两条命令。

出处：2026-10-22 watchtower session transcript d5852c1b L252：`rtk proxy cat … ;
echo ===` 报 `(eval):1: == not found`，整段输出丢失后被迫重跑；同 transcript 多处
`[segments omitted]`。2026-10-22 retro session 亲历：验证用的 grep 输出两次被折成
`sqz expand` 提示，需展开才见原文。
