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

function element(tag, className = '', text = '') {
  const value = document.createElement(tag);
  if (className) value.className = className;
  if (text !== '') value.textContent = text;
  return value;
}

const MERMAID_BLOCK = /^[ \t]*```mermaid[ \t]*\r?\n([\s\S]*?)^[ \t]*```[ \t]*$/gm;

let mermaidLoader = null;
let diagramSequence = 0;

function hasDiagram(text) {
  MERMAID_BLOCK.lastIndex = 0;
  return MERMAID_BLOCK.test(text || '');
}

function loadMermaid() {
  mermaidLoader ||= new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = '/vendor/mermaid.min.js';
    script.onload = () => resolve(globalThis.mermaid);
    script.onerror = () => {
      script.remove();
      reject(new Error('图表组件加载失败，切换主题或刷新页面可重试'));
    };
    document.head.append(script);
  // 失败的 promise 不能留下来，否则一次网络抖动会让这一页所有图表永远渲染不出。
  }).catch((error) => {
    mermaidLoader = null;
    throw error;
  });
  return mermaidLoader;
}

// 把 Memphis 的语义 token 喂给 mermaid，这样切换明暗主题时图表跟着换。
function mermaidTheme() {
  const styles = getComputedStyle(document.documentElement);
  const read = (name) => styles.getPropertyValue(name).trim();
  const line = read('--line');
  return {
    theme: 'base',
    fontFamily: styles.fontFamily,
    themeVariables: {
      background: read('--surface'),
      primaryColor: read('--mustard'),
      primaryTextColor: read('--on-mustard'),
      primaryBorderColor: line,
      secondaryColor: read('--blue'),
      secondaryTextColor: read('--on-blue'),
      secondaryBorderColor: line,
      tertiaryColor: read('--surface-2'),
      tertiaryTextColor: read('--ink'),
      tertiaryBorderColor: line,
      lineColor: line,
      textColor: read('--ink'),
      mainBkg: read('--mustard'),
      nodeBorder: line,
      clusterBkg: read('--surface-2'),
      clusterBorder: line,
      titleColor: read('--ink'),
      edgeLabelBackground: read('--surface'),
      actorBkg: read('--mustard'),
      actorBorder: line,
      actorTextColor: read('--on-mustard'),
      signalColor: read('--ink'),
      signalTextColor: read('--ink'),
      labelBoxBkgColor: read('--blue'),
      labelBoxBorderColor: line,
      labelTextColor: read('--on-blue'),
      noteBkgColor: read('--surface-2'),
      noteBorderColor: line,
      noteTextColor: read('--ink'),
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
        color: ${read('--ink')};
        background: ${read('--surface')};
      }
      .edgeLabel rect {
        fill: ${read('--surface')};
      }
    `,
  };
}

async function renderDiagram(host, code) {
  diagramSequence += 1;
  const id = `ask-ui-diagram-${diagramSequence}`;
  try {
    const mermaid = await loadMermaid();
    mermaid.initialize({ startOnLoad: false, securityLevel: 'strict', ...mermaidTheme() });
    const { svg } = await mermaid.render(id, code);
    host.innerHTML = svg;
    host.dataset.state = 'ready';
  } catch (error) {
    // 渲染不出来时把原始图表源码亮出来，比留一个空框有用。
    host.replaceChildren();
    host.dataset.state = 'failed';
    host.append(element('p', 'diagram-error', `图表无法渲染：${error.message}`));
    host.append(element('pre', 'diagram-source', code));
  }
}

// 文本里的 ```mermaid 块渲染成图，其余部分保持纯文本，绝不当 HTML 解析。
// 返回第一个文字段落，调用方可以往它前面插标签，保持标签与正文同行。
function appendRichText(container, text) {
  const value = text || '';
  MERMAID_BLOCK.lastIndex = 0;
  let firstProse = null;
  const addProse = (prose) => {
    if (!prose) return;
    const paragraph = element('p', 'rich-text', prose);
    firstProse ||= paragraph;
    container.append(paragraph);
  };

  let cursor = 0;
  let match = MERMAID_BLOCK.exec(value);
  while (match) {
    addProse(value.slice(cursor, match.index).trim());
    const host = element('div', 'diagram');
    host.dataset.state = 'loading';
    host.append(element('p', 'diagram-loading', '图表加载中…'));
    container.append(host);
    renderDiagram(host, match[1].trim());
    cursor = match.index + match[0].length;
    match = MERMAID_BLOCK.exec(value);
  }
  addProse(value.slice(cursor).trim());
  return firstProse;
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

// 推荐值只做视觉提示，绝不预填答案：只有用户点过、选过、输入过才算已答。
function defaultAnswer(question) {
  return {
    questionId: question.id,
    selectedOptionIds: [],
    customText: '',
    supplementaryText: '',
  };
}

function normalizeAnswer(answer) {
  const normalized = structuredClone(answer);
  normalized.selectedOptionIds ||= [];
  normalized.customText ||= '';
  normalized.supplementaryText ||= '';
  return normalized;
}

function answersForRound(round) {
  const source = round.answers?.answers || round.questions.questions.map(defaultAnswer);
  const byId = new Map(source.map((answer) => [answer.questionId, answer]));
  return round.questions.questions.map((question) => normalizeAnswer(
    byId.get(question.id) || defaultAnswer(question),
  ));
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

function optionLabel(question, optionId) {
  return question.options?.find((option) => option.id === optionId)?.label || optionId;
}

function displayAnswer(question, answer) {
  if (!answer) return '未填写';
  const parts = question.type === 'text'
    ? [answer.customText?.trim()].filter(Boolean)
    : (answer.selectedOptionIds || []).map((id) => optionLabel(question, id));
  const primary = parts.length ? parts.join('、') : '未填写';
  const supplement = answer.supplementaryText?.trim();
  return supplement ? `${primary}；补充：${supplement}` : primary;
}

function selectionCount(question, answer) {
  if (question.type === 'text') return answer.customText.trim() ? 1 : 0;
  return (answer.selectedOptionIds || []).length;
}

// 只写补充说明、一个选项都不选，同样算这一题已经回答。
function isAnswered(question, editable, submittedAnswers) {
  const answer = editable
    ? answerFor(question.id)
    : submittedAnswers?.find((item) => item.questionId === question.id);
  if (!answer) return false;
  return selectionCount(question, answer) > 0 || Boolean(answer.supplementaryText?.trim());
}

function answeredQuestionCount(round, editable) {
  return round.questions.questions.reduce((count, question) => (
    count + (isAnswered(question, editable, round.answers?.answers) ? 1 : 0)
  ), 0);
}

function questionState(question, editable, submittedAnswers) {
  if (editable && question.id === focusedQuestionId) return 'current';
  return isAnswered(question, editable, submittedAnswers) ? 'done' : 'todo';
}

function firstUnansweredId(round, editable) {
  const pending = round.questions.questions.find(
    (question) => !isAnswered(question, editable, round.answers?.answers),
  );
  return pending?.id || null;
}

function roundEditable(round) {
  return round.status === 'waiting_for_user' && bundle.session.status === 'active';
}

function refreshProgress() {
  const round = currentRound();
  if (!round) return;
  const editable = roundEditable(round);
  const answered = answeredQuestionCount(round, editable);
  if (answeredCountElement) {
    answeredCountElement.textContent = `已答 ${answered} / ${round.questionCount}`;
  }
  if (progressCellsElement) {
    // 每个格子对应同序号的那一题，跳答时空格留在原位，不做左对齐填充。
    [...progressCellsElement.children].forEach((cell, index) => {
      const question = round.questions.questions[index];
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
    counter.textContent = `${answeredQuestionCount(round, editable)} / ${round.questionCount}`;
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
      pendingAnswers = answersForRound(round);
      focusedQuestionId = firstUnansweredId(round, roundEditable(round));
      render();
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

  const head = element('div', 'rail-head');
  head.append(element('span', '', '队列里还有谁在等'));
  head.append(element(
    'span',
    'rail-count',
    `${answeredQuestionCount(round, editable)} / ${round.questionCount}`,
  ));
  rail.append(head);

  const nav = element('ul', 'rail-nav');
  railNavElement = nav;
  round.questions.questions.forEach((question, index) => {
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
      document
        .querySelector(`.question-card[data-question-id="${CSS.escape(question.id)}"]`)
        ?.scrollIntoView({ block: 'center', behavior: 'smooth' });
      refreshRailStates(round, editable);
      refreshCardStates(round, editable);
    });
    item.append(button);
    nav.append(item);
  });
  rail.append(nav);
  container.append(rail);
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
    input.addEventListener('change', () => {
      if (question.type === 'single') {
        answer.selectedOptionIds = [option.id];
      } else if (input.checked) {
        answer.selectedOptionIds = [...new Set([...answer.selectedOptionIds, option.id])];
      } else {
        answer.selectedOptionIds = answer.selectedOptionIds.filter((id) => id !== option.id);
      }
      refreshProgress();
    });
    const content = element('span', 'option-content');
    const title = element('span', 'option-label');
    title.append(element('span', '', option.label));
    if (question.recommendedOptionIds?.includes(option.id)) {
      title.append(badge('推荐', 'recommended'));
    }
    content.append(title);
    if (option.description) {
      content.append(element('span', 'option-description', option.description));
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
  copy.append(element('h3', 'question-title', question.title));
  if (question.description) {
    const description = element('div', 'question-description');
    appendRichText(description, question.description);
    copy.append(description);
  }
  header.append(copy, questionFlags(question));
  card.append(header);

  if (question.background) {
    const background = element('div', 'question-background');
    const firstProse = appendRichText(background, question.background);
    const lead = element('b', '', '背景 · ');
    if (firstProse) {
      firstProse.prepend(lead);
    } else {
      // 背景整段只有一张图时，标签自成一行落在图前面。
      const label = element('p', 'rich-text');
      label.append(lead);
      background.prepend(label);
    }
    card.append(background);
  }

  const answer = editable
    ? answerFor(question.id)
    : submittedAnswers?.find((item) => item.questionId === question.id);
  if (editable) {
    if (question.type === 'text') renderTextQuestion(card, question, answer, true);
    else renderChoiceQuestion(card, question, answer, true);
    if (question.recommendationReason) {
      card.append(element('p', 'recommendation', `推荐理由：${question.recommendationReason}`));
    }
    renderSupplementaryInput(card, question, answer);
  } else {
    card.append(element('div', 'history-answer', displayAnswer(question, answer)));
  }
  return card;
}

function clientValidation(round) {
  const errors = [];
  for (const question of round.questions.questions) {
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
          answers: pendingAnswers,
        }),
      },
    );
    showSubmissionConfirmation();
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
  round.questions.questions.forEach((question, index) => {
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
    for (let index = 0; index < round.questionCount; index += 1) {
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
    status.append(element('span', 'answered-count', `共 ${round.questionCount} 题 · 只读`));
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
    pendingAnswers = round ? answersForRound(round) : [];
    focusedQuestionId = round ? firstUnansweredId(round, roundEditable(round)) : null;
  }
  if (changed) render();
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
