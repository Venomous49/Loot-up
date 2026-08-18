from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

css=r'''
/* RISELOOTER_CREATOR_FINAL_V19 */
#creatorModal{padding:0!important;background:#02070b!important;overflow:auto!important;align-items:start!important}
#creatorModal.show{display:block!important}
#creatorModal .modal-box{width:min(1480px,96%)!important;max-height:none!important;margin:18px auto 30px!important;padding:0!important;border:0!important;background:transparent!important;overflow:visible!important}
.creator-shell{display:grid;grid-template-columns:.96fr 1.04fr;gap:16px}
.creator-panel{border:1px solid #1e3445;border-radius:12px;background:#061019;padding:22px}
.creator-heading{font-size:28px;font-weight:1000;margin:0 0 6px}.creator-heading em{color:#913fff}.creator-lead{color:#b0bcc6;margin:0 0 20px}
.creator-step{padding:17px 0;border-top:1px solid #142735}.creator-step:first-of-type{border-top:0}.creator-step-title{font-size:15px;font-weight:900;margin-bottom:13px}.creator-step-title b{color:#9d4cff;margin-right:7px}
#creatorModal .choices{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin:0}
#creatorModal #genderChoices{grid-template-columns:1fr 1fr}
#creatorModal .choice{min-height:62px;border:1px solid #2a4050;border-radius:8px;background:#071019;color:#fff;font-weight:800;padding:10px;transition:.15s}
#creatorModal .choice:hover{border-color:#7240a8}#creatorModal .choice.selected{border-color:#a23fff;background:#120a1d;box-shadow:0 0 0 1px #a23fff,0 0 18px rgba(143,63,255,.22)}
#skinChoices .choice,#hairColorChoices .choice{height:72px;min-height:72px;font-size:0;position:relative;overflow:hidden}
#skinChoices .choice:after,#hairColorChoices .choice:after{content:'✓';display:none;position:absolute;right:6px;top:5px;width:22px;height:22px;border-radius:50%;place-items:center;background:#7c2cff;color:#fff;font-size:13px}#skinChoices .choice.selected:after,#hairColorChoices .choice.selected:after{display:grid}
#skinChoices [data-value="light"]{background:#e6b88f}#skinChoices [data-value="warm"]{background:#bd7f50}#skinChoices [data-value="medium"]{background:#96613c}#skinChoices [data-value="deep"]{background:#694125}#skinChoices [data-value="dark"]{background:#3b2114}
#hairColorChoices [data-value="black"]{background:#0b0a0b}#hairColorChoices [data-value="brown"]{background:#2b1b12}#hairColorChoices [data-value="blond"]{background:#c79550}#hairColorChoices [data-value="red"]{background:#8c3519}#hairColorChoices [data-value="purple"]{background:#4d256d}
#hairStyleChoices{grid-template-columns:repeat(5,minmax(0,1fr))!important}.hair-choice{min-height:88px!important;font-size:12px!important;display:grid;place-items:end center;background:linear-gradient(180deg,#15212c,#080d13)!important;text-align:center}
.creator-save{width:100%;margin-top:18px;padding:16px!important;font-size:17px!important;background:linear-gradient(90deg,#5411c9,#842bea)!important}.creator-note{text-align:center;color:#9aa8b5;font-size:12px;margin-top:10px}
.creator-live{padding:18px;border:1px solid #1e3445;border-radius:12px;background:#061019}.creator-live-title{font-weight:900;margin-bottom:12px}.creator-live-title span{color:#48dd82;font-size:12px;margin-left:10px}
#creatorModal .creator-preview{height:610px;margin:0;border:1px solid #294052;border-radius:9px;background:#03090d;position:relative;overflow:hidden}
#creatorModal .creator-preview img{width:100%!important;height:100%!important;max-width:none!important;object-fit:cover!important;object-position:center 20%!important;animation:none!important;filter:none!important}
.creator-live-badge{position:absolute;right:16px;top:16px;z-index:5;text-align:right}.creator-live-badge b{display:inline-block;padding:6px 10px;border-radius:7px;background:#7225d6}.creator-live-badge strong{display:block;margin-top:7px;font-size:18px}
.creator-path{margin-top:12px;padding:14px;border:1px solid #1b3040;border-radius:9px}.creator-path-title{font-size:12px;font-weight:900;margin-bottom:13px}.creator-path-row{display:grid;grid-template-columns:repeat(8,1fr);gap:6px;text-align:center}.creator-path-node{font-size:9px;color:#93a0ab}.creator-path-node i{width:34px;height:34px;margin:0 auto 5px;display:grid;place-items:center;border:1px solid #405263;border-radius:50%;font-style:normal}.creator-path-node:first-child{color:#c36cff}.creator-path-node:first-child i{background:#7225d6;border-color:#9b43ff}
.creator-benefits{grid-column:1/-1;display:grid;grid-template-columns:repeat(4,1fr);gap:0;border:1px solid #1e3445;border-radius:12px;background:#061019;padding:20px}.creator-benefit{padding:0 24px;border-right:1px solid #18303f}.creator-benefit:last-child{border:0}.creator-benefit b{display:block;margin-bottom:6px}.creator-benefit span{font-size:12px;color:#a9b5bf}
@media(max-width:900px){.creator-shell{grid-template-columns:1fr}.creator-benefits{grid-template-columns:1fr 1fr;gap:18px}.creator-benefit{border:0;padding:0}#creatorModal .creator-preview{height:500px}}
@media(max-width:560px){#creatorModal .choices,#hairStyleChoices{grid-template-columns:repeat(3,1fr)!important}.creator-benefits{grid-template-columns:1fr}.creator-path-row{grid-template-columns:repeat(4,1fr)}}
'''
if 'RISELOOTER_CREATOR_FINAL_V19' not in s:
    s=s.replace('</style>',css+'\n</style>',1)

