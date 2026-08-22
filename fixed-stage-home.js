(() => {
  'use strict';
  const VERSION='native-hd-20260822-2';
  const MALE_STAGE_ASSETS=[
    `/01-debutant.webp?v=${VERSION}`,`/05-debrouillard.webp?v=${VERSION}`,`/10-chasseur.webp?v=${VERSION}`,`/15-hustler.webp?v=${VERSION}`,
    `/20-pro.webp?v=${VERSION}`,`/30-elite.webp?v=${VERSION}`,`/40-cyber-looter.webp?v=${VERSION}`,`/50-rise-looter.webp?v=${VERSION}`
  ];
  const FEMALE_STAGE_ASSETS=[
    `/female-01-debutant.webp?v=${VERSION}`,`/female-05-debrouillard.webp?v=${VERSION}`,`/female-10-chasseur.webp?v=${VERSION}`,`/female-15-hustler.webp?v=${VERSION}`,
    `/female-20-pro.webp?v=${VERSION}`,`/female-30-elite.webp?v=${VERSION}`,`/female-40-cyber-looter.webp?v=${VERSION}`,`/female-50-rise-looter.webp?v=${VERSION}`
  ];
  const assetsFor=profile=>String(profile?.avatar_gender||'male').toLowerCase()==='female'?FEMALE_STAGE_ASSETS:MALE_STAGE_ASSETS;
  const fixedAssetPath=(profile,stage)=>assetsFor(profile)[Math.max(0,Math.min(Number(stage)||0,7))];
  window.assetPath=fixedAssetPath;

  const style=document.createElement('style');
  style.id='fixed-stage-home-art-style';
  style.textContent=`
    #home .hero #mainCharacter{display:block!important;visibility:visible!important;opacity:1!important;position:absolute!important;inset:0!important;width:100%!important;height:100%!important;overflow:hidden!important;z-index:1!important}
    #home .hero #mainCharacter .character-scene-clean{display:block!important;visibility:visible!important;position:absolute!important;inset:0!important;width:100%!important;height:100%!important;overflow:hidden!important}
    #home .hero #mainCharacter .scene-clean-image.stage-art-clean{display:block!important;visibility:visible!important;position:absolute!important;inset:0!important;width:100%!important;height:100%!important;max-width:none!important;max-height:none!important;object-fit:contain!important;object-position:68% 54%!important;opacity:1!important;padding:6px 8px 4px!important;box-sizing:border-box!important;transform:none!important;filter:none!important;animation:none!important;image-rendering:auto!important}
    #home .hero #mainCharacter .character-missing{display:none!important}
    .evolution-real.stage-art-clean{display:block!important;visibility:visible!important;width:100%!important;height:100%!important;max-width:none!important;max-height:none!important;object-fit:contain!important;object-position:center 54%!important;opacity:1!important;padding:3px!important;box-sizing:border-box!important;transform:none!important;filter:none!important;animation:none!important;image-rendering:auto!important}
    .evolution-card.locked .evolution-real.stage-art-clean{filter:brightness(0)!important;opacity:.86!important}
  `;
  document.head.appendChild(style);

  function mark(root=document){
    root.querySelectorAll?.('img').forEach(img=>{
      const src=img.getAttribute('src')||img.currentSrc||'';
      if([...MALE_STAGE_ASSETS,...FEMALE_STAGE_ASSETS].some(a=>src.includes(a.split('?')[0]))){
        img.classList.add('stage-art-clean');
        img.decoding='async';
      }
    });
  }

  function repairHome(){
    const holder=document.getElementById('mainCharacter');
    if(!holder)return;
    const profile=window.currentProfile||null;
    const level=Number(profile?.level||1);
    const levels=[1,5,10,15,20,30,40,50];
    let stage=0;levels.forEach((n,i)=>{if(level>=n)stage=i});
    const wanted=fixedAssetPath(profile,stage);
    let img=holder.querySelector('img.scene-clean-image');
    if(!img){
      holder.innerHTML=`<div class="character-scene-clean"><img class="scene-clean-image stage-art-clean" src="${wanted}" alt="Looter" decoding="async"></div>`;
      return;
    }
    const current=img.getAttribute('src')||'';
    if(!current.includes(wanted.split('?')[0]))img.src=wanted;
    img.style.display='block';
    img.classList.add('stage-art-clean');
    holder.querySelectorAll('.character-missing').forEach(el=>el.style.display='none');
  }

  function apply(){mark();repairHome()}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',apply,{once:true});else apply();
  let queued=false;
  new MutationObserver(()=>{if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;apply()})}).observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['src','style']});
})();