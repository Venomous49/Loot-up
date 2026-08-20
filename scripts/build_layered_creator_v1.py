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

def build_clean_male(bg):
 # Use the dedicated transparent character-only source: no black level plaque,
 # no rectangular background patch, and no hard-cut canvas around the body.
 src=Image.open(ROOT/'01-debutant-character.png').convert('RGBA')
 fx,fy,fw,fh=face_box('male')
 sm=np.asarray(exact(SRC/'male_skin_mask.png','L'),dtype=np.uint8)
 ys,xs=np.where(sm>60)
 skin_bottom=int(ys.max()) if len(ys) else int(SIZE[1]*.86)
 target_h=int(np.clip((skin_bottom-fy)*1.18, SIZE[1]*.62, SIZE[1]*.80))
 target_w=max(1,int(src.width*target_h/src.height))
 src=src.resize((target_w,target_h),Image.Resampling.LANCZOS)
 # Keep the head aligned with the existing face/skin/hair coordinate system while
 # centering the full body naturally in the preview.
 cx=fx+fw/2
 left=int(cx-target_w/2)
 top=int(fy-target_h*.075)
 left=max(0,min(SIZE[0]-target_w,left)); top=max(0,min(SIZE[1]-target_h,top))
 layer=Image.new('RGBA',SIZE,(0,0,0,0)); layer.alpha_composite(src,(left,top))
 out=bg.copy(); out.alpha_composite(layer)
 return out

def build_base(gender):
 bg=exact(SRC/'background.webp','RGBA')
 if gender=='male':
  out=build_clean_male(bg)
 else:
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

def register_hair(im,gender):
 arr=np.asarray(im,dtype=np.uint8).copy(); a=arr[...,3]
 if np.count_nonzero(a>16)<180: raise SystemExit('EMPTY HAIR SOURCE')
 fx,fy,fw,fh=face_box(gender); cx=fx+fw/2
 # Hard safety ROI around the head only. This removes hood/shoulder/background fragments.
 x0=max(0,int(cx-fw*1.35)); x1=min(SIZE[0],int(cx+fw*1.35))
 y0=max(0,int(fy-fh*1.20)); y1=min(SIZE[1],int(fy+fh*1.25))
 keep=np.zeros_like(a,dtype=bool); keep[y0:y1,x0:x1]=True
 arr[~keep]=0; a=arr[...,3]
 ys,xs=np.where(a>16)
 if len(xs)<120: raise SystemExit('HAIR ROI REMOVED TOO MUCH')
 # Keep components close to the face and discard detached floating debris.
 bw=(a>16).astype(np.uint8); n,labels,stats,cent=cv2.connectedComponentsWithStats(bw,8)
 target=np.array([cx, fy+fh*.05])
 chosen=[]
 for i in range(1,n):
  x,y,w,h,area=stats[i]
  if area<35: continue
  dist=np.linalg.norm(cent[i]-target)
  if dist < max(fw,fh)*1.35: chosen.append(i)
 if chosen:
  km=np.isin(labels,chosen); arr[~km]=0
 a=arr[...,3]; ys,xs=np.where(a>16)
 if len(xs)<120: raise SystemExit('HAIR COMPONENT CLEANUP REMOVED TOO MUCH')
 # Apply only a bounded registration correction; never arbitrary full-canvas scaling.
 bx0,bx1,by0,by1=int(xs.min()),int(xs.max()+1),int(ys.min()),int(ys.max()+1)
 crop=Image.fromarray(arr[by0:by1,bx0:bx1],'RGBA')
 max_w=max(40,int(fw*2.0)); max_h=max(35,int(fh*1.35))
 scale=min(1.0,max_w/crop.width,max_h/crop.height)
 if crop.width>max_w or crop.height>max_h:
  scale=min(max_w/crop.width,max_h/crop.height)
  crop=crop.resize((max(1,int(crop.width*scale)),max(1,int(crop.height*scale))),Image.Resampling.LANCZOS)
 tx=int(cx-crop.width/2)
 desired_bottom=int(fy+fh*.22)
 ty=int(desired_bottom-crop.height)
 tx=max(0,min(SIZE[0]-crop.width,tx)); ty=max(0,min(SIZE[1]-crop.height,ty))
 canvas=Image.new('RGBA',SIZE,(0,0,0,0)); canvas.alpha_composite(crop,(tx,ty))
 return canvas

def hair_layers(gender):
 for style in STYLES[gender]:
  for color in COLORS:
   p=HAIR/f'{style}_{color}.png'; im=exact(p,'RGBA')
   out=register_hair(im,gender)
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
 print('Layered creator validated: clean centered male base, no plaque/cutout, face-registered hair')

if __name__=='__main__': main()
