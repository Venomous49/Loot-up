/* Rise Looter creator stable runtime v2
   Branch-only validation runtime. Uses existing full-frame source images directly.
   No canvas segmentation/recolouring: prevents eaten bodies, face artifacts and clothing overlays. */
(() => {
  const ROOT='/assets/creator_sources/';
  const FEMALE=new Set(['female_long','female_wavy','female_bob','female_ponytail','female_short']);
  const MALE_NATURAL=new Set(['male_medium','male_short','male_textured']);

  function fileFor(style,color){
    const c=color==='black'?'brown':color;
    if(FEMALE.has(style)){
      if(style==='female_wavy' && (color==='black'||c==='brown')) return 'female_wavy.png';
      if(color==='black') return `${style}_brown_natural.png`;
      return `${style}_${c}_natural.png`;
    }
    if(MALE_NATURAL.has(style)){
      if(style==='male_textured' && color==='black') return 'male_textured_brown_natural.png';
      if(color==='black') return `${style}_brown_natural.png`;
      return `${style}_${c}_natural.png`;
    }
    return `${style}_clean.png`;
  }
  function pathFor(style,color){return ROOT+fileFor(style,color);}
  function normalizeStyle(){
    const list=avatarDraft.gender==='female'?femaleHair:maleHair;
    if(!list.some(([v])=>v===avatarDraft.hairStyle)) avatarDraft.hairStyle=list[0][0];
    return avatarDraft.hairStyle;
  }
  function setSave(ok){const b=document.getElementById('saveAvatar');if(b)b.disabled=!ok;}

  function update(){
    const preview=document.getElementById('creatorPreview');
    if(!preview||typeof avatarDraft==='undefined')return;
    const style=normalizeStyle();
    const src=pathFor(style,avatarDraft.hairColor);
    preview.innerHTML=`<img class="creator-real-preview" src="${src}" alt="Aperçu Looter"><div class="creator-asset-missing" style="display:none"><strong>APERÇU INDISPONIBLE</strong><span>Cette source doit être corrigée avant publication.</span></div><div class="creator-live-badge"><b>NIVEAU 1</b><strong>DÉBUTANT</strong></div>`;
    const img=preview.querySelector('.creator-real-preview');
    const miss=preview.querySelector('.creator-asset-missing');
    setSave(false);
    img.onload=()=>setSave(true);
    img.onerror=()=>{img.style.display='none';miss.style.display='grid';setSave(false);console.error('[creator stable] missing',src);};
  }

  function renderHair(){
    if(typeof avatarDraft==='undefined')return;
    const list=avatarDraft.gender==='female'?femaleHair:maleHair;
    normalizeStyle();
    const root=document.getElementById('hairStyleChoices');
    if(!root)return;
    root.innerHTML=list.map(([value,label])=>`<button type="button" class="choice hair-choice ${avatarDraft.hairStyle===value?'selected':''}" data-value="${value}"><span class="hair-thumb"><img src="${pathFor(value,avatarDraft.hairColor)}" alt="${label}"></span><span>${label}</span></button>`).join('');
    root.querySelectorAll('.hair-choice').forEach(btn=>{
      const img=btn.querySelector('img');
      img.onerror=()=>{img.style.visibility='hidden';};
      btn.onclick=()=>{avatarDraft.hairStyle=btn.dataset.value;renderHair();update();};
    });
  }

  function refresh(){renderHair();update();}
  function install(){
    window.updateCreatorPreview=update;
    window.renderHairChoices=renderHair;
    ['genderChoices','skinChoices','hairColorChoices'].forEach(id=>{
      const root=document.getElementById(id);if(!root)return;
      root.addEventListener('click',()=>setTimeout(refresh,0),true);
    });
    refresh();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();
