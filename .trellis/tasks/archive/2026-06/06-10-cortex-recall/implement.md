# Implement — cortex-recall

## Phase A — 建 skill (S1)

- [ ] **[L3] S1** dispatch trellis-implement: 建 skills/cortex-recall/{SKILL.md, references/{search,fallback,writeback}.md} 按 design.md

## Phase B — wire (S2)

- [ ] **[L1] S2** main: plugin.json skills 7→8 + keywords + agent + README + llms + 根 marketplace.json cortex desc

## Phase C — 验证 (S3)

- [ ] **[L1] S3** main: frontmatter 体检 + plugin.json/marketplace JSON + 6 既有脚本 smoke + grep cortex-recall + 暂存

## Phase D — 收尾

- [ ] commit + archive + journal

## S1 Dispatch Prompt

```
Active task: .trellis/tasks/06-10-cortex-recall

## 目标
建 cortex-recall skill: SKILL.md (≤ 60 行) + references/{search,fallback,writeback}.md. 无脚本. skill 步骤指导 main 调 vault 搜索 / WebSearch / cortex-extract 回填.

## 已知
- 流程: 搜双层 vault → 未命中 WebSearch → 拿不准问用户 → 答案按 scope 归类自动回填
- frontmatter (见 design.md "frontmatter" 节, 照抄)
- 归类复用 cortex-context-digest scope 规则; 路径/级别复用 cortex-schema; 回填调 cortex-extract/cortex-save
- 项目级 vault 仅 memory + 领域 (无 项目/脚本); 外部 repo 回填只落全局
- L0/L1 写入仍 ask; 回填默认 L3-short; 互联网答案带 source URL
- 内容细节见 design.md "references/*.md" 三节

## 工作目录
cwd: /Users/luoxin/persons/lyxamour/ccplugin
可改: plugins/tools/cortex/skills/cortex-recall/** (新建)
禁改: 其他

## 输出限
- SKILL.md ≤ 60 行; 各 reference ≤ 220 行
- frontmatter: name=cortex-recall, desc ≤ 512, wtu ≤ 128, arguments 字符串, user-invocable: true, 无 "用户说"

## 验收
- SKILL.md frontmatter yaml 合法 + 上述约束
- 3 references 存在
- search.md 含 项目级+用户级; fallback.md 含 WebSearch+问用户顺序; writeback.md 含 scope 判定 + L0/L1 ask

## Sub-agent 自防护
trellis-implement, 不再 spawn.

完成回报: 4 文件清单 + 行数 + 验证退出码.
```

## S3 验证命令

```bash
d=plugins/tools/cortex/skills/cortex-recall
test -f $d/SKILL.md && [[ $(wc -l < $d/SKILL.md) -le 60 ]] && echo "SKILL ok"
for r in search fallback writeback; do test -f $d/references/$r.md && echo "ref $r ok"; done
python3 -c "
import yaml
fm=yaml.safe_load(open('$d/SKILL.md').read().split('---')[1])
assert fm['name']=='cortex-recall'
assert len(fm['description'])<=512 and len(fm['when_to_use'])<=128
assert '用户说' not in fm['description'] and '用户说' not in fm['when_to_use']
assert isinstance(fm['arguments'],str) and fm.get('user-invocable') is True
print('frontmatter OK')
"
python3 -c "import json; d=json.load(open('plugins/tools/cortex/.claude-plugin/plugin.json')); assert len(d['skills'])==8 and './skills/cortex-recall' in d['skills']; print('plugin.json 8 OK')"
python3 -c "import json; d=json.load(open('.claude-plugin/marketplace.json')); print('marketplace JSON OK')"
for f in agents/cortex.md README.md llms.txt; do grep -q cortex-recall plugins/tools/cortex/$f && echo "$f ok"; done
# smoke
bash plugins/tools/cortex/scripts/validate-layout.sh --target plugins/tools/cortex/tests/fixtures/layout-ok/ >/dev/null; echo "validate $?"
bash plugins/tools/cortex/scripts/lint.sh --check --target plugins/tools/cortex/tests/fixtures/lint/ >/dev/null 2>&1; echo "lint $?"
bash plugins/tools/cortex/scripts/extract.sh --dry-run --target plugins/tools/cortex/tests/fixtures/extract/ >/dev/null 2>&1; echo "extract $?"
```
