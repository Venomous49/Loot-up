(() => {
  'use strict';

  const VERSION='stage-render-20260822-4';
  const MALE_STAGE_ASSETS = [
    `/01-debutant.webp?v=${VERSION}`,`/05-debrouillard.webp?v=${VERSION}`,`/10-chasseur.webp?v=${VERSION}`,`/15-hustler.webp?v=${VERSION}`,
    `/20-pro.webp?v=${VERSION}`,`/30-elite.webp?v=${VERSION}`,`/40-cyber-looter.webp?v=${VERSION}`,`/50-rise-looter.webp?v=${VERSION}`
  ];
  const FEMALE_STAGE_ASSETS = [
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

  const sharpCache=new Map();
  function enhance(img){
    if(!img||img.dataset.stageEnhance==='1')return;
    const run=()=>{
      if(img.dataset.stageEnhance==='1'||!img.naturalWidth||!img.naturalHeight)return;
      img.dataset.stageEnhance='1';
      const original=img.currentSrc||img.src;
      if(img.naturalHeight>=600)return;
      if(sharpCache.has(original)){img.src=sharpCache.get(original);return;}
      const work=()=>{
        try{
          const scale=Math.max(2,Math.min(3,Math.ceil(900/img.naturalHeight)));
          const w=img.naturalWidth*scale,h=img.naturalHeight*scale;
          const c=document.createElement('canvas');c.width=w;c.height=h;
          const x=c.getContext('2d',{willReadFrequently:true});x.imageSmoothingEnabled=true;x.imageSmoothingQuality='high';x.drawImage(img,0,0,w,h);
          const d=x.getImageData(0,0,w,h),s=d.data,o=new Uint8ClampedArray(s);
          for(let y=1;y<h-1;y++)for(let xx=1;xx<w-1;xx++){
            const i=(y*w+xx)*4;
            for(let ch=0;ch<3;ch++){
              const v=1.32*s[i+ch]-.08*(s[i-4+ch]+s[i+4+ch]+s[i-w*4+ch]+s[i+w*4+ch]);
              o[i+ch]=Math.max(0,Math.min(255,v));
            }
          }
          d.data.set(o);x.putImageData(d,0,0);
          const url=c.toDataURL('image/webp',.98);sharpCache.set(original,url);img.src=url;
        }catch(_){ }
      };
      if('requestIdleCallback'in window)requestIdleCallback(work,{timeout:500});else setTimeout(work,0);
    };
    if(img.complete)run();else img.addEventListener('load',run,{once:true});
  }

  function mark(root=document){
    root.querySelectorAll?.('img').forEach(img=>{
      const src=img.getAttribute('src')||img.currentSrc||'';
      const match=[...MALE_STAGE_ASSETS,...FEMALE_STAGE_ASSETS].some(a=>src.includes(a.split('?')[0]));
      if(match){img.classList.add('stage-art-clean');img.decoding='async';enhance(img);}
    });
  }
  mark();
  new MutationObserver(()=>mark()).observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['src']});
})();