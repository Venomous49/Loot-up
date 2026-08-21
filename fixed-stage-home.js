(() => {
  'use strict';

  const STAGE_SLUGS = [
    '01-debutant',
    '05-debrouillard',
    '10-chasseur',
    '15-hustler',
    '20-pro',
    '30-elite',
    '40-cyber-looter',
    '50-rise-looter'
  ];

  const originalAssetPath = window.assetPath;

  if (typeof originalAssetPath === 'function') {
    window.assetPath = function(profile, stage) {
      const gender = profile?.avatar_gender || 'male';
      if (gender !== 'male') return originalAssetPath(profile, stage);
      const index = Math.max(0, Math.min(Number(stage) || 0, STAGE_SLUGS.length - 1));
      return `/assets/characters/male/medium/brown/male_textured/${STAGE_SLUGS[index]}.webp`;
    };
  }

  const style = document.createElement('style');
  style.id = 'fixed-stage-home-art-style';
  style.textContent = `
    #home .hero .scene-clean-image.stage-art-clean {
      object-fit: contain !important;
      object-position: 79% center !important;
      transform: scale(1.12) !important;
      transform-origin: 79% 50% !important;
    }
    .evolution-real.stage-art-clean {
      width: 112% !important;
      height: 112% !important;
      max-width: none !important;
      object-fit: cover !important;
      object-position: center center !important;
      transform: translate(-5.35%,-5.35%) !important;
    }
  `;
  document.head.appendChild(style);

  function markStageArtwork(root = document) {
    root.querySelectorAll?.('img[src*="/assets/characters/"]').forEach(img => {
      img.classList.add('stage-art-clean');
    });
  }

  markStageArtwork();
  new MutationObserver(() => markStageArtwork()).observe(document.documentElement, {
    childList: true,
    subtree: true
  });
})();
