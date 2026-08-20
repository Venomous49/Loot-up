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

def largest_alpha_component(im,threshold=16):
 arr=np.asarray(im,dtype=np.uint8).copy(); a=arr[...,3]
 bw=(a>threshold).astype(np.uint8)
 n,labels,stats,cent=cv2.connectedComponentsWithStats(bw,8)
 if n<=1: raise SystemExit('NO ALPHA COMPONENT')
 idx=1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA]))
 keep=labels==idx
 arr[~keep]=0
 ys,xs=np.where(keep)
 return Image.fromarray(arr,'RGBA'), (int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1))

def male_anchor_box():
 # The old full-canvas source has the correct body location even though it contains visual contamination.
 # Use only the largest alpha component geometry as the anchor; never render its pixels.
 old=exact(SRC/'male_base.png','RGBA')
 _,box=largest_alpha_component(old)
 x0,y0,x1,y1=box
 w=x1-x0; h=y1-y0
 # Add safety room so hands/feet are never clipped and keep the body visually centered.
 pad_x=max(18,int(w*.06)); pad_y=max(14,int(h*.025))
 return (max(0,x0-pad_x), max(0,y0-pad_y), min(SIZE[0],x1+pad_x), min(SIZE[1],y1+pad_y))

def build_clean_male(bg):
 # Use only the isolated main subject from the dedicated character PNG.
 raw=Image.open(ROOT/'01-debutant-character.png').convert('RGBA')
 subject,box=largest_alpha_component(raw)
 x0,y0,x1,y1=box
 subject=subject.crop(box)
 ax0,ay0,ax1,ay1=male_anchor_box(); aw=ax1-ax0; ah=ay1-ay0
 # Fit inside the trusted full-body anchor with margin; no floating tiny character and no edge clipping.
 fit_w=int(aw*.90); fit_h=int(ah*.94)
 scale=min(fit_w/subject.width,fit_h/subject.height)
 nw=max(1,int(subject.width*scale)); nh=max(1,int(subject.height*scale))
 subject=subject.resize((nw,nh),Image.Resampling.LANCZOS)
 # Center horizontally and vertically in the original full-body position, then keep feet slightly above frame edge.
 left=int((ax0+ax1)/2-nw/2)
 top=int((ay0+ay1)/2-nh/2)
 left=max(0,min(SIZE[0]-nw,left)); top=max(0,min(SIZE[1]-nh,top))
 layer=Image.new('RGBA',SIZE,(0,0,0,0)); layer.alpha_composite(subject,(left,top))
 out=bg.copy(); out.alpha_composite(layer)
 return out, layer

def build_base(gender):
 bg=exact(SRC/'background.webp','RGBA')
 if gender=='male':
  out,person_layer=build_clean_male(bg)
 else:
  person_layer=exact(SRC/f'{gender}_base.png','RGBA')
  a=np.asarray(person_layer.getchannel('A'))
  if np.count_nonzero(a>12)<10000: raise SystemExit(f'{gender} base alpha invalid')
  out=bg.copy(); out.alpha_composite(person_layer)
 d=OUT/gender; d.mkdir(parents=True,exist_ok=True)
 out.convert('RGB').save(d/'base.webp','WEBP',quality=100,method=6)
 return out.convert('RGB'),person_layer

def face_box_from_person(person_layer):
 arr=np.asarray(person_layer,dtype=np.uint8); a=arr[...,3]
 ys,xs=np.where(a>24)
 if len(xs)<1000: raise SystemExit('PERSON ALPHA TOO SMALL')
 x0,x1,y0,y1=int(xs.min()),int(xs.max()),int(ys.min()),int(ys.max())
 w=x1-x0+1; h=y1-y0+1
 # Stable anatomical head box derived from body bounds, independent of old contaminated skin masks.
 fw=max(60,int(w*.36)); fh=max(70,int(h*.19))
 fx=int((x0+x1)/2-fw/2); fy=int(y0+h*.015)
 return fx,fy,fw,fh

