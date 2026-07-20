# 修复设置页一直加载中 — PRD

## 目标
config-modal.js `init()` → `mounted()`。petite-vue 生命周期用 mounted, 无 init。init 永不调用 → loading 永真 → 加载中卡死。

## 根因
config-modal.js L124 `async init()` — petite-vue createApp 不调 init, 只调 mounted。queue.js L146 正确用 mounted。

## 改动
plugins/tools/skein/assets/webapp/src/lib/config-modal.js: `async init()` → `async mounted()`

## 验收
- [ ] 打开设置不再卡加载中
- [ ] config 值正确显示
- [ ] ESM 过
