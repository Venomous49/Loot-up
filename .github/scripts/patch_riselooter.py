from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Keep Cloudflare direct-upload asset paths.
s = s.replace(
    'return `/assets/characters/male/medium/brown/male_textured/${stages[stage].slug}.webp`;',
    'return `/${stages[stage].slug}.webp`;'
)
s = s.replace(
    'return "/assets/characters/male/medium/brown/male_textured/01-debutant.webp";',
    'return "/01-debutant.webp";'
)

# Remove previous visual overrides so this patch is deterministic.
s = re.sub(
    r'/\* RISELOOTER_VISUAL_OVERRIDE_V[0-9]+ \*/.*?(?=</style>)',
    '',
    s,
    count=1,
    flags=re.S
)

css = r'''
/* RISELOOTER_VISUAL_OVERRIDE_V4 */
.hero{
  min-height:560px!important;
  position:relative!important;
  overflow:hidden!important;
  background:linear-gradient(90deg,#070b0e 0%,#0a0f13 36%,#11100d 100%)!important;
}
.hero:after{
  content:""!important;
  position:absolute!important;
  inset:0!important;
  z-index:4!important;
  pointer-events:none!important;
  background:
    linear-gradient(90deg,rgba(4,8,12,.98) 0%,rgba(4,8,12,.97) 26%,rgba(4,8,12,.78) 39%,rgba(4,8,12,.24) 54%,rgba(4,8,12,0) 72%),
    linear-gradient(180deg,rgba(4,8,12,.16) 0%,rgba(4,8,12,0) 70%,rgba(4,8,12,.88) 100%)!important;
}

/* Main scene: fill the visual side cleanly, keep the full character readable,
   and bury the labels that are baked into the source image. */
.character-holder{
  position:absolute!important;
  top:0!important;
  right:0!important;
  bottom:58px!important;
  left:34%!important;
  width:66%!important;
  height:auto!important;
  z-index:1!important;
  transform:none!important;
  display:block!important;
  overflow:hidden!important;
  animation:none!important;
}
.character-holder>div{
  position:absolute!important;
  inset:-10% -7% -8% -7%!important;
  width:auto!important;
  height:auto!important;
  overflow:hidden!important;
}
.character-holder img{
  position:absolute!important;
  inset:0!important;
  width:100%!important;
  height:100%!important;
  object-fit:cover!important;
  object-position:center 50%!important;
  transform:scale(1.10)!important;
  filter:saturate(.96) contrast(1.04)!important;
  animation:riseSceneIdleV4 7s ease-in-out infinite!important;
}
.character-holder>div:after{
  content:""!important;
  position:absolute!important;
  inset:0!important;
  z-index:3!important;
  pointer-events:none!important;
  background:
    linear-gradient(90deg,rgba(5,9,13,.72) 0%,rgba(5,9,13,.22) 24%,rgba(5,9,13,0) 46%),
    linear-gradient(180deg,rgba(5,9,13,.42) 0%,rgba(5,9,13,0) 18%,rgba(5,9,13,0) 82%,rgba(5,9,13,.82) 100%)!important;
}
@keyframes riseSceneIdleV4{
  0%,100%{transform:scale(1.10) translateY(0)}
  50%{transform:scale(1.105) translateY(-.6%)}
}

.hero-copy,.next-evolution,.hero-track{z-index:9!important}
.next-evolution{
  background:rgba(4,10,16,.93)!important;
  backdrop-filter:blur(3px)!important;
}

/* Next evolution: dark preview of the real next skin, not a black rectangle. */
.shadow-character{
  height:145px!important;
  margin:10px auto!important;
  overflow:hidden!important;
  border-radius:8px!important;
  position:relative!important;
  background:#0a1117!important;
  box-shadow:inset 0 0 26px rgba(0,0,0,.68)!important;
}
.shadow-character img{
  width:100%!important;
  height:100%!important;
  max-width:none!important;
  object-fit:cover!important;
  object-position:center 45%!important;
  transform:scale(1.28)!important;
  filter:brightness(.42) grayscale(.88) contrast(1.12) saturate(.35)!important;
  opacity:1!important;
}
.shadow-character:after{
  content:""!important;
  position:absolute!important;
  inset:0!important;
  pointer-events:none!important;
  background:linear-gradient(180deg,rgba(1,4,7,.18),rgba(1,4,7,.48)),radial-gradient(circle at 50% 42%,transparent 18%,rgba(0,0,0,.32) 75%)!important;
}
.generic-shadow{display:none!important}

/* Locked evolution cards: real silhouettes with just enough detail to create suspense. */
.evolution-character{
  overflow:hidden!important;
  border-radius:7px!important;
}
.evolution-card.locked .evolution-character img{
  width:100%!important;
  height:100%!important;
  object-fit:cover!important;
  object-position:center 45%!important;
  transform:scale(1.26)!important;
  filter:brightness(.34) grayscale(.92) contrast(1.16) saturate(.3)!important;
  opacity:1!important;
}
.evolution-card.locked .evolution-character:after{
  content:""!important;
  position:absolute!important;
  inset:0!important;
  pointer-events:none!important;
  background:linear-gradient(180deg,rgba(2,5,8,.12),rgba(2,5,8,.50)),radial-gradient(circle at 50% 38%,transparent 14%,rgba(0,0,0,.28) 76%)!important;
}
'''

s = s.replace('</style>', css + '\n</style>', 1)

p.write_text(s, encoding='utf-8')
