from pathlib import Path
import cv2
import numpy as np

ROOT=Path('.')
SRC=ROOT/'assets'/'creator_sources'
OUT=SRC/'fullbody'/'hair'
OUT.mkdir(parents=True,exist_ok=True)
BG=cv2.imread(str(SRC/'creator_background_master.png'),cv2.IMREAD_COLOR)
if BG is None: raise SystemExit('missing creator background')
H,W=BG.shape[:2]
MODEL=str(SRC/'face_detection_yunet_2023mar.onnx')

styles={
 'male':['male_textured','male_short','male_medium','male_undercut','male_slick'],
 'female':['female_long','female_wavy','female_bob','female_ponytail','female_short']
}
colors=['black','brown','blond','red','purple']


def detect_face(img):
    h,w=img.shape[:2]
    try:
        det=cv2.FaceDetectorYN.create(MODEL,'',(w,h),score_threshold=.65,nms_threshold=.3,top_k=50)
        _,faces=det.detect(img)
        if faces is not None and len(faces):
            f=min(faces,key=lambda r:abs((r[0]+r[2]/2)-w/2)+abs((r[1]+r[3]/2)-h*.2))
            return tuple(map(float,f[:4]))
    except Exception:
        pass
    return (w*.42,h*.075,w*.16,h*.19)


def fit_layer(rgba, person_mask, target_h=.86, x_center=.52):
    ys,xs=np.where(person_mask>20)
    if not len(xs): return np.zeros((H,W,4),np.uint8)
    x0,y0,x1,y1=xs.min(),ys.min(),xs.max()+1,ys.max()+1
    ch,cw=y1-y0,x1-x0
    scale=min((H*target_h)/max(ch,1),(W*.48)/max(cw,1))
    nw,nh=max(1,int(cw*scale)),max(1,int(ch*scale))
    full=cv2.resize(rgba,(max(1,int(rgba.shape[1]*scale)),max(1,int(rgba.shape[0]*scale))),interpolation=cv2.INTER_LANCZOS4)
    fx0=int(x0*scale); fy0=int(y0*scale)
    ox=int(W*x_center-nw/2)-fx0
    oy=H-nh-int(H*.055)-fy0
    canvas=np.zeros((H,W,4),np.uint8)
    xA=max(0,ox); yA=max(0,oy); xB=min(W,ox+full.shape[1]); yB=min(H,oy+full.shape[0])
    if xB>xA and yB>yA:
        sx=xA-ox; sy=yA-oy
        canvas[yA:yB,xA:xB]=full[sy:sy+(yB-yA),sx:sx+(xB-xA)]
    return canvas


def source_for(style,color):
    if color=='black': return SRC/'standardized_black'/f'{style}.webp'
    return SRC/f'{style}_{color}_natural.png'


def mask_for(style,color):
    p=SRC/'person_masks'/f'{style}.png'
    if p.exists(): return p
    return SRC/'color_master_masks'/f'{style}_{color}_natural.png'

for gender,ss in styles.items():
    for style in ss:
        for color in colors:
            sp=source_for(style,color); mp=mask_for(style,color)
            img=cv2.imread(str(sp),cv2.IMREAD_COLOR)
            pm=cv2.imread(str(mp),cv2.IMREAD_GRAYSCALE)
            if img is None or pm is None:
                print('skip',style,color,'missing source/mask'); continue
            h,w=img.shape[:2]
            if pm.shape[:2]!=(h,w): pm=cv2.resize(pm,(w,h),interpolation=cv2.INTER_NEAREST)
            pm=(pm>60).astype(np.uint8)*255
            fx,fy,fw,fh=detect_face(img)
            cx=fx+fw/2; cy=fy+fh/2

            region=np.zeros((h,w),np.uint8)
            top=max(0,int(fy-1.05*fh)); bottom=min(h,int(fy+1.65*fh if gender=='female' else fy+0.78*fh))
            left=max(0,int(fx-.95*fw)); right=min(w,int(fx+1.95*fw))
            region[top:bottom,left:right]=255
            hair=cv2.bitwise_and(pm,region)

            face_hole=np.zeros((h,w),np.uint8)
            cv2.ellipse(face_hole,(int(cx),int(cy+.08*fh)),(int(.56*fw),int(.67*fh)),0,0,360,255,-1)
            cv2.rectangle(face_hole,(int(cx-.25*fw),int(fy+.75*fh)),(int(cx+.25*fw),int(fy+1.35*fh)),255,-1)
            hair[face_hole>0]=0

            if gender=='male':
                hair[int(fy+1.02*fh):,:]=0
            else:
                ycut=int(fy+1.0*fh)
                if ycut<h:
                    xx=np.indices((h-ycut,w))[1]
                    central=(xx>int(cx-.42*fw))&(xx<int(cx+.42*fw))
                    sub=hair[ycut:,:]; sub[central]=0; hair[ycut:,:]=sub

            hair=cv2.morphologyEx(hair,cv2.MORPH_OPEN,np.ones((3,3),np.uint8),iterations=1)
            hair=cv2.GaussianBlur(hair,(5,5),0)
            rgba=cv2.cvtColor(img,cv2.COLOR_BGR2BGRA); rgba[:,:,3]=hair
            out=fit_layer(rgba,pm,.86,.52 if gender=='female' else .54)
            cv2.imwrite(str(OUT/f'{style}_{color}.png'),out)
            print('built',style,color)

print('clean hairstyle overlays build complete v13')
