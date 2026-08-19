from pathlib import Path
import hashlib
import re
import cv2

ROOT = Path('assets/creator')
MASTER_ROOT = Path('assets/creator_sources')
EXPECTED = {
    'male': ['male_textured','male_short','male_medium','male_undercut','male_slick'],
    'female': ['female_long','female_wavy','female_bob','female_ponytail','female_short'],
}
SKINS = ['light','warm','medium','deep','dark']
HAIRS = ['black','brown','blond','red','purple']

errors = []

for gender, styles in EXPECTED.items():
    for style in styles:
        candidates = list(MASTER_ROOT.glob(f'{style}.*'))
        if not candidates:
            errors.append(f'missing hairstyle master: {gender}/{style}')

for gender, styles in EXPECTED.items():
    files = list((ROOT/gender).rglob('*.webp'))
    if len(files) != 125:
        errors.append(f'{gender}: expected 125 assets, got {len(files)}')

    for skin in SKINS:
        for hair in HAIRS:
            group = []
            for style in styles:
                p = ROOT/gender/skin/hair/f'{style}.webp'
                if not p.exists() or p.stat().st_size < 1000:
                    errors.append(f'missing/empty: {p}')
                    continue
                im = cv2.imread(str(p), cv2.IMREAD_COLOR)
                if im is None or im.size == 0:
                    errors.append(f'undecodable: {p}')
                    continue
                if im.std() < 10:
                    errors.append(f'near blank: {p}')
                group.append((style, p, im))

            digests = [hashlib.sha256(p.read_bytes()).hexdigest() for _,p,_ in group]
            if len(digests) == 5 and len(set(digests)) != 5:
                errors.append(f'{gender}/{skin}/{hair}: duplicate hairstyle files')

            if len(group) == 5:
                ref = group[0][2]
                for style,p,im in group[1:]:
                    if im.shape != ref.shape:
                        errors.append(f'shape mismatch: {p}')
                        continue
                    delta = cv2.absdiff(ref, im).mean()
                    if delta < 0.30:
                        errors.append(f'{gender}/{skin}/{hair}/{style}: hairstyle too similar ({delta:.3f})')

for gender, styles in EXPECTED.items():
    style = styles[0]
    skin_imgs=[]
    for skin in SKINS:
        p=ROOT/gender/skin/'brown'/f'{style}.webp'
        im=cv2.imread(str(p)) if p.exists() else None
        if im is not None:
            skin_imgs.append((skin,im))
    if len(skin_imgs)==5:
        for (a,ia),(b,ib) in zip(skin_imgs,skin_imgs[1:]):
            if ia.shape==ib.shape and cv2.absdiff(ia,ib).mean() < 0.18:
                errors.append(f'{gender}: adjacent skin tones {a}/{b} too similar')

    for style in styles:
        hair_imgs=[]
        for hair in HAIRS:
            p=ROOT/gender/'medium'/hair/f'{style}.webp'
            im=cv2.imread(str(p)) if p.exists() else None
            if im is not None:
                hair_imgs.append((hair,im))
        if len(hair_imgs)==5:
            for (a,ia),(b,ib) in zip(hair_imgs,hair_imgs[1:]):
                if ia.shape==ib.shape and cv2.absdiff(ia,ib).mean() < 0.10:
                    errors.append(f'{gender}/{style}: adjacent hair colours {a}/{b} too similar')

html = Path('index.html').read_text(encoding='utf-8')
worker = Path('worker.js').read_text(encoding='utf-8') if Path('worker.js').exists() else ''

required = [
    'function creatorAssetPath(state=avatarDraft,style=state.hairStyle)',
    'assets/creator/${state.gender}/${state.skin}/${state.hairColor}/${style}.webp?v=${CREATOR_ASSET_VERSION}',
    'const thumb = creatorAssetPath(avatarDraft,value)',
    'setupChoiceGroup(\n"genderChoices",\n"gender"',
    'setupChoiceGroup(\n"skinChoices",\n"skin"',
    'setupChoiceGroup(\n"hairColorChoices",\n"hairColor"',
    'renderHairChoices();\n\nupdateCreatorPreview();',
]
for token in required:
    if token not in html:
        errors.append(f'index routing/UI token missing: {token}')

for value in SKINS:
    if f'data-value="{value}"' not in html:
        errors.append(f'missing skin button: {value}')
for value in HAIRS:
    if f'data-value="{value}"' not in html:
        errors.append(f'missing hair-colour button: {value}')
for styles in EXPECTED.values():
    for value in styles:
        if f'["{value}",' not in html:
            errors.append(f'missing hairstyle option: {value}')

for forbidden in [
    '<div class="creator-skin-overlay',
    '<div class="creator-hair-overlay',
    'mix-blend-mode:multiply',
    'hue-rotate(',
    'background-blend-mode:',
]:
    if forbidden in html:
        errors.append(f'legacy creator overlay/filter still active: {forbidden}')

hardened_fallback = 'function creatorFallbackPath(gender=avatarDraft.gender,skin=avatarDraft.skin,hairColor=avatarDraft.hairColor){'
hardened_return = 'return creatorAssetPath({gender,skin,hairColor,hairStyle:style});'
hardened_character = '? creatorFallbackPath(gender, profile?.avatar_skin || "medium", profile?.avatar_hair_color || "brown")'
hardened_onload = "document.getElementById('saveAvatar').disabled=this.dataset.triedFallback==='1'"
legacy_fallback = 'function creatorFallbackPath(gender=avatarDraft.gender){'
legacy_onload = "document.getElementById('saveAvatar').disabled=false"

for token in [hardened_fallback, hardened_return, hardened_character, hardened_onload]:
    if token not in html:
        errors.append(f'source creator fallback hardening missing: {token}')
if legacy_fallback in html:
    errors.append('legacy medium/brown creator fallback remains in source')
if legacy_onload in html:
    errors.append('legacy creator preview save-on-fallback behavior remains in source')

# Production must serve the reviewed source, not maintain a second hidden patch
# implementation at the Cloudflare edge.
for forbidden in ['hardenCreatorHtml', 'CREATOR_FALLBACK_NEW', 'CHARACTER_FALLBACK_NEW', 'PREVIEW_ONLOAD_NEW']:
    if forbidden in worker:
        errors.append(f'obsolete creator edge rewrite remains active: {forbidden}')
if 'env.ASSETS.fetch(request)' not in worker:
    errors.append('Cloudflare Worker no longer serves the static asset binding')
if "x-riselooter-creator-source', 'validated'" not in worker:
    errors.append('Cloudflare Worker deployment marker missing')

for stale in ['cleanbase28', 'presets31', 'hairstyles2', 'hairstyles3']:
    if stale in html:
        errors.append(f'stale creator asset version/path still present: {stale}')

preview_match = re.search(r'function updateCreatorPreview\(\)\{.*?\n\}', html, re.S)
if not preview_match:
    errors.append('updateCreatorPreview function missing')
else:
    preview = preview_match.group(0)
    if 'creatorAssetPath()' not in preview or 'creatorFallbackPath()' not in preview:
        errors.append('creator preview does not use canonical asset/fallback helpers')

if errors:
    print('CREATOR VALIDATION FAILED')
    for e in errors:
        print(' -', e)
    raise SystemExit(1)

print('Creator library validated: 250 complete pre-rendered assets, live controls, thumbnails and source-owned fallbacks are structurally consistent with no active legacy overlays or edge rewrites.')
