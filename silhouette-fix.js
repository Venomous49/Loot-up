(() => {
  const masters = [
    '/01-debutant.webp',
    '/05-debrouillard.webp',
    '/10-chasseur.webp',
    '/15-hustler.webp',
    '/20-pro.webp',
    '/30-elite.webp',
    '/40-cyber-looter.webp',
    '/50-rise-looter.webp'
  ];

  function apply(img,src){
    if(!img) return;
    img.src=src+'?locked-silhouette=v5';
    img.alt='';
    img.style.setProperty('display','block','important');
    img.style.setProperty('width','100%','important');
    img.style.setProperty('height','100%','important');
    img.style.setProperty('object-fit','contain','important');
    img.style.setProperty('object-position','50% 100%','important');
    img.style.setProperty('transform','none','important');
    img.style.setProperty('filter','brightness(0) saturate(100%) contrast(200%)','important');
    img.style.setProperty('opacity','1','important');
  }

  function refresh(){
    const cards=[...document.querySelectorAll('.evolution-card')];
    cards.forEach((card,i)=>{
      if(!card.classList.contains('locked')||!masters[i]) return;
      const holder=card.querySelector('.evolution-character');
      if(!holder) return;
      let img=holder.querySelector('img');
      if(!img){img=document.createElement('img');holder.innerHTML='';holder.appendChild(img);}
      apply(img,masters[i]);
      holder.style.setProperty('background','#d8dadd','important');
    });
    const firstLocked=cards.findIndex(c=>c.classList.contains('locked'));
    const nextIndex=firstLocked>=0?firstLocked:1;
    const holder=document.querySelector('.shadow-character');
    if(holder&&masters[nextIndex]){
      let img=holder.querySelector('img');
      if(!img){img=document.createElement('img');holder.innerHTML='';holder.appendChild(img);}
      apply(img,masters[nextIndex]);
      holder.style.setProperty('background','#d8dadd','important');
    }
  }

  function boot(){
    refresh();
    const root=document.getElementById('evolutionGrid')||document.body;
    let pending=false;
    new MutationObserver(()=>{if(pending)return;pending=true;requestAnimationFrame(()=>{pending=false;refresh();});}).observe(root,{childList:true,subtree:true});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
