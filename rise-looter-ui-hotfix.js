(() => {
  const ROOT='/assets/creator_sources/';
  const FULL=ROOT+'fullbody/';
  const HAIR=FULL+'hair/';
  const maleStyles=new Set(['male_textured','male_short','male_medium','male_undercut','male_slick']);
  const femaleStyles=new Set(['female_long','female_wavy','female_bob','female_ponytail','female_short']);
  const skinTones={light:'#f4d6c0',warm:'#d9a06d',medium:'#b97855',deep:'#7d4b36',dark:'#4a2d24'};

  function normalized(gender,style){
    const g=gender==='female'?'female':'male';
    const fallback=g==='female'?'female_bob':'male_textured';
    if(g==='male'&&!maleStyles.has(style)) style=fallback;
    if(g==='female'&&!femaleStyles.has(style)) style=fallback;
    return [g,style];
  }
  function baseFor(g){return `${FULL}${g}_base.png`;}
  function skinMaskFor(g){return `${FULL}${g}_skin_mask.png`;}
  function hairFor(g,s,c){return `${HAIR}${s}_${c||'brown'}.png`;}

  function avatarMarkup(gender,style,color,skin,home=false){
    const [g,s]=normalized(gender,style);
    const tone=skinTones[skin]||skinTones.medium;
    return `<div class="rl-avatar-stack ${g==='female'?'female-avatar':''}${home?' home-avatar':''}" data-gender="${g}" data-skin="${skin||'medium'}" style="--skin-tone:${tone}">
      <img class="rl-avatar-bg" src="${FULL}background.webp?avatar=v14" alt="">
      <img class="rl-avatar-base" src="${baseFor(g)}?avatar=v14" alt="Looter">
      <div class="rl-avatar-skin" style="-webkit-mask-image:url('${skinMaskFor(g)}?avatar=v14');mask-image:url('${skinMaskFor(g)}?avatar=v14')"></div>
      <img class="rl-avatar-hair" src="${hairFor(g,s,color)}?avatar=v14" alt="">
    </div>`;
  }

  function attachFallbacks(root){
    root.querySelectorAll('.rl-avatar-base,.rl-avatar-bg,.rl-avatar-hair').forEach(img=>{img.onerror=()=>{img.style.display='none';};});
  }

  function restoreCreator(){
    if(typeof avatarDraft==='undefined') return;
    const preview=document.getElementById('creatorPreview'); if(!preview) return;
    const gender=avatarDraft.gender||'male';
    const style=avatarDraft.hairStyle||(gender==='female'?'female_bob':'male_textured');
    const color=avatarDraft.hairColor||'brown';
    const skin=avatarDraft.skin||'medium';
    preview.innerHTML=`${avatarMarkup(gender,style,color,skin,false)}<div class="creator-live-badge"><b>NIVEAU 1</b><strong>DÉBUTANT</strong></div>`;
    attachFallbacks(preview);
  }

  function restoreHomepage(){
    const holder=document.getElementById('mainCharacter'); if(!holder) return;
    const p=window.currentProfile||{};
    const gender=p.avatar_gender||'male';
    const style=p.avatar_hair_style||(gender==='female'?'female_bob':'male_textured');
    const color=p.avatar_hair_color||'brown';
    const skin=p.avatar_skin||'medium';
    holder.innerHTML=`<div class="character-scene-clean">${avatarMarkup(gender,style,color,skin,true)}</div>`;
    attachFallbacks(holder);
  }

  function surveyOnlyUI(){
    document.querySelectorAll('.filter').forEach(btn=>{
      const t=(btn.textContent||'').toLowerCase();
      if(t.includes('jeu')||t.includes('vidéo')||t.includes('video')||t.includes('toutes')) btn.style.display='none';
      if(t.includes('sondage')){btn.style.display='inline-flex';btn.classList.add('active');}
    });
    document.querySelectorAll('.challenge').forEach(row=>{if(!(row.textContent||'').toLowerCase().includes('sondage')) row.style.display='none';});
    document.querySelectorAll('.mission-title').forEach(el=>{if(/loot up/i.test(el.textContent||'')) el.textContent=(el.textContent||'').replace(/loot up/ig,'Rise Looter');});
    document.querySelectorAll('.mission-description').forEach(el=>{if(/lootix|niveau demandé/i.test(el.textContent||'')) el.textContent="Atteins le niveau demandé pour gagner de l'XP.";});
    document.querySelectorAll('.mission-reward').forEach(el=>{if(/rl coins|lootix/i.test(el.textContent||'')) el.textContent='+ XP';});
    document.querySelectorAll('.bonus').forEach(el=>{el.style.display='none';});
    document.querySelectorAll('.day-wrap').forEach((wrap,i)=>{if(!wrap.querySelector('.day-xp')){const x=document.createElement('div');x.className='day-xp';x.textContent=`+${(i+1)*5} XP`;x.style.cssText='font-size:10px;color:#b77cff;margin-top:4px;font-weight:800';wrap.appendChild(x);}});
  }

  async function awardDailyStreakXP(){
    if(!window.sb||!window.currentUser||!window.currentProfile) return;
    const d=new Date(), dateKey=[d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-');
    const key=`riselooter_streak_xp_${currentUser.id}_${dateKey}`; if(localStorage.getItem(key)) return;
    const streak=Math.max(1,Math.min(7,Number(currentProfile.current_streak||1))), reward=streak*5, newXP=Number(currentProfile.xp||0)+reward;
    const {error}=await sb.from('profiles').update({xp:newXP}).eq('id',currentUser.id); if(error) return;
    currentProfile.xp=newXP; localStorage.setItem(key,String(reward)); if(typeof window.renderDashboard==='function') window.renderDashboard(currentProfile);
  }

  function refreshAll(){restoreCreator();restoreHomepage();surveyOnlyUI();awardDailyStreakXP();}
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',()=>setTimeout(refreshAll,180),{once:true}); else setTimeout(refreshAll,180);
  document.addEventListener('click',e=>{if(e.target.closest('#genderChoices,#skinChoices,#hairColorChoices,#hairStyleChoices,#testCreator')) setTimeout(()=>{restoreCreator();surveyOnlyUI();},80);},true);
  const obs=new MutationObserver(()=>{clearTimeout(window.__rlHotfixTimer);window.__rlHotfixTimer=setTimeout(()=>{restoreHomepage();surveyOnlyUI();awardDailyStreakXP();},150);});
  obs.observe(document.documentElement,{childList:true,subtree:true});
})();
