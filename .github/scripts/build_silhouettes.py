from pathlib import Path
from io import BytesIO
import cv2
import numpy as np
from PIL import Image
from rembg import remove, new_session

SRC = Path('assets/characters/male/medium/brown/male_textured')
OUT = Path('silhouettes')
OUT.mkdir(exist_ok=True)

FILES = [
    '01-debutant.webp','05-debrouillard.webp','10-chasseur.webp','15-hustler.webp',
    '20-pro.webp','30-elite.webp','40-cyber-looter.webp','50-rise-looter.webp'
]

# Human-specific segmentation model: isolates the character instead of darkening
# the full master artwork. The generated PNG keeps the exact pose/outline only.
session = new_session('u2net_human_seg')

for name in FILES:
    src = SRC / name
    if not src.exists():
        raise FileNotFoundError(src)

    original = Image.open(src).convert('RGBA')
    cut = remove(original, session=session, alpha_matting=True,
                 alpha_matting_foreground_threshold=245,
                 alpha_matting_background_threshold=12,
                 alpha_matting_erode_size=5)

    rgba = np.array(cut)
    alpha = rgba[:, :, 3]
    h, w = alpha.shape

    # Remove weak segmentation noise and keep the subject itself.
    mask = np.where(alpha >= 36, 255, 0).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3,3), np.uint8), iterations=1)

    n, labels, stats, centroids = cv2.connectedComponentsWithStats((mask > 0).astype(np.uint8), 8)
    if n <= 1:
        raise RuntimeError(f'No character detected for {name}')

    # Main component = large, tall, near image centre. This rejects title text,
    # vehicles, buildings and other background remnants.
    scores = []
    for lab in range(1, n):
        x, y, bw, bh, area = stats[lab]
        cx, cy = centroids[lab]
        if area < h*w*0.002:
            continue
        centre = max(0.02, 1.0 - abs(cx - w/2)/(w/2))
        tall = bh / h
        score = area * (0.45 + centre) * (0.5 + 2.5*tall)
        scores.append((score, lab))
    if not scores:
        raise RuntimeError(f'No valid character component for {name}')

    main_lab = max(scores)[1]
    main = np.where(labels == main_lab, 255, 0).astype(np.uint8)

    # Keep nearby pieces belonging to the same design (coat flaps, bag, wings,
    # cyber ornaments) only when close enough to the main silhouette.
    grown = cv2.dilate(main, np.ones((17,17), np.uint8), iterations=1)
    keep = main.copy()
    for lab in range(1, n):
        if lab == main_lab:
            continue
        x, y, bw, bh, area = stats[lab]
        if area < h*w*0.001:
            continue
        comp = np.where(labels == lab, 255, 0).astype(np.uint8)
        if cv2.countNonZero(cv2.bitwise_and(grown, comp)):
            keep = cv2.bitwise_or(keep, comp)

    # Crisp contour with only tiny smoothing—no swollen generic blob.
    keep = cv2.morphologyEx(keep, cv2.MORPH_CLOSE, np.ones((3,3), np.uint8), iterations=1)
    keep = cv2.GaussianBlur(keep, (3,3), 0)

    # Crop to the actual character contour, then place it centered on a clean
    # light card while preserving the original aspect ratio and exact pose.
    ys, xs = np.where(keep > 24)
    if len(xs) == 0:
        raise RuntimeError(f'Empty contour for {name}')
    x1, x2 = xs.min(), xs.max()
    y1, y2 = ys.min(), ys.max()
    pad_x = max(3, int((x2-x1+1)*0.025))
    pad_y = max(3, int((y2-y1+1)*0.015))
    x1, x2 = max(0,x1-pad_x), min(w-1,x2+pad_x)
    y1, y2 = max(0,y1-pad_y), min(h-1,y2+pad_y)

    char_mask = keep[y1:y2+1, x1:x2+1]
    ch, cw = char_mask.shape
    canvas_h, canvas_w = h, w
    canvas = np.full((canvas_h, canvas_w, 3), 226, dtype=np.uint8)

    max_w = int(canvas_w*0.74)
    max_h = int(canvas_h*0.88)
    scale = min(max_w/cw, max_h/ch)
    new_w = max(1, int(cw*scale))
    new_h = max(1, int(ch*scale))
    resized = cv2.resize(char_mask, (new_w,new_h), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)

    ox = (canvas_w-new_w)//2
    oy = canvas_h-new_h-int(canvas_h*0.045)
    oy = max(0, oy)
    region = canvas[oy:oy+new_h, ox:ox+new_w]
    a = (resized.astype(np.float32)/255.0)[:,:,None]
    region[:] = (region*(1-a) + np.zeros_like(region)*a).astype(np.uint8)

    out = OUT / name.replace('.webp','.png')
    cv2.imwrite(str(out), canvas)
    print(f'Wrote {out} — contour {cw}x{ch}, placed {new_w}x{new_h}')
