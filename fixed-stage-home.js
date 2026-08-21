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
      transform: none !important;
    }
    #home .hero .scene-clean-image.stage-art-clean[data-clean-debutant="1"] {
      object-position: center bottom !important;
      padding: 2% 8% 0 8% !important;
      box-sizing: border-box !important;
    }
    .evolution-real.stage-art-clean {
      width: 100% !important;
      height: 100% !important;
      max-width: 100% !important;
      object-fit: contain !important;
      object-position: center center !important;
      transform: none !important;
    }
  `;
  document.head.appendChild(style);

  function cleanHomepageDebutant(root = document) {
    const img = root.querySelector?.('#home .hero .scene-clean-image');
    if (!img) return;

    const src = img.getAttribute('src') || img.currentSrc || '';
    const isDebutant = /01-debutant(?:\.webp)?(?:\?|$)/i.test(src) || /01-debutant/i.test(src);

    if (isDebutant) {
      const cleanSrc = '/01-debutant-character.png';
      if (img.getAttribute('src') !== cleanSrc) img.setAttribute('src', cleanSrc);
      img.dataset.cleanDebutant = '1';
      const scene = img.closest('.character-scene-clean');
      if (scene) scene.style.setProperty('--stage-backdrop', 'url("/01-debutant-background.webp")');
    } else {
      delete img.dataset.cleanDebutant;
    }
  }

  function markStageArtwork(root = document) {
    root.querySelectorAll?.('img[src*="/assets/characters/"], img[src="/01-debutant-character.png"]').forEach(img => {
      img.classList.add('stage-art-clean');
    });
    cleanHomepageDebutant(root);
  }

  markStageArtwork();
  new MutationObserver(() => markStageArtwork()).observe(document.documentElement, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['src']
  });
})();
