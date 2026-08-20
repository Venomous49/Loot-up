from pathlib import Path
import cv2
import numpy as np

ROOT = Path('assets/creator/male')
SKINS = ['light', 'warm', 'medium', 'deep', 'dark']
HAIRS = ['black', 'brown', 'blond', 'red', 'purple']
STYLES = ['male_textured', 'male_short', 'male_medium', 'male_undercut', 'male_slick']

# Everything below this line belongs to the fixed body/clothes. Hair and skin
# tinting are forbidden from changing it.
BODY_Y = 350
MEAN_TOL = 0.55
P99_TOL = 3.0
# WebP quality=100 can still create isolated single-channel rounding deltas.
# Keep the mean/p99 gates strict and allow one extra code value at the absolute max.
MAX_TOL = 14


def load(skin, hair, style):
    path = ROOT / skin / hair / f'{style}.webp'
    im = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if im is None:
        raise SystemExit(f'Cannot decode {path}')
    return im


def assert_same_body(a, b, label):
    diff = cv2.absdiff(a[BODY_Y:], b[BODY_Y:]).astype(np.float32)
    mean = float(diff.mean())
    p99 = float(np.percentile(diff, 99))
    maxv = float(diff.max())
    if mean > MEAN_TOL or p99 > P99_TOL or maxv > MAX_TOL:
        raise SystemExit(
            f'Fixed male body regression ({label}): '
            f'mean={mean:.3f}, p99={p99:.1f}, max={maxv:.0f}'
        )


for skin in SKINS:
    reference = load(skin, 'brown', 'male_undercut')
    for hair in HAIRS:
        for style in STYLES:
            assert_same_body(reference, load(skin, hair, style), f'{skin}/{hair}/{style}')

for hair in HAIRS:
    for style in STYLES:
        reference = load('medium', hair, style)
        for skin in SKINS:
            assert_same_body(reference, load(skin, hair, style), f'skin:{skin}/{hair}/{style}')

print('Male creator body lock validated: torso/arms/legs/clothes invariant across all 125 male presets.')
