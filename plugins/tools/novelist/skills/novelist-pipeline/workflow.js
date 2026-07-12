export const meta = {
	name: "novelist-pipeline",
	description:
		"逐章串行批量写小说: 前置(路线图→世界观→预检)→逐章(write→三环并行检测(check/humanize/proofread)→fix串行改→定稿, 前章定稿才写下一章)→统一检查。root 与设定全部参数化/从小说文件读, 不硬编码任何小说。支持 mode=write(默认, 全流程)/review/humanize/proofread/polish/rewrite/outline 选 phase 子集。",
	phases: [
		{ title: "路线图", detail: "生成/读取本批章节路线图(outliner)" },
		{ title: "世界观", detail: "更新本批涉及的设定/人物(worldbuilder)" },
		{ title: "预检", detail: "路线图一致性预检(continuity-auditor 预检模式)" },
		{ title: "写作", detail: "逐章 chapter-writer 写正文" },
		{ title: "查一致", detail: "continuity-auditor 一致性检查" },
		{ title: "去AI味", detail: "humanizer 去AIGC" },
		{ title: "校对", detail: "proofreader 文字校对" },
		{ title: "修复", detail: "fix-c/t/h 按三环结果定点修复" },
		{ title: "定稿", detail: "indexer 登记索引+进度" },
		{ title: "统一检查", detail: "一次性审本批全部章节 + 与全书设定/前文冲突" },
	],
};

// ===== mode 路由(每 mode 跑哪些 phase; write 全跑 → 零回归) =====
// phase 名对齐 meta.phases / 各函数 label。outline 批级: 仅路线图, 无写作/收尾/统一。
// rewrite 走 fixer 的 rewrite 模式 A(报告修复, 最安全); 默认仅跑统一检查前的"修复"环节。
const MODE_PHASES = {
	write: new Set(["路线图", "世界观", "预检", "写作", "查一致", "去AI味", "校对", "修复", "定稿", "统一检查"]),
	review: new Set(["查一致", "统一检查"]),
	humanize: new Set(["去AI味", "修复", "定稿"]),
	proofread: new Set(["校对", "修复", "定稿"]),
	polish: new Set(["查一致", "去AI味", "校对", "修复", "定稿", "统一检查"]),
	rewrite: new Set(["修复", "统一检查"]),
	outline: new Set(["路线图"]),
};
function needsPhase(mode, phase) {
	const set = MODE_PHASES[mode];
	return set ? set.has(phase) : false;
}

// ===== 入参(全部来自 args, 不硬编码任何小说) =====
const _args = typeof args === "string" ? JSON.parse(args) : args || {};
const MODE = _args.mode || "write"; // write(默认, 零回归)/review/humanize/proofread/polish/rewrite/outline
if (!MODE_PHASES[MODE]) {
	log(`⚠️ 未知 mode=${MODE}, 退化为 write`);
}
const EFFECTIVE_MODE = MODE_PHASES[MODE] ? MODE : "write";
const ROOT = _args.root;
if (!ROOT) {
	throw new Error(
		"novelist-pipeline: 缺 args.root(小说项目根目录绝对路径)。pipeline 不硬编码任何小说路径。",
	);
}
const START = _args.startChapter || 1;
const END =
	_args.endChapter ||
	(_args.count ? START + Math.max(1, _args.count) - 1 : START);

const CHAPTER_DIR = `${ROOT}/章节`;
const PROGRESS_FILE = `${ROOT}/元数据/进度.md`;
const INDEX_FILE = `${ROOT}/章节/_索引.md`;

// ===== 可调常量(对齐 novelist 插件评分门控) =====
const BATCH_SIZE = 5; // 每批最多章数, 超出自动分批
const MAX_FIX_ATTEMPTS = Infinity; // fix 最大重试(无限: 一直修到达标; 用户要求)
const PASS_TOTAL = 100; // 定稿综合分阈值(严格 == 100 才过; 零容忍满分门控)
const PASS_CONSISTENCY = 100; // 一致性单项阈值(严格 == 100 才过; 零冲突含 建议级)
const PASS_HUMANNESS = 100; // 人味单项阈值(严格 == 100 才过)
const MAX_AGENT_RETRIES = Infinity; // 单 agent 调用失败重试上限(无限: 一直重试到成功; 用户要求)
const EST_SEC_PER_AGENT = 30; // 单 agent 调用预估耗时(秒, 仅粗估; Workflow 禁 Date.now 无法实测)
let AGENT_CALLS = 0; // 全局 agent 实际调用计数(含重试), 用于整体耗时预估

function ch(n) {
	return String(n).padStart(3, "0");
}

