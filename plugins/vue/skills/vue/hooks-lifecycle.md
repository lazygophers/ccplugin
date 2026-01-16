# 生命周期 Hooks 与高级响应式

## 生命周期 Hooks

### 生命周期执行顺序

```typescript
import {
  onBeforeMount,
  onMounted,
  onBeforeUpdate,
  onUpdated,
  onBeforeUnmount,
  onUnmounted
} from 'vue'

export default {
  setup() {
    // 1. setup() - 最先执行，用于初始化
    
    onBeforeMount(() => {
      // 2. 组件挂载到 DOM 之前（SSR 不调用）
      console.log('即将挂载')
    })

    onMounted(() => {
      // 3. 组件挂载到 DOM 完成
      console.log('已挂载')
      // ✅ 可以访问 DOM 元素、初始化第三方库
    })

    onBeforeUpdate(() => {
      // 4. 响应式数据变化导致更新前
      console.log('即将更新')
    })

    onUpdated(() => {
      // 5. 更新完成后
      console.log('已更新')
      // ⚠️ 避免在此修改数据，可能导致无限循环
    })

    onBeforeUnmount(() => {
      // 6. 组件卸载前
      console.log('即将卸载')
      // ✅ 清理资源、移除事件监听
    })

    onUnmounted(() => {
      // 7. 组件已卸载
      console.log('已卸载')
    })
  }
}
```

## onMounted 常见用途

### 初始化 DOM 引用

```typescript
import { ref, onMounted } from 'vue'

const inputRef = ref<HTMLInputElement | null>(null)

onMounted(() => {
  // ✅ 可以安全访问 DOM 元素
  inputRef.value?.focus()
})
```

### 初始化第三方库

```typescript
import { onMounted, onUnmounted } from 'vue'
import Chart from 'chart.js'

let chartInstance: Chart | null = null

onMounted(() => {
  const ctx = document.getElementById('myChart') as HTMLCanvasElement
  chartInstance = new Chart(ctx, { /* 配置 */ })
})

onUnmounted(() => {
  // ✅ 清理资源
  chartInstance?.destroy()
})
```

### 获取数据（旧方式）

```typescript
// ❌ 旧 Options API 方式
export default {
  data() { return { user: null } },
  mounted() {
    fetch('/api/user').then(r => r.json()).then(u => this.user = u)
  }
}

// ✅ 新 Composition API 方式
import { ref, onMounted } from 'vue'

const user = ref(null)

onMounted(async () => {
  const response = await fetch('/api/user')
  user.value = await response.json()
})

// ✅ 更好的方式：使用 Composable
function useUser(id: number) {
  const user = ref(null)
  
  onMounted(async () => {
    const response = await fetch(`/api/user/${id}`)
    user.value = await response.json()
  })
  
  return { user }
}
```

## onUnmounted 清理资源

### 移除事件监听

```typescript
import { onMounted, onUnmounted } from 'vue'

onMounted(() => {
  const handleResize = () => { /* 处理 */ }
  
  window.addEventListener('resize', handleResize)
  
  onUnmounted(() => {
    // ✅ 清理事件监听
    window.removeEventListener('resize', handleResize)
  })
})
```

### 清理定时器

```typescript
import { onMounted, onUnmounted, ref } from 'vue'

const count = ref(0)

onMounted(() => {
  const timer = setInterval(() => {
    count.value++
  }, 1000)
  
  onUnmounted(() => {
    // ✅ 清理定时器防止内存泄漏
    clearInterval(timer)
  })
})
```

### 取消 API 请求

```typescript
import { onMounted, onUnmounted } from 'vue'

onMounted(() => {
  const controller = new AbortController()
  
  fetch('/api/data', { signal: controller.signal })
    .then(r => r.json())
    .then(data => { /* 处理 */ })
  
  onUnmounted(() => {
    // ✅ 取消进行中的请求
    controller.abort()
  })
})
```

## 高级响应式模式

### Computed vs Watch

| 特性 | computed | watch |
|------|----------|-------|
| 用途 | 派生状态 | 副作用 |
| 缓存 | ✅ 自动缓存 | ❌ 无缓存 |
| 同步 | ✅ 同步执行 | ⚠️ 异步可能 |
| 依赖 | 自动追踪 | 手动指定 |
| 返回值 | ✅ 有返回值 | ❌ 无返回值 |

### 使用 watch 处理复杂副作用

