/* Rise Looter creator stable runtime v6
   Direct full WebP matrix: gender / skin / hair color / hairstyle.
   No canvas, overlays or destructive recolouring. */
(() => {
  const ROOT='/assets/creator/';
  const FEMALE=new Set(['female_long','female_wavy','female_bob','female_ponytail','female_short']);
  const SKINS=new Set(['light','warm','medium','deep','dark']);
  const COLORS=new Set(['black','brown','blond','red','purple']);
  const SKIN_ALIAS={fair:'light',tan:'warm',olive:'medium',brown:'deep',deep:'deep'};

  const skin=v=>SKINS.has(v)?v:(SKIN_ALIAS[v]||'medium');
  const color=v=>COLORS.has(v)?v:'brown';
  function style(){
    const list=avatarDraft.gender==='female'?femaleHair:maleHair;
    if(!list.some(([v])=>v===avatarDraft.hairStyle)) avatarDraft.hairStyle=list[0][0];
    return avatarDraft.hairStyle;
  }
  function srcFor(s){
    const gender=FEMALE.has(s)?'female':'male';
    return `${ROOT}${gender}/${skin(avatarDraft.skin)}/${color(avatarDraft.hairColor)}/${s}.webp`;
  }
  function saveEnabled(ok){const b=document.getElementById('saveAvatar');if(b)b.disabled=!ok;}
  function update(){
    const p=document.getElementById('creatorPreview');
    if(!p||typeof avatarDraft==='undefined')return;
    const s=style(),src=srcFor(s);
    p.innerHTML=`<img class="creator-real-preview" src="${src}" alt="Aperçu Looter"><div class="creator-asset-missing" hidden><strong>APERÇU INDISPONIBLE</strong></div><div class="creator-live-badge"><b>NIVEAU 1</b><strong>DÉBUTANT</strong></div>`;
    const img=p.querySelector('img'); const miss=p.querySelector('.creator-asset-missing');
    saveEnabled(false);
    img.onload=()=>saveEnabled(true);
    img.onerror=()=>{img.hidden=true;miss.hidden=false;saveEnabled(false);console.error('[creator v6]',src);};
  }
  function renderHair(){
    if(typeof avatarDraft==='undefined')return;
    const list=avatarDraft.gender==='female'?femaleHair:maleHair; style();
    const root=document.getElementById('hairStyleChoices'); if(!root)return;
    root.innerHTML=list.map(([v,label])=>`<button type="button" class="choice hair-choice ${avatarDraft.hairStyle===v?'selected':''}" data-value="${v}"><span class="hair-thumb"><img src="${srcFor(v)}" alt=""></span><span>${label}</span></button>`).join('');
    root.querySelectorAll('.hair-choice').forEach(btn=>{
      const img=btn.querySelector('img'); img.onerror=()=>{img.hidden=true;};
      btn.onclick=()=>{avatarDraft.hairStyle=btn.dataset.value;renderHair();update();};
    });
  }
  function refresh(){renderHair();update();}
  function install(){
    window.updateCreatorPreview=update; window.renderHairChoices=renderHair;
    ['genderChoices','skinChoices','hairColorChoices'].forEach(id=>{
      const root=document.getElementById(id); if(root) root.addEventListener('click',()=>setTimeout(refresh,0),true);
    });
    refresh();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();
