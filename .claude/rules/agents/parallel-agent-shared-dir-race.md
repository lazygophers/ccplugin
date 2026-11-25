# 并行 agent 不共享可变目录：只读约束或改串行，二选一

派并行 agent 前先列每个 thunk 要写的路径；两个 thunk 写同一目录就不是并行，
要么给验证类一方加只读约束（见 agents/verify-phase-read-only.md），要么按目
录互斥改串行。
