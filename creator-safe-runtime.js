/* Rise Looter creator runtime v7
   Visual stability first: use the clean full-frame hairstyle masters directly.
   Keeps the validated street background and full-body framing intact.
   Skin selection remains stored in avatarDraft and will be used by evolution assets,
   but is never allowed to corrupt the base creator image. */
(() => {
  const ROOT='/assets/creator_sources/';
  const FEMALE=new Set(['female_long','female_wavy','female_bob','female_ponytail','female_short']);
  const MALE_NATURAL=new Set(['male_textured','male_short','male_medium']);

  function listForGender(){ return avatarDraft.gender==='female' ? femaleHair : maleHair; }
  function normalizeStyle(){
    const list=listForGender();
    if(!list.some(([v])=>v===avatarDraft.hairStyle)) avatarDraft.hairStyle=list[0][0];
    return avatarDraft.hairStyle;
  }
  function cleanSource(style,color){
    const c=color==='black'?'brown':color;
    if(FEMALE.has(style)){
      if(style==='female_wavy' && (color==='black'||c==='brown')) return `${ROOT}female_wavy.png`;
      if(color==='black') return `${ROOT}${style}_brown_natural.png`;
      return `${ROOT}${style}_${c}_natural.png`;
    }
    if(MALE_NATURAL.has(style)){
      if(color==='black') return `${ROOT}${style}_brown_natural.png`;
      return `${ROOT}${style}_${c}_natural.png`;
    }
    return `${ROOT}${style}_clean.png`;
  }
  function fallbackSource(){
    return avatarDraft.gender==='female' ? `${ROOT}female_long_brown_natural.png` : `${ROOT}male_textured_brown_natural.png`;
  }
  function setSave(ok){ const b=document.getElementById('saveAvatar'); if(b) b.disabled=!ok; }

  function updateCreator(){
    const p=document.getElementById('creatorPreview');
    if(!p||typeof avatarDraft==='undefined') return;
    const s=normalizeStyle();
    const src=cleanSource(s,avatarDraft.hairColor);
    const fallback=fallbackSource();
    p.innerHTML=`<img class="creator-real-preview" src="${src}" alt="Aperçu Looter" data-fallback="${fallback}" data-fallback-used="0"><div class="creator-asset-missing" hidden><strong>APERÇU INDISPONIBLE</strong></div><div class="creator-live-badge"><b>NIVEAU 1</b><strong>DÉBUTANT</strong></div>`;
    const img=p.querySelector('.creator-real-preview');
    const miss=p.querySelector('.creator-asset-missing');
    setSave(false);
    img.onload=()=>setSave(true);
    img.onerror=()=>{
      if(img.dataset.fallbackUsed==='0' && img.src!==new URL(fallback,location.href).href){
        img.dataset.fallbackUsed='1';
        img.src=fallback;
        return;
      }
      img.hidden=true; miss.hidden=false; setSave(false);
    };
  }

  function renderHair(){
    if(typeof avatarDraft==='undefined') return;
    const list=listForGender(); normalizeStyle();
    const root=document.getElementById('hairStyleChoices'); if(!root) return;
    root.innerHTML=list.map(([v,label])=>{
      const src=cleanSource(v,avatarDraft.hairColor);
      return `<button type="button" class="choice hair-choice ${avatarDraft.hairStyle===v?'selected':''}" data-value="${v}"><span class="hair-thumb"><img src="${src}" alt=""></span><span>${label}</span></button>`;
    }).join('');
    root.querySelectorAll('.hair-choice').forEach(btn=>{
      const img=btn.querySelector('img');
      img.onerror=()=>{ img.src=fallbackSource(); };
      btn.onclick=()=>{ avatarDraft.hairStyle=btn.dataset.value; renderHair(); updateCreator(); };
    });
  }

  function cleanBeginnerPath(profile){
    const gender=profile?.avatar_gender||'male';
    const color=profile?.avatar_hair_color||'brown';
    const defaultStyle=gender==='female'?'female_long':'male_textured';
    const style=profile?.avatar_hair_style||defaultStyle;
    const previousGender=avatarDraft.gender, previousColor=avatarDraft.hairColor;
    avatarDraft.gender=gender; avatarDraft.hairColor=color;
    const src=cleanSource(style,color);
    avatarDraft.gender=previousGender; avatarDraft.hairColor=previousColor;
    return src;
  }

  function install(){
    window.updateCreatorPreview=updateCreator;
    window.renderHairChoices=renderHair;
    window.creatorAssetPath=(state=avatarDraft,style=state.hairStyle)=>{
      const oldG=avatarDraft.gender,oldC=avatarDraft.hairColor;
      avatarDraft.gender=state.gender; avatarDraft.hairColor=state.hairColor;
      const src=cleanSource(style,state.hairColor);
      avatarDraft.gender=oldG; avatarDraft.hairColor=oldC;
      return src;
    };
    const oldAssetPath=window.assetPath;
    window.assetPath=(profile,stage)=> stage===0 ? cleanBeginnerPath(profile) : oldAssetPath(profile,stage);
    ['genderChoices','skinChoices','hairColorChoices'].forEach(id=>{
      const root=document.getElementById(id);
      if(root) root.addEventListener('click',()=>setTimeout(()=>{renderHair();updateCreator();},0),true);
    });
    renderHair(); updateCreator();
    if(window.currentProfile && document.getElementById('mainCharacter')){
      document.getElementById('mainCharacter').innerHTML=window.characterHTML(window.currentProfile,0);
    }
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',install,{once:true}); else install();
})();
