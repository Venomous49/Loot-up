from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'assets' / 'creator_sources' / 'fullbody'
OUT = ROOT / 'assets' / 'creator' / 'male'
SIZE = (1728, 910)
SKINS = ['light','warm','medium','deep','dark']
HAIRS = ['black','brown','blond','red','purple']
STYLES = ['male_textured','male_short','male_medium','male_undercut','male_slick']

base = ImageOps.fit(Image.open(SRC / 'male_base.png').convert('RGBA'), SIZE, Image.Resampling.LANCZOS)
alpha = np.asarray(base.getchannel('A'), dtype=np.uint8)
ys, xs = np.where(alpha > 18)
if len(xs) < 1000:
    raise SystemExit('Dedicated male fullbody base has no usable alpha')
x0,x1,y0,y1 = int(xs.min()),int(xs.max()),int(ys.min()),int(ys.max())
if y1-y0+1 < 600 or y1 < 750:
    raise SystemExit(f'Dedicated male base is not head-to-feet: {(x0,y0,x1,y1)}')

files = list(OUT.rglob('*.webp'))
if len(files) != 125:
    raise SystemExit(f'Expected 125 male assets, got {len(files)}')

# Every style/color must be unique, but the body below the head must remain fixed.
for skin in SKINS:
    ref = cv2.imread(str(OUT / skin / 'brown' / 'male_undercut.webp'))
    if ref is None or ref.shape[:2] != (910,1728):
        raise SystemExit(f'Bad reference asset for skin {skin}')
    digests = set()
    for hair in HAIRS:
        for style in STYLES:
            p = OUT / skin / hair / f'{style}.webp'
            im = cv2.imread(str(p))
            if im is None or im.shape[:2] != (910,1728):
                raise SystemExit(f'Bad asset: {p}')
            body_diff = cv2.absdiff(ref[390:], im[390:]).astype(np.float32)
            if float(body_diff.mean()) > .7 or float(np.percentile(body_diff,99)) > 4.0:
                raise SystemExit(f'Body/clothes changed below head: {p}')
            import hashlib
            digests.add(hashlib.sha256(p.read_bytes()).hexdigest())
    if len(digests) != 25:
        raise SystemExit(f'Expected 25 distinct style/color assets for {skin}, got {len(digests)}')

# Skin changes may not alter clothing/lower body.
for hair in HAIRS:
    for style in STYLES:
        ref = cv2.imread(str(OUT / 'medium' / hair / f'{style}.webp'))
        for skin in SKINS:
            im = cv2.imread(str(OUT / skin / hair / f'{style}.webp'))
            diff = cv2.absdiff(ref[390:], im[390:]).astype(np.float32)
            if float(diff.mean()) > .7 or float(np.percentile(diff,99)) > 4.0:
                raise SystemExit(f'Skin tone changed clothes/body: {skin}/{hair}/{style}')

print('Dedicated fullbody male creator validated: head-to-feet base, 125 distinct presets, body/clothes invariant below head.')
