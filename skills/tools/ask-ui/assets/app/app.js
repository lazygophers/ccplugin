import * as viewState from '/view-state.js';
import { answersForRound, displayAnswer, selectionCount } from '/view-state.js';

const app = document.querySelector('#app');
const toast = document.querySelector('#toast');

const SUPPLEMENTARY_TEXT_MAX_LENGTH = 2000;
const THEME_STORAGE_KEY = 'ask-ui-theme';
const sessionId = decodeURIComponent(location.pathname.split('/').filter(Boolean).at(-1) || '');
const token = new URLSearchParams(location.search).get('token') || '';

let bundle = null;
let activeRoundNumber = null;
let focusedQuestionId = null;
let pendingAnswers = [];
let answeredCountElement = null;
let progressCellsElement = null;
let railNavElement = null;
let lastUpdatedAt = null;
let submitting = false;
let submissionConfirmationTimer = null;
let submissionConfirmationInterval = null;
let lastVisibilitySignature = '';

function element(tag, className = '', text = '') {
  const value = document.createElement(tag);
  if (className) value.className = className;
  if (text !== '') value.textContent = text;
  return value;
}

const MERMAID_BLOCK = /^[ \t]*```mermaid[ \t]*\r?\n([\s\S]*?)^[ \t]*```[ \t]*$/gm;

// 富文本的一组底板配色 token，定义见 fallback.css 的 .rich-text。
const RICH_TOKENS = [
  '--rich-bg',
  '--rich-fg',
  '--rich-muted',
  '--rich-accent',
  '--rich-accent-fg',
  '--rich-accent-2',
  '--rich-accent-2-fg',
];

const vendorLoaders = new Map();
let diagramSequence = 0;
const pendingRichText = new Set();

// 首屏要滚到第一道未答题，而正文和图表是异步渲染的：不等它们渲染完，卡片高度
// 还在变，刚滚到的位置立刻就偏掉了。
function trackRichText(promise) {
  pendingRichText.add(promise);
  promise.finally(() => pendingRichText.delete(promise));
  return promise;
}

async function richTextSettled() {
  while (pendingRichText.size) {
    await Promise.allSettled([...pendingRichText]);
  }
}

function loadVendor(name, globalName) {
  if (!vendorLoaders.has(name)) {
    vendorLoaders.set(name, new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = `/vendor/${name}.min.js`;
      script.onload = () => resolve(globalThis[globalName]);
      script.onerror = () => {
        script.remove();
        reject(new Error(`${name} 组件加载失败，刷新页面可重试`));
      };
      document.head.append(script);
    // 失败的 promise 不能留下来，否则一次网络抖动会让这一页永远加载不出。
    }).catch((error) => {
      vendorLoaders.delete(name);
      throw error;
    }));
  }
  return vendorLoaders.get(name);
}

function loadMermaid() {
  return loadVendor('mermaid', 'mermaid');
}

async function loadMarkdown() {
  const [marked, purify] = await Promise.all([
    loadVendor('marked', 'marked'),
    loadVendor('purify', 'DOMPurify'),
  ]);
  return { marked, purify };
}

// 图表用它所在底板的配色，不用全局 token：黄色左栏里的图必须是黄色系的，
// 否则一块 surface 色的图钉在黄底上，整页就散了。明暗主题同样跟着换。
function mermaidTheme(host) {
  const styles = getComputedStyle(host);
  const read = (name) => styles.getPropertyValue(name).trim();
  const background = read('--rich-bg');
  const line = read('--rich-fg');
  const muted = read('--rich-muted');
  const mutedText = read('--ink');
  const accent = read('--rich-accent');
  const accentText = read('--rich-accent-fg');
  const accent2 = read('--rich-accent-2');
  const accent2Text = read('--rich-accent-2-fg');
  return {
    theme: 'base',
    fontFamily: styles.fontFamily,
    themeVariables: {
      background,
      primaryColor: accent,
      primaryTextColor: accentText,
      primaryBorderColor: line,
      secondaryColor: accent2,
      secondaryTextColor: accent2Text,
      secondaryBorderColor: line,
      tertiaryColor: muted,
      tertiaryTextColor: mutedText,
      tertiaryBorderColor: line,
      lineColor: line,
      textColor: line,
      mainBkg: accent,
      nodeBorder: line,
      clusterBkg: muted,
      clusterBorder: line,
      titleColor: line,
      edgeLabelBackground: background,
      actorBkg: accent,
      actorBorder: line,
      actorTextColor: accentText,
      signalColor: line,
      signalTextColor: line,
      labelBoxBkgColor: accent2,
      labelBoxBorderColor: line,
      labelTextColor: accent2Text,
      noteBkgColor: muted,
      noteBorderColor: line,
      noteTextColor: mutedText,
    },
    // themeVariables 管不到线宽，也管不到连线标签的文字色——后者在暗色主题下
    // 会留在默认深色上，压在深色背景里看不见。
    themeCSS: `
      .node rect, .node circle, .node ellipse, .node polygon, .node path,
      .cluster rect, .actor, .labelBox, .note {
        stroke-width: 3px;
      }
      .edgePath .path, .flowchart-link, .messageLine0, .messageLine1 {
        stroke-width: 2.5px;
      }
      .edgeLabel, .edgeLabel p, .edgeLabel span, .edgeLabel foreignObject div {
        color: ${line};
        background: ${background};
      }
      .edgeLabel rect {
        fill: ${background};
      }
    `,
  };
}

