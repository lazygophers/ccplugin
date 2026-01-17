# Vue 3 插件

专业的 Vue 3 开发插件，提供 Composition API、Pinia 状态管理、Vite 构建和完整的开发工具链支持。

## 功能特性

### 专业开发代理

- **dev** - Vue 3 开发专家，专注于 Composition API、响应式系统和现代 Vue 3 开发
- **test** - Vue 测试专家，专注于 Vue Test Utils、Vitest 和组件测试
- **debug** - Vue 调试专家，专注于响应式问题诊断和性能瓶颈定位
- **perf** - Vue 性能优化专家，专注于编译优化、运行时性能和 Core Web Vitals

### 完整的开发规范

包含 Vue 3.5+ 开发标准、最佳实践和工具链配置：
- Composition API 最佳实践
- 项目结构和命名规范
- Pinia 状态管理设计
- Vite 构建优化
- TypeScript 集成
- 测试策略（Vitest + Vue Test Utils）
- 性能优化指南

### 集成开发环境支持

- Vue Language Server (Volar) 配置
- 代码补全、类型推断
- 格式化和 Linting 支持
- 调试工具集成

## 安装

```bash
/plugin install vue
```

## 快速开始

### 创建 Vue 项目

```bash
# 使用推荐的构建工具
npm create vite@latest my-app -- --template vue-ts

# 安装依赖（使用 yarn，优先级：yarn > pnpm > npm）
cd my-app
yarn install
```

### 项目结构

```
src/
├── components/         # 可复用组件
├── pages/             # 页面组件
├── stores/            # Pinia 状态管理
├── composables/       # 可复用逻辑
├── utils/             # 工具函数
├── types/             # TypeScript 类型
├── router/            # 路由配置
├── App.vue            # 根组件
└── main.ts            # 应用入口
```

### 基础组件示例

```vue
<template>
  <div>
    <h1>{{ title }}</h1>
    <button @click="increment">点击次数: {{ count }}</button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const count = ref(0)
const title = computed(() => `计数: ${count.value}`)

const increment = () => {
  count.value++
}
</script>

<style scoped>
div {
  padding: 2rem;
}

button {
  padding: 0.5rem 1rem;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
</style>
```

## 代理使用指南

### dev - 开发专家

使用场景：
- 设计 Composition API 架构
- 解决响应式系统问题
- 项目结构规划
- TypeScript 类型系统设计
- Pinia 状态管理设计

```
/agent dev
```

### test - 测试专家

使用场景：
- 编写单元测试
- 设计测试策略
- 提高测试覆盖率
- Vue Test Utils 使用
- Mock 和 Stub 设置

```
/agent test
```

### debug - 调试专家

使用场景：
- 诊断响应式问题
- 定位性能瓶颈
- 调试组件行为
- 分析内存泄漏
- 使用 Vue DevTools

```
/agent debug
```

### perf - 性能优化专家

使用场景：
- 优化编译性能
- 减小 Bundle 大小
- 改进运行时性能
- 优化 Core Web Vitals
- 代码分割策略

```
/agent perf
```

## 核心规范

### Composition API 标准

```typescript
import { ref, computed, watch } from 'vue'

// 状态管理
const count = ref(0)
const name = ref('Vue')

// 计算属性（自动缓存）
const doubled = computed(() => count.value * 2)

// 监听器
watch(count, (newVal) => {
  console.log(`count 变化: ${newVal}`)
})
```

### 组件通信

```typescript
// Props 定义
interface Props {
  modelValue: string
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false
})

// Emits 定义
const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'submit'): void
}>()

// v-model 双向绑定
const localValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})
```

### Pinia 状态管理

```typescript
// stores/counter.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useCounterStore = defineStore('counter', () => {
  const count = ref(0)
  const doubled = computed(() => count.value * 2)

  const increment = () => count.value++
  const decrement = () => count.value--

  return { count, doubled, increment, decrement }
})

// 在组件中使用
const store = useCounterStore()
store.increment()
```

