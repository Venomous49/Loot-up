from pathlib import Path
import cv2
import numpy as np

SRC = Path('assets/characters/male/medium/brown/male_textured')
OUT = Path('silhouettes')
OUT.mkdir(exist_ok=True)

files = [
    '01-debutant.webp','05-debrouillard.webp','10-chasseur.webp','15-hustler.webp',
    '20-pro.webp','30-elite.webp','40-cyber-looter.webp','50-rise-looter.webp'
]

for name in files:
    img = cv2.imread(str(SRC / name), cv2.IMREAD_COLOR)
    if img is None:
        continue
    h, w = img.shape[:2]

    # GrabCut around the central full-body subject. The generated assets all keep
    # the character near the centre, so this produces a robust dark silhouette.
    mask = np.zeros((h, w), np.uint8)
    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    x = int(w * 0.18)
    y = int(h * 0.03)
    rw = int(w * 0.64)
    rh = int(h * 0.94)
    cv2.grabCut(img, mask, (x, y, rw, rh), bgd, fgd, 6, cv2.GC_INIT_WITH_RECT)
    fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype('uint8')

    # Clean small islands while preserving the character outline.
    kernel = np.ones((3,3), np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, kernel, iterations=2)
    fg = cv2.GaussianBlur(fg, (3,3), 0)

    # Light smoky background + almost-black character, matching the requested UI.
    bg = np.full((h, w, 3), 205, dtype=np.uint8)
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    shade = (205 - yy * 65).astype(np.uint8)
    bg[:] = np.repeat(shade[:, :, None], w, axis=1)

    alpha = (fg.astype(np.float32) / 255.0)[:, :, None]
    silhouette = (bg * (1 - alpha) + np.full_like(bg, 7) * alpha).astype(np.uint8)

    # Slight vignette for depth.
    Y, X = np.ogrid[:h, :w]
    cx, cy = w/2, h/2
    dist = ((X-cx)/(w/1.35))**2 + ((Y-cy)/(h/1.25))**2
    vignette = np.clip(1 - 0.22*dist, 0.72, 1.0)[:, :, None]
    silhouette = np.clip(silhouette.astype(np.float32)*vignette,0,255).astype(np.uint8)

    out = OUT / name.replace('.webp','.png')
    cv2.imwrite(str(out), silhouette)
