# Vue 开发规范

## 核心原则

### 必须遵守

1. **Composition API 优先** - Vue 3 优先使用 Composition API
2. **响应式原则** - 遵循 Vue 响应式系统规则
3. **Props 类型** - 使用 props 定义验证类型
4. **生命周期** - 正确使用生命周期钩子
5. **组件通信** - 遵循单向数据流原则

### 禁止行为

- 直接修改 props
- 在模板中使用复杂表达式
- 在 setup 中滥用 this
- 忽略响应式限制
- 混用 Options API 和 Composition API

## Composition API

### script setup

```vue
<!-- ✅ 正确 - 使用 script setup -->
<script setup>
import { ref, computed, onMounted } from 'vue';

/**
 * UserCard 组件
 * @props {Object} user - 用户数据
 * @props {Boolean} [showEmail=true] - 是否显示邮箱
 */
const props = defineProps({
  user: {
    type: Object,
    required: true,
  },
  showEmail: {
    type: Boolean,
    default: true,
  },
});

const emit = defineEmits(['edit', 'delete']);

const loading = ref(false);
const error = ref(null);

const fullName = computed(() => {
  return `${props.user.firstName} ${props.user.lastName}`;
});

const handleEdit = () => {
  emit('edit', props.user.id);
};

const handleDelete = async () => {
  loading.value = true;
  try {
    await deleteUser(props.user.id);
    emit('delete', props.user.id);
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  console.log('UserCard mounted');
});
</script>

<template>
  <div class="user-card">
    <h3>{{ fullName }}</h3>
    <p v-if="showEmail">{{ user.email }}</p>
    <button @click="handleEdit" :disabled="loading">
      Edit
    </button>
    <button @click="handleDelete" :disabled="loading">
      Delete
    </button>
    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<!-- ❌ 错误 - 混用 Options API -->
<script>
export default {
  props: ['user'],
  setup(props) {
    const loading = ref(false);
    // 不应该混用 this
    this.someMethod(); // 错误！
    return { loading };
  },
  methods: {
    // 不应该混用
  }
};
</script>
```

### 响应式数据

```javascript
// ✅ 正确 - ref 和 reactive 使用
import { ref, reactive, toRefs } from 'vue';

// ref 用于基本类型和需要重新赋值的对象
const count = ref(0);
const user = ref({ name: 'Alice', age: 25 });

// 修改值
count.value++;
user.value.name = 'Bob';

// reactive 用于对象，不需要 .value
const state = reactive({
  count: 0,
  user: { name: 'Alice' },
  loading: false,
});

// 修改值
state.count++;
state.user.name = 'Bob';

// 从 reactive 对象解构时使用 toRefs
const { count, user, loading } = toRefs(state);
count.value++;
user.value.name = 'Bob';

// ❌ 错误 - 解构 reactive 失去响应性
const { count, user } = state;  // 失去响应性！
count++;  // 不会触发更新
```

### computed

```javascript
// ✅ 正确 - 计算属性
import { ref, computed } from 'vue';

const firstName = ref('Alice');
const lastName = ref('Smith');

const fullName = computed(() => {
  return `${firstName.value} ${lastName.value}`;
});

// 可写计算属性
const fullNameWritable = computed({
  get() {
    return `${firstName.value} ${lastName.value}`;
  },
  set(value) {
    [firstName.value, lastName.value] = value.split(' ');
  }
});

// ❌ 错误 - 在计算属性中产生副作用
const badComputed = computed(() => {
  console.log('This is a side effect!');  // 不要这样做
  return firstName.value + ' ' + lastName.value;
});
```

## 组件通信

### Props 和 Emits

```vue
<script setup>
// ✅ 正确 - 定义 props
const props = defineProps({
  userId: {
    type: Number,
    required: true,
  },
  userName: {
    type: String,
    default: 'Anonymous',
  },
  userSettings: {
    type: Object,
    // 对象/数组的默认值必须使用函数
    default: () => ({
      theme: 'light',
      notifications: true,
    }),
  },
});

// ✅ 正确 - 定义 emits
const emit = defineEmits({
  // 无验证
  update: null,

  // 带验证
  delete: (userId) => {
    if (userId && typeof userId === 'number') {
      return true;
    }
    console.warn('Invalid userId for delete event');
    return false;
  },
});

// 使用
const handleUpdate = () => {
  emit('update', props.userId);
};

const handleDelete = () => {
  emit('delete', props.userId);
};
</script>
```

### Provide/Inject

```javascript
// 父组件
import { provide, ref, readonly } from 'vue';

const theme = ref('light');

// 提供只读的响应式数据
provide('theme', readonly(theme));

// 提供方法
provide('setTheme', (newTheme) => {
  theme.value = newTheme;
});

// 子组件
import { inject } from 'vue';

const theme = inject('theme');
const setTheme = inject('setTheme');

// 使用默认值
const config = inject('config', {
  apiUrl: '/api',
  timeout: 5000,
});
```

## 生命周期

### onMounted 和 onUnmounted

```javascript
import { onMounted, onUnmounted, ref } from 'vue';

const data = ref(null);
let intervalId = null;

onMounted(async () => {
  // 组件挂载后执行
  await fetchData();

  // 设置定时器
  intervalId = setInterval(() => {
    console.log('Tick');
  }, 1000);
});

onUnmounted(() => {
  // 清理定时器
  if (intervalId) {
    clearInterval(intervalId);
  }
});

// ✅ 正确 - watchEffect 自动清理
import { watchEffect } from 'vue';

watchEffect((onCleanup) => {
  const interval = setInterval(() => {
    console.log('Tick');
  }, 1000);

  // 清理函数
  onCleanup(() => {
    clearInterval(interval);
  });
});
```

