(() => {
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

  function refreshUI(){surveyOnlyUI();awardDailyStreakXP();}
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',()=>setTimeout(refreshUI,180),{once:true}); else setTimeout(refreshUI,180);
  document.addEventListener('click',e=>{if(e.target.closest('.filter,#testCreator')) setTimeout(surveyOnlyUI,80);},true);
  const obs=new MutationObserver(()=>{clearTimeout(window.__rlHotfixTimer);window.__rlHotfixTimer=setTimeout(refreshUI,150);});
  obs.observe(document.documentElement,{childList:true,subtree:true});
})();
