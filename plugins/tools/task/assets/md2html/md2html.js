(function () {
  const THEME_STORAGE_KEY = 'md2html.theme';
  const THEME_DARK = 'dark';
  const THEME_LIGHT = 'light';

  const safeStorageGet = (key) => {
    try {
      return window.localStorage ? window.localStorage.getItem(key) : null;
    } catch (_e) {
      return null;
    }
  };
  const safeStorageSet = (key, value) => {
    try {
      if (window.localStorage) window.localStorage.setItem(key, value);
    } catch (_e) {}
  };

  const getTheme = () => {
    const saved = safeStorageGet(THEME_STORAGE_KEY);
    if (saved === THEME_DARK || saved === THEME_LIGHT) return saved;
    const fromDom = document.documentElement && document.documentElement.getAttribute('data-theme');
    return fromDom === THEME_LIGHT ? THEME_LIGHT : THEME_DARK;
  };

  const setTheme = (theme) => {
    const next = theme === THEME_LIGHT ? THEME_LIGHT : THEME_DARK;
    document.documentElement.setAttribute('data-theme', next);
    // Help form controls / scrollbars follow the current theme.
    try {
      document.documentElement.style.colorScheme = next;
    } catch (_e) {}
    updateThemeToggleIcon(next);
  };

  const updateThemeToggleIcon = (theme) => {
    const btn = document.getElementById('md2html-theme-toggle');
    if (!btn) return;
    const icon = btn.querySelector('.theme-toggle__icon');
    if (icon) icon.textContent = theme === THEME_DARK ? '☀' : '☾';
    btn.setAttribute('aria-label', theme === THEME_DARK ? '切换为浅色模式' : '切换为深色模式');
    btn.setAttribute('title', theme === THEME_DARK ? '切换为浅色模式' : '切换为深色模式');
  };

  const initThemeToggle = () => {
    const btn = document.getElementById('md2html-theme-toggle');
    const theme = getTheme();
    setTheme(theme);
    if (!btn) return;
    btn.addEventListener('click', () => {
      const current = getTheme();
      const next = current === THEME_DARK ? THEME_LIGHT : THEME_DARK;
      safeStorageSet(THEME_STORAGE_KEY, next);
      setTheme(next);
      // Re-render mermaid with the new theme.
      renderMermaid({ theme: next, rerender: true });
    });
  };

  // Viewer modal (images + diagrams)
  const modal = document.getElementById('viewer-modal');
  const inner = document.getElementById('viewer-inner');
  const title = document.getElementById('viewer-title');
  const caption = document.getElementById('viewer-caption');
  const closeBtn = document.getElementById('viewer-close');
  const stage = document.getElementById('viewer-stage');

  const zoomOutBtn = document.getElementById('viewer-zoom-out');
  const zoomInBtn = document.getElementById('viewer-zoom-in');
  const zoomResetBtn = document.getElementById('viewer-zoom-reset');
  const zoomLevelText = document.getElementById('viewer-zoom-level');

  let scale = 1;
  let baseScale = 1;
  let translateX = 0;
  let translateY = 0;
  let dragging = false;
  let dragStartX = 0;
  let dragStartY = 0;
  let dragBaseX = 0;
  let dragBaseY = 0;

  const clamp = (n, min, max) => Math.min(max, Math.max(min, n));

  const updateZoomUi = () => {
    if (!zoomLevelText) return;
    const denom = baseScale > 0 ? baseScale : 1;
    const pct = Math.round((scale / denom) * 100);
    zoomLevelText.textContent = pct + '%';
  };

  const applyTransform = () => {
    if (!inner) return;
    inner.style.transform =
      'translate(calc(-50% + ' +
      translateX +
      'px), calc(-50% + ' +
      translateY +
      'px)) scale(' +
      scale +
      ')';
    updateZoomUi();
  };

  const measureContentSize = () => {
    if (!inner) return null;
    const el = inner.querySelector('svg, img');
    if (!el) return null;
    if (el.tagName && el.tagName.toLowerCase() === 'svg') {
      const svg = el;
      try {
        if (typeof svg.getBBox === 'function') {
          const box = svg.getBBox();
          if (box && box.width > 0 && box.height > 0) return { width: box.width, height: box.height };
        }
      } catch (_e) {}
      try {
        const rect = svg.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) return { width: rect.width, height: rect.height };
      } catch (_e) {}
      return null;
    }
    const img = el;
    const w = img.naturalWidth || img.width || 0;
    const h = img.naturalHeight || img.height || 0;
    if (w > 0 && h > 0) return { width: w, height: h };
    try {
      const rect = img.getBoundingClientRect();
      if (rect.width > 0 && rect.height > 0) return { width: rect.width, height: rect.height };
    } catch (_e) {}
    return null;
  };

  const computeBaseScale = () => {
    if (!stage) return 1;
    const size = measureContentSize();
    if (!size) return 1;
    const stageRect = stage.getBoundingClientRect();
    const maxW = Math.max(1, stageRect.width - 32);
    const maxH = Math.max(1, stageRect.height - 32);
    const fit = Math.min(maxW / size.width, maxH / size.height);
    // Avoid extreme values; allow shrinking to fit, but don't auto upscale by default.
    return clamp(fit, 0.1, 1);
  };

  const resetViewerTransform = ({ fit } = {}) => {
    translateX = 0;
    translateY = 0;
    baseScale = fit ? computeBaseScale() : 1;
    // Define "100%" as the fit-to-stage base scale so users can always zoom >100%.
    scale = baseScale;
    applyTransform();
  };

  const setScaleFromBase = (next) => {
    const n = Number(next);
    if (!Number.isFinite(n)) return;
    const minScale = Math.max(0.01, baseScale * 0.01);
    scale = Math.max(minScale, n);
    applyTransform();
  };

  const openViewer = (opts) => {
    if (!modal || !inner) return;
    scale = 1;
    baseScale = 1;
    translateX = 0;
    translateY = 0;
    inner.classList.remove('dragging');
    inner.innerHTML = '';
    inner.style.opacity = '0';

    if (title) title.textContent = opts.title || '';
    if (caption) caption.textContent = opts.caption || '';

    if (opts.type === 'img') {
      const img = new Image();
      img.src = opts.src;
      img.alt = opts.alt || '';
      inner.appendChild(img);
    } else if (opts.type === 'svg') {
      inner.innerHTML = opts.svg || '';
    }

    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');

    // Fit & center after DOM paints.
    requestAnimationFrame(() => {
      resetViewerTransform({ fit: true });
      inner.style.opacity = '1';
      // For SVG, getBBox may be 0 before fonts load; re-fit once after load.
      window.addEventListener(
        'load',
        () => {
          if (!modal.classList.contains('open')) return;
          resetViewerTransform({ fit: true });
        },
        { once: true }
      );
    });
  };

  const closeViewer = () => {
    if (!modal || !inner) return;
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
    inner.innerHTML = '';
  };

  closeBtn && closeBtn.addEventListener('click', closeViewer);
  zoomOutBtn &&
    zoomOutBtn.addEventListener('click', () => {
      if (!modal || !modal.classList.contains('open')) return;
      setScaleFromBase(scale - baseScale * 0.15);
    });
  zoomInBtn &&
    zoomInBtn.addEventListener('click', () => {
      if (!modal || !modal.classList.contains('open')) return;
      setScaleFromBase(scale + baseScale * 0.15);
    });
  zoomResetBtn &&
    zoomResetBtn.addEventListener('click', () => {
      if (!modal || !modal.classList.contains('open')) return;
      resetViewerTransform({ fit: true });
    });
  modal && modal.addEventListener('click', (ev) => {
    if (ev.target === modal) closeViewer();
  });
  window.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape') closeViewer();
  });

  // Zoom with wheel
  stage &&
    stage.addEventListener(
      'wheel',
      (ev) => {
        if (!modal || !modal.classList.contains('open')) return;
        ev.preventDefault();
        const delta = Math.sign(ev.deltaY);
        const next = scale + (delta > 0 ? -baseScale * 0.15 : baseScale * 0.15);
        setScaleFromBase(next);
      },
      { passive: false }
    );

  // Pan with drag
  inner &&
    inner.addEventListener('pointerdown', (ev) => {
      if (scale <= baseScale) return;
      dragging = true;
      inner.classList.add('dragging');
      dragStartX = ev.clientX;
      dragStartY = ev.clientY;
      dragBaseX = translateX;
      dragBaseY = translateY;
      inner.setPointerCapture(ev.pointerId);
    });
  inner &&
    inner.addEventListener('pointermove', (ev) => {
      if (!dragging) return;
      translateX = dragBaseX + (ev.clientX - dragStartX);
      translateY = dragBaseY + (ev.clientY - dragStartY);
      applyTransform();
    });
  inner &&
    inner.addEventListener('pointerup', () => {
      dragging = false;
      inner.classList.remove('dragging');
    });
  inner &&
    inner.addEventListener('pointercancel', () => {
      dragging = false;
      inner.classList.remove('dragging');
    });

  // Code copy buttons
  document.querySelectorAll('pre > code').forEach((code) => {
    const pre = code.parentElement;
    if (!pre || pre.querySelector('.code-copy')) return;
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'code-copy';
    btn.textContent = '复制';
    btn.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(code.innerText);
        btn.textContent = '已复制';
        setTimeout(() => (btn.textContent = '复制'), 900);
      } catch (_e) {
        btn.textContent = '失败';
        setTimeout(() => (btn.textContent = '复制'), 900);
      }
    });
    pre.appendChild(btn);
  });

  // External links in new tab
  document.querySelectorAll('a[href]').forEach((a) => {
    const href = a.getAttribute('href') || '';
    if (/^https?:\/\//i.test(href)) {
      a.setAttribute('target', '_blank');
      a.setAttribute('rel', 'noopener noreferrer');
    }
  });

  // Heading anchor: copy link
  document.querySelectorAll('.h-anchor').forEach((a) => {
    a.addEventListener('click', async (ev) => {
      ev.preventDefault();
      const href = a.getAttribute('href') || '';
      const base = location.href.split('#')[0];
      const url = base + href;
      try {
        await navigator.clipboard.writeText(url);
      } catch (_e) {}
      history.replaceState(null, '', href);
    });
  });

  // Image captions + viewer
  const images = Array.from(document.querySelectorAll('img.md-image'));
  images.forEach((img) => {
    const cap = img.getAttribute('data-caption') || img.getAttribute('alt') || '';
    const p = img.parentElement;
    if (cap && p && p.tagName === 'P' && p.children.length === 1) {
      const div = document.createElement('div');
      div.className = 'img-caption';
      div.textContent = cap;
      p.insertAdjacentElement('afterend', div);
    }
    img.addEventListener('click', (ev) => {
      ev.preventDefault();
      const src = img.currentSrc || img.getAttribute('src') || '';
      openViewer({
        type: 'img',
        src,
        alt: img.getAttribute('alt') || '',
        title: src,
        caption: cap,
      });
    });
  });

  // Mermaid helpers
  const tagMermaidSvgs = (root) => {
    try {
      const scope = root && root.querySelectorAll ? root : document;
      const mermaidRoots = [];
      if (root && root.matches && root.matches('.mermaid')) mermaidRoots.push(root);
      mermaidRoots.push(...scope.querySelectorAll('.mermaid'));
      mermaidRoots.forEach((m) => {
        m.querySelectorAll('svg').forEach((svg) => svg.classList.add('md2html-mermaid-svg'));
      });
    } catch (_e) {}
  };

  const getMermaidTheme = (theme) => {
    return theme === THEME_LIGHT ? 'default' : 'dark';
  };

  const configureMermaid = (theme) => {
    try {
      if (!window.mermaid || !window.mermaid.initialize) return;
      // Prevent Mermaid's built-in auto-start from rendering before we stash sources.
      window.mermaid.startOnLoad = false;

      const computedSans =
        (document.body && getComputedStyle(document.body).fontFamily) ||
        (document.documentElement && getComputedStyle(document.documentElement).fontFamily) ||
        '';
      const sans = String(computedSans)
        .replace(/\s+/g, ' ')
        .trim();

      window.mermaid.initialize({
        startOnLoad: false,
        theme: getMermaidTheme(theme || getTheme()),
        securityLevel: 'loose',
        themeVariables: {
          fontFamily: sans || 'arial, sans-serif',
          fontSize: '13px',
        },
        flowchart: { useMaxWidth: true, htmlLabels: true, curve: 'basis' },
      });
    } catch (_e) {}
  };

  const ensureMermaidSources = (nodes) => {
    nodes.forEach((el) => {
      if (!el || !el.dataset) return;
      if (typeof el.dataset.md2htmlMermaidSrc === 'string') return;
      // Store original source before Mermaid replaces it with <svg>.
      el.dataset.md2htmlMermaidSrc = (el.textContent || '').replace(/\r\n/g, '\n');
    });
  };

  const restoreMermaidSources = (nodes) => {
    nodes.forEach((el) => {
      if (!el || !el.dataset) return;
      const src = el.dataset.md2htmlMermaidSrc;
      if (typeof src !== 'string') return;
      el.removeAttribute('data-processed');
      // Remove previous render output.
      el.innerHTML = '';
      el.textContent = src;
    });
  };

  const renderMermaid = async ({ theme, rerender } = {}) => {
    try {
      const nodes = Array.from(document.querySelectorAll('.mermaid[data-md2html-viewer="mermaid"]'));
      if (!nodes.length) return;
      if (!window.mermaid || !window.mermaid.initialize || !window.mermaid.render) return;

      configureMermaid(theme || getTheme());

      ensureMermaidSources(nodes);
      if (rerender) restoreMermaidSources(nodes);

      for (let i = 0; i < nodes.length; i++) {
        const el = nodes[i];
        const src = (el && el.dataset && el.dataset.md2htmlMermaidSrc) || (el ? el.textContent : '') || '';
        const id = 'md2html-' + String(Date.now()) + '-' + String(i);
        try {
          const out = await window.mermaid.render(id, src);
          const svg = out && out.svg ? out.svg : '';
          el.innerHTML = svg;
          if (out && typeof out.bindFunctions === 'function') out.bindFunctions(el);
        } catch (_e) {
          // Mermaid will render an error diagram for invalid sources; keep going.
        }
      }
      tagMermaidSvgs(document);
    } catch (_e) {}
  };

  // Mermaid viewer (click to open)
  const mermaids = Array.from(document.querySelectorAll('.mermaid[data-md2html-viewer="mermaid"]'));
  mermaids.forEach((el) => {
    el.addEventListener('click', (ev) => {
      ev.preventDefault();
      const tryOpen = () => {
        const svg = el.querySelector('svg');
        if (svg) openViewer({ type: 'svg', svg: svg.outerHTML, title: 'Mermaid', caption: '' });
      };

      tryOpen();
      if (!el.querySelector('svg')) {
        try {
          if (window.mermaid && window.mermaid.render) {
            ensureMermaidSources([el]);
            const src = (el.dataset && el.dataset.md2htmlMermaidSrc) || el.textContent || '';
            const id = 'md2html-onclick-' + String(Date.now());
            window.mermaid
              .render(id, src)
              .then((out) => {
                el.innerHTML = (out && out.svg) || '';
                if (out && typeof out.bindFunctions === 'function') out.bindFunctions(el);
                tagMermaidSvgs(el);
                tryOpen();
              })
              .catch(() => {});
          }
        } catch (_e) {}
      }
    });
  });

  // TOC active highlight
  const tocLinks = Array.from(document.querySelectorAll('.toc a[href^="#"]'));
  const headings = tocLinks
    .map((a) => document.querySelector(a.getAttribute('href')))
    .filter(Boolean);
  const setActive = () => {
    let activeIdx = -1;
    for (let i = 0; i < headings.length; i++) {
      const h = headings[i];
      const top = h.getBoundingClientRect().top;
      if (top <= 36) activeIdx = i;
    }
    tocLinks.forEach((a, idx) => {
      if (idx === activeIdx) a.classList.add('active');
      else a.classList.remove('active');
    });
  };
  window.addEventListener('scroll', setActive, { passive: true });
  setActive();

  // Init: theme then mermaid (after fonts), then svg tagging.
  initThemeToggle();

  // Stash sources early (before Mermaid's DOMContentLoaded auto-start).
  ensureMermaidSources(Array.from(document.querySelectorAll('.mermaid[data-md2html-viewer="mermaid"]')));
  configureMermaid(getTheme());

  if (document.fonts && document.fonts.ready && typeof document.fonts.ready.then === 'function') {
    document.fonts.ready
      .then(() => renderMermaid({ theme: getTheme(), rerender: false }))
      .catch(() => renderMermaid({ theme: getTheme(), rerender: false }));
  } else {
    renderMermaid({ theme: getTheme(), rerender: false });
    // Fallback for environments without FontFaceSet: re-render once after all resources load
    // to reduce layout issues (e.g., journey label overlap).
    window.addEventListener(
      'load',
      () => {
        renderMermaid({ theme: getTheme(), rerender: true });
      },
      { once: true }
    );
  }
})();
