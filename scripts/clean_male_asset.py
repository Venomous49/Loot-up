from pathlib import Path
from PIL import Image
import numpy as np
import cv2
from rembg import remove, new_session

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / '01-debutant.webp'
OUT = ROOT / 'assets/creator_sources/fullbody/male_base_clean.png'
CANVAS = (1728, 910)

img = Image.open(SRC).convert('RGBA')
session = new_session('u2net_human_seg')
cut = remove(img, session=session, alpha_matting=False).convert('RGBA')
arr = np.asarray(cut).copy()
a = arr[..., 3]
bw = (a > 18).astype('uint8')
n, labels, stats, _ = cv2.connectedComponentsWithStats(bw, 8)
if n <= 1:
    raise SystemExit('segmentation returned no subject')
main = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
mx, my, mw, mh, ma = map(int, stats[main])
keep = labels == main
for i in range(1, n):
    if i == main:
        continue
    x, y, w, h, area = map(int, stats[i])
    cx, cy = x + w/2, y + h/2
    near = (mx - 80 <= cx <= mx + mw + 80 and my - 30 <= cy <= my + mh + 30)
    if near and area >= 180:
        keep |= labels == i
arr[~keep] = 0
ys, xs = np.where(arr[..., 3] > 18)
if len(xs) < 15000:
    raise SystemExit('clean subject unexpectedly small')
subject = Image.fromarray(arr, 'RGBA').crop((int(xs.min()), int(ys.min()), int(xs.max()+1), int(ys.max()+1)))
max_w, max_h = 500, 800
scale = min(max_w / subject.width, max_h / subject.height, 1.0)
nw, nh = max(1, round(subject.width * scale)), max(1, round(subject.height * scale))
subject = subject.resize((nw, nh), Image.Resampling.LANCZOS)
canvas = Image.new('RGBA', CANVAS, (0,0,0,0))
left = (CANVAS[0] - nw)//2
top = max(20, CANVAS[1] - nh - 35)
canvas.alpha_composite(subject, (left, top))
OUT.parent.mkdir(parents=True, exist_ok=True)
canvas.save(OUT)
print(f'clean male asset written: subject={nw}x{nh} at {left},{top}')
