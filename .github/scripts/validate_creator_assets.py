from pathlib import Path
import cv2, numpy as np, sys

ROOT=Path('.')
FULL=ROOT/'assets'/'creator_sources'/'fullbody'
HAIR=FULL/'hair'
errors=[]
WANT=(910,1728)  # h,w


def read_rgba(p):
    im=cv2.imread(str(p),cv2.IMREAD_UNCHANGED)
    if im is None:
        errors.append(f'missing {p}')
        return None
    if im.ndim!=3 or im.shape[2]!=4:
        errors.append(f'not RGBA {p}: {im.shape}')
        return None
    if im.shape[:2]!=WANT:
        errors.append(f'wrong size {p}: {im.shape[:2]} expected {WANT}')
    return im


def bbox(alpha,thr=8):
    ys,xs=np.where(alpha>thr)
    if len(xs)==0:return None
    return xs.min(),ys.min(),xs.max()+1,ys.max()+1

for gender in ('male','female'):
    p=FULL/f'{gender}_base.png'
    im=read_rgba(p)
    if im is None: continue
    a=im[:,:,3]
    b=bbox(a)
    if not b:
        errors.append(f'empty alpha {p}'); continue
    x0,y0,x1,y1=b; h,w=a.shape
    margins=(x0/w,y0/h,(w-x1)/w,(h-y1)/h)
    if min(margins)<.018:
        errors.append(f'{gender} base touches edge, margins={margins}')
    body_h=(y1-y0)/h
    if not (.68<=body_h<=.92):
        errors.append(f'{gender} body height ratio out of range: {body_h:.3f}')
    fg=(a>18).astype(np.uint8)
    n,labels,stats,_=cv2.connectedComponentsWithStats(fg,8)
    areas=sorted([stats[i,cv2.CC_STAT_AREA] for i in range(1,n)],reverse=True)
    if areas and len(areas)>1 and sum(areas[1:])>areas[0]*.025:
        errors.append(f'{gender} base contains detached foreground/junk: main={areas[0]} junk={sum(areas[1:])}')

    mp=FULL/f'{gender}_skin_mask.png'
    m=cv2.imread(str(mp),cv2.IMREAD_GRAYSCALE)
    if m is None:
        errors.append(f'missing {mp}')
    else:
        if m.shape!=a.shape: errors.append(f'wrong skin mask size {gender}: {m.shape}')
        outside=np.count_nonzero((m>8)&(a<8))
        total=max(1,np.count_nonzero(m>8))
        if outside/total>.005: errors.append(f'{gender} skin mask spills outside body: {outside/total:.3%}')
        if total<500: errors.append(f'{gender} skin mask nearly empty: {total}')

styles={
 'male':['male_textured','male_short','male_medium','male_undercut','male_slick'],
 'female':['female_long','female_wavy','female_bob','female_ponytail','female_short']
}
colors=['black','brown','blond','red','purple']
for gender,ss in styles.items():
    for style in ss:
        for color in colors:
            p=HAIR/f'{style}_{color}.png'
            im=read_rgba(p)
            if im is None: continue
            a=im[:,:,3]; h,w=a.shape
            b=bbox(a)
            if not b:
                errors.append(f'empty hair {p}'); continue
            x0,y0,x1,y1=b
            if y0>h*.38: errors.append(f'hair starts too low {p}: {y0/h:.3f}')
            max_bottom=.72 if gender=='female' and style in ('female_long','female_wavy','female_ponytail') else .48
            if y1>h*max_bottom: errors.append(f'hair extends too low {p}: {y1/h:.3f}')
            cx=(x0+x1)/2/w
            if not .35<=cx<=.68: errors.append(f'hair horizontally misaligned {p}: cx={cx:.3f}')
            face=a[int(h*.105):int(h*.285),int(w*.455):int(w*.595)]
            coverage=np.count_nonzero(face>18)/max(1,face.size)
            if coverage>.34: errors.append(f'hair covers face {p}: {coverage:.1%}')
            if x0<4 or x1>w-4 or y0<4: errors.append(f'hair touches canvas edge {p}')

status=ROOT/'creator-asset-validation.txt'
if errors:
    status.write_text('status=failed\n'+'\n'.join(errors)+'\n',encoding='utf-8')
    print('\n'.join(errors))
    sys.exit(1)
status.write_text('status=success\nchecks=fullbody,hair,skin,alpha,margins,face-clearance\nassets=52\nvalidator=v2\n',encoding='utf-8')
print('Creator assets validated successfully')
