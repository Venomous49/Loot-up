(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const hair = {
    male:[['male_textured','Texturé'],['male_short','Court classique'],['male_medium','Mi-long'],['male_undercut','Dégradé'],['male_slick','Coiffé arrière']],
    female:[['female_long','Long lisse'],['female_wavy','Ondulé'],['female_bob','Carré'],['female_ponytail','Queue attachée'],['female_short','Court moderne']]
  };
  const state={gender:'male',skin:'medium',hairColor:'brown',hairStyle:'male_textured'};
  const isOpen=()=>document.body.classList.contains('creator-test-active');
  const layer=(kind)=>{
    const root=`/assets/creator_layers/${state.gender}`;
    if(kind==='base') return `${root}/base.webp?v=layered1`;
    if(kind==='skin') return `${root}/skin-${state.skin}.webp?v=layered1`;
    return `${root}/hair-${state.hairStyle}-${state.hairColor}.webp?v=layered1`;
  };
  const sync=(id,field)=>{const r=$(id);if(r)r.querySelectorAll('.choice').forEach(b=>b.classList.toggle('selected',b.dataset.value===state[field]));};
  function previewMarkup(){return `<div class="creator-layer-stack" style="position:relative;width:100%;height:100%;overflow:hidden">
    <img src="${layer('base')}" alt="Base personnage" style="position:absolute;inset:0;width:100%;height:100%;object-fit:contain;object-position:center bottom;z-index:1">
    <img src="${layer('skin')}" alt="" aria-hidden="true" style="position:absolute;inset:0;width:100%;height:100%;object-fit:contain;object-position:center bottom;z-index:2;pointer-events:none">
    <img src="${layer('hair')}" alt="" aria-hidden="true" style="position:absolute;inset:0;width:100%;height:100%;object-fit:contain;object-position:center bottom;z-index:3;pointer-events:none">
    <div class="creator-live-badge" style="z-index:4"><b>NIVEAU 1</b><strong>DÉBUTANT</strong></div></div>`;}
  function updatePreview(){const p=$('creatorPreview');if(p)p.innerHTML=previewMarkup();}
  function renderHair(){const r=$('hairStyleChoices');if(!r)return;const list=hair[state.gender];if(!list.some(x=>x[0]===state.hairStyle))state.hairStyle=list[0][0];r.innerHTML=list.map(([v,l])=>`<button type="button" class="choice hair-choice ${v===state.hairStyle?'selected':''}" data-value="${v}"><span class="hair-thumb"><img src="/assets/creator_layers/${state.gender}/hair-${v}-${state.hairColor}.webp?v=layered1" alt="${l}" style="width:100%;height:100%;object-fit:contain"></span><span>${l}</span></button>`).join('');r.querySelectorAll('.choice').forEach(b=>b.addEventListener('click',e=>{if(!isOpen())return;e.preventDefault();e.stopImmediatePropagation();state.hairStyle=b.dataset.value;renderHair();updatePreview();},true));}
  function reset(){Object.assign(state,{gender:'male',skin:'medium',hairColor:'brown',hairStyle:'male_textured'});sync('genderChoices','gender');sync('skinChoices','skin');sync('hairColorChoices','hairColor');renderHair();updatePreview();}
  function open(e){if(e){e.preventDefault();e.stopImmediatePropagation();}const m=$('creatorModal');if(!m)return;document.body.classList.add('creator-test-active');m.classList.add('show');m.style.display='grid';m.setAttribute('aria-hidden','false');reset();}
  function close(){const m=$('creatorModal');document.body.classList.remove('creator-test-active');if(m){m.classList.remove('show');m.style.removeProperty('display');m.setAttribute('aria-hidden','true');}}
  function bind(id,field){const r=$(id);if(!r)return;r.querySelectorAll('.choice').forEach(b=>b.addEventListener('click',e=>{if(!isOpen())return;e.preventDefault();e.stopImmediatePropagation();state[field]=b.dataset.value;if(field==='gender')state.hairStyle=state.gender==='female'?'female_long':'male_textured';sync(id,field);renderHair();updatePreview();},true));}
  function init(){const b=$('creatorTestButton');if(b)b.addEventListener('click',open,true);bind('genderChoices','gender');bind('skinChoices','skin');bind('hairColorChoices','hairColor');const s=$('saveAvatar');if(s)s.addEventListener('click',e=>{if(!isOpen())return;e.preventDefault();e.stopImmediatePropagation();alert('TEST OK — rendu par calques. Rien n\'a été enregistré.');},true);const m=$('creatorModal');if(m)m.addEventListener('click',e=>{if(isOpen()&&e.target===m)close();});document.addEventListener('keydown',e=>{if(e.key==='Escape'&&isOpen())close();});if(new URLSearchParams(location.search).get('creatorTest')==='1')open();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
