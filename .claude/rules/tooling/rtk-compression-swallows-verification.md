# RTK 压缩输出吞验证信息：被压掉的不算结论；rtk proxy 下别用 `echo ===`

RTK hook 自动把命令包进 `rtk` 代理并压缩输出。两点：

1. **压缩吞验证信息**：输出被折成 `[N low-information segments omitted]` / `[full
   output: sqz expand <id>]`。被压掉的内容（测试计数、票面勾选状态、报错原文）
   不下结论：跑 `sqz expand <id>`
   取全文，或把命令重定向到 `/tmp` 下的文件再 Read（放 `/tmp`，不写进仓库目录）。
2. **`rtk proxy` 破坏 shell 分隔符**：命令里不用裸 `===` 分隔符，用 `echo '---'`，或干脆拆成两条命令。
