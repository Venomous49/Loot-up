from pathlib import Path
import hashlib
import re
import cv2

ROOT = Path('assets/creator')
MASTER_ROOT = Path('assets/creator_sources')
FACE_MODEL = MASTER_ROOT / 'face_detection_yunet_2023mar.onnx'
EXPECTED = {
    'male': ['male_textured','male_short','male_medium','male_undercut','male_slick'],
    'female': ['female_long','female_wavy','female_bob','female_ponytail','female_short'],
}
SKINS = ['light','warm','medium','deep','dark']
HAIRS = ['black','brown','blond','red','purple']
EXPECTED_SIZE = (910, 1728)
EXPECTED_EYE_MIDPOINTS = {
    'male': (983.0, 242.0),
    'female': (899.0, 250.0),
}
EYE_POSITION_TOLERANCE = 15.0
FACE_HEIGHT_RANGES = {
    'male': (210.0, 265.0),
    'female': (275.0, 330.0),
}

errors = []

if not FACE_MODEL.exists():
    errors.append(f'missing creator face detector: {FACE_MODEL}')
    face_detector = None
else:
    face_detector = cv2.FaceDetectorYN.create(
        str(FACE_MODEL), '', (EXPECTED_SIZE[1], EXPECTED_SIZE[0]), .64, .3, 5000
    )

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
                if im.shape[:2] != EXPECTED_SIZE:
                    errors.append(f'unexpected creator framing: {p} is {im.shape[1]}x{im.shape[0]}, expected 1728x910')
                    continue
                if im.std() < 10:
                    errors.append(f'near blank: {p}')

                if face_detector is not None:
                    _, faces = face_detector.detect(im)
                    if faces is None or len(faces) == 0:
                        errors.append(f'creator face not detected: {p}')
                    else:
                        face = max(faces, key=lambda row: row[-1])
                        _, _, _, h = (float(v) for v in face[:4])
                        eye_x = (float(face[4]) + float(face[6])) / 2
                        eye_y = (float(face[5]) + float(face[7])) / 2
                        expected_eye_x, expected_eye_y = EXPECTED_EYE_MIDPOINTS[gender]
                        if (
                            abs(eye_x - expected_eye_x) > EYE_POSITION_TOLERANCE
                            or abs(eye_y - expected_eye_y) > EYE_POSITION_TOLERANCE
                        ):
                            errors.append(
                                f'creator eye position drift: {p} detected at ({eye_x:.1f},{eye_y:.1f}), '
                                f'expected near ({expected_eye_x:.1f},{expected_eye_y:.1f})'
                            )
                        min_h, max_h = FACE_HEIGHT_RANGES[gender]
                        if not min_h <= h <= max_h:
                            errors.append(
                                f'creator face scale drift: {p} detected at {h:.1f}px high, '
                                f'expected {min_h:.1f}-{max_h:.1f}px'
                            )

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

print('Creator library validated: 250 complete pre-rendered assets at canonical 1728x910 framing with locked face placement, live controls, thumbnails and source-owned fallbacks are structurally consistent with no active legacy overlays or edge rewrites.')
