from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageFilter

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'assets/creator_sources/fullbody'
HAIR=SRC/'hair'
OUT=ROOT/'assets/creator_layers'
SIZE=(1728,910)
SKINS={
 'light':(224,181,153),
 'warm':(198,139,101),
 'medium':(158,105,76),
 'deep':(105,69,50),
 'dark':(62,43,34),
}
STYLES={
 'male':['male_textured','male_short','male_medium','male_undercut','male_slick'],
 'female':['female_long','female_wavy','female_bob','female_ponytail','female_short'],
}
COLORS=['black','brown','blond','red','purple']

def exact(path,mode='RGBA'):
 im=Image.open(path).convert(mode)
 if im.size!=SIZE: raise SystemExit(f'BAD SIZE {path}: {im.size}, expected {SIZE}')
 return im

def build_base(gender):
 bg=exact(SRC/'background.webp','RGBA')
 person=exact(SRC/f'{gender}_base.png','RGBA')
 a=np.asarray(person.getchannel('A'))
 if np.count_nonzero(a>12)<10000: raise SystemExit(f'{gender} base alpha invalid')
 out=bg.copy(); out.alpha_composite(person)
 d=OUT/gender; d.mkdir(parents=True,exist_ok=True)
 out.convert('RGB').save(d/'base.webp','WEBP',quality=100,method=6)
 return out.convert('RGB')

def skin_layer(gender,base):
 mask=exact(SRC/f'{gender}_skin_mask.png','L')
 m=np.asarray(mask,dtype=np.float32)/255.0
 # Never permit hard mask edges; preserve pores/shadows by transferring chroma in LAB.
 soft=np.asarray(mask.filter(ImageFilter.GaussianBlur(.65)),dtype=np.float32)/255.0
 rgb=np.asarray(base,dtype=np.uint8)
 lab=cv2.cvtColor(rgb,cv2.COLOR_RGB2LAB).astype(np.float32)
 inside=m>.22
 if inside.sum()<1000: raise SystemExit(f'{gender} skin mask too small')
 for name,target in SKINS.items():
  t=np.array(target,dtype=np.uint8).reshape(1,1,3)
  tlab=cv2.cvtColor(t,cv2.COLOR_RGB2LAB)[0,0].astype(np.float32)
  toned=lab.copy()
  # Keep original luminance/texture; change chroma strongly and luminance gently.
  toned[...,0]=np.clip(lab[...,0]*.82+tlab[0]*.18,0,255)
  toned[...,1]=np.clip(lab[...,1]*.18+tlab[1]*.82,0,255)
  toned[...,2]=np.clip(lab[...,2]*.18+tlab[2]*.82,0,255)
  trgb=cv2.cvtColor(toned.astype(np.uint8),cv2.COLOR_LAB2RGB)
  rgba=np.zeros((SIZE[1],SIZE[0],4),dtype=np.uint8)
  rgba[...,:3]=trgb
  rgba[...,3]=np.clip(soft*255,0,255).astype(np.uint8)
  Image.fromarray(rgba,'RGBA').save(OUT/gender/f'skin-{name}.webp','WEBP',lossless=True,method=6)

def hair_layers(gender):
 for style in STYLES[gender]:
  for color in COLORS:
   p=HAIR/f'{style}_{color}.png'
   im=exact(p,'RGBA')
   a=np.asarray(im.getchannel('A'),dtype=np.uint8)
   if np.count_nonzero(a>16)<250: raise SystemExit(f'EMPTY HAIR {p}')
   # Keep antialiased/semitransparent strands; remove only invisible RGB fringe.
   arr=np.asarray(im,dtype=np.uint8).copy()
   arr[a==0,:3]=0
   ys,xs=np.where(a>16)
   if ys.max()>int(SIZE[1]*.88): raise SystemExit(f'HAIR SPILLS TOO LOW {p}: y={ys.max()}')
   Image.fromarray(arr,'RGBA').save(OUT/gender/f'hair-{style}-{color}.webp','WEBP',lossless=True,method=6)

def main():
 for g in ('male','female'):
  base=build_base(g)
  skin_layer(g,base)
  hair_layers(g)
 for g in ('male','female'):
  files=list((OUT/g).glob('*.webp'))
  if len(files)!=31: raise SystemExit(f'{g}: expected 31 layered assets, got {len(files)}')
 print('Layered creator built: 2 immutable bases + 10 skin overlays + 50 transparent HD hair layers')

if __name__=='__main__': main()