// ===== agent 调用统一重试包装(兜网络/余额/瞬时 API 失败) =====
// Workflow 自带的 retry 用尽后会返回 null; 本包装在其上再加应用层重试, 仍失败才返回 null + 明确报错。
async function callAgent(prompt, opts, retries = MAX_AGENT_RETRIES) {
	const tag = (opts && opts.label) || "agent";
	for (let i = 1; i <= retries; i++) {
		try {
			AGENT_CALLS++;
			const r = await agent(prompt, opts);
			if (r != null) return r;
			log(`⚠️ ${tag} 返回 null(第${i}次), 重试`);
		} catch (e) {
			log(`⚠️ ${tag} 调用异常: ${(e && e.message) || e}(第${i}次), 重试`);
		}
	}
	log(`❌ ${tag} 重试 ${retries} 次仍失败(网络/余额/API?), 放弃该 callAgent(返回 null)`);
	return null;
}

// ===== 评分 =====
function extractScore(text) {
	if (!text) return 90;
	const m = text.match(/(\d+)\s*分/);
	return m ? parseInt(m[1]) : 90;
}
function computeScores(checkResult, proofResult, humanResult) {
	// 满分门控(零容忍): cScore/tScore/hScore 任一 <100 → total <100 → 不过。
	// cScore 二值(冲突?80:100): 有任一冲突 → 80 <100 不过; 零冲突 → 100 过。
	// tScore/hScore 由 extractScore 解析 agent「N分」, 满分要求 ==100。
	// total = cScore×0.5 + tScore×0.2 + hScore×0.3; 三项非全 100 时自然 <100, 已满足零容忍。
	const cScore = checkResult?.includes("冲突") ? 80 : 100;
	const tScore = extractScore(proofResult);
	const hScore = extractScore(humanResult);
	const total =
		Math.round((cScore * 0.5 + tScore * 0.2 + hScore * 0.3) * 10) / 10;
	return { cScore, tScore, hScore, total };
}

// ===== 路线图章节结构化 schema(强制 agent 返回结构, 不靠文本正则) =====
const ROUTE_SCHEMA = {
	type: "object",
	properties: {
		found: { type: "boolean", description: "路线图文件读取时是否已存在" },
		chapters: {
			type: "array",
			description: "每章结构化数据",
			items: {
				type: "object",
				properties: {
					num: { type: "integer", description: "章节号" },
					title: { type: "string" },
					event: { type: "string", description: "核心事件" },
					change: { type: "string", description: "人物变化" },
					foreshadow: { type: "string", description: "伏笔推进" },
					hook: { type: "string", description: "收尾钩子" },
					target: { type: "integer", description: "字数目标" },
				},
				required: ["num", "title"],
			},
		},
	},
	required: ["chapters"],
};

function chaptersToMap(arr) {
	const m = {};
	if (!Array.isArray(arr)) return m;
	for (const c of arr) {
		const num = parseInt(c?.num);
		if (!Number.isInteger(num)) continue;
		m[num] = {
			title: c.title || `第${ch(num)}章`,
			event: c.event || "",
			change: c.change || "",
			foreshadow: c.foreshadow || "",
			hook: c.hook || "待定",
			target: parseInt(c.target) || 3000,
		};
	}
	return m;
}

// ===== 前置: 路线图(schema 强制 agent 返回结构化 chapters, 不靠脆弱文本正则) =====
// 返回 { num: info } map, 或 null(失败)。修复: callAgent() 无 schema 时返回的是 agent 最终文本(摘要),
// 不一定含 ### 第NNN章 标题 → 旧 parseRouteMap 正则匹配 0 → 静默跳过整批。改用 schema 拿结构化数据。
async function ensureRouteMap(batchStart, batchEnd) {
	const batchId = `${ch(batchStart)}-${ch(batchEnd)}`;
	const routeFile = `${ROOT}/情节/第${batchId}章路线图.md`;

	// 1) 读已存在路线图(schema 强制结构化)
	let res = null;
	try {
		res = await callAgent(
			`读取路线图文件 ${routeFile}。\n` +
				`若文件存在: 解析其中每一章, 按 schema 返回 found=true + chapters 数组(每章含 num/title/event/change/foreshadow/hook/target)。\n` +
				`若文件不存在: 返回 found=false + chapters 空数组。`,
			{ label: `路线图查:${batchId}`, phase: "路线图", agentType: "novelist:outliner", schema: ROUTE_SCHEMA },
		);
	} catch (e) {
		log(`路线图读取异常: ${e.message}`);
	}
	if (res && res.found && Array.isArray(res.chapters) && res.chapters.length) {
		log(`路线图 ${batchId} 已存在(${res.chapters.length}章), 直接使用`);
		return chaptersToMap(res.chapters);
	}

	// 2) 不存在 → 生成 + 结构化返回(双产出: 写文件 + 返回 chapters)
	log(`生成路线图 ${batchId}`);
	let attempt = 0;
	while (true) {
		attempt++;
		let gen = null;
		try {
			gen = await callAgent(
				`目标: 为本小说生成第${ch(batchStart)}-${ch(batchEnd)}章路线图。\n\n` +
					`先读取该小说的设定(不要凭空设计):\n` +
					`- ${ROOT}/总览.md (题材/基调)\n` +
					`- ${ROOT}/大纲/总纲.md + ${ROOT}/大纲/分卷.md (核心冲突/结局/分卷结构)\n` +
					`- ${ROOT}/情节/主线.md + ${ROOT}/情节/伏笔.md (主线节点/伏笔台账)\n` +
					`- ${ROOT}/元数据/进度.md (上一章状态, 衔接点)\n\n` +
					`方法: 引用 novelist-outline skill 的大纲/情节编排方法。\n\n` +
					`双重产出(都要):\n` +
					`(a) 写入文件 ${routeFile}: markdown, 每章一块「### 第NNN章：标题」+ 核心事件/人物变化/伏笔推进/收尾钩子/字数目标。\n` +
					`(b) 同时按 schema 返回 chapters 数组(num/title/event/change/foreshadow/hook/target), 内容与文件一致。\n\n` +
					`验收: 与主线表对齐, 伏笔位与伏笔表一致, chapters 覆盖第${ch(batchStart)}-${ch(batchEnd)}章。`,
				{ label: `路线图:${batchId}`, phase: "路线图", agentType: "novelist:outliner", schema: ROUTE_SCHEMA },
			);
		} catch (e) {
			log(`路线图生成异常: ${e.message}`);
		}
		if (gen && Array.isArray(gen.chapters) && gen.chapters.length) {
			log(`路线图 ${batchId} 生成(${gen.chapters.length}章)`);
			return chaptersToMap(gen.chapters);
		}
		log(`⚠️ 路线图 ${batchId} 第${attempt}次返回 chapters 为空, 重试(无限)`);
	}
}

