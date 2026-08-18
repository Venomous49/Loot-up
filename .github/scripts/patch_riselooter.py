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

const base =
assetPath(profile,stage);

const outfit =
outfitOverlayPath(
profile.equipped_outfit_slug
);

return `

<div class="character-scene-layered">

<img
class="scene-base"
src="${base}"
alt="Looter"
onerror="
this.style.display='none';
this.parentElement.querySelectorAll('.scene-torso,.scene-head').forEach(el=>el.style.display='none');
this.parentElement.querySelector('.character-missing').style.display='block';
">

<img
class="scene-torso"
src="${base}"
alt=""
aria-hidden="true"
onerror="this.style.display='none';">

<img
class="scene-head"
src="${base}"
alt=""
aria-hidden="true"
onerror="this.style.display='none';">

${outfit ? `
<img
class="scene-outfit"
src="${outfit}"
alt="Tenue équipée"
onerror="this.style.display='none';">
` : ""}

<div class="character-missing" style="display:none">
Asset réaliste manquant.
</div>

</div>

`;

}'''

s = re.sub(
    r'function characterHTML\(profile,stage\)\{.*?\n\}\n\n/\* ==========================================================\nAPERÇU CRÉATEUR',
    new_character + '\n\n/* ==========================================================\nAPERÇU CRÉATEUR',
    s,
    count=1,
    flags=re.S
)

marker = '/* RISELOOTER_VISUAL_OVERRIDE_V7 */'
css = r'''
/* RISELOOTER_VISUAL_OVERRIDE_V7 */
.hero{min-height:560px!important;position:relative!important;overflow:hidden!important;background:#070b0e!important}
.hero:after{content:""!important;position:absolute!important;inset:0!important;z-index:4!important;background:linear-gradient(90deg,rgba(5,9,13,.995) 0%,rgba(5,9,13,.985) 28%,rgba(5,9,13,.86) 40%,rgba(5,9,13,.35) 53%,rgba(5,9,13,.08) 72%,rgba(5,9,13,0) 100%)!important;pointer-events:none!important}
.character-holder{position:absolute!important;top:0!important;right:0!important;bottom:0!important;left:31%!important;width:auto!important;height:auto!important;z-index:1!important;transform:none!important;display:block!important;overflow:hidden!important;animation:none!important}
.character-scene-layered{position:absolute!important;inset:0!important;width:100%!important;height:100%!important;overflow:hidden!important}
.character-scene-layered img{position:absolute!important;inset:0!important;width:100%!important;height:100%!important;object-fit:cover!important;object-position:center 18%!important;filter:saturate(.96) contrast(1.03)!important}
.scene-base{z-index:1!important;transform:scale(.99)!important;animation:none!important}
.scene-torso{z-index:2!important;clip-path:polygon(37% 19%,84% 19%,91% 73%,34% 73%)!important;transform-origin:61% 51%!important;animation:torsoBreathingV7 4.6s ease-in-out infinite!important}
.scene-head{z-index:3!important;clip-path:polygon(43% 0%,80% 0%,82% 29%,41% 29%)!important;transform-origin:62% 18%!important;animation:headIdleV7 7.5s ease-in-out infinite!important}
.scene-outfit{z-index:4!important;object-fit:cover!important;object-position:center 18%!important;pointer-events:none!important}
.character-holder:before{content:""!important;position:absolute!important;left:0!important;top:0!important;width:49%!important;height:128px!important;z-index:6!important;background:linear-gradient(135deg,rgba(5,9,13,1) 0%,rgba(5,9,13,.99) 44%,rgba(5,9,13,.86) 68%,rgba(5,9,13,0) 100%)!important;pointer-events:none!important}
.character-holder:after{content:""!important;position:absolute!important;left:0!important;right:0!important;bottom:0!important;height:84px!important;z-index:6!important;background:linear-gradient(0deg,rgba(5,9,13,1) 0%,rgba(5,9,13,.90) 52%,rgba(5,9,13,0) 100%)!important;pointer-events:none!important}
@keyframes torsoBreathingV7{0%,100%{transform:scaleX(1) scaleY(1) translateY(0)}50%{transform:scaleX(1.012) scaleY(1.006) translateY(-1px)}}
@keyframes headIdleV7{0%,100%{transform:rotate(0deg) translate(0,0)}28%{transform:rotate(-.7deg) translate(-1px,0)}58%{transform:rotate(.8deg) translate(1px,-1px)}82%{transform:rotate(-.25deg) translate(0,0)}}
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