async function renderDiagram(host, code) {
  diagramSequence += 1;
  const id = `ask-ui-diagram-${diagramSequence}`;
  try {
    const mermaid = await loadMermaid();
    mermaid.initialize({ startOnLoad: false, securityLevel: 'strict', ...mermaidTheme(host) });
    const { svg } = await mermaid.render(id, code);
    host.innerHTML = svg;
    host.dataset.state = 'ready';
    makePreviewable(host, '图表');
  } catch (error) {
    // 渲染不出来时把原始图表源码亮出来，比留一个空框有用。
    host.replaceChildren();
    host.dataset.state = 'failed';
    host.append(element('p', 'diagram-error', `图表无法渲染：${error.message}`));
    host.append(element('pre', 'diagram-source', code));
  }
}

let markdownWarned = false;
let highlightWarned = false;

// 代码块按 ```lang 标注的语言上色。hljs 只认自己注册过的语言，标注是别名或
// 没标注的就保持素色，不猜。
async function highlightCode(host) {
  const blocks = [...host.querySelectorAll('pre code[class*="language-"]')];
  if (!blocks.length) return;
  try {
    const hljs = await loadVendor('highlight', 'hljs');
    for (const block of blocks) {
      const language = block.className.match(/language-([\w+#.-]+)/)[1];
      if (!hljs.getLanguage(language)) continue;
      block.innerHTML = hljs.highlight(block.textContent, { language }).value;
      block.classList.add('hljs');
    }
  } catch {
    // 高亮组件下载不到时代码块保持素色，正文和答题都不受影响。
    if (highlightWarned) return;
    highlightWarned = true;
    showToast('代码高亮组件加载失败，代码块按素色显示');
  }
}

async function renderProse(host, source) {
  try {
    const { marked, purify } = await loadMarkdown();
    // marked 只负责结构，DOMPurify 负责把脚本和事件属性剥干净，两步都不能省。
    host.innerHTML = purify.sanitize(marked.parse(source, { gfm: true, breaks: true }));
    host.dataset.state = 'ready';
    for (const table of host.querySelectorAll('table')) {
      const frame = element('div', 'table-frame');
      table.replaceWith(frame);
      frame.append(table);
      makePreviewable(frame, '表格');
    }
    highlightCode(host);
  } catch {
    // 组件下载不到时保持纯文本：内容照样读得懂，答题不受影响。
    host.dataset.state = 'plain';
    if (markdownWarned) return;
    markdownWarned = true;
    showToast('Markdown 组件加载失败，正文按纯文本显示');
  }
}

// 文本里的 ```mermaid 块渲染成图，其余部分按 Markdown 渲染再净化，绝不直出原始 HTML。
// diagrams 为 false 时整段只走 Markdown——选项卡片一人一张图会挤得没法比较。
function appendRichText(container, text, { diagrams = true } = {}) {
  const value = text || '';
  const host = element('div', 'rich-text');
  container.append(host);

  const addProse = (prose) => {
    const trimmed = prose.trim();
    if (!trimmed) return;
    // Markdown 组件到位前先按纯文本显示，加载完再整体替换。
    const block = element('div', 'prose', trimmed);
    block.dataset.state = 'plain';
    host.append(block);
    trackRichText(renderProse(block, trimmed));
  };

  if (!diagrams) {
    addProse(value);
    return host;
  }

  MERMAID_BLOCK.lastIndex = 0;
  let cursor = 0;
  let match = MERMAID_BLOCK.exec(value);
  while (match) {
    addProse(value.slice(cursor, match.index));
    const diagram = element('div', 'diagram');
    diagram.dataset.state = 'loading';
    diagram.append(element('p', 'diagram-loading', '图表加载中…'));
    host.append(diagram);
    trackRichText(renderDiagram(diagram, match[1].trim()));
    cursor = match.index + match[0].length;
    match = MERMAID_BLOCK.exec(value);
  }
  addProse(value.slice(cursor));
  return host;
}

// 图表和表格常常比题卡宽。点开进全屏预览，滚轮缩放、拖拽平移。
function makePreviewable(host, label) {
  host.classList.add('previewable');
  host.tabIndex = 0;
  host.setAttribute('role', 'button');
  host.setAttribute('aria-label', `放大查看${label}`);
  host.title = `点击放大查看${label}`;
  host.append(element('span', 'preview-hint', '点击放大'));
  host.addEventListener('click', () => openPreview(host, label));
  host.addEventListener('keydown', (event) => {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    event.preventDefault();
    openPreview(host, label);
  });
}

function openPreview(host, label) {
  const overlay = element('div', 'preview-overlay');
  const stage = element('div', 'preview-stage');
  const canvas = element('div', 'preview-canvas');
  const toolbar = element('div', 'preview-toolbar');
  const readout = element('span', 'preview-readout');

  overlay.setAttribute('role', 'dialog');
  overlay.setAttribute('aria-modal', 'true');
  overlay.setAttribute('aria-label', `${label}预览`);
  // 克隆体离开了原来的底板，配色 token 一并带过来，预览里的图表表格才不变色。
  const hostStyles = getComputedStyle(host);
  for (const token of RICH_TOKENS) {
    canvas.style.setProperty(token, hostStyles.getPropertyValue(token));
  }
  // append 会把节点从克隆体上摘走，先固化成数组再遍历，否则会漏掉一半。
  for (const node of [...host.cloneNode(true).childNodes]) {
    if (node.classList?.contains('preview-hint')) continue;
    canvas.append(node);
  }

  // mermaid 的 svg 带 width="100%"，脱离原容器后量不出宽度。按 viewBox 写死尺寸，
  // 舞台才有东西可以量、可以缩放。
  for (const svg of canvas.querySelectorAll('svg')) {
    const box = svg.viewBox?.baseVal;
    if (!box?.width) continue;
    svg.style.width = `${box.width}px`;
    svg.style.height = `${box.height}px`;
  }

  // 图表按原始尺寸渲染，多半比屏幕小得多。打开预览时先缩放到铺满舞台，
  // 留一圈边距，再由用户滚轮微调。
  const fitScale = () => {
    const margin = 48;
    const width = canvas.offsetWidth;
    const height = canvas.offsetHeight;
    if (!width || !height) return 1;
    const ratio = Math.min(
      (stage.clientWidth - margin) / width,
      (stage.clientHeight - margin) / height,
    );
    return Math.min(8, Math.max(0.2, ratio));
  };

  let scale = 1;
  let offsetX = 0;
  let offsetY = 0;
  const apply = () => {
    canvas.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${scale})`;
    readout.textContent = `${Math.round(scale * 100)}%`;
  };
  const zoomTo = (next, anchorX = 0, anchorY = 0) => {
    const clamped = Math.min(8, Math.max(0.2, next));
    const ratio = clamped / scale;
    offsetX = anchorX - (anchorX - offsetX) * ratio;
    offsetY = anchorY - (anchorY - offsetY) * ratio;
    scale = clamped;
    apply();
  };

  const close = () => {
    overlay.remove();
    document.removeEventListener('keydown', onKeydown);
    host.focus();
  };
  function onKeydown(event) {
    if (event.key === 'Escape') close();
  }

  const button = (text, onClick, buttonLabel) => {
    const control = element('button', 'preview-button', text);
    control.type = 'button';
    control.setAttribute('aria-label', buttonLabel);
    control.addEventListener('click', (event) => {
      event.stopPropagation();
      onClick();
    });
    return control;
  };
  toolbar.append(
    button('－', () => zoomTo(scale / 1.25), '缩小'),
    readout,
    button('＋', () => zoomTo(scale * 1.25), '放大'),
    button('重置', () => { scale = fitScale(); offsetX = 0; offsetY = 0; apply(); }, '重置缩放'),
    button('关闭', close, '关闭预览'),
  );

  stage.addEventListener('wheel', (event) => {
    event.preventDefault();
    const rect = stage.getBoundingClientRect();
    zoomTo(
      scale * (event.deltaY < 0 ? 1.12 : 1 / 1.12),
      event.clientX - rect.left - rect.width / 2,
      event.clientY - rect.top - rect.height / 2,
    );
  }, { passive: false });

  let dragging = null;
  stage.addEventListener('pointerdown', (event) => {
    dragging = { pointerId: event.pointerId, x: event.clientX - offsetX, y: event.clientY - offsetY };
    stage.setPointerCapture(event.pointerId);
    stage.classList.add('dragging');
  });
  stage.addEventListener('pointermove', (event) => {
    if (dragging?.pointerId !== event.pointerId) return;
    offsetX = event.clientX - dragging.x;
    offsetY = event.clientY - dragging.y;
    apply();
  });
  const endDrag = (event) => {
    if (dragging?.pointerId !== event.pointerId) return;
    dragging = null;
    stage.classList.remove('dragging');
  };
  stage.addEventListener('pointerup', endDrag);
  stage.addEventListener('pointercancel', endDrag);

  overlay.addEventListener('click', (event) => {
    if (event.target === overlay) close();
  });
  document.addEventListener('keydown', onKeydown);

  stage.append(canvas);
  overlay.append(stage, toolbar);
  document.body.append(overlay);
  scale = fitScale();
  apply();
  toolbar.querySelector('.preview-button')?.focus();
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `请求失败：${response.status}`);
  return data;
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2200);
}

function currentRound() {
  return bundle.rounds.find((round) => round.roundNumber === activeRoundNumber);
}

function currentTheme() {
  return document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light';
}

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  document.querySelector('meta[name="color-scheme"]')?.setAttribute('content', theme);
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // The visual theme still works when browser storage is unavailable.
  }
  if (bundle) render();
}

// 草稿按轮次留在内存里：切去看上一轮再切回来，这一轮已经填的东西必须还在。
const draftsByRound = new Map();

function draftsFor(round) {
  if (!draftsByRound.has(round.roundNumber)) {
    draftsByRound.set(round.roundNumber, answersForRound(round));
  }
  return draftsByRound.get(round.roundNumber);
}

function answerFor(questionId) {
  let answer = pendingAnswers.find((item) => item.questionId === questionId);
  if (!answer) {
    answer = {
      questionId,
      selectedOptionIds: [],
      customText: '',
      supplementaryText: '',
    };
    pendingAnswers.push(answer);
  }
  return answer;
}

// 下面几个只是把模块级的草稿与当前题绑上去，推导本身在 view-state.js 里，
// 页面这一侧不再重复实现一遍。
function visibleQuestionsOf(round, editable) {
  return viewState.visibleQuestionsOf(round, editable, pendingAnswers);
}

function visibilitySignature(round, editable) {
  return viewState.visibilitySignature(round, editable, pendingAnswers);
}

function isAnswered(question, editable, submittedAnswers) {
  return viewState.isAnswered(question, editable, submittedAnswers, pendingAnswers);
}

function answeredQuestionCount(round, editable) {
  return viewState.answeredQuestionCount(round, editable, pendingAnswers);
}

function questionState(question, editable, submittedAnswers) {
  return viewState.questionState(question, editable, submittedAnswers, pendingAnswers, focusedQuestionId);
}

function firstUnansweredId(round, editable) {
  return viewState.firstUnansweredId(round, editable, pendingAnswers);
}

function roundEditable(round) {
  return round.status === 'waiting_for_user' && bundle.session.status === 'active';
}

function scrollToQuestion(questionId, behavior = 'smooth') {
  document
    .querySelector(`.question-card[data-question-id="${CSS.escape(questionId)}"]`)
    ?.scrollIntoView({ block: 'center', behavior });
}

// 条件题出现或消失时只增删这几张卡，不重建整页：整页重建会打断正在输入的
// 那一行、丢掉滚动位置，还要把已经渲染好的图表和代码高亮全部重做一遍。
function syncVisibleQuestions(round, editable) {
  lastVisibilitySignature = visibilitySignature(round, editable);
  const visible = visibleQuestionsOf(round, editable);
  const visibleIds = new Set(visible.map((question) => question.id));
  const scroll = document.querySelector('.question-scroll');
  if (!scroll) return;
  for (const card of [...scroll.children]) {
    if (!visibleIds.has(card.dataset.questionId)) card.remove();
  }
  const cards = new Map([...scroll.children].map((card) => [card.dataset.questionId, card]));
  visible.forEach((question, index) => {
    const card = cards.get(question.id)
      || renderQuestion(question, index, editable, round.answers?.answers);
    // 序号是按可见顺序排的，分支一变就得跟着改。
    const number = card.querySelector('.question-number');
    if (number) number.textContent = String(index + 1).padStart(2, '0');
    if (scroll.children[index] !== card) scroll.insertBefore(card, scroll.children[index] || null);
  });
  if (railNavElement) fillRailNav(railNavElement, round, editable, visible);
  if (progressCellsElement) {
    while (progressCellsElement.children.length > visible.length) {
      progressCellsElement.lastElementChild.remove();
    }
    while (progressCellsElement.children.length < visible.length) {
      progressCellsElement.append(element('span', 'progress-cell'));
    }
  }
}

// 单选选完就把用户送到下一道没答的题，不用自己回去找。
function advanceFrom(questionId) {
  const round = currentRound();
  const editable = roundEditable(round);
  const pending = viewState.nextUnansweredIdFrom(round, editable, pendingAnswers, questionId);
  if (!pending) return;
  focusedQuestionId = pending;
  if (railNavElement) refreshRailStates(round, editable);
  refreshCardStates(round, editable);
  scrollToQuestion(pending);
}

async function alignToFocusedQuestion() {
  const round = currentRound();
  if (!round || !focusedQuestionId || !roundEditable(round)) return;
  const visible = visibleQuestionsOf(round, true);
  // 第一题就是待答题时不动，页面本来就从它开始。
  if (visible[0]?.id === focusedQuestionId) return;
  await richTextSettled();
  scrollToQuestion(focusedQuestionId, 'auto');
}

function refreshProgress() {
  const round = currentRound();
  if (!round) return;
  const editable = roundEditable(round);
  if (visibilitySignature(round, editable) !== lastVisibilitySignature) {
    syncVisibleQuestions(round, editable);
  }
  const visible = visibleQuestionsOf(round, editable);
  const answered = answeredQuestionCount(round, editable);
  if (answeredCountElement) {
    answeredCountElement.textContent = `已答 ${answered} / ${visible.length}`;
  }
  if (progressCellsElement) {
    // 每个格子对应同序号的那一题，跳答时空格留在原位，不做左对齐填充。
    [...progressCellsElement.children].forEach((cell, index) => {
      const question = visible[index];
      cell.classList.toggle('on', Boolean(question) && isAnswered(question, editable, round.answers?.answers));
    });
  }
  if (editable && focusedQuestionId) {
    const focused = round.questions.questions.find((item) => item.id === focusedQuestionId);
    if (focused && isAnswered(focused, editable, round.answers?.answers)) {
      focusedQuestionId = firstUnansweredId(round, editable);
    }
  }
  if (railNavElement) refreshRailStates(round, editable);
  refreshCardStates(round, editable);
}

function refreshRailStates(round, editable) {
  for (const button of railNavElement.querySelectorAll('.nav-button')) {
    const question = round.questions.questions.find((item) => item.id === button.dataset.questionId);
    if (!question) continue;
    const state = questionState(question, editable, round.answers?.answers);
    button.dataset.state = state;
    const status = button.querySelector('.st');
    if (status) status.textContent = { done: '已答', current: '当前', todo: '未答' }[state];
  }
  const counter = railNavElement.parentElement?.querySelector('.rail-count');
  if (counter) {
    counter.textContent = `${answeredQuestionCount(round, editable)} / ${visibleQuestionsOf(round, editable).length}`;
  }
}

function refreshCardStates(round, editable) {
  for (const card of document.querySelectorAll('.question-card')) {
    const question = round.questions.questions.find((item) => item.id === card.dataset.questionId);
    if (!question) continue;
    card.dataset.state = questionState(question, editable, round.answers?.answers);
    card.querySelector('.question-flag')?.remove();
    if (card.dataset.state === 'current') {
      card.prepend(element('span', 'question-flag', '现在轮到这一题'));
    }
  }
}

function badge(text, variant = '') {
  return element('span', `badge${variant ? ` ${variant}` : ''}`, text);
}

function makeThemeButton(theme, label) {
  const button = element('button', 'theme-button', label);
  button.type = 'button';
  button.setAttribute('aria-pressed', String(currentTheme() === theme));
  button.addEventListener('click', () => setTheme(theme));
  return button;
}

function projectName() {
  if (bundle.session.projectName) return bundle.session.projectName;
  const workspace = bundle.session.workspace || '';
  return workspace.split('/').filter(Boolean).at(-1) || 'ask-ui';
}

function renderHeader(container) {
  document.title = `${projectName()}-Ask UI`;
  const header = element('header', 'session-header');
  for (const variant of ['d1', 'd2', 'd3']) {
    const deco = element('span', `header-deco ${variant}`);
    deco.setAttribute('aria-hidden', 'true');
    header.append(deco);
  }

  const copy = element('div', 'header-copy');
  copy.append(element('span', 'project-badge', bundle.session.title));
  copy.append(element('h1', 'session-title', projectName()));
  copy.append(element(
    'p',
    'session-summary',
    bundle.session.summary || 'Agent 已暂停，正在等你的答复。',
  ));

  const tools = element('div', 'header-tools');
  tools.append(renderTabs());
  const themes = element('div', 'theme-toggle');
  themes.setAttribute('aria-label', '页面主题');
  themes.append(makeThemeButton(currentTheme() === 'dark' ? 'light' : 'dark', currentTheme() === 'dark' ? '切换浅色主题' : '切换暗色主题'));
  tools.append(themes);

  header.append(copy, tools);
  container.append(header);
}

function renderTabs() {
  const tabs = element('nav', 'round-tabs');
  tabs.setAttribute('role', 'tablist');
  tabs.setAttribute('aria-label', '问题轮次');
  for (const round of bundle.rounds) {
    const completed = ['submitted', 'processed'].includes(round.status);
    const label = completed
      ? `第 ${round.roundNumber} 轮 · 已提交`
      : `第 ${round.roundNumber} 轮 · 进行中`;
    const button = element('button', 'round-tab', label);
    button.type = 'button';
    button.setAttribute('role', 'tab');
    button.setAttribute('aria-selected', String(round.roundNumber === activeRoundNumber));
    button.dataset.locked = String(completed);
    button.addEventListener('click', () => {
      activeRoundNumber = round.roundNumber;
      pendingAnswers = draftsFor(round);
      focusedQuestionId = firstUnansweredId(round, roundEditable(round));
      render();
      alignToFocusedQuestion();
    });
    tabs.append(button);
  }
  return tabs;
}

function renderRail(container) {
  const round = currentRound();
  if (!round) return;
  const editable = roundEditable(round);
  const rail = element('aside', 'rail');
  rail.setAttribute('aria-label', '本轮问题导航');

  if (bundle.session.background) {
    const context = element('div', 'rail-block context');
    context.append(element('h2', '', '本次背景'));
    appendRichText(context, bundle.session.background);
    rail.append(context);
  }

  const roundBlock = element('div', 'rail-block round');
  roundBlock.append(element('span', 'kicker', `第 ${round.roundNumber} 轮`));
  roundBlock.append(element('h2', '', round.title || '需求确认'));
  if (round.purpose) roundBlock.append(element('p', '', round.purpose));
  rail.append(roundBlock);

  const visible = visibleQuestionsOf(round, editable);
  const head = element('div', 'rail-head');
  head.append(element('span', '', '队列里还有谁在等'));
  head.append(element(
    'span',
    'rail-count',
    `${answeredQuestionCount(round, editable)} / ${visible.length}`,
  ));
  rail.append(head);

  const nav = element('ul', 'rail-nav');
  railNavElement = nav;
  fillRailNav(nav, round, editable, visible);
  rail.append(nav);
  container.append(rail);
}

function fillRailNav(nav, round, editable, visible) {
  nav.replaceChildren();
  visible.forEach((question, index) => {
    const item = element('li');
    const state = questionState(question, editable, round.answers?.answers);
    const button = element('button', 'nav-button');
    button.type = 'button';
    button.dataset.questionId = question.id;
    button.dataset.state = state;
    button.append(element('span', 'n', String(index + 1).padStart(2, '0')));
    // 导航是索引不是正文：多行标题只取第一行，免得把左栏撑乱。
    button.append(element('span', 't', question.title.split('\n')[0]));
    button.append(element('span', 'st', { done: '已答', current: '当前', todo: '未答' }[state]));
    button.addEventListener('click', () => {
      if (editable) focusedQuestionId = question.id;
      scrollToQuestion(question.id);
      refreshRailStates(round, editable);
      refreshCardStates(round, editable);
    });
    item.append(button);
    nav.append(item);
  });
}

function renderChoiceQuestion(card, question, answer, editable) {
  const list = element('div', 'option-list');
  question.options.forEach((option, optionIndex) => {
    const optionCard = element('label', 'option-card');
    const input = document.createElement('input');
    input.className = 'option-selector';
    input.type = question.type === 'single' ? 'radio' : 'checkbox';
    input.name = `question-${question.id}`;
    input.value = option.id;
    input.checked = answer.selectedOptionIds.includes(option.id);
    input.disabled = !editable;

    // 单选也要能反悔：再点一次选中项就清空。radio 点自己不触发 change，
    // 所以按下时先记住原状态，click 里据此撤销。
    let checkedBeforeClick = false;
    const rememberState = () => { checkedBeforeClick = input.checked; };
    input.addEventListener('pointerdown', rememberState);
    input.addEventListener('keydown', rememberState);
    optionCard.addEventListener('pointerdown', rememberState);
    input.addEventListener('click', () => {
      if (question.type !== 'single' || !checkedBeforeClick) return;
      input.checked = false;
      answer.selectedOptionIds = [];
      refreshProgress();
    });

    input.addEventListener('change', () => {
      if (question.type === 'single') {
        answer.selectedOptionIds = input.checked ? [option.id] : [];
      } else if (input.checked) {
        answer.selectedOptionIds = [...new Set([...answer.selectedOptionIds, option.id])];
      } else {
        answer.selectedOptionIds = answer.selectedOptionIds.filter((id) => id !== option.id);
      }
      refreshProgress();
      // 多选和文本题不自动前进：用户还要继续选、继续写。
      if (question.type === 'single' && input.checked) advanceFrom(question.id);
    });

    const content = element('span', 'option-content');
    const title = element('span', 'option-label');
    title.append(element('span', '', option.text));
    if (option.recommended) title.append(badge('推荐', 'recommended'));
    content.append(title);
    if (option.description) {
      const description = element('span', 'option-description');
      appendRichText(description, option.description, { diagrams: false });
      content.append(description);
    }
    if (option.recommended && option.reason) {
      content.append(element('span', 'option-reason', `推荐理由：${option.reason}`));
    }
    // 序号由渲染顺序自动生成，QuestionSet 不需要也不应该传。
    optionCard.append(input, element('span', 'option-number', String(optionIndex + 1)), content);
    list.append(optionCard);
  });

  card.append(list);
}

function renderTextQuestion(card, question, answer, editable) {
  const input = document.createElement(question.multiline === false ? 'input' : 'textarea');
  const counter = element('span', 'text-counter');
  input.className = 'text-input';
  input.dataset.questionId = question.id;
  input.dataset.answerField = 'text';
  if (input.tagName === 'TEXTAREA') input.rows = 3;
  if (question.recommendedDraft) input.placeholder = `建议：${question.recommendedDraft}`;
  input.maxLength = question.maxLength || 4000;
  input.value = answer.customText || '';
  input.disabled = !editable;
  const updateCounter = () => {
    counter.textContent = `${input.value.length}/${input.maxLength}`;
  };
  input.addEventListener('input', () => {
    answer.customText = input.value;
    updateCounter();
    refreshProgress();
  });
  updateCounter();
  card.append(input, counter);
}

function renderSupplementaryInput(card, question, answer) {
  const field = element('div', 'supplement-field');
  const trigger = element('button', 'supplement-trigger');
  const triggerIcon = element('span', 'supplement-trigger-icon', '＋');
  const triggerText = element('span', 'supplement-trigger-text');
  const triggerBadge = element('span', 'supplement-badge');
  const panel = element('div', 'supplement-panel');
  const heading = element('div', 'supplement-heading');
  const inputId = `supplement-${question.id}`;
  const helperId = `${inputId}-helper`;
  const panelId = `${inputId}-panel`;
  const label = element('label', 'supplement-label', '补充说明');
  const optional = element('span', 'supplement-optional', '选填');
  const counter = element('span', 'supplement-counter');
  const helper = element(
    'p',
    'supplement-helper',
    '选项里没有合适的？在这里直接写你的答案、限制条件或偏好，Agent 会一并读到。',
  );
  const input = document.createElement('textarea');

  trigger.type = 'button';
  trigger.setAttribute('aria-controls', panelId);
  trigger.append(triggerIcon, triggerText, triggerBadge);
  panel.id = panelId;
  label.htmlFor = inputId;
  label.append(' ', optional);
  input.id = inputId;
  input.className = 'supplement-input';
  input.dataset.questionId = question.id;
  input.dataset.answerField = 'supplement';
  input.rows = 2;
  input.maxLength = SUPPLEMENTARY_TEXT_MAX_LENGTH;
  input.placeholder = '例如：都不合适，我想要按项目分组；或：仅适用于首期版本';
  input.value = answer.supplementaryText || '';
  input.setAttribute('aria-describedby', helperId);
  helper.id = helperId;

  const setExpanded = (expanded, focusInput = false) => {
    const filled = Boolean(answer.supplementaryText?.trim());
    trigger.setAttribute('aria-expanded', String(expanded));
    field.classList.toggle('has-content', filled);
    triggerIcon.textContent = expanded ? '－' : '＋';
    triggerText.textContent = filled
      ? (expanded ? '收起补充说明' : '编辑补充说明')
      : (expanded ? '收起补充说明' : '添加补充说明');
    triggerBadge.textContent = filled ? '已填写' : '';
    panel.hidden = !expanded;
    if (expanded && focusInput) input.focus();
  };

  const updateCounter = () => {
    counter.textContent = `${input.value.length}/${input.maxLength}`;
  };
  input.addEventListener('input', () => {
    answer.supplementaryText = input.value;
    updateCounter();
    setExpanded(true);
    refreshProgress();
  });
  trigger.addEventListener('click', () => {
    const expanded = trigger.getAttribute('aria-expanded') === 'true';
    setExpanded(!expanded, !expanded);
  });
  updateCounter();
  heading.append(label, counter);
  panel.append(heading, input, helper);
  field.append(trigger, panel);
  setExpanded(Boolean(answer.supplementaryText?.trim()));
  card.append(field);
}

function showSubmissionConfirmation() {
  document.querySelector('.submission-overlay')?.remove();
  clearTimeout(submissionConfirmationTimer);
  clearInterval(submissionConfirmationInterval);

  const overlay = element('div', 'submission-overlay');
  const card = element('div', 'submission-confirmation');
  const title = element('strong', 'submission-confirmation-title', '已提交给 Agent');
  const message = element('p', 'submission-confirmation-message', '答案已安全保存，Agent 正在继续工作。');
  const countdown = element('span', 'submission-confirmation-countdown', '此页面将在 5 秒后自动关闭');
  let remaining = 5;

  overlay.setAttribute('role', 'dialog');
  overlay.setAttribute('aria-live', 'assertive');
  overlay.setAttribute('aria-atomic', 'true');
  card.append(title, message, countdown);
  overlay.append(card);
  document.body.append(overlay);

  submissionConfirmationInterval = setInterval(() => {
    remaining -= 1;
    if (remaining > 0) countdown.textContent = `此页面将在 ${remaining} 秒后自动关闭`;
  }, 1000);
  submissionConfirmationTimer = setTimeout(() => {
    clearInterval(submissionConfirmationInterval);
    window.close();
    // 浏览器只允许关闭脚本自己打开的标签页，其余情况停在终态卡上。
    countdown.textContent = '可以关闭这个标签页了';
  }, 5000);
}

function questionFlags(question) {
  const flags = element('div', 'question-flags');
  flags.append(badge(question.required ? '必填' : '选填', question.required ? 'required' : 'optional'));
  const typeLabel = { single: '单选', multiple: '多选', text: '文本' }[question.type];
  flags.append(badge(typeLabel, question.type === 'multiple' ? 'multi' : ''));
  return flags;
}

function renderQuestion(question, index, editable, submittedAnswers) {
  const card = element('section', 'question-card');
  const state = questionState(question, editable, submittedAnswers);
  card.dataset.questionId = question.id;
  card.dataset.state = state;
  if (state === 'current') {
    card.append(element('span', 'question-flag', '现在轮到这一题'));
  }

  const header = element('div', 'question-header');
  header.append(element('span', 'question-number', String(index + 1).padStart(2, '0')));
  const copy = element('div', 'question-copy');
  const body = element('div', 'question-body');
  appendRichText(body, question.text);
  copy.append(body);
  header.append(copy, questionFlags(question));
  card.append(header);

  if (question.background) {
    const background = element('div', 'question-background');
    // 正文可能以表格或图表开头，标签独立成块，不再往第一段里插。
    background.append(element('b', 'background-lead', '背景 ·'));
    appendRichText(background, question.background);
    card.append(background);
  }

  const answer = editable
    ? answerFor(question.id)
    : submittedAnswers?.find((item) => item.questionId === question.id);
  if (editable) {
    if (question.type === 'text') {
      renderTextQuestion(card, question, answer, true);
      if (question.recommendationReason) {
        card.append(element('p', 'recommendation', `推荐理由：${question.recommendationReason}`));
      }
    } else {
      renderChoiceQuestion(card, question, answer, true);
    }
    renderSupplementaryInput(card, question, answer);
  } else {
    card.append(element('div', 'history-answer', displayAnswer(question, answer)));
  }
  return card;
}

function clientValidation(round) {
  const errors = [];
  for (const question of visibleQuestionsOf(round, true)) {
    const answer = answerFor(question.id);
    const count = selectionCount(question, answer);
    const answeredBySupplement = Boolean(answer.supplementaryText?.trim());
    if (question.required && count === 0 && !answeredBySupplement) {
      errors.push(`请回答“${question.title}”`);
    }
    if (question.type === 'single' && count > 1) errors.push(`“${question.title}”只能选择一项`);
    if (question.type === 'multiple' && !(count === 0 && answeredBySupplement)) {
      if (count < question.minSelections) {
        errors.push(`“${question.title}”至少选择 ${question.minSelections} 项`);
      }
      if (count > question.maxSelections) {
        errors.push(`“${question.title}”最多选择 ${question.maxSelections} 项`);
      }
    }
  }
  return errors;
}

async function submitRound(round, submitButton) {
  const errors = clientValidation(round);
  if (errors.length) {
    showToast(errors[0]);
    return;
  }
  if (submitting) return;
  // 隐藏题的草稿只留在页面上供用户切回分支时复用，不进提交：Agent 读到的答案
  // 必须和用户屏幕上的表单一一对应。
  const visible = new Set(visibleQuestionsOf(round, true).map((question) => question.id));
  submitting = true;
  submitButton.disabled = true;
  submitButton.textContent = '正在提交…';
  try {
    await api(
      `/api/sessions/${encodeURIComponent(sessionId)}/rounds/${round.roundNumber}/answers`,
      {
        method: 'POST',
        body: JSON.stringify({
          submissionId: `submit-${crypto.randomUUID()}`,
          answers: pendingAnswers.filter((answer) => visible.has(answer.questionId)),
        }),
      },
    );
    showSubmissionConfirmation();
    // 提交后这一轮的答案以服务端存下的为准，草稿缓存留着会盖掉它。
    draftsByRound.delete(round.roundNumber);
    await loadBundle(true);
  } catch (error) {
    showToast(error.message);
  } finally {
    submitting = false;
    submitButton.disabled = false;
    submitButton.textContent = '提交本轮答案';
  }
}

function renderQuestions(container) {
  const round = currentRound();
  if (!round) return;
  const scroll = element('main', 'question-scroll');
  scroll.setAttribute('role', 'tabpanel');
  const editable = roundEditable(round);
  visibleQuestionsOf(round, editable).forEach((question, index) => {
    scroll.append(renderQuestion(question, index, editable, round.answers?.answers));
  });
  container.append(scroll);
}

function renderSubmitDock(container) {
  const round = currentRound();
  if (!round) return;
  const dock = element('footer', 'submit-dock');
  const editable = roundEditable(round);
  const directReturn = round.deliveryMode === 'direct';

  if (editable) {
    dock.append(element(
      'p',
      'submit-readme',
      directReturn
        ? '提交后 Agent 会立即用你的答案继续工作，本轮不可再修改。'
        : '提交后本轮变为只读，请回到 Agent 会话回复「已提交」继续。',
    ));
    const status = element('div', 'dock-status');
    progressCellsElement = element('div', 'progress-cells');
    for (let index = 0; index < visibleQuestionsOf(round, editable).length; index += 1) {
      progressCellsElement.append(element('span', 'progress-cell'));
    }
    answeredCountElement = element('span', 'answered-count');
    status.append(progressCellsElement, answeredCountElement);
    dock.append(status);

    const submit = element('button', 'btn-primary', '提交本轮答案');
    submit.type = 'button';
    submit.addEventListener('click', () => submitRound(round, submit));
    dock.append(submit);
    refreshProgress();
  } else {
    dock.append(element(
      'p',
      'submit-readme',
      round.status === 'submitted'
        ? (directReturn
            ? '答案已返回 Agent，可以回到会话查看后续处理。'
            : '本轮已提交，请回到 Agent 会话回复「已提交」。')
        : '本轮已处理，以上内容作为后续轮次的只读依据。',
    ));
    const status = element('div', 'dock-status');
    status.append(element(
      'span',
      'answered-count',
      `共 ${visibleQuestionsOf(round, editable).length} 题 · 只读`,
    ));
    dock.append(status);
  }
  container.append(dock);
}

function renderError(error) {
  app.replaceChildren();
  const panel = element('div', 'error-panel');
  panel.append(element('strong', '', 'Ask UI 无法加载'));
  panel.append(element('p', '', error.message));
  app.append(panel);
}

function render() {
  const round = currentRound();
  lastVisibilitySignature = round ? visibilitySignature(round, roundEditable(round)) : '';
  answeredCountElement = null;
  progressCellsElement = null;
  railNavElement = null;
  app.replaceChildren();
  renderHeader(app);
  const workspace = element('div', 'workspace');
  renderRail(workspace);
  renderQuestions(workspace);
  app.append(workspace);
  renderSubmitDock(app);
}

async function loadBundle(force = false) {
  const next = await api(`/api/sessions/${encodeURIComponent(sessionId)}`);
  const changed = force || next.session.updatedAt !== lastUpdatedAt;
  const previousMaxRound = bundle?.rounds?.length
    ? Math.max(...bundle.rounds.map((round) => round.roundNumber))
    : 0;
  bundle = next;
  lastUpdatedAt = next.session.updatedAt;
  const waiting = [...bundle.rounds].reverse().find((round) => round.status === 'waiting_for_user');
  const activeStillExists = bundle.rounds.some((round) => round.roundNumber === activeRoundNumber);
  const hasNewWaitingRound = waiting && waiting.roundNumber > previousMaxRound;
  if (!activeStillExists || force || hasNewWaitingRound) {
    activeRoundNumber = waiting?.roundNumber || bundle.rounds.at(-1)?.roundNumber || null;
    const round = currentRound();
    pendingAnswers = round ? draftsFor(round) : [];
    focusedQuestionId = round ? firstUnansweredId(round, roundEditable(round)) : null;
  }
  if (changed) render();
  // 首次打开和新一轮到达时把视口停在第一道待答题上；轮询中的普通刷新不动视口，
  // 那会把正在答题的人推走。
  if (force || hasNewWaitingRound) alignToFocusedQuestion();
}

// macOS 上 Home/End 在文本框里不移动光标，而是滚动页面。这里把它们接管成
// 行首/行尾，配合 Shift 扩选、配合 Cmd/Ctrl 跳到全文首尾。
document.addEventListener('keydown', (event) => {
  if (event.key !== 'Home' && event.key !== 'End') return;
  if (event.altKey) return;
  const field = event.target;
  // radio 和 checkbox 也是 input，但没有文本光标，selectionStart 为 null。
  if (!field || field.selectionStart === null || field.selectionStart === undefined) return;

  const value = field.value;
  const toStart = event.key === 'Home';
  const backward = field.selectionDirection === 'backward';
  const caret = event.shiftKey
    ? (backward ? field.selectionStart : field.selectionEnd)
    : (toStart ? field.selectionStart : field.selectionEnd);

  let target;
  if (event.metaKey || event.ctrlKey) {
    target = toStart ? 0 : value.length;
  } else if (toStart) {
    target = value.lastIndexOf('\n', caret - 1) + 1;
  } else {
    const lineEnd = value.indexOf('\n', caret);
    target = lineEnd === -1 ? value.length : lineEnd;
  }

  event.preventDefault();
  if (event.shiftKey) {
    const anchor = backward ? field.selectionEnd : field.selectionStart;
    field.setSelectionRange(
      Math.min(anchor, target),
      Math.max(anchor, target),
      target < anchor ? 'backward' : 'forward',
    );
  } else {
    field.setSelectionRange(target, target);
  }
});

if (!sessionId || !token) {
  renderError(new Error('页面链接缺少 Session 或访问令牌。请使用 Agent 返回的完整链接。'));
} else {
  loadBundle(true)
    .then(() => {
      setInterval(() => loadBundle(false).catch(() => {}), 3000);
    })
    .catch(renderError);
}
