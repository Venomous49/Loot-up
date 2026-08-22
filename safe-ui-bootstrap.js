(() => {
  'use strict';
  const $=id=>document.getElementById(id); const VERSION='beginner-preview-20260822-1';
  const state={gender:'male'}; const isOpen=()=>document.body.classList.contains('creator-test-active');
  const fixedCharacter=()=>state.gender==='female'
    ? `/female-01-debutant.webp?v=${VERSION}`
    : `/01-debutant.webp?v=${VERSION}`;
  const syncGender=()=>{const r=$('genderChoices');if(r)r.querySelectorAll('.choice').forEach(b=>b.classList.toggle('selected',b.dataset.value===state.gender));};
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
    `;
    document.head.appendChild(style);
  }
  function updatePreview(){
    const p=$('creatorPreview');if(!p)return;
    p.innerHTML=`<div class="creator-fixed-preview" style="position:relative;width:100%;height:100%;overflow:hidden"><img src="${fixedCharacter()}" alt="Aperçu Looter" style="position:absolute;inset:0;width:100%;height:100%;object-fit:contain;object-position:center center;filter:none;transform:none;animation:none"><div class="creator-live-badge" style="z-index:2"><b>NIVEAU 1</b><strong>DÉBUTANT</strong></div></div>`;
  }
  function reset(){state.gender='male';syncGender();updatePreview();}
  function open(e){
    if(e){e.preventDefault();e.stopImmediatePropagation();}
    const m=$('creatorModal');if(!m)return;
    installTestOnlyStyle();
    document.body.classList.add('creator-test-active');
    m.classList.add('show');m.style.display='grid';reset();
  }
  function bindGender(){
    const r=$('genderChoices');if(!r)return;
    r.querySelectorAll('.choice').forEach(b=>b.addEventListener('click',e=>{
      if(!isOpen())return;
      e.preventDefault();e.stopImmediatePropagation();
      state.gender=b.dataset.value==='female'?'female':'male';
      syncGender();updatePreview();
    },true));
  }
  function init(){
    installTestOnlyStyle();
    const b=$('creatorTestButton');if(b)b.addEventListener('click',open,true);
    bindGender();
    const s=$('saveAvatar');if(s)s.addEventListener('click',e=>{if(!isOpen())return;e.preventDefault();e.stopImmediatePropagation();},true);
    if(new URLSearchParams(location.search).get('creatorTest')==='1')open();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
