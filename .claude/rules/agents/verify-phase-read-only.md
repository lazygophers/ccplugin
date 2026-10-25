# verify 阶段默认只读：发现新问题回报，不擅自动文件

多阶段 workflow 里只有被授权改文件的阶段能动文件；verify agent 的任务是核对
产出后的状态，不是继续修。它看到没修干净的、或自认为「顺手就能修」的，一律
写进回报由主对话拍板——不升级钉版、不加 overrides、不改配置文件。

- verify 派单写明：「verify 只读：除 <要核对的产物/日志> 外不写任何文件；
  发现越界或遗留问题回报，不动手」。授权范围原样抄入，同
  fix-phase-authorization.md 的要求。
- 主对话验收时核对 verify 的实际改动为零文件写入（`git status` / diff 核对）；
  有写入即越权，先回滚再重派。

同类越权第二次（第一次见 fix-phase-authorization.md，只盖了 fix 派单）：用户
原话「警告全部都需要处理」被 verify agent 自行扩大解释成「可以升级 next 钉
版、加 overrides、改 pnpm-workspace.yaml」——结果碰巧被用户追认，但边界窄一
点就是事故。

出处：2026-10-25 skein dependabot 全清 session。
