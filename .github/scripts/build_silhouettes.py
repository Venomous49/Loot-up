from pathlib import Path
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

human_session = new_session('u2net_human_seg')
general_session = new_session('isnet-general-use')

for name in FILES:
    src = SRC / name
    if not src.exists():
        raise FileNotFoundError(src)

    original = Image.open(src).convert('RGBA')
    special = name in {'30-elite.webp','40-cyber-looter.webp','50-rise-looter.webp'}
    session = general_session if special else human_session

    cut = remove(
        original,
        session=session,
        alpha_matting=True,
        alpha_matting_foreground_threshold=240 if special else 245,
        alpha_matting_background_threshold=8 if special else 12,
        alpha_matting_erode_size=3 if special else 5,
    )

    rgba = np.array(cut)
    alpha = rgba[:, :, 3]
    h, w = alpha.shape
    threshold = 20 if special else 36
    mask = np.where(alpha >= threshold, 255, 0).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3,3), np.uint8), iterations=1)

    n, labels, stats, centroids = cv2.connectedComponentsWithStats((mask > 0).astype(np.uint8), 8)
    if n <= 1:
        raise RuntimeError(f'No subject detected for {name}')

    # Find the central body first.
    body_candidates = []
    for lab in range(1, n):
        x, y, bw, bh, area = stats[lab]
        cx, cy = centroids[lab]
        if area < h*w*0.0015:
            continue
        centre = max(0.01, 1.0 - abs(cx - w/2)/(w/2))
        tall = bh / h
        lower_reach = (y + bh) / h
        score = area * (0.4 + centre) * (0.5 + 2.6*tall) * (0.7 + 0.3*lower_reach)
        body_candidates.append((score, lab))
    if not body_candidates:
        raise RuntimeError(f'No body component for {name}')

    main_lab = max(body_candidates)[1]
    main = np.where(labels == main_lab, 255, 0).astype(np.uint8)
    keep = main.copy()

    # Reattach disconnected pieces that belong to the character design.
    # Special masters need a much wider reach to retain wings, halo, cape,
    # floating armor ornaments and other defining elements.
    dilation = 95 if name == '50-rise-looter.webp' else (55 if special else 17)
    grown = cv2.dilate(main, np.ones((dilation, dilation), np.uint8), iterations=1)

    body_x, body_y, body_w, body_h, _ = stats[main_lab]
    body_cx = body_x + body_w/2
    body_top = body_y
    body_bottom = body_y + body_h

    for lab in range(1, n):
        if lab == main_lab:
            continue
        x, y, bw, bh, area = stats[lab]
        cx, cy = centroids[lab]
        if area < h*w*(0.00045 if special else 0.001):
            continue
        comp = np.where(labels == lab, 255, 0).astype(np.uint8)
        touches = cv2.countNonZero(cv2.bitwise_and(grown, comp)) > 0

        # For Rise Looter / Cyber Looter, keep substantial components in the
        # same vertical band and near the central character, even if disconnected
        # by glow gaps. This is what preserves wings and halo.
        near_character = (
            special and
            abs(cx - body_cx) < w*0.46 and
            y < min(h, body_bottom + h*0.12) and
            (y + bh) > max(0, body_top - h*0.20)
        )
        halo_zone = (
            name == '50-rise-looter.webp' and
            cy < h*0.24 and
            abs(cx - body_cx) < w*0.28 and
            area > h*w*0.00035
        )
        wing_zone = (
            name == '50-rise-looter.webp' and
            y < h*0.67 and
            abs(cx - body_cx) < w*0.49 and
            bw > w*0.055
        )

        if touches or near_character or halo_zone or wing_zone:
            keep = cv2.bitwise_or(keep, comp)

    # Explicitly remove title/label zones from the generated card artwork.
    keep[:int(h*0.18), :int(w*0.34)] = 0
    keep[int(h*0.91):, :int(w*0.22)] = 0
    keep[int(h*0.91):, int(w*0.78):] = 0

    # Protect Rise Looter halo region from the title cleanup while still
    # excluding the upper-left typography.
    if name == '50-rise-looter.webp':
        halo_source = mask[:int(h*0.22), int(w*0.28):int(w*0.76)]
        keep[:int(h*0.22), int(w*0.28):int(w*0.76)] = cv2.bitwise_or(
            keep[:int(h*0.22), int(w*0.28):int(w*0.76)], halo_source
        )

    keep = cv2.morphologyEx(keep, cv2.MORPH_CLOSE, np.ones((3,3), np.uint8), iterations=1)
    keep = cv2.GaussianBlur(keep, (3,3), 0)

    ys, xs = np.where(keep > 24)
    if len(xs) == 0:
        raise RuntimeError(f'Empty contour for {name}')
    x1, x2 = xs.min(), xs.max()
    y1, y2 = ys.min(), ys.max()
    pad_x = max(3, int((x2-x1+1)*0.02))
    pad_y = max(3, int((y2-y1+1)*0.012))
    x1, x2 = max(0,x1-pad_x), min(w-1,x2+pad_x)
    y1, y2 = max(0,y1-pad_y), min(h-1,y2+pad_y)

    char_mask = keep[y1:y2+1, x1:x2+1]
    ch, cw = char_mask.shape
    canvas = np.full((h, w, 3), 226, dtype=np.uint8)

    # Wider allowance for the winged Rise Looter so the silhouette is not
    # squeezed into a generic vertical blob.
    max_w_ratio = 0.94 if name == '50-rise-looter.webp' else (0.86 if special else 0.74)
    max_h_ratio = 0.91 if special else 0.88
    scale = min((w*max_w_ratio)/cw, (h*max_h_ratio)/ch)
    new_w = max(1, int(cw*scale))
    new_h = max(1, int(ch*scale))
    resized = cv2.resize(char_mask, (new_w,new_h), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)

    ox = (w-new_w)//2
    oy = max(0, h-new_h-int(h*0.035))
    region = canvas[oy:oy+new_h, ox:ox+new_w]
    a = (resized.astype(np.float32)/255.0)[:,:,None]
    region[:] = (region*(1-a)).astype(np.uint8)

    out = OUT / name.replace('.webp','.png')
    cv2.imwrite(str(out), canvas)
    print(f'Wrote {out} — source contour {cw}x{ch}, placed {new_w}x{new_h}')
