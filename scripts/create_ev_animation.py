from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import imageio.v2 as imageio
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "frontend" / "public" / "ev-source-close.png"
OUT_GIF = ROOT / "frontend" / "public" / "ev-charging.gif"
OUT_WEBP = ROOT / "frontend" / "public" / "ev-charging.webp"
OUT_MP4 = ROOT / "frontend" / "public" / "ev-charging.mp4"


def masked_sprite(source: Image.Image, polygon: list[tuple[int, int]]) -> Image.Image:
    mask = Image.new("L", source.size, 0)
    ImageDraw.Draw(mask).polygon(polygon, fill=255)
    sprite = source.convert("RGBA")
    sprite.putalpha(mask)
    return sprite


def build_frames() -> list[Image.Image]:
    source = Image.open(SOURCE).convert("RGBA")
    width, height = source.size

    charger_outline = [
        (86, 176), (205, 177), (252, 212), (273, 430), (275, 791),
        (238, 851), (113, 850), (85, 815),
    ]
    car_outline = [
        (309, 610), (360, 559), (512, 510), (650, 450), (742, 388),
        (878, 365), (1154, 365), (1308, 405), (1450, 484), (1575, 573),
        (1631, 603), (1648, 729), (1613, 823), (1516, 876), (1285, 914),
        (555, 914), (365, 871), (310, 790),
    ]
    charger = masked_sprite(source, charger_outline)
    car = masked_sprite(source, car_outline)

    # Preserve the source cable pixels as a raster stroke in the fixed charging-station layer.
    cable = Image.new("RGBA", source.size, (0, 0, 0, 0))
    cable_mask = Image.new("L", source.size, 0)
    cable_draw = ImageDraw.Draw(cable_mask)
    cable_draw.line([(208, 315), (218, 510), (260, 715), (355, 850), (550, 900)], fill=255, width=18, joint="curve")
    cable.putalpha(cable_mask)
    cable_source = source.copy()
    cable_source.putalpha(cable_mask)

    frames: list[Image.Image] = []
    for frame_index in range(48):
        canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        canvas.alpha_composite(charger)
        canvas.alpha_composite(cable_source)

        if frame_index < 19:
            progress = frame_index / 18
            offset = int(520 * (1 - progress) ** 1.55)
        else:
            offset = 0
        moving_car = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        moving_car.alpha_composite(car, (offset, 0))
        canvas.alpha_composite(moving_car)

        if frame_index >= 19:
            pulse = 0.35 + 0.3 * ((frame_index - 19) % 10) / 9
            glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow)
            glow_draw.ellipse((170, 410, 250, 490), fill=(0, 245, 154, int(90 * pulse)))
            glow_draw.ellipse((205, 285, 285, 365), fill=(0, 245, 154, int(55 * pulse)))
            glow = glow.filter(ImageFilter.GaussianBlur(8))
            canvas.alpha_composite(glow)

        frames.append(canvas)
    return frames


if __name__ == "__main__":
    animation = build_frames()
    animation[0].save(OUT_GIF, save_all=True, append_images=animation[1:], duration=83, loop=0, disposal=2, transparency=0)
    animation[0].save(OUT_WEBP, save_all=True, append_images=animation[1:], duration=83, loop=0, lossless=True, quality=95, method=6)
    writer = imageio.get_writer(OUT_MP4, fps=12, codec="libx264", quality=8, macro_block_size=1)
    video_background = Image.new("RGBA", animation[0].size, (242, 242, 240, 255))
    for frame in animation:
        rendered = video_background.copy()
        rendered.alpha_composite(frame)
        rendered = rendered.convert("RGB").resize((740, 492))
        writer.append_data(np.asarray(rendered))
    writer.close()
    print(f"created {OUT_GIF}")
    print(f"created {OUT_WEBP}")
    print(f"created {OUT_MP4}")
