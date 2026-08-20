(() => {
  const ROOT='/assets/creator_sources/';
  const STD=ROOT+'standardized_black/';
  const MASKS=ROOT+'color_master_masks/';
  const maleStyles=new Set(['male_textured','male_short','male_medium','male_undercut','male_slick']);
  const femaleStyles=new Set(['female_long','female_wavy','female_bob','female_ponytail','female_short']);
  const naturalColors=new Set(['brown','blond','red','purple']);
  const skinTones={light:'#f5d8c3',warm:'#e7b07a',medium:'#c9875f',deep:'#8b563d',dark:'#5a3528'};

  function normalized(gender,style){
    const g=gender==='female'?'female':'male';
    const fallback=g==='female'?'female_long':'male_textured';
    if(g==='male'&&!maleStyles.has(style)) style=fallback;
    if(g==='female'&&!femaleStyles.has(style)) style=fallback;
    return [g,style];
  }
  function baseFor(gender,style){const [,s]=normalized(gender,style);return `${STD}${s}.webp`;}
  function colorFor(gender,style,color){
    const [,s]=normalized(gender,style);
    if(color==='black') return `${STD}${s}.webp`;
    if(naturalColors.has(color)) return `${ROOT}${s}_${color}_natural.png`;
    return `${ROOT}${s}_clean.png`;
  }
  function maskFor(gender,style,color){
    const [,s]=normalized(gender,style);
    if(color==='black'||!naturalColors.has(color)) return '';
    return `${MASKS}${s}_${color}_natural.png`;
  }
  function fallbackFor(gender){return gender==='female'?`${STD}female_long.webp`:`${STD}male_textured.webp`;}

  function avatarMarkup(gender,style,color,skin,home=false){
    const base=baseFor(gender,style), col=colorFor(gender,style,color), mask=maskFor(gender,style,color);
    const tone=skinTones[skin]||skinTones.medium;
    const female=gender==='female'?' female-avatar':'';
    const maskStyle=mask?`-webkit-mask-image:url('${mask}');mask-image:url('${mask}');`:'';
    return `<div class="rl-avatar-stack${female}${home?' home-avatar':''}" data-skin="${skin||'medium'}" style="--skin-tone:${tone}">
      <img class="rl-avatar-base" src="${base}?avatar=v11" data-fallback="${fallbackFor(gender)}" alt="Looter">
      ${color==='black'?'':`<img class="rl-avatar-hair" src="${col}?avatar=v11" alt="" style="${maskStyle}">`}
      <div class="rl-avatar-skin"></div>
    </div>`;
  }

  function attachFallbacks(root){
    root.querySelectorAll('.rl-avatar-base').forEach(img=>{
      img.onerror=()=>{if(img.dataset.used!=='1'){img.dataset.used='1';img.src=img.dataset.fallback+'?avatar=v11';}else img.style.display='none';};
    });
    root.querySelectorAll('.rl-avatar-hair').forEach(img=>{img.onerror=()=>img.style.display='none';});
  }

  function restoreCreator(){
    if(typeof avatarDraft==='undefined') return;
    const preview=document.getElementById('creatorPreview'); if(!preview) return;
    const gender=avatarDraft.gender||'male';
    const style=avatarDraft.hairStyle||(gender==='female'?'female_long':'male_textured');
    const color=avatarDraft.hairColor||'brown';
    const skin=avatarDraft.skin||'medium';
    preview.innerHTML=`${avatarMarkup(gender,style,color,skin,false)}<div class="creator-live-badge"><b>NIVEAU 1</b><strong>DÉBUTANT</strong></div>`;
    attachFallbacks(preview);
  }

  function restoreHomepage(){
    const holder=document.getElementById('mainCharacter'); if(!holder) return;
    const p=window.currentProfile||{};
    const gender=p.avatar_gender||'male';
    const style=p.avatar_hair_style||(gender==='female'?'female_long':'male_textured');
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
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',()=>setTimeout(refreshAll,120),{once:true}); else setTimeout(refreshAll,120);
  document.addEventListener('click',e=>{if(e.target.closest('#genderChoices,#skinChoices,#hairColorChoices,#hairStyleChoices,#testCreator')) setTimeout(()=>{restoreCreator();surveyOnlyUI();},60);},true);
  const obs=new MutationObserver(()=>{clearTimeout(window.__rlHotfixTimer);window.__rlHotfixTimer=setTimeout(()=>{restoreHomepage();surveyOnlyUI();awardDailyStreakXP();},120);});
  obs.observe(document.documentElement,{childList:true,subtree:true});
})();
