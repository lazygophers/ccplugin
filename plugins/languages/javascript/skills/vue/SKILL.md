---
name: vue
description: JavaScript Vue 开发规范：Vue 3、Composition API、响应式。开发 Vue 应用时必须加载。
---

# JavaScript Vue 开发规范

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 核心规范 | Skills(core) | ES2024-2025 标准、强制约定 |
| 异步编程 | Skills(async) | async/await、Promise |

## Composition API

```vue
<script setup>
import { ref, computed, onMounted } from 'vue';

const users = ref([]);
const loading = ref(true);
const searchQuery = ref('');

const filteredUsers = computed(() => {
  return users.value.filter(user =>
    user.name.includes(searchQuery.value)
  );
});

onMounted(async () => {
  try {
    users.value = await fetchUsers();
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <input v-model="searchQuery" placeholder="Search..." />
  <UserList :users="filteredUsers" :loading="loading" />
</template>
```

## 组合式函数

```javascript
export function useUser(userId) {
  const user = ref(null);
  const loading = ref(true);
  const error = ref(null);

  watch(userId, async (id) => {
    loading.value = true;
    try {
      user.value = await fetchUser(id);
    } catch (e) {
      error.value = e;
    } finally {
      loading.value = false;
    }
  }, { immediate: true });

  return { user, loading, error };
}
```

## 检查清单

- [ ] 使用 Composition API
- [ ] 使用 <script setup>
- [ ] 提取组合式函数
- [ ] 使用 computed 和 watch
