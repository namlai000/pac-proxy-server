"""Generate icon.ico used as the exe icon (PyInstaller --icon)."""

from pathlib import Path

from PIL import Image, ImageDraw

SIZES = [16, 24, 32, 48, 64, 128, 256]


def draw_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pad = max(1, size // 16)
    draw.pieslice(
        (pad, pad, size - pad, size - pad),
        start=35,
        end=325,
        fill=(255, 187, 0, 255),
        outline=(140, 85, 0, 255),
        width=max(1, size // 32),
    )
    eye = max(2, size // 10)
    cx, cy = int(size * 0.52), int(size * 0.28)
    draw.ellipse((cx - eye, cy - eye, cx + eye, cy + eye), fill=(60, 40, 0, 255))
    return img


def main() -> None:
    target = Path(__file__).resolve().parent / "icon.ico"
    images = [draw_icon(size) for size in SIZES]
    images[-1].save(target, format="ICO", sizes=[(s, s) for s in SIZES])
    print(f"Wrote {target}")


if __name__ == "__main__":
    main()
