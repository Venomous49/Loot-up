from pathlib import Path
import cv2
import numpy as np

ROOT = Path('.')
SOURCE = ROOT / '01-debutant.webp'
OUT = ROOT / 'assets' / 'creator' / 'male'
OUT.mkdir(parents=True, exist_ok=True)

base = cv2.imread(str(SOURCE), cv2.IMREAD_COLOR)
if base is None:
    raise SystemExit('Missing 01-debutant.webp')

h, w = base.shape[:2]
hsv = cv2.cvtColor(base, cv2.COLOR_BGR2HSV)
H, S, V = cv2.split(hsv)

# IMPORTANT: the hair mask is a tight polygon entirely ABOVE the face.
# No ellipse, rectangle, skin overlay or browser-side transformation is used.
# Coordinates are relative so the same logic works if the artwork resolution changes.
poly = np.array([
    [int(w*.535), int(h*.045)],
    [int(w*.565), int(h*.018)],
    [int(w*.600), int(h*.020)],
    [int(w*.625), int(h*.050)],
    [int(w*.632), int(h*.082)],
    [int(w*.620), int(h*.115)],
    [int(w*.598), int(h*.128)],
    [int(w*.570), int(h*.120)],
    [int(w*.545), int(h*.098)],
    [int(w*.530), int(h*.070)],
], np.int32)
zone = np.zeros((h,w), np.uint8)
cv2.fillPoly(zone, [poly], 255)
# Keep dark textured pixels only inside the polygon. This excludes forehead/eyes/skin.
hair_candidate = ((V < 145) & (S > 8)).astype(np.uint8) * 255
hair_mask = cv2.bitwise_and(zone, hair_candidate)
hair_mask = cv2.morphologyEx(hair_mask, cv2.MORPH_CLOSE, np.ones((3,3),np.uint8), iterations=1)
hair_mask = cv2.morphologyEx(hair_mask, cv2.MORPH_OPEN, np.ones((2,2),np.uint8), iterations=1)
hair_mask = cv2.GaussianBlur(hair_mask, (3,3), 0)
if cv2.countNonZero(hair_mask) < 20:
    raise SystemExit('Hair mask too small: refusing to publish')

# Skin recolouring is restricted to plausible skin pixels and anatomy regions only.
# It never paints a geometric shape: only already-skin-coloured source pixels are tinted.
skin_candidate = (H < 28) & (S > 35) & (S < 230) & (V > 45)
region = np.zeros((h,w), np.uint8)
cv2.rectangle(region, (int(w*.535),int(h*.115)), (int(w*.635),int(h*.305)), 255, -1) # face/neck
cv2.rectangle(region, (int(w*.375),int(h*.285)), (int(w*.705),int(h*.650)), 255, -1) # hands/arms
cv2.rectangle(region, (int(w*.400),int(h*.555)), (int(w*.690),int(h*.925)), 255, -1) # exposed legs
skin_mask = ((skin_candidate.astype(np.uint8)*255) & region)
skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, np.ones((3,3),np.uint8), iterations=1)
skin_mask = cv2.GaussianBlur(skin_mask, (5,5), 0)

SKINS = {
    'light': (218,171,137),
    'warm': (190,128,82),
    'medium': (150,97,60),
    'deep': (105,66,39),
    'dark': (62,38,25),
}
HAIRS = {
    'black': (22,18,18),
    'brown': (58,38,28),
    'blond': (186,144,82),
    'red': (126,55,30),
    'purple': (78,42,108),
}
STYLES = ['male_textured','male_short','male_medium','male_undercut','male_slick']


def tint_preserve_luma(src, mask, rgb, strength):
    srcf = src.astype(np.float32)
    gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY).astype(np.float32)
    target = np.array([rgb[2],rgb[1],rgb[0]], np.float32)
    lum = np.clip(gray / 105.0, .38, 1.65)[...,None]
    coloured = np.clip(target[None,None,:] * lum, 0, 255)
    a = (mask.astype(np.float32)/255.0*strength)[...,None]
    return np.clip(srcf*(1-a)+coloured*a,0,255).astype(np.uint8)

ys,xs = np.where(hair_mask > 18)
if len(xs) == 0:
    raise SystemExit('Empty hair mask')
