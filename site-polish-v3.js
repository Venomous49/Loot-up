(() => {
  'use strict';

  const style = document.createElement('style');
  style.id = 'riselooter-polish-v3-style';
  style.textContent = `
    #home .hero .character-scene-clean {position:absolute!important;inset:0!important;overflow:hidden!important;background:#070b0e!important}
    #home .hero .character-scene-clean::after {content:""!important;display:block!important;position:absolute!important;inset:0!important;z-index:0!important;background-image:var(--stage-backdrop,none)!important;background-size:cover!important;background-position:center center!important;background-repeat:no-repeat!important;filter:brightness(.34) saturate(.78)!important;opacity:.46!important;transform:scale(1.02)!important;pointer-events:none!important}
    #home .hero .scene-clean-image.stage-art-clean {position:absolute!important;inset:0!important;z-index:1!important;width:100%!important;height:100%!important;max-width:100%!important;object-fit:contain!important;object-position:68% center!important;transform:none!important;filter:none!important;opacity:1!important;image-rendering:auto!important}
    .evolution-real.stage-art-clean {width:100%!important;height:100%!important;max-width:100%!important;object-fit:contain!important;object-position:center center!important;transform:none!important;filter:none!important;image-rendering:auto!important}
    #home .next-evolution{bottom:68px!important}
    #challenges .bonus{display:none!important}
    #missions .filters .filter:not([data-filter="survey"]){display:none!important}
    #shop,#inventory,#dailyChest,nav [data-nav="shop"],nav [data-nav="inventory"]{display:none!important}
  `;
  document.head.appendChild(style);

  function setText(el,value){if(el&&el.textContent!==value)el.textContent=value}
  function syncStageBackdrop(){const img=document.querySelector('#home .hero .scene-clean-image.stage-art-clean');const scene=img&&img.closest('.character-scene-clean');if(!img||!scene)return;const src=img.currentSrc||img.src;const backdrop=src;const value=backdrop?`url("${backdrop.replace(/"/g,'\\"')}")`:'none';if(scene.style.getPropertyValue('--stage-backdrop')!==value)scene.style.setProperty('--stage-backdrop',value)}
  function polishChallenges(){const section=document.getElementById('challenges');if(!section)return;setText(section.querySelector('.section-subtitle'),'Réponds à 5 sondages pour gagner de l’XP.');[...section.querySelectorAll('.challenge')].forEach(challenge=>{if(challenge.dataset.category!=='survey'){challenge.remove();return}challenge.dataset.category='survey';setText(challenge.querySelector('span:first-child'),'▤ Réponds à 5 sondages');const reward=challenge.querySelector('.challenge-reward');setText(reward,'+150 XP');if(reward)reward.style.color='#bd74ff';challenge.onclick=async()=>{if(typeof window.loadMissions==='function')await window.loadMissions('survey');document.getElementById('missions')?.scrollIntoView({behavior:'smooth',block:'start'})}})}
  function polishMissions(){const section=document.getElementById('missions');if(!section)return;setText(section.querySelector('.section-subtitle'),'Réponds à des sondages pour gagner de l’XP.');section.querySelectorAll('.filters .filter').forEach(button=>{const survey=button.dataset.filter==='survey';button.classList.toggle('active',survey);button.style.display=survey?'':'none';if(survey)button.onclick=()=>window.loadMissions?.('survey')});section.querySelectorAll('.mission').forEach(card=>{const isSurvey=(card.textContent||'').toLowerCase().includes('sondage');card.style.display=isSurvey?'':'none'});}
  function apply(){syncStageBackdrop();polishChallenges();polishMissions()}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',apply,{once:true});else apply();
  let queued=false;new MutationObserver(()=>{if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;apply()})}).observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['src','class']});
})();
