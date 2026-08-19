/* Rise Looter creator stable runtime v5
   Uses the full WebP matrix directly: gender / skin / hair color / hairstyle.
   No canvas, no overlays, no destructive recolouring. */
(() => {
  const ROOT='/assets/creator/';
  const FEMALE=new Set(['female_long','female_wavy','female_bob','female_ponytail','female_short']);
  const SKINS=['light','warm','medium','deep','dark'];
  const COLORS=['black','brown','blond','red','purple'];

  function normalizeSkin(v){
    if(SKINS.includes(v)) return v;
    const aliases={fair:'light',tan:'warm',olive:'medium',brown:'deep,',deep:'dark'};
    return aliases[v]||'medium';
  }
  function normalizeColor(v){return COLORS.includes(v)?v:'brown';}
  function normalizeStyle(){
    const list=avatarDraft.gender==='female'?femaleHair:maleHair;
    if(!list.some(([v])=>v===avatarDraft.hairStyle)) avatarDraft.hairStyle=list[0][0];
    return avatarDraft.hairStyle;
  }
  function pathFor(style,skin,color){
    const gender=FEMALE.has(style)?'female':'male';
    return `${ROOT}${gender}/${normalizeSkin(skin)}/${normalizeColor(color)}/${style}.webp`;
  }
  function setSave(ok){const b=document.getElementById('saveAvatar');if(b)b.disabled=!ok;}

  function update(){
    const preview=document.getElementById('creatorPreview');
    if(!preview||typeof avatarDraft==='undefined')return;
    const style=normalizeStyle();
    const src=pathFor(style,avatarDraft.skin,avatarDraft.hairColor);
    preview.innerHTML=`<img class="creator-real-preview" src="${src}" alt="Aperçu Looter"><div class="creator-asset-missing" style="display:none"><strong>APERÇU INDISPONIBLE</strong><span>Asset manquant : ${src}</span></div><div class="creator-live-badge"><b>NIVEAU 1</b><strong>DÉBUTANT</strong></div>`;
    const img=preview.querySelector('.creator-real-preview');
    const miss=preview.querySelector('.creator-asset-missing');
    setSave(false);
    img.onload=()=>setSave(true);
    img.onerror=()=>{img.style.display='none';miss.style.display='grid';setSave(false);console.error('[creator v5] missing',src);};
  }

  function renderHair(){
    if(typeof avatarDraft==='undefined')return;
    const list=avatarDraft.gender==='female'?femaleHair:maleHair;
    normalizeStyle();
    const root=document.getElementById('hairStyleChoices');
    if(!root)return;
    root.innerHTML=list.map(([value,label])=>{
      const src=pathFor(value,avatarDraft.skin,avatarDraft.hairColor);
      return `<button type="button" class="choice hair-choice ${avatarDraft.hairStyle===value?'selected':''}" data-value="${value}"><span class="hair-thumb"><img src="${src}" alt="${label}"></span><span>${label}</span></button>`;
    }).join('');
    root.querySelectorAll('.hair-choice').forEach(btn=>{
      const img=btn.querySelector('img');
      img.onerror=()=>{img.style.visibility='hidden';console.error('[creator v5] thumb missing',img.src);};
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
