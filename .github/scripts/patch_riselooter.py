from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

RAW = 'https://raw.githubusercontent.com/Venomous49/Loot-up/main/assets/characters/male/medium/brown/male_textured'

s = re.sub(
    r'function assetPath\(profile,stage\)\{.*?\n\}',
    '''function assetPath(profile,stage){\n\nreturn `https://raw.githubusercontent.com/Venomous49/Loot-up/main/assets/characters/male/medium/brown/male_textured/${stages[stage].slug}.webp`;\n\n}''',
    s,
    count=1,
    flags=re.S
)

s = re.sub(
    r'function creatorAssetPath\(\)\{.*?\n\}',
    '''function creatorAssetPath(){\n\nreturn "https://raw.githubusercontent.com/Venomous49/Loot-up/main/assets/characters/male/medium/brown/male_textured/01-debutant.webp";\n\n}''',
    s,
    count=1,
    flags=re.S
)

# Repair any old local/root paths left by previous patches.
s = s.replace('src="/01-debutant.webp"', f'src="{RAW}/01-debutant.webp"')
s = s.replace('src="assets/characters/male/medium/brown/male_textured/01-debutant.webp"', f'src="{RAW}/01-debutant.webp"')
s = s.replace('"/01-debutant.webp"', f'"{RAW}/01-debutant.webp"')
s = s.replace('"assets/characters/male/medium/brown/male_textured/01-debutant.webp"', f'"{RAW}/01-debutant.webp"')

new_character = r'''function characterHTML(profile,stage){

const base = assetPath(profile,stage);
const outfit = outfitOverlayPath(profile.equipped_outfit_slug);

return `
<div class="character-scene-clean">
  <img class="scene-clean-image" src="${base}" alt="Looter" onerror="this.style.display='none';this.nextElementSibling.style.display='block'">
  <div class="character-missing" style="display:none">Asset réaliste manquant.</div>
  ${outfit ? `<img class="scene-outfit-clean" src="${outfit}" alt="Tenue équipée" onerror="this.style.display='none'">` : ""}
</div>`;

}'''

s = re.sub(
    r'function characterHTML\(profile,stage\)\{.*?\n\}\n\n/\* ==========================================================\nAPERÇU CRÉATEUR',
    new_character + '\n\n/* ==========================================================\nAPERÇU CRÉATEUR',
    s,
    count=1,
    flags=re.S
)

marker = '/* RISELOOTER_CLEAN_STATIC_V12 */'
css = r'''
/* RISELOOTER_CLEAN_STATIC_V12 */
.hero{min-height:560px!important;position:relative!important;overflow:hidden!important;background:#070b0e!important}
.hero:after{content:""!important;position:absolute!important;inset:0!important;z-index:4!important;pointer-events:none!important;background:linear-gradient(90deg,rgba(5,9,13,.995) 0%,rgba(5,9,13,.985) 26%,rgba(5,9,13,.80) 39%,rgba(5,9,13,.25) 54%,rgba(5,9,13,.03) 74%,rgba(5,9,13,0) 100%)!important}
.character-holder{position:absolute!important;top:0!important;right:0!important;bottom:0!important;left:31%!important;width:auto!important;height:auto!important;z-index:1!important;transform:none!important;display:block!important;overflow:hidden!important;animation:none!important}
.character-scene-clean{position:absolute!important;inset:0!important;width:100%!important;height:100%!important;overflow:hidden!important;animation:none!important;transform:none!important}
.character-scene-clean .scene-clean-image{position:absolute!important;inset:0!important;width:100%!important;height:100%!important;object-fit:cover!important;object-position:center 23%!important;transform:none!important;animation:none!important;filter:none!important;opacity:1!important;image-rendering:auto!important}
.character-scene-clean:before{content:""!important;position:absolute!important;left:0!important;top:0!important;width:43%!important;height:130px!important;z-index:7!important;pointer-events:none!important;background:linear-gradient(135deg,#05090d 0%,#05090d 61%,rgba(5,9,13,.97) 75%,rgba(5,9,13,0) 100%)!important}
.character-scene-clean:after{content:""!important;position:absolute!important;left:23%!important;right:10%!important;bottom:0!important;height:52px!important;z-index:7!important;pointer-events:none!important;background:linear-gradient(0deg,#05090d 0%,rgba(5,9,13,.96) 42%,rgba(5,9,13,0) 100%)!important}
.scene-outfit-clean{position:absolute!important;inset:0!important;width:100%!important;height:100%!important;object-fit:contain!important;object-position:center bottom!important;z-index:6!important;animation:none!important;transform:none!important;filter:none!important;pointer-events:none!important}
.scene-background,.scene-body,.scene-torso,.scene-head,.character-scene-real{animation:none!important;filter:none!important}
.hero-copy,.next-evolution,.hero-track{z-index:9!important}
.hero-track{padding-top:8px!important;background:linear-gradient(0deg,rgba(4,9,14,.99) 0%,rgba(4,9,14,.88) 60%,rgba(4,9,14,0) 100%)!important}
.next-evolution{background:rgba(4,10,16,.96)!important;backdrop-filter:blur(3px)!important}
.shadow-character{height:145px!important;margin:10px auto!important;overflow:hidden!important;border-radius:8px!important;position:relative!important;background:#080d12!important;box-shadow:inset 0 0 30px rgba(0,0,0,.82)!important}
.shadow-character img{width:100%!important;height:100%!important;max-width:none!important;object-fit:cover!important;object-position:center 28%!important;transform:scale(1.02)!important;filter:brightness(.24) grayscale(1) contrast(1.28)!important;opacity:.98!important}
.generic-shadow{display:none!important}
'''

if marker not in s:
    s = s.replace('</style>', css + '\n</style>', 1)

p.write_text(s, encoding='utf-8')
