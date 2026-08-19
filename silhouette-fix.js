(() => {
  const stageMasters = [
    '/01-debutant.webp',
    '/05-debrouillard.webp',
    '/10-chasseur.webp',
    '/15-hustler.webp',
    '/20-pro.webp',
    '/30-elite.webp',
    '/40-cyber-looter.webp',
    '/50-rise-looter.webp'
  ];

  function applyExactStageSilhouettes() {
    const cards = Array.from(document.querySelectorAll('.evolution-card'));
    if (!cards.length) return;

    cards.forEach((card, index) => {
      if (index >= stageMasters.length) return;
      if (!card.classList.contains('locked')) return;
      const img = card.querySelector('.evolution-character img, .scene-clean-image, img');
      if (!img) return;
      img.src = stageMasters[index] + '?silhouette=master-v1';
      img.alt = '';
      img.style.objectFit = 'contain';
      img.style.objectPosition = '50% 100%';
      img.style.transform = 'none';
      img.style.filter = 'brightness(0) grayscale(1)';
      img.style.opacity = '1';
    });

    const firstLockedIndex = cards.findIndex(card => card.classList.contains('locked'));
    const nextIndex = firstLockedIndex > 0 ? firstLockedIndex : 1;
    const nextImg = document.querySelector('.shadow-character img');
    if (nextImg && stageMasters[nextIndex]) {
      nextImg.src = stageMasters[nextIndex] + '?silhouette=master-v1';
      nextImg.style.objectFit = 'contain';
      nextImg.style.objectPosition = '50% 100%';
      nextImg.style.transform = 'none';
      nextImg.style.filter = 'brightness(0) grayscale(1)';
      nextImg.style.opacity = '1';
    }
  }

  function boot() {
    applyExactStageSilhouettes();
    const observer = new MutationObserver(() => applyExactStageSilhouettes());
    observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot, { once: true });
  } else {
    boot();
  }
})();
