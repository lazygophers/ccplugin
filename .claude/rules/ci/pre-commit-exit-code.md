# pre-commit 里每条自测必须自己 `|| exit 1`

`scripts/hooks/pre-commit` 按 skill 加段式增长。每段必须写成
`node …/self-test.mjs || exit 1` 这种自带失败传播的形态：原 ask-ui 段裸跑自测，
失败仍走到脚本末尾 exit 0，检查在但拦不住坏提交，静默空转了整个存在期。

出处：commit 60a8dc38 修的就是这个；hook 目前覆盖 ask-ui 自测与
tracking-progress pytest 两段。
