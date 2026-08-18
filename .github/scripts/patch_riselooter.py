from pathlib import Path

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

marker = '/* RISELOOTER_VISUAL_OVERRIDE_V6 */'
css = '''
/* RISELOOTER_VISUAL_OVERRIDE_V6 */
.hero{min-height:560px!important;position:relative!important;overflow:hidden!important;background:#070b0e!important}
.hero:after{content:""!important;position:absolute!important;inset:0!important;z-index:4!important;background:linear-gradient(90deg,rgba(5,9,13,.995) 0%,rgba(5,9,13,.985) 28%,rgba(5,9,13,.86) 40%,rgba(5,9,13,.35) 53%,rgba(5,9,13,.08) 72%,rgba(5,9,13,0) 100%)!important;pointer-events:none!important}
.character-holder{position:absolute!important;top:0!important;right:0!important;bottom:0!important;left:31%!important;width:auto!important;height:auto!important;z-index:1!important;transform:none!important;display:block!important;overflow:hidden!important;animation:none!important}
.character-holder>div{position:absolute!important;inset:0!important;width:100%!important;height:100%!important;overflow:hidden!important;transform-origin:54% 78%!important;animation:riseBodyBreathe 5.2s ease-in-out infinite!important}
.character-holder img{position:absolute!important;inset:0!important;width:100%!important;height:100%!important;object-fit:cover!important;object-position:center 27%!important;transform-origin:54% 78%!important;filter:saturate(.96) contrast(1.03)!important;animation:riseIdleImage 8.5s ease-in-out infinite!important}
.character-holder:before{content:""!important;position:absolute!important;left:0!important;top:0!important;width:54%!important;height:145px!important;z-index:3!important;background:linear-gradient(135deg,rgba(5,9,13,1) 0%,rgba(5,9,13,.99) 45%,rgba(5,9,13,.88) 68%,rgba(5,9,13,0) 100%)!important;pointer-events:none!important}
.character-holder:after{content:""!important;position:absolute!important;left:0!important;right:0!important;bottom:0!important;height:84px!important;z-index:3!important;background:linear-gradient(0deg,rgba(5,9,13,1) 0%,rgba(5,9,13,.90) 52%,rgba(5,9,13,0) 100%)!important;pointer-events:none!important}
@keyframes riseBodyBreathe{0%,100%{transform:translateY(0) scaleY(1)}45%{transform:translateY(-1px) scaleY(1.004)}55%{transform:translateY(-2px) scaleY(1.006)}}
@keyframes riseIdleImage{0%,100%{transform:scale(1.015) translateX(0) translateY(0) rotate(0deg)}24%{transform:scale(1.018) translateX(-1px) translateY(-1px) rotate(-.08deg)}52%{transform:scale(1.022) translateX(1px) translateY(-2px) rotate(.10deg)}76%{transform:scale(1.018) translateX(0) translateY(-1px) rotate(-.05deg)}}
.hero-copy,.next-evolution,.hero-track{z-index:9!important}
.hero-track{padding-top:8px!important;background:linear-gradient(0deg,rgba(4,9,14,.99) 0%,rgba(4,9,14,.88) 60%,rgba(4,9,14,0) 100%)!important}
.next-evolution{background:rgba(4,10,16,.96)!important;backdrop-filter:blur(3px)!important}
.shadow-character{height:145px!important;margin:10px auto!important;overflow:hidden!important;border-radius:8px!important;position:relative!important;background:#080d12!important;box-shadow:inset 0 0 30px rgba(0,0,0,.82)!important}
.shadow-character:before{content:""!important;position:absolute!important;left:0!important;top:0!important;width:100%!important;height:42px!important;z-index:3!important;background:linear-gradient(180deg,rgba(4,10,16,.99),rgba(4,10,16,.86),rgba(4,10,16,0))!important;pointer-events:none!important}
.shadow-character img{width:100%!important;height:100%!important;max-width:none!important;object-fit:cover!important;object-position:center 30%!important;transform:scale(1.03)!important;filter:brightness(.13) grayscale(1) contrast(1.42)!important;opacity:.98!important}
.evolution-character{overflow:hidden!important;border-radius:7px!important;position:relative!important}
.evolution-card.locked .evolution-character:before{content:""!important;position:absolute!important;left:0!important;right:0!important;top:0!important;height:32px!important;z-index:3!important;background:linear-gradient(180deg,rgba(5,9,13,.98),rgba(5,9,13,0))!important;pointer-events:none!important}
.evolution-card.locked .evolution-character img{width:100%!important;height:100%!important;object-fit:cover!important;object-position:center 30%!important;transform:scale(1.03)!important;filter:brightness(.13) grayscale(1) contrast(1.42)!important;opacity:.98!important}
@media (prefers-reduced-motion: reduce){.character-holder>div,.character-holder img{animation:none!important}}
'''

if marker not in s:
    s = s.replace('</style>', css + '\n</style>', 1)

p.write_text(s, encoding='utf-8')
