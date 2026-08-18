from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

# Stable root-level character assets.
s=re.sub(r'function assetPath\(profile,stage\)\{.*?\n\}', '''function assetPath(profile,stage){\nreturn `${stages[stage].slug}.webp`;\n}''', s, count=1, flags=re.S)
s=re.sub(r'function creatorAssetPath\(\)\{.*?\n\}', '''function creatorAssetPath(){\nreturn "01-debutant.webp";\n}''', s, count=1, flags=re.S)

# Silhouette assets are also published at repository root for Cloudflare reliability.
if 'function silhouettePath(stage)' in s:
    s=re.sub(r'function silhouettePath\(stage\)\{.*?\n\}', '''function silhouettePath(stage){\nreturn `sil-${stages[stage].slug}.png`;\n}''', s, count=1, flags=re.S)
else:
    s=s.replace('function creatorAssetPath(){\nreturn "01-debutant.webp";\n}', 'function creatorAssetPath(){\nreturn "01-debutant.webp";\n}\n\nfunction silhouettePath(stage){\nreturn `sil-${stages[stage].slug}.png`;\n}')

# Main character stays static and sharp.
new_character=r'''function characterHTML(profile,stage){
const base=assetPath(profile,stage);
return `<div class="character-scene-clean"><img class="scene-clean-image" src="${base}" alt="Looter" onerror="this.style.display='none';this.nextElementSibling.style.display='block'"><div class="character-missing" style="display:none">Asset réaliste manquant.</div></div>`;
}'''
s=re.sub(r'function characterHTML\(profile,stage\)\{.*?\n\}\n\n/\* ==========================================================\nAPERÇU CRÉATEUR', new_character+'\n\n/* ==========================================================\nAPERÇU CRÉATEUR', s, count=1, flags=re.S)

# Locked evolution cards use the generated silhouette PNGs; unlocked cards use the real artwork.
new_grid=r'''function renderEvolutionGrid(profile){

const level = profile.level || 1;

$("evolutionGrid").innerHTML = stages.map((stage,i) => {
  const unlocked = level >= stage.level;
  const visual = unlocked
    ? `<img class="evolution-real" src="${assetPath(profile,i)}" alt="${stage.name}" onerror="this.style.display='none'">`
    : `<img class="evolution-silhouette" src="${silhouettePath(i)}" alt="" onerror="this.style.display='none'">`;

  return `
  <div class="evolution-card ${unlocked ? "unlocked" : "locked"}">
    <div class="evolution-character">${visual}</div>
    <div class="evolution-name">
      NIVEAU ${stage.level}<br>
      <b>${stage.name}</b><br>
      ${unlocked ? escapeHTML(stage.desc) : "Évolution à découvrir"}
    </div>
  </div>`;
}).join("");

}'''
s=re.sub(r'function renderEvolutionGrid\(profile\)\{.*?\n\}\n\n/\* ==========================================================\nPROFIL', new_grid+'\n\n/* ==========================================================\nPROFIL', s, count=1, flags=re.S)

# Next evolution card also uses the generated silhouette PNG.
s=re.sub(
    r'\$\("nextEvolutionShadow"\)\.innerHTML = `.*?`;\n\n}\nelse\{',
    '''$("nextEvolutionShadow").innerHTML = `\n<img class="next-silhouette" src="${silhouettePath(idx + 1)}" alt="" onerror="this.style.display='none'">\n`;\n\n}\nelse{''',
    s,
    count=1,
    flags=re.S
)

marker='/* RISELOOTER_REAL_SILHOUETTES_V16 */'
css=r'''
/* RISELOOTER_REAL_SILHOUETTES_V16 */
[data-nav="shop"],[data-nav="inventory"],#shop,#inventory,#dailyChest{display:none!important}

/* Main artwork remains static and crisp. */
.character-holder{animation:none!important;transform:none!important;overflow:hidden!important}
.character-holder .character-scene-clean{position:absolute!important;inset:0!important;overflow:hidden!important}
.character-holder .scene-clean-image{position:absolute!important;inset:0!important;width:100%!important;height:100%!important;object-fit:cover!important;object-position:center 23%!important;filter:none!important;opacity:1!important;transform:none!important;animation:none!important}
.character-holder .character-scene-clean:before{content:""!important;position:absolute!important;inset:0 auto 0 0!important;width:35%!important;height:100%!important;z-index:7!important;pointer-events:none!important;background:linear-gradient(90deg,#05090d 0%,rgba(5,9,13,.98) 38%,rgba(5,9,13,.58) 70%,rgba(5,9,13,0) 100%)!important}
.character-holder .character-scene-clean:after{display:none!important;content:none!important}

/* Next evolution preview: actual generated silhouette on a light smoky card. */
.shadow-character{height:145px!important;margin:10px auto!important;overflow:hidden!important;border-radius:8px!important;position:relative!important;background:#b8bec3!important;box-shadow:inset 0 0 24px rgba(0,0,0,.28)!important}
.shadow-character .next-silhouette{display:block!important;width:100%!important;height:100%!important;object-fit:cover!important;object-position:center 20%!important;filter:none!important;opacity:1!important;transform:none!important}
.generic-shadow{display:none!important}

/* Evolution path: locked cards use dedicated light-background silhouette images. */
.evolution-card{background:#111a22!important}
.evolution-character{position:absolute!important;inset:8px 5px 42px!important;display:block!important;overflow:hidden!important;border-radius:7px!important}
.evolution-card.locked .evolution-character{background:#b8bec3!important}
.evolution-card .evolution-silhouette,.evolution-card .evolution-real{display:block!important;width:100%!important;height:100%!important;object-fit:cover!important;object-position:center 20%!important;filter:none!important;opacity:1!important;transform:none!important}
.evolution-card.unlocked .evolution-character{background:#0b1117!important}
.evolution-card.locked .evolution-name{color:#fff!important}
.scene-background,.scene-body,.scene-torso,.scene-head,.character-scene-real{display:none!important;animation:none!important}
'''
if marker not in s:
    s=s.replace('</style>',css+'\n</style>',1)

p.write_text(s,encoding='utf-8')
