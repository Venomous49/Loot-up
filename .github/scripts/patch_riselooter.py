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

marker = '/* RISELOOTER_VISUAL_OVERRIDE_V5 */'
css = '''
/* RISELOOTER_VISUAL_OVERRIDE_V5 */
.hero{
  min-height:560px!important;
  position:relative!important;
  overflow:hidden!important;
  background:#070b0e!important;
}
.hero:after{
  content:""!important;
  position:absolute!important;
  inset:0!important;
  z-index:4!important;
  background:linear-gradient(90deg,rgba(5,9,13,.99) 0%,rgba(5,9,13,.96) 25%,rgba(5,9,13,.78) 38%,rgba(5,9,13,.28) 52%,rgba(5,9,13,.06) 72%,rgba(5,9,13,0) 100%)!important;
  pointer-events:none!important;
}
.character-holder{
  position:absolute!important;
  top:0!important;
  right:0!important;
  bottom:0!important;
  left:31%!important;
  width:auto!important;
  height:auto!important;
  z-index:1!important;
  transform:none!important;
  display:block!important;
  overflow:hidden!important;
  animation:none!important;
}
.character-holder>div{
  position:absolute!important;
  inset:0!important;
  width:100%!important;
  height:100%!important;
}
.character-holder img{
  position:absolute!important;
  inset:0!important;
  width:100%!important;
  height:100%!important;
  object-fit:cover!important;
  object-position:center 27%!important;
  transform:scale(1.015)!important;
  filter:saturate(.96) contrast(1.03)!important;
  animation:riseSceneIdleV5 7s ease-in-out infinite!important;
}
.character-holder:before{
  content:""!important;
  position:absolute!important;
  left:0!important;
  top:0!important;
  width:45%!important;
  height:125px!important;
  z-index:3!important;
  background:linear-gradient(135deg,rgba(5,9,13,.98) 0%,rgba(5,9,13,.9) 45%,rgba(5,9,13,0) 100%)!important;
  pointer-events:none!important;
}
.character-holder:after{
  content:""!important;
  position:absolute!important;
  left:0!important;
  right:0!important;
  bottom:0!important;
  height:74px!important;
  z-index:3!important;
  background:linear-gradient(0deg,rgba(5,9,13,.98) 0%,rgba(5,9,13,.76) 46%,rgba(5,9,13,0) 100%)!important;
  pointer-events:none!important;
}
@keyframes riseSceneIdleV5{
  0%,100%{transform:scale(1.015) translateY(0)}
  50%{transform:scale(1.022) translateY(-2px)}
}
.hero-copy,.next-evolution,.hero-track{
  z-index:9!important;
}
.hero-track{
  padding-top:8px!important;
  background:linear-gradient(0deg,rgba(4,9,14,.98) 0%,rgba(4,9,14,.82) 58%,rgba(4,9,14,0) 100%)!important;
}
.next-evolution{
  background:rgba(4,10,16,.95)!important;
  backdrop-filter:blur(3px)!important;
}
.shadow-character{
  height:145px!important;
  margin:10px auto!important;
  overflow:hidden!important;
  border-radius:8px!important;
  position:relative!important;
  background:#080d12!important;
  box-shadow:inset 0 0 26px rgba(0,0,0,.72)!important;
}
.shadow-character img{
  width:100%!important;
  height:100%!important;
  max-width:none!important;
  object-fit:cover!important;
  object-position:center 30%!important;
  transform:scale(1.03)!important;
  filter:brightness(.18) grayscale(1) contrast(1.30)!important;
  opacity:.98!important;
}
.evolution-character{
  overflow:hidden!important;
  border-radius:7px!important;
}
.evolution-card.locked .evolution-character img{
  width:100%!important;
  height:100%!important;
  object-fit:cover!important;
  object-position:center 30%!important;
  transform:scale(1.03)!important;
  filter:brightness(.16) grayscale(1) contrast(1.32)!important;
  opacity:.98!important;
}
'''

if marker not in s:
    s = s.replace('</style>', css + '\n</style>', 1)

p.write_text(s, encoding='utf-8')
