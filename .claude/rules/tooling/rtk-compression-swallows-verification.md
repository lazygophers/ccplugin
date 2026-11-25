# RTK 压缩输出吞验证信息：被压掉的不算结论；rtk proxy 下别用 `echo ===`

RTK hook 自动把命令包进 `rtk` 代理并压缩输出。两点：

1. **压缩吞验证信息**：输出被折成 `[N low-information segments omitted]` / `[full
   output: sqz expand <id>]`。测试计数（`# pass / # fail`）、票面勾选状态、报错
   原文恰是低频词，最容易被折叠。被压掉的内容不下结论：跑 `sqz expand <id>`
   取全文，或把命令重定向到 `/tmp` 下的文件再 Read（放 `/tmp`，别写进仓库目录
   制造脏文件）。
2. **`rtk proxy` 破坏 shell 分隔符**：`cat a; echo ===; ls b` 这类命令里裸 `===`
   会被 zsh 当成模式匹配报 `(eval):1: == not found`，整条命令 exit 1、输出丢失。
   分隔符用 `echo '---'`，或干脆拆成两条命令。
