(() => {
  const silhouettes = [
    '/silhouettes/01-debutant.png',
    '/silhouettes/05-debrouillard.png',
    '/silhouettes/10-chasseur.png',
    '/silhouettes/15-hustler.png',
    '/silhouettes/20-pro.png',
    '/silhouettes/30-elite.png',
    '/silhouettes/40-cyber-looter.png',
    '/silhouettes/50-rise-looter.png'
  ];

  function apply(img,src){
    if(!img) return;
    if(img.getAttribute('src')!==src) img.setAttribute('src',src);
    img.alt='';
    img.style.setProperty('display','block','important');
    img.style.setProperty('width','100%','important');
    img.style.setProperty('height','100%','important');
    img.style.setProperty('object-fit','contain','important');
    img.style.setProperty('object-position','50% 100%','important');
    img.style.setProperty('transform','none','important');
    img.style.setProperty('filter','none','important');
    img.style.setProperty('opacity','1','important');
  }

  function refresh(){
    const cards=[...document.querySelectorAll('.evolution-card')];
    cards.forEach((card,i)=>{
      if(!card.classList.contains('locked')||!silhouettes[i]) return;
      let img=card.querySelector('.evolution-character img');
      if(!img){
        const holder=card.querySelector('.evolution-character');
        if(holder){ img=document.createElement('img'); holder.innerHTML=''; holder.appendChild(img); }
      }
      apply(img,silhouettes[i]);
    });
    const firstLocked=cards.findIndex(c=>c.classList.contains('locked'));
    const nextIndex=firstLocked>=0?firstLocked:1;
    const holder=document.querySelector('.shadow-character');
    if(holder&&silhouettes[nextIndex]){
      let img=holder.querySelector('img');
      if(!img){ img=document.createElement('img'); holder.innerHTML=''; holder.appendChild(img); }
      apply(img,silhouettes[nextIndex]);
    }
  }

  function boot(){
    refresh();
    const root=document.getElementById('evolutionGrid')||document.body;
    const obs=new MutationObserver(()=>requestAnimationFrame(refresh));
    obs.observe(root,{childList:true,subtree:true});
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot,{once:true}); else boot();
})();