### 工具链配置

```bash
# Vite 配置
yarn add -D vite @vitejs/plugin-vue

# TypeScript 支持
yarn add -D typescript @vue/tsconfig

# 测试框架
yarn add -D vitest @vue/test-utils happy-dom

# 状态管理
yarn add pinia

# 路由
yarn add vue-router

# 依赖更新
yarn upgrade
```

### 测试示例

```typescript
// src/components/__tests__/Counter.test.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Counter from '@/components/Counter.vue'

describe('Counter.vue', () => {
  it('初始计数为 0', () => {
    const wrapper = mount(Counter)
    expect(wrapper.text()).toContain('0')
  })

  it('点击按钮增加计数', async () => {
    const wrapper = mount(Counter)
    await wrapper.find('button').trigger('click')
    expect(wrapper.find('button').text()).toContain('1')
  })
})
```

### 性能优化

```typescript
// 代码分割
const routes = [
  {
    path: '/',
    component: () => import('@/pages/Home.vue')
  },
  {
    path: '/about',
    component: () => import('@/pages/About.vue')
  }
]

// 异步组件加载
const HeavyComponent = defineAsyncComponent(() =>
  import('@/components/HeavyComponent.vue')
)

// 响应式性能优化
const largeData = shallowRef({ /* 大数据 */ })
```

## 最佳实践

### ✅ 推荐

- 使用 \<script setup\> 语法
- ref 优先于 reactive
- 明确定义 Props 和 Emits 类型
- 使用 computed 处理派生状态
- 使用 Pinia 进行全局状态管理
- 组件测试覆盖率 ≥ 80%
- 使用 yarn 管理依赖
- 启用 TypeScript strict 模式

### ❌ 避免

- 过度使用 watch
- 混合使用 ref 和 reactive
- Props 嵌套过深
- 在计算属性中执行副作用
- 直接修改 Props
- 忽视类型检查
- 使用全局变量进行状态管理
- 未测试的关键业务逻辑

## Core Web Vitals 指标

性能优化目标：
- **LCP** (Largest Contentful Paint): < 2.5s
- **INP** (Interaction to Next Paint): < 200ms
- **CLS** (Cumulative Layout Shift): < 0.1

## 常用命令

```bash
# 开发服务器
yarn dev

# 生产构建
yarn build

# 类型检查
yarn type-check

# 运行测试
yarn test

# 测试覆盖率
yarn test:coverage

# 代码格式化
yarn format

# Linting
yarn lint
```

## 框架集成

### 与 Nuxt 3 集成

Vue 3 插件完全兼容 Nuxt 3 框架，提供以下特性：
- 自动文件路由
- 自动导入组件
- SSR 支持
- 集成式 API 路由

### 与 Next.js 互操作

在 Next.js 项目中集成 Vue 3（通过 `next-vue`）：
```typescript
// 混合框架开发时参考 Vue 3 最佳实践
```

## 常见问题

**Q: 应该使用 ref 还是 reactive？**

A: 推荐使用 ref，除非处理复杂嵌套对象需要深层追踪的特定场景。

**Q: Props 应该如何处理？**

A: 总是使用 TypeScript 定义 Props 接口，配合 `withDefaults` 设置默认值。

**Q: 如何组织大型项目？**

A: 按功能模块划分目录，使用 Pinia 进行状态管理，使用 Composables 复用逻辑。

**Q: 性能优化的优先级？**

A: 1) 代码分割 2) 懒加载 3) 图片优化 4) 缓存策略 5) 监测和分析

## 学习资源

- [Vue 3 官方文档](https://vuejs.org/)
- [Pinia 文档](https://pinia.vuejs.org/)
- [Vue Router 文档](https://router.vuejs.org/)
- [Vite 文档](https://vitejs.dev/)
- [Nuxt 3 文档](https://nuxt.com/)

## 支持

如有问题或建议，请提交 Issue 或 PR 到项目仓库。

## 许可证

MIT License
