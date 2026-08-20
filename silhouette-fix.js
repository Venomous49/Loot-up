(() => {
  const silhouettes=['/silhouettes/01-debutant.png','/silhouettes/05-debrouillard.png','/silhouettes/10-chasseur.png','/silhouettes/15-hustler.png','/silhouettes/20-pro.png','/silhouettes/30-elite.png','/silhouettes/40-cyber-looter.png','/silhouettes/50-rise-looter.png'];

  function apply(img,src){
    if(!img) return;
    const wanted=src+'?cutout=v7';
    if(img.getAttribute('src')!==wanted) img.setAttribute('src',wanted);
    img.alt='';
    const s=img.style;
    s.setProperty('display','block','important'); s.setProperty('visibility','visible','important');
    s.setProperty('width','100%','important'); s.setProperty('height','100%','important');
    s.setProperty('object-fit','contain','important'); s.setProperty('object-position','50% 100%','important');
    s.setProperty('transform','none','important'); s.setProperty('filter','none','important'); s.setProperty('opacity','1','important');
  }

  function makeVisible(holder){
    holder.style.setProperty('display','grid','important'); holder.style.setProperty('visibility','visible','important');
    holder.style.setProperty('opacity','1','important'); holder.style.setProperty('overflow','hidden','important');
    holder.style.setProperty('background','#d8dadd','important');
    holder.querySelectorAll('::before,::after');
  }

  function refresh(){
    const cards=[...document.querySelectorAll('.evolution-card')];
    cards.forEach((card,i)=>{
      if(i===0 || !silhouettes[i]) return;
      const holder=card.querySelector('.evolution-character'); if(!holder) return;
      card.classList.add('locked'); makeVisible(holder);
      holder.querySelectorAll(':scope > *').forEach(n=>{ if(n.tagName!=='IMG') n.style.setProperty('display','none','important'); });
      let img=holder.querySelector(':scope > img');
      if(!img){ img=document.createElement('img'); holder.appendChild(img); }
      apply(img,silhouettes[i]);
    });
    const holder=document.querySelector('.shadow-character');
    if(holder){ makeVisible(holder); let img=holder.querySelector('img'); if(!img){img=document.createElement('img');holder.appendChild(img);} apply(img,silhouettes[1]); }
  }

  function boot(){
    refresh();
    let pending=false;
    new MutationObserver(()=>{ if(pending)return; pending=true; requestAnimationFrame(()=>{pending=false;refresh();}); }).observe(document.body,{childList:true,subtree:true});
    setTimeout(refresh,300); setTimeout(refresh,1200);
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot,{once:true}); else boot();
})();
