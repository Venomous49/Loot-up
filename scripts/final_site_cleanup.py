from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# SAFETY FIRST: never show a distorted/generated head. Until the full preset
# library is rebuilt from clean complete images, the male creator uses the
# validated original artwork as a clean fallback. No browser-side overlay,
# tint, mask or synthetic head is allowed.
creator_fn = r'''function creatorAssetPath(){
  if(avatarDraft.gender === "female"){
    return `assets/creator/female/${avatarDraft.skin}/${avatarDraft.hairColor}/${avatarDraft.hairStyle}.webp?v=fullpreset28`;
  }
  return `01-debutant.webp?v=cleanbase28`;
}'''
s = re.sub(r'function creatorAssetPath\(\)\{.*?\n\}', creator_fn, s, count=1, flags=re.S)

# While the new full-image preset library is being rebuilt, male hairstyle
# thumbnails also use the clean validated artwork instead of corrupted variants.
s = re.sub(
    r'const thumb = `assets/creator/\$\{avatarDraft\.gender\}/\$\{avatarDraft\.skin\}/\$\{avatarDraft\.hairColor\}/\$\{value\}\.webp\?v=[^`]+`;',
    'const thumb = avatarDraft.gender === "male" ? `01-debutant.webp?v=cleanbase28` : `assets/creator/female/${avatarDraft.skin}/${avatarDraft.hairColor}/${value}.webp?v=fullpreset28`;',
    s,
    count=1,
)

marker_start = '/* RISELOOTER_FINAL_CLEAN_V25 */'
marker_end = '/* /RISELOOTER_FINAL_CLEAN_V25 */'
css = r'''
/* RISELOOTER_FINAL_CLEAN_V25 */
/* Only complete images are displayed. Synthetic head/skin/hair overlays are forbidden. */
#creatorModal .creator-skin-overlay,
#creatorModal .creator-hair-overlay{display:none!important;visibility:hidden!important;opacity:0!important}
#creatorModal .creator-preview{background:#03080d!important;overflow:hidden!important}
#creatorModal .creator-real-preview{
  width:100%!important;height:100%!important;max-width:none!important;
  object-fit:cover!important;object-position:center 18%!important;
  filter:none!important;mix-blend-mode:normal!important;
  transform:none!important;animation:none!important;
}
#hairStyleChoices .hair-choice{min-height:116px!important;grid-template-rows:80px auto!important}
#hairStyleChoices .hair-thumb{
  width:100%!important;height:80px!important;background-repeat:no-repeat!important;
  background-size:cover!important;background-position:center 12%!important;
  border-radius:7px!important;background-color:#071018!important;
}
#shop,#inventory,#dailyChest,
nav [data-nav="shop"],nav [data-nav="inventory"]{display:none!important}
.character-holder,.character-holder img,.scene-clean-image{animation:none!important}
.character-holder:before,.character-holder>div:after{display:none!important;content:none!important}
/* /RISELOOTER_FINAL_CLEAN_V25 */
'''

if marker_start in s and marker_end in s:
    s = re.sub(re.escape(marker_start) + r'.*?' + re.escape(marker_end), css.strip(), s, count=1, flags=re.S)
else:
    pos = s.rfind('</style>')
    if pos == -1:
        raise SystemExit('No style block found')
    s = s[:pos] + '\n' + css + '\n' + s[pos:]

p.write_text(s, encoding='utf-8')
print('Creator safety cleanup applied: no distorted synthetic head can be displayed')
