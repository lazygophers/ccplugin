# /spec 页面重新设计 — PRD

## 目标
skein webapp /spec 页面从「双栏 树+单文件 md」升级到「三栏 树/列表+详情」, 支持 metadata frontmatter 表单独立编辑、编辑器增强、全屏 diff、快捷键、信息密度提升。

## 现状痛点
- 导航: 两层(core/recall)×类目 嵌套树找文件累, 无搜索
- metadata: frontmatter (title/layer/category/keywords/source/authored-by/created) 混入 md 正文渲染, 无法独立编辑
- 编辑: 裸 textarea 无增强 (无行号/tab/快捷键)
- diff: 弹层小, 增删色不够清晰
- 信息密度: 无面包屑/标签/概览, 不知全貌

## 范围
- 范围内: src/pages/spec.js (整页重写), src/input.css (新增 spec 三栏 + metadata 表单 + diff 全屏样式), dist/app.css 重建
- 范围外: 其他 pages/*.js; api 层 (api.specList/specLoad/specSave 不改契约, 复用); router.js 路由; board/themes
- 约束: petite-vue 无构建, 所有 CSS 进 input.css 经 tailwind 编译; spec.js 内运行时 `<style>` 注入的 CSS 不进 dist (已有架构); 保留 diffLines LCS 函数

## 验收
- [ ] 三栏布局: 左导航树 (layer+category 折叠) / 中文件列表 (当前 category 下文件) / 右详情
- [ ] 中栏顶部搜索框 (按 title/keywords 模糊过滤文件)
- [ ] metadata 表单: 详情区顶部独立编辑 title/layer/category/keywords/source/authored-by/created; 保存自动序列化为 frontmatter 合并写回
- [ ] 详情区双模式: md 预览 (可读渲染) ↔ 原始编辑 (textarea); 顶部 toggle 切换
- [ ] 编辑器增强: 等宽字体 + 行号 + tab 缩进 (textarea 层, 不引外部编辑器库)
- [ ] diff 全屏: 保存前 diff 弹层改全屏覆盖, 行级增(绿)/删(红)色清晰
- [ ] 快捷键: Cmd+S 保存 (进 diff), Esc 取消编辑
- [ ] 视觉: 面包屑 (layer/category/file) + 标签 chip (layer/category) + 右栏顶部文件元信息
- [ ] ESM 语法过 (node --input-type=module spec.js)
- [ ] dist/app.css 重建

## 索引
- 设计: design.md
- 任务/子任务: task.json
