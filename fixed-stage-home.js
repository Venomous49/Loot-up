(() => {
  'use strict';
  const VERSION='native-hd-20260822-1';
  const MALE_STAGE_ASSETS=[
    `/01-debutant.webp?v=${VERSION}`,`/05-debrouillard.webp?v=${VERSION}`,`/10-chasseur.webp?v=${VERSION}`,`/15-hustler.webp?v=${VERSION}`,
    `/20-pro.webp?v=${VERSION}`,`/30-elite.webp?v=${VERSION}`,`/40-cyber-looter.webp?v=${VERSION}`,`/50-rise-looter.webp?v=${VERSION}`
  ];
  const FEMALE_STAGE_ASSETS=[
    `/female-01-debutant.webp?v=${VERSION}`,`/female-05-debrouillard.webp?v=${VERSION}`,`/female-10-chasseur.webp?v=${VERSION}`,`/female-15-hustler.webp?v=${VERSION}`,
    `/female-20-pro.webp?v=${VERSION}`,`/female-30-elite.webp?v=${VERSION}`,`/female-40-cyber-looter.webp?v=${VERSION}`,`/female-50-rise-looter.webp?v=${VERSION}`
  ];
  if(typeof window.assetPath==='function'){
    window.assetPath=function(profile,stage){
      const i=Math.max(0,Math.min(Number(stage)||0,7));
      return profile?.avatar_gender==='female'?FEMALE_STAGE_ASSETS[i]:MALE_STAGE_ASSETS[i];
    };
  }
  const style=document.createElement('style');
  style.id='fixed-stage-home-art-style';
  style.textContent=`
    #home .hero .scene-clean-image.stage-art-clean,.evolution-real.stage-art-clean{
      width:100%!important;height:100%!important;max-width:100%!important;max-height:100%!important;
      object-fit:contain!important;object-position:center 55%!important;opacity:1!important;
      padding:8px 6px 2px!important;box-sizing:border-box!important;image-rendering:auto!important;
      backface-visibility:hidden!important;
    }
    #home .hero .scene-clean-image.stage-art-clean{transform:translateY(4px)!important;filter:none!important}
    .evolution-real.stage-art-clean{transform:translateY(2px)!important;filter:none!important}
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
  mark();
  new MutationObserver(()=>mark()).observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['src']});
})();