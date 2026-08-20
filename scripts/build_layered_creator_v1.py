from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageFilter

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'assets/creator_sources/fullbody'
HAIR=SRC/'hair'
OUT=ROOT/'assets/creator_layers'
SIZE=(1728,910)
SKINS={'light':(224,181,153),'warm':(198,139,101),'medium':(158,105,76),'deep':(105,69,50),'dark':(62,43,34)}
STYLES={'male':['male_textured','male_short','male_medium','male_undercut','male_slick'],'female':['female_long','female_wavy','female_bob','female_ponytail','female_short']}
COLORS=['black','brown','blond','red','purple']
SPECIAL_FIX={'male_undercut','male_slick'}

def exact(path,mode='RGBA'):
 im=Image.open(path).convert(mode)
 if im.size != SIZE:
  dw=im.size[0]-SIZE[0]; dh=im.size[1]-SIZE[1]
  if abs(dw)<=1 and abs(dh)<=1:
   if im.size[0]>=SIZE[0] and im.size[1]>=SIZE[1]: im=im.crop((0,0,SIZE[0],SIZE[1]))
   else:
    fill=0 if mode=='L' else (0,0,0,0)
    canvas=Image.new(mode,SIZE,fill); canvas.paste(im,(0,0)); im=canvas
  else: raise SystemExit(f'BAD SIZE {path}: {im.size}, expected {SIZE}')
 return im

def build_base(gender):
 bg=exact(SRC/'background.webp','RGBA'); person=exact(SRC/f'{gender}_base.png','RGBA')
 a=np.asarray(person.getchannel('A'))
 if np.count_nonzero(a>12)<10000: raise SystemExit(f'{gender} base alpha invalid')
 out=bg.copy(); out.alpha_composite(person)
 d=OUT/gender; d.mkdir(parents=True,exist_ok=True)
 out.convert('RGB').save(d/'base.webp','WEBP',quality=100,method=6)
 return out.convert('RGB')

def skin_layer(gender,base):
 mask=exact(SRC/f'{gender}_skin_mask.png','L')
 m=np.asarray(mask,dtype=np.float32)/255.0
 soft=np.asarray(mask.filter(ImageFilter.GaussianBlur(.65)),dtype=np.float32)/255.0
 rgb=np.asarray(base,dtype=np.uint8); lab=cv2.cvtColor(rgb,cv2.COLOR_RGB2LAB).astype(np.float32)
 if (m>.22).sum()<1000: raise SystemExit(f'{gender} skin mask too small')
 for name,target in SKINS.items():
  tlab=cv2.cvtColor(np.array(target,dtype=np.uint8).reshape(1,1,3),cv2.COLOR_RGB2LAB)[0,0].astype(np.float32)
  toned=lab.copy()
  toned[...,0]=np.clip(lab[...,0]*.88+tlab[0]*.12,0,255)
  toned[...,1]=np.clip(lab[...,1]*.20+tlab[1]*.80,0,255)
  toned[...,2]=np.clip(lab[...,2]*.20+tlab[2]*.80,0,255)
  trgb=cv2.cvtColor(toned.astype(np.uint8),cv2.COLOR_LAB2RGB)
  rgba=np.zeros((SIZE[1],SIZE[0],4),dtype=np.uint8); rgba[...,:3]=trgb; rgba[...,3]=np.clip(soft*255,0,255).astype(np.uint8)
  Image.fromarray(rgba,'RGBA').save(OUT/gender/f'skin-{name}.webp','WEBP',lossless=True,method=6)

def face_box(gender):
 mask=np.asarray(exact(SRC/f'{gender}_skin_mask.png','L'),dtype=np.uint8)
 bw=(mask>80).astype(np.uint8)
 n,labels,stats,cent=cv2.connectedComponentsWithStats(bw,8)
 candidates=[]
 for i in range(1,n):
  x,y,w,h,area=stats[i]
  if area>=120: candidates.append((y,-area,x,y,w,h))
 if not candidates: raise SystemExit(f'{gender}: cannot detect face anchor')
 _,_,x,y,w,h=sorted(candidates)[0]
 return x,y,w,h

def clean_broken_male_style(im,gender):
 arr=np.asarray(im,dtype=np.uint8); a=arr[...,3]
 ys,xs=np.where(a>16)
 if len(xs)<250: raise SystemExit('EMPTY HAIR SOURCE')
 crop=Image.fromarray(arr[int(ys.min()):int(ys.max()+1),int(xs.min()):int(xs.max()+1)],'RGBA')
 # Broken source files contain a large lower hood/shoulder region. Keep only the upper hair mass.
 ca=np.asarray(crop.getchannel('A')); cys,cxs=np.where(ca>16)
 keep_h=max(20,int(crop.height*0.42))
 carr=np.asarray(crop,dtype=np.uint8).copy(); carr[keep_h:,:,:]=0
 crop=Image.fromarray(carr,'RGBA')
 aa=np.asarray(crop.getchannel('A')); ys2,xs2=np.where(aa>16)
 if len(xs2)<150: raise SystemExit('HAIR CLEANUP REMOVED TOO MUCH')
 crop=crop.crop((int(xs2.min()),int(ys2.min()),int(xs2.max()+1),int(ys2.max()+1)))
 fx,fy,fw,fh=face_box(gender)
 target_w=max(70,int(fw*1.18)); target_h=max(45,int(fh*.72))
 scale=min(target_w/crop.width,target_h/crop.height)
 nw=max(1,int(crop.width*scale)); nh=max(1,int(crop.height*scale))
 crop=crop.resize((nw,nh),Image.Resampling.LANCZOS)
 tx=int(fx+fw/2-nw/2); ty=int(fy-nh*.45)
 tx=max(0,min(SIZE[0]-nw,tx)); ty=max(0,min(SIZE[1]-nh,ty))
 canvas=Image.new('RGBA',SIZE,(0,0,0,0)); canvas.alpha_composite(crop,(tx,ty))
 return canvas

def hair_layers(gender):
 for style in STYLES[gender]:
  for color in COLORS:
   p=HAIR/f'{style}_{color}.png'; im=exact(p,'RGBA')
   # Preserve every previously-good hairstyle pixel-for-pixel.
   if gender=='male' and style in SPECIAL_FIX:
    out=clean_broken_male_style(im,gender)
   else:
    arr=np.asarray(im,dtype=np.uint8).copy(); a=arr[...,3]
    if np.count_nonzero(a>16)<250: raise SystemExit(f'EMPTY HAIR {p}')
    arr[a==0,:3]=0
    out=Image.fromarray(arr,'RGBA')
   out.save(OUT/gender/f'hair-{style}-{color}.webp','WEBP',lossless=True,method=6)

def validate_outputs():
 for g in ('male','female'):
  d=OUT/g; files=list(d.glob('*.webp'))
  if len(files)!=31: raise SystemExit(f'{g}: expected 31 layered assets, got {len(files)}')
  for p in files:
   if Image.open(p).size!=SIZE: raise SystemExit(f'OUTPUT SIZE DRIFT {p}')

def main():
 for g in ('male','female'):
  base=build_base(g); skin_layer(g,base); hair_layers(g)
 validate_outputs()
 print('Layered creator validated: stable hairstyles restored; cleanup isolated to male undercut/slick')

if __name__=='__main__': main()
