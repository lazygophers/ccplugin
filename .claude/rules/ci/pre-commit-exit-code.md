# pre-commit 里每条自测必须自己 `|| exit 1`

`scripts/hooks/pre-commit` 按 skill 加段式增长。每段必须写成
`node …/self-test.mjs || exit 1` 这种自带失败传播的形态。出现自测失败但脚本末尾仍 exit 0 时，给该段补 `|| exit 1`。
