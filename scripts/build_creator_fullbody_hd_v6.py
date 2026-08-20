from pathlib import Path
import sys
import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_creator_fullbody_hd as legacy

# The creator must start from a source that already contains the complete level-1
# male from head to feet.  Never use the close-up hairstyle master as body base.
MALE_FULL_BODY = ROOT / "assets/characters/male/medium/brown/male_textured/01-debutant.webp"


def base_center_x(gender, width):
    return int(round(width * (.50 if gender == "male" else .52)))


def full_scene(path):
    """Preserve every source pixel; no crop, segmentation or body repaste."""
    im = Image.open(path).convert("RGB")
    if im.size == legacy.CANVAS_SIZE:
        return im
    # contain() guarantees head AND feet survive if a future source has a different ratio.
    fitted = im.copy()
    fitted.thumbnail(legacy.CANVAS_SIZE, Image.Resampling.LANCZOS)
    canvas = legacy.BACKGROUND.copy()
    x = (legacy.CANVAS_SIZE[0] - fitted.width) // 2
    y = legacy.CANVAS_SIZE[1] - fitted.height
    canvas.paste(fitted, (x, y))
    return canvas


def immutable_canonical_body(gender):
    if gender == "male":
        scene = full_scene(MALE_FULL_BODY)
    else:
        path, _ = legacy.CANONICAL[gender]
        scene = legacy.fit_scene(path)

    rgb = np.asarray(scene, dtype=np.uint8)
    h, w = rgb.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    cx = base_center_x(gender, w)

    # Only exposed face/neck may receive complexion changes. Clothes/body geometry
    # are outside this anatomical gate and therefore remain byte-identical.
    if gender == "male":
        face_cy, neck_cy = int(h * .19), int(h * .265)
        face_rx, face_ry, neck_rx, neck_ry = 58, 66, 39, 34
    else:
        face_cy, neck_cy = int(h * .235), int(h * .315)
        face_rx, face_ry, neck_rx, neck_ry = 70, 86, 46, 40
    anatomical = ((((xx-cx)/face_rx)**2 + ((yy-face_cy)/face_ry)**2) <= 1) | ((((xx-cx)/neck_rx)**2 + ((yy-neck_cy)/neck_ry)**2) <= 1)
    ycrcb = cv2.cvtColor(rgb, cv2.COLOR_RGB2YCrCb)
    lum, cr, cb = cv2.split(ycrcb)
    skinlike = (cr >= 126) & (cr <= 184) & (cb >= 72) & (cb <= 142) & (lum >= 28)
    mask = (skinlike & anatomical).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3,3), np.uint8))
    mask = cv2.GaussianBlur(mask, (0,0), .5)
    return scene, mask.astype(np.float32)/255.0


def hair_envelope(gender, style, h, w):
    yy, xx = np.mgrid[0:h, 0:w]
    xn, yn = xx/float(w), yy/float(h)
    if gender == "male":
        cx = .50
        rx, ry, cy = {
            "male_textured": (.060,.070,.125),
            "male_short": (.055,.060,.132),
            "male_medium": (.068,.083,.122),
            "male_undercut": (.060,.068,.128),
            "male_slick": (.061,.064,.128),
        }[style]
        env = 1.0 - np.clip(((xn-cx)/rx)**2 + ((yn-cy)/ry)**2,0,1)
        face = (((xn-cx)/.040)**2 + ((yn-.19)/.052)**2) <= 1
        env[face] = 0
        return env.astype(np.float32)
    cx=.52
    top=1.0-np.clip(((xn-cx)/.110)**2+((yn-.165)/.120)**2,0,1)
    return top.astype(np.float32)


def scalp_only_hair(gender, style):
    source = legacy.fit_scene(legacy.STYLE_SOURCES[gender][style])
    raw = legacy.fallback_hair_mask(source, gender, style)
    h,w = raw.shape
    shaped = np.clip(raw * hair_envelope(gender, style, h, w),0,1)
    mask = (shaped >= .42).astype(np.uint8)*255
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3,3),np.uint8))
    n, labels, stats, _ = cv2.connectedComponentsWithStats((mask>0).astype(np.uint8),8)
    if n <= 1:
        raise SystemExit(f"No clean hairstyle component: {gender}/{style}")
    candidates=[(stats[i,cv2.CC_STAT_AREA],i) for i in range(1,n) if stats[i,cv2.CC_STAT_AREA] >= 40]
    if not candidates:
        raise SystemExit(f"No clean hairstyle pixels: {gender}/{style}")
    keep=np.zeros_like(mask)
    for _,i in sorted(candidates,reverse=True)[:2]: keep[labels==i]=255
    mask=cv2.GaussianBlur(keep,(0,0),.22)
    ys,xs=np.where(mask>60)
    if not len(xs): raise SystemExit(f"Empty hairstyle: {gender}/{style}")
    x0,x1,y0,y1=int(xs.min()),int(xs.max())+1,int(ys.min()),int(ys.max())+1
    rgb=np.asarray(source,dtype=np.uint8)[y0:y1,x0:x1]
    a=mask[y0:y1,x0:x1]
    max_w,max_h,_=legacy.HAIR_ENVELOPES[style]
    # Hair is deliberately smaller than old masters: it must sit on the skull,
    # never become a cloud around the face.
    if gender == "male": max_w,max_h=int(max_w*.72),int(max_h*.72)
    scale=min(max_w/max(1,rgb.shape[1]),max_h/max(1,rgb.shape[0]))
    ow,oh=max(1,round(rgb.shape[1]*scale)),max(1,round(rgb.shape[0]*scale))
    rgb=cv2.resize(rgb,(ow,oh),interpolation=cv2.INTER_LANCZOS4)
    a=cv2.resize(a,(ow,oh),interpolation=cv2.INTER_LINEAR)
    cx=base_center_x(gender,legacy.CANVAS_SIZE[0])
    x=round(cx-ow/2)
    y=78 if gender=="male" else legacy.HAIR_ENVELOPES[style][2]
    rgb_out=np.zeros((legacy.CANVAS_SIZE[1],legacy.CANVAS_SIZE[0],3),dtype=np.float32)
    alpha=np.zeros((legacy.CANVAS_SIZE[1],legacy.CANVAS_SIZE[0]),dtype=np.float32)
    x2,y2=min(legacy.CANVAS_SIZE[0],x+ow),min(legacy.CANVAS_SIZE[1],y+oh)
    cw,ch=x2-x,y2-y
    rgb_out[y:y2,x:x2]=rgb[:ch,:cw].astype(np.float32)
    alpha[y:y2,x:x2]=a[:ch,:cw].astype(np.float32)/255.0
    alpha[int(legacy.CANVAS_SIZE[1]*.28):,:]=0
    alpha[alpha<.18]=0
    return rgb_out,np.clip(alpha,0,1)


legacy.canonical_body = immutable_canonical_body
legacy.align_style_hair = scalp_only_hair
legacy.build()
