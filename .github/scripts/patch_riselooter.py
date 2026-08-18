from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

# ----------------------------------------------------------
# Character asset routing: use saved avatar customization when
# the matching asset exists, but always fall back to the validated
# reference set at repository root so the UI never breaks.
# ----------------------------------------------------------
s=re.sub(r'function assetPath\(profile,stage\)\{.*?\n\}', '''function assetPath(profile,stage){\nconst gender = profile?.avatar_gender || "male";\nconst skin = profile?.avatar_skin || "medium";\nconst hairColor = profile?.avatar_hair_color || "brown";\nconst hairStyle = profile?.avatar_hair_style || "male_textured";\nreturn `assets/characters/${gender}/${skin}/${hairColor}/${hairStyle}/${stages[stage].slug}.webp`;\n}''', s, count=1, flags=re.S)

s=re.sub(r'function creatorAssetPath\(\)\{.*?\n\}', '''function creatorAssetPath(){\nreturn `assets/characters/${avatarDraft.gender}/${avatarDraft.skin}/${avatarDraft.hairColor}/${avatarDraft.hairStyle}/01-debutant.webp`;\n}''', s, count=1, flags=re.S)

if 'function fallbackAssetPath(stage)' not in s:
    s=s.replace('function creatorAssetPath(){\nreturn `assets/characters/${avatarDraft.gender}/${avatarDraft.skin}/${avatarDraft.hairColor}/${avatarDraft.hairStyle}/01-debutant.webp`;\n}', 'function creatorAssetPath(){\nreturn `assets/characters/${avatarDraft.gender}/${avatarDraft.skin}/${avatarDraft.hairColor}/${avatarDraft.hairStyle}/01-debutant.webp`;\n}\n\nfunction fallbackAssetPath(stage){\nreturn `${stages[stage].slug}.webp`;\n}')

if 'function silhouettePath(stage)' in s:
    s=re.sub(r'function silhouettePath\(stage\)\{.*?\n\}', '''function silhouettePath(stage){\nreturn `sil-${stages[stage].slug}.png`;\n}''', s, count=1, flags=re.S)
else:
    s=s.replace('function fallbackAssetPath(stage){\nreturn `${stages[stage].slug}.webp`;\n}', 'function fallbackAssetPath(stage){\nreturn `${stages[stage].slug}.webp`;\n}\n\nfunction silhouettePath(stage){\nreturn `sil-${stages[stage].slug}.png`;\n}')

new_character=r'''function characterHTML(profile,stage){
const preferred=assetPath(profile,stage);
const fallback=fallbackAssetPath(stage);
return `<div class="character-scene-clean"><img class="scene-clean-image" src="${preferred}" alt="Looter" data-fallback="${fallback}" onerror="if(this.src.indexOf(this.dataset.fallback)===-1){this.src=this.dataset.fallback}else{this.style.display='none';this.nextElementSibling.style.display='block'}"><div class="character-missing" style="display:none">Asset réaliste manquant.</div></div>`;
}'''
s=re.sub(r'function characterHTML\(profile,stage\)\{.*?\n\}\n\n/\* ==========================================================\nAPERÇU CRÉATEUR', new_character+'\n\n/* ==========================================================\nAPERÇU CRÉATEUR', s, count=1, flags=re.S)

new_preview=r'''function updateCreatorPreview(){
$("creatorPreview").innerHTML = `
<img src="${creatorAssetPath()}" alt="Aperçu Looter" data-fallback="01-debutant.webp" onerror="if(this.src.indexOf(this.dataset.fallback)===-1){this.src=this.dataset.fallback}else{this.style.display='none';this.nextElementSibling.style.display='block'}">
<div class="creator-empty" style="display:none">Aperçu indisponible pour cette combinaison.</div>`;
}'''
s=re.sub(r'function updateCreatorPreview\(\)\{.*?\n\}\n\n/\* ==========================================================\nCOIFFURES', new_preview+'\n\n/* ==========================================================\nCOIFFURES', s, count=1, flags=re.S)

# Evolution cards: exact validated artwork when unlocked; dedicated silhouette
# of that same validated artwork while locked.
new_grid=r'''function renderEvolutionGrid(profile){
const level = profile.level || 1;
$("evolutionGrid").innerHTML = stages.map((stage,i) => {
  const unlocked = level >= stage.level;
  const visual = unlocked
    ? `<img class="evolution-real" src="${assetPath(profile,i)}" data-fallback="${fallbackAssetPath(i)}" alt="${stage.name}" onerror="if(this.src.indexOf(this.dataset.fallback)===-1){this.src=this.dataset.fallback}else{this.style.display='none'}">`
    : `<img class="evolution-silhouette" src="${silhouettePath(i)}" alt="">`;
  return `
  <div class="evolution-card ${unlocked ? "unlocked" : "locked"}">
    <div class="evolution-character">${visual}</div>
    <div class="evolution-name">
      <span>NIVEAU ${stage.level}</span><br>
      <b>${stage.name}</b><br>
      <small>${unlocked ? escapeHTML(stage.desc) : "Évolution à découvrir"}</small>
    </div>
  </div>`;
}).join("");
}'''
s=re.sub(r'function renderEvolutionGrid\(profile\)\{.*?\n\}\n\n/\* ==========================================================\nPROFIL', new_grid+'\n\n/* ==========================================================\nPROFIL', s, count=1, flags=re.S)

