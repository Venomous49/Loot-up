from pathlib import Path
import base64
import cv2
import numpy as np

ROOT = Path('.')
SRC64 = ROOT / 'assets/source/female_base.webp.b64'
SRC64_PART2 = ROOT / 'assets/source/female_base.webp.b64.part2'
SOURCE = ROOT / 'assets/source/female_base.webp'
OUT = ROOT / 'assets/creator/female'
OUT.mkdir(parents=True, exist_ok=True)

encoded = SRC64.read_text(encoding='ascii').strip()
if SRC64_PART2.exists():
    encoded += SRC64_PART2.read_text(encoding='ascii').strip()
SOURCE.write_bytes(base64.b64decode(encoded, validate=True))
base = cv2.imread(str(SOURCE), cv2.IMREAD_COLOR)
if base is None:
    raise SystemExit('Unable to decode female source artwork')
h, w = base.shape[:2]
yy, xx = np.mgrid[0:h, 0:w]
hsv = cv2.cvtColor(base, cv2.COLOR_BGR2HSV)
H, S, V = cv2.split(hsv)

# Tight, hand-fitted female hair geometry. The mask is clamped after every
# morphology operation so background pixels can never become a square overlay.
geom = np.zeros((h,w), np.uint8)
cv2.ellipse(geom,(int(.501*w),int(.224*h)),(int(.136*w),int(.200*h)),0,0,360,255,-1)
left = np.array([
    [.390*w,.13*h],[.452*w,.12*h],[.476*w,.24*h],[.470*w,.36*h],
    [.458*w,.50*h],[.438*w,.66*h],[.418*w,.825*h],[.383*w,.825*h],
    [.394*w,.67*h],[.390*w,.53*h],[.372*w,.365*h]
],np.int32)
right = np.array([
    [.545*w,.12*h],[.607*w,.14*h],[.638*w,.26*h],[.656*w,.40*h],
    [.653*w,.55*h],[.637*w,.71*h],[.619*w,.815*h],[.590*w,.815*h],
    [.600*w,.665*h],[.589*w,.52*h],[.575*w,.355*h]
],np.int32)
cv2.fillPoly(geom,[left,right],255)
face_guard=np.zeros((h,w),np.uint8)
cv2.ellipse(face_guard,(int(.498*w),int(.311*h)),(int(.106*w),int(.165*h)),0,0,360,255,-1)
geom[face_guard>0]=0
hair_candidate=(geom>0)&(S>35)&(V<150)&((H<30)|(H>165))
hair_mask=hair_candidate.astype(np.uint8)*255
hair_mask=cv2.morphologyEx(hair_mask,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8),iterations=1)
hair_mask=cv2.GaussianBlur(hair_mask,(3,3),0)
hair_mask[geom==0]=0
if not (12000 < cv2.countNonZero(hair_mask) < 42000):
    raise SystemExit(f'Female hair mask unsafe size: {cv2.countNonZero(hair_mask)}')

skin_candidate=(H<30)&(S>35)&(S<225)&(V>45)
face=(((xx-.497*w)/(.105*w))**2+((yy-.31*h)/(.17*h))**2)<1
neck=(xx>.435*w)&(xx<.56*w)&(yy>.405*h)&(yy<.62*h)
arm_r=(xx>.72*w)&(xx<.84*w)&(yy>.61*h)&(yy<.98*h)
skin_mask=(skin_candidate&(face|neck|arm_r)).astype(np.uint8)*255
skin_mask=cv2.morphologyEx(skin_mask,cv2.MORPH_OPEN,np.ones((3,3),np.uint8),iterations=1)
skin_mask=cv2.GaussianBlur(skin_mask,(5,5),0)

SKINS={
 'light':(226,184,154),'warm':(198,139,96),'medium':(160,105,72),
 'deep':(112,72,48),'dark':(72,46,32)}
HAIRS={'black':(23,20,20),'brown':(67,43,31),'blond':(191,151,93),'red':(137,61,35),'purple':(83,46,113)}
STYLES=['female_long','female_wavy','female_bob','female_ponytail','female_short']

def tint(src,mask,rgb,strength):
    srcf=src.astype(np.float32)
    target=np.array([rgb[2],rgb[1],rgb[0]],np.float32)
    lum=cv2.cvtColor(src,cv2.COLOR_BGR2GRAY).astype(np.float32)
    lum=np.clip(lum/115.0,.38,1.70)[...,None]
    col=np.clip(target[None,None,:]*lum,0,255)
    a=(mask.astype(np.float32)/255.0*strength)[...,None]
    return np.clip(srcf*(1-a)+col*a,0,255).astype(np.uint8)

def remove_mask(src,mask):
    m=cv2.dilate((mask>22).astype(np.uint8)*255,np.ones((3,3),np.uint8),iterations=1)
    m[face_guard>0]=0
    return cv2.inpaint(src,m,2,cv2.INPAINT_TELEA)

def compose_style(skinned,hair_rgb,style):
    coloured=tint(skinned,hair_mask,hair_rgb,.92)
    if style=='female_long': return coloured
    if style=='female_wavy':
        dx=(4.0*np.sin((yy/h)*15.0)).astype(np.float32)
        warped=cv2.remap(coloured,xx.astype(np.float32)+dx,yy.astype(np.float32),cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT)
        a=(hair_mask.astype(np.float32)/255.0)[...,None]
        return np.clip(coloured.astype(np.float32)*(1-a)+warped.astype(np.float32)*a,0,255).astype(np.uint8)
    cutoff={'female_bob':.57,'female_ponytail':.49,'female_short':.405}[style]
    lower=hair_mask.copy(); lower[yy<cutoff*h]=0
    clean=remove_mask(coloured,lower)
    if style=='female_ponytail':
        keep=((xx>.585*w)&(xx<.635*w)&(yy>.39*h)&(yy<.68*h)).astype(np.uint8)*255
        keep=cv2.bitwise_and(keep,hair_mask)
        a=(keep.astype(np.float32)/255.0)[...,None]
        clean=np.clip(clean.astype(np.float32)*(1-a)+coloured.astype(np.float32)*a,0,255).astype(np.uint8)
    return clean

for skin_name,skin_rgb in SKINS.items():
    skinned=tint(base,skin_mask,skin_rgb,.76)
    for hair_name,hair_rgb in HAIRS.items():
        for style in STYLES:
            out=compose_style(skinned,hair_rgb,style)
            path=OUT/skin_name/hair_name/f'{style}.webp'
            path.parent.mkdir(parents=True,exist_ok=True)
            if not cv2.imwrite(str(path),out,[cv2.IMWRITE_WEBP_QUALITY,94]):
                raise SystemExit(f'Failed writing {path}')

files=list(OUT.rglob('*.webp'))
if len(files)!=125: raise SystemExit(f'Expected 125 female presets, got {len(files)}')
print('Generated 125 full-image female creator presets')
