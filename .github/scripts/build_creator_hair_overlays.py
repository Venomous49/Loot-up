from pathlib import Path
import cv2, numpy as np

ROOT=Path('.')
SRC=ROOT/'assets'/'creator_sources'
OUT=SRC/'fullbody'/'hair'
OUT.mkdir(parents=True,exist_ok=True)
H,W=910,1728
MODEL=str(SRC/'face_detection_yunet_2023mar.onnx')
styles={'male':['male_textured','male_short','male_medium','male_undercut','male_slick'],'female':['female_long','female_wavy','female_bob','female_ponytail','female_short']}
colors=['black','brown','blond','red','purple']
tints={'brown':(72,112,150),'blond':(165,205,235),'red':(55,90,190),'purple':(150,70,185)}

def detect_face(img):
    h,w=img.shape[:2]
    try:
        det=cv2.FaceDetectorYN.create(MODEL,'',(w,h),score_threshold=.60,nms_threshold=.3,top_k=20)
        _,faces=det.detect(img)
        if faces is not None and len(faces):
            f=min(faces,key=lambda r:abs((r[0]+r[2]/2)-w*.5)+abs((r[1]+r[3]/2)-h*.2))
            return tuple(map(float,f[:4]))
    except Exception: pass
    return (w*.42,h*.075,w*.16,h*.19)

def source_for(style,color):
    if color!='black':
        p=SRC/f'{style}_{color}_natural.png'
        if p.exists(): return p,False
    return SRC/'standardized_black'/f'{style}.webp', color!='black'

def mask_for(style,color):
    p=SRC/'person_masks'/f'{style}.png'
    if p.exists(): return p
    p=SRC/'color_master_masks'/f'{style}_{color}_natural.png'
    return p

def tint(img,color):
    if color=='black': return img
    target=np.array(tints[color],np.float32)
    gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY).astype(np.float32)/255.0
    shade=(.35+.65*gray)[:,:,None]
    return np.clip(target*shade,0,255).astype(np.uint8)

def warp_to_canonical(rgba,face,gender):
    fx,fy,fw,fh=face
    src_c=np.array([fx+fw/2,fy+fh/2],np.float32)
    target_c=np.array([W*(.54 if gender=='male' else .52),H*.205],np.float32)
    target_fw=W*(.075 if gender=='male' else .072)
    s=target_fw/max(fw,1.0)
    M=np.array([[s,0,target_c[0]-s*src_c[0]],[0,s,target_c[1]-s*src_c[1]]],np.float32)
    return cv2.warpAffine(rgba,M,(W,H),flags=cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))

for gender,ss in styles.items():
    for style in ss:
        for color in colors:
            sp,needs_tint=source_for(style,color); mp=mask_for(style,color)
            img=cv2.imread(str(sp),cv2.IMREAD_COLOR)
            pm=cv2.imread(str(mp),cv2.IMREAD_GRAYSCALE)
            if img is None or pm is None:
                raise SystemExit(f'missing source/mask for {style} {color}: {sp} / {mp}')
            h,w=img.shape[:2]
            if pm.shape[:2]!=(h,w): pm=cv2.resize(pm,(w,h),interpolation=cv2.INTER_NEAREST)
            pm=(pm>55).astype(np.uint8)*255
            fx,fy,fw,fh=detect_face(img); cx,cy=fx+fw/2,fy+fh/2
            region=np.zeros((h,w),np.uint8)
            top=max(0,int(fy-1.15*fh)); bottom=min(h,int(fy+(1.85 if gender=='female' else .95)*fh))
            left=max(0,int(fx-1.05*fw)); right=min(w,int(fx+2.05*fw))
            region[top:bottom,left:right]=255
            hair=cv2.bitwise_and(pm,region)
            # Remove the actual face and neck at source level.
            hole=np.zeros((h,w),np.uint8)
            cv2.ellipse(hole,(int(cx),int(fy+.58*fh)),(int(.62*fw),int(.78*fh)),0,0,360,255,-1)
            cv2.rectangle(hole,(int(cx-.28*fw),int(fy+.88*fh)),(int(cx+.28*fw),int(fy+1.42*fh)),255,-1)
            hair[hole>0]=0
            if gender=='male': hair[int(fy+1.08*fh):,:]=0
            else:
                ycut=int(fy+1.08*fh)
                if ycut<h:
                    xx=np.indices((h-ycut,w))[1]; central=(xx>int(cx-.40*fw))&(xx<int(cx+.40*fw))
                    sub=hair[ycut:,:]; sub[central]=0; hair[ycut:,:]=sub
            hair=cv2.morphologyEx(hair,cv2.MORPH_OPEN,np.ones((3,3),np.uint8),iterations=1)
            hair=cv2.GaussianBlur(hair,(5,5),0)
            rgb=tint(img,color) if needs_tint else img
            rgba=cv2.cvtColor(rgb,cv2.COLOR_BGR2BGRA); rgba[:,:,3]=hair
            out=warp_to_canonical(rgba,(fx,fy,fw,fh),gender)
            # Final fixed face clearance in canonical coordinates: eyes/nose/mouth can never be covered.
            a=out[:,:,3]
            fc=(int(W*(.54 if gender=='male' else .52)),int(H*.215))
            final_hole=np.zeros((H,W),np.uint8)
            cv2.ellipse(final_hole,fc,(int(W*.052),int(H*.078)),0,0,360,255,-1)
            a[final_hole>0]=0
            a=cv2.GaussianBlur(a,(3,3),0); out[:,:,3]=a
            cv2.imwrite(str(OUT/f'{style}_{color}.png'),out)
            print('built',style,color)
print('Built all 50 fixed-head hairstyle overlays v15')
