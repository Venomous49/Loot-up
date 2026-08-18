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

marker = '/* RISELOOTER_VISUAL_OVERRIDE_V10 */'
css = r'''
/* RISELOOTER_VISUAL_OVERRIDE_V10 */
.hero{min-height:560px!important;position:relative!important;overflow:hidden!important;background:#070b0e!important}
.hero:after{content:""!important;position:absolute!important;inset:0!important;z-index:4!important;background:linear-gradient(90deg,rgba(5,9,13,.995) 0%,rgba(5,9,13,.985) 27%,rgba(5,9,13,.82) 40%,rgba(5,9,13,.28) 55%,rgba(5,9,13,.04) 74%,rgba(5,9,13,0) 100%)!important;pointer-events:none!important}
.character-holder{position:absolute!important;top:0!important;right:0!important;bottom:0!important;left:31%!important;width:auto!important;height:auto!important;z-index:1!important;transform:none!important;display:block!important;overflow:hidden!important;animation:none!important}
.character-scene-real,.character-scene-static{position:absolute!important;inset:0!important;overflow:hidden!important;animation:none!important;transform:none!important}
.character-scene-real img,.character-scene-static img{position:absolute!important;inset:0!important;width:100%!important;height:100%!important;margin:0!important;image-rendering:auto!important;backface-visibility:hidden!important}
.scene-background{z-index:1!important;object-fit:cover!important;object-position:center 18%!important;filter:none!important;transform:none!important;animation:none!important}
.scene-body{z-index:2!important;object-fit:contain!important;object-position:center bottom!important;clip-path:inset(54% 0 0 0)!important;filter:none!important;transform:none!important;animation:none!important}
.scene-torso{z-index:3!important;object-fit:contain!important;object-position:center bottom!important;clip-path:inset(27% 0 42% 0)!important;filter:none!important;transform-origin:50% 51%!important;animation:torsoBreathingV10 4.1s ease-in-out infinite!important;will-change:transform!important}
.scene-head{z-index:4!important;object-fit:contain!important;object-position:center bottom!important;clip-path:inset(0 0 69% 0)!important;filter:none!important;transform-origin:50% 23%!important;animation:headIdleV10 7.4s ease-in-out infinite!important;will-change:transform!important}
.scene-outfit{z-index:5!important;object-fit:contain!important;object-position:center bottom!important;pointer-events:none!important;filter:none!important;animation:none!important}
@keyframes torsoBreathingV10{
  0%,100%{transform:translateY(0) scaleX(1) scaleY(1)}
  48%,52%{transform:translateY(-1px) scaleX(1.024) scaleY(1.012)}
}
@keyframes headIdleV10{
  0%,18%,100%{transform:translate(0,0) rotate(0deg)}
  32%{transform:translate(-1px,0) rotate(-1.2deg)}
  52%{transform:translate(1px,-1px) rotate(.9deg)}
  72%{transform:translate(0,0) rotate(-.35deg)}
}
.character-holder:before{content:""!important;position:absolute!important;left:0!important;top:0!important;width:46%!important;height:115px!important;z-index:6!important;background:linear-gradient(135deg,rgba(5,9,13,1) 0%,rgba(5,9,13,.96) 48%,rgba(5,9,13,.55) 72%,rgba(5,9,13,0) 100%)!important;pointer-events:none!important}
.character-holder:after{content:""!important;position:absolute!important;left:0!important;right:0!important;bottom:0!important;height:76px!important;z-index:6!important;background:linear-gradient(0deg,rgba(5,9,13,1) 0%,rgba(5,9,13,.85) 48%,rgba(5,9,13,0) 100%)!important;pointer-events:none!important}
.hero-copy,.next-evolution,.hero-track{z-index:9!important}
.hero-track{padding-top:8px!important;background:linear-gradient(0deg,rgba(4,9,14,.99) 0%,rgba(4,9,14,.88) 60%,rgba(4,9,14,0) 100%)!important}
.next-evolution{background:rgba(4,10,16,.96)!important;backdrop-filter:blur(3px)!important}
.shadow-character{height:145px!important;margin:10px auto!important;overflow:hidden!important;border-radius:8px!important;position:relative!important;background:#080d12!important;box-shadow:inset 0 0 30px rgba(0,0,0,.82)!important}
.shadow-character img{width:100%!important;height:100%!important;max-width:none!important;object-fit:cover!important;object-position:center 22%!important;transform:scale(1.01)!important;filter:brightness(.22) grayscale(1) contrast(1.30)!important;opacity:.98!important}
'''

if marker not in s:
    s = s.replace('</style>', css + '\n</style>', 1)

p.write_text(s, encoding='utf-8')
