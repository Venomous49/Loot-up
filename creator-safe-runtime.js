/* Rise Looter creator runtime v11
   Canonical matrix runtime: every visible creator state maps to one complete
   pre-rendered WebP asset. No skin/hair overlays, filters, tint blocks or
   compositing are used at runtime. */
(() => {
  const ROOT = '/assets/creator';
  const FEMALE = ['female_long','female_wavy','female_bob','female_ponytail','female_short'];
  const MALE = ['male_textured','male_short','male_medium','male_undercut','male_slick'];
  const SKINS = new Set(['light','warm','medium','deep','dark']);
  const COLOURS = new Set(['black','brown','blond','red','purple']);

  function stylesForGender(gender = avatarDraft.gender) {
    return gender === 'female' ? FEMALE : MALE;
  }

  function normalizedState(state = avatarDraft, style = state.hairStyle) {
    const gender = state?.gender === 'female' ? 'female' : 'male';
    const skin = SKINS.has(state?.skin) ? state.skin : 'medium';
    const hairColor = COLOURS.has(state?.hairColor) ? state.hairColor : 'brown';
    const styles = stylesForGender(gender);
    const hairStyle = styles.includes(style) ? style : styles[0];
    return { gender, skin, hairColor, hairStyle };
  }

  function matrixPath(state = avatarDraft, style = state.hairStyle) {
    const s = normalizedState(state, style);
    return `${ROOT}/${s.gender}/${s.skin}/${s.hairColor}/${s.hairStyle}.webp`;
  }

  function fallbackPath(state = avatarDraft) {
    const s = normalizedState(state);
    return matrixPath(s, stylesForGender(s.gender)[0]);
  }

  function setSave(enabled) {
    const button = document.getElementById('saveAvatar');
    if (button) button.disabled = !enabled;
  }

  function normalizeDraftStyle() {
    const styles = stylesForGender();
    if (!styles.includes(avatarDraft.hairStyle)) avatarDraft.hairStyle = styles[0];
    return avatarDraft.hairStyle;
  }

  function updateCreator() {
    const root = document.getElementById('creatorPreview');
    if (!root || typeof avatarDraft === 'undefined') return;

    normalizeDraftStyle();
    const requested = matrixPath();
    const fallback = fallbackPath();
    root.innerHTML = `<img class="creator-real-preview" src="${requested}" alt="Aperçu Looter" data-fallback="${fallback}" data-tried-fallback="0"><div class="creator-asset-missing" hidden><strong>APERÇU INDISPONIBLE</strong></div><div class="creator-live-badge"><b>NIVEAU 1</b><strong>DÉBUTANT</strong></div>`;

    const img = root.querySelector('.creator-real-preview');
    const missing = root.querySelector('.creator-asset-missing');
    setSave(false);

    img.onload = () => {
      setSave(img.dataset.triedFallback !== '1');
    };

    img.onerror = () => {
      const fallbackURL = new URL(fallback, location.href).href;
      if (img.dataset.triedFallback === '0' && img.src !== fallbackURL && requested !== fallback) {
        img.dataset.triedFallback = '1';
        img.src = fallback;
        return;
      }
      img.hidden = true;
      missing.hidden = false;
      setSave(false);
    };
  }

  function renderHair() {
    if (typeof avatarDraft === 'undefined') return;
    normalizeDraftStyle();
    const root = document.getElementById('hairStyleChoices');
    if (!root) return;

    const styles = stylesForGender();
    const labels = avatarDraft.gender === 'female'
      ? ['Longue','Ondulée','Carré','Queue-de-cheval','Courte']
      : ['Texturée','Courte','Mi-longue','Undercut','Plaquée'];

    root.innerHTML = styles.map((value, index) => {
      const src = matrixPath(avatarDraft, value);
      const selected = avatarDraft.hairStyle === value ? 'selected' : '';
      return `<button type="button" class="choice hair-choice ${selected}" data-value="${value}"><span class="hair-thumb"><img src="${src}" alt="${labels[index]}"></span><span>${labels[index]}</span></button>`;
    }).join('');

    root.querySelectorAll('.hair-choice').forEach(button => {
      const img = button.querySelector('img');
      img.onerror = () => {
        if (img.dataset.triedFallback === '1') return;
        img.dataset.triedFallback = '1';
        img.src = fallbackPath();
      };
      button.onclick = () => {
        avatarDraft.hairStyle = button.dataset.value;
        renderHair();
        updateCreator();
      };
    });
  }

  function profileState(profile) {
    const gender = profile?.avatar_gender === 'female' ? 'female' : 'male';
    const styles = stylesForGender(gender);
    return normalizedState({
      gender,
      skin: profile?.avatar_skin || 'medium',
      hairColor: profile?.avatar_hair_color || 'brown',
      hairStyle: profile?.avatar_hair_style || styles[0],
    });
  }

  function beginnerPath(profile) {
    const state = profileState(profile);
    return matrixPath(state, state.hairStyle);
  }

  function install() {
    if (typeof avatarDraft === 'undefined') return;

    window.creatorAssetPath = matrixPath;
    window.creatorFallbackPath = (gender = avatarDraft.gender, skin = avatarDraft.skin, hairColor = avatarDraft.hairColor) => {
      const styles = stylesForGender(gender);
      return matrixPath({ gender, skin, hairColor, hairStyle: styles[0] }, styles[0]);
    };
    window.updateCreatorPreview = updateCreator;
    window.renderHairChoices = renderHair;

    const previousAssetPath = window.assetPath;
    if (typeof previousAssetPath === 'function') {
      window.assetPath = (profile, stage) => stage === 0 ? beginnerPath(profile) : previousAssetPath(profile, stage);
    }

    ['genderChoices','skinChoices','hairColorChoices'].forEach(id => {
      const root = document.getElementById(id);
      if (!root) return;
      root.addEventListener('click', () => {
        setTimeout(() => {
          normalizeDraftStyle();
          renderHair();
          updateCreator();
        }, 0);
      }, true);
    });

    renderHair();
    updateCreator();

    if (window.currentProfile && document.getElementById('mainCharacter') && typeof window.characterHTML === 'function') {
      document.getElementById('mainCharacter').innerHTML = window.characterHTML(window.currentProfile, 0);
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, { once: true });
  else install();
})();