def skin_layer(gender,base):
 mask=exact(SRC/f'{gender}_skin_mask.png','L')
 m=np.asarray(mask,dtype=np.float32)/255.0
 soft=np.asarray(mask.filter(ImageFilter.GaussianBlur(.65)),dtype=np.float32)/255.0
 rgb=np.asarray(base,dtype=np.uint8); lab=cv2.cvtColor(rgb,cv2.COLOR_RGB2LAB).astype(np.float32)
 if (m>.22).sum()<1000: raise SystemExit(f'{gender} skin mask too small')
 for name,target in SKINS.items():
  tlab=cv2.cvtColor(np.array(target,dtype=np.uint8).reshape(1,1,3),cv2.COLOR_RGB2LAB)[0,0].astype(np.float32); toned=lab.copy()
  toned[...,0]=np.clip(lab[...,0]*.88+tlab[0]*.12,0,255)
  toned[...,1]=np.clip(lab[...,1]*.20+tlab[1]*.80,0,255)
  toned[...,2]=np.clip(lab[...,2]*.20+tlab[2]*.80,0,255)
  trgb=cv2.cvtColor(toned.astype(np.uint8),cv2.COLOR_LAB2RGB)
  rgba=np.zeros((SIZE[1],SIZE[0],4),dtype=np.uint8); rgba[...,:3]=trgb; rgba[...,3]=np.clip(soft*255,0,255).astype(np.uint8)
  Image.fromarray(rgba,'RGBA').save(OUT/gender/f'skin-{name}.webp','WEBP',lossless=True,method=6)

def register_hair(im,person_layer):
 arr=np.asarray(im,dtype=np.uint8).copy(); a=arr[...,3]
 if np.count_nonzero(a>16)<120: raise SystemExit('EMPTY HAIR SOURCE')
 fx,fy,fw,fh=face_box_from_person(person_layer); cx=fx+fw/2
 # Keep only pixels in a strict head-sized window: removes hood, text and detached artifacts.
 x0=max(0,int(cx-fw*.95)); x1=min(SIZE[0],int(cx+fw*.95))
 y0=max(0,int(fy-fh*.65)); y1=min(SIZE[1],int(fy+fh*.95))
 keep=np.zeros_like(a,dtype=bool); keep[y0:y1,x0:x1]=True
 arr[~keep]=0; a=arr[...,3]
 ys,xs=np.where(a>16)
 if len(xs)<80:
  # Source coordinates may not match the rebuilt body; isolate its largest hair-like component globally, then re-anchor.
  raw=Image.fromarray(np.asarray(im,dtype=np.uint8),'RGBA')
  comp,box=largest_alpha_component(raw)
  crop=comp.crop(box)
 else:
  bx0,bx1,by0,by1=int(xs.min()),int(xs.max()+1),int(ys.min()),int(ys.max()+1)
  crop=Image.fromarray(arr[by0:by1,bx0:bx1],'RGBA')
 # Force natural head proportions without allowing miniature floating hair.
 target_w=max(78,int(fw*1.18)); target_h=max(55,int(fh*.72))
 scale=min(target_w/crop.width,target_h/crop.height)
 nw=max(1,int(crop.width*scale)); nh=max(1,int(crop.height*scale))
 crop=crop.resize((nw,nh),Image.Resampling.LANCZOS)
 tx=int(cx-nw/2); ty=int(fy-nh*.28)
 tx=max(0,min(SIZE[0]-nw,tx)); ty=max(0,min(SIZE[1]-nh,ty))
 canvas=Image.new('RGBA',SIZE,(0,0,0,0)); canvas.alpha_composite(crop,(tx,ty))
 return canvas

def hair_layers(gender,person_layer):
 for style in STYLES[gender]:
  for color in COLORS:
   p=HAIR/f'{style}_{color}.png'; im=exact(p,'RGBA')
   out=register_hair(im,person_layer)
   out.save(OUT/gender/f'hair-{style}-{color}.webp','WEBP',lossless=True,method=6)

def validate_outputs():
 for g in ('male','female'):
  d=OUT/g; files=list(d.glob('*.webp'))
  if len(files)!=31: raise SystemExit(f'{g}: expected 31 layered assets, got {len(files)}')
  for p in files:
   if Image.open(p).size!=SIZE: raise SystemExit(f'OUTPUT SIZE DRIFT {p}')

def main():
 for g in ('male','female'):
  base,person_layer=build_base(g); skin_layer(g,base); hair_layers(g,person_layer)
 validate_outputs()
 print('Layered creator validated: isolated full body, centered anchor, no plaque/text debris, head-sized hair')

if __name__=='__main__': main()