// ===== 前置: 更新世界观(读小说自己的规则.md) =====
async function updateWorldview(batchStart, batchEnd) {
	const batchId = `${ch(batchStart)}-${ch(batchEnd)}`;
	return callAgent(
		`根据第${batchId}章路线图, 更新本小说世界观设定。\n\n` +
			`读取: ${ROOT}/情节/第${batchId}章路线图.md、${ROOT}/世界观/规则.md、${ROOT}/世界观/_索引.md。\n\n` +
			`任务:\n` +
			`1. 检查路线图是否涉及新世界观元素(新规则/新势力/新地理/新设定)\n` +
			`2. 有则更新 世界观/ 或 设定/ 对应文件\n` +
			`3. 新设定不得与现有 规则.md 硬约束冲突(力量体系边界与代价)\n` +
			`4. 有新人物 → 在 人物/<名>/ 建 简介.md/经历.md/关系.md 三件套\n\n` +
			`直接改文件。无新元素返回"无需更新"。`,
		{ label: `世界观:${batchId}`, phase: "世界观", agentType: "novelist:worldbuilder" },
	);
}

// ===== 前置: 一致性预检 =====
async function preCheck(batchStart, batchEnd) {
	const batchId = `${ch(batchStart)}-${ch(batchEnd)}`;
	return callAgent(
		`【预检模式】对第${batchId}章路线图做一致性预检(写正文前, 可直接改路线图消除冲突)。\n\n` +
			`读取: ${ROOT}/情节/第${batchId}章路线图.md、${ROOT}/世界观/规则.md、${ROOT}/情节/主线.md、${ROOT}/情节/伏笔.md、${ROOT}/元数据/进度.md。\n\n` +
			`检查项:\n` +
			`1. 路线图与主线表对齐\n2. 伏笔推进与伏笔台账一致\n3. 与进度.md 最后一章衔接连续\n` +
			`4. 不违反 规则.md 硬约束\n5. 人物行为符合 人物/简介.md\n\n` +
			`输出: 通过 / 有冲突(附问题清单)。有冲突则直接改路线图文件消除。`,
		{ label: `预检:${batchId}`, phase: "预检", agentType: "novelist:continuity-auditor" },
	);
}

// ===== Writer(引用 novelist-craft 镜片, 读小说自己的规则/人物) =====
async function writer(chNum, info) {
	const num = ch(chNum);
	const prevNum = ch(chNum - 1);
	return callAgent(
		`你是小说写作员。职责: 只写正文, 不做其他。\n\n` +
			`目标: 写第${num}章「${info.title}」正文, 约${info.target}字。\n\n` +
			`四要素(来自路线图):\n` +
			`(i) 出场+梗概: ${info.title}。核心事件: ${info.event}\n` +
			`(ii) 事件前: 读 ${CHAPTER_DIR}/第${prevNum}章-*.md 了解前章结尾\n` +
			`(iii) 事件后: ${info.change}; 推进伏笔「${info.foreshadow}」\n` +
			`(iv) 收尾钩子: ${info.hook}\n\n` +
			`硬约束: 读 ${ROOT}/世界观/规则.md, 不得越界(力量体系边界与代价)。\n` +
			`人物: 读 ${ROOT}/人物/ 相关角色 简介.md, 言行合性格。\n` +
			`文风: 引用 novelist-craft 按题材(读 ${ROOT}/总览.md)取叙事镜片; 人物言行查 novelist-character, 设定守 novelist-worldview。\n\n` +
			`输出: 直接写到 ${CHAPTER_DIR}/第${num}章-${info.title}.md\n` +
			`验收: 不违反 规则.md, 字数±500。失败缺设定标「需要:」回传。`,
		{ label: `写作:${num}`, phase: "写作", agentType: "novelist:chapter-writer" }
	);
}