pad = max(2, int(w*.003))
x0,x1 = max(0,xs.min()-pad), min(w-1,xs.max()+pad)
y0,y1 = max(0,ys.min()-pad), min(h-1,ys.max()+pad)
base_patch = base[y0:y1+1,x0:x1+1].copy()
base_alpha = hair_mask[y0:y1+1,x0:x1+1].copy()
center_x = (x0+x1)//2

# Remove ONLY original hair pixels. The face is below the polygon and cannot be touched.
inpaint_mask = cv2.dilate((hair_mask>18).astype(np.uint8)*255, np.ones((3,3),np.uint8), iterations=1)
inpaint_mask[zone==0] = 0


def build_hair(style, hair_rgb):
    patch = tint_preserve_luma(base_patch, base_alpha, hair_rgb, .98)
    alpha = base_alpha.copy()
    ph,pw = alpha.shape
    sx=sy=1.0; dx=dy=0; shear=0.0
    if style == 'male_short':
        sx,sy = .88,.62; dy=int(ph*.30)
    elif style == 'male_medium':
        sx,sy = 1.18,1.30; dy=-int(ph*.12)
    elif style == 'male_undercut':
        sx,sy = .94,.78; dy=int(ph*.16)
    elif style == 'male_slick':
        sx,sy = 1.12,.74; dx=int(pw*.14); dy=int(ph*.18); shear=.24

    nw,nh = max(4,int(pw*sx)), max(4,int(ph*sy))
    patch = cv2.resize(patch,(nw,nh),interpolation=cv2.INTER_CUBIC)
    alpha = cv2.resize(alpha,(nw,nh),interpolation=cv2.INTER_CUBIC)

    if style == 'male_undercut':
        ah,aw=alpha.shape
        for r in range(ah):
            t=r/max(1,ah-1)
            cut=int(aw*.24*t)
            if cut:
                alpha[r,:cut]=0; alpha[r,aw-cut:]=0
    if shear:
        M=np.float32([[1,shear,-nw*.10],[0,1,0]])
        patch=cv2.warpAffine(patch,M,(nw,nh),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT)
        alpha=cv2.warpAffine(alpha,M,(nw,nh),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT,borderValue=0)

    alpha=cv2.GaussianBlur(alpha,(3,3),0)
    return patch,alpha,dx,dy


def composite_variant(skin_rgb, hair_rgb, style):
    skinned=tint_preserve_luma(base,skin_mask,skin_rgb,.80)
    clean=cv2.inpaint(skinned,inpaint_mask,3,cv2.INPAINT_TELEA)
    patch,alpha,dx,dy=build_hair(style,hair_rgb)
    ah,aw=alpha.shape
    left=int(center_x-aw/2+dx); top=int(y0+dy)
    right,bottom=left+aw,top+ah
    sx0,sy0=max(0,-left),max(0,-top)
    sx1,sy1=aw-max(0,right-w),ah-max(0,bottom-h)
    dx0,dy0=max(0,left),max(0,top)
    dx1,dy1=min(w,right),min(h,bottom)
    if dx1>dx0 and dy1>dy0:
        a=(alpha[sy0:sy1,sx0:sx1].astype(np.float32)/255.0)[...,None]
        roi=clean[dy0:dy1,dx0:dx1].astype(np.float32)
        pp=patch[sy0:sy1,sx0:sx1].astype(np.float32)
        clean[dy0:dy1,dx0:dx1]=np.clip(roi*(1-a)+pp*a,0,255).astype(np.uint8)
    return clean

count=0
for skin_name,skin_rgb in SKINS.items():
    for hair_name,hair_rgb in HAIRS.items():
        outdir=OUT/skin_name/hair_name
        outdir.mkdir(parents=True,exist_ok=True)
        for style in STYLES:
            out=composite_variant(skin_rgb,hair_rgb,style)
            path=outdir/f'{style}.webp'
            if not cv2.imwrite(str(path),out,[cv2.IMWRITE_WEBP_QUALITY,92]):
                raise SystemExit(f'Failed writing {path}')
            count+=1

if count != 125:
    raise SystemExit(f'Expected 125 presets, got {count}')
print(f'Generated {count} complete male preset images without face overlays')
