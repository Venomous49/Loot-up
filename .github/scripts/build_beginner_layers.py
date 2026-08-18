from pathlib import Path
import cv2
import numpy as np

SRC = Path('assets/characters/male/medium/brown/male_textured/01-debutant.webp')
OUT_DIR = Path('assets/characters/male/medium/brown/male_textured/generated')
OUT_DIR.mkdir(parents=True, exist_ok=True)

img = cv2.imread(str(SRC), cv2.IMREAD_COLOR)
if img is None:
    raise SystemExit('Unable to load beginner asset')

h, w = img.shape[:2]

# GrabCut autour du personnage central. Les coordonnées sont proportionnelles
# afin de rester robustes si l'image source change légèrement de résolution.
mask = np.full((h, w), cv2.GC_BGD, dtype=np.uint8)

# Zone probable du personnage.
x0, y0 = int(w * 0.28), int(h * 0.025)
x1, y1 = int(w * 0.73), int(h * 0.965)
mask[y0:y1, x0:x1] = cv2.GC_PR_FGD

# Coeur certain du personnage : tête, torse et jambes centrales.
cv2.ellipse(mask, (int(w*.51), int(h*.13)), (int(w*.11), int(h*.12)), 0, 0, 360, cv2.GC_FGD, -1)
cv2.rectangle(mask, (int(w*.38), int(h*.18)), (int(w*.64), int(h*.62)), cv2.GC_FGD, -1)
cv2.rectangle(mask, (int(w*.40), int(h*.55)), (int(w*.62), int(h*.91)), cv2.GC_FGD, -1)

bgd = np.zeros((1, 65), np.float64)
fgd = np.zeros((1, 65), np.float64)
cv2.grabCut(img, mask, None, bgd, fgd, 10, cv2.GC_INIT_WITH_MASK)

fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1, 0).astype(np.uint8)

# Garde le plus gros composant connecté dans la zone centrale.
num, labels, stats, _ = cv2.connectedComponentsWithStats(fg, 8)
if num > 1:
    candidates = []
    for i in range(1, num):
        cx = stats[i, cv2.CC_STAT_LEFT] + stats[i, cv2.CC_STAT_WIDTH] / 2
        cy = stats[i, cv2.CC_STAT_TOP] + stats[i, cv2.CC_STAT_HEIGHT] / 2
        area = stats[i, cv2.CC_STAT_AREA]
        if w*.25 < cx < w*.78 and h*.02 < cy < h*.98:
            candidates.append((area, i))
    if candidates:
        _, keep = max(candidates)
        fg = (labels == keep).astype(np.uint8)

# Nettoyage et contour légèrement adouci.
kernel = np.ones((3, 3), np.uint8)
fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, kernel, iterations=1)
fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, kernel, iterations=2)
alpha = cv2.GaussianBlur((fg * 255).astype(np.uint8), (5, 5), 0)

rgba = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
rgba[:, :, 3] = alpha
cv2.imwrite(str(OUT_DIR / '01-debutant-character.png'), rgba)

# Création d'un décor sans personnage. Le masque est dilaté pour éviter un halo.
inpaint_mask = cv2.dilate((fg * 255).astype(np.uint8), np.ones((13,13), np.uint8), iterations=2)
bg = cv2.inpaint(img, inpaint_mask, 9, cv2.INPAINT_TELEA)

# Efface aussi les deux légendes intégrées à l'image source (haut gauche + bas).
text_mask = np.zeros((h, w), dtype=np.uint8)
cv2.rectangle(text_mask, (0, 0), (int(w*.58), int(h*.20)), 255, -1)
cv2.rectangle(text_mask, (int(w*.15), int(h*.90)), (int(w*.86), h-1), 255, -1)
bg = cv2.inpaint(bg, text_mask, 7, cv2.INPAINT_TELEA)
cv2.imwrite(str(OUT_DIR / '01-debutant-background.webp'), bg, [cv2.IMWRITE_WEBP_QUALITY, 92])

print('Generated beginner background and transparent character layers')
