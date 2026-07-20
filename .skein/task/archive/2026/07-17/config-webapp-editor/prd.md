# 设置可视化编辑器 — PRD

## 目标
webapp 顶栏右上角加齿轮设置按钮, 点开模态可视化读写 .skein/config.yaml。表单+YAML 双 Tab, 双向同步, 实时保存 (改值即写盘, 无保存按钮)。

## 范围
- 后端: skein.py 加 web route GET /__skein__/config (读) + POST /__skein__/config (写); 复用 config() 读 + _yaml_dump 写
- 前端:
  - index.html: 顶栏 theme-toggle 旁加齿轮按钮
  - app.js: 模态渲染 + Tab 切换 + 实时保存 (input/change 事件 debounce 写盘)
  - src/pages/config.js: 新页面模块 (或 inline 到 app.js 模态)
  - input.css: 模态 + 表单 + 开关样式
  - dist/app.css: 重建

## config 10 键 (扁平标量)
| 键 | 类型 | 控件 |
|---|---|---|
| max_active | int | number |
| max_parallel | int | number |
| auto_commit | bool | switch |
| use_worktree | bool | switch |
| worktree_root | str | text |
| retain_days | int | number |
| board_theme | str | select (skein) |
| web_serve | bool | switch |
| board_open | bool | switch |

## 交互
- 表单 Tab: 每键一个控件 + 标签 + 说明 (title 属性或小字)
- YAML Tab: textarea, 编辑即 parse→写盘 (双向: 表单改→同步 YAML 文本; YAML 改→parse→同步表单)
- 实时保存: debounce 400ms 写盘, 成功 toast「已保存」, 失败 toast 错误
- ESC 或点遮罩关模态

## 约束
- _yaml_dump/_yaml_load 已有, 不引 PyYAML
- 后端 config() 有 ENV override (CLAUDE_PLUGIN_OPTION_*), 写盘值可能与读回值不同 — 写盘写纯用户值, 读时 config() 再叠 ENV, UI 显示 config() 返回值 (含 override)
- petite-vue 无构建, IIFE
- board_theme/worktree_root 改了需重启 serve 才生效 — UI 加提示

## 验收
- [ ] 齿轮按钮在顶栏右上角
- [ ] 模态 2 Tab (表单/YAML) 双向同步
- [ ] 改值实时写盘 (debounce)
- [ ] GET/POST config route 工作
- [ ] dist/app.css 重建
- [ ] ESM 无破坏
