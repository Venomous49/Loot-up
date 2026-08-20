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
  if abs(im.size[0]-SIZE[0])<=1 and abs(im.size[1]-SIZE[1])<=1:
   canvas=Image.new(mode,SIZE,0 if mode=='L' else (0,0,0,0)); canvas.paste(im.crop((0,0,min(im.width,SIZE[0]),min(im.height,SIZE[1]))),(0,0)); im=canvas
  else: raise SystemExit(f'BAD SIZE {path}: {im.size}')
 return im

def clean_components(im):
 arr=np.asarray(im,dtype=np.uint8).copy(); a=arr[...,3]; bw=(a>20).astype(np.uint8)
 n,labels,stats,_=cv2.connectedComponentsWithStats(bw,8)
 if n<=1: raise SystemExit('NO SUBJECT')
 areas=stats[1:,cv2.CC_STAT_AREA]; biggest=1+int(np.argmax(areas)); main=stats[biggest]
 mx,my,mw,mh,ma=map(int,main)
 keep=labels==biggest
 for i in range(1,n):
  if i==biggest: continue
  x,y,w,h,area=map(int,stats[i]); near=(x < mx+mw+18 and x+w > mx-18 and y < my+mh+18 and y+h > my-18); meaningful=area>max(90,int(ma*.0015))
  if near and meaningful: keep |= labels==i
 arr[~keep]=0; ys,xs=np.where(keep)
 return Image.fromarray(arr,'RGBA'),(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1))

def build_clean_male(bg):
 raw=Image.open(ROOT/'01-debutant-character.png').convert('RGBA'); subject,box=clean_components(raw); subject=subject.crop(box)
 max_w,max_h=500,790; scale=min(max_w/subject.width,max_h/subject.height); nw,nh=max(1,int(subject.width*scale)),max(1,int(subject.height*scale)); subject=subject.resize((nw,nh),Image.Resampling.LANCZOS)
 left=(SIZE[0]-nw)//2; top=max(25,SIZE[1]-nh-35); layer=Image.new('RGBA',SIZE,(0,0,0,0)); layer.alpha_composite(subject,(left,top)); out=bg.copy(); out.alpha_composite(layer); return out,layer

def build_base(gender):
 bg=exact(SRC/'background.webp','RGBA')
 if gender=='male': out,person=build_clean_male(bg)
 else: person=exact(SRC/f'{gender}_base.png','RGBA'); out=bg.copy(); out.alpha_composite(person)
 d=OUT/gender; d.mkdir(parents=True,exist_ok=True); out.convert('RGB').save(d/'base.webp','WEBP',quality=100,method=6); return out.convert('RGB'),person

def body_box(person):
 a=np.asarray(person.getchannel('A')); ys,xs=np.where(a>24)
 if len(xs)<1000: raise SystemExit('PERSON ALPHA TOO SMALL')
 return int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)

def face_box(person):
 x0,y0,x1,y1=body_box(person); w=x1-x0; h=y1-y0; fw=max(72,int(w*.34)); fh=max(85,int(h*.18)); fx=int((x0+x1-fw)/2); fy=y0+int(h*.015); return fx,fy,fw,fh

def skin_layer(gender,base):
 if gender=='male':
  for name in SKINS: Image.new('RGBA',SIZE,(0,0,0,0)).save(OUT/gender/f'skin-{name}.webp','WEBP',lossless=True,method=6)
  return
 mask=exact(SRC/f'{gender}_skin_mask.png','L'); soft=np.asarray(mask.filter(ImageFilter.GaussianBlur(.65)),dtype=np.float32)/255.; rgb=np.asarray(base,dtype=np.uint8); lab=cv2.cvtColor(rgb,cv2.COLOR_RGB2LAB).astype(np.float32)
 for name,target in SKINS.items():
  tlab=cv2.cvtColor(np.array(target,dtype=np.uint8).reshape(1,1,3),cv2.COLOR_RGB2LAB)[0,0].astype(np.float32); toned=lab.copy(); toned[...,0]=np.clip(lab[...,0]*.88+tlab[0]*.12,0,255); toned[...,1]=np.clip(lab[...,1]*.20+tlab[1]*.80,0,255); toned[...,2]=np.clip(lab[...,2]*.20+tlab[2]*.80,0,255)
  trgb=cv2.cvtColor(toned.astype(np.uint8),cv2.COLOR_LAB2RGB); rgba=np.zeros((SIZE[1],SIZE[0],4),dtype=np.uint8); rgba[...,:3]=trgb; rgba[...,3]=np.clip(soft*255,0,255).astype(np.uint8); Image.fromarray(rgba,'RGBA').save(OUT/gender/f'skin-{name}.webp','WEBP',lossless=True,method=6)

