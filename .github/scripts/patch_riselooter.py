from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

s = s.replace(
    'return `/assets/characters/male/medium/brown/male_textured/${stages[stage].slug}.webp`;',
    'return `/${stages[stage].slug}.webp`;'
)
s = s.replace(
    'return "/assets/characters/male/medium/brown/male_textured/01-debutant.webp";',
    'return "/01-debutant.webp";'
)

new_character = r'''function characterHTML(profile,stage){

const base = assetPath(profile,stage);
const outfit = outfitOverlayPath(profile.equipped_outfit_slug);

if(stage === 0){
return `
<div class="character-scene-real">
  <img class="scene-background" src="/01-debutant-background.webp" alt="Décor" onerror="this.src='${base}'">
  <img class="scene-body" src="/01-debutant-character.png" alt="Looter" onerror="this.style.display='none'">
  <img class="scene-torso" src="/01-debutant-character.png" alt="" aria-hidden="true" onerror="this.style.display='none'">
  <img class="scene-head" src="/01-debutant-character.png" alt="" aria-hidden="true" onerror="this.style.display='none'">
  ${outfit ? `<img class="scene-outfit" src="${outfit}" alt="Tenue équipée" onerror="this.style.display='none'">` : ""}
</div>`;
}

return `
<div class="character-scene-static">
  <img src="${base}" alt="Looter" onerror="this.style.display='none';this.nextElementSibling.style.display='block'">
  <div class="character-missing" style="display:none">Asset réaliste manquant.</div>
</div>`;

}'''

s = re.sub(
    r'function characterHTML\(profile,stage\)\{.*?\n\}\n\n/\* ==========================================================\nAPERÇU CRÉATEUR',
    new_character + '\n\n/* ==========================================================\nAPERÇU CRÉATEUR',
    s,
    count=1,
    flags=re.S
)

marker = '/* RISELOOTER_VISUAL_OVERRIDE_V8 */'
css = r'''
/* RISELOOTER_VISUAL_OVERRIDE_V8 */
.hero{min-height:560px!important;position:relative!important;overflow:hidden!important;background:#070b0e!important}
.hero:after{content:""!important;position:absolute!important;inset:0!important;z-index:4!important;background:linear-gradient(90deg,rgba(5,9,13,.995) 0%,rgba(5,9,13,.985) 27%,rgba(5,9,13,.82) 40%,rgba(5,9,13,.28) 55%,rgba(5,9,13,.04) 74%,rgba(5,9,13,0) 100%)!important;pointer-events:none!important}
.character-holder{position:absolute!important;top:0!important;right:0!important;bottom:0!important;left:31%!important;width:auto!important;height:auto!important;z-index:1!important;transform:none!important;display:block!important;overflow:hidden!important;animation:none!important}
.character-scene-real,.character-scene-static{position:absolute!important;inset:0!important;overflow:hidden!important}
.character-scene-real img,.character-scene-static img{position:absolute!important;inset:0!important;width:100%!important;height:100%!important;object-fit:cover!important;object-position:center 18%!important}
.scene-background{z-index:1!important;filter:saturate(.95) contrast(1.03) brightness(.92)!important}
.scene-body{z-index:2!important;object-fit:contain!important;object-position:center bottom!important;filter:drop-shadow(0 15px 16px rgba(0,0,0,.35))!important}
.scene-torso{z-index:3!important;object-fit:contain!important;object-position:center bottom!important;clip-path:polygon(24% 17%,78% 17%,84% 68%,20% 68%)!important;transform-origin:51% 58%!important;animation:realBreathing 4.8s ease-in-out infinite!important}
.scene-head{z-index:4!important;object-fit:contain!important;object-position:center bottom!important;clip-path:polygon(31% 0%,70% 0%,73% 28%,29% 28%)!important;transform-origin:51% 24%!important;animation:realHeadIdle 7.2s ease-in-out infinite!important}
.scene-outfit{z-index:5!important;object-fit:contain!important;object-position:center bottom!important;pointer-events:none!important}
@keyframes realBreathing{0%,100%{transform:scaleX(1) scaleY(1) translateY(0)}50%{transform:scaleX(1.018) scaleY(1.009) translateY(-1px)}}
@keyframes realHeadIdle{0%,100%{transform:rotate(0deg) translate(0,0)}25%{transform:rotate(-1deg) translate(-1px,0)}55%{transform:rotate(.9deg) translate(1px,-1px)}78%{transform:rotate(-.35deg) translate(0,0)}}
.character-holder:before{content:""!important;position:absolute!important;left:0!important;top:0!important;width:46%!important;height:115px!important;z-index:6!important;background:linear-gradient(135deg,rgba(5,9,13,1) 0%,rgba(5,9,13,.96) 48%,rgba(5,9,13,.55) 72%,rgba(5,9,13,0) 100%)!important;pointer-events:none!important}
.character-holder:after{content:""!important;position:absolute!important;left:0!important;right:0!important;bottom:0!important;height:76px!important;z-index:6!important;background:linear-gradient(0deg,rgba(5,9,13,1) 0%,rgba(5,9,13,.85) 48%,rgba(5,9,13,0) 100%)!important;pointer-events:none!important}
.hero-copy,.next-evolution,.hero-track{z-index:9!important}
.hero-track{padding-top:8px!important;background:linear-gradient(0deg,rgba(4,9,14,.99) 0%,rgba(4,9,14,.88) 60%,rgba(4,9,14,0) 100%)!important}
.next-evolution{background:rgba(4,10,16,.96)!important;backdrop-filter:blur(3px)!important}
.shadow-character{height:145px!important;margin:10px auto!important;overflow:hidden!important;border-radius:8px!important;position:relative!important;background:#080d12!important;box-shadow:inset 0 0 30px rgba(0,0,0,.82)!important}
.shadow-character:before{content:""!important;position:absolute!important;left:0!important;top:0!important;width:100%!important;height:46px!important;z-index:3!important;background:linear-gradient(180deg,rgba(4,10,16,.99),rgba(4,10,16,.9),rgba(4,10,16,0))!important;pointer-events:none!important}
.shadow-character img{width:100%!important;height:100%!important;max-width:none!important;object-fit:cover!important;object-position:center 22%!important;transform:scale(1.01)!important;filter:brightness(.12) grayscale(1) contrast(1.45)!important;opacity:.98!important}
.evolution-character{overflow:hidden!important;border-radius:7px!important;position:relative!important}
.evolution-card.locked .evolution-character:before{content:""!important;position:absolute!important;left:0!important;right:0!important;top:0!important;height:34px!important;z-index:3!important;background:linear-gradient(180deg,rgba(5,9,13,.98),rgba(5,9,13,0))!important;pointer-events:none!important}
.evolution-card.locked .evolution-character img{width:100%!important;height:100%!important;object-fit:cover!important;object-position:center 22%!important;transform:scale(1.01)!important;filter:brightness(.12) grayscale(1) contrast(1.45)!important;opacity:.98!important}
@media (prefers-reduced-motion: reduce){.scene-torso,.scene-head{animation:none!important}}
'''

if marker not in s:
    s = s.replace('</style>', css + '\n</style>', 1)

p.write_text(s, encoding='utf-8')
