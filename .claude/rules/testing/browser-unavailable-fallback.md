# 浏览器验证不可用：node --check + 结构配平 + 用户肉眼，不下载 chromium

用户环境可能主动停掉 chromium 下载（2026-10-23 session 两次停掉）。design_lint /
headless Chrome 截图链路因此跑不了时：不重试下载、不绕路硬装。降级验证链：

1. **页内 JS 语法**：把生成产物里每个 `<script>` 块抽成临时 .js，逐个
   `node --check`；
2. **结构配平**：对生成的 HTML 数起止标签配对（`<script` vs `</script>` 等出现
   次数相等），证明没截断、没嵌坏；
3. **视觉与交互**：明说「渲染未经验证」，交给用户肉眼验收；不把 1+2 说成
   「已验证渲染」。

出处：2026-10-23 tracking-progress 重设计 session（commits 2932d20、1ff1dfa3、
08fc85ff），node --check 全过 + 结构配平 + 用户验收通过。