# Next evolution remains a silhouette of the exact next validated artwork.
s=re.sub(
    r'\$\("nextEvolutionShadow"\)\.innerHTML = `.*?`;\n\n}\nelse\{',
    '''$("nextEvolutionShadow").innerHTML = `\n<img class="next-silhouette" src="${silhouettePath(idx + 1)}" alt="">\n`;\n\n}\nelse{''',
    s,
    count=1,
    flags=re.S
)

marker='/* RISELOOTER_REFERENCE_LAYOUT_V18 */'
css=r'''
/* RISELOOTER_REFERENCE_LAYOUT_V18 */
:root{--bg:#02070b!important;--panel:#061019!important;--line:#1e3445!important;--purple:#8f3fff!important;--purple2:#bd74ff!important;--gold:#f5ad20!important;--green:#4de18a!important;--muted:#9eb0bf!important}
body{background:#02070b!important;font-family:Arial,Helvetica,sans-serif!important}
.wrapper{width:min(1460px,94%)!important;margin:auto!important}
header{min-height:56px!important;gap:24px!important;background:#02070b!important;border-bottom:1px solid #10202c!important;backdrop-filter:none!important}
.logo{font-size:27px!important;letter-spacing:-1px!important}
nav{gap:25px!important}
nav button{font-size:11px!important;padding:20px 0!important;color:#e4e9ee!important}
[data-nav="shop"],[data-nav="inventory"],#shop,#inventory,#dailyChest{display:none!important}
.header-right{gap:9px!important}.coin-pill{padding:9px 14px!important;border-color:#294052!important;background:#03090e!important}.btn{border-radius:7px!important}
main{padding-top:10px!important}.panel{border-color:#1c3445!important;border-radius:12px!important;background:#040d14!important;box-shadow:none!important}.section{margin-top:12px!important;padding:16px!important}.section h2{font-size:19px!important}.section-subtitle{font-size:13px!important;color:#9fb0bd!important}
.dashboard{grid-template-columns:1.05fr 1fr!important;gap:12px!important}
.hero{min-height:455px!important;background:#03090d!important;position:relative!important;overflow:hidden!important}
.hero:after{content:""!important;position:absolute!important;inset:0!important;z-index:4!important;background:linear-gradient(90deg,#03090d 0%,rgba(3,9,13,.98) 30%,rgba(3,9,13,.74) 42%,rgba(3,9,13,.15) 65%,rgba(3,9,13,0) 100%),linear-gradient(180deg,rgba(3,9,13,0) 67%,#03090d 100%)!important;pointer-events:none!important}
.hero-copy{top:22px!important;left:22px!important}.hero-copy small{font-size:12px!important}.hero-copy h1{font-size:28px!important;margin:10px 0 5px!important}.hero-copy p{font-size:14px!important}.level-badge{background:#7631dc!important;padding:4px 8px!important}
.character-holder{position:absolute!important;left:37%!important;right:0!important;top:0!important;bottom:0!important;width:auto!important;height:auto!important;z-index:1!important;transform:none!important;animation:none!important;overflow:hidden!important}
.character-holder .character-scene-clean{position:absolute!important;inset:0!important;overflow:hidden!important}
.character-holder .scene-clean-image{position:absolute!important;inset:0!important;width:100%!important;height:100%!important;object-fit:cover!important;object-position:center 27%!important;transform:none!important;filter:none!important;opacity:1!important;animation:none!important}
.character-holder .character-scene-clean:before{content:""!important;position:absolute!important;inset:0!important;z-index:3!important;background:linear-gradient(90deg,rgba(3,9,13,.66) 0%,rgba(3,9,13,.18) 35%,rgba(3,9,13,0) 67%),linear-gradient(180deg,rgba(3,9,13,0) 65%,rgba(3,9,13,.86) 100%)!important;pointer-events:none!important}.character-holder .character-scene-clean:after{display:none!important;content:none!important}
.next-evolution{left:20px!important;bottom:78px!important;width:195px!important;padding:12px!important;background:rgba(4,11,17,.96)!important;border-color:#2a4355!important;border-radius:10px!important;backdrop-filter:none!important}.next-evolution small{font-size:11px!important}.next-evolution h3{font-size:14px!important;margin:7px 0 4px!important}.next-evolution b{font-size:15px!important}.next-evolution .muted{font-size:12px!important}
.shadow-character{height:130px!important;margin:9px 0!important;border-radius:7px!important;overflow:hidden!important;background:linear-gradient(#d7dadb,#969fa5)!important;box-shadow:inset 0 0 28px rgba(0,0,0,.26)!important}.shadow-character:before,.shadow-character:after{display:none!important;content:none!important}.shadow-character .next-silhouette{display:block!important;width:100%!important;height:100%!important;object-fit:cover!important;object-position:center 18%!important;filter:none!important;opacity:1!important;transform:none!important}
.hero-track{left:25px!important;right:25px!important;bottom:13px!important;display:grid!important;grid-template-columns:repeat(8,1fr)!important;align-items:end!important;background:none!important;padding:0!important}.track-node{font-size:9px!important;color:#7e909d!important}.track-circle{width:28px!important;height:28px!important;font-size:10px!important;background:#07111a!important}.track-node.unlocked{color:#d078ff!important}
.progress{padding:22px!important}.progress h3{font-size:13px!important;margin-bottom:20px!important}.progress-grid{gap:28px!important}.level-number{font-size:61px!important;color:#963fff!important}.progress-bar{height:9px!important;max-width:285px!important}.progress-stats{margin-top:25px!important}.pstat{padding-top:19px!important;font-size:13px!important}.pstat b{font-size:22px!important}
.two-cols{gap:12px!important}.challenge{padding:12px 4px!important;font-size:14px!important}.bonus{font-size:14px!important}.days{margin:16px 0!important;gap:11px!important}.day{width:35px!important;height:35px!important}.streak-big{font-size:30px!important}
/* Hide the full missions catalogue on the landing composition; challenge clicks still scroll to it when needed. */
#missions{margin-top:12px!important}
/* Evolution path exactly as the reference composition. */
.evolution-grid{display:grid!important;grid-template-columns:repeat(8,minmax(0,1fr))!important;gap:12px!important;overflow:visible!important}
.evolution-card{height:205px!important;position:relative!important;overflow:visible!important;border:1px solid #294052!important;border-radius:8px!important;background:#08131c!important}
.evolution-card.unlocked{border-color:#8b3bff!important;box-shadow:0 0 15px rgba(139,59,255,.45)!important}
.evolution-character{position:absolute!important;inset:5px 5px 48px!important;border-radius:6px!important;overflow:hidden!important;background:linear-gradient(#d9dcdd,#9aa3a8)!important}
.evolution-card.unlocked .evolution-character{background:#071019!important}
.evolution-card .evolution-real,.evolution-card .evolution-silhouette{display:block!important;width:100%!important;height:100%!important;max-width:none!important;object-fit:cover!important;object-position:center 18%!important;transform:none!important;filter:none!important;opacity:1!important;mix-blend-mode:normal!important}
.evolution-card.locked .evolution-character:before,.evolution-card.locked .evolution-character:after{display:none!important;content:none!important}
.evolution-card.locked:before{content:"🔒"!important;position:absolute!important;right:8px!important;top:8px!important;z-index:10!important;width:23px!important;height:23px!important;display:grid!important;place-items:center!important;border-radius:50%!important;background:rgba(255,255,255,.88)!important;color:#23303a!important;font-size:12px!important}
.evolution-card:not(:last-child):after{content:"›"!important;position:absolute!important;right:-11px!important;top:78px!important;z-index:20!important;color:#fff!important;font-size:28px!important;font-weight:900!important;text-shadow:0 2px 7px #000!important}
.evolution-name{left:7px!important;right:7px!important;bottom:6px!important;font-size:9px!important;line-height:1.08!important;text-shadow:0 2px 5px #000!important}.evolution-name span{font-size:9px!important}.evolution-name b{font-size:12px!important}.evolution-name small{font-size:9px!important;color:#fff!important}
/* Creator stays part of first-login flow and visually matches the site. */
#creatorModal .modal-box{width:min(620px,96%)!important;background:#061019!important;border-color:#294052!important}#creatorModal h2{margin-top:0!important}.creator-preview{height:330px!important;background:#03090d!important;border-color:#294052!important}.creator-preview img{width:100%!important;height:100%!important;object-fit:cover!important;object-position:center 22%!important;animation:none!important}.choice{background:#0b1721!important;border-color:#2a4050!important}.choice.selected{background:#24113d!important;border-color:#9a45ff!important;box-shadow:0 0 12px rgba(143,63,255,.35)!important}
@media(max-width:1050px){.dashboard,.two-cols{grid-template-columns:1fr!important}.evolution-grid{grid-template-columns:repeat(4,1fr)!important}.evolution-card{height:220px!important}.character-holder{left:34%!important}}
@media(max-width:680px){.wrapper{width:96%!important}.evolution-grid{grid-template-columns:repeat(2,1fr)!important}.evolution-card{height:220px!important}.next-evolution{width:175px!important}.hero{min-height:500px!important}.character-holder{left:25%!important}.header-right .coin-pill{display:none!important}}
'''
if marker not in s:
    s=s.replace('</style>',css+'\n</style>',1)

p.write_text(s,encoding='utf-8')
