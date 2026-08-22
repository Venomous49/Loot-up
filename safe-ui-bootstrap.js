(() => {
  'use strict';
  const $=id=>document.getElementById(id); const VERSION='beginner-preview-20260822-4';
  const state={gender:'male'}; const isOpen=()=>document.body.classList.contains('creator-test-active');
  const fixedCharacter=()=>state.gender==='female'
    ? `/female-01-debutant.webp?v=${VERSION}`
    : `/01-debutant.webp?v=${VERSION}`;
  const syncGender=()=>{const r=$('genderChoices');if(r)r.querySelectorAll('.choice').forEach(b=>b.classList.toggle('selected',b.dataset.value===state.gender));};

  function renderHD(img){
    if(!img || img.dataset.hdRendered==='1') return;
    const run=()=>{
      if(img.dataset.hdRendered==='1' || !img.naturalWidth || !img.naturalHeight) return;
      img.dataset.hdRendered='1';
      try{
        const rect=img.getBoundingClientRect();
        const dpr=Math.min(window.devicePixelRatio||1,2);
        const targetH=Math.min(1600,Math.max(img.naturalHeight,1200,Math.ceil(rect.height*dpr*2)));
        const targetW=Math.max(1,Math.round(targetH*(img.naturalWidth/img.naturalHeight)));
        const c=document.createElement('canvas'); c.width=targetW;c.height=targetH;
        const x=c.getContext('2d',{willReadFrequently:true,alpha:true});
        x.imageSmoothingEnabled=true;x.imageSmoothingQuality='high';
        x.drawImage(img,0,0,targetW,targetH);
        const d=x.getImageData(0,0,targetW,targetH),s=d.data,o=new Uint8ClampedArray(s);
        const stride=targetW*4, amount=.14;
        for(let y=1;y<targetH-1;y++){
          for(let xx=1;xx<targetW-1;xx++){
            const i=y*stride+xx*4;
            for(let ch=0;ch<3;ch++){
              const center=s[i+ch];
              const v=(1+4*amount)*center-amount*(s[i-4+ch]+s[i+4+ch]+s[i-stride+ch]+s[i+stride+ch]);
              const contrasted=(v-128)*1.035+128;
              o[i+ch]=Math.max(0,Math.min(255,contrasted));
            }
          }
        }
        d.data.set(o);x.putImageData(d,0,0);
        img.src=c.toDataURL('image/png');
      }catch(_){ }
    };
    if(img.complete) run(); else img.addEventListener('load',run,{once:true});
  }

  function installTestOnlyStyle(){
    if(document.getElementById('creator-gender-only-test-style'))return;
    const steps=document.querySelectorAll('#creatorModal .creator-step');
    steps.forEach((step,index)=>step.dataset.creatorTestStep=String(index+1));
    const style=document.createElement('style');
    style.id='creator-gender-only-test-style';
    style.textContent=`
      body.creator-test-active #creatorModal [data-creator-test-step="2"],
      body.creator-test-active #creatorModal [data-creator-test-step="3"],
      body.creator-test-active #creatorModal [data-creator-test-step="4"]{display:none!important}
      body.creator-test-active #creatorPreview{overflow:hidden!important}
      body.creator-test-active #creatorPreview .creator-fixed-preview{display:flex!important;align-items:center!important;justify-content:center!important}
      body.creator-test-active #creatorPreview .creator-fixed-preview>img{
        width:100%!important;height:100%!important;max-width:100%!important;max-height:100%!important;
        object-fit:contain!important;object-position:center 56%!important;padding:12px 10px 4px!important;
        box-sizing:border-box!important;filter:none!important;opacity:1!important;transform:translateY(5px)!important;
        animation:none!important;image-rendering:auto!important;backface-visibility:hidden!important;
      }
    `;
    document.head.appendChild(style);
  }
  function updatePreview(){
    const p=$('creatorPreview');if(!p)return;
    p.innerHTML=`<div class="creator-fixed-preview" style="position:relative;width:100%;height:100%;overflow:hidden"><img id="creatorFixedCharacter" src="${fixedCharacter()}" alt="Aperçu Looter" decoding="async" fetchpriority="high"><div class="creator-live-badge" style="z-index:2"><b>NIVEAU 1</b><strong>DÉBUTANT</strong></div></div>`;
    renderHD($('creatorFixedCharacter'));
  }
  function reset(){state.gender='male';syncGender();updatePreview();}
  function open(e){if(e){e.preventDefault();e.stopImmediatePropagation();}const m=$('creatorModal');if(!m)return;installTestOnlyStyle();document.body.classList.add('creator-test-active');m.classList.add('show');m.style.display='grid';reset();}
  function bindGender(){const r=$('genderChoices');if(!r)return;r.querySelectorAll('.choice').forEach(b=>b.addEventListener('click',e=>{if(!isOpen())return;e.preventDefault();e.stopImmediatePropagation();state.gender=b.dataset.value==='female'?'female':'male';syncGender();updatePreview();},true));}
  function init(){installTestOnlyStyle();const b=$('creatorTestButton');if(b)b.addEventListener('click',open,true);bindGender();const s=$('saveAvatar');if(s)s.addEventListener('click',e=>{if(!isOpen())return;e.preventDefault();e.stopImmediatePropagation();},true);if(new URLSearchParams(location.search).get('creatorTest')==='1')open();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();