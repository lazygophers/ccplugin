# API 参考

## 配置模块

### Config

```python
@dataclass
class Config:
    layout_mode: LayoutMode = LayoutMode.EXPANDED
    layout_width: int = 80
    theme: str = "default"
    refresh: RefreshConfig
    cache: CacheConfig
    show_user: bool = True
    show_progress: bool = True
    show_resources: bool = True
    show_errors: bool = True
    verbose: bool = False
    debug: bool = False
```

**方法:**

- `to_dict() -> Dict[str, Any]`: 转换为字典
- `from_dict(data: Dict[str, Any]) -> Config`: 从字典创建
- `validate() -> List[str]`: 验证配置，返回错误列表

### ConfigManager

```python
class ConfigManager:
    def __init__(self, config_path: Optional[Path] = None)
    def load(self, config_path: Optional[Path] = None) -> Config
    def save(self, config_path: Optional[Path] = None) -> None
    def get(self) -> Config
    def update(self, **kwargs) -> None
    def reload(self) -> Config
    def watch(self, callback: callable) -> None
```

## 解析器模块

### IncrementalParser

```python
class IncrementalParser:
    def __init__(self, initial_state: Optional[ParserContext] = None)
    def parse(self, chunk: str) -> List[TranscriptEvent]
    def get_state(self) -> ParserContext
    def reset(self) -> None
    def get_events(self) -> List[TranscriptEvent]
```

## 事件模块

### 事件类型

```python
class EventType(Enum):
    USER_MESSAGE = "user_message"
    ASSISTANT_MESSAGE = "assistant_message"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    STATUS_CHANGE = "status_change"
    ERROR = "error"
```

### TranscriptEvent

```python
@dataclass
class TranscriptEvent:
    event_type: EventType
    timestamp: float
    data: Dict[str, Any]
    metadata: Dict[str, Any]
```

## 状态追踪模块

### StateAggregator

```python
class StateAggregator:
    def __init__(self)
    def register_source(self, source: DataSource) -> None
    def update(self, event: TranscriptEvent) -> None
    def aggregate(self, dimension: StateDimension) -> AggregatedState
    def get_all_states(self) -> Dict[StateDimension, AggregatedState]
    def clear(self) -> None
```

### StateCache

```python
class StateCache:
    def __init__(self, l1_size: int = 1000, default_ttl: int = 60)
    def get(self, key: CacheKey) -> Optional[AggregatedState]
    def set(self, key: CacheKey, value: AggregatedState, ttl: Optional[int] = None) -> None
    def invalidate(self, pattern: Optional[str] = None) -> None
    def clear(self) -> None
    def get_stats(self) -> Dict[str, CacheStats]
```

## 布局模块

### Layout (基类)

```python
class Layout(ABC):
    def __init__(self, config: Optional[Dict[str, Any]] = None)
    @abstractmethod
    def render(self, state: AggregatedState) -> str
    @abstractmethod
    def get_width(self) -> int
    def validate(self) -> bool
    def supports_component(self, component: str) -> bool
    def enable_component(self, component: str) -> None
    def disable_component(self, component: str) -> None
```

### LayoutFactory

```python
class LayoutFactory:
    @classmethod
    def register(cls, name: str, layout_cls: Type[Layout]) -> None
    @classmethod
    def create(cls, name: str, config: Optional[Dict[str, Any]] = None) -> Layout
    @classmethod
    def create_from_config(cls, config: Config) -> Layout
    @classmethod
    def list_available(cls) -> List[str]
    @classmethod
    def is_registered(cls, name: str) -> bool
```

## 渲染模块

### ThemeManager

```python
class ThemeManager:
    def load_theme(self, name: str) -> Theme
    def register_theme(self, theme: Theme) -> None
    def list_themes(self) -> List[str]
    def get_current_theme(self) -> Optional[Theme]
    def apply_theme(self, theme: Theme) -> None
    def load_from_file(self, path: Path) -> Theme
    def save_to_file(self, theme: Theme, path: Path) -> None
```

### IncrementalRenderer

```python
class IncrementalRenderer:
    def __init__(self, layout: Layout, theme: Theme)
    def render(self, state: AggregatedState) -> str
    def reset(self) -> None
    def get_cache_stats(self) -> Dict[str, Any]
```

## 核心模块

### StatuslineLoop

```python
class StatuslineLoop:
    def __init__(self, config: Config)
    def start(self) -> None
    def pause(self) -> None
    def resume(self) -> None
    def process(self, transcript: str) -> str
    def get_stats(self) -> Dict[str, Any]
```

## 兼容模块

### CompatLayer

```python
class CompatLayer:
    def __init__(self, config: Any, use_legacy: bool = False, warn: bool = True)
    def process(self, transcript: str) -> str
```

### 工具函数

```python
def format_statusline(transcript: str, config: Optional[Config] = None) -> str
def load_config_from_file(path: Path) -> Config
def save_config_to_file(config: Config, path: Path) -> None
def migrate_config(old_config: Dict[str, Any]) -> Dict[str, Any]
```
