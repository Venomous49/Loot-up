(() => {
  'use strict';

  const style = document.createElement('style');
  style.id = 'riselooter-polish-v3-style';
  style.textContent = `
    /* Stage artwork: crop the previously retouched top strip and remove side bars. */
    #home .hero .scene-clean-image.stage-art-clean {
      width: 100% !important;
      height: 100% !important;
      object-fit: cover !important;
      object-position: center 52% !important;
      transform: scale(1.10) !important;
      transform-origin: center center !important;
      filter: none !important;
    }
    .evolution-real.stage-art-clean {
      width: 100% !important;
      height: 100% !important;
      max-width: none !important;
      object-fit: cover !important;
      object-position: center 52% !important;
      transform: scale(1.10) !important;
      transform-origin: center center !important;
      filter: none !important;
    }

    /* Give the description a little more breathing room. */
    #home .next-evolution {
      bottom: 68px !important;
    }

    /* Survey-only experience. */
    #challenges .bonus { display: none !important; }
    #missions .filters .filter:not([data-filter="survey"]) { display: none !important; }
  `;
  document.head.appendChild(style);

  function polishChallenges() {
    const section = document.getElementById('challenges');
    if (!section) return;

    const subtitle = section.querySelector('.section-subtitle');
    if (subtitle) subtitle.textContent = 'Réponds à 5 sondages pour gagner de l’XP.';

    const challenges = [...section.querySelectorAll('.challenge')];
    challenges.forEach(challenge => {
      if (challenge.dataset.category !== 'survey') {
        challenge.remove();
        return;
      }
      const label = challenge.querySelector('span:first-child');
      const reward = challenge.querySelector('.challenge-reward');
      if (label) label.textContent = '▤ Réponds à 5 sondages';
      if (reward) {
        reward.textContent = '+150 XP';
        reward.style.color = '#bd74ff';
      }
    });
  }

  function polishMissions() {
    const section = document.getElementById('missions');
    if (!section) return;

    const subtitle = section.querySelector('.section-subtitle');
    if (subtitle) subtitle.textContent = 'Choisis comment tu veux gagner de l’XP.';

    section.querySelectorAll('.filters .filter').forEach(button => {
      if (button.dataset.filter === 'survey') {
        button.classList.add('active');
      } else {
        button.classList.remove('active');
        button.style.display = 'none';
      }
    });

    section.querySelectorAll('.mission').forEach(card => {
      const text = (card.textContent || '').toLowerCase();
      const isSurvey = text.includes('sondage');
      card.style.display = isSurvey ? '' : 'none';
    });
  }

  function polishMissionTest() {
    const root = document.querySelector('main') || document.body;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);

    nodes.forEach(node => {
      const value = node.nodeValue || '';
      if (/mission test looter/i.test(value)) {
        node.nodeValue = value.replace(/mission test looter/gi, 'Mission test Rise Looter');
      }
      if (/atteint le niveau demandé pour gagner des? lootx/i.test(value)) {
        node.nodeValue = value.replace(/atteint le niveau demandé pour gagner des? lootx/gi, 'Atteint le niveau demandé pour gagner de l’XP');
      }
      if (/atteint le niveau demandé pour gagner des? rl coins/i.test(value)) {
        node.nodeValue = value.replace(/atteint le niveau demandé pour gagner des? rl coins/gi, 'Atteint le niveau demandé pour gagner de l’XP');
      }
    });
  }

  function apply() {
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
  }).observe(document.documentElement, { childList: true, subtree: true });
})();
