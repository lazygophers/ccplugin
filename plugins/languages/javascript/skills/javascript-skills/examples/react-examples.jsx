/**
 * React 开发示例
 *
 * 本文件展示了 React 18+ 组件开发的正确模式。
 * 遵循 javascript-skills/specialized/react-development.md 规范。
 */

// =============================================================================
// 1. 函数组件 + Hooks
// =============================================================================

/**
 * UserCard 组件 - 带数据获取和清理逻辑
 * @param {Object} props - 组件属性
 * @param {number} props.userId - 用户 ID
 * @param {Function} [props.onEdit] - 编辑回调
 * @returns {JSX.Element}
 */
function UserCard({ userId, onEdit }) {
  const [user, setUser] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    let cancelled = false;

    async function loadUser() {
      try {
        setLoading(true);
        // 模拟 API 调用
        await new Promise(resolve => setTimeout(resolve, 500));
        const mockUser = { id: userId, name: `User ${userId}`, email: `user${userId}@example.com` };

        if (!cancelled) {
          setUser(mockUser);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadUser();

    return () => {
      cancelled = true;  // 清理逻辑
    };
  }, [userId]);

  if (loading) {
    return React.createElement('div', { className: 'user-card loading' }, 'Loading...');
  }

  if (error) {
    return React.createElement('div', { className: 'user-card error' }, error);
  }

  return React.createElement('div', { className: 'user-card' },
    React.createElement('h3', null, user.name),
    React.createElement('p', null, user.email),
    onEdit && React.createElement('button', {
      onClick: () => onEdit(user.id)
    }, 'Edit')
  );
}

// =============================================================================
// 2. 自定义 Hook
// =============================================================================

/**
 * useUser - 获取用户数据的自定义 Hook
 * @param {number} userId - 用户 ID
 * @returns {Object} { user, loading, error, refetch }
 */
function useUser(userId) {
  const [user, setUser] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  const fetchUser = React.useCallback(async () => {
    try {
      setLoading(true);
      await new Promise(resolve => setTimeout(resolve, 500));
      const mockUser = { id: userId, name: `User ${userId}`, email: `user${userId}@example.com` };
      setUser(mockUser);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  React.useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  return { user, loading, error, refetch: fetchUser };
}

/**
 * UserProfile 组件 - 使用自定义 Hook
 */
function UserProfile({ userId }) {
  const { user, loading, error } = useUser(userId);

  if (loading) {
    return React.createElement('div', null, 'Loading...');
  }

  if (error) {
    return React.createElement('div', null, 'Error: ', error);
  }

  return React.createElement('div', null,
    React.createElement('h1', null, user.name),
    React.createElement('p', null, user.email)
  );
}

// =============================================================================
// 3. useReducer - 复杂状态管理
// =============================================================================

const initialState = {
  user: null,
  loading: false,
  error: null,
};

function userReducer(state, action) {
  switch (action.type) {
    case 'FETCH_START':
      return { ...state, loading: true, error: null };
    case 'FETCH_SUCCESS':
      return { ...state, loading: false, user: action.payload };
    case 'FETCH_ERROR':
      return { ...state, loading: false, error: action.payload };
    default:
      return state;
  }
}

/**
 * UserProfileWithReducer 组件 - 使用 useReducer
 */
function UserProfileWithReducer({ userId }) {
  const [state, dispatch] = React.useReducer(userReducer, initialState);

  React.useEffect(() => {
    const fetchUser = async () => {
      dispatch({ type: 'FETCH_START' });
      try {
        await new Promise(resolve => setTimeout(resolve, 500));
        const mockUser = { id: userId, name: `User ${userId}` };
        dispatch({ type: 'FETCH_SUCCESS', payload: mockUser });
      } catch (error) {
        dispatch({ type: 'FETCH_ERROR', payload: error.message });
      }
    };

    fetchUser();
  }, [userId]);

  if (state.loading) {
    return React.createElement('div', null, 'Loading...');
  }

  if (state.error) {
    return React.createElement('div', null, 'Error: ', state.error);
  }

  return React.createElement('div', null,
    React.createElement('h1', null, state.user.name)
  );
}

// =============================================================================
// 4. useMemo 和 useCallback
// =============================================================================

/**
 * ExpensiveList 组件 - 使用 useMemo 优化计算
 */
function ExpensiveList({ items, filter }) {
  const filteredItems = React.useMemo(() => {
    console.log('Filtering items...');
    return items.filter(item =>
      item.name.toLowerCase().includes(filter.toLowerCase())
    );
  }, [items, filter]);

  return React.createElement('ul', null,
    filteredItems.map(item =>
      React.createElement('li', { key: item.id }, item.name)
    )
  );
}

/**
 * ButtonList 组件 - 使用 useCallback 优化回调
 */
function ButtonList({ items, onSelect }) {
  const handleClick = React.useCallback((id, event) => {
    event.stopPropagation();
    onSelect(id);
  }, [onSelect]);

  return React.createElement('ul', null,
    items.map(item =>
      React.createElement('li', { key: item.id },
        React.createElement('button', {
          onClick: (e) => handleClick(item.id, e)
        }, item.name)
      )
    )
  );
}

// =============================================================================
// 5. 表单处理
// =============================================================================

/**
 * LoginForm 组件 - 受控表单
 */
function LoginForm({ onSubmit }) {
  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [errors, setErrors] = React.useState({});

  const validate = React.useCallback(() => {
    const newErrors = {};
    if (!email) newErrors.email = 'Email is required';
    if (!password) newErrors.password = 'Password is required';
    if (password.length < 8) newErrors.password = 'Password must be at least 8 characters';
    return newErrors;
  }, [email, password]);

  const handleSubmit = React.useCallback((e) => {
    e.preventDefault();
    const validationErrors = validate();

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    onSubmit({ email, password });
  }, [email, password, onSubmit, validate]);

  return React.createElement('form', { onSubmit: handleSubmit },
    React.createElement('div', null,
      React.createElement('label', null, 'Email'),
      React.createElement('input', {
        type: 'email',
        value: email,
        onChange: (e) => setEmail(e.target.value)
      }),
      errors.email && React.createElement('span', { className: 'error' }, errors.email)
    ),
    React.createElement('div', null,
      React.createElement('label', null, 'Password'),
      React.createElement('input', {
        type: 'password',
        value: password,
        onChange: (e) => setPassword(e.target.value)
      }),
      errors.password && React.createElement('span', { className: 'error' }, errors.password)
    ),
    React.createElement('button', { type: 'submit' }, 'Login')
  );
}

// =============================================================================
// 6. 错误边界
// =============================================================================

/**
 * ErrorBoundary 组件
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error);
    console.error('Component stack:', errorInfo.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return React.createElement('div', { className: 'error-fallback' },
        React.createElement('h2', null, 'Something went wrong'),
        React.createElement('p', null, this.state.error?.message || 'Unknown error'),
        React.createElement('button', {
          onClick: () => this.setState({ hasError: false, error: null })
        }, 'Try again')
      );
    }

    return this.props.children;
  }
}

// =============================================================================
// 7. React.memo - 性能优化
// =============================================================================

/**
 * UserCardMemo 组件 - 使用 React.memo
 */
const UserCardMemo = React.memo(function UserCardMemo({ user, onSelect }) {
  console.log('Rendering UserCardMemo:', user.id);

  return React.createElement('div', { onClick: () => onSelect(user.id) },
    React.createElement('h3', null, user.name),
    React.createElement('p', null, user.email)
  );
});

// 自定义比较函数
const UserCardMemoWithCompare = React.memo(
  function UserCardMemoWithCompare({ user, onSelect }) {
    return React.createElement('div', { onClick: () => onSelect(user.id) },
      React.createElement('h3', null, user.name)
    );
  },
  (prevProps, nextProps) => {
    // 只比较 user.id
    return prevProps.user.id === nextProps.user.id;
  }
);

// =============================================================================
// 8. Context API
// =============================================================================

/**
 * 创建用户 Context
 */
const UserContext = React.createContext(null);

/**
 * UserProvider 组件
 */
function UserProvider({ children }) {
  const [user, setUser] = React.useState(null);

  const login = React.useCallback(async (credentials) => {
    // 模拟登录
    await new Promise(resolve => setTimeout(resolve, 500));
    const mockUser = { id: 1, name: 'Logged User', email: credentials.email };
    setUser(mockUser);
  }, []);

  const logout = React.useCallback(() => {
    setUser(null);
  }, []);

  const value = React.useMemo(() => ({
    user,
    login,
    logout,
    isAuthenticated: !!user,
  }), [user, login, logout]);

  return React.createElement(UserContext.Provider, { value }, children);
}

/**
 * useUser Hook - 访问用户 Context
 */
function useUserContext() {
  const context = React.useContext(UserContext);
  if (!context) {
    throw new Error('useUserContext must be used within UserProvider');
  }
  return context;
}

// =============================================================================
// 导出
// =============================================================================

// 导出所有组件和 Hooks
export {
  // 基础组件
  UserCard,
  UserProfile,
  UserProfileWithReducer,

  // 自定义 Hooks
  useUser,

  // 性能优化
  ExpensiveList,
  ButtonList,
  UserCardMemo,
  UserCardMemoWithCompare,

  // 表单
  LoginForm,

  // 错误处理
  ErrorBoundary,

  // Context
  UserContext,
  UserProvider,
  useUserContext,
};

// 注意：这是 JSX 的纯 JavaScript 表示形式
// 在实际项目中，使用 JSX 语法和 .jsx 扩展名
