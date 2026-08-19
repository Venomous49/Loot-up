"""Rise Looter canonical creator build override.

Keeps the reviewed hairstyle library and background, but fixes the live creator
geometry requested for production: both genders share the true canvas centre,
identical ground line and scale policy. It also softens synthetic recolouring so
skin and hair transitions are less likely to show visible mask edges.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_creator_fullbody_hd as core
import build_creator_from_hairstyle_masters as base

# True centre of the 1728 px scene. The previous 1110 value visibly pushed the
# avatar to the right in the production preview.
core.CENTER_X = core.CANVAS_SIZE[0] // 2  # 864
core.GROUND_Y = 900
core.TARGET_PERSON_HEIGHT = 820
core.MAX_PERSON_WIDTH = 900

# Keep texture/detail and reduce hard complexion boundaries. The source skin
# masks are reviewed but some neckline edges remain visible at strong blends.
_original_tint_skin = base.tint_skin
_original_tint = base.tint


def softer_tint_skin(rgb, alpha, target, strength=.76):
    return _original_tint_skin(rgb, alpha, target, strength=min(strength, .38))


def softer_tint(rgb, alpha, target, strength, minimum_luminance=.35,
                preserve_texture=False, maximum_luminance=1.08):
    # Natural colour-master files are used unchanged by the main builder.
    # This cap applies only to combinations that still need algorithmic tinting.
    return _original_tint(
        rgb, alpha, target, min(strength, .56), minimum_luminance,
        preserve_texture, maximum_luminance
    )


base.tint_skin = softer_tint_skin
base.tint = softer_tint
core.base.tint_skin = softer_tint_skin
core.base.tint = softer_tint

if __name__ == "__main__":
    core.build()
