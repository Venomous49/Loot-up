from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'assets' / 'creator_sources' / 'fullbody'
HAIR_DIR = SRC / 'hair'
OUT = ROOT / 'assets' / 'creator' / 'male'
SIZE = (1728, 910)
SKINS = {
    'light': (222, 174, 145),
    'warm': (194, 130, 87),
    'medium': (154, 96, 62),
    'deep': (111, 68, 45),
    'dark': (75, 45, 31),
}
HAIRS = ['black', 'brown', 'blond', 'red', 'purple']
STYLES = ['male_textured', 'male_short', 'male_medium', 'male_undercut', 'male_slick']


def fit(im, mode):
    if im.size == SIZE:
        return im.convert(mode)
    return ImageOps.fit(im.convert(mode), SIZE, Image.Resampling.LANCZOS)


def load_background():
    return fit(Image.open(SRC / 'background.webp'), 'RGB')


def load_base_scene():
    bg = load_background().convert('RGBA')
    base = fit(Image.open(SRC / 'male_base.png'), 'RGBA')
    alpha = np.asarray(base.getchannel('A'), dtype=np.uint8)
    ys, xs = np.where(alpha > 18)
    if len(xs) < 1000:
        raise SystemExit('male_base.png has no usable full-body alpha')
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    if (y1 - y0 + 1) < 600 or y1 < int(SIZE[1] * .82):
        raise SystemExit(f'male_base.png is not full body: bbox={(x0,y0,x1,y1)}')
    bg.alpha_composite(base)
    return bg.convert('RGB'), base


def tint_skin(scene_rgb, mask_img, target):
    rgb = np.asarray(scene_rgb, dtype=np.uint8)
    mask = np.asarray(fit(mask_img, 'L'), dtype=np.float32) / 255.0
    # Skin mask must never reach clothing/lower body.
    if np.count_nonzero(mask[int(SIZE[1] * .42):] > .05):
        raise SystemExit('male_skin_mask.png reaches clothing/lower body')
    src_lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    target_lab = cv2.cvtColor(np.asarray(target, dtype=np.uint8).reshape(1,1,3), cv2.COLOR_RGB2LAB)[0,0].astype(np.float32)
    toned = src_lab.copy()
    toned[...,0] = np.clip(src_lab[...,0] * .88 + target_lab[0] * .12, 0, 255)
    toned[...,1] = np.clip(src_lab[...,1] * .28 + target_lab[1] * .72, 0, 255)
    toned[...,2] = np.clip(src_lab[...,2] * .28 + target_lab[2] * .72, 0, 255)
    toned = cv2.cvtColor(toned.astype(np.uint8), cv2.COLOR_LAB2RGB).astype(np.float32)
    a = cv2.GaussianBlur(mask, (0,0), .45)[...,None] * .80
    out = np.clip(rgb.astype(np.float32) * (1-a) + toned * a, 0, 255).astype(np.uint8)
    return Image.fromarray(out, 'RGB')


def load_hair(style, colour):
    path = HAIR_DIR / f'{style}_{colour}.png'
    if not path.exists():
        raise SystemExit(f'Missing hair source: {path}')
    hair = fit(Image.open(path), 'RGBA')
    alpha = np.asarray(hair.getchannel('A'), dtype=np.uint8)
    ys, xs = np.where(alpha > 20)
    if len(xs) < 50:
        raise SystemExit(f'Empty hair alpha: {path}')
    y0, y1 = int(ys.min()), int(ys.max())
    # Dedicated hair layers are only allowed near the head.
    if y1 >= int(SIZE[1] * .43):
        raise SystemExit(f'Hair layer reaches torso: {path} y1={y1}')
    # Remove extremely weak pixels that can look like smoke/halo.
    a = np.asarray(hair.getchannel('A'), dtype=np.uint8)
    a[a < 26] = 0
    hair.putalpha(Image.fromarray(a, 'L'))
    return hair


def main():
    base_scene, _ = load_base_scene()
    skin_mask = Image.open(SRC / 'male_skin_mask.png')
    written = 0
    for skin_name, skin_rgb in SKINS.items():
        skinned = tint_skin(base_scene, skin_mask, skin_rgb).convert('RGBA')
        for colour in HAIRS:
            for style in STYLES:
                result = skinned.copy()
                result.alpha_composite(load_hair(style, colour))
                out = result.convert('RGB')
                path = OUT / skin_name / colour / f'{style}.webp'
                path.parent.mkdir(parents=True, exist_ok=True)
                out.save(path, 'WEBP', quality=100, method=6)
                written += 1
    if written != 125:
        raise SystemExit(f'Expected 125 male assets, wrote {written}')
    print('Built 125 male presets from dedicated fullbody base + reviewed skin mask + 25 dedicated hair layers.')


if __name__ == '__main__':
    main()
