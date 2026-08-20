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
   fill=0 if mode=='L' else (0,0,0,0)
   canvas=Image.new(mode,SIZE,fill)
   crop=im.crop((0,0,min(im.width,SIZE[0]),min(im.height,SIZE[1])))
   canvas.paste(crop,(0,0))
   im=canvas
  else:
   raise SystemExit(f'BAD SIZE {path}: {im.size}')
 return im

def clean_subject(im):
 arr=np.asarray(im,dtype=np.uint8).copy(); a=arr[...,3]; bw=(a>18).astype(np.uint8)
 n,labels,stats,_=cv2.connectedComponentsWithStats(bw,8)
 if n<=1: raise SystemExit('NO SUBJECT')
 biggest=1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA])); mx,my,mw,mh,ma=map(int,stats[biggest]); keep=labels==biggest
 for i in range(1,n):
  if i==biggest: continue
  x,y,w,h,area=map(int,stats[i]); cx=x+w/2; cy=y+h/2
  limb_zone=(my+mh*.12)<=cy<=(my+mh+16) and (mx-125)<=cx<=(mx+mw+125)
  if limb_zone and area>=80: keep|=labels==i
 arr[~keep]=0; ys,xs=np.where(keep)
 if len(xs)<1000: raise SystemExit('CLEAN SUBJECT TOO SMALL')
 return Image.fromarray(arr,'RGBA'),(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1))

def build_person(gender,bg):
 raw=exact(SRC/f'{gender}_base.png','RGBA'); subject,box=clean_subject(raw); subject=subject.crop(box)
 max_w,max_h=(500,790) if gender=='male' else (540,790)
 scale=min(max_w/subject.width,max_h/subject.height); nw,nh=max(1,int(subject.width*scale)),max(1,int(subject.height*scale)); subject=subject.resize((nw,nh),Image.Resampling.LANCZOS)
 left=(SIZE[0]-nw)//2; top=max(20,SIZE[1]-nh-35)
 layer=Image.new('RGBA',SIZE,(0,0,0,0)); layer.alpha_composite(subject,(left,top)); out=bg.copy(); out.alpha_composite(layer); return out,layer

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
  biggest=1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA])); x,y,w,h,_=map(int,stats[biggest]); cutoff=y+max(45,int(h*.30)); mask=(labels==biggest)&(np.indices(labels.shape)[0]<cutoff); arr[~mask]=0
 else:
  arr[labels!=max(valid)[1]]=0
 ys,xs=np.where(arr[...,3]>24)
 if len(xs)<60: raise SystemExit('NO USABLE HAIR')
 return Image.fromarray(arr,'RGBA').crop((int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)))

def register_hair(im,person):
 crop=isolate_hair(im); fx,fy,fw,fh=face_box(person); target_w=int(fw*1.08); target_h=int(fh*.68); scale=min(target_w/crop.width,target_h/crop.height); nw,nh=max(1,int(crop.width*scale)),max(1,int(crop.height*scale)); crop=crop.resize((nw,nh),Image.Resampling.LANCZOS)
 tx=int(fx+fw/2-nw/2); ty=int(fy-nh*.30); canvas=Image.new('RGBA',SIZE,(0,0,0,0)); canvas.alpha_composite(crop,(max(0,min(SIZE[0]-nw,tx)),max(0,min(SIZE[1]-nh,ty)))); return canvas

def main():
 bg=exact(SRC/'background.webp','RGBA')
 for g in ('male','female'):
  d=OUT/g; d.mkdir(parents=True,exist_ok=True); out,person=build_person(g,bg); out.convert('RGB').save(d/'base.webp','WEBP',quality=100,method=6); skin_layer(g,out.convert('RGB'))
  for style in STYLES[g]:
   for color in COLORS: register_hair(exact(HAIR/f'{style}_{color}.png','RGBA'),person).save(d/f'hair-{style}-{color}.webp','WEBP',lossless=True,method=6)
  files=list(d.glob('*.webp'))
  if len(files)!=31: raise SystemExit(f'{g}: expected 31 assets, got {len(files)}')
 print('layered-v3: fullbody source, complete silhouette, debris rejected, skull-anchored hair')

if __name__=='__main__': main()
