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

  function silhouette(img, src) {
    if (!img) return;
    img.src = src + '?silhouette=master-v2';
    img.alt = '';
    img.style.setProperty('width','100%','important');
    img.style.setProperty('height','100%','important');
    img.style.setProperty('object-fit','contain','important');
    img.style.setProperty('object-position','50% 100%','important');
    img.style.setProperty('transform','none','important');
    img.style.setProperty('filter','brightness(0) grayscale(1) contrast(2)','important');
    img.style.setProperty('opacity','1','important');
  }

  function applyExactStageSilhouettes() {
    const cards = Array.from(document.querySelectorAll('.evolution-card'));
    if (!cards.length) return;

    cards.forEach((card, index) => {
      if (index >= stageMasters.length) return;
      const locked = card.classList.contains('locked');
      const img = card.querySelector('.evolution-character img, .scene-clean-image, img');
      if (!img) return;
      if (locked) {
        silhouette(img, stageMasters[index]);
        card.classList.add('master-silhouette');
      } else {
        card.classList.remove('master-silhouette');
      }
    });

    const firstLockedIndex = cards.findIndex(card => card.classList.contains('locked'));
    const nextIndex = firstLockedIndex >= 0 ? firstLockedIndex : 1;
    silhouette(document.querySelector('.shadow-character img'), stageMasters[nextIndex]);
  }

  function boot() {
    applyExactStageSilhouettes();
    let scheduled = false;
    const observer = new MutationObserver(() => {
      if (scheduled) return;
      scheduled = true;
      requestAnimationFrame(() => { scheduled = false; applyExactStageSilhouettes(); });
    });
    observer.observe(document.body, { childList:true, subtree:true, attributes:true, attributeFilter:['class','src'] });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once:true });
  else boot();
})();
