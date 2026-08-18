from pathlib import Path
import cv2
import numpy as np

ROOT = Path('.')
SOURCE = ROOT / '01-debutant.webp'
OUT = ROOT / 'assets' / 'creator' / 'male'
OUT.mkdir(parents=True, exist_ok=True)

base = cv2.imread(str(SOURCE), cv2.IMREAD_COLOR)
if base is None:
    raise SystemExit('Missing validated 01-debutant.webp source artwork')

h, w = base.shape[:2]
hsv = cv2.cvtColor(base, cv2.COLOR_BGR2HSV)
H, S, V = cv2.split(hsv)
yy, xx = np.mgrid[0:h, 0:w]

# IMPORTANT: the previous broad head rectangle included dark wall/background
# pixels. When transformed as hair it produced the large square visible in the
# creator. The mask below is intentionally tiny and elliptical around the real
# hair only, so no background or torso pixel can ever become part of a style.
cx, cy = w * .585, h * .105
rx, ry = w * .085, h * .095
hair_zone = (((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2) <= 1.0
hair_zone &= yy < h * .205
hair_candidate = hair_zone & (V < 125) & (S > 8)
raw = (hair_candidate.astype(np.uint8) * 255)

# Keep only connected components that live in the upper central hair zone.
num, labels, stats, cents = cv2.connectedComponentsWithStats(raw, 8)
mask = np.zeros_like(raw)
for i in range(1, num):
    area = stats[i, cv2.CC_STAT_AREA]
    ccx, ccy = cents[i]
    if area < 8:
        continue
    if abs(ccx - cx) <= rx * .95 and abs(ccy - cy) <= ry * .95:
        mask[labels == i] = 255

# Intersect again with the ellipse after morphology: hard guarantee that the
# mask cannot grow into the background.
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8), iterations=1)
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8), iterations=1)
mask[~hair_zone] = 0
hair_mask = cv2.GaussianBlur(mask, (3, 3), 0)

if cv2.countNonZero(hair_mask) < 30:
    raise SystemExit('Hair mask unexpectedly small; aborting rather than publishing broken assets')

# Skin recolouring is likewise restricted to plausible anatomy regions.
skin_candidate = (H < 28) & (S > 28) & (S < 220) & (V > 42)
face = (xx > w * .46) & (xx < w * .66) & (yy > h * .09) & (yy < h * .31)
left_arm = (xx > w * .29) & (xx < w * .47) & (yy > h * .27) & (yy < h * .64)
right_arm = (xx > w * .57) & (xx < w * .78) & (yy > h * .27) & (yy < h * .66)
legs = (xx > w * .32) & (xx < w * .70) & (yy > h * .57) & (yy < h * .92)
skin_mask = (skin_candidate & (face | left_arm | right_arm | legs)).astype(np.uint8) * 255
skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)
skin_mask = cv2.GaussianBlur(skin_mask, (5, 5), 0)

SKINS = {
    'light': (218, 171, 137),
    'warm': (190, 128, 82),
    'medium': (150, 97, 60),
    'deep': (105, 66, 39),
    'dark': (62, 38, 25),
}
HAIRS = {
    'black': (22, 18, 18),
    'brown': (58, 38, 28),
    'blond': (186, 144, 82),
    'red': (126, 55, 30),
    'purple': (78, 42, 108),
}
STYLES = ['male_textured', 'male_short', 'male_medium', 'male_undercut', 'male_slick']


