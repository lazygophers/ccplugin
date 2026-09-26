# headless 验证断言必须查 DOM 状态，不 grep 页面源码

用 headless Chrome `--dump-dom` 验证 JS 渲染结果时，grep 的对象必须是被 JS 写过的
DOM 属性或元素（如 `data-r="..."`），不能 grep 'RENDERED' 这类也出现在脚本原文里的字符串——
脚本文本会原样出现在 dump 里，命中不代表执行成功。

出处：2026-09-26 mermaid 图两轮误判「渲染成功」，实际 jison 解析失败；
改成把结果写 `document.body.setAttribute('data-r', ...)` 后才暴露真状态。
