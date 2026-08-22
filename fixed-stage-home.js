(() => {
  'use strict';

  const VERSION='stage-render-20260822-3';
  const MALE_STAGE_ASSETS = [
    `/01-debutant.webp?v=${VERSION}`,
    `/05-debrouillard.webp?v=${VERSION}`,
    `/10-chasseur.webp?v=${VERSION}`,
    `/15-hustler.webp?v=${VERSION}`,
    `/20-pro.webp?v=${VERSION}`,
    `/30-elite.webp?v=${VERSION}`,
    `/40-cyber-looter.webp?v=${VERSION}`,
    `/50-rise-looter.webp?v=${VERSION}`
  ];

  const FEMALE_STAGE_ASSETS = [
    `/female-01-debutant.webp?v=${VERSION}`,
    `/female-05-debrouillard.webp?v=${VERSION}`,
    `/female-10-chasseur.webp?v=${VERSION}`,
    `/female-15-hustler.webp?v=${VERSION}`,
    `/female-20-pro.webp?v=${VERSION}`,
    `/female-30-elite.webp?v=${VERSION}`,
    `/female-40-cyber-looter.webp?v=${VERSION}`,
    `/female-50-rise-looter.webp?v=${VERSION}`
  ];

  const originalAssetPath = window.assetPath;
  if (typeof originalAssetPath === 'function') {
    window.assetPath = function(profile, stage) {
      const index = Math.max(0, Math.min(Number(stage) || 0, MALE_STAGE_ASSETS.length - 1));
      return profile?.avatar_gender === 'female'
        ? FEMALE_STAGE_ASSETS[index]
        : MALE_STAGE_ASSETS[index];
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
      max-height: 100% !important;
      object-fit: contain !important;
      object-position: center 55% !important;
      filter: none !important;
      opacity: 1 !important;
      padding: 8px 6px 2px !important;
      box-sizing: border-box !important;
      image-rendering: auto !important;
      backface-visibility: hidden !important;
    }
    #home .hero .scene-clean-image.stage-art-clean {
      transform: translateY(4px) !important;
    }
    .evolution-real.stage-art-clean {
      transform: translateY(2px) !important;
    }
  `;
  document.head.appendChild(style);

  function markStageArtwork(root = document) {
    root.querySelectorAll?.('img').forEach(img => {
      const src = img.getAttribute('src') || img.currentSrc || '';
      const matches = [...MALE_STAGE_ASSETS, ...FEMALE_STAGE_ASSETS]
        .some(asset => src.includes(asset.split('?')[0]));
      if (matches) {
        img.classList.add('stage-art-clean');
        img.decoding = 'async';
      }
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
