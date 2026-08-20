(() => {
  'use strict';
  const VERSION = 'fullbody23';

  const rewrite = (img) => {
    if (!(img instanceof HTMLImageElement)) return;
    const raw = img.getAttribute('src') || '';
    if (!raw.includes('assets/creator/')) return;

    try {
      const url = new URL(raw, location.href);
      if (url.searchParams.get('v') !== VERSION) {
        url.searchParams.set('v', VERSION);
        const nextSrc = url.toString();
        if (img.src !== nextSrc) img.src = nextSrc;
      }

      const fallback = img.dataset.fallback;
      if (fallback && fallback.includes('assets/creator/')) {
        const f = new URL(fallback, location.href);
        if (f.searchParams.get('v') !== VERSION) {
          f.searchParams.set('v', VERSION);
          const nextFallback = f.toString();
          if (img.dataset.fallback !== nextFallback) img.dataset.fallback = nextFallback;
        }
      }
    } catch (_) {}
  };

  const scan = (root = document) => {
    root.querySelectorAll?.('img[src*="assets/creator/"]').forEach(rewrite);
  };

  const start = () => {
    scan();
    const observer = new MutationObserver((mutations) => {
      for (const m of mutations) {
        if (m.type === 'attributes' && m.target instanceof HTMLImageElement) {
          rewrite(m.target);
          continue;
        }
        for (const node of m.addedNodes) {
          if (!(node instanceof Element)) continue;
          if (node instanceof HTMLImageElement) rewrite(node);
          scan(node);
        }
      }
    });
    observer.observe(document.documentElement, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ['src','data-fallback']
    });
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once:true});
  else start();
})();
