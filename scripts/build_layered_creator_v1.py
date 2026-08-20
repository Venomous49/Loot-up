from pathlib import Path
import cv2
import numpy as np
from PIL import Image

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
   fill=0 if mode=='L' else (0,0,0,0); canvas=Image.new(mode,SIZE,fill); crop=im.crop((0,0,min(im.width,SIZE[0]),min(im.height,SIZE[1]))); canvas.paste(crop,(0,0)); im=canvas
  else: raise SystemExit(f'BAD SIZE {path}: {im.size}')
 return im

def clean_subject(im):
 arr=np.asarray(im,dtype=np.uint8).copy(); bw=(arr[...,3]>18).astype(np.uint8)
 n,labels,stats,_=cv2.connectedComponentsWithStats(bw,8)
 if n<=1: raise SystemExit('NO SUBJECT')
 biggest=1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA])); mx,my,mw,mh,_=map(int,stats[biggest]); keep=labels==biggest
 for i in range(1,n):
  if i==biggest: continue
  x,y,w,h,area=map(int,stats[i]); cx=x+w/2; cy=y+h/2
  if (my+mh*.12)<=cy<=(my+mh+16) and (mx-125)<=cx<=(mx+mw+125) and area>=80: keep|=labels==i
 arr[~keep]=0; ys,xs=np.where(keep)
 if len(xs)<1000: raise SystemExit('CLEAN SUBJECT TOO SMALL')
 return Image.fromarray(arr,'RGBA'),(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1))

def normalize_subject(layer,max_w,max_h,bottom=35):
 a=np.asarray(layer.getchannel('A')); ys,xs=np.where(a>18)
 if len(xs)<1000: raise SystemExit('SUBJECT ALPHA TOO SMALL')
 crop=layer.crop((int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)))
 scale=min(max_w/crop.width,max_h/crop.height)
 nw,nh=max(1,int(crop.width*scale)),max(1,int(crop.height*scale)); crop=crop.resize((nw,nh),Image.Resampling.LANCZOS)
 canvas=Image.new('RGBA',SIZE,(0,0,0,0)); left=(SIZE[0]-nw)//2; top=max(18,SIZE[1]-nh-bottom); canvas.alpha_composite(crop,(left,top)); return canvas

def build_person(gender,bg):
 if gender=='male':
  clean=SRC/'male_base_clean.png'
  if not clean.exists(): raise SystemExit('male_base_clean.png missing: clean source must be generated first')
  layer=normalize_subject(exact(clean,'RGBA'),560,785,32)
  out=bg.copy(); out.alpha_composite(layer); return out,layer
 raw=exact(SRC/f'{gender}_base.png','RGBA'); subject,_=clean_subject(raw); layer=normalize_subject(subject,540,790,35); out=bg.copy(); out.alpha_composite(layer); return out,layer

def body_box(person):
 a=np.asarray(person.getchannel('A')); ys,xs=np.where(a>24)
 if len(xs)<1000: raise SystemExit('PERSON ALPHA TOO SMALL')
 return int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)

def face_box(person):
 x0,y0,x1,y1=body_box(person); w=x1-x0; h=y1-y0; fw=max(72,int(w*.34)); fh=max(85,int(h*.18)); return int((x0+x1-fw)/2),y0+int(h*.015),fw,fh

def skin_layer(gender,base):
 for name in SKINS: Image.new('RGBA',SIZE,(0,0,0,0)).save(OUT/gender/f'skin-{name}.webp','WEBP',lossless=True,method=6)

def isolate_hair(im):
 arr=np.asarray(im,dtype=np.uint8).copy(); bw=(arr[...,3]>24).astype(np.uint8); n,labels,stats,_=cv2.connectedComponentsWithStats(bw,8)
 if n<=1: raise SystemExit('EMPTY HAIR')
 valid=[]
 for i in range(1,n):
  x,y,w,h,area=map(int,stats[i])
  if area>=80 and w<=420 and h<=320: valid.append((area,i))
 if not valid:
  biggest=1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA])); x,y,w,h,_=map(int,stats[biggest]); cutoff=y+max(40,int(h*.24)); mask=(labels==biggest)&(np.indices(labels.shape)[0]<cutoff); arr[~mask]=0
 else: arr[labels!=max(valid)[1]]=0
 ys,xs=np.where(arr[...,3]>24)
 if len(xs)<60: raise SystemExit('NO USABLE HAIR')
 return Image.fromarray(arr,'RGBA').crop((int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)))

def register_hair(im,person,gender,style):
 crop=isolate_hair(im); fx,fy,fw,fh=face_box(person)

 # Global registration. The previous male offset was wrong for every hairstyle:
 # all male overlays were sitting slightly right and too high on the skull.
 if gender=='male':
  width_factor=1.08
  height_factor=.61
  x_nudge=-2
  y_nudge=5
 else:
  width_factor=1.05
  height_factor=.58
  x_nudge=0
  y_nudge=0

 # Keep only tiny style-specific size compensation, never a separate position shift.
 if gender=='male' and style=='male_medium':
  width_factor=1.11
  height_factor=.63
 elif gender=='male' and style=='male_slick':
  width_factor=1.09
  height_factor=.62

 target_w=int(fw*width_factor); target_h=int(fh*height_factor)
 scale=min(target_w/crop.width,target_h/crop.height)
 nw,nh=max(1,int(crop.width*scale)),max(1,int(crop.height*scale)); crop=crop.resize((nw,nh),Image.Resampling.LANCZOS)
 tx=int(fx+fw/2-nw/2+x_nudge); ty=int(fy+y_nudge)
 canvas=Image.new('RGBA',SIZE,(0,0,0,0)); canvas.alpha_composite(crop,(max(0,min(SIZE[0]-nw,tx)),max(0,min(SIZE[1]-nh,ty)))); return canvas

def main():
 bg=exact(SRC/'background.webp','RGBA')
 for g in ('male','female'):
  d=OUT/g; d.mkdir(parents=True,exist_ok=True); out,person=build_person(g,bg); out.convert('RGB').save(d/'base.webp','WEBP',quality=100,method=6); skin_layer(g,out.convert('RGB'))
  for style in STYLES[g]:
   for color in COLORS: register_hair(exact(HAIR/f'{style}_{color}.png','RGBA'),person,g,style).save(d/f'hair-{style}-{color}.webp','WEBP',lossless=True,method=6)
  files=list(d.glob('*.webp'))
  if len(files)!=31: raise SystemExit(f'{g}: expected 31 assets, got {len(files)}')
 print('layered-v4-fit4: global male hair registration fixed 9px left, 5px down, slightly enlarged')

if __name__=='__main__': main()
