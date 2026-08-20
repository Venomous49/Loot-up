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
    return `${ROOT}${style}_clean.png`;
  }
  function fallbackFor(gender){return gender==='female'?`${ROOT}female_long_brown_natural.png`:`${ROOT}male_textured_brown_natural.png`;}

  function setImage(img,src,fallback){
    if(!img) return;
    img.style.display='block';
    img.dataset.fallback='0';
    img.src=src+'?character=v10';
    img.onerror=()=>{if(img.dataset.fallback!=='1'){img.dataset.fallback='1';img.src=fallback+'?character=v10';}else{img.style.display='none';}};
  }

  function restoreCreator(){
    if(typeof avatarDraft==='undefined') return;
    const preview=document.getElementById('creatorPreview');
    if(!preview) return;
    const gender=avatarDraft.gender||'male';
    const style=avatarDraft.hairStyle||(gender==='female'?'female_long':'male_textured');
    const color=avatarDraft.hairColor||'brown';
    preview.innerHTML=`<img class="creator-real-preview" alt="Aperçu Looter"><div class="creator-live-badge"><b>NIVEAU 1</b><strong>DÉBUTANT</strong></div>`;
    setImage(preview.querySelector('img'),sourceFor(gender,style,color),fallbackFor(gender));
  }

  function restoreHomepage(){
    const holder=document.getElementById('mainCharacter');
    if(!holder) return;
    const p=window.currentProfile||{};
    const gender=p.avatar_gender||'male';
    const style=p.avatar_hair_style||(gender==='female'?'female_long':'male_textured');
    const color=p.avatar_hair_color||'brown';
    holder.innerHTML='<div class="character-scene-clean"><img class="scene-clean-image" alt="Looter"></div>';
    setImage(holder.querySelector('img'),sourceFor(gender,style,color),fallbackFor(gender));
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

  async function awardDailyStreakXP(){
    if(!window.sb||!window.currentUser||!window.currentProfile) return;
    const d=new Date();
    const dateKey=[d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-');
    const key=`riselooter_streak_xp_${currentUser.id}_${dateKey}`;
    if(localStorage.getItem(key)) return;
    const streak=Math.max(1,Math.min(7,Number(currentProfile.current_streak||1)));
    const reward=streak*5;
    const newXP=Number(currentProfile.xp||0)+reward;
    const {error}=await sb.from('profiles').update({xp:newXP}).eq('id',currentUser.id);
    if(error) return;
    currentProfile.xp=newXP;
    localStorage.setItem(key,String(reward));
    if(typeof window.renderDashboard==='function') window.renderDashboard(currentProfile);
  }

  function refreshAll(){restoreCreator();restoreHomepage();surveyOnlyUI();awardDailyStreakXP();}
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',()=>setTimeout(refreshAll,120),{once:true}); else setTimeout(refreshAll,120);
  document.addEventListener('click',e=>{
    if(e.target.closest('#genderChoices,#skinChoices,#hairColorChoices,#hairStyleChoices,#testCreator')) setTimeout(()=>{restoreCreator();surveyOnlyUI();},80);
  },true);
  const obs=new MutationObserver(()=>{clearTimeout(window.__rlHotfixTimer);window.__rlHotfixTimer=setTimeout(()=>{restoreHomepage();surveyOnlyUI();awardDailyStreakXP();},100);});
  obs.observe(document.documentElement,{childList:true,subtree:true});
})();
