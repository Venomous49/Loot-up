from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Root-level static character assets copied by the workflow.
s = re.sub(
    r'function assetPath\(profile,stage\)\{.*?\n\}',
    '''function assetPath(profile,stage){\n\nreturn `${stages[stage].slug}.webp`;\n\n}''',
    s,
    count=1,
    flags=re.S
)

s = re.sub(
    r'function creatorAssetPath\(\)\{.*?\n\}',
    '''function creatorAssetPath(){\n\nreturn "01-debutant.webp";\n\n}''',
    s,
    count=1,
    flags=re.S
)

# Clean up paths left by previous experiments.
s = re.sub(
    r'https://raw\.githubusercontent\.com/Venomous49/Loot-up/main/assets/characters/male/medium/brown/male_textured/([0-9]{2}-[a-z-]+\.webp)',
    r'\1',
    s
)
s = re.sub(
    r'/?assets/characters/male/medium/brown/male_textured/([0-9]{2}-[a-z-]+\.webp)',
    r'\1',
    s
)

new_character = r'''function characterHTML(profile,stage){

const base = assetPath(profile,stage);

return `
<div class="character-scene-clean">
  <img class="scene-clean-image" src="${base}" alt="Looter" onerror="this.style.display='none';this.nextElementSibling.style.display='block'">
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

marker = '/* RISELOOTER_SIMPLIFIED_V14 */'
css = r'''
/* RISELOOTER_SIMPLIFIED_V14 */

/* Simplified navigation and sections */
[data-nav="shop"],
[data-nav="inventory"],
#shop,
#inventory,
#dailyChest{
  display:none!important;
}

/* Main hero: static, crisp artwork */
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
.character-holder .character-scene-clean{
  position:absolute!important;
  inset:0!important;
  width:100%!important;
  height:100%!important;
  overflow:hidden!important;
  animation:none!important;
  transform:none!important;
}
.character-holder .scene-clean-image{
  position:absolute!important;
  inset:0!important;
  width:100%!important;
  height:100%!important;
  object-fit:cover!important;
  object-position:center 23%!important;
  transform:none!important;
  animation:none!important;
  filter:none!important;
  opacity:1!important;
}

/* Hide baked text on the left with a full-height horizontal fade.
   Full height avoids the old hard horizontal edge crossing the face. */
.character-holder .character-scene-clean:before{
  content:""!important;
  display:block!important;
  position:absolute!important;
  left:0!important;
  top:0!important;
  width:39%!important;
  height:100%!important;
  z-index:7!important;
  pointer-events:none!important;
  background:linear-gradient(90deg,#05090d 0%,rgba(5,9,13,.99) 48%,rgba(5,9,13,.72) 72%,rgba(5,9,13,0) 100%)!important;
}
.character-holder .character-scene-clean:after{
  content:""!important;
  display:block!important;
  position:absolute!important;
  left:20%!important;
  right:7%!important;
  bottom:0!important;
  height:55px!important;
  z-index:7!important;
  pointer-events:none!important;
  background:linear-gradient(0deg,#05090d 0%,rgba(5,9,13,.88) 45%,rgba(5,9,13,0) 100%)!important;
}

/* Next evolution: use the real next asset as a visible dark silhouette. */
.next-evolution{
  background:rgba(4,10,16,.96)!important;
  backdrop-filter:blur(3px)!important;
}
.shadow-character{
  height:145px!important;
  margin:10px auto!important;
  overflow:hidden!important;
  border-radius:8px!important;
  position:relative!important;
  background:radial-gradient(circle at 50% 42%,#3a4650 0%,#202a32 48%,#10161c 100%)!important;
  box-shadow:inset 0 0 24px rgba(0,0,0,.55)!important;
}
.shadow-character img{
  display:block!important;
  width:100%!important;
  height:100%!important;
  max-width:none!important;
  object-fit:cover!important;
  object-position:center 28%!important;
  transform:scale(1.02)!important;
  filter:brightness(.16) grayscale(1) contrast(1.38)!important;
  opacity:1!important;
}
.generic-shadow{display:none!important}

/* Evolution path: every locked level shows the real character silhouette. */
.evolution-card .character-scene-clean{
  position:absolute!important;
  inset:0!important;
  width:100%!important;
  height:100%!important;
  overflow:hidden!important;
}
.evolution-card .character-scene-clean:before,
.evolution-card .character-scene-clean:after{
  display:none!important;
  content:none!important;
}
.evolution-card .scene-clean-image{
  display:block!important;
  position:absolute!important;
  inset:0!important;
  width:100%!important;
  height:100%!important;
  object-fit:cover!important;
  object-position:center 28%!important;
  transform:scale(1.02)!important;
  opacity:1!important;
}
.evolution-card.locked{
  background:radial-gradient(circle at 50% 40%,#3c4852 0%,#222c34 48%,#10161b 100%)!important;
}
.evolution-card.locked .scene-clean-image{
  filter:brightness(.15) grayscale(1) contrast(1.42)!important;
  opacity:1!important;
}
.evolution-card.unlocked .scene-clean-image{
  filter:none!important;
}

/* Remove every experimental animation layer from previous versions. */
.scene-background,.scene-body,.scene-torso,.scene-head,.character-scene-real{
  display:none!important;
  animation:none!important;
}
'''

if marker not in s:
    s = s.replace('</style>', css + '\n</style>', 1)

p.write_text(s, encoding='utf-8')
