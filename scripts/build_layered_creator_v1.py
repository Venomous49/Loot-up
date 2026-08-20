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

def exact(path,mode='RGBA'):
 im=Image.open(path).convert(mode)
 if im.size != SIZE:
  dw=im.size[0]-SIZE[0]; dh=im.size[1]-SIZE[1]
  if abs(dw)<=1 and abs(dh)<=1:
   if im.size[0]>=SIZE[0] and im.size[1]>=SIZE[1]: im=im.crop((0,0,SIZE[0],SIZE[1]))
   else:
    fill=0 if mode=='L' else (0,0,0,0); canvas=Image.new(mode,SIZE,fill); canvas.paste(im,(0,0)); im=canvas
  else: raise SystemExit(f'BAD SIZE {path}: {im.size}, expected {SIZE}')
 return im

def build_base(gender):
 bg=exact(SRC/'background.webp','RGBA'); person=exact(SRC/f'{gender}_base.png','RGBA')
 a=np.asarray(person.getchannel('A'))
 if np.count_nonzero(a>12)<10000: raise SystemExit(f'{gender} base alpha invalid')
 out=bg.copy(); out.alpha_composite(person); d=OUT/gender; d.mkdir(parents=True,exist_ok=True)
 out.convert('RGB').save(d/'base.webp','WEBP',quality=100,method=6); return out.convert('RGB')

def skin_layer(gender,base):
 mask=exact(SRC/f'{gender}_skin_mask.png','L'); m=np.asarray(mask,dtype=np.float32)/255.0
 soft=np.asarray(mask.filter(ImageFilter.GaussianBlur(.65)),dtype=np.float32)/255.0
 rgb=np.asarray(base,dtype=np.uint8); lab=cv2.cvtColor(rgb,cv2.COLOR_RGB2LAB).astype(np.float32)
 if (m>.22).sum()<1000: raise SystemExit(f'{gender} skin mask too small')
 for name,target in SKINS.items():
  tlab=cv2.cvtColor(np.array(target,dtype=np.uint8).reshape(1,1,3),cv2.COLOR_RGB2LAB)[0,0].astype(np.float32); toned=lab.copy()
  toned[...,0]=np.clip(lab[...,0]*.88+tlab[0]*.12,0,255); toned[...,1]=np.clip(lab[...,1]*.20+tlab[1]*.80,0,255); toned[...,2]=np.clip(lab[...,2]*.20+tlab[2]*.80,0,255)
  trgb=cv2.cvtColor(toned.astype(np.uint8),cv2.COLOR_LAB2RGB); rgba=np.zeros((SIZE[1],SIZE[0],4),dtype=np.uint8); rgba[...,:3]=trgb; rgba[...,3]=np.clip(soft*255,0,255).astype(np.uint8)
  Image.fromarray(rgba,'RGBA').save(OUT/gender/f'skin-{name}.webp','WEBP',lossless=True,method=6)

def hair_layers(gender):
 # Hair PNGs are already full-canvas registration layers. Never scale/reposition them in runtime.
 # Reject source masks that include hood/shoulders/body instead of silently publishing bad overlays.
 person=np.asarray(exact(SRC/f'{gender}_base.png','RGBA').getchannel('A'),dtype=np.uint8)
 pys,pxs=np.where(person>12); person_top=int(pys.min()); person_left=int(pxs.min()); person_right=int(pxs.max())
 for style in STYLES[gender]:
  for color in COLORS:
   p=HAIR/f'{style}_{color}.png'; im=exact(p,'RGBA'); a=np.asarray(im.getchannel('A'),dtype=np.uint8)
   ys,xs=np.where(a>16)
   if len(xs)<250: raise SystemExit(f'EMPTY HAIR {p}')
   w=int(xs.max()-xs.min()+1); h=int(ys.max()-ys.min()+1); cx=float(xs.min()+xs.max())/2
   person_w=max(1,person_right-person_left+1); pcx=float(person_left+person_right)/2
   # Hair must stay in a compact head region. This catches the visible pink hood/shoulder spill.
   if ys.min() < max(0,person_top-45): raise SystemExit(f'HAIR TOO HIGH {p}: y={ys.min()}')
   if ys.max() > person_top+220: raise SystemExit(f'HAIR MASK INCLUDES HOOD/BODY {p}: y={ys.max()}')
   if h>230 or w>240: raise SystemExit(f'HAIR MASK OVERSIZED {p}: {w}x{h}')
   if abs(cx-pcx)>105: raise SystemExit(f'HAIR MASK OFF-CENTER {p}: hair_cx={cx:.1f}, person_cx={pcx:.1f}')
   arr=np.asarray(im,dtype=np.uint8).copy(); arr[a==0,:3]=0
   Image.fromarray(arr,'RGBA').save(OUT/gender/f'hair-{style}-{color}.webp','WEBP',lossless=True,method=6)

def validate_outputs():
 for g in ('male','female'):
  d=OUT/g; files=list(d.glob('*.webp'))
  if len(files)!=31: raise SystemExit(f'{g}: expected 31 layered assets, got {len(files)}')
  for p in files:
   if Image.open(p).size!=SIZE: raise SystemExit(f'OUTPUT SIZE DRIFT {p}')

def main():
 for g in ('male','female'):
  base=build_base(g); skin_layer(g,base); hair_layers(g)
 validate_outputs(); print('Layered creator validated: compact registered hair masks, immutable base and skin overlays')

if __name__=='__main__': main()
