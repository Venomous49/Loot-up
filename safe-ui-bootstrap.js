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
  const hair = {
    male: [
      ['male_textured','Texturé'],
      ['male_short','Court classique'],
      ['male_medium','Mi-long'],
      ['male_undercut','Dégradé'],
      ['male_slick','Coiffé arrière']
    ],
    female: [
      ['female_long','Long lisse'],
      ['female_wavy','Ondulé'],
      ['female_bob','Carré'],
      ['female_ponytail','Queue attachée'],
      ['female_short','Court moderne']
    ]
  };

  const state = {
    gender: 'male',
    skin: 'medium',
    hairColor: 'brown',
    hairStyle: 'male_textured'
  };

  const isTestOpen = () => document.body.classList.contains('creator-test-active');
  const assetPath = (style = state.hairStyle) =>
    `/assets/creator/${state.gender}/${state.skin}/${state.hairColor}/${style}.webp?v=fullbody23`;

  function syncSelection(id, field) {
    const root = $(id);
    if (!root) return;
    root.querySelectorAll('.choice').forEach(button => {
      button.classList.toggle('selected', button.dataset.value === state[field]);
    });
  }

  function renderHairChoices() {
    const root = $('hairStyleChoices');
    if (!root) return;
    const list = hair[state.gender] || hair.male;
    if (!list.some(([value]) => value === state.hairStyle)) state.hairStyle = list[0][0];
    root.innerHTML = list.map(([value,label]) => `
      <button type="button" class="choice hair-choice ${state.hairStyle === value ? 'selected' : ''}" data-value="${value}">
        <span class="hair-thumb"><img src="${assetPath(value)}" alt="${label}" style="width:100%;height:100%;object-fit:cover;object-position:center 8%" onerror="this.style.display='none';this.parentElement.textContent='×'"></span>
        <span>${label}</span>
      </button>`).join('');

    root.querySelectorAll('.choice').forEach(button => {
      button.addEventListener('click', event => {
        if (!isTestOpen()) return;
        event.preventDefault();
        event.stopImmediatePropagation();
        state.hairStyle = button.dataset.value;
        renderHairChoices();
        updatePreview();
      }, true);
    });
  }

  function updatePreview() {
    const preview = $('creatorPreview');
    if (!preview) return;
    const src = assetPath();
    preview.innerHTML = `
      <img class="creator-real-preview" src="${src}" alt="Aperçu Looter"
        style="display:block;width:100%;height:100%;object-fit:contain;object-position:center bottom;transform:none;filter:none;animation:none"
        onerror="this.style.display='none';this.nextElementSibling.style.display='grid'">
      <div class="creator-empty creator-asset-missing" style="display:none;height:100%;place-items:center;text-align:center;padding:30px">
        <div><strong>VARIANTE INDISPONIBLE</strong><br><span>Cette combinaison n'a pas pu être chargée.</span></div>
      </div>
      <div class="creator-live-badge"><b>NIVEAU 1</b><strong>DÉBUTANT</strong></div>`;
  }

  function resetCreator() {
    state.gender = 'male';
    state.skin = 'medium';
    state.hairColor = 'brown';
    state.hairStyle = 'male_textured';
    syncSelection('genderChoices','gender');
    syncSelection('skinChoices','skin');
    syncSelection('hairColorChoices','hairColor');
    renderHairChoices();
    updatePreview();
  }

  function openCreator(event) {
    if (event) {
      event.preventDefault();
      event.stopImmediatePropagation();
    }
    const modal = $('creatorModal');
    if (!modal) return;
    document.body.classList.add('creator-test-active');
    modal.classList.add('show');
    modal.style.display = 'grid';
    modal.setAttribute('aria-hidden','false');
    resetCreator();
  }

  function closeCreator() {
    const modal = $('creatorModal');
    document.body.classList.remove('creator-test-active');
    if (!modal) return;
    modal.classList.remove('show');
    modal.style.removeProperty('display');
    modal.setAttribute('aria-hidden','true');
  }

  function bindChoiceGroup(id, field) {
    const root = $(id);
    if (!root) return;
    root.querySelectorAll('.choice').forEach(button => {
      button.addEventListener('click', event => {
        if (!isTestOpen()) return;
        event.preventDefault();
        event.stopImmediatePropagation();
        state[field] = button.dataset.value;
        if (field === 'gender') state.hairStyle = state.gender === 'female' ? 'female_long' : 'male_textured';
        syncSelection(id, field);
        renderHairChoices();
        updatePreview();
      }, true);
    });
  }

  function restoreEvolution() {
    const grid = $('evolutionGrid');
    if (!grid || grid.children.length) return;
    grid.innerHTML = stages.map(([slug,name,level], i) => `
      <div class="evolution-card ${i === 0 ? 'unlocked' : 'locked'}">
        <div class="evolution-character">
          <img class="evolution-silhouette" src="/silhouettes/${slug}.png?v=10" alt="${name}">
        </div>
        <div class="evolution-name"><span>NIVEAU ${level}</span><br><b>${name}</b><br><small>${i===0?'Niveau actuel':'Évolution à découvrir'}</small></div>
      </div>`).join('');
    const next = $('nextEvolutionShadow');
    if (next && !next.children.length) next.innerHTML = '<img class="next-silhouette" src="/silhouettes/05-debrouillard.png?v=10" alt="DÉBROUILLARD">';
  }

  function init() {
    const button = $('creatorTestButton');
    if (button) button.addEventListener('click', openCreator, true);

    bindChoiceGroup('genderChoices','gender');
    bindChoiceGroup('skinChoices','skin');
    bindChoiceGroup('hairColorChoices','hairColor');

    const save = $('saveAvatar');
    if (save) {
      save.addEventListener('click', event => {
        if (!isTestOpen()) return;
        event.preventDefault();
        event.stopImmediatePropagation();
        alert(`TEST OK\nSexe : ${state.gender}\nTeint : ${state.skin}\nCheveux : ${state.hairColor}\nCoiffure : ${state.hairStyle}\n\nRien n'a été enregistré.`);
      }, true);
    }

    const modal = $('creatorModal');
    if (modal) {
      modal.addEventListener('click', event => {
        if (isTestOpen() && event.target === modal) closeCreator();
      });
    }
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && isTestOpen()) closeCreator();
    });

    restoreEvolution();
    if (new URLSearchParams(location.search).get('creatorTest') === '1') openCreator();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, {once:true});
  else init();
})();
