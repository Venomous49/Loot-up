from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

# Stable root-level assets.
s=re.sub(r'function assetPath\(profile,stage\)\{.*?\n\}', '''function assetPath(profile,stage){\nreturn `${stages[stage].slug}.webp`;\n}''', s, count=1, flags=re.S)
s=re.sub(r'function creatorAssetPath\(\)\{.*?\n\}', '''function creatorAssetPath(){\nreturn "01-debutant.webp";\n}''', s, count=1, flags=re.S)

# Keep the main artwork static and sharp.
new_character=r'''function characterHTML(profile,stage){
const base=assetPath(profile,stage);
return `<div class="character-scene-clean"><img class="scene-clean-image" src="${base}" alt="Looter" onerror="this.style.display='none';this.nextElementSibling.style.display='block'"><div class="character-missing" style="display:none">Asset réaliste manquant.</div></div>`;
}'''
s=re.sub(r'function characterHTML\(profile,stage\)\{.*?\n\}\n\n/\* ==========================================================\nAPERÇU CRÉATEUR', new_character+'\n\n/* ==========================================================\nAPERÇU CRÉATEUR', s, count=1, flags=re.S)

marker='/* RISELOOTER_FINAL_SIMPLE_V15 */'
css=r'''
/* RISELOOTER_FINAL_SIMPLE_V15 */
/* Simplify site */
[data-nav="shop"],[data-nav="inventory"],#shop,#inventory,#dailyChest{display:none!important}

/* Main artwork: no animation, no blur, no horizontal masking edge */
.character-holder{position:absolute!important;top:0!important;right:0!important;bottom:0!important;left:31%!important;width:auto!important;height:auto!important;z-index:1!important;transform:none!important;display:block!important;overflow:hidden!important;animation:none!important}
.character-holder .character-scene-clean{position:absolute!important;inset:0!important;overflow:hidden!important;animation:none!important;transform:none!important}
.character-holder .scene-clean-image{position:absolute!important;inset:0!important;width:100%!important;height:100%!important;object-fit:cover!important;object-position:center 23%!important;filter:none!important;opacity:1!important;transform:none!important;animation:none!important}
/* Only a soft left gradient. It spans full height, so there is no line through the face. */
.character-holder .character-scene-clean:before{content:""!important;position:absolute!important;inset:0 auto 0 0!important;width:35%!important;height:100%!important;z-index:7!important;pointer-events:none!important;background:linear-gradient(90deg,#05090d 0%,rgba(5,9,13,.98) 38%,rgba(5,9,13,.58) 70%,rgba(5,9,13,0) 100%)!important}
.character-holder .character-scene-clean:after{display:none!important;content:none!important}

/* Next evolution silhouette */
.next-evolution{background:rgba(4,10,16,.96)!important}
.shadow-character{height:145px!important;margin:10px auto!important;overflow:hidden!important;border-radius:8px!important;position:relative!important;background:radial-gradient(circle at 50% 40%,#71808c 0%,#4a5862 42%,#26323a 100%)!important}
.shadow-character img{display:block!important;width:100%!important;height:100%!important;max-width:none!important;object-fit:cover!important;object-position:center 25%!important;filter:brightness(.08) grayscale(1) contrast(1.65)!important;opacity:1!important;transform:none!important}
.generic-shadow{display:none!important}

/* Evolution cards: make the real asset visible as a silhouette */
.evolution-card{background:radial-gradient(circle at 50% 38%,#65737d 0%,#3b4851 45%,#1c252c 100%)!important}
.evolution-character{position:absolute!important;inset:8px 5px 42px!important;display:block!important;overflow:hidden!important}
.evolution-character img,.evolution-card .scene-clean-image{display:block!important;width:100%!important;height:100%!important;max-width:none!important;object-fit:cover!important;object-position:center 24%!important;transform:none!important;opacity:1!important}
.evolution-card.locked .evolution-character img,.evolution-card.locked .scene-clean-image{filter:brightness(.07) grayscale(1) contrast(1.7)!important;opacity:1!important}
.evolution-card.unlocked .evolution-character img,.evolution-card.unlocked .scene-clean-image{filter:none!important}
.evolution-card .character-scene-clean{position:absolute!important;inset:0!important;overflow:hidden!important}
.evolution-card .character-scene-clean:before,.evolution-card .character-scene-clean:after{display:none!important;content:none!important}
.scene-background,.scene-body,.scene-torso,.scene-head,.character-scene-real{display:none!important;animation:none!important}
'''
if marker not in s:
    s=s.replace('</style>',css+'\n</style>',1)

p.write_text(s,encoding='utf-8')
