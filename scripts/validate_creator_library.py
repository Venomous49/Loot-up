from pathlib import Path
import hashlib
import cv2
import numpy as np

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

            # Five hairstyle buttons must not point to byte-identical assets.
            digests = [hashlib.sha256(p.read_bytes()).hexdigest() for _,p,_ in group]
            if len(digests) == 5 and len(set(digests)) != 5:
                errors.append(f'{gender}/{skin}/{hair}: duplicate hairstyle files')

            # Require visible differences between hairstyle renders.
            if len(group) == 5:
                ref = group[0][2]
                for style,p,im in group[1:]:
                    if im.shape != ref.shape:
                        errors.append(f'shape mismatch: {p}')
                        continue
                    delta = cv2.absdiff(ref, im).mean()
                    if delta < 0.30:
                        errors.append(f'{gender}/{skin}/{hair}/{style}: hairstyle too similar ({delta:.3f})')

# Skin and hair colour controls must also result in different complete images.
for gender, styles in EXPECTED.items():
    style = styles[0]
    skin_imgs=[]
    for skin in SKINS:
        p=ROOT/gender/skin/'brown'/f'{style}.webp'
        im=cv2.imread(str(p)) if p.exists() else None
        if im is not None: skin_imgs.append((skin,im))
    if len(skin_imgs)==5:
        for (a,ia),(b,ib) in zip(skin_imgs,skin_imgs[1:]):
            if ia.shape==ib.shape and cv2.absdiff(ia,ib).mean() < 0.18:
                errors.append(f'{gender}: adjacent skin tones {a}/{b} too similar')

    hair_imgs=[]
    for hair in HAIRS:
        p=ROOT/gender/'medium'/hair/f'{style}.webp'
        im=cv2.imread(str(p)) if p.exists() else None
        if im is not None: hair_imgs.append((hair,im))
    if len(hair_imgs)==5:
        for (a,ia),(b,ib) in zip(hair_imgs,hair_imgs[1:]):
            if ia.shape==ib.shape and cv2.absdiff(ia,ib).mean() < 0.12:
                errors.append(f'{gender}: adjacent hair colours {a}/{b} too similar')

html = Path('index.html').read_text(encoding='utf-8')
required = [
    'function creatorAssetPath(state=avatarDraft,style=state.hairStyle)',
    'assets/creator/${state.gender}/${state.skin}/${state.hairColor}/${style}.webp?v=${CREATOR_ASSET_VERSION}',
    'const thumb = creatorAssetPath(avatarDraft,value)',
    'if(field === "gender")',
]
for token in required:
    if token not in html:
        errors.append(f'index routing token missing: {token}')

# Production creator must use pre-rendered full images only.
for forbidden in ['creator-skin-overlay','creator-hair-overlay','mix-blend-mode:multiply','filter:hue-rotate']:
    if forbidden in html and 'display:none!important' not in html:
        errors.append(f'legacy overlay/filter may still be active: {forbidden}')

if html.count('function creatorFallbackPath(gender=avatarDraft.gender){') != 1:
    errors.append('creatorFallbackPath must exist exactly once')

if errors:
    print('CREATOR VALIDATION FAILED')
    for e in errors:
        print(' -', e)
    raise SystemExit(1)

print('Creator library validated: 250 complete pre-rendered assets, routing and fallbacks structurally consistent.')
