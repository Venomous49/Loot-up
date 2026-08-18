from pathlib import Path
import base64
import cv2
import numpy as np

ROOT = Path('.')
SRC64 = ROOT / 'assets/source/female_base.webp.b64'
SOURCE = ROOT / 'assets/source/female_base.webp'
OUT = ROOT / 'assets/creator/female'
OUT.mkdir(parents=True, exist_ok=True)

SOURCE.write_bytes(base64.b64decode(SRC64.read_text(encoding='ascii').strip()))
base = cv2.imread(str(SOURCE), cv2.IMREAD_COLOR)
if base is None:
    raise SystemExit('Unable to decode female source artwork')
h, w = base.shape[:2]
yy, xx = np.mgrid[0:h, 0:w]
hsv = cv2.cvtColor(base, cv2.COLOR_BGR2HSV)
H, S, V = cv2.split(hsv)

# Conservative masks. All geometry is limited to the central character so the
# alley/background can never become a coloured rectangle around the face.
character = (xx > .23*w) & (xx < .77*w) & (yy > .015*h) & (yy < .98*h)
head = (((xx-.495*w)/(.205*w))**2 + ((yy-.235*h)/(.255*h))**2) < 1
side_hair = (xx > .285*w) & (xx < .70*w) & (yy > .12*h) & (yy < .78*h)
face_guard = (((xx-.497*w)/(.105*w))**2 + ((yy-.285*h)/(.155*h))**2) < 1
hair_candidate = character & (head | side_hair) & ~face_guard & (V < 128) & (S > 18)
raw = hair_candidate.astype(np.uint8)*255
raw = cv2.morphologyEx(raw, cv2.MORPH_CLOSE, np.ones((5,5),np.uint8), iterations=2)
raw = cv2.morphologyEx(raw, cv2.MORPH_OPEN, np.ones((3,3),np.uint8), iterations=1)
# Keep components close to the actual head only.
num, labels, stats, cents = cv2.connectedComponentsWithStats(raw, 8)
hair_mask = np.zeros_like(raw)
for i in range(1,num):
    area = stats[i,cv2.CC_STAT_AREA]
    cx, cy = cents[i]
    if area > 40 and .27*w < cx < .72*w and .03*h < cy < .76*h:
        hair_mask[labels==i] = 255
hair_mask = cv2.GaussianBlur(hair_mask,(5,5),0)
if cv2.countNonZero(hair_mask) < 1000:
    raise SystemExit('Female hair mask unexpectedly small')

# Skin mask: recolour only plausible exposed skin and preserve luminance/detail.
skin_candidate = (H < 30) & (S > 35) & (S < 225) & (V > 45)
face = (((xx-.497*w)/(.10*w))**2 + ((yy-.29*h)/(.165*h))**2) < 1
neck = (xx>.435*w)&(xx<.56*w)&(yy>.405*h)&(yy<.61*h)
arm_r = (xx>.72*w)&(xx<.84*w)&(yy>.61*h)&(yy<.98*h)
skin_mask = (skin_candidate & (face|neck|arm_r)).astype(np.uint8)*255
skin_mask = cv2.morphologyEx(skin_mask,cv2.MORPH_OPEN,np.ones((3,3),np.uint8),iterations=1)
skin_mask = cv2.GaussianBlur(skin_mask,(5,5),0)

SKINS={
 'light':(226,184,154),'warm':(198,139,96),'medium':(160,105,72),
 'deep':(112,72,48),'dark':(72,46,32)}
HAIRS={'black':(23,20,20),'brown':(67,43,31),'blond':(191,151,93),'red':(137,61,35),'purple':(83,46,113)}
STYLES=['female_long','female_wavy','female_bob','female_ponytail','female_short']

def tint(src, mask, rgb, strength):
    srcf=src.astype(np.float32)
    target=np.array([rgb[2],rgb[1],rgb[0]],np.float32)
    lum=cv2.cvtColor(src,cv2.COLOR_BGR2GRAY).astype(np.float32)
    lum=np.clip(lum/115.0,.38,1.70)[...,None]
    col=np.clip(target[None,None,:]*lum,0,255)
    a=(mask.astype(np.float32)/255.0*strength)[...,None]
    return np.clip(srcf*(1-a)+col*a,0,255).astype(np.uint8)

def remove_mask(src, mask):
    m=cv2.dilate((mask>22).astype(np.uint8)*255,np.ones((5,5),np.uint8),iterations=1)
    return cv2.inpaint(src,m,3,cv2.INPAINT_TELEA)

def compose_style(skinned, hair_rgb, style):
    coloured=tint(skinned,hair_mask,hair_rgb,.94)
    if style=='female_long':
        return coloured
    # All shorter/tied styles start from a clean inpaint of only the unwanted
    # lower hair; the face itself is never warped or replaced.
    if style=='female_bob': cutoff=.54
    elif style=='female_short': cutoff=.39
    elif style=='female_ponytail': cutoff=.47
    else: cutoff=None
    if style=='female_wavy':
        # Gentle local wave inside the existing hair mask only.
        dx=(5.0*np.sin((yy/h)*14.0)).astype(np.float32)
        mapx=(xx.astype(np.float32)+dx)
        mapy=yy.astype(np.float32)
        warped=cv2.remap(coloured,mapx,mapy,cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT)
        a=(hair_mask.astype(np.float32)/255.0)[...,None]
        return np.clip(coloured.astype(np.float32)*(1-a)+warped.astype(np.float32)*a,0,255).astype(np.uint8)
    lower=hair_mask.copy()
    lower[yy < cutoff*h]=0
    clean=remove_mask(coloured,lower)
    if style=='female_ponytail':
        # Preserve a narrow back section to read visually as tied-back hair,
        # still sampled from the original real hair rather than a flat shape.
        keep=((xx>.58*w)&(xx<.69*w)&(yy>.34*h)&(yy<.68*h)).astype(np.uint8)*255
        keep=cv2.bitwise_and(keep,hair_mask)
        a=(keep.astype(np.float32)/255.0)[...,None]
        clean=np.clip(clean.astype(np.float32)*(1-a)+coloured.astype(np.float32)*a,0,255).astype(np.uint8)
    return clean

for skin_name,skin_rgb in SKINS.items():
    skinned=tint(base,skin_mask,skin_rgb,.78)
    for hair_name,hair_rgb in HAIRS.items():
        for style in STYLES:
            out=compose_style(skinned,hair_rgb,style)
            path=OUT/skin_name/hair_name/f'{style}.webp'
            path.parent.mkdir(parents=True,exist_ok=True)
            ok=cv2.imwrite(str(path),out,[cv2.IMWRITE_WEBP_QUALITY,94])
            if not ok: raise SystemExit(f'Failed writing {path}')

files=list(OUT.rglob('*.webp'))
if len(files)!=125: raise SystemExit(f'Expected 125 female presets, got {len(files)}')
print('Generated 125 full-image female creator presets')