modal=r'''<div class="modal" id="creatorModal">
<div class="modal-box">
  <div class="creator-shell">
    <section class="creator-panel">
      <h2 class="creator-heading">CRÉATION DE TON <em>LOOTER</em></h2>
      <p class="creator-lead">Personnalise ton personnage. Tu pourras le voir évoluer à chaque nouveau niveau !</p>
      <div class="creator-step"><div class="creator-step-title"><b>1.</b> CHOISIS TON SEXE</div><div class="choices" id="genderChoices"><button class="choice selected" data-value="male">♂ &nbsp; HOMME</button><button class="choice" data-value="female">♀ &nbsp; FEMME</button></div></div>
      <div class="creator-step"><div class="creator-step-title"><b>2.</b> CHOISIS TA COULEUR DE PEAU</div><div class="choices" id="skinChoices"><button class="choice" data-value="light">Clair</button><button class="choice" data-value="warm">Doré</button><button class="choice selected" data-value="medium">Mat</button><button class="choice" data-value="deep">Foncé</button><button class="choice" data-value="dark">Très foncé</button></div></div>
      <div class="creator-step"><div class="creator-step-title"><b>3.</b> CHOISIS TA COULEUR DE CHEVEUX</div><div class="choices" id="hairColorChoices"><button class="choice" data-value="black">Noir</button><button class="choice selected" data-value="brown">Brun</button><button class="choice" data-value="blond">Blond</button><button class="choice" data-value="red">Roux</button><button class="choice" data-value="purple">Violet</button></div></div>
      <div class="creator-step"><div class="creator-step-title"><b>4.</b> CHOISIS TA COUPE DE CHEVEUX</div><div class="choices" id="hairStyleChoices"></div></div>
      <button class="btn creator-save" id="saveAvatar">CRÉER MON LOOTER &nbsp; →</button>
      <div class="creator-note">🔒 Tu pourras modifier ton apparence plus tard dans ton profil.</div>
    </section>
    <section class="creator-live">
      <div class="creator-live-title">APERÇU EN TEMPS RÉEL <span>● En direct</span></div>
      <div class="creator-preview" id="creatorPreview"><div class="creator-empty">Chargement du personnage...</div><div class="creator-live-badge"><b>NIVEAU 1</b><strong>DÉBUTANT</strong></div></div>
      <div class="creator-path"><div class="creator-path-title">TON PARCOURS D'ÉVOLUTION</div><div class="creator-path-row">
        <div class="creator-path-node"><i>1</i>DÉBUTANT</div><div class="creator-path-node"><i>5</i>DÉBROUILLARD</div><div class="creator-path-node"><i>10</i>CHASSEUR</div><div class="creator-path-node"><i>15</i>HUSTLER</div><div class="creator-path-node"><i>20</i>PRO</div><div class="creator-path-node"><i>30</i>ÉLITE</div><div class="creator-path-node"><i>40</i>CYBER LOOTER</div><div class="creator-path-node"><i>50</i>RISE LOOTER</div>
      </div></div>
    </section>
    <section class="creator-benefits"><div class="creator-benefit"><b>📈 Gagne de l'XP</b><span>Complète des missions et gagne de l'expérience.</span></div><div class="creator-benefit"><b>🔥 Monte de niveau</b><span>Débloque de nouveaux skins et récompenses exclusives.</span></div><div class="creator-benefit"><b>🏆 Grimpe au classement</b><span>Deviens le meilleur et gagne des récompenses.</span></div><div class="creator-benefit"><b>🎁 Gagne des récompenses</b><span>Échange tes gains contre de l'argent ou des cadeaux.</span></div></section>
  </div>
</div>
</div>'''
s=re.sub(r'<div class="modal" id="creatorModal">.*?</div>\s*</div>\s*<div class="modal" id="withdrawModal">',modal+'\n\n<div class="modal" id="withdrawModal">',s,count=1,flags=re.S)

# Broaden hairstyles: neutral/universal styles, same count for both sexes.
s=re.sub(r'const maleHair = \[.*?\n\];', '''const maleHair = [\n["male_textured","Texturé"],\n["male_short","Court classique"],\n["male_medium","Mi-long"],\n["male_undercut","Dégradé"],\n["male_slick","Coiffé arrière"]\n];''', s, count=1, flags=re.S)
s=re.sub(r'const femaleHair = \[.*?\n\];', '''const femaleHair = [\n["female_long","Long lisse"],\n["female_wavy","Ondulé"],\n["female_bob","Carré"],\n["female_ponytail","Queue attachée"],\n["female_short","Court moderne"]\n];''', s, count=1, flags=re.S)

# Give hairstyle choices the visual-card class while keeping the existing real-time logic.
s=s.replace('class="\nchoice\n${avatarDraft.hairStyle === value ? "selected" : ""}\n"','class="\nchoice hair-choice\n${avatarDraft.hairStyle === value ? "selected" : ""}\n"')

# Preserve the level badge over every preview refresh.
s=s.replace('<div class="creator-empty" style="display:none">Aperçu indisponible pour cette combinaison.</div>`;','<div class="creator-empty" style="display:none">Aperçu indisponible pour cette combinaison.</div><div class="creator-live-badge"><b>NIVEAU 1</b><strong>DÉBUTANT</strong></div>`;')

p.write_text(s,encoding='utf-8')
print('creator interface patched')
