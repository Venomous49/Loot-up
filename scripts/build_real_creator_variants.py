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

# Masks are deliberately restricted to the character anatomy. This keeps the
# alley/background and clothing completely untouched.
head_region = (xx > w * .42) & (xx < w * .70) & (yy > h * .015) & (yy < h * .285)
hair_candidate = head_region & (V < 115) & (S > 12)
hair_mask = (hair_candidate.astype(np.uint8) * 255)
hair_mask = cv2.morphologyEx(hair_mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), iterations=2)
hair_mask = cv2.morphologyEx(hair_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)
hair_mask = cv2.GaussianBlur(hair_mask, (3, 3), 0)

skin_candidate = (H < 28) & (S > 28) & (S < 220) & (V > 42)
face = (xx > w * .44) & (xx < w * .66) & (yy > h * .085) & (yy < h * .315)
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


def tint_preserve_luma(src_bgr, mask, rgb, strength=1.0):
    src = src_bgr.astype(np.float32)
    target = np.array([rgb[2], rgb[1], rgb[0]], dtype=np.float32)
    gray = cv2.cvtColor(src_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    lum = np.clip(gray / 118.0, .38, 1.65)[..., None]
    coloured = np.clip(target[None, None, :] * lum, 0, 255)
    m = (mask.astype(np.float32) / 255.0 * strength)[..., None]
    return np.clip(src * (1 - m) + coloured * m, 0, 255).astype(np.uint8)


def hair_bbox(mask):
    ys, xs = np.where(mask > 24)
    if not len(xs):
        raise SystemExit('Hair mask is empty; source layout changed')
    pad = 3
    return max(0, xs.min() - pad), min(w - 1, xs.max() + pad), max(0, ys.min() - pad), min(h - 1, ys.max() + pad)


x0, x1, y0, y1 = hair_bbox(hair_mask)
base_hair_patch = base[y0:y1 + 1, x0:x1 + 1].copy()
base_hair_alpha = hair_mask[y0:y1 + 1, x0:x1 + 1].copy()


def place_patch(canvas_img, canvas_alpha, patch, alpha, cx, top):
    ph, pw = alpha.shape
    xa = int(round(cx - pw / 2))
    ya = int(round(top))
    xb, yb = xa + pw, ya + ph
    sx0, sy0 = max(0, -xa), max(0, -ya)
    sx1, sy1 = pw - max(0, xb - w), ph - max(0, yb - h)
    xa, ya = max(0, xa), max(0, ya)
    xb, yb = min(w, xb), min(h, yb)
    if xb <= xa or yb <= ya:
        return
    canvas_img[ya:yb, xa:xb] = patch[sy0:sy1, sx0:sx1]
    canvas_alpha[ya:yb, xa:xb] = np.maximum(canvas_alpha[ya:yb, xa:xb], alpha[sy0:sy1, sx0:sx1])


def make_hair_layer(style, hair_rgb):
    patch = tint_preserve_luma(base_hair_patch, base_hair_alpha, hair_rgb, .96)
    alpha = base_hair_alpha.copy()
    ph, pw = alpha.shape
    cx = (x0 + x1) / 2
    top = y0

    if style == 'male_short':
        nh = max(5, int(ph * .72))
        patch = cv2.resize(patch, (pw, nh), interpolation=cv2.INTER_AREA)
        alpha = cv2.resize(alpha, (pw, nh), interpolation=cv2.INTER_AREA)
        top = y1 - nh + 1
    elif style == 'male_medium':
        nw, nh = int(pw * 1.10), int(ph * 1.22)
        patch = cv2.resize(patch, (nw, nh), interpolation=cv2.INTER_CUBIC)
        alpha = cv2.resize(alpha, (nw, nh), interpolation=cv2.INTER_CUBIC)
        alpha = cv2.dilate(alpha, np.ones((3, 3), np.uint8), iterations=1)
        top = y0 - int(ph * .05)
    elif style == 'male_undercut':
        alpha = cv2.erode(alpha, np.ones((3, 3), np.uint8), iterations=1)
        ah, aw = alpha.shape
        for row in range(ah):
            t = row / max(1, ah - 1)
            cut = int(aw * .17 * t)
            if cut:
                alpha[row, :cut] = 0
                alpha[row, aw - cut:] = 0
    elif style == 'male_slick':
        M = np.float32([[1, .20, -pw * .09], [0, 1, 0]])
        patch = cv2.warpAffine(patch, M, (pw, ph), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        alpha = cv2.warpAffine(alpha, M, (pw, ph), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        alpha = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, np.ones((5, 3), np.uint8), iterations=1)

    layer = np.zeros_like(base)
    layer_alpha = np.zeros((h, w), np.uint8)
    place_patch(layer, layer_alpha, patch, alpha, cx, top)
    layer_alpha = cv2.GaussianBlur(layer_alpha, (3, 3), 0)
    return layer, layer_alpha


# Inpaint only the original hair area. This avoids the rectangular/duplicated
# character artefact produced by the previous transparent-character composite.
inpaint_mask = cv2.dilate((hair_mask > 18).astype(np.uint8) * 255, np.ones((3, 3), np.uint8), iterations=1)
hairless = cv2.inpaint(base, inpaint_mask, 3, cv2.INPAINT_TELEA)

for skin_name, skin_rgb in SKINS.items():
    skinned = tint_preserve_luma(base, skin_mask, skin_rgb, .82)
    # Replace only the hair region with the inpainted source, preserving all other pixels.
    rm = (inpaint_mask.astype(np.float32) / 255.0)[..., None]
    clean_head = np.clip(skinned.astype(np.float32) * (1 - rm) + hairless.astype(np.float32) * rm, 0, 255).astype(np.uint8)

    for hair_name, hair_rgb in HAIRS.items():
        for style in STYLES:
            hair_layer, style_alpha = make_hair_layer(style, hair_rgb)
            a = (style_alpha.astype(np.float32) / 255.0)[..., None]
            comp = np.clip(clean_head.astype(np.float32) * (1 - a) + hair_layer.astype(np.float32) * a, 0, 255).astype(np.uint8)

            outdir = OUT / skin_name / hair_name
            outdir.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(outdir / f'{style}.webp'), comp, [cv2.IMWRITE_WEBP_QUALITY, 94])

print('Generated', len(SKINS) * len(HAIRS) * len(STYLES), 'clean male creator variants from full artwork')