```typescript
import { watch, ref } from 'vue'

const userId = ref(1)
const user = ref(null)
const posts = ref([])

// ✅ 单个源监听
watch(userId, async (newId, oldId) => {
  console.log(`用户从 ${oldId} 变为 ${newId}`)
  const response = await fetch(`/api/users/${newId}`)
  user.value = await response.json()
}, { immediate: true }) // immediate: true 在组件挂载时立即执行

// ✅ 多个源监听
watch([userId, user], ([newId, newUser], [oldId, oldUser]) => {
  console.log('userId 或 user 变化了')
})

// ✅ 监听对象的特定属性
watch(
  () => user.value?.name,
  (newName) => {
    console.log(`用户名变为: ${newName}`)
  }
)
```

### 条件监听

```typescript
// ✅ 有条件地启动/停止监听
const userId = ref(1)
const isWatching = ref(true)

const stopWatching = watch(userId, fetchUser, {
  // 条件函数：返回 true 才执行 callback
  // Vitest 6.0+ 特性
})
```

## 处理异步操作

### 正确处理异步状态

```typescript
import { ref, onMounted } from 'vue'

const user = ref(null)
const loading = ref(false)
const error = ref<Error | null>(null)

onMounted(async () => {
  try {
    loading.value = true
    error.value = null
    
    const response = await fetch('/api/user')
    if (!response.ok) throw new Error('Failed to fetch')
    
    user.value = await response.json()
  } catch (e) {
    error.value = e instanceof Error ? e : new Error('Unknown error')
  } finally {
    loading.value = false
  }
})
```

### 竞态条件处理

```typescript
import { ref, watch } from 'vue'

const searchQuery = ref('')
const results = ref([])

watch(searchQuery, async (query) => {
  if (!query) {
    results.value = []
    return
  }
  
  // ✅ 记录请求 ID 避免竞态条件
  const requestId = Math.random()
  let isLatest = true
  
  const response = await fetch(`/api/search?q=${query}`)
  const data = await response.json()
  
  if (isLatest) {
    results.value = data
  }
  
  return () => { isLatest = false }
})
```

## 防止内存泄漏

### 常见泄漏源

```typescript
// ❌ 泄漏 1: 未清理的定时器
onMounted(() => {
  setInterval(() => { /* ... */ }, 1000) // 无限运行
})

// ❌ 泄漏 2: 未移除的事件监听
onMounted(() => {
  window.addEventListener('scroll', handler)
  // 未在 onUnmounted 移除
})

// ❌ 泄漏 3: 未取消的 Promise
onMounted(() => {
  fetch('/api/data').then(r => r.json())
  // 组件卸载时请求还在处理
})

// ✅ 正确的清理
onMounted(() => {
  const timer = setInterval(() => { /* ... */ }, 1000)
  const handleScroll = () => { /* ... */ }
  const controller = new AbortController()
  
  window.addEventListener('scroll', handleScroll)
  fetch('/api/data', { signal: controller.signal })
  
  onUnmounted(() => {
    clearInterval(timer)
    window.removeEventListener('scroll', handleScroll)
    controller.abort()
  })
})
```

## 完整示例：用户数据管理

```typescript
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

function useUserData(userId: number) {
  const user = ref(null)
  const loading = ref(false)
  const error = ref<Error | null>(null)
  const lastUpdated = ref<Date | null>(null)
  
  // 计算派生数据
  const isStale = computed(() => {
    if (!lastUpdated.value) return true
    const diff = Date.now() - lastUpdated.value.getTime()
    return diff > 5 * 60 * 1000 // 5分钟过期
  })
  
  // 获取用户数据
  const fetchUser = async (id: number) => {
    try {
      loading.value = true
      error.value = null
      
      const response = await fetch(`/api/users/${id}`)
      if (!response.ok) throw new Error('Failed to fetch')
      
      user.value = await response.json()
      lastUpdated.value = new Date()
    } catch (e) {
      error.value = e instanceof Error ? e : new Error('Unknown error')
    } finally {
      loading.value = false
    }
  }
  
  // userId 变化时重新获取
  watch(userId, fetchUser, { immediate: true })
  
  // 定期刷新数据
  onMounted(() => {
    const timer = setInterval(() => {
      if (isStale.value) {
        fetchUser(userId.value)
      }
    }, 60000) // 每分钟检查一次
    
    onUnmounted(() => clearInterval(timer))
  })
  
  return {
    user,
    loading,
    error,
    isStale,
    refetch: () => fetchUser(userId.value)
  }
}
```