// ===== Checker(continuity-auditor 风格) =====
async function checker(chNum, title) {
	const num = ch(chNum);
	const file = `${CHAPTER_DIR}/第${num}章-${title}.md`;
	return callAgent(
		`你是小说一致性检查员(只读, 只查一致性, 不管文字/风格)。\n\n` +
			`读取: ${file}、${ROOT}/世界观/规则.md、${ROOT}/元数据/进度.md、${ROOT}/情节/伏笔.md、相关 人物/简介.md。\n\n` +
			`方法: 引用 novelist-check skill 的 18 子项一致性审查(6 维 × 3 子项: 设定冲突3/人物矛盾3/世界观违规3/时间线错乱3/伏笔遗漏3/逻辑合理性3) + continuity-auditor 视角。\n` +
    `18 子项核对: 1a物品定义不一/1b术语定义不一/1c组织定义不一; 2a关系突变无铺垫/2b行为违背性格动机/2c生死状态错乱; 3a力量超规则边界/3b未付代价/3c势力格局自相矛盾; 4a事件顺序矛盾/4b年龄经历对不上/4c时长跨度不合理; 5a计划回收章未回收/5b结尾悬空伏笔/5c伏笔间相互矛盾; 6a因果断裂/6b关键转折动机不足/6c过度巧合。\n` +
			`零容忍满分门控: 任一子项有冲突(含 建议级)即 <100 不过。\n\n` +
			`先把检查报告写入 ${ROOT}/元数据/检查报告/第${num}章.md(含结论/评分/18 子项问题清单, 每条标 [子项编号 维度]), 再按下方格式返回结论。\n\n` +
			`输出格式:\n结论: 通过 / 有冲突\n评分: 0-100(100=零冲突含 建议级, 满分才过)\n问题清单: [子项编号 维度] [行号] 问题(如有)`,
		{ label: `查一致:${num}`, phase: "查一致", agentType: "novelist:continuity-auditor" }
	);
}

// ===== Humanizer(去AI味, 算客观人味分) =====
async function humanizer(chNum, title) {
	const num = ch(chNum);
	const file = `${CHAPTER_DIR}/第${num}章-${title}.md`;
	return callAgent(
		`你是小说去AI味检测员(本阶段只检测AI味, 不改正文; 改由 fix 阶段做)。\n\n` +
			`读取: ${file}\n\n` +
			`引用 novelist-humanize skill 跑 score_aitaste.py 取客观人味分(只读不改正文)。\n\n` +
			`检测项: 1.匀质句长 2.陈词过渡(首先/其次/综上/然而) 3.模板腔 4.空泛抽象 ` +
			`5.否定式排比(不是A而是B) 6.过度总结。\n\n` +
			`本阶段**只检测不改正文**(改由 fix 阶段统一做, 避免三环并行写冲突)。把检测报告写入 ${ROOT}/元数据/校对报告/第${num}章-deaigc.md(问题清单), 再按下方格式返回评分。\n\n` +
			`输出格式:\n人味评分: 0-100(100=完全人写, ==${PASS_HUMANNESS}满分才通过)\nAI味等级: 轻/中/重\n问题清单: [行号] 原文 → 建议改法(不就地改)`,
		{ label: `去AI味:${num}`, phase: "去AI味", agentType: "novelist:humanizer" }
	);
}

// ===== Proofer(校对) =====
async function proofer(chNum, title) {
	const num = ch(chNum);
	const file = `${CHAPTER_DIR}/第${num}章-${title}.md`;
	return callAgent(
		`你是小说校对检测员(本阶段只检测文字问题, 不改正文; 改由 fix 阶段做)。\n\n` +
			`读取: ${file}\n\n` +
			`方法: 引用 novelist-proofread skill 的 12 子项文字校对(5 维 × 子项: 错别字3/语法3/标点2/用词2/用字统一2)。\n` +
    `12 子项核对: 1a形近字(己/已/的得地)/1b音近字/1c多字漏字; 2a成分残缺(缺主谓宾)/2b搭配不当/2c语序与关联词; 3a误用与缺失/3b中英标点混用与引号书名号配对; 4a啰嗦重复与口语书面混杂/4b生造词; 5a人物称呼译名(基准 人物/_索引.md)/5b术语专有名词(基准 设定/_索引.md)。\n` +
			`零容忍满分门控: 任一子项有错即 <100 不过。\n\n` +
			`本阶段**只检测不改正文**(改由 fix 阶段统一做)。把检测报告写入 ${ROOT}/元数据/校对报告/第${num}章.md(12 子项问题清单, 每条标 [子项编号 维度]), 再按下方格式返回评分。\n\n` +
			`输出格式:\n评分: 0-100(100=无任何文字问题, 满分才过)\n问题清单: [子项编号 维度] [行号] 原文 → 建议改法(不就地改)`,
		{ label: `校对:${num}`, phase: "校对", agentType: "novelist:proofreader" }
	);
}