### watch 和 watchEffect

```javascript
import { ref, watch, watchEffect } from 'vue';

const count = ref(0);
const user = ref({ name: 'Alice' });

// ✅ watch - 监听单个源
watch(count, (newValue, oldValue) => {
  console.log(`Count changed from ${oldValue} to ${newValue}`);
});

// ✅ watch - 监听多个源
watch([count, user], ([newCount, newUser], [oldCount, oldUser]) => {
  console.log('Values changed');
});

// ✅ watch - 监听对象属性
watch(
  () => user.value.name,
  (newName, oldName) => {
    console.log(`Name changed from ${oldName} to ${newName}`);
  }
);

// ✅ watch - 带选项
watch(count, (value) => {
  console.log('Count changed:', value);
}, {
  immediate: true,  // 立即执行
  deep: true,       // 深度监听
});

// ✅ watchEffect - 自动追踪依赖
watchEffect(() => {
  console.log(`Count is ${count.value}`);
  console.log(`User is ${user.value.name}`);
});

// ❌ 错误 - watch 丢失响应性
watch(user.value.name, (newName) => {
  console.log(newName);  // 不会工作！
});
```

## 模板语法

### 指令

```vue
<template>
  <!-- ✅ v-if 条件渲染 -->
  <div v-if="loading">Loading...</div>
  <div v-else-if="error">{{ error }}</div>
  <div v-else>{{ data }}</div>

  <!-- ✅ v-for 列表渲染 -->
  <ul>
    <li
      v-for="item in items"
      :key="item.id"
    >
      {{ item.name }}
    </li>
  </ul>

  <!-- ✅ v-model 表单绑定 -->
  <input v-model="name" />
  <input v-model.trim="name" />
  <textarea v-model="message" />
  <input type="checkbox" v-model="checked" />
  <input type="radio" v-model="picked" value="Option1" />
  <select v-model="selected">
    <option value="">Please select</option>
    <option v-for="option in options" :key="option.value" :value="option.value">
      {{ option.text }}
    </option>
  </select>

  <!-- ✅ 事件修饰符 -->
  <button @click.stop="handleClick">Stop Propagation</button>
  <form @submit.prevent="handleSubmit">Prevent Default</form>
  <input @keyup.enter="handleEnter" />

  <!-- ❌ 错误 - v-if 和 v-for 同时使用 -->
  <li v-for="item in items" v-if="item.active" :key="item.id">
    <!-- 应该使用计算属性过滤 -->
  </li>
</template>

<script setup>
import { ref, computed } from 'vue';

const items = ref([
  { id: 1, name: 'Item 1', active: true },
  { id: 2, name: 'Item 2', active: false },
]);

// ✅ 正确 - 使用计算属性
const activeItems = computed(() => {
  return items.value.filter(item => item.active);
});
</script>
```

## 组件设计

### 单文件组件结构

```vue
<!--
  UserCard.vue
  用户卡片组件，展示用户基本信息和操作按钮
-->
<script setup>
/**
 * 导入依赖
 */
import { ref, computed, onMounted } from 'vue';
import { useUserStore } from '@/stores/user';

/**
 * Props 定义
 */
const props = defineProps({
  userId: {
    type: Number,
    required: true,
  },
  showActions: {
    type: Boolean,
    default: true,
  },
});

/**
 * Emits 定义
 */
const emit = defineEmits(['edit', 'delete']);

/**
 * 组合式函数
 */
const userStore = useUserStore();

/**
 * 响应式状态
 */
const user = ref(null);
const loading = ref(false);

/**
 * 计算属性
 */
const displayName = computed(() => {
  return user.value ? `${user.value.firstName} ${user.value.lastName}` : '';
});

/**
 * 方法
 */
const loadUser = async () => {
  loading.value = true;
  try {
    user.value = await userStore.fetchUser(props.userId);
  } finally {
    loading.value = false;
  }
};

const handleEdit = () => {
  emit('edit', props.userId);
};

/**
 * 生命周期
 */
onMounted(() => {
  loadUser();
});
</script>

<template>
  <div class="user-card">
    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="user" class="user-info">
      <h3>{{ displayName }}</h3>
      <p>{{ user.email }}</p>
      <div v-if="showActions" class="actions">
        <button @click="handleEdit">Edit</button>
        <button @click="emit('delete', userId)">Delete</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.user-card {
  padding: 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.loading {
  color: #666;
}

.user-info h3 {
  margin: 0 0 8px;
}

.actions {
  margin-top: 12px;
}

.actions button {
  margin-right: 8px;
}
</style>
```

## 检查清单

提交 Vue 代码前，确保：

- [ ] 使用 Composition API（Vue 3）
- [ ] Props 有类型定义
- [ ] 不直接修改 props
- [ ] 列表渲染有 key 属性
- [ ] 响应式数据正确使用 ref/reactive
- [ ] 副作用正确清理（onUnmounted）
- [ ] 避免在模板中使用复杂表达式
- [ ] 使用计算属性替代复杂模板逻辑
- [ ] 组件有清晰的命名和结构
- [ ] 样式使用 scoped
