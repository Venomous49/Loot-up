from pathlib import Path
import hashlib

import cv2
import numpy as np

ROOT = Path('assets/creator')
EXPECTED = {
    'male': ['male_textured','male_short','male_medium','male_undercut','male_slick'],
    'female': ['female_long','female_wavy','female_bob','female_ponytail','female_short'],
}
SKINS = ['light','warm','medium','deep','dark']
HAIRS = ['black','brown','blond','red','purple']
EXPECTED_HW = (910, 1728)

errors = []


def load(path):
    im = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if im is None or im.size == 0:
        errors.append(f'undecodable: {path}')
        return None
    if im.shape[:2] != EXPECTED_HW:
        errors.append(f'unexpected format: {path} is {im.shape[1]}x{im.shape[0]}, expected 1728x910')
        return None
    if im.std() < 10:
        errors.append(f'near blank: {path}')
        return None
    return im


for gender, styles in EXPECTED.items():
    files = list((ROOT / gender).rglob('*.webp'))
    if len(files) != 125:
        errors.append(f'{gender}: expected 125 assets, got {len(files)}')

    for skin in SKINS:
        for hair in HAIRS:
            digests = []
            for style in styles:
                p = ROOT / gender / skin / hair / f'{style}.webp'
                if not p.exists() or p.stat().st_size < 1000:
                    errors.append(f'missing/empty: {p}')
                    continue
                im = load(p)
                if im is not None:
                    digests.append(hashlib.sha256(p.read_bytes()).hexdigest())
            if len(digests) == 5 and len(set(digests)) != 5:
                errors.append(f'{gender}/{skin}/{hair}: duplicate hairstyle files')


MALE_X0, MALE_X1 = 790, 1215
MALE_Y0, MALE_Y1 = 70, 340
static_mask = np.ones(EXPECTED_HW, dtype=bool)
static_mask[MALE_Y0:MALE_Y1, MALE_X0:MALE_X1] = False

# Skin colour is a legitimate customization and can change face/neck/arms.
# Therefore body invariants must be compared within the same skin tone, not
# against one global medium-skin image. Hairstyle and hair-colour changes are
# still forbidden from altering the scene outside the head customization box.
for skin in SKINS:
    ref_path = ROOT / 'male' / skin / 'brown' / 'male_undercut.webp'
    ref = load(ref_path)
    if ref is None:
        errors.append(f'male same-skin immutable reference missing: {ref_path}')
        continue
    ref_static = ref[static_mask].astype(np.int16)

    for hair in HAIRS:
        for style in EXPECTED['male']:
            p = ROOT / 'male' / skin / hair / f'{style}.webp'
            im = load(p)
            if im is None:
                continue
            cur = im[static_mask].astype(np.int16)
            diff = np.abs(cur - ref_static)
            mean_diff = float(diff.mean())
            p99 = float(np.percentile(diff, 99))
            if mean_diff > 1.60 or p99 > 9.0:
                errors.append(
                    f'male immutable base changed outside head: {p} '
                    f'mean_diff={mean_diff:.3f} p99={p99:.1f}'
                )


BODY_Y = 345
for skin in SKINS:
    ref_path = ROOT / 'male' / skin / 'brown' / 'male_undercut.webp'
    ref = load(ref_path)
    if ref is None:
        continue
    ref_body = ref[BODY_Y:].astype(np.int16)
    for hair in HAIRS:
        for style in EXPECTED['male']:
            p = ROOT / 'male' / skin / hair / f'{style}.webp'
            im = load(p)
            if im is None:
                continue
            diff = np.abs(im[BODY_Y:].astype(np.int16) - ref_body)
            mean_diff = float(diff.mean())
            p99 = float(np.percentile(diff, 99))
            if mean_diff > .70 or p99 > 4.0:
                errors.append(
                    f'male body/clothes changed below head: {p} '
                    f'mean_diff={mean_diff:.3f} p99={p99:.1f}'
                )

if errors:
    print('CREATOR HD VALIDATION FAILED')
    for error in errors:
        print(' -', error)
    raise SystemExit(1)

print('Creator HD library validated: 250 assets; hairstyle/hair-colour changes keep the male body locked while selected skin-tone changes remain allowed.')
