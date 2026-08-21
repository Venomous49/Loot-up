(() => {
  'use strict';

  const style = document.createElement('style');
  style.id = 'riselooter-polish-v3-style';
  style.textContent = `
    #home .hero .character-scene-clean {
      position: absolute !important;
      inset: 0 !important;
      overflow: hidden !important;
      background: #070b0e !important;
    }
    #home .hero .character-scene-clean::after {
      content: "" !important;
      display: block !important;
      position: absolute !important;
      inset: 0 !important;
      z-index: 0 !important;
      background-image: var(--stage-backdrop, none) !important;
      background-size: cover !important;
      background-position: center center !important;
      background-repeat: no-repeat !important;
      filter: brightness(.42) saturate(.82) !important;
      opacity: .72 !important;
      transform: scale(1.03) !important;
      pointer-events: none !important;
    }
    #home .hero .scene-clean-image.stage-art-clean {
      position: absolute !important;
      inset: 0 !important;
      z-index: 1 !important;
      width: 100% !important;
      height: 100% !important;
      max-width: 100% !important;
      object-fit: contain !important;
      object-position: center center !important;
      transform: none !important;
      filter: none !important;
      opacity: 1 !important;
    }
    .evolution-real.stage-art-clean {
      width: 100% !important;
      height: 100% !important;
      max-width: 100% !important;
      object-fit: contain !important;
      object-position: center center !important;
      transform: none !important;
      filter: none !important;
    }
    #home .next-evolution {
      bottom: 68px !important;
    }
    #challenges .bonus { display: none !important; }
    #missions .filters .filter:not([data-filter="survey"]) { display: none !important; }
  `;
  document.head.appendChild(style);

  function setText(el, value) {
    if (el && el.textContent !== value) el.textContent = value;
  }

  function syncStageBackdrop() {
    const img = document.querySelector('#home .hero .scene-clean-image.stage-art-clean');
    const scene = img && img.closest('.character-scene-clean');
    if (!img || !scene) return;
    const src = img.currentSrc || img.src;
    const value = src ? `url("${src.replace(/"/g, '\\"')}")` : 'none';
    if (scene.style.getPropertyValue('--stage-backdrop') !== value) {
      scene.style.setProperty('--stage-backdrop', value);
    }
  }

  function polishChallenges() {
    const section = document.getElementById('challenges');
    if (!section) return;

    setText(section.querySelector('.section-subtitle'), 'Réponds à 5 sondages pour gagner de l’XP.');

    [...section.querySelectorAll('.challenge')].forEach(challenge => {
      if (challenge.dataset.category !== 'survey') {
        challenge.remove();
        return;
      }
      setText(challenge.querySelector('span:first-child'), '▤ Réponds à 5 sondages');
      const reward = challenge.querySelector('.challenge-reward');
      setText(reward, '+150 XP');
      if (reward && reward.style.color !== 'rgb(189, 116, 255)') reward.style.color = '#bd74ff';
    });
  }

  function polishMissions() {
    const section = document.getElementById('missions');
    if (!section) return;

    setText(section.querySelector('.section-subtitle'), 'Choisis comment tu veux gagner de l’XP.');

    section.querySelectorAll('.filters .filter').forEach(button => {
      const survey = button.dataset.filter === 'survey';
      button.classList.toggle('active', survey);
      if (!survey && button.style.display !== 'none') button.style.display = 'none';
    });

    section.querySelectorAll('.mission').forEach(card => {
      const isSurvey = (card.textContent || '').toLowerCase().includes('sondage');
      const target = isSurvey ? '' : 'none';
      if (card.style.display !== target) card.style.display = target;
    });
  }

  function polishMissionTest() {
    const root = document.querySelector('main') || document.body;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);

    nodes.forEach(node => {
      const value = node.nodeValue || '';
      let next = value;
      next = next.replace(/mission test looter/gi, 'Mission test Rise Looter');
      next = next.replace(/atteint le niveau demandé pour gagner des? lootx/gi, 'Atteint le niveau demandé pour gagner de l’XP');
      next = next.replace(/atteint le niveau demandé pour gagner des? rl coins/gi, 'Atteint le niveau demandé pour gagner de l’XP');
      if (next !== value) node.nodeValue = next;
    });
  }

  function apply() {
    syncStageBackdrop();
    polishChallenges();
    polishMissions();
    polishMissionTest();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', apply, { once: true });
  } else {
    apply();
  }

  let queued = false;
  new MutationObserver(() => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => {
      queued = false;
      apply();
    });
  }).observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ['src', 'class'] });
})();
