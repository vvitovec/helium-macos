#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs" / "assets"

SCREEN_W = 2880
SCREEN_H = 1864

# Approximate physical notch proportions for a 14/16-inch MacBook Pro display,
# scaled to these 2880px-wide screenshots. Screenshots do not capture the
# physical camera cutout, so the overlay makes that missing hardware visible.
NOTCH_W = 264
NOTCH_H = 54
NOTCH_RADIUS = 14

BG = (9, 11, 18)
BEZEL = (5, 6, 9)
ALUMINUM = (188, 193, 201)
ALUMINUM_DARK = (84, 91, 102)
TEXT = (241, 245, 249)
MUTED = (148, 163, 184)
RED = (248, 113, 113)
GREEN = (74, 222, 128)
PANEL = (15, 20, 30)
PANEL_EDGE = (43, 51, 66)


def font(size: int, paths: tuple[str, ...] | None = None) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in paths or (
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ):
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            pass
    return ImageFont.load_default()


FONT_TITLE = font(52)
FONT_LABEL = font(32)
FONT_SMALL = font(24)
FONT_TINY = font(20)
FONT_GIF_EYEBROW = font(28, ("/System/Library/Fonts/Supplemental/Avenir Next.ttc",))
FONT_GIF_TITLE = font(64, ("/System/Library/Fonts/Supplemental/Avenir Next.ttc",))
FONT_GIF_BODY = font(30, ("/System/Library/Fonts/Supplemental/Avenir Next.ttc",))


def rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255)
    return mask


def draw_notch(draw: ImageDraw.ImageDraw, screen_x: int, screen_y: int, scale: float) -> None:
    notch_w = round(NOTCH_W * scale)
    notch_h = round(NOTCH_H * scale)
    radius = round(NOTCH_RADIUS * scale)
    cx = screen_x + round(SCREEN_W * scale / 2)
    left = cx - notch_w // 2
    right = left + notch_w
    top = screen_y
    bottom = top + notch_h

    draw.rounded_rectangle((left, top - radius, right, bottom), radius=radius, fill=(0, 0, 0))
    draw.rectangle((left, top - radius, right, top + radius), fill=(0, 0, 0))

    camera_r = max(3, round(6 * scale))
    camera_x = cx
    camera_y = top + round(22 * scale)
    draw.ellipse(
        (camera_x - camera_r, camera_y - camera_r, camera_x + camera_r, camera_y + camera_r),
        fill=(13, 16, 20),
        outline=(25, 30, 38),
        width=max(1, round(1.5 * scale)),
    )


def frame_screenshot(source: Path, output: Path, max_screen_w: int = 1860) -> None:
    screenshot = ImageOps.exif_transpose(Image.open(source)).convert("RGB")
    if screenshot.size != (SCREEN_W, SCREEN_H):
        screenshot = ImageOps.fit(screenshot, (SCREEN_W, SCREEN_H), method=Image.Resampling.LANCZOS)

    scale = max_screen_w / SCREEN_W
    screen_w = round(SCREEN_W * scale)
    screen_h = round(SCREEN_H * scale)
    bezel = round(24 * scale)
    aluminum = max(3, round(6 * scale))
    radius = round(44 * scale)
    screen_radius = round(34 * scale)

    frame_w = screen_w + 2 * (bezel + aluminum)
    frame_h = screen_h + 2 * (bezel + aluminum)
    pad_x = round(34 * scale)
    pad_y = round(34 * scale)
    canvas = Image.new("RGBA", (frame_w + 2 * pad_x, frame_h + 2 * pad_y), BG + (255,))

    x = pad_x
    y = pad_y
    draw = ImageDraw.Draw(canvas)

    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (x + 8, y + 18, x + frame_w - 8, y + frame_h + 18),
        radius=radius,
        fill=(0, 0, 0, 150),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(round(18 * scale)))
    canvas.alpha_composite(shadow)

    draw.rounded_rectangle(
        (x, y, x + frame_w, y + frame_h),
        radius=radius,
        fill=ALUMINUM,
        outline=(226, 230, 236),
        width=max(1, round(1.5 * scale)),
    )
    draw.rounded_rectangle(
        (x + aluminum, y + aluminum, x + frame_w - aluminum, y + frame_h - aluminum),
        radius=radius - aluminum,
        fill=BEZEL,
        outline=ALUMINUM_DARK,
        width=max(1, round(1.5 * scale)),
    )

    screen_x = x + aluminum + bezel
    screen_y = y + aluminum + bezel
    scaled = screenshot.resize((screen_w, screen_h), Image.Resampling.LANCZOS)
    canvas.paste(scaled, (screen_x, screen_y), rounded_mask((screen_w, screen_h), screen_radius))

    # Repaint the inner bezel edge after pasting the screen so the laptop outline
    # stays crisp at README sizes.
    draw.rounded_rectangle(
        (screen_x, screen_y, screen_x + screen_w, screen_y + screen_h),
        radius=screen_radius,
        outline=(37, 43, 53),
        width=max(2, round(3 * scale)),
    )
    draw_notch(draw, screen_x, screen_y, scale)

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output, quality=94, optimize=True)


def draw_badge(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, color: tuple[int, int, int]) -> None:
    x, y = xy
    width = 128 if len(text) < 7 else 146
    height = 40
    draw.rounded_rectangle((x, y, x + width, y + height), radius=20, fill=color)
    bbox = draw.textbbox((0, 0), text, font=FONT_TINY)
    tx = x + (width - (bbox[2] - bbox[0])) // 2
    ty = y + (height - (bbox[3] - bbox[1])) // 2 - 1
    draw.text((tx, ty), text, font=FONT_TINY, fill=(8, 11, 18))