def isolate_hair(im):
 arr=np.asarray(im,dtype=np.uint8).copy(); a=arr[...,3]; bw=(a>24).astype(np.uint8); n,labels,stats,_=cv2.connectedComponentsWithStats(bw,8)
 if n<=1: raise SystemExit('EMPTY HAIR')
 candidates=[]
 for i in range(1,n):
  x,y,w,h,area=map(int,stats[i])
  if 100<=area and w<=420 and h<=320: candidates.append((area,i))
 if candidates:
  i=max(candidates)[1]; keep=labels==i; arr[~keep]=0; ys,xs=np.where(keep); return Image.fromarray(arr,'RGBA').crop((int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)))
 # Fallback for presets whose alpha also contains hood/body: keep only the upper region of the dominant blob,
 # then pick the dominant component from that upper region. This prevents old contaminated presets from blocking the build.
 biggest=1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA])); x,y,w,h,area=map(int,stats[biggest]); upper_h=max(40,int(h*.34)); roi=np.zeros_like(bw); roi[y:min(y+upper_h,bw.shape[0]),x:min(x+w,bw.shape[1])]=bw[y:min(y+upper_h,bw.shape[0]),x:min(x+w,bw.shape[1])]
 n2,l2,s2,_=cv2.connectedComponentsWithStats(roi,8)
 if n2<=1: raise SystemExit('NO HAIR IN UPPER SOURCE REGION')
 valid=[(int(s2[i,cv2.CC_STAT_AREA]),i) for i in range(1,n2) if int(s2[i,cv2.CC_STAT_AREA])>=60]
 if not valid: raise SystemExit('NO USABLE HAIR COMPONENT')
 i=max(valid)[1]; keep=l2==i; out=arr.copy(); out[~keep]=0; ys,xs=np.where(keep); return Image.fromarray(out,'RGBA').crop((int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)))

def register_hair(im,person):
 crop=isolate_hair(im); fx,fy,fw,fh=face_box(person); target_w=int(fw*1.15); target_h=int(fh*.72); scale=min(target_w/crop.width,target_h/crop.height); nw,nh=max(1,int(crop.width*scale)),max(1,int(crop.height*scale)); crop=crop.resize((nw,nh),Image.Resampling.LANCZOS); tx=int(fx+fw/2-nw/2); ty=int(fy-nh*.42); canvas=Image.new('RGBA',SIZE,(0,0,0,0)); canvas.alpha_composite(crop,(max(0,min(SIZE[0]-nw,tx)),max(0,min(SIZE[1]-nh,ty)))); return canvas

def hair_layers(gender,person):
 for style in STYLES[gender]:
  for color in COLORS:
   out=register_hair(exact(HAIR/f'{style}_{color}.png','RGBA'),person); out.save(OUT/gender/f'hair-{style}-{color}.webp','WEBP',lossless=True,method=6)

def validate_outputs():
 for g in ('male','female'):
  files=list((OUT/g).glob('*.webp'))
  if len(files)!=31: raise SystemExit(f'{g}: expected 31 assets, got {len(files)}')
  for p in files:
   if Image.open(p).size!=SIZE: raise SystemExit(f'OUTPUT SIZE DRIFT {p}')

def main():
 for g in ('male','female'):
  base,person=build_base(g); skin_layer(g,base); hair_layers(g,person)
 validate_outputs(); print('Creator rebuilt from clean subject: centered full body, detached debris removed, skull-anchored hair')

if __name__=='__main__': main()
