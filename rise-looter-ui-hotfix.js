(() => {
  const ROOT='/assets/creator_sources/';
  const maleStyles=new Set(['male_textured','male_short','male_medium','male_undercut','male_slick']);
  const femaleStyles=new Set(['female_long','female_wavy','female_bob','female_ponytail','female_short']);
  const naturalColors=new Set(['brown','blond','red','purple']);

  function sourceFor(gender,style,color){
    const g=gender==='female'?'female':'male';
    const fallbackStyle=g==='female'?'female_long':'male_textured';
    if(g==='male'&&!maleStyles.has(style)) style=fallbackStyle;
    if(g==='female'&&!femaleStyles.has(style)) style=fallbackStyle;
    if(color==='black') color='brown';
    if(naturalColors.has(color)) return `${ROOT}${style}_${color}_natural.png`;
    const clean=`${ROOT}${style}_clean.png`;
    return clean;
  }
  function fallbackFor(gender){return gender==='female'?`${ROOT}female_long_brown_natural.png`:`${ROOT}male_textured_brown_natural.png`;}

  function setImage(img,src,fallback){
    if(!img) return;
    img.style.display='block';
    img.src=src+'?character=v9';
    img.onerror=()=>{if(img.dataset.fallback!=='1'){img.dataset.fallback='1';img.src=fallback+'?character=v9';}else{img.style.display='none';}};
  }

  function restoreCreator(){
    if(typeof avatarDraft==='undefined') return;
    const preview=document.getElementById('creatorPreview');
    if(!preview) return;
    const gender=avatarDraft.gender||'male';
    const style=avatarDraft.hairStyle||(gender==='female'?'female_long':'male_textured');
    const color=avatarDraft.hairColor||'brown';
    const src=sourceFor(gender,style,color), fallback=fallbackFor(gender);
    preview.innerHTML=`<img class="creator-real-preview" alt="Aperçu Looter"><div class="creator-live-badge"><b>NIVEAU 1</b><strong>DÉBUTANT</strong></div>`;
    setImage(preview.querySelector('img'),src,fallback);
  }

  function restoreHomepage(){
    const holder=document.getElementById('mainCharacter');
    if(!holder) return;
    const p=window.currentProfile||{};
    const gender=p.avatar_gender||'male';
    const style=p.avatar_hair_style||(gender==='female'?'female_long':'male_textured');
    const color=p.avatar_hair_color||'brown';
    const src=sourceFor(gender,style,color), fallback=fallbackFor(gender);
    holder.innerHTML='<div class="character-scene-clean"><img class="scene-clean-image" alt="Looter"></div>';
    setImage(holder.querySelector('img'),src,fallback);
  }

  function surveyOnlyUI(){
    document.querySelectorAll('.filter').forEach(btn=>{
      const t=(btn.textContent||'').toLowerCase();
      if(t.includes('jeu')||t.includes('vidéo')||t.includes('video')||t.includes('toutes')) btn.style.display='none';
      if(t.includes('sondage')){btn.style.display='inline-flex';btn.classList.add('active');}
    });
    document.querySelectorAll('.challenge').forEach(row=>{
      const t=(row.textContent||'').toLowerCase();
      if(!t.includes('sondage')) row.style.display='none';
    });
    document.querySelectorAll('.mission-title').forEach(el=>{
      if(/loot up/i.test(el.textContent||'')) el.textContent=(el.textContent||'').replace(/loot up/ig,'Rise Looter');
    });
    document.querySelectorAll('.mission-description').forEach(el=>{
      if(/lootix|niveau demandé/i.test(el.textContent||'')) el.textContent="Atteins le niveau demandé pour gagner de l'XP.";
    });
    document.querySelectorAll('.mission-reward').forEach(el=>{
      if(/rl coins|lootix/i.test(el.textContent||'')) el.textContent='+ XP';
    });
    document.querySelectorAll('.bonus').forEach(el=>{el.style.display='none';});

    document.querySelectorAll('.day-wrap').forEach((wrap,i)=>{
      if(!wrap.querySelector('.day-xp')){
        const x=document.createElement('div');x.className='day-xp';x.textContent=`+${(i+1)*5} XP`;x.style.cssText='font-size:10px;color:#b77cff;margin-top:4px;font-weight:800';wrap.appendChild(x);
      }
    });
  }

  function refreshAll(){restoreCreator();restoreHomepage();surveyOnlyUI();}
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',()=>setTimeout(refreshAll,50),{once:true}); else setTimeout(refreshAll,50);
  document.addEventListener('click',e=>{
    if(e.target.closest('#genderChoices,#skinChoices,#hairColorChoices,#hairStyleChoices,#testCreator')) setTimeout(()=>{restoreCreator();surveyOnlyUI();},80);
  },true);
  const obs=new MutationObserver(()=>{clearTimeout(window.__rlHotfixTimer);window.__rlHotfixTimer=setTimeout(()=>{restoreHomepage();surveyOnlyUI();},60);});
  obs.observe(document.documentElement,{childList:true,subtree:true});
})();