// ===== Fixer(按三环结果修, 不改风格不重写) =====
async function fixer(chNum, title, checkResult, proofResult, humanResult) {
	const num = ch(chNum);
	const file = `${CHAPTER_DIR}/第${num}章-${title}.md`;
	const needsCheckFix = checkResult?.includes("冲突");
	const needsTextFix =
		proofResult?.includes("逻辑矛盾") || proofResult?.includes("硬伤");
	const needsHumanFix =
		humanResult?.includes("中") || humanResult?.includes("重");

	const fixers = [];
	if (needsCheckFix)
		fixers.push(() =>
			callAgent(
				`【mode=fix 单点冲突修正】修复一致性问题(单点事实修正, 不重写整段/不改结构; 段落级重写交 chapter-writer)。读 ${file}、${ROOT}/世界观/规则.md。\n问题: ${checkResult?.slice(0, 500)}\n只修冲突点(改一处事实陈述消除冲突), 不改风格。直接改文件。`,
				{ label: `修一致:${num}`, phase: "修复", agentType: "novelist:chapter-writer" }
			),
		);
	if (needsTextFix)
		fixers.push(() =>
			callAgent(
				`【mode=fix 文字修正】修复文字硬伤(就地改错别字/语法/标点, 不改风格)。读 ${file}。\n问题: ${proofResult?.slice(0, 500)}\n只修硬伤(对应 12 子项), 不改风格。直接改文件。`,
				{ label: `修文字:${num}`, phase: "修复", agentType: "novelist:proofreader" }
			),
		);
	if (needsHumanFix)
		fixers.push(() =>
			callAgent(
				`【mode=fix 人味修正】去 AI 味修复(就地改, 不重写)。读 ${file}。\n问题: ${humanResult?.slice(0, 500)}\n修匀质句长/陈词过渡/模板腔, 保持风格, 不动剧情。直接改文件。`,
				{ label: `修AI味:${num}`, phase: "修复", agentType: "novelist:humanizer" }
			),
		);

	// 串行执行: 三个 fix 都改同一章文件, 并行会写冲突, 必须一个改完再下一个
	for (const f of fixers) await f();
}

// ===== Finalizer(只更新索引/进度, 串行) =====
async function finalizer(chNum, title, checkResult, proofResult, humanResult) {
	const num = ch(chNum);
	const { cScore, tScore, hScore, total } = computeScores(
		checkResult,
		proofResult,
		humanResult,
	);
	const passed =
		total >= PASS_TOTAL &&
		cScore >= PASS_CONSISTENCY &&
		hScore >= PASS_HUMANNESS;

	await callAgent(
		`更新索引与进度。第${num}章「${title}」${passed ? "定稿" : "需复审"}(综合${total})。\n\n` +
			`1. 读 ${INDEX_FILE}, 在表格末尾加一行:\n` +
			`| 第${num}章 | ${title} | ~${"目标字数"} | ${passed ? "定稿" : "需复审"} | 综合${total}(一致${cScore}/文字${tScore}/人味${hScore}) |\n\n` +
			`2. 读 ${PROGRESS_FILE}, 更新: 已写章节+1; 当前阶段; 下一步。\n\n` +
			`直接改文件, 保持现有 markdown 格式。`,
		{ label: `定稿:${num}`, phase: "定稿", agentType: "novelist:indexer" },
	);
	return { chapter: num, title, total, cScore, tScore, hScore, passed };
}

