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

    # Start GrabCut from a mask instead of one loose rectangle. This tells OpenCV
    # that the subject is the central full-body character and strongly rejects
    # the title/logo text and scenery around the borders.
    mask = np.full((h, w), cv2.GC_BGD, dtype=np.uint8)

    # Broad probable-foreground zone around the character.
    x1, x2 = int(w * 0.20), int(w * 0.82)
    y1, y2 = int(h * 0.035), int(h * 0.97)
    mask[y1:y2, x1:x2] = cv2.GC_PR_FGD

    # Strong central body seed. It intentionally follows a human-shaped stack
    # rather than covering the whole artwork.
    cv2.ellipse(mask, (int(w*.52), int(h*.16)), (int(w*.14), int(h*.14)), 0, 0, 360, cv2.GC_FGD, -1)
    cv2.ellipse(mask, (int(w*.52), int(h*.43)), (int(w*.22), int(h*.29)), 0, 0, 360, cv2.GC_FGD, -1)
    cv2.ellipse(mask, (int(w*.52), int(h*.74)), (int(w*.20), int(h*.27)), 0, 0, 360, cv2.GC_FGD, -1)

    # Explicitly reject the places where the generated cards contain their
    # typography. Keep the central head area untouched.
    mask[:int(h*.18), :int(w*.30)] = cv2.GC_BGD
    mask[:int(h*.12), int(w*.78):] = cv2.GC_BGD
    mask[int(h*.90):, :int(w*.16)] = cv2.GC_BGD
    mask[int(h*.90):, int(w*.86):] = cv2.GC_BGD

    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(img, mask, None, bgd, fgd, 8, cv2.GC_INIT_WITH_MASK)

    fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)

    # Join tiny gaps in clothing/limbs without swelling the outline too much.
    kernel = np.ones((3,3), np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, kernel, iterations=2)

    # Keep the central character component and discard floating text/logo pieces
    # or isolated bits of scenery. Score components by vertical span, area and
    # proximity to the horizontal centre of the artwork.
    n, labels, stats, centroids = cv2.connectedComponentsWithStats((fg > 0).astype(np.uint8), 8)
    best_label = 0
    best_score = -1.0

    for lab in range(1, n):
        x, y, bw, bh, area = stats[lab]
        cx, cy = centroids[lab]
        if area < h*w*0.004:
            continue
        centre_factor = max(0.05, 1.0 - abs(cx - w/2) / (w/2))
        vertical_factor = max(0.05, bh / h)
        border_penalty = 0.45 if (x <= 1 or x+bw >= w-1) else 1.0
        score = area * (1.0 + 2.2*vertical_factor) * (0.45 + centre_factor) * border_penalty
        if score > best_score:
            best_score = score
            best_label = lab

    if best_label:
        main = np.where(labels == best_label, 255, 0).astype(np.uint8)

        # Re-attach nearby foreground components that touch/dilate into the main
        # body (useful for an arm, bag, coat flap, wings or cyber accessories).
        grown = cv2.dilate(main, np.ones((11,11), np.uint8), iterations=1)
        keep = main.copy()
        for lab in range(1, n):
            if lab == best_label:
                continue
            comp = np.where(labels == lab, 255, 0).astype(np.uint8)
            area = stats[lab, cv2.CC_STAT_AREA]
            if area < h*w*0.0015:
                continue
            if cv2.countNonZero(cv2.bitwise_and(grown, comp)) > 0:
                keep = cv2.bitwise_or(keep, comp)
        fg = keep

    # Smooth only the edge by a very small amount so the silhouette remains crisp.
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((5,5), np.uint8), iterations=1)
    fg = cv2.GaussianBlur(fg, (3,3), 0)

    # Light smoky background + almost-black exact character silhouette.
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    shade = (214 - yy * 62).astype(np.uint8)
    bg = np.repeat(shade[:, :, None], w, axis=1)
    bg = np.repeat(bg, 3, axis=2)

    alpha = (fg.astype(np.float32) / 255.0)[:, :, None]
    silhouette = (bg * (1 - alpha) + np.full_like(bg, 5) * alpha).astype(np.uint8)

    # Subtle vignette only on the background; it does not alter the outline.
    Y, X = np.ogrid[:h, :w]
    dist = ((X-w/2)/(w/1.25))**2 + ((Y-h/2)/(h/1.20))**2
    vignette = np.clip(1 - 0.16*dist, 0.78, 1.0)[:, :, None]
    silhouette = np.clip(silhouette.astype(np.float32)*vignette, 0, 255).astype(np.uint8)

    out = OUT / name.replace('.webp','.png')
    cv2.imwrite(str(out), silhouette)
