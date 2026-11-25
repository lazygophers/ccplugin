# pre-commit 里每条自测必须自己 `|| exit 1`

`scripts/hooks/pre-commit` 按 skill 加段式增长。每段必须写成
`node …/self-test.mjs || exit 1` 这种自带失败传播的形态。
