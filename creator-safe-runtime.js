/* Rise Looter creator runtime v8
   One fixed scene for every hairstyle: the character is isolated with the
   existing per-style person mask and composited over creator_background_master.
*/
(() => {
  const ROOT='/assets/creator_sources/';
  const BG=`${ROOT}creator_background_master.png`;
  const MASK_ROOT=`${ROOT}person_masks/`;
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
  function maskSource(style){ return `${MASK_ROOT}${style}.png`; }
  function fallbackSource(){
    return avatarDraft.gender==='female' ? `${ROOT}female_long_brown_natural.png` : `${ROOT}male_textured_brown_natural.png`;
  }
  function maskedImage(src,style,cls='creator-real-preview'){
    const mask=maskSource(style);
    return `<img class="${cls}" src="${src}" alt="" style="-webkit-mask-image:url('${mask}');mask-image:url('${mask}');-webkit-mask-size:100% 100%;mask-size:100% 100%;-webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;-webkit-mask-position:center;mask-position:center">`;
  }
  function setSave(ok){ const b=document.getElementById('saveAvatar'); if(b) b.disabled=!ok; }

  function updateCreator(){
    const p=document.getElementById('creatorPreview');
    if(!p||typeof avatarDraft==='undefined') return;
    const s=normalizeStyle();
    const src=cleanSource(s,avatarDraft.hairColor);
    const fallback=fallbackSource();
    p.innerHTML=`<div class="creator-fixed-bg"></div>${maskedImage(src,s)}<div class="creator-asset-missing" hidden><strong>APERÇU INDISPONIBLE</strong></div><div class="creator-live-badge"><b>NIVEAU 1</b><strong>DÉBUTANT</strong></div>`;
    const bg=p.querySelector('.creator-fixed-bg');
    bg.style.backgroundImage=`url('${BG}?bg=v1')`;
    const img=p.querySelector('.creator-real-preview');
    const miss=p.querySelector('.creator-asset-missing');
    setSave(false);
    img.onload=()=>setSave(true);
    img.onerror=()=>{
      if(!img.dataset.fallbackUsed){ img.dataset.fallbackUsed='1'; img.src=fallback; return; }
      img.hidden=true; miss.hidden=false; setSave(false);
    };
  }

  function renderHair(){
    if(typeof avatarDraft==='undefined') return;
    const list=listForGender(); normalizeStyle();
    const root=document.getElementById('hairStyleChoices'); if(!root) return;
    root.innerHTML=list.map(([v,label])=>{
      const src=cleanSource(v,avatarDraft.hairColor);
      const mask=maskSource(v);
      return `<button type="button" class="choice hair-choice ${avatarDraft.hairStyle===v?'selected':''}" data-value="${v}"><span class="hair-thumb" style="background-image:url('${BG}?bg=v1')"><img src="${src}" alt="" style="-webkit-mask-image:url('${mask}');mask-image:url('${mask}');-webkit-mask-size:100% 100%;mask-size:100% 100%;-webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;-webkit-mask-position:center;mask-position:center"></span><span>${label}</span></button>`;
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
    window.creatorMaskPath=(style)=>maskSource(style);
    window.creatorFixedBackground=BG;
    const oldAssetPath=window.assetPath;
    window.assetPath=(profile,stage)=> stage===0 ? cleanBeginnerPath(profile) : oldAssetPath(profile,stage);
    ['genderChoices','skinChoices','hairColorChoices'].forEach(id=>{
      const root=document.getElementById(id);
      if(root) root.addEventListener('click',()=>setTimeout(()=>{renderHair();updateCreator();},0),true);
    });
    renderHair(); updateCreator();
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',install,{once:true}); else install();
})();
