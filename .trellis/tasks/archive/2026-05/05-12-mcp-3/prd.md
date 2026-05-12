# PRD — MCP 3 骨架工具完整实现

## 背景

`mcp/cortex_mcp.py` 三个工具仍 `return _wrap(_err(1, "not_implemented"))`:
1. `cortex_memory_consolidate` — ledger → views 巩固
2. `cortex_memory_promote` — partial logic (policy gate done, 缺真 move + frontmatter update)
3. `cortex_session_import` — claude code transcript → sessions/

## 目标

3 工具完整实现, 不再 not_implemented。

## 设计

### 1. `cortex_memory_consolidate()`

输入: 无 (或 optional `week_offset` 默认 -1 = 上周)
输出: `{ok, code, data: {consolidated_file, candidates_added, connections_added}}`

流程:
1. 计算上周日期范围 (今天 -7 ~ -1)
2. 读 `<vault>/记忆体系/L4-流水账/ledger/<date>.jsonl` 7 天范围
3. 解析事件 → 提取 (entity, topic, context) 三元组
4. 统计 freq:
   - freq ≥ 3 → 写入 `views/candidates.md` (晋级候选, 表格行)
   - 跨域出现 ≥ 3 次 → 写 `知识库/反思/连接/<YYYY-Wnn>.md`
5. 高频 top 20 实体/主题 → 写 `views/consolidated/<YYYY-Wnn>.md`
6. 返回统计

实现要点:
- ledger 不存在 → 返回 ok=True data 空
- 使用现有 `lib.file_lock` 写文件
- views/* 已存追加, 不重写

### 2. `cortex_memory_promote(uri, target_level)`

现有: policy gate (L2→L1 / L1→L0 returns code 6 needs_user_approval)
缺: L4→L3 / L3→L2 auto path 实际 move file + 更新 frontmatter

补:
```python
def _do_promote(uri, target_level, vault):
    """实际执行晋级: mv 文件到新 level 目录 + 改 frontmatter level/uri + 更新 uri-index.json."""
    from pathlib import Path
    import yaml, re, json
    
    src_path = resolve_uri(uri, vault)
    if not src_path.is_file():
        return _err(2, f"uri not found: {uri}")
    
    # 解析新 uri (按 target_level)
    src_level = uri.split("://")[0]
    rest = uri.split("://", 1)[1]
    # 简化: target_level 决定目录, path 保留 (用户后续可改)
    new_uri = f"{target_level}://{rest}"
    new_path = resolve_uri(new_uri, vault)
    
    # 读 fm
    text = src_path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        return _err(1, "invalid frontmatter")
    fm = yaml.safe_load(m.group(1)) or {}
    body = m.group(2)
    
    # 更新 fm
    fm["uri"] = new_uri
    fm["level"] = target_level
    fm["promoted_at"] = datetime.now(timezone.utc).isoformat()
    # weight 调整 (晋级时 boost)
    fm["weight"] = min(1.0, (fm.get("weight", 0.5) or 0.5) + 0.1)
    
    new_path.parent.mkdir(parents=True, exist_ok=True)
    new_fm = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False)
    new_path.write_text(f"---\n{new_fm}---\n{body}")
    if src_path != new_path:
        src_path.unlink()
    
    # 更新 uri-index.json
    idx_path = vault / "_meta" / "uri-index.json"
    if idx_path.is_file():
        try:
            idx = json.loads(idx_path.read_text())
            entries = idx.get("entries", [])
            for e in entries:
                if e.get("uri") == uri:
                    e["uri"] = new_uri
                    e["level"] = target_level
                    break
            idx["entries"] = entries
            idx_path.write_text(json.dumps(idx, ensure_ascii=False, indent=2))
        except Exception:
            pass
    
    return _ok({"new_uri": new_uri, "new_path": str(new_path.relative_to(vault))})
```

cortex_memory_promote 调用:
- policy gate 通过 → `_do_promote`
- 不通过 → return code=6

### 3. `cortex_session_import(transcript_path)`

输入: claude code transcript JSON 文件路径 (e.g. `~/.claude/projects/<id>/<sid>.jsonl`)
输出: `{ok, code, data: {session_uri, events_appended}}`

流程:
1. 验证 transcript 文件存在 + 是 jsonl
2. 解析 jsonl, 提取 metadata:
   - session_id (从文件名或 first line)
   - cli (固定 "claude-code" 或从 metadata 提)
   - started_at / ended_at (first/last line timestamp)
   - turn_count
3. 写 `<vault>/记忆体系/L4-流水账/sessions/<cli>/<YYYY-MM>/<sid>.md`:
   - frontmatter: cli/session_id/started_at/ended_at/turn_count/source_path
   - body: 摘要 (前 N 条 user/assistant turns 简要 + key tool calls)
4. append 每个 turn 到 `<vault>/记忆体系/L4-流水账/ledger/<date>.jsonl`:
   - `{type: "session_event", session_id, turn_idx, role, content_preview, ts}`
5. 返回

实现要点:
- 大 transcript cap N=200 turns (避免日志爆量)
- backup_path 不创建 (claude code transcript 原文件用户的, 不动)

## 实施

### Step 1: 加 datetime/yaml/json imports (若缺)

### Step 2: 3 函数实现

### Step 3: 测试

`tests/python/test_mcp_3_tools.py`:
- consolidate empty ledger → ok 空 data
- consolidate 假 ledger → 检 consolidated_file 写入
- promote L4→L3 auto → 文件 mv + fm 更新
- promote L2→L1 → returns code 6
- session_import 假 transcript → sessions/ 文件创建

## 验收

- [ ] 3 工具不再 not_implemented
- [ ] grep `not_implemented` cortex_mcp.py → 0 (除 cortex_memory_consolidate 边界 case 可能用作 fallback message)
- [ ] consolidate 跑 mock ledger 写 views/consolidated/<week>.md
- [ ] promote L4→L3 mv + 更新 fm + uri-index
- [ ] session_import 写 sessions/ + ledger
- [ ] 271 + 新测试 PASS

## 风险

| 风险 | 缓解 |
|------|------|
| consolidate 大 ledger 慢 | cap 7 天 × 大事件 OK; 异步 cron 跑 |
| promote 移文件破坏 wikilink | 暂不处理 (cortex-linker agent 后续维护); 用户自行刷新 |
| transcript 格式变 | 兼容 jsonl 主流字段, 缺则跳过 |

## 子任务

单 trellis-implement。
