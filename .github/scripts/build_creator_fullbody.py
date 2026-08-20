from pathlib import Path
import cv2
import numpy as np

ROOT = Path('.')
OUT = ROOT / 'assets' / 'creator_sources' / 'fullbody'
OUT.mkdir(parents=True, exist_ok=True)

BG = cv2.imread(str(ROOT / 'assets' / 'creator_sources' / 'creator_background_master.png'), cv2.IMREAD_COLOR)
if BG is None:
    raise SystemExit('creator_background_master.png missing')
H, W = BG.shape[:2]


def alpha_bbox(alpha):
    ys, xs = np.where(alpha > 18)
    if len(xs) == 0:
        return None
    return xs.min(), ys.min(), xs.max()+1, ys.max()+1


def keep_largest(mask, center_x=.5):
    n, labels, stats, cent = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    candidates=[]
    for i in range(1,n):
        area=stats[i,cv2.CC_STAT_AREA]
        cx,cy=cent[i]
        if area>mask.size*.01 and .20*mask.shape[1] < cx < .80*mask.shape[1] and .03*mask.shape[0] < cy < .98*mask.shape[0]:
            candidates.append((area,-abs(cx-mask.shape[1]*center_x),i))
    if not candidates:
        return mask
    keep=max(candidates)[2]
    return (labels==keep).astype(np.uint8)


def segment_person(path, gender):
    img=cv2.imread(str(path),cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f'missing {path}')
    h,w=img.shape[:2]
    mask=np.full((h,w),cv2.GC_BGD,np.uint8)
    x0,x1=int(w*.22),int(w*.78)
    y0,y1=int(h*.03),int(h*.965)
    mask[y0:y1,x0:x1]=cv2.GC_PR_FGD
    cv2.ellipse(mask,(int(w*.50),int(h*.17)),(int(w*.10),int(h*.115)),0,0,360,cv2.GC_FGD,-1)
    cv2.rectangle(mask,(int(w*.36),int(h*.24)),(int(w*.64),int(h*.58)),cv2.GC_FGD,-1)
    cv2.rectangle(mask,(int(w*.34),int(h*.34)),(int(w*.42),int(h*.68)),cv2.GC_PR_FGD,-1)
    cv2.rectangle(mask,(int(w*.58),int(h*.34)),(int(w*.68),int(h*.68)),cv2.GC_PR_FGD,-1)
    cv2.rectangle(mask,(int(w*.38),int(h*.55)),(int(w*.50),int(h*.95)),cv2.GC_FGD,-1)
    cv2.rectangle(mask,(int(w*.50),int(h*.55)),(int(w*.62),int(h*.95)),cv2.GC_FGD,-1)
    mask[:int(h*.20),:int(w*.40)] = cv2.GC_BGD
    mask[int(h*.91):,:int(w*.36)] = cv2.GC_BGD
    mask[int(h*.91):,int(w*.67):] = cv2.GC_BGD
    bgd=np.zeros((1,65),np.float64); fgd=np.zeros((1,65),np.float64)
    cv2.grabCut(img,mask,None,bgd,fgd,12,cv2.GC_INIT_WITH_MASK)
    fg=np.where((mask==cv2.GC_FGD)|(mask==cv2.GC_PR_FGD),1,0).astype(np.uint8)
    fg=keep_largest(fg)
    fg=cv2.morphologyEx(fg,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8),iterations=2)
    fg=cv2.morphologyEx(fg,cv2.MORPH_OPEN,np.ones((3,3),np.uint8),iterations=1)
    alpha=cv2.GaussianBlur((fg*255).astype(np.uint8),(5,5),0)
    rgba=cv2.cvtColor(img,cv2.COLOR_BGR2BGRA)
    rgba[:,:,3]=alpha
    return rgba


def fit_rgba(rgba, target_h_ratio=.86, x_center=.50):
    bb=alpha_bbox(rgba[:,:,3])
    if not bb:
        return rgba
    x0,y0,x1,y1=bb
    crop=rgba[y0:y1,x0:x1]
    ch,cw=crop.shape[:2]
    target_h=int(H*target_h_ratio)
    target_w=int(W*.48)
    scale=min(target_h/max(ch,1),target_w/max(cw,1))
    nw,nh=max(1,int(cw*scale)),max(1,int(ch*scale))
    crop=cv2.resize(crop,(nw,nh),interpolation=cv2.INTER_LANCZOS4)
    canvas=np.zeros((H,W,4),np.uint8)
    x=int(W*x_center-nw/2)
    y=H-nh-int(H*.055)
    x=max(0,min(W-nw,x)); y=max(0,min(H-nh,y))
    canvas[y:y+nh,x:x+nw]=crop
    return canvas


def build_skin_mask(rgba):
    bgr=rgba[:,:,:3]
    alpha=rgba[:,:,3]
    ycrcb=cv2.cvtColor(bgr,cv2.COLOR_BGR2YCrCb)
    _,cr,cb=cv2.split(ycrcb)
    skin=((cr>132)&(cr<180)&(cb>72)&(cb<138)&(alpha>25)).astype(np.uint8)*255
    # Restrict to plausible exposed-skin zones so clothing/background can never be recoloured.
    zone=np.zeros_like(skin)
    zone[int(H*.08):int(H*.34), int(W*.37):int(W*.68)] = 255
    zone[int(H*.31):int(H*.67), int(W*.25):int(W*.43)] = 255
    zone[int(H*.31):int(H*.67), int(W*.60):int(W*.76)] = 255
    skin=cv2.bitwise_and(skin,zone)
    skin=cv2.morphologyEx(skin,cv2.MORPH_OPEN,np.ones((3,3),np.uint8),iterations=1)
    skin=cv2.morphologyEx(skin,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8),iterations=2)
    skin=cv2.GaussianBlur(skin,(7,7),0)
    return skin

male=segment_person(ROOT/'01-debutant.webp','male')
male=fit_rgba(male,.86,.54)
cv2.imwrite(str(OUT/'male_base.png'),male)
cv2.imwrite(str(OUT/'male_skin_mask.png'),build_skin_mask(male))

female_src=ROOT/'assets'/'creator'/'female'/'medium'/'brown'/'female_bob.webp'
female=segment_person(female_src,'female')
female=fit_rgba(female,.86,.52)
cv2.imwrite(str(OUT/'female_base.png'),female)
cv2.imwrite(str(OUT/'female_skin_mask.png'),build_skin_mask(female))

cv2.imwrite(str(OUT/'background.webp'),BG,[cv2.IMWRITE_WEBP_QUALITY,94])
print('Built canonical full-body bases + swappable skin masks v14')
