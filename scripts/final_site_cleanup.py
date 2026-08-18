from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Creator presets are complete pre-rendered images. Never build a face/hair
# from browser-side overlays: simply select the matching full image.
creator_fn = r'''function creatorAssetPath(){
  return `assets/creator/${avatarDraft.gender}/${avatarDraft.skin}/${avatarDraft.hairColor}/${avatarDraft.hairStyle}.webp?v=presets29`;
}'''
s = re.sub(r'function creatorAssetPath\(\)\{.*?\n\}', creator_fn, s, count=1, flags=re.S)

# Every hairstyle button previews the exact selected gender/skin/hair colour.
s = re.sub(
    r'const thumb = .*?;',
    'const thumb = `assets/creator/${avatarDraft.gender}/${avatarDraft.skin}/${avatarDraft.hairColor}/${value}.webp?v=presets29`;',
    s,
    count=1,
)

marker_start = '/* RISELOOTER_FINAL_CLEAN_V25 */'
marker_end = '/* /RISELOOTER_FINAL_CLEAN_V25 */'
css = r'''
/* RISELOOTER_FINAL_CLEAN_V25 */
/* Complete-image presets only: no synthetic head/skin/hair overlays. */
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
print('Creator preset routing enabled for male and female full-image assets')
