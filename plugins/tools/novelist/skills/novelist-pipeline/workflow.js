export const meta = {
	name: "novelist-pipeline",
	description:
		"逐章串行批量写小说: 前置(路线图→世界观→预检)→逐章(write→check→humanize→proofread→fix循环→定稿, 前章定稿才写下一章)→统一检查。root 与设定全部参数化/从小说文件读, 不硬编码任何小说。",
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
		{ title: "统一检查", detail: "全批最终一致性检查" },
	],
};

// ===== 入参(全部来自 args, 不硬编码任何小说) =====
const _args = typeof args === "string" ? JSON.parse(args) : args || {};
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
const MAX_FIX_ATTEMPTS = 10; // fix 最大重试
const PASS_TOTAL = 85; // 定稿综合分阈值
const PASS_CONSISTENCY = 85; // 一致性单项阈值
const PASS_HUMANNESS = 70; // 人味单项阈值(对齐 score_aitaste 目标线)

function ch(n) {
	return String(n).padStart(3, "0");
}

// ===== 评分 =====
function extractScore(text) {
	if (!text) return 90;
	const m = text.match(/(\d+)\s*分/);
	return m ? parseInt(m[1]) : 90;
}
function computeScores(checkResult, proofResult, humanResult) {
	const cScore = checkResult?.includes("冲突") ? 80 : 95;
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
// 返回 { num: info } map, 或 null(失败)。修复: agent() 无 schema 时返回的是 agent 最终文本(摘要),
// 不一定含 ### 第NNN章 标题 → 旧 parseRouteMap 正则匹配 0 → 静默跳过整批。改用 schema 拿结构化数据。
async function ensureRouteMap(batchStart, batchEnd) {
	const batchId = `${ch(batchStart)}-${ch(batchEnd)}`;
	const routeFile = `${ROOT}/情节/第${batchId}章路线图.md`;

	// 1) 读已存在路线图(schema 强制结构化)
	let res = null;
	try {
		res = await agent(
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
	for (let attempt = 1; attempt <= 2; attempt++) {
		let gen = null;
		try {
			gen = await agent(
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
		log(`⚠️ 路线图 ${batchId} 第${attempt}/2 次返回 chapters 为空, 重试`);
	}
	log(`❌ 路线图 ${batchId} 生成/解析失败(chapters 始终为空), 跳过本批`);
	return null;
}

// ===== 前置: 更新世界观(读小说自己的规则.md) =====
async function updateWorldview(batchStart, batchEnd) {
	const batchId = `${ch(batchStart)}-${ch(batchEnd)}`;
	return agent(
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
	return agent(
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
	return agent(
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
	return agent(
		`你是小说一致性检查员(只读, 只查一致性, 不管文字/风格)。\n\n` +
			`读取: ${file}、${ROOT}/世界观/规则.md、${ROOT}/元数据/进度.md、${ROOT}/情节/伏笔.md、相关 人物/简介.md。\n\n` +
			`方法: 引用 novelist-check skill 的六维一致性审查 + continuity-auditor 视角。\n` +
    `检查项: 1.世界观/力量规则是否被违反 2.人物性格是否一致 3.伏笔推进是否合理 ` +
			`4.与前章衔接是否连贯 5.时间线是否错乱。\n\n` +
			`先把检查报告写入 ${ROOT}/元数据/检查报告/第${num}章.md(含结论/评分/六维问题清单), 再按下方格式返回结论。\n\n` +
			`输出格式:\n结论: 通过 / 有冲突\n评分: 0-100(100=完美一致)\n问题清单: [行号] 问题(如有)`,
		{ label: `查一致:${num}`, phase: "查一致", agentType: "novelist:continuity-auditor" }
	);
}

// ===== Humanizer(去AI味, 算客观人味分) =====
async function humanizer(chNum, title) {
	const num = ch(chNum);
	const file = `${CHAPTER_DIR}/第${num}章-${title}.md`;
	return agent(
		`你是小说去AI味员(只查/改 AI 味, 不管一致性/错别字, 不动剧情)。\n\n` +
			`读取: ${file}\n\n` +
			`引用 novelist-humanize skill 去味并取客观人味分(它会自行定位 score_aitaste.py 脚本 + 接力外部 humanizer)。\n\n` +
			`检查项: 1.匀质句长 2.陈词过渡(首先/其次/综上/然而) 3.模板腔 4.空泛抽象 ` +
			`5.否定式排比(不是A而是B) 6.过度总结。命中则就地改(保持风格, 不动剧情)。\n\n` +
			`命中处就地改正文, 并把去AI味报告写入 ${ROOT}/元数据/校对报告/第${num}章-deaigc.md(改动清单), 再按下方格式返回评分。\n\n` +
			`输出格式:\n人味评分: 0-100(100=完全人写, ≥${PASS_HUMANNESS}通过)\nAI味等级: 轻/中/重\n问题清单: [行号] 原文 → 改后(如有)`,
		{ label: `去AI味:${num}`, phase: "去AI味", agentType: "novelist:humanizer" }
	);
}

// ===== Proofer(校对) =====
async function proofer(chNum, title) {
	const num = ch(chNum);
	const file = `${CHAPTER_DIR}/第${num}章-${title}.md`;
	return agent(
		`你是小说校对员(只校文字, 不管一致性/AI味, 不动剧情)。\n\n` +
			`读取: ${file}\n\n` +
			`方法: 引用 novelist-proofread skill 的文字校对清单。\n` +
    `检查项: 1.错别字 2.语法 3.标点 4.用词准确 5.逻辑矛盾(前后自相矛盾)。\n\n` +
			`先把校对报告写入 ${ROOT}/元数据/校对报告/第${num}章.md(问题清单), 再按下方格式返回评分。\n\n` +
			`输出格式:\n评分: 0-100(100=无任何文字问题)\n问题清单: [行号] 原文 → 改后(如有)`,
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
			agent(
				`修复一致性问题。读 ${file}、${ROOT}/世界观/规则.md。\n问题: ${checkResult?.slice(0, 500)}\n只修冲突点, 不改风格。直接改文件。`,
				{ label: `修一致:${num}`, phase: "修复", agentType: "novelist:chapter-writer" }
			),
		);
	if (needsTextFix)
		fixers.push(() =>
			agent(
				`修复文字硬伤。读 ${file}。\n问题: ${proofResult?.slice(0, 500)}\n只修硬伤, 不改风格。直接改文件。`,
				{ label: `修文字:${num}`, phase: "修复", agentType: "novelist:proofreader" }
			),
		);
	if (needsHumanFix)
		fixers.push(() =>
			agent(
				`去 AI 味修复。读 ${file}。\n问题: ${humanResult?.slice(0, 500)}\n修匀质句长/陈词过渡/模板腔, 保持风格, 不动剧情。直接改文件。`,
				{ label: `修AI味:${num}`, phase: "修复", agentType: "novelist:humanizer" }
			),
		);

	if (fixers.length) await parallel(fixers);
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

	await agent(
		`更新索引与进度。第${num}章「${title}」${passed ? "定稿" : "需复审"}(综合${total})。\n\n` +
			`1. 读 ${INDEX_FILE}, 在表格末尾加一行:\n` +
			`| 第${num}章 | ${title} | ~${"目标字数"} | ${passed ? "定稿" : "需复审"} | 综合${total}(一致${cScore}/文字${tScore}/人味${hScore}) |\n\n` +
			`2. 读 ${PROGRESS_FILE}, 更新: 已写章节+1; 当前阶段; 下一步。\n\n` +
			`直接改文件, 保持现有 markdown 格式。`,
		{ label: `定稿:${num}`, phase: "定稿", agentType: "novelist:indexer" },
	);
	return { chapter: num, title, total, cScore, tScore, hScore, passed };
}

// ===== 后置: 统一一致性检查(全批并行只读) =====
async function unifiedCheck(chapterNums, chapters) {
	log(`统一一致性检查: ${chapterNums.length}章并行`);
	const results = await parallel(
		chapterNums.map(
			(n) => () =>
				agent(
					`对第${ch(n)}章做最终全局一致性检查。\n\n` +
						`读取: ${CHAPTER_DIR}/第${ch(n)}章-${chapters[n].title}.md、${ROOT}/世界观/规则.md、${ROOT}/元数据/进度.md、${ROOT}/情节/伏笔.md、${ROOT}/情节/主线.md。\n\n` +
						`检查: 1.前后章衔接 2.伏笔与台账一致 3.人物性格一致 4.不违反规则.md 5.本批章节间无矛盾。\n\n` +
						`先把统一检查报告写入 ${ROOT}/元数据/检查报告/统一-第${ch(n)}章.md, 再返回。\n输出: 通过 / 有冲突(附问题清单)`,
					{
						label: `统一检查:${ch(n)}`,
						phase: "统一检查",
							agentType: "novelist:continuity-auditor",
					},
				),
		),
	);
	const conflicts = [];
	results.forEach((r, i) => {
		if (r && r.includes("冲突")) conflicts.push(chapterNums[i]);
	});
	if (conflicts.length)
		log(`⚠️ 统一检查发现冲突: 第${conflicts.map(ch).join(", ")}章`);
	else log(`✅ 统一检查全部通过`);
	return { conflicts, results };
}

// ===== 主流程 =====
log(
	`流水线启动: 第${ch(START)}-${ch(END)}章, root=${ROOT}, 每批${BATCH_SIZE}章`,
);
const allResults = [];

for (let batchStart = START; batchStart <= END; batchStart += BATCH_SIZE) {
	const batchEnd = Math.min(batchStart + BATCH_SIZE - 1, END);
	const batchId = `${ch(batchStart)}-${ch(batchEnd)}`;
	log(`\n===== 批次 ${batchId} =====`);

	// Phase 1: 大纲(串行)
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
	await updateWorldview(batchStart, batchEnd);
	await preCheck(batchStart, batchEnd);

	// Phase 2: 逐章严格串行 —— 🔴 前一章定稿后才写下一章
	// (小说章节强依赖前文: 第N+1章 write 需要第N章已定稿的人物关系/伏笔/状态, 不能基于草稿开写)
	for (const n of chapterNums) {
		const info = chapters[n];
		// 1) 写正文
		log(`第${ch(n)}章 Writer 开始`);
		await writer(n, info);

		// 2) 收尾链 + fix 循环(每章自己跑完才算数)
		let checkResult,
			humanResult,
			proofResult,
			attempts = 0;
		while (true) {
			checkResult = await checker(n, info.title); // 一致性
			humanResult = await humanizer(n, info.title); // 去AI味
			proofResult = await proofer(n, info.title); // 校对
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
			if (passed || attempts >= MAX_FIX_ATTEMPTS) {
				if (!passed)
					log(
						`⚠️ 第${ch(n)}章 超重试上限(${MAX_FIX_ATTEMPTS}), 标记需复审`,
					);
				break;
			}
			log(`第${ch(n)}章 分数不足, 执行 fix(第${attempts + 1}次)`);
			await fixer(n, info.title, checkResult, proofResult, humanResult);
			attempts++;
		}

		// 3) 定稿(更新索引+进度) —— 🔴 定稿完成才进下一章
		const r = await finalizer(
			n,
			info.title,
			checkResult,
			proofResult,
			humanResult,
		);
		allResults.push(r);
		log(
			`✅ 第${ch(n)}章「${info.title}」${r.passed ? "定稿" : "需复审"} (${r.total}分) → 进入下一章`,
		);
	}
	log(`批次 ${batchId} 逐章串行完成`);

	// Phase 3: 后置(统一检查)
	await unifiedCheck(chapterNums, chapters);
}

// 汇总
const passed = allResults.filter((r) => r.passed);
const failed = allResults.filter((r) => !r.passed);
log(`\n===== 流水线完成 =====`);
log(`定稿: ${passed.length}章 | 需复审: ${failed.length}章`);
if (failed.length)
	log(
		`复审章节: ${failed.map((r) => `第${r.chapter}章(${r.total}分)`).join(", ")}`,
	);

return { results: allResults, passed: passed.length, failed: failed.length };