def tint_preserve_luma(src_bgr, alpha_mask, rgb, strength=1.0):
    src = src_bgr.astype(np.float32)
    target = np.array([rgb[2], rgb[1], rgb[0]], dtype=np.float32)
    gray = cv2.cvtColor(src_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    lum = np.clip(gray / 118.0, .40, 1.60)[..., None]
    coloured = np.clip(target[None, None, :] * lum, 0, 255)
    a = (alpha_mask.astype(np.float32) / 255.0 * strength)[..., None]
    return np.clip(src * (1 - a) + coloured * a, 0, 255).astype(np.uint8)


def bbox_from_mask(alpha_mask):
    ys, xs = np.where(alpha_mask > 24)
    if len(xs) == 0:
        raise SystemExit('Empty hair mask')
    pad = 2
    return max(0, xs.min()-pad), min(w-1, xs.max()+pad), max(0, ys.min()-pad), min(h-1, ys.max()+pad)


x0, x1, y0, y1 = bbox_from_mask(hair_mask)
base_patch = base[y0:y1+1, x0:x1+1].copy()
base_alpha = hair_mask[y0:y1+1, x0:x1+1].copy()


def safe_resize(patch, alpha, sx, sy):
    nw = max(3, int(round(patch.shape[1] * sx)))
    nh = max(3, int(round(patch.shape[0] * sy)))
    p = cv2.resize(patch, (nw, nh), interpolation=cv2.INTER_CUBIC)
    a = cv2.resize(alpha, (nw, nh), interpolation=cv2.INTER_CUBIC)
    return p, a


def build_style(style, hair_rgb):
    patch = tint_preserve_luma(base_patch, base_alpha, hair_rgb, .96)
    alpha = base_alpha.copy()
    ph, pw = alpha.shape

    sx = sy = 1.0
    shear = 0.0
    side_trim = 0.0
    y_shift = 0

    if style == 'male_short':
        sy = .72
        y_shift = int(ph * .23)
    elif style == 'male_medium':
        sx, sy = 1.08, 1.14
        y_shift = -int(ph * .04)
    elif style == 'male_undercut':
        sx, sy = .94, .93
        side_trim = .15
        y_shift = int(ph * .03)
    elif style == 'male_slick':
        sx, sy = 1.03, .92
        shear = .16
        y_shift = int(ph * .02)

    patch, alpha = safe_resize(patch, alpha, sx, sy)
    ah, aw = alpha.shape

    if side_trim:
        for row in range(ah):
            t = row / max(1, ah-1)
            cut = int(aw * side_trim * t)
            if cut:
                alpha[row, :cut] = 0
                alpha[row, aw-cut:] = 0

    if shear:
        M = np.float32([[1, shear, -aw * shear * .45], [0, 1, 0]])
        patch = cv2.warpAffine(patch, M, (aw, ah), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        alpha = cv2.warpAffine(alpha, M, (aw, ah), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

    alpha = cv2.GaussianBlur(alpha, (3,3), 0)

    layer = np.zeros_like(base)
    layer_a = np.zeros((h,w), np.uint8)
    center_x = int(round((x0+x1)/2))
    left = center_x - aw//2
    top = y0 + y_shift
    right, bottom = left + aw, top + ah

    # Clamp placement safely to image bounds.
    sx0, sy0 = max(0,-left), max(0,-top)
    sx1, sy1 = aw-max(0,right-w), ah-max(0,bottom-h)
    dx0, dy0 = max(0,left), max(0,top)
    dx1, dy1 = min(w,right), min(h,bottom)
    if dx1 > dx0 and dy1 > dy0:
        layer[dy0:dy1,dx0:dx1] = patch[sy0:sy1,sx0:sx1]
        layer_a[dy0:dy1,dx0:dx1] = alpha[sy0:sy1,sx0:sx1]

    # Absolute safety crop: no generated hairstyle alpha is allowed outside a
    # small ellipse around the head. This permanently prevents square artefacts.
    style_zone = (((xx-cx)/(rx*1.22))**2 + ((yy-(cy+.01*h))/(ry*1.20))**2) <= 1.0
    layer_a[~style_zone] = 0
    return layer, layer_a


# Remove only the original real hair, never a rectangular region.
inpaint_mask = cv2.dilate((hair_mask > 20).astype(np.uint8)*255, np.ones((3,3),np.uint8), iterations=1)
inpaint_mask[~hair_zone] = 0
hairless = cv2.inpaint(base, inpaint_mask, 2, cv2.INPAINT_TELEA)

for skin_name, skin_rgb in SKINS.items():
    skinned = tint_preserve_luma(base, skin_mask, skin_rgb, .82)
    rm = (inpaint_mask.astype(np.float32)/255.0)[...,None]
    clean = np.clip(skinned.astype(np.float32)*(1-rm) + hairless.astype(np.float32)*rm,0,255).astype(np.uint8)

    for hair_name, hair_rgb in HAIRS.items():
        for style in STYLES:
            layer, a8 = build_style(style, hair_rgb)
            a = (a8.astype(np.float32)/255.0)[...,None]
            comp = np.clip(clean.astype(np.float32)*(1-a) + layer.astype(np.float32)*a,0,255).astype(np.uint8)
            outdir = OUT / skin_name / hair_name
            outdir.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(outdir / f'{style}.webp'), comp, [cv2.IMWRITE_WEBP_QUALITY, 94])

print('Generated', len(SKINS)*len(HAIRS)*len(STYLES), 'safe full-image male creator variants')
