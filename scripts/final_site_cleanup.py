from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Cache-bust regenerated creator assets so browsers never keep the previous broken images.
s = s.replace('return `assets/creator/male/${skin}/${hairColor}/${hairStyle}.webp`;',
              'return `assets/creator/male/${skin}/${hairColor}/${hairStyle}.webp?v=25`;')
s = s.replace('return `assets/creator/male/${avatarDraft.skin}/${avatarDraft.hairColor}/${avatarDraft.hairStyle}.webp`;',
              'return `assets/creator/male/${avatarDraft.skin}/${avatarDraft.hairColor}/${avatarDraft.hairStyle}.webp?v=25`;')
s = s.replace("? `assets/creator/male/${avatarDraft.skin}/${avatarDraft.hairColor}/${value}.webp`",
              "? `assets/creator/male/${avatarDraft.skin}/${avatarDraft.hairColor}/${value}.webp?v=25`")

marker_start = '/* RISELOOTER_FINAL_CLEAN_V25 */'
marker_end = '/* /RISELOOTER_FINAL_CLEAN_V25 */'
css = r'''
/* RISELOOTER_FINAL_CLEAN_V25 */
/* Final creator presentation: only complete pre-rendered artwork, never synthetic overlays. */
#creatorModal .creator-skin-overlay,
#creatorModal .creator-hair-overlay{display:none!important}
#creatorModal .creator-preview{background:#03080d!important;overflow:hidden!important}
#creatorModal .creator-real-preview{
  width:100%!important;height:100%!important;max-width:none!important;
  object-fit:cover!important;object-position:72% 20%!important;
  filter:none!important;mix-blend-mode:normal!important;
  transform:scale(1.035)!important;animation:none!important;
}
#hairStyleChoices .hair-choice{min-height:116px!important;grid-template-rows:80px auto!important}
#hairStyleChoices .hair-thumb{
  width:100%!important;height:80px!important;background-repeat:no-repeat!important;
  background-size:335% auto!important;background-position:71% 7%!important;
  border-radius:7px!important;background-color:#071018!important;
}
/* Features intentionally removed from the simplified product. */
#shop,#inventory,#dailyChest,
nav [data-nav="shop"],nav [data-nav="inventory"]{display:none!important}
/* Keep the validated static character crisp: no fake whole-image breathing motion. */
.character-holder,.character-holder img,.scene-clean-image{animation:none!important}
/* Prevent old visual patches from drawing cover rectangles on the hero. */
.character-holder:before,.character-holder>div:after{display:none!important;content:none!important}
/* /RISELOOTER_FINAL_CLEAN_V25 */
'''

if marker_start in s and marker_end in s:
    s = re.sub(re.escape(marker_start) + r'.*?' + re.escape(marker_end), css.strip(), s, count=1, flags=re.S)
else:
    # Last style block wins over all historical overrides.
    pos = s.rfind('</style>')
    if pos == -1:
        raise SystemExit('No style block found')
    s = s[:pos] + '\n' + css + '\n' + s[pos:]

# Improve the missing-female state without showing a fake male avatar.
s = s.replace('BASE FÉMININE À INTÉGRER', 'MODÈLE FÉMININ EN PRÉPARATION')
s = s.replace('Le dépôt ne contient pas encore le modèle féminin validé. Aucun faux personnage ne sera affiché à sa place.',
              'La base féminine photoréaliste sera ajoutée séparément afin de conserver la même qualité que le modèle masculin.')

p.write_text(s, encoding='utf-8')
print('Final site cleanup V25 applied')
