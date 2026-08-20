from pathlib import Path
import hashlib

import cv2
import numpy as np
from PIL import Image, ImageOps

ROOT = Path('assets/creator')
MASTER_ROOT = Path('assets/creator_sources')
BACKGROUND = MASTER_ROOT / 'creator_background_master.png'
FACE_MODEL = MASTER_ROOT / 'face_detection_yunet_2023mar.onnx'
EXPECTED = {
    'male': ['male_textured','male_short','male_medium','male_undercut','male_slick'],
    'female': ['female_long','female_wavy','female_bob','female_ponytail','female_short'],
}
SKINS = ['light','warm','medium','deep','dark']
HAIRS = ['black','brown','blond','red','purple']
EXPECTED_WH = (1728, 910)
EXPECTED_HW = (910, 1728)
TARGET_CENTER_X = 864
TARGET_GROUND_Y = 900
CENTER_TOLERANCE = 28
GROUND_TOLERANCE = 12
HEIGHT_RANGE = (755, 805)

errors = []
warnings = []

if not BACKGROUND.exists():
    raise SystemExit(f'Missing creator background: {BACKGROUND}')
bg_pil = Image.open(BACKGROUND).convert('RGB')
if bg_pil.size != EXPECTED_WH:
    bg_pil = ImageOps.fit(bg_pil, EXPECTED_WH, Image.Resampling.LANCZOS)
bg = cv2.cvtColor(np.asarray(bg_pil), cv2.COLOR_RGB2BGR)

face_detector = None
if FACE_MODEL.exists():
    face_detector = cv2.FaceDetectorYN.create(str(FACE_MODEL), '', EXPECTED_WH, .52, .3, 5000)


def foreground_bbox(im):
    delta = cv2.absdiff(im, bg).mean(axis=2)
    mask = (delta > 10.0).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    if n <= 1:
        return None
    idx = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x, y, w, h, area = (int(v) for v in stats[idx])
    if area < 18000:
        return None
    return x, y, w, h


for gender, styles in EXPECTED.items():
    files = list((ROOT / gender).rglob('*.webp'))
    if len(files) != 125:
        errors.append(f'{gender}: expected 125 assets, got {len(files)}')

    reference_boxes = []
    face_hits = 0
    checked_faces = 0

    for skin in SKINS:
        for hair in HAIRS:
            group = []
            for style in styles:
                p = ROOT / gender / skin / hair / f'{style}.webp'
                if not p.exists() or p.stat().st_size < 1000:
                    errors.append(f'missing/empty: {p}')
                    continue
                im = cv2.imread(str(p), cv2.IMREAD_COLOR)
                if im is None or im.size == 0:
                    errors.append(f'undecodable: {p}')
                    continue
                if im.shape[:2] != EXPECTED_HW:
                    errors.append(f'unexpected format: {p} is {im.shape[1]}x{im.shape[0]}, expected 1728x910')
                    continue
                if im.std() < 10:
                    errors.append(f'near blank: {p}')
                    continue

                box = foreground_bbox(im)
                if box is None:
                    errors.append(f'avatar foreground not isolated: {p}')
                else:
                    x, y, w, h = box
                    center = x + w / 2
                    ground = y + h
                    if not HEIGHT_RANGE[0] <= h <= HEIGHT_RANGE[1]:
                        errors.append(f'full-body height drift: {p} detected {h}px, expected {HEIGHT_RANGE[0]}-{HEIGHT_RANGE[1]}')
                    if abs(center - TARGET_CENTER_X) > CENTER_TOLERANCE:
                        errors.append(f'horizontal placement drift: {p} center={center:.1f}, target={TARGET_CENTER_X}')
                    if abs(ground - TARGET_GROUND_Y) > GROUND_TOLERANCE:
                        errors.append(f'ground placement drift: {p} bottom={ground}, target={TARGET_GROUND_Y}')
                    reference_boxes.append((center, ground, h))

                if face_detector is not None and skin == 'medium' and hair == 'brown':
                    checked_faces += 1
                    _, faces = face_detector.detect(im)
                    if faces is not None and len(faces):
                        face_hits += 1

                group.append((style, p, im))

            digests = [hashlib.sha256(p.read_bytes()).hexdigest() for _, p, _ in group]
            if len(digests) == 5 and len(set(digests)) != 5:
                errors.append(f'{gender}/{skin}/{hair}: duplicate hairstyle files')

    if checked_faces and face_hits == 0:
        warnings.append(f'{gender}: face detector produced no hits on neutral diagnostic presets')

    if reference_boxes:
        centers = np.array([v[0] for v in reference_boxes])
        grounds = np.array([v[1] for v in reference_boxes])
        heights = np.array([v[2] for v in reference_boxes])
        if np.ptp(centers) > CENTER_TOLERANCE * 2:
            errors.append(f'{gender}: creator center spread too large ({centers.min():.1f}-{centers.max():.1f})')
        if np.ptp(grounds) > GROUND_TOLERANCE * 2:
            errors.append(f'{gender}: creator ground spread too large ({grounds.min():.1f}-{grounds.max():.1f})')
        if np.ptp(heights) > 35:
            errors.append(f'{gender}: creator body-height spread too large ({heights.min():.0f}-{heights.max():.0f})')


# Strong invariant required by the product: for a given male skin tone, changing
# hairstyle or hair colour is forbidden from changing the full-body base below
# the head.  Only codec noise is tolerated after WebP encoding.
MALE_BODY_Y0 = 350
MALE_BODY_X0 = 430
MALE_BODY_X1 = 1298
for skin in SKINS:
    ref_path = ROOT / 'male' / skin / 'brown' / 'male_textured.webp'
    ref = cv2.imread(str(ref_path), cv2.IMREAD_COLOR)
    if ref is None:
        errors.append(f'male fixed-body reference missing: {ref_path}')
        continue
    ref_body = ref[MALE_BODY_Y0:900, MALE_BODY_X0:MALE_BODY_X1].astype(np.int16)
    for hair in HAIRS:
        for style in EXPECTED['male']:
            p = ROOT / 'male' / skin / hair / f'{style}.webp'
            im = cv2.imread(str(p), cv2.IMREAD_COLOR)
            if im is None:
                continue
            body = im[MALE_BODY_Y0:900, MALE_BODY_X0:MALE_BODY_X1].astype(np.int16)
            diff = np.abs(body - ref_body)
            mean_diff = float(diff.mean())
            p99 = float(np.percentile(diff, 99))
            if mean_diff > 1.35 or p99 > 7.0:
                errors.append(
                    f'male full-body base changed outside head: {p} '
                    f'mean_diff={mean_diff:.3f} p99={p99:.1f}'
                )

if warnings:
    print('CREATOR HD VALIDATION WARNINGS')
    for warning in warnings:
        print(' -', warning)

if errors:
    print('CREATOR HD VALIDATION FAILED')
    for error in errors:
        print(' -', error)
    raise SystemExit(1)

print('Creator HD library validated: 250 assets; male body/clothes/arms/legs remain locked to one canonical full-body base; only skin tone and head/hair area may vary.')
