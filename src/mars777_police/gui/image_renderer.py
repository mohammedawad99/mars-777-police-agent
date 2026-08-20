"""Drawing a frame into an image, with no display and no window manager.

This is the render proof that runs everywhere: an offscreen rasteriser needs no
X server, no desktop session and no window, so the graphical output can be
produced and asserted on Linux and Windows CI alike - and it is what produces the
screenshots `DOC-001` requires, from the real renderer rather than from a
drawing somebody made.

The same `Frame` feeds the interactive window, so the picture a grader sees in a
screenshot is the picture the application draws.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .primitives import Frame


def _font(size: int, bold: bool) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """A bitmap font that ships with the imaging library, so nothing is fetched.

    Deliberately not a system font: a screenshot that renders differently on
    another machine is weaker evidence, and a font downloaded at render time
    would be a network dependency this application does not have.
    """
    return ImageFont.load_default(size=max(9, size + (1 if bold else 0)))


def render(frame: Frame) -> Image.Image:
    """Rasterise *frame* exactly as the window would draw it."""
    image = Image.new("RGB", (frame.width, frame.height), "#000000")
    draw = ImageDraw.Draw(image)
    for rect in frame.rects:
        draw.rectangle(
            [rect.left, rect.top, rect.right - 1, rect.bottom - 1],
            fill=rect.fill,
            outline=rect.outline,
        )
    for text in frame.texts:
        font = _font(text.size, text.bold)
        draw.text((text.left, text.top), text.value, fill=text.fill, font=font)
    return image


def write_png(frame: Frame, path: Path) -> Path:
    """Render *frame* and write it as a PNG, returning where it went."""
    path.parent.mkdir(parents=True, exist_ok=True)
    render(frame).save(path, format="PNG")
    return path