// ===== 单章收尾链(三环并行检测 → fix 串行改 → 定稿), push allResults =====
// mode 守卫: 各检测/修复/定稿按 MODE_PHASES 决定是否跑; write 时全跑(零回归)。
// 非 write 模式: 无 writer → finishChain 不与写作并行, 直接逐章跑对应 phase 子集。
// rewrite 特例: 无三环检测, 直接派 novelist-rewrite skill(fix 模式A 报告修复)。
async function finishChain(n, info) {
	let checkResult,
		humanResult,
		proofResult,
		attempts = 0;

	// rewrite 独立路径: 派 rewrite-fix-A 单独改本章, 不走三环。
	if (EFFECTIVE_MODE === "rewrite") {
		const num = ch(n);
		const file = `${CHAPTER_DIR}/第${num}章-${info.title}.md`;
		log(`第${num}章 rewrite(模式A 报告修复)`);
		await callAgent(
			`你是小说重写员(novelist-rewrite skill)。对第${num}章执行 fix 模式 A(报告修复, 最安全)。\n\n` +
				`读取: ${file}、${ROOT}/世界观/规则.md、${ROOT}/元数据/进度.md、相关 人物/简介.md、${ROOT}/情节/主线.md、${ROOT}/情节/伏笔.md。\n\n` +
				`方法: 引用 novelist-rewrite skill。先做一致性/文字/AI味 综合检测, 生成重写报告, 再按报告定点修复(改事实/错字/AI腔), 不整章推翻重写。\n` +
				`硬约束: 不违反 规则.md, 保持人物性格与风格连续。\n\n` +
				`直接改 ${file}。把重写报告写入 ${ROOT}/元数据/检查报告/第${num}章.md。\n` +
				`输出: 完成 / 失败(标「需要:」回传)。`,
			{ label: `重写:${num}`, phase: "修复", agentType: "novelist:chapter-writer" },
		);
		const r = { chapter: num, title: info.title, total: null, attempts: 0, estCalls: 1, passed: false, skipped: true };
		allResults.push(r);
		log(`✅ 第${num}章「${info.title}」rewrite(模式A) 完成(未定稿, 交统一检查)`);
		return;
	}

	while (true) {
		// 各检测环按 needsPhase 决定跑/不跑; 全跳过则直接退出循环(无评分来源)。
		const runCheck = needsPhase(EFFECTIVE_MODE, "查一致");
		const runHuman = needsPhase(EFFECTIVE_MODE, "去AI味");
		const runProof = needsPhase(EFFECTIVE_MODE, "校对");
		if (!runCheck && !runHuman && !runProof) break; // 无检测 phase(如 rewrite 仅 fix)

		// 三环并行检测(查一致/去AI味/校对正交, 均只读不改正文 → 无写冲突)
		const tasks = [];
		if (runCheck) tasks.push(() => checker(n, info.title)); // 一致性
		if (runHuman) tasks.push(() => humanizer(n, info.title)); // 去AI味
		if (runProof) tasks.push(() => proofer(n, info.title)); // 校对
		const detectResults = await parallel(tasks);
		// 按 run* 顺序回填到三槽位
		let slot = 0;
		if (runCheck) checkResult = detectResults[slot++];
		if (runHuman) humanResult = detectResults[slot++];
		if (runProof) proofResult = detectResults[slot++];

		const { cScore, tScore, hScore, total } = computeScores(
			checkResult,
			proofResult,
			humanResult,
		);
		log(
			`第${ch(n)}章评分: 一致${cScore} 文字${tScore} 人味${hScore} 综合${total}(第${attempts}次)`,
		);
		const passed =
			total >= PASS_TOTAL &&
			cScore >= PASS_CONSISTENCY &&
			hScore >= PASS_HUMANNESS;
		if (passed || attempts >= MAX_FIX_ATTEMPTS || !needsPhase(EFFECTIVE_MODE, "修复")) {
			if (!passed && !needsPhase(EFFECTIVE_MODE, "修复"))
				log(`第${ch(n)}章 本 mode 不跑修复 phase, 标记检测结果入库`);
			if (!passed)
				log(`⚠️ 第${ch(n)}章 超重试上限(${MAX_FIX_ATTEMPTS}), 标记需复审`);
			break;
		}
		log(`第${ch(n)}章 分数不足, 执行 fix(第${attempts + 1}次)`);
		await fixer(n, info.title, checkResult, proofResult, humanResult);
		attempts++;
	}
	const r = needsPhase(EFFECTIVE_MODE, "定稿")
		? await finalizer(n, info.title, checkResult, proofResult, humanResult)
		: { chapter: ch(n), title: info.title, total: null, attempts, estCalls: 0, passed: false, skipped: true };
	if (r.attempts == null) r.attempts = attempts;
	if (r.estCalls == null) r.estCalls = 2 + 3 * (attempts + 1) + 2 * attempts;
	allResults.push(r);
	log(`✅ 第${ch(n)}章「${info.title}」${r.skipped ? "(未定稿)" : r.passed ? "定稿" : "需复审"}`);
}

