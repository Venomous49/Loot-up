(() => {
  'use strict';

  const STAGE_ASSETS = [
    '/01-debutant.webp',
    '/05-debrouillard.webp',
    '/10-chasseur.webp',
    '/15-hustler.webp',
    '/20-pro.webp',
    '/30-elite.webp',
    '/40-cyber-looter.webp',
    '/50-rise-looter.webp'
  ];

  // The character creator has been retired. The homepage now uses exactly one
  // canonical full-scene image per evolution stage, with no dependency on
  // gender/skin/hair folders.
  const originalAssetPath = window.assetPath;
  if (typeof originalAssetPath === 'function') {
    window.assetPath = function(_profile, stage) {
      const index = Math.max(0, Math.min(Number(stage) || 0, STAGE_ASSETS.length - 1));
      return STAGE_ASSETS[index];
    };
  }

  const style = document.createElement('style');
  style.id = 'fixed-stage-home-art-style';
  style.textContent = `
    #home .hero .scene-clean-image.stage-art-clean,
    .evolution-real.stage-art-clean {
      width: 100% !important;
      height: 100% !important;
      max-width: 100% !important;
      object-fit: contain !important;
      object-position: center center !important;
      transform: none !important;
      filter: none !important;
      opacity: 1 !important;
      padding: 0 !important;
      box-sizing: border-box !important;
      image-rendering: auto !important;
    }
  `;
  document.head.appendChild(style);

  function markStageArtwork(root = document) {
    root.querySelectorAll?.('img').forEach(img => {
      const src = img.getAttribute('src') || img.currentSrc || '';
      if (STAGE_ASSETS.some(asset => src.includes(asset))) img.classList.add('stage-art-clean');
    });
  }

  markStageArtwork();
  new MutationObserver(() => markStageArtwork()).observe(document.documentElement, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['src']
  });
})();
