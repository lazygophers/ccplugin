---
name: javascript-vue
description: |
  Vue 3.5+ 开发规范 (2026)：Composition API + `<script setup>`, Vapor Mode 高性能编译,
  defineProps 解构 + reactive props, useTemplateRef, Pinia 2 setup-store 状态,
  Nuxt 4 全栈, Vue Router 4 懒加载, VueUse 12 工具库, Volar 类型推断。
  Use when building Vue components, SFCs, composables, stores, or Nuxt pages.
  Triggers: "Vue 组件", "Composition API", "Pinia", "Nuxt", "script setup",
  "reactive", "ref", "computed", "SFC", "v-model".
context: fork
model: sonnet
---

# Vue 3.5+ 开发规范 (2026)

## 配套

- `Skills(javascript:core)` — ESM/Vite/Biome
- `Skills(javascript:async)` — AbortController + onUnmounted
- `Skills(javascript:security)` — v-html + DOMPurify

## SFC + `<script setup>` (默认)

```vue
<script setup>
import { ref, computed, onMounted, useTemplateRef } from 'vue';

const users = ref([]);
const query = ref('');
const loading = ref(true);

const filtered = computed(() =>
  users.value.filter(u => u.name.includes(query.value))
);

const inputRef = useTemplateRef('input');

onMounted(async () => {
  try {
    const r = await fetch('/api/users');
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    users.value = await r.json();
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
    inputRef.value?.focus();
  }
});
</script>

<template>
  <input ref="input" v-model="query" />
  <p v-if="loading">Loading…</p>
  <UserList v-else :users="filtered" />
</template>
```

## Vue 3.5+ 关键特性

```vue
<script setup>
// defineProps 解构 — 解构后仍响应式 (3.5+)
const { name, count = 0 } = defineProps({
  name: String,
  count: { type: Number, default: 0 },
});

// useTemplateRef — 类型安全的 ref (3.5+, 代替字符串 `$refs`)
const list = useTemplateRef('list');

// defineModel — 双向绑定 (3.4+)
const value = defineModel({ type: String, required: true });

// onWatcherCleanup (3.5+) — 替代 watch 内的 onCleanup 参数
import { watch, onWatcherCleanup } from 'vue';
watch(id, async (newId) => {
  const ctrl = new AbortController();
  onWatcherCleanup(() => ctrl.abort());
  const r = await fetch(`/api/u/${newId}`, { signal: ctrl.signal });
});
</script>
```

## Vapor Mode (高性能编译, 3.5+ 实验)

无虚拟 DOM、直接生成命令式代码，性能近似 Solid。适合性能敏感页面或微前端组件。

```js
// vite.config.js
import vue from '@vitejs/plugin-vue';
export default {
  plugins: [vue({ features: { vaporMode: true } })],
};
```

```vue
<script setup vapor>
// 该 SFC 编译为 Vapor 模式
</script>
```

## Composables (复用逻辑)

```js
// composables/useFetch.js
import { ref, watchEffect, onScopeDispose } from 'vue';

export function useFetch(url) {
  const data = ref(null), error = ref(null), loading = ref(true);
  let ctrl;
  watchEffect(async () => {
    ctrl?.abort();
    ctrl = new AbortController();
    loading.value = true;
    try {
      const r = await fetch(typeof url === 'function' ? url() : url, { signal: ctrl.signal });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      data.value = await r.json();
    } catch (e) {
      if (e.name !== 'AbortError') error.value = e;
    } finally {
      loading.value = false;
    }
  });
  onScopeDispose(() => ctrl?.abort());
  return { data, error, loading };
}
```

## Pinia 2 (Setup Store 风格)

```js
// stores/user.js
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useUserStore = defineStore('user', () => {
  const current = ref(null);
  const list = ref([]);
  const isLoggedIn = computed(() => !!current.value);

  async function login(creds) {
    const r = await fetch('/api/login', { method: 'POST', body: JSON.stringify(creds) });
    current.value = await r.json();
  }
  function logout() { current.value = null; }

  return { current, list, isLoggedIn, login, logout };
});
```

## Nuxt 4

```js
// nuxt.config.ts
export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  future: { compatibilityVersion: 4 },
  modules: ['@pinia/nuxt', '@vueuse/nuxt'],
  experimental: { typedPages: true },
});
```

```vue
<!-- pages/users/[id].vue -->
<script setup>
const route = useRoute();
const { data: user, error } = await useFetch(`/api/users/${route.params.id}`);
</script>
```

```js
// server/api/users/[id].get.ts — Nitro server route
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id');
  return await db.users.findById(id);
});
```

## Vue Router 4

```js
import { createRouter, createWebHistory } from 'vue-router';
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: () => import('./pages/Home.vue') },
    { path: '/u/:id', component: () => import('./pages/User.vue'), props: true },
  ],
});
router.beforeEach((to) => {
  const store = useUserStore();
  if (to.meta.requiresAuth && !store.isLoggedIn) return { name: 'login' };
});
```

## Red Flags

| 现象 | 应改 | 严重 |
|------|------|------|
| Options API 新代码 | Composition API + `<script setup>` | 高 |
| Vuex | Pinia 2 setup store | 中 |
| 字符串 `ref="..."` + `$refs` | `useTemplateRef` | 中 |
| Mixin | composable | 高 |
| `v-html` 无清理 | DOMPurify | 高 |
| watch 内未清理副作用 | `onWatcherCleanup` | 中 |
| 路由组件不 lazy | `() => import(...)` | 中 |
| Vue 2 语法 (Vue.extend 等) | Vue 3.5 | 高 |

## 检查清单

- [ ] `<script setup>` + Composition API
- [ ] `defineProps` 解构 (响应式)
- [ ] `useTemplateRef` 而非字符串 ref
- [ ] 复用逻辑提 composable
- [ ] Pinia setup store + computed getter
- [ ] 路由懒加载
- [ ] `onUnmounted` / `onScopeDispose` 清理 AbortController / interval
- [ ] `v-html` 经 DOMPurify
- [ ] Volar / vue-tsc 类型检查通过

## 参考

- Vue 3.5: <https://vuejs.org/guide/>
- Pinia: <https://pinia.vuejs.org>
- Nuxt 4: <https://nuxt.com>
- VueUse: <https://vueuse.org>
