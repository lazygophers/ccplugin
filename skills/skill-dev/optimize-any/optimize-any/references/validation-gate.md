# Validation Gate — 改前/改后对比操作手册

> 配套主 SKILL.md Phase 2「单变量轮」。主文件讲 4 阶段流程与本门定位；本文件只讲**验证门每一步的具体命令与判定**：质量门跑法、before/after 同 prompt 对比、token/缓存定性评估、ratchet 回滚、触顶 break 信号。

## 1. 质量门命令（每轮必跑，项目 CLAUDE.md 强制）

改过组件内容即过门，禁跳过直接提交：

```bash
# 单次跑（macOS 无 timeout 命令，别加 timeout，用 gtimeout 或不加）
claude -p "<改后内容或触发 prompt>" --output-format stream-json \
  | jq -r 'select(.type=="result" and .subtype=="success") | .result'
```

端点抖动（记忆 `claude-p-endpoint-flaky`：路由到火山方舟 CodingPlan 端点，长 prompt 高频 400 / `subscription expired`，非真随机而是配额门槛），包一层重试循环，**单个组件单独跑，禁批量串行**（撞 Bash 2min 超时）：

```bash
for i in $(seq 1 8); do
  out=$(claude -p "<待测内容>" --output-format stream-json \
        | jq -r 'select(.type=="result" and .subtype=="success") | .result' 2>/dev/null)
  # 过滤空 / API Error / subscription 失败才算拿到一次成功
  if [ -n "$out" ] && ! echo "$out" | grep -qiE 'API Error|subscription|expired'; then
    echo "$out"; exit 0
  fi
  echo "retry $i: 端点抖动，重试" >&2
done
echo "3 次仍败 → 人工验 + 小步可回滚提交，标『待端点恢复补跑』" >&2; exit 1
```

- 拿到非空且有意义的 result → 过门；3 次仍败 → 停，标「待端点恢复补跑」，禁「我觉得能过」直落。
- 判定「有意义」：返回结果**符合 prompt 预期**（识别正确组件 / 触发正确路由 / 输出结构合规），非仅「非空」。

## 2. 改前 → 改后对比（同一测试 prompt 两轮盲评）

每轮**同一组 prompt** 跑改前 / 改后两遍，对比输出质量。**禁同 context 自评**（乐观偏差，LLM-as-judge ~46% 准确率），spawn 独立子 agent 或独立 session 盲评（不告知哪版是改后）。

```bash
# 0. 改前先记 commit 哈希（回滚锚点）
PREV=$(git rev-parse HEAD)
git add <组件> && git commit -m "optimize <组件>: <单变量摘要>"

# 1. 测试集三段式（现场编，照搬 skill-dev 的 test-prompts.json 结构）
#    should-trigger   — 该触发的 prompt，改后必须仍命中
#    should-not-trigger — 不该触发的，改后必须仍不命中（防误触发）
#    edge             — 模糊边界，路由不漂移

# 2. 两轮盲评（独立子 agent / 独立 session，喂同一 prompt 不带版本标识）
#    compare(before=PREV 版输出, after=当前版输出)
#    维度：触发准确 / 输出质量 / 无负面（冗余·跑偏·格式怪）
```

接受准则（**任一退步即 reject**）：

- 触发准确：should-trigger 全命中 + should-not-trigger 全不命中。
- 输出无负面：无新增冗余 / 跑偏 / 格式怪（人审或独立 judge 共识）。
- 分数：gross Δ > 0 即可（fine-grained 不可信，见主文件诚实边界）。

## 3. token / 缓存命中率定性评估（禁编数字）

无第三方基准，仅作定性维度对比（改前 vs 改后，方向对即留）：

| 维度 | 改好信号 | 退化信号 |
|---|---|---|
| 文件大小 | ↓（删冗余 / 合并重复） | ↑ > 原 ×1.5（体积膨胀护栏拒提交） |
| 前缀稳定性 | ↑（frontmatter / 开头固定段不动，缓存命中） | ↓（开头频繁变，缓存失效） |
| 冗余度 | ↓（无重复段落 / 无 AI 腔） | ↑（为凑分加废话，典型触顶症状） |

- 禁给具体 token 数 / 命中率百分比（未基准测，编数字违反事实声明硬规）。
- 体积护栏硬线：改后 > 原 ×1.5 → 拒提交，先精简（删冗余 / 合并重复）回 ×1.5 内再评。

## 4. git revert ratchet 棘轮（只留严格更好）

**只留严格更好的改动，任一退步即 revert**。回滚用 `git revert HEAD` 建反向 commit，**禁 `git reset --hard`**（丢工作树未提交改动 + 历史链断裂）：

```bash
# 通过 → 留（已在第 2 节 commit），记 success
# 退步 → revert
git revert HEAD --no-edit          # 建反向 commit，保可追溯链
# 记失败尝试原因到主文件 Phase 3 汇总：归因不明 / Δ<0 / 触发变差
```

revert 失败 fallback（冲突 / 工作树脏）：先 `git stash` 再重试；仍失败则从 `PREV` commit 读出内容覆盖当前文件手动恢复，告知用户。

分支纪律：优化在独立分支 `optimize/<组件>-YYYYMMDD` 上跑，rejected edit 不入主分支历史；破坏性变更（触发词 / 大范围重写）merge 必须用户确认。

## 5. 触顶 break 信号（连续 2 轮 Δ < 2 → 停）

```text
round N:   Δ < 2  → 记一次「触顶候选」，继续
round N+1: Δ < 2  → break，进 Phase 3 汇总（禁硬凑 MAX_ROUNDS）
```

- `+0.x` 是**停手信号非继续信号**：典型症状 = 加废话让 LLM 觉得更详细，体积膨胀即警示。
- 已混改多维无法归因 → revert 全部，逐维重做建立因果（主文件硬规 3）。
- 见好就收优于凑轮数：ratchet 只认严格更好，不认轮数 KPI。

## 与主文件分工

| 主 SKILL.md | 本文件 |
|---|---|
| 4 阶段流程（Phase 0-3）+ 硬规 + 路由 + 失败模式速查 | 验证门**每步命令**：质量门重试脚本 / before-after 对比序列 / token 定性表 / revert 指令 / 触顶判据 |

主文件 Phase 2 第 2 步指向本文件拿操作命令；本文件不重复流程叙述，只给可执行步骤。
