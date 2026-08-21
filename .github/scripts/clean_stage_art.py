import os, subprocess, tempfile
import cv2
import numpy as np

REPO_ROOT = os.getcwd()
SOURCE_REF = os.environ.get('SOURCE_REF', '01e0cf95075b52d5635e9402d06ce17e18f45a03')
BASE = 'assets/characters/male/medium/brown/male_textured'
STAGES = [
    '01-debutant.webp','05-debrouillard.webp','10-chasseur.webp','15-hustler.webp',
    '20-pro.webp','30-elite.webp','40-cyber-looter.webp','50-rise-looter.webp'
]

def load_from_git(path):
    data = subprocess.check_output(['git','show',f'{SOURCE_REF}:{path}'])
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError(f'Cannot decode {path}')
    return img

def targeted_title_mask(img):
    h,w = img.shape[:2]
    roi = img[:int(h*0.42), :int(w*0.58)]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    # bright, relatively low-saturation lettering / strokes
    m1 = cv2.inRange(hsv, (0,0,145), (179,175,255))
    # high-frequency bright edges to catch anti-aliased title strokes
    lap = cv2.Laplacian(gray, cv2.CV_16S, ksize=3)
    lap = cv2.convertScaleAbs(lap)
    m2 = cv2.inRange(lap, 24, 255)
    m2 = cv2.bitwise_and(m2, cv2.inRange(gray, 95, 255))
    mask = cv2.bitwise_or(m1, m2)
    # keep plausible text-like connected components only
    num, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    clean = np.zeros_like(mask)
    for i in range(1,num):
        x,y,ww,hh,area = stats[i]
        if 3 <= area <= 5000 and ww <= int(w*0.50) and hh <= int(h*0.20):
            if y <= int(h*0.33):
                clean[labels==i] = 255
    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, np.ones((3,3),np.uint8))
    clean = cv2.dilate(clean, np.ones((5,5),np.uint8), iterations=1)
    full = np.zeros((h,w), np.uint8)
    full[:clean.shape[0], :clean.shape[1]] = clean
    return full

def bottom_label_mask(img):
    h,w = img.shape[:2]
    y0 = int(h*0.78)
    roi = img[y0:,:]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    # detect wide dark rounded label regions near the bottom
    dark = cv2.inRange(gray, 0, 82)
    dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, np.ones((13,5),np.uint8), iterations=2)
    num, labels, stats, _ = cv2.connectedComponentsWithStats(dark, 8)
    chosen = np.zeros_like(dark)
    best = None
    for i in range(1,num):
        x,y,ww,hh,area = stats[i]
        score = ww * hh
        if ww >= int(w*0.28) and hh >= 8 and y+hh >= int(roi.shape[0]*0.42):
            if best is None or score > best[0]:
                best = (score,i,x,y,ww,hh)
    if best:
        _,i,x,y,ww,hh = best
        pad_x,pad_y = 8,5
        x1=max(0,x-pad_x); y1=max(0,y-pad_y)
        x2=min(w,x+ww+pad_x); y2=min(roi.shape[0],y+hh+pad_y)
        chosen[y1:y2,x1:x2]=255
    else:
        # fallback around bright filename text in lower strip
        bright = cv2.inRange(gray, 150, 255)
        ys,xs = np.where(bright>0)
        if len(xs):
            x1=max(0,int(xs.min())-12); x2=min(w,int(xs.max())+13)
            y1=max(0,int(ys.min())-8); y2=min(roi.shape[0],int(ys.max())+9)
            chosen[y1:y2,x1:x2]=255
    full = np.zeros((h,w), np.uint8)
    full[y0:,:] = chosen
    return full

def clean_image(img):
    title = targeted_title_mask(img)
    bottom = bottom_label_mask(img)
    mask = cv2.bitwise_or(title, bottom)
    # two-pass inpainting reduces obvious smearing on larger removals
    first = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
    soft = cv2.GaussianBlur(mask, (0,0), 1.2)
    soft = (soft.astype(np.float32)/255.0)[...,None]
    second = cv2.inpaint(first, mask, 5, cv2.INPAINT_NS)
    merged = (second.astype(np.float32)*soft + first.astype(np.float32)*(1-soft)).clip(0,255).astype(np.uint8)
    return merged

def upscale_uhd(img):
    h,w = img.shape[:2]
    up = cv2.resize(img, (w*4,h*4), interpolation=cv2.INTER_LANCZOS4)
    blur = cv2.GaussianBlur(up, (0,0), 1.0)
    sharp = cv2.addWeighted(up, 1.18, blur, -0.18, 0)
    return sharp

def main():
    for name in STAGES:
        path = f'{BASE}/{name}'
        img = load_from_git(path)
        cleaned = clean_image(img)
        uhd = upscale_uhd(cleaned)
        out = os.path.join(REPO_ROOT, path)
        ok = cv2.imwrite(out, uhd, [cv2.IMWRITE_WEBP_QUALITY, 100])
        if not ok:
            raise RuntimeError(f'Cannot write {out}')
        print(name, img.shape, '->', uhd.shape)

if __name__ == '__main__':
    main()