// ===== 后置: 统一一致性检查(一个 agent 一次性审本批全部章节 + 与全书设定/前文的冲突) =====
// 不是逐章独立检查, 而是把本批章节作为整体, 核对它们之间 + 与现有设定/历史内容的冲突。
async function unifiedCheck(chapterNums, chapters) {
	const batchId = `${ch(chapterNums[0])}-${ch(chapterNums[chapterNums.length - 1])}`;
	log(`统一检查: 一次性审本批 ${chapterNums.length} 章(第${batchId})整体一致性`);
	const fileList = chapterNums
		.map((n) => `${CHAPTER_DIR}/第${ch(n)}章-${chapters[n].title}.md`)
		.join("、");
	const result = await callAgent(
		`【统一检查】把本批全部章节(第${batchId}, 共${chapterNums.length}章)作为**整体**做一次性一致性审查。\n` +
			`目的: 核对本批这次变更的章节 与 本批内部 + 与现有设定/前文/历史内容 是否存在冲突。\n\n` +
			`读取本批全部正文: ${fileList}\n` +
			`读取全书设定与历史(对照基线): ${ROOT}/世界观/规则.md、${ROOT}/世界观/、${ROOT}/设定/、${ROOT}/人物/(相关角色)、${ROOT}/情节/主线.md、${ROOT}/情节/伏笔.md、${ROOT}/元数据/进度.md, 以及本批之前的相邻章节(衔接处)。\n\n` +
			`检查维度(本批 vs 本批内部 + vs 历史):\n` +
			`1. 本批章节**之间**是否互相矛盾(跨章人物/事件/时间线)\n` +
			`2. 本批是否违反全书 规则.md 硬约束(力量体系边界与代价)\n` +
			`3. 本批人物言行是否与现有人物设定/性格一致\n` +
			`4. 本批埋设/回收的伏笔与 伏笔.md 台账是否一致(跨章追踪)\n` +
			`5. 本批与**之前章节**(前文)的衔接、时间线、状态是否连贯\n` +
			`6. 本批引入的新设定是否与历史设定/术语冲突\n\n` +
			`把统一检查报告写入 ${ROOT}/元数据/检查报告/统一-第${batchId}章.md(按上述 6 维 + 按涉及章节归类问题)。\n` +
			`输出: 通过 / 有冲突(附按章节与维度归类的问题清单)`,
		{
			label: `统一检查:${batchId}`,
			phase: "统一检查",
			agentType: "novelist:continuity-auditor",
		},
	);
	const hasConflict = result != null && result.includes("冲突");
	if (hasConflict) log(`⚠️ 统一检查发现冲突(第${batchId}批), 详见 元数据/检查报告/统一-第${batchId}章.md`);
	else log(`✅ 统一检查通过(第${batchId}批整体一致)`);
	return { batchId, hasConflict, result };
}

// ===== 主流程 =====
log(
	`流水线启动: mode=${EFFECTIVE_MODE} 第${ch(START)}-${ch(END)}章, root=${ROOT}, 每批${BATCH_SIZE}章`,
);
const allResults = [];

for (let batchStart = START; batchStart <= END; batchStart += BATCH_SIZE) {
	const batchEnd = Math.min(batchStart + BATCH_SIZE - 1, END);
	const batchId = `${ch(batchStart)}-${ch(batchEnd)}`;
	log(`\n===== 批次 ${batchId} (mode=${EFFECTIVE_MODE}) =====`);

	// Phase 1: 路线图(write + outline 才跑; 其余 mode 跳前置直接进收尾链)
	if (needsPhase(EFFECTIVE_MODE, "路线图")) {
		const chapters = await ensureRouteMap(batchStart, batchEnd);
		if (!chapters) {
			log(`⚠️ 批次 ${batchId} 路线图缺失(生成/解析失败), 跳过`);
			continue;
		}
		const chapterNums = Object.keys(chapters)
			.map(Number)
			.filter((n) => n >= batchStart && n <= batchEnd);
		if (chapterNums.length === 0) {
			log(`⚠️ 批次 ${batchId} 路线图无第${batchStart}-${batchEnd}章数据, 跳过`);
			continue;
		}

		// outline: 仅路线图, 跳 worldview/precheck/写作/收尾/统一
		if (EFFECTIVE_MODE === "outline") {
			log(`批次 ${batchId} mode=outline 仅生成路线图, 完成`);
			continue;
		}

		if (needsPhase(EFFECTIVE_MODE, "世界观")) await updateWorldview(batchStart, batchEnd);
		if (needsPhase(EFFECTIVE_MODE, "预检")) await preCheck(batchStart, batchEnd);

		await runChapters(batchStart, batchEnd, chapterNums, chapters);
		continue;
	}

	// 非 write 非 outline(无路线图 phase): 从现有章节目录探测标题 → 跑收尾链
	const probed = await probeChapters(batchStart, batchEnd);
	if (probed.nums.length === 0) {
		log(`⚠️ 批次 ${batchId} mode=${EFFECTIVE_MODE} 未找到第${batchStart}-${batchEnd}章文件, 跳过`);
		continue;
	}
	await runChapters(batchStart, batchEnd, probed.nums, probed.chapters);
}

