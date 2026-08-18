from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Stage 1 and creator preview both use the exact complete preset image for the
# selected gender/skin/hair combination. Later evolution stages keep their own
# dedicated evolution library.
asset_fn = r'''function assetPath(profile,stage){
  const gender = profile?.avatar_gender || "male";
  const skin = profile?.avatar_skin || "medium";
  const hairColor = profile?.avatar_hair_color || "brown";
  const hairStyle = profile?.avatar_hair_style || (gender === "female" ? "female_long" : "male_textured");
  if(stage === 0){
    return `assets/creator/${gender}/${skin}/${hairColor}/${hairStyle}.webp?v=presets30`;
  }
  return `assets/characters/${gender}/${skin}/${hairColor}/${hairStyle}/${stages[stage].slug}.webp`;
}'''
s = re.sub(r'function assetPath\(profile,stage\)\{.*?\n\}', asset_fn, s, count=1, flags=re.S)

creator_fn = r'''function creatorAssetPath(){
  return `assets/creator/${avatarDraft.gender}/${avatarDraft.skin}/${avatarDraft.hairColor}/${avatarDraft.hairStyle}.webp?v=presets30`;
}

function creatorFallbackPath(gender=avatarDraft.gender){
  const style = gender === "female" ? "female_long" : "male_textured";
  return `assets/creator/${gender}/medium/brown/${style}.webp?v=presets30`;
}'''
s = re.sub(r'function creatorAssetPath\(\)\{.*?\n\}', creator_fn, s, count=1, flags=re.S)

# Same-gender fallback on the main dashboard for level 1.
character_fn = r'''function characterHTML(profile,stage){
const preferred=assetPath(profile,stage);
const gender=profile?.avatar_gender || "male";
const fallback=stage===0
  ? `assets/creator/${gender}/medium/brown/${gender === "female" ? "female_long" : "male_textured"}.webp?v=presets30`
  : fallbackAssetPath(stage);
return `<div class="character-scene-clean"><img class="scene-clean-image" src="${preferred}" alt="Looter" data-fallback="${fallback}" data-tried-fallback="0" onerror="if(this.dataset.triedFallback!=='1'){this.dataset.triedFallback='1';this.src=this.dataset.fallback}else{this.style.display='none';this.nextElementSibling.style.display='block'}"><div class="character-missing" style="display:none">Asset réaliste manquant.</div></div>`;
}'''
s = re.sub(r'function characterHTML\(profile,stage\)\{.*?\n\}', character_fn, s, count=1, flags=re.S)

# Preview retries a safe complete same-gender asset before showing an error.
preview_fn = r'''function updateCreatorPreview(){
const preview=$("creatorPreview");
if(!preview) return;
const src=creatorAssetPath();
const fallback=creatorFallbackPath();
preview.innerHTML = `
<img class="creator-real-preview" src="${src}" alt="Aperçu Looter" data-fallback="${fallback}" data-tried-fallback="0"
 onload="document.getElementById('saveAvatar').disabled=false"
 onerror="if(this.dataset.triedFallback!=='1'){this.dataset.triedFallback='1';this.src=this.dataset.fallback}else{this.style.display='none';this.nextElementSibling.style.display='grid';document.getElementById('saveAvatar').disabled=true}">
<div class="creator-empty creator-asset-missing" style="display:none">
  <strong>VARIANTE INDISPONIBLE</strong>
  <span>Le preset n'a pas pu être chargé.</span>
</div>
<div class="creator-live-badge"><b>NIVEAU 1</b><strong>DÉBUTANT</strong></div>`;
}'''
s = re.sub(r'function updateCreatorPreview\(\)\{.*?\n\}', preview_fn, s, count=1, flags=re.S)

# Every hairstyle button previews the exact selected gender/skin/hair colour.
s = re.sub(
    r'const thumb = .*?;',
    'const thumb = `assets/creator/${avatarDraft.gender}/${avatarDraft.skin}/${avatarDraft.hairColor}/${value}.webp?v=presets30`;',
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
print('Creator preset routing and same-gender fallbacks enabled')
