from pathlib import Path
import cv2
import numpy as np

ROOT=Path('.')
FULL=ROOT/'assets'/'creator_sources'/'fullbody'

for gender in ('male','female'):
    path=FULL/f'{gender}_base.png'
    img=cv2.imread(str(path),cv2.IMREAD_UNCHANGED)
    if img is None or img.shape[2] != 4:
        raise SystemExit(f'missing {path}')
    bgr=img[:,:,:3]
    alpha=img[:,:,3]
    h,w=bgr.shape[:2]

    ycrcb=cv2.cvtColor(bgr,cv2.COLOR_BGR2YCrCb)
    # Broad human-skin chroma window, then restrict to plausible exposed-skin zones.
    skin=cv2.inRange(ycrcb,np.array([0,130,75],np.uint8),np.array([255,185,145],np.uint8))
    skin=cv2.bitwise_and(skin,alpha)

    region=np.zeros((h,w),np.uint8)
    # face/head
    cv2.ellipse(region,(int(w*.52),int(h*.17)),(int(w*.075),int(h*.095)),0,0,360,255,-1)
    # neck
    cv2.rectangle(region,(int(w*.485),int(h*.225)),(int(w*.555),int(h*.295)),255,-1)
    # hands/forearms: generous but still localized; intersected with detected skin chroma
    cv2.ellipse(region,(int(w*.405),int(h*.50)),(int(w*.045),int(h*.09)),0,0,360,255,-1)
    cv2.ellipse(region,(int(w*.625),int(h*.50)),(int(w*.045),int(h*.09)),0,0,360,255,-1)

    mask=cv2.bitwise_and(skin,region)
    mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8),iterations=2)
    mask=cv2.GaussianBlur(mask,(9,9),0)
    cv2.imwrite(str(FULL/f'{gender}_skin_mask.png'),mask)
    print('built',gender)

# trigger: skin-mask-v1
