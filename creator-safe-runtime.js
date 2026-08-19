/* Rise Looter creator runtime v2
   Single source of truth: the already validated 250 HD presets.
   No canvas recolouring, no masks, no synthetic fallback, no generated fragments. */
(() => {
  const ROOT = '/assets/creator/';
  const VALID_GENDERS = new Set(['male','female']);
  const VALID_SKINS = new Set(['light','warm','medium','deep','dark']);
  const VALID_COLORS = new Set(['black','brown','blond','red','purple']);

  function presetPath(style, gender, skin, hairColor) {
    const g = VALID_GENDERS.has(gender) ? gender : 'male';
    const s = VALID_SKINS.has(skin) ? skin : 'medium';
    const c = VALID_COLORS.has(hairColor) ? hairColor : 'brown';
    return `${ROOT}${g}/${s}/${c}/${style}.webp`;
  }

  function currentStyle() {
    const list = avatarDraft.gender === 'female' ? femaleHair : maleHair;
    if (!list.some(([v]) => v === avatarDraft.hairStyle)) avatarDraft.hairStyle = list[0][0];
    return avatarDraft.hairStyle;
  }

  function safeUpdateCreatorPreview() {
    const preview = document.getElementById('creatorPreview');
    if (!preview || typeof avatarDraft === 'undefined') return;
    const style = currentStyle();
    const src = presetPath(style, avatarDraft.gender, avatarDraft.skin, avatarDraft.hairColor);
    preview.innerHTML = `<img class="creator-real-preview" src="${src}" alt="Aperçu Looter"><div class="creator-asset-missing" style="display:none"><strong>Aperçu indisponible</strong><span>Ce preset validé n'a pas pu être chargé.</span></div>`;
    const img = preview.querySelector('img');
    const missing = preview.querySelector('.creator-asset-missing');
    img.addEventListener('load', () => {
      const save = document.getElementById('saveAvatar');
      if (save) save.disabled = false;
    }, {once:true});
    img.addEventListener('error', () => {
      img.style.display = 'none';
      missing.style.display = 'grid';
      const save = document.getElementById('saveAvatar');
      if (save) save.disabled = true;
      console.error('Missing validated creator preset:', src);
    }, {once:true});
  }

  function safeRenderHairChoices() {
    if (typeof avatarDraft === 'undefined') return;
    const list = avatarDraft.gender === 'female' ? femaleHair : maleHair;
    currentStyle();
    const root = document.getElementById('hairStyleChoices');
    if (!root) return;
    root.innerHTML = list.map(([value,label]) => {
      const src = presetPath(value, avatarDraft.gender, avatarDraft.skin, avatarDraft.hairColor);
      return `<button type="button" class="choice hair-choice ${avatarDraft.hairStyle===value?'selected':''}" data-value="${value}"><span class="hair-thumb"><img src="${src}" alt="${label}"></span><span>${label}</span></button>`;
    }).join('');
    root.querySelectorAll('.hair-choice').forEach(btn => btn.addEventListener('click', () => {
      avatarDraft.hairStyle = btn.dataset.value;
      root.querySelectorAll('.hair-choice').forEach(b => b.classList.toggle('selected', b === btn));
      safeUpdateCreatorPreview();
    }));
  }

  function install() {
    window.updateCreatorPreview = safeUpdateCreatorPreview;
    window.renderHairChoices = safeRenderHairChoices;
    const creator = document.getElementById('creatorModal');
    if (!creator) return;
    ['genderChoices','skinChoices','hairColorChoices'].forEach(id => {
      const root = document.getElementById(id);
      if (!root) return;
      root.addEventListener('click', () => setTimeout(() => {
        safeRenderHairChoices();
        safeUpdateCreatorPreview();
      }, 0), true);
    });
    safeRenderHairChoices();
    safeUpdateCreatorPreview();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, {once:true});
  else install();
})();
