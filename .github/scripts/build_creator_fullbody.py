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
    ys, xs = np.where(alpha > 12)
    if len(xs) == 0:
        return None
    return xs.min(), ys.min(), xs.max()+1, ys.max()+1


def fit_rgba(rgba, target_h_ratio=.90, x_center=.50):
    a = rgba[:, :, 3]
    bb = alpha_bbox(a)
    if not bb:
        return rgba
    x0,y0,x1,y1 = bb
    crop = rgba[y0:y1, x0:x1]
    ch, cw = crop.shape[:2]
    target_h = int(H * target_h_ratio)
    scale = min(target_h / max(ch,1), (W*.62) / max(cw,1))
    nw, nh = max(1,int(cw*scale)), max(1,int(ch*scale))
    crop = cv2.resize(crop, (nw,nh), interpolation=cv2.INTER_LANCZOS4)
    canvas = np.zeros((H,W,4), np.uint8)
    x = int(W*x_center - nw/2)
    y = H - nh - int(H*.035)
    x = max(0,min(W-nw,x)); y=max(0,min(H-nh,y))
    canvas[y:y+nh, x:x+nw] = crop
    return canvas


def segment_person(path):
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f'missing {path}')
    h,w = img.shape[:2]
    mask = np.full((h,w), cv2.GC_PR_BGD, np.uint8)
    mask[:int(h*.02),:] = cv2.GC_BGD
    mask[int(h*.98):,:] = cv2.GC_BGD
    mask[:,:int(w*.10)] = cv2.GC_BGD
    mask[:,int(w*.90):] = cv2.GC_BGD
    mask[int(h*.04):int(h*.96), int(w*.20):int(w*.80)] = cv2.GC_PR_FGD
    cv2.ellipse(mask,(int(w*.50),int(h*.18)),(int(w*.11),int(h*.13)),0,0,360,cv2.GC_FGD,-1)
    cv2.rectangle(mask,(int(w*.36),int(h*.25)),(int(w*.64),int(h*.63)),cv2.GC_FGD,-1)
    cv2.rectangle(mask,(int(w*.39),int(h*.58)),(int(w*.61),int(h*.94)),cv2.GC_FGD,-1)
    bgd=np.zeros((1,65),np.float64); fgd=np.zeros((1,65),np.float64)
    cv2.grabCut(img,mask,None,bgd,fgd,8,cv2.GC_INIT_WITH_MASK)
    fg=np.where((mask==cv2.GC_FGD)|(mask==cv2.GC_PR_FGD),1,0).astype(np.uint8)
    num, labels, stats, cent = cv2.connectedComponentsWithStats(fg,8)
    keep=np.zeros_like(fg)
    comps=[]
    for i in range(1,num):
        area=stats[i,cv2.CC_STAT_AREA]
        cx,cy=cent[i]
        if area>h*w*.001 and w*.15<cx<w*.85 and h*.02<cy<h*.98:
            comps.append((area,i))
    for _,i in sorted(comps,reverse=True)[:4]:
        keep[labels==i]=1
    k=np.ones((5,5),np.uint8)
    keep=cv2.morphologyEx(keep,cv2.MORPH_CLOSE,k,iterations=2)
    alpha=cv2.GaussianBlur((keep*255).astype(np.uint8),(5,5),0)
    rgba=cv2.cvtColor(img,cv2.COLOR_BGR2BGRA)
    rgba[:,:,3]=alpha
    return rgba

# Canonical male: validated full-body beginner cutout.
male = cv2.imread(str(ROOT / '01-debutant-character.png'), cv2.IMREAD_UNCHANGED)
if male is None or male.shape[2] != 4:
    raise SystemExit('01-debutant-character.png missing')
male = fit_rgba(male, .90, .54)
cv2.imwrite(str(OUT/'male_base.png'), male)

# Canonical female: one body/pose reused by every hairstyle and color.
female_src = ROOT / 'assets' / 'creator' / 'female' / 'medium' / 'brown' / 'female_bob.webp'
female = segment_person(female_src)
female = fit_rgba(female, .90, .52)
cv2.imwrite(str(OUT/'female_base.png'), female)

# One shared background for both sexes and every haircut.
cv2.imwrite(str(OUT/'background.webp'), BG, [cv2.IMWRITE_WEBP_QUALITY, 94])
print('Built canonical full-body male/female bases and shared background v12')
