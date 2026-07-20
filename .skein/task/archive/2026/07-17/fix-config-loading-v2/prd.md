# 修复设置页加载中 (v2 根因) — PRD

## 目标
config-modal.js 改用 "先 await 再 createApp" 模式, 去掉 mounted 依赖。

## 根因 (v1 init→mounted 未解决的真因)
vendored petite-vue (`vendor/petite-vue.js`) **不支持 mounted 生命周期钩子**。实测 `createApp({mounted(){}}).mount(host)` → mounted 从不调用。其他页 (queue/board/task) 全用 "先 await fetchState() 拿数据, 再 createApp" 模式, 不依赖 mounted。config-modal 是唯一用 mounted 的 — loading 永真。

## 改动
config-modal.js open() 重构:
1. open() 改 async, 先 `const cfg = await _api.getConfig()` 拿数据 (catch → loadErr)
2. createApp 时 loading 初始 = false (或去掉 loading 态), cfg 直接注入已拉到的值
3. 删 mounted() 方法
4. yamlText 初始 = dumpYaml(cfg)
5. 模板 `v-if="loading"` 保留 (用于 loadErr 态显示错误, 但 loading 初始 false)

## 边界
- 范围内: config-modal.js open() + 删 mounted
- 范围外: vendor/petite-vue.js (不动); 其他页; 后端 config 端点 (已 200)
- 约束: 复用 queue.js 同款模式

## 验收
- [ ] 打开设置立即显示 config 值 (不卡加载中)
- [ ] 无 mounted 残留
- [ ] loadErr 时显示错误 (非加载中)
- [ ] ESM 过
- [ ] chrome 实测打开设置页看到值
