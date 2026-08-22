(() => {
  'use strict';

  const MALE_STAGE_ASSETS = [
    '/01-debutant.webp?v=final-eight-20260821-2',
    '/05-debrouillard.webp?v=final-eight-20260821-2',
    '/10-chasseur.webp?v=final-eight-20260821-2',
    '/15-hustler.webp?v=final-eight-20260821-2',
    '/20-pro.webp?v=final-eight-20260821-2',
    '/30-elite.webp?v=final-eight-20260821-2',
    '/40-cyber-looter.webp?v=final-eight-20260821-2',
    '/50-rise-looter.webp?v=final-eight-20260821-2'
  ];

  const FEMALE_STAGE_ASSETS = [
    '/female-01-debutant.webp?v=female-fixed-20260822-1',
    '/female-05-debrouillard.webp?v=female-fixed-20260822-1',
    '/female-10-chasseur.webp?v=female-fixed-20260822-1',
    '/female-15-hustler.webp?v=female-fixed-20260822-1',
    '/female-20-pro.webp?v=female-fixed-20260822-1',
    '/female-30-elite.webp?v=female-fixed-20260822-1',
    '/female-40-cyber-looter.webp?v=female-fixed-20260822-1',
    '/female-50-rise-looter.webp?v=female-fixed-20260822-1'
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
      const matches = [...MALE_STAGE_ASSETS, ...FEMALE_STAGE_ASSETS]
        .some(asset => src.includes(asset.split('?')[0]));
      if (matches) img.classList.add('stage-art-clean');
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