def make_comparison(before: Path, after: Path, output: Path) -> None:
    left = Image.open(before).convert("RGB")
    right = Image.open(after).convert("RGB")
    panel_w = 1180
    left.thumbnail((panel_w, 980), Image.Resampling.LANCZOS)
    right.thumbnail((panel_w, 980), Image.Resampling.LANCZOS)

    pad = 58
    gap = 44
    label_h = 112
    image_h = max(left.height, right.height)
    width = pad * 2 + panel_w * 2 + gap
    height = 150 + label_h + image_h + 68
    canvas = Image.new("RGBA", (width, height), BG + (255,))
    draw = ImageDraw.Draw(canvas)

    draw.text((pad, 38), "Fullscreen, without wasting the notch", font=FONT_TITLE, fill=TEXT)
    draw.text(
        (pad, 94),
        "Same screenshot geometry, same MacBook outline. The notch is drawn in its real top-center position.",
        font=FONT_SMALL,
        fill=MUTED,
    )

    panels = [
        (left, pad, "Before", "normal fullscreen leaves the top strip empty", RED),
        (right, pad + panel_w + gap, "After", "Helium puts tabs and controls around the notch", GREEN),
    ]
    for image, x, title, subtitle, color in panels:
        y = 150
        draw.rounded_rectangle(
            (x, y, x + panel_w, y + label_h + image_h + 36),
            radius=28,
            fill=PANEL,
            outline=PANEL_EDGE,
            width=1,
        )
        draw_badge(draw, (x + 26, y + 28), title.upper(), color)
        draw.text((x + 182, y + 22), title, font=FONT_LABEL, fill=TEXT)
        draw.text((x + 182, y + 60), subtitle, font=FONT_SMALL, fill=MUTED)
        ix = x + (panel_w - image.width) // 2
        iy = y + label_h
        canvas.paste(image, (ix, iy))

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output, quality=94, optimize=True)


def draw_gif_header(
    draw: ImageDraw.ImageDraw,
    eyebrow: str,
    title: str,
    body: str,
    accent: tuple[int, int, int],
) -> None:
    draw.rounded_rectangle((64, 50, 228, 94), radius=22, fill=accent)
    draw.text((91, 60), eyebrow, font=FONT_GIF_EYEBROW, fill=(8, 11, 18))
    draw.text((64, 118), title, font=FONT_GIF_TITLE, fill=TEXT)
    draw.text((66, 198), body, font=FONT_GIF_BODY, fill=MUTED)


def make_gif_frame(
    image_path: Path,
    eyebrow: str,
    title: str,
    body: str,
    accent: tuple[int, int, int],
) -> Image.Image:
    width = 1700
    height = 1330
    image_max_w = 1580
    header_h = 270
    canvas = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(canvas)
    draw_gif_header(draw, eyebrow, title, body, accent)

    image = Image.open(image_path).convert("RGB")
    image.thumbnail((image_max_w, height - header_h - 56), Image.Resampling.LANCZOS)
    x = (width - image.width) // 2
    y = header_h

    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (x + 16, y + 20, x + image.width - 16, y + image.height + 18),
        radius=28,
        fill=(0, 0, 0, 120),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(28))
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.alpha_composite(shadow)
    canvas_rgba.paste(image, (x, y))
    return canvas_rgba.convert("RGB")


def make_demo_gif(before: Path, after: Path, output: Path) -> None:
    before_frame = make_gif_frame(
        before,
        "SAFARI",
        "Other browsers waste the notch strip",
        "A black band sits above the page, while tabs and the URL bar still take another row.",
        RED,
    )
    after_frame = make_gif_frame(
        after,
        "HELIUM",
        "Helium turns the notch strip into browser chrome",
        "Tabs and controls wrap around the camera cutout, giving more vertical room back to the page.",
        GREEN,
    )

    frames: list[Image.Image] = []
    durations: list[int] = []

    frames.append(before_frame)
    durations.append(2400)
    for step in range(1, 8):
        alpha = step / 8
        frames.append(Image.blend(before_frame, after_frame, alpha))
        durations.append(80)
    frames.append(after_frame)
    durations.append(2600)
    for step in range(1, 8):
        alpha = step / 8
        frames.append(Image.blend(after_frame, before_frame, alpha))
        durations.append(80)

    paletted = [
        frame.quantize(colors=192, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        for frame in frames
    ]

    output.parent.mkdir(parents=True, exist_ok=True)
    paletted[0].save(
        output,
        save_all=True,
        append_images=paletted[1:],
        duration=durations,
        loop=0,
        disposal=2,
        optimize=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", required=True, type=Path)
    parser.add_argument("--after", required=True, type=Path)
    args = parser.parse_args()

    before_source = ASSETS / "source-before-fullscreen.png"
    after_source = ASSETS / "source-helium-notch-fullscreen.png"
    before_source.write_bytes(args.before.read_bytes())
    after_source.write_bytes(args.after.read_bytes())

    framed_before = ASSETS / "macbook-before-fullscreen-wider-notch.png"
    framed_after = ASSETS / "macbook-helium-notch-fullscreen-wider-notch.png"
    frame_screenshot(before_source, framed_before)
    frame_screenshot(after_source, framed_after)
    make_comparison(framed_before, framed_after, ASSETS / "macbook-notch-before-after-wider-notch.png")
    make_demo_gif(framed_before, framed_after, ASSETS / "helium-notch-fullscreen-demo.gif")


if __name__ == "__main__":
    main()
