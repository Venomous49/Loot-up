from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')
marker='RISELOOTER_CREATOR_TEST_V20'
if marker in s:
    print('creator test already enabled')
    raise SystemExit(0)

css='''\n/* RISELOOTER_CREATOR_TEST_V20 */\n#creatorTestButton{background:#0b1721!important;border:1px solid #7f36e8!important;color:#d7a9ff!important}\n#creatorTestButton:hover{background:#24113d!important}\n.creator-test-banner{position:fixed;left:50%;top:8px;transform:translateX(-50%);z-index:1000;padding:7px 12px;border:1px solid #7f36e8;border-radius:8px;background:#160a27;color:#d7a9ff;font-size:12px;font-weight:800;display:none}\nbody.creator-test-active .creator-test-banner{display:block}\nbody.creator-test-active #creatorModal .creator-note:after{content:' • MODE TEST : rien ne sera enregistré';color:#d7a9ff}\n'''
s=s.replace('</style>',css+'\n</style>',1)

# Add a visible test button in the header, just before the auth button.
needle='<button class="btn dark" id="authButton">\nConnexion\n</button>'
replacement='''<button class="btn dark" id="creatorTestButton">\nTester la création\n</button>\n\n'''+needle
if needle in s:
    s=s.replace(needle,replacement,1)

# Add a small test-mode banner immediately after body.
s=s.replace('<body>','<body>\n<div class="creator-test-banner">MODE TEST — aperçu uniquement</div>',1)

js='''\n\n/* ==========================================================\nMODE TEST CRÉATEUR\n========================================================== */\nlet creatorTestMode = false;\n\nfunction openCreatorTest(){\n  creatorTestMode = true;\n  document.body.classList.add('creator-test-active');\n  avatarDraft = {gender:'male',skin:'medium',hairColor:'brown',hairStyle:'male_textured'};\n  document.querySelectorAll('#genderChoices .choice,#skinChoices .choice,#hairColorChoices .choice').forEach(b=>b.classList.remove('selected'));\n  document.querySelector('#genderChoices [data-value="male"]')?.classList.add('selected');\n  document.querySelector('#skinChoices [data-value="medium"]')?.classList.add('selected');\n  document.querySelector('#hairColorChoices [data-value="brown"]')?.classList.add('selected');\n  renderHairChoices();\n  updateCreatorPreview();\n  $('creatorModal').classList.add('show');\n}\n\nfunction closeCreatorTest(){\n  creatorTestMode = false;\n  document.body.classList.remove('creator-test-active');\n  $('creatorModal').classList.remove('show');\n}\n\nconst creatorTestButton = $('creatorTestButton');\nif(creatorTestButton){ creatorTestButton.onclick = openCreatorTest; }\n\nconst originalSaveAvatar = saveAvatar;\n$('saveAvatar').onclick = async () => {\n  if(creatorTestMode){\n    alert(`TEST OK\\nSexe : ${avatarDraft.gender}\\nTeint : ${avatarDraft.skin}\\nCheveux : ${avatarDraft.hairColor}\\nCoiffure : ${avatarDraft.hairStyle}\\n\\nRien n'a été enregistré.`);\n    return;\n  }\n  await originalSaveAvatar();\n};\n\nif(new URLSearchParams(location.search).get('creatorTest') === '1'){\n  setTimeout(openCreatorTest,150);\n}\n'''
# Insert after initialization handlers exist, before closing script.
s=s.replace('\n</script>\n\n</body>',js+'\n</script>\n\n</body>',1)

p.write_text(s,encoding='utf-8')
print('creator test mode patched')
