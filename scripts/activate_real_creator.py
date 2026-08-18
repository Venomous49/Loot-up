from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')
marker='RISELOOTER_REAL_CREATOR_V23'
ASSET_VERSION='safehair27'

s=re.sub(
    r'function assetPath\(profile,stage\)\{.*?\n\}',
    '''function assetPath(profile,stage){\n  const gender = profile?.avatar_gender || "male";\n  const skin = profile?.avatar_skin || "medium";\n  const hairColor = profile?.avatar_hair_color || "brown";\n  const hairStyle = profile?.avatar_hair_style || "male_textured";\n  if(stage === 0 && gender === "male"){\n    return `assets/creator/male/${skin}/${hairColor}/${hairStyle}.webp?v=safehair27`;\n  }\n  return `assets/characters/${gender}/${skin}/${hairColor}/${hairStyle}/${stages[stage].slug}.webp`;\n}''',
    s,count=1,flags=re.S
)

s=re.sub(
    r'function creatorAssetPath\(\)\{.*?\n\}',
    '''function creatorAssetPath(){\n  if(avatarDraft.gender === "female"){\n    return `assets/creator/female/${avatarDraft.skin}/${avatarDraft.hairColor}/${avatarDraft.hairStyle}.webp?v=safehair27`;\n  }\n  return `assets/creator/male/${avatarDraft.skin}/${avatarDraft.hairColor}/${avatarDraft.hairStyle}.webp?v=safehair27`;\n}''',
    s,count=1,flags=re.S
)

preview=r'''function updateCreatorPreview(){
const preview=$("creatorPreview");
if(!preview) return;
const src=creatorAssetPath();
const female=avatarDraft.gender === "female";
preview.innerHTML = `
<img class="creator-real-preview" src="${src}" alt="Aperçu Looter"
 onload="document.getElementById('saveAvatar').disabled=false"
 onerror="this.style.display='none';this.nextElementSibling.style.display='grid';document.getElementById('saveAvatar').disabled=true">
<div class="creator-empty creator-asset-missing" style="display:none">
  <strong>${female ? "BASE FÉMININE À INTÉGRER" : "VARIANTE INDISPONIBLE"}</strong>
  <span>${female ? "Le modèle féminin est en cours d'intégration." : "Cette variante n'a pas pu être chargée."}</span>
</div>
<div class="creator-live-badge"><b>NIVEAU 1</b><strong>DÉBUTANT</strong></div>`;
}'''
s=re.sub(
    r'function updateCreatorPreview\(\)\{.*?\n\}\n\n/\* ==========================================================\nCOIFFURES',
    preview+'\n\n/* ==========================================================\nCOIFFURES',
    s,count=1,flags=re.S
)

hair=r'''function renderHairChoices(){
const list = avatarDraft.gender === "female" ? femaleHair : maleHair;
if(!list.some(x => x[0] === avatarDraft.hairStyle)) avatarDraft.hairStyle=list[0][0];

$("hairStyleChoices").innerHTML = list.map(([value,label]) => {
  const thumb = `assets/creator/${avatarDraft.gender}/${avatarDraft.skin}/${avatarDraft.hairColor}/${value}.webp?v=safehair27`;
  return `<button class="choice hair-choice ${avatarDraft.hairStyle===value?"selected":""}" data-value="${value}">
    <span class="hair-thumb" style="background-image:url('${thumb}')"></span>
    <span>${label}</span>
  </button>`;
}).join("");

$("hairStyleChoices").querySelectorAll(".choice").forEach(btn=>{
  btn.onclick=()=>{
    avatarDraft.hairStyle=btn.dataset.value;
    renderHairChoices();
    updateCreatorPreview();
  };
});
}'''
s=re.sub(
    r'function renderHairChoices\(\)\{.*?\n\}\n\n/\* ==========================================================\nGROUPES CHOIX',
    hair+'\n\n/* ==========================================================\nGROUPES CHOIX',
    s,count=1,flags=re.S
)

css=r'''
/* RISELOOTER_REAL_CREATOR_V23 */
#creatorModal .creator-skin-overlay,
#creatorModal .creator-hair-overlay{display:none!important;content:none!important}
#creatorModal .creator-preview{position:relative!important;overflow:hidden!important;background:#03090d!important}
#creatorModal .creator-real-preview{display:block;width:100%!important;height:100%!important;object-fit:cover!important;object-position:center 16%!important;filter:none!important;mix-blend-mode:normal!important;transform:none!important;animation:none!important}
#creatorModal .creator-asset-missing{height:100%;padding:40px;place-content:center;text-align:center;gap:10px;color:#aab7c2;background:radial-gradient(circle at 50% 35%,#15212a,#050a0e 65%)}
#creatorModal .creator-asset-missing strong{color:#fff;font-size:18px}#creatorModal .creator-asset-missing span{max-width:420px;font-size:13px;line-height:1.45}
#skinChoices .choice,#hairColorChoices .choice{background:#071019!important;position:relative!important;padding:8px!important}
#skinChoices .choice:before,#hairColorChoices .choice:before{content:"";display:block;width:100%;height:48px;border-radius:6px;border:1px solid rgba(255,255,255,.12)}
#skinChoices [data-value="light"]:before{background:#dab09a}#skinChoices [data-value="warm"]:before{background:#be8052}#skinChoices [data-value="medium"]:before{background:#96613c}#skinChoices [data-value="deep"]:before{background:#694227}#skinChoices [data-value="dark"]:before{background:#3e2619}
#hairColorChoices [data-value="black"]:before{background:#141214}#hairColorChoices [data-value="brown"]:before{background:#3a261c}#hairColorChoices [data-value="blond"]:before{background:#b99058}#hairColorChoices [data-value="red"]:before{background:#8a3d24}#hairColorChoices [data-value="purple"]:before{background:#583470}
#skinChoices .choice.selected,#hairColorChoices .choice.selected{background:#140a22!important;box-shadow:0 0 0 2px #9841ff,0 0 18px rgba(143,63,255,.28)!important}
#skinChoices .choice.selected:after,#hairColorChoices .choice.selected:after{z-index:5}
#hairStyleChoices .hair-choice{min-height:108px!important;padding:6px!important;display:grid!important;grid-template-rows:72px auto!important;gap:5px!important;align-items:center!important;background:#08131c!important;overflow:hidden!important}
#hairStyleChoices .hair-choice:before{display:none!important;content:none!important}
.hair-thumb{display:block;width:100%;height:72px;border-radius:6px;background-color:#101b23;background-size:260% auto;background-position:58% 7%;background-repeat:no-repeat;border:1px solid rgba(255,255,255,.08)}
#hairStyleChoices .hair-choice>span:last-child{font-size:11px;font-weight:800;line-height:1.1}
#hairStyleChoices .hair-choice.selected{border-color:#a146ff!important;box-shadow:0 0 0 1px #a146ff,0 0 16px rgba(143,63,255,.28)!important}
'''
if marker not in s:
    s=s.replace('</style>',css+'\n</style>',1)

if 'RISELOOTER_REFRESH_HAIR_THUMBS_V23' not in s:
    js=r'''
/* RISELOOTER_REFRESH_HAIR_THUMBS_V23 */
["skinChoices","hairColorChoices"].forEach(id=>{
  const root=document.getElementById(id);
  if(!root) return;
  root.addEventListener("click",()=>setTimeout(()=>{renderHairChoices();updateCreatorPreview();},0));
});
'''
    s=s.replace('\n</script>\n\n</body>',js+'\n</script>\n\n</body>',1)

p.write_text(s,encoding='utf-8')
print('real creator integration applied with cache bust', ASSET_VERSION)
