from pathlib import Path
import cv2
import numpy as np

ROOT=Path('.')
OUT=ROOT/'assets'/'creator_sources'/'fullbody'
OUT.mkdir(parents=True,exist_ok=True)
H,W=910,1728
BG=cv2.imread(str(ROOT/'assets'/'creator_sources'/'creator_background_master.png'),cv2.IMREAD_COLOR)
if BG is None: raise SystemExit('creator_background_master.png missing')
BG=cv2.resize(BG,(W,H),interpolation=cv2.INTER_LANCZOS4)

def alpha_bbox(a):
    ys,xs=np.where(a>18)
    return None if len(xs)==0 else (xs.min(),ys.min(),xs.max()+1,ys.max()+1)

def keep_largest(mask):
    n,lab,stats,cent=cv2.connectedComponentsWithStats(mask.astype(np.uint8),8)
    if n<=1:return mask
    cand=[]
    for i in range(1,n):
        area=stats[i,cv2.CC_STAT_AREA]; cx,cy=cent[i]
        if area>mask.size*.01 and .18*mask.shape[1]<cx<.82*mask.shape[1] and .02*mask.shape[0]<cy<.99*mask.shape[0]: cand.append((area,i))
    if not cand:return mask
    keep=max(cand)[1]
    return (lab==keep).astype(np.uint8)

def segment_person(path):
    img=cv2.imread(str(path),cv2.IMREAD_COLOR)
    if img is None: raise SystemExit(f'missing {path}')
    h,w=img.shape[:2]
    m=np.full((h,w),cv2.GC_BGD,np.uint8)
    m[int(h*.025):int(h*.97),int(w*.20):int(w*.80)]=cv2.GC_PR_FGD
    cv2.ellipse(m,(int(w*.50),int(h*.17)),(int(w*.105),int(h*.125)),0,0,360,cv2.GC_FGD,-1)
    cv2.rectangle(m,(int(w*.34),int(h*.24)),(int(w*.66),int(h*.60)),cv2.GC_FGD,-1)
    cv2.rectangle(m,(int(w*.32),int(h*.34)),(int(w*.43),int(h*.70)),cv2.GC_PR_FGD,-1)
    cv2.rectangle(m,(int(w*.57),int(h*.34)),(int(w*.69),int(h*.70)),cv2.GC_PR_FGD,-1)
    cv2.rectangle(m,(int(w*.37),int(h*.56)),(int(w*.51),int(h*.96)),cv2.GC_FGD,-1)
    cv2.rectangle(m,(int(w*.49),int(h*.56)),(int(w*.64),int(h*.96)),cv2.GC_FGD,-1)
    m[:int(h*.20),:int(w*.38)]=cv2.GC_BGD
    m[int(h*.91):,:int(w*.33)]=cv2.GC_BGD
    m[int(h*.91):,int(w*.69):]=cv2.GC_BGD
    bg=np.zeros((1,65),np.float64); fg=np.zeros((1,65),np.float64)
    cv2.grabCut(img,m,None,bg,fg,12,cv2.GC_INIT_WITH_MASK)
    mask=np.where((m==cv2.GC_FGD)|(m==cv2.GC_PR_FGD),1,0).astype(np.uint8)
    mask=keep_largest(mask)
    mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8),iterations=2)
    mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,np.ones((3,3),np.uint8),iterations=1)
    a=cv2.GaussianBlur((mask*255).astype(np.uint8),(5,5),0)
    out=cv2.cvtColor(img,cv2.COLOR_BGR2BGRA); out[:,:,3]=a
    return out

def fit_rgba(rgba,target_h=.84,xcenter=.5):
    b=alpha_bbox(rgba[:,:,3]); canvas=np.zeros((H,W,4),np.uint8)
    if not b:return canvas
    x0,y0,x1,y1=b; crop=rgba[y0:y1,x0:x1]; ch,cw=crop.shape[:2]
    s=min((H*target_h)/max(ch,1),(W*.46)/max(cw,1))
    nw,nh=max(1,int(cw*s)),max(1,int(ch*s))
    crop=cv2.resize(crop,(nw,nh),interpolation=cv2.INTER_LANCZOS4)
    x=int(W*xcenter-nw/2); y=H-nh-int(H*.065)
    x=max(0,min(W-nw,x)); y=max(0,min(H-nh,y))
    canvas[y:y+nh,x:x+nw]=crop
    return canvas

def build_skin_mask(rgba):
    bgr=rgba[:,:,:3]; alpha=rgba[:,:,3]
    ycc=cv2.cvtColor(bgr,cv2.COLOR_BGR2YCrCb); _,cr,cb=cv2.split(ycc)
    skin=((cr>132)&(cr<180)&(cb>72)&(cb<138)&(alpha>25)).astype(np.uint8)*255
    zone=np.zeros_like(skin)
    zone[int(H*.08):int(H*.34),int(W*.36):int(W*.69)]=255
    zone[int(H*.31):int(H*.69),int(W*.24):int(W*.44)]=255
    zone[int(H*.31):int(H*.69),int(W*.59):int(W*.77)]=255
    skin=cv2.bitwise_and(skin,zone)
    skin=cv2.morphologyEx(skin,cv2.MORPH_OPEN,np.ones((3,3),np.uint8),iterations=1)
    skin=cv2.morphologyEx(skin,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8),iterations=1)
    skin=cv2.GaussianBlur(skin,(7,7),0)
    skin[alpha<16]=0
    return skin

male=fit_rgba(segment_person(ROOT/'01-debutant.webp'),.84,.54)
female=fit_rgba(segment_person(ROOT/'assets'/'creator'/'female'/'medium'/'brown'/'female_bob.webp'),.84,.52)
for g,img in [('male',male),('female',female)]:
    cv2.imwrite(str(OUT/f'{g}_base.png'),img)
    cv2.imwrite(str(OUT/f'{g}_skin_mask.png'),build_skin_mask(img))
cv2.imwrite(str(OUT/'background.webp'),BG,[cv2.IMWRITE_WEBP_QUALITY,94])
print('Built fixed 1728x910 canonical full-body bases and skin masks v15')
