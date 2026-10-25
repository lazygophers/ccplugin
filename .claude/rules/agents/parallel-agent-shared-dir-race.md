# 并行 agent 不共享可变目录：只读约束或改串行，二选一

派并行 agent 前先列每个 thunk 要写的路径；两个 thunk 写同一目录就不是并行，
要么给验证类一方加只读约束（见 agents/verify-phase-read-only.md），要么按目
录互斥改串行。

2026-10-25 skein dependabot session：两个 Verify agent 并行跑在
plugins/tools/skein/assets/nextjs/（一个 pnpm audit 核对锁文件、一个 pnpm
install + build），锁文件读写互踩——audit 两次读到旧态，等另一方退出后才收
口；一方覆写 pnpm-workspace.yaml 把原有配置冲掉，手工补回。

出处：2026-10-25 skein dependabot 全清 session。
