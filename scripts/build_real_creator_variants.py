from pathlib import Path
import cv2
import numpy as np

ROOT = Path('.')
CHAR = ROOT / '01-debutant-character.png'
BG = ROOT / '01-debutant-background.webp'
OUT = ROOT / 'assets' / 'creator' / 'male'
OUT.mkdir(parents=True, exist_ok=True)

char = cv2.imread(str(CHAR), cv2.IMREAD_UNCHANGED)
bg = cv2.imread(str(BG), cv2.IMREAD_COLOR)
if char is None or char.shape[2] != 4:
    raise SystemExit('Missing transparent beginner character')
if bg is None:
    raise SystemExit('Missing beginner background')

h, w = char.shape[:2]
if bg.shape[:2] != (h, w):
    bg = cv2.resize(bg, (w, h), interpolation=cv2.INTER_CUBIC)

bgr = char[:, :, :3].copy()
alpha = char[:, :, 3].copy()
alpha_f = alpha.astype(np.float32) / 255.0

# ---------- masks built from the REAL character pixels ----------
hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
H, S, V = cv2.split(hsv)
opaque = alpha > 24

# Hair: dark pixels in a tight head region only, so hoodie/background can never be recoloured.
yy, xx = np.mgrid[0:h, 0:w]
head_region = (xx > w*.37) & (xx < w*.66) & (yy > h*.015) & (yy < h*.245)
hair_mask = opaque & head_region & (V < 105) & (S > 18)
# Fill small gaps while keeping exact image-derived silhouette.
hm = (hair_mask.astype(np.uint8) * 255)
hm = cv2.morphologyEx(hm, cv2.MORPH_CLOSE, np.ones((5,5),np.uint8), iterations=2)
hm = cv2.morphologyEx(hm, cv2.MORPH_OPEN, np.ones((3,3),np.uint8), iterations=1)

# Skin: HSV candidate pixels restricted to anatomically plausible zones.
skin_candidate = opaque & (H < 25) & (S > 35) & (S < 210) & (V > 45)
face = (xx > w*.405) & (xx < w*.625) & (yy > h*.07) & (yy < h*.30)
left_arm = (xx > w*.27) & (xx < w*.46) & (yy > h*.27) & (yy < h*.64)
right_arm = (xx > w*.57) & (xx < w*.77) & (yy > h*.27) & (yy < h*.65)
legs = (xx > w*.32) & (xx < w*.68) & (yy > h*.58) & (yy < h*.91)
skin_mask = skin_candidate & (face | left_arm | right_arm | legs)
sm = (skin_mask.astype(np.uint8) * 255)
sm = cv2.morphologyEx(sm, cv2.MORPH_OPEN, np.ones((3,3),np.uint8), iterations=1)
sm = cv2.GaussianBlur(sm, (5,5), 0)

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
STYLES = ['male_textured','male_short','male_medium','male_undercut','male_slick']


def tint_preserve_luma(src_bgr, mask, rgb):
    out = src_bgr.copy().astype(np.float32)
    target = np.array([rgb[2], rgb[1], rgb[0]], dtype=np.float32)  # RGB -> BGR
    gray = cv2.cvtColor(src_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    # Preserve original light/shadow detail around target colour.
    lum = np.clip(gray / 128.0, .42, 1.55)[...,None]
    coloured = np.clip(target[None,None,:] * lum, 0, 255)
    m = (mask.astype(np.float32)/255.0)[...,None]
    return np.clip(out*(1-m) + coloured*m, 0, 255).astype(np.uint8)


def hairstyle_mask(base, style):
    ys, xs = np.where(base > 15)
    if len(xs) == 0:
        return base.copy()
    x0,x1,y0,y1 = xs.min(),xs.max(),ys.min(),ys.max()
    roi = base[y0:y1+1, x0:x1+1]
    canvas = np.zeros_like(base)

    if style == 'male_textured':
        return base.copy()
    if style == 'male_short':
        new_h = max(3, int(roi.shape[0]*.72))
        r = cv2.resize(roi, (roi.shape[1], new_h), interpolation=cv2.INTER_AREA)
        yy0 = y1-new_h+1
        canvas[yy0:y1+1, x0:x1+1] = r
    elif style == 'male_medium':
        r = cv2.dilate(roi, np.ones((5,5),np.uint8), iterations=1)
        r = cv2.resize(r, (int(r.shape[1]*1.06), int(r.shape[0]*1.15)), interpolation=cv2.INTER_CUBIC)
        rh,rw = r.shape
        cx=(x0+x1)//2; bottom=y1+3
        xa=max(0,cx-rw//2); xb=min(w,xa+rw); ya=max(0,bottom-rh); yb=min(h,ya+rh)
        canvas[ya:yb,xa:xb]=r[:yb-ya,:xb-xa]
    elif style == 'male_undercut':
        r = cv2.erode(roi, np.ones((3,3),np.uint8), iterations=1)
        # Narrow the lower sides but preserve the textured top.
        rh,rw=r.shape
        for y in range(rh):
            t=y/max(1,rh-1)
            cut=int((rw*.13)*t)
            if cut:
                r[y,:cut]=0; r[y,rw-cut:]=0
        canvas[y0:y1+1,x0:x1+1]=r
    elif style == 'male_slick':
        rh,rw=roi.shape
        M=np.float32([[1,.18,-rw*.08],[0,1,0]])
        r=cv2.warpAffine(roi,M,(rw,rh),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
        r=cv2.morphologyEx(r,cv2.MORPH_CLOSE,np.ones((5,3),np.uint8),iterations=1)
        canvas[y0:y1+1,x0:x1+1]=r
    return cv2.GaussianBlur(canvas,(3,3),0)


for skin_name, skin_rgb in SKINS.items():
    skin_bgr = tint_preserve_luma(bgr, sm, skin_rgb)
    for hair_name, hair_rgb in HAIRS.items():
        for style in STYLES:
            styled = hairstyle_mask(hm, style)
            # Remove original detected hair before applying transformed real-hair texture.
            result = skin_bgr.copy()
            base_m = (hm.astype(np.float32)/255.0)[...,None]
            # Fill removed hair from nearby dark neutral tone to avoid duplicate silhouettes.
            neutral = np.full_like(result, (28,27,27))
            result = np.clip(result*(1-base_m) + neutral*base_m,0,255).astype(np.uint8)
            # Use original hair texture resized through the style mask; recolour while preserving luma.
            hair_col = tint_preserve_luma(bgr, styled, hair_rgb)
            style_m = (styled.astype(np.float32)/255.0)[...,None]
            result = np.clip(result*(1-style_m) + hair_col*style_m,0,255).astype(np.uint8)

            # Composite on the validated background. No CSS painting needed in browser.
            af = alpha_f[...,None]
            comp = np.clip(result.astype(np.float32)*af + bg.astype(np.float32)*(1-af),0,255).astype(np.uint8)
            outdir = OUT / skin_name / hair_name
            outdir.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(outdir / f'{style}.webp'), comp, [cv2.IMWRITE_WEBP_QUALITY, 93])

print('Generated', len(SKINS)*len(HAIRS)*len(STYLES), 'real male creator variants')