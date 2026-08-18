from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "creator_sources"
OUTPUT = ROOT / "assets" / "creator"

MASTERS = {
    "female": {
        "female_long": SOURCE / "female_long.webp",
        "female_wavy": SOURCE / "female_wavy.png",
        "female_bob": SOURCE / "female_bob.png",
        "female_ponytail": SOURCE / "female_ponytail.png",
        "female_short": SOURCE / "female_short.png",
    },
    "male": {
        "male_textured": SOURCE / "male_textured.webp",
        "male_short": SOURCE / "male_short.png",
        "male_medium": SOURCE / "male_medium.png",
        "male_undercut": SOURCE / "male_undercut.png",
        "male_slick": SOURCE / "male_slick.png",
    },
}

SIZES = {"female": (1728, 910), "male": (1086, 1448)}
SKINS = {
    "light": (222, 174, 145),
    "warm": (194, 130, 87),
    "medium": (154, 96, 62),
    "deep": (105, 64, 42),
    "dark": (66, 40, 29),
}
HAIRS = {
    "black": (24, 20, 19),
    "brown": (70, 43, 29),
    "blond": (190, 145, 83),
    "red": (136, 57, 31),
    "purple": (84, 45, 111),
}


def ellipse(xx, yy, cx, cy, rx, ry):
    return ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1


def masks(image, gender, style):
    rgb = np.asarray(image).astype(np.float32)
    h, w = rgb.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    x, y = xx / w, yy / h
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]

    # Existing hair is dark and neutral/warm. Geometry keeps alley and clothes out.
    dark_hair = (r < 125) & (g < 105) & (b < 100) & (r >= b * .82)
    if gender == "female":
        face = ellipse(x, y, .52, .285, .092, .185)
        bounds = {
            "female_long": ((x > .31) & (x < .69) & (y < .88)),
            "female_wavy": ((x > .30) & (x < .70) & (y < .91)),
            "female_bob": ((x > .38) & (x < .64) & (y < .53)),
            "female_ponytail": ((x > .39) & (x < .65) & (y < .58)),
            "female_short": ((x > .40) & (x < .63) & (y < .39)),
        }[style]
        hair = dark_hair & bounds & ~face
        anatomy = face | ((x > .46) & (x < .58) & (y > .39) & (y < .60))
    else:
        face = ellipse(x, y, .585, .145, .070, .070)
        bounds = (x > .49) & (x < .68) & (y > .025) & (y < .17)
        hair = dark_hair & bounds & ~face
        anatomy = face | ((x > .52) & (x < .65) & (y > .17) & (y < .31))
        anatomy |= ((x > .39) & (x < .76) & (y > .25) & (y < .72))

    skin_colour = (r > g * 1.05) & (g > b * 1.04) & (r > 48) & (b < 185)
    skin = skin_colour & anatomy

    def soften(mask, radius):
        layer = Image.fromarray((mask.astype(np.uint8) * 255), "L")
        return np.asarray(layer.filter(ImageFilter.GaussianBlur(radius))) / 255.0

    return soften(hair, 1.4), soften(skin, 2.0)


def tint(rgb, alpha, target, strength):
    src = rgb.astype(np.float32)
    luminance = .299 * src[..., 0] + .587 * src[..., 1] + .114 * src[..., 2]
    target = np.asarray(target, dtype=np.float32)
    coloured = target[None, None, :] * np.clip(luminance[..., None] / 105.0, .35, 1.75)
    a = (alpha * strength)[..., None]
    return np.clip(src * (1 - a) + coloured * a, 0, 255)


def build():
    written = 0
    for gender, styles in MASTERS.items():
        for style, source in styles.items():
            if not source.exists():
                raise SystemExit(f"Missing hairstyle master: {source}")
            master = Image.open(source).convert("RGB")
            master = ImageOps.fit(master, SIZES[gender], Image.Resampling.LANCZOS)
            base = np.asarray(master).astype(np.float32)
            hair_mask, skin_mask = masks(master, gender, style)
            if hair_mask.sum() < 250:
                raise SystemExit(f"Unsafe hair mask for {gender}/{style}")

            for skin_name, skin_rgb in SKINS.items():
                skinned = tint(base, skin_mask, skin_rgb, .78)
                for hair_name, hair_rgb in HAIRS.items():
                    result = tint(skinned, hair_mask, hair_rgb, .94).astype(np.uint8)
                    path = OUTPUT / gender / skin_name / hair_name / f"{style}.webp"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    Image.fromarray(result, "RGB").save(path, "WEBP", quality=91, method=6)
                    written += 1

    if written != 250:
        raise SystemExit(f"Expected 250 presets, wrote {written}")
    print(f"Built {written} presets from ten distinct hairstyle masters")


if __name__ == "__main__":
    build()
