import os
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
DEPS = ROOT.parent / "rembg-deps"
MODEL_HOME = ROOT.parent / "rembg-models"
sys.path.insert(0, str(DEPS))
os.environ["U2NET_HOME"] = str(MODEL_HOME)

from rembg import new_session, remove

STYLES = {
    "male": ["male_textured", "male_short", "male_medium", "male_undercut", "male_slick"],
    "female": ["female_long", "female_wavy", "female_bob", "female_ponytail", "female_short"],
}
OUT = ROOT / "assets" / "creator_sources" / "person_masks"
OUT.mkdir(parents=True, exist_ok=True)
COLOR_OUT = ROOT / "assets" / "creator_sources" / "color_master_masks"
COLOR_OUT.mkdir(parents=True, exist_ok=True)

session = new_session("u2net_human_seg")


def extract(source, destination, label):
    image = Image.open(source).convert("RGB")
    isolated = remove(image, session=session, only_mask=True, post_process_mask=True)
    alpha = np.asarray(isolated.convert("L"))
    binary = (alpha > 40).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(binary, 8)
    if count < 2:
        raise SystemExit(f"No foreground component: {label}")
    largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    alpha = np.where(labels == largest, alpha, 0).astype(np.uint8)
    mask = Image.fromarray(alpha, "L").filter(ImageFilter.GaussianBlur(.65))
    arr = np.asarray(mask)
    ys, xs = np.where(arr > 24)
    coverage = len(xs) / arr.size
    corner = np.concatenate([
        arr[:40, :40].ravel(), arr[:40, -40:].ravel(),
        arr[-40:, :40].ravel(), arr[-40:, -40:].ravel(),
    ]).mean()
    if not (.08 < coverage < .58):
        raise SystemExit(f"Unsafe coverage {coverage:.3f}: {label}")
    if corner > 2:
        raise SystemExit(f"Foreground reaches corners ({corner:.2f}): {label}")
    bbox = (int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1))
    mask.save(destination)
    print(label, f"coverage={coverage:.3f}", f"bbox={bbox}", f"corner={corner:.2f}")


for gender, styles in STYLES.items():
    for style in styles:
        source = ROOT / "assets" / "creator" / gender / "medium" / "black" / f"{style}.webp"
        extract(source, OUT / f"{style}.png", style)

for source in sorted((ROOT / "assets" / "creator_sources").glob("*_natural.png")):
    extract(source, COLOR_OUT / source.with_suffix(".png").name, source.stem)