// 从现有章节目录探测标题(非 write/outline mode 用, 避免依赖路线图)。
// ponytail: 单次 agent 列目录代替逐章探测, 省 N 次调用; 若文件命名不规范可退化手填。
async function probeChapters(batchStart, batchEnd) {
	const batchId = `${ch(batchStart)}-${ch(batchEnd)}`;
	const list = await callAgent(
		`列出目录 ${CHAPTER_DIR} 下所有以 "第" 开头、"-章" 形如 "第NNN章-标题.md" 的文件名。\n` +
			`只返回第${ch(batchStart)}-${ch(batchEnd)}章范围内的文件名(每行一个, 形如 "第NNN章-标题.md")。\n` +
			`若无任何匹配, 返回 "无"。`,
		{ label: `探测章节:${batchId}`, phase: "查一致", agentType: "novelist:indexer" },
	);
	const chapters = {};
	const nums = [];
	if (typeof list === "string" && !list.startsWith("无")) {
		const re = /第(\d{3})章-(.+?)\.md/g;
		let m;
		while ((m = re.exec(list)) !== null) {
			const n = parseInt(m[1]);
			if (n >= batchStart && n <= batchEnd) {
				chapters[n] = { num: n, title: m[2], target: 3000 };
				nums.push(n);
			}
		}
	}
	nums.sort((a, b) => a - b);
	return { nums, chapters };
}

// 跑章节收尾链(write 时双流水线并行; 非 write 时 finishChain 逐章串行)
async function runChapters(batchStart, batchEnd, chapterNums, chapters) {
	const batchId = `${ch(batchStart)}-${ch(batchEnd)}`;
	const doWrite = needsPhase(EFFECTIVE_MODE, "写作");

	if (doWrite) {
		// Phase 2(write 模式): 流水线并行 —— 当前章收尾链 ‖ 下一章 write
		// 用 Workflow parallel() 显式声明并行(原生 Promise.all 的 await agent 不会被 Workflow 并发调度)。
		const first = chapterNums[0];
		log(`第${ch(first)}章 Writer 开始`);
		await writer(first, chapters[first]);
		log(`第${ch(first)}章 Writer 完成`);

		for (let i = 0; i < chapterNums.length; i++) {
			const cur = chapterNums[i];
			const next = chapterNums[i + 1];
			// 并行: 第 cur 章收尾链 ‖ 第 next 章 write
			await parallel([
				() => finishChain(cur, chapters[cur]),
				() =>
					next != null
						? (async () => {
								log(`第${ch(next)}章 Writer 开始(与第${ch(cur)}章收尾并行)`);
								await writer(next, chapters[next]);
								log(`第${ch(next)}章 Writer 完成`);
							})()
						: Promise.resolve(),
			]);
		}
		log(`批次 ${batchId} 流水线(收尾 ‖ 下一章写)完成`);
	} else {
		// 非 write: 无 writer, finishChain 逐章串行(共享章节文件, 但各章独立 → 仍可并行, 受并发约束串行以求稳)
		for (const n of chapterNums) {
			await finishChain(n, chapters[n]);
		}
		log(`批次 ${batchId} 收尾链完成(mode=${EFFECTIVE_MODE}, 无 writer)`);
	}

	// Phase 3: 后置(统一检查)
	if (needsPhase(EFFECTIVE_MODE, "统一检查")) {
		await unifiedCheck(chapterNums, chapters);
	}
}

// ===== 汇总: 每章明细 + 整体评分 + 预估耗时(非实测) =====
const passed = allResults.filter((r) => r.passed);
const failed = allResults.filter((r) => !r.passed);
const N = allResults.length || 1;
const avg = (k) => Math.round((allResults.reduce((s, r) => s + (r[k] || 0), 0) / N) * 10) / 10;
const fmtMin = (sec) => `${sec}s(≈${Math.round((sec / 60) * 10) / 10}分)`;

log(`\n===== 流水线完成 =====`);
log(`章数: ${allResults.length} | 定稿: ${passed.length} | 需复审: ${failed.length} | 定稿率 ${Math.round((passed.length / N) * 100)}%`);
log(`平均分: 综合${avg("total")} (一致${avg("cScore")} / 文字${avg("tScore")} / 人味${avg("hScore")})`);
log(`agent 总调用 ${AGENT_CALLS} 次 | 整体预估耗时 ≈ ${fmtMin(AGENT_CALLS * EST_SEC_PER_AGENT)} (粗估: 调用数×${EST_SEC_PER_AGENT}s, 非实测——Workflow 禁 Date.now)`);

log(`\n每章明细:`);
for (const r of allResults) {
	log(
		`  第${r.chapter}章「${r.title}」` +
			`综合${r.total}(一致${r.cScore}/文字${r.tScore}/人味${r.hScore}) ` +
			`fix${r.attempts || 0}轮 ${r.passed ? "✅定稿" : "⚠️需复审"} ` +
			`预估≈${fmtMin((r.estCalls || 0) * EST_SEC_PER_AGENT)}`,
	);
}
if (failed.length)
	log(`\n复审章节: ${failed.map((r) => `第${r.chapter}章(${r.total}分)`).join(", ")}`);

return {
	results: allResults,
	passed: passed.length,
	failed: failed.length,
	avgTotal: avg("total"),
	agentCalls: AGENT_CALLS,
	estSeconds: AGENT_CALLS * EST_SEC_PER_AGENT,
};
