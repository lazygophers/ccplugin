---
description: JavaScript Vue 3.5 开发规范：Composition API、Vapor mode、Pinia、Nuxt 4。开发 Vue 应用时必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# JavaScript Vue 3.5 开发规范

## 适用 Agents

| Agent | 说明 |
| ----- | ---- |
| dev   | JavaScript 开发专家 |
| test  | JavaScript 测试专家 |

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 核心规范 | Skills(javascript:core) | ES2024-2025 标准、ESM、工具链 |
| 异步编程 | Skills(javascript:async) | async/await、Promise |
| 安全编码 | Skills(javascript:security) | XSS 防护、Zod 验证 |

## Composition API + `<script setup>`

```vue
<script setup>
import { ref, computed, onMounted, watch } from 'vue';

const users = ref([]);
const loading = ref(true);
const searchQuery = ref('');

const filteredUsers = computed(() =>
  users.value.filter(user =>
    user.name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
);

onMounted(async () => {
  try {
    const response = await fetch('/api/users');
    users.value = await response.json();
  } catch (error) {
    console.error('Failed to fetch users:', error);
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <input v-model="searchQuery" placeholder="Search users..." />
  <div v-if="loading">Loading...</div>
  <UserList v-else :users="filteredUsers" />
</template>
```

## Vue 3.5 新特性

```vue
<script setup>
// defineProps 解构（Vue 3.5）- 保持响应式
const { name, count = 0 } = defineProps({
  name: String,
  count: { type: Number, default: 0 },
});

// useTemplateRef（Vue 3.5）- 类型安全的模板引用
import { useTemplateRef, onMounted } from 'vue';

const inputRef = useTemplateRef('input');

onMounted(() => {
  inputRef.value?.focus();
});
</script>

<template>
  <input ref="input" />
  <p>{{ name }}: {{ count }}</p>
</template>
```

## 组合式函数（Composables）

```javascript
// composables/useUser.js
import { ref, watch } from 'vue';

export function useUser(userId) {
  const user = ref(null);
  const loading = ref(true);
  const error = ref(null);

  watch(userId, async (id) => {
    if (!id) return;
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch(`/api/users/${id}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      user.value = await response.json();
    } catch (e) {
      error.value = e;
    } finally {
      loading.value = false;
    }
  }, { immediate: true });

  return { user, loading, error };
}

// composables/useAbortFetch.js
import { ref, onUnmounted } from 'vue';

export function useAbortFetch() {
  let controller = null;

  async function fetchData(url) {
    controller?.abort();
    controller = new AbortController();

    const response = await fetch(url, { signal: controller.signal });
    return response.json();
  }

  onUnmounted(() => controller?.abort());

  return { fetchData };
}
```

## Pinia 状态管理

```javascript
// stores/user.js
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useUserStore = defineStore('user', () => {
  // State
  const users = ref([]);
  const currentUser = ref(null);

  // Getters
  const activeUsers = computed(() =>
    users.value.filter(u => u.isActive)
  );

  // Actions
  async function fetchUsers() {
    const response = await fetch('/api/users');
    users.value = await response.json();
  }

  async function login(credentials) {
    const response = await fetch('/api/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    currentUser.value = await response.json();
  }

  return { users, currentUser, activeUsers, fetchUsers, login };
});
```

## Nuxt 4 集成

```javascript
// nuxt.config.js
export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  future: { compatibilityVersion: 4 },
  modules: ['@pinia/nuxt'],
});

// pages/users/[id].vue - 自动路由
<script setup>
const route = useRoute();
const { data: user } = await useFetch(`/api/users/${route.params.id}`);
</script>

// server/api/users/[id].get.js - Server API
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id');
  return await db.users.findById(id);
});
```

## Vue Router 4

```javascript
import { createRouter, createWebHistory } from 'vue-router';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: () => import('./pages/Home.vue'), // 懒加载
    },
    {
      path: '/users/:id',
      component: () => import('./pages/UserDetail.vue'),
      props: true, // 路由参数作为 props
    },
  ],
});

// 导航守卫
router.beforeEach((to, from) => {
  const store = useUserStore();
  if (to.meta.requiresAuth && !store.currentUser) {
    return { name: 'login' };
  }
});
```

## Red Flags

| 现象 | 问题 | 严重程度 |
|------|------|---------|
| Options API | 应使用 Composition API + `<script setup>` | 高 |
| Vuex | 应迁移到 Pinia | 中 |
| `this.$refs` | 应使用 `useTemplateRef()`（Vue 3.5）| 中 |
| Mixin | 应使用组合式函数替代 | 高 |
| `v-html` 无清理 | 必须使用 DOMPurify 清理 | 高 |
| 无 AbortController | 应在 onUnmounted 中取消请求 | 中 |
| Vue 2 语法 | 应迁移到 Vue 3.5 | 高 |

## 检查清单

- [ ] 使用 Composition API + `<script setup>`
- [ ] Vue 3.5 `defineProps` 解构保持响应式
- [ ] Vue 3.5 `useTemplateRef()` 替代字符串 ref
- [ ] 提取组合式函数封装复用逻辑
- [ ] Pinia 管理全局状态（Setup Store 风格）
- [ ] 路由组件懒加载（`() => import()`）
- [ ] `onUnmounted` 清理 AbortController 和计时器
- [ ] `v-html` 必须配合 DOMPurify
- [ ] computed 处理派生状态
- [ ] watch 处理副作用
