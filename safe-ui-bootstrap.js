(() => {
  'use strict';

  const $ = id => document.getElementById(id);
  const stages = [
    ['01-debutant','DÉBUTANT',1],
    ['05-debrouillard','DÉBROUILLARD',5],
    ['10-chasseur','CHASSEUR',10],
    ['15-hustler','HUSTLER',15],
    ['20-pro','PRO',20],
    ['30-elite','ÉLITE',30],
    ['40-cyber-looter','CYBER LOOTER',40],
    ['50-rise-looter','RISE LOOTER',50]
  ];

  function openCreator() {
    const modal = $('creatorModal');
    if (!modal) return;
    document.body.classList.add('creator-test-active');
    modal.classList.add('show');
    modal.style.display = 'grid';
    modal.setAttribute('aria-hidden','false');
    try {
      if (typeof window.openCreatorTest === 'function') window.openCreatorTest();
      else {
        if (typeof window.renderHairChoices === 'function') window.renderHairChoices();
        if (typeof window.updateCreatorPreview === 'function') window.updateCreatorPreview();
      }
    } catch (e) { console.warn('Creator bootstrap fallback:', e); }
  }

  function restoreEvolution() {
    const grid = $('evolutionGrid');
    if (!grid) return;
    grid.innerHTML = stages.map(([slug,name,level], i) => `
      <div class="evolution-card ${i === 0 ? 'unlocked' : 'locked'}">
        <div class="evolution-character">
          <img class="evolution-silhouette" src="/silhouettes/${slug}.png?v=9" alt="${name}">
        </div>
        <div class="evolution-name"><span>NIVEAU ${level}</span><br><b>${name}</b><br><small>${i===0?'Niveau actuel':'Évolution à découvrir'}</small></div>
      </div>`).join('');

    const next = $('nextEvolutionShadow');
    if (next) next.innerHTML = '<img class="next-silhouette" src="/silhouettes/05-debrouillard.png?v=9" alt="DÉBROUILLARD">';
  }

  function init() {
    const button = $('creatorTestButton');
    if (button) {
      button.onclick = openCreator;
      button.addEventListener('click', openCreator, {capture:true});
    }
    restoreEvolution();
    if (new URLSearchParams(location.search).get('creatorTest') === '1') openCreator();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, {once:true});
  else init();
})();
