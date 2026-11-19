"""Image preparation and offline checks. This is not platform-side approval."""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

TARGET = (957, 1278)
MAX_BYTES = 500_000


@dataclass(frozen=True)
class CheckResult:
    path: str
    width: int
    height: int
    format: str
    size_bytes: int
    valid: bool
    issues: tuple[str, ...]


def check_cover(path: str | Path, max_bytes: int = MAX_BYTES) -> CheckResult:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    issues: list[str] = []
    with Image.open(path) as img:
        img.verify()
    with Image.open(path) as img:
        width, height = img.size
        file_format = img.format or "unknown"
    size_bytes = path.stat().st_size
    if (width, height) != TARGET:
        issues.append(f"尺寸应为 {TARGET[0]}x{TARGET[1]}，实际 {width}x{height}")
    if file_format != "JPEG":
        issues.append(f"格式应为 JPEG，实际 {file_format}")
    if size_bytes > max_bytes:
        issues.append(f"图片过大：{size_bytes} > {max_bytes} 字节")
    return CheckResult(str(path), width, height, file_format, size_bytes, not issues, tuple(issues))


def export_cover(source: str | Path, destination: str | Path,
                 focus_x: float = 0.5, focus_y: float = 0.5,
                 max_bytes: int = MAX_BYTES) -> CheckResult:
    if not (0.0 <= focus_x <= 1.0 and 0.0 <= focus_y <= 1.0):
        raise ValueError("focus_x/focus_y 需要在 0 与 1 之间")
    if max_bytes < 10_000:
        raise ValueError("max_bytes 太小，无法合理导出")
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve():
        raise ValueError("输入和输出不能是同一个文件")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as raw:
        img = ImageOps.exif_transpose(raw).convert("RGBA")
        canvas = Image.new("RGBA", img.size, "white")
        canvas.alpha_composite(img)
        final = ImageOps.fit(canvas.convert("RGB"), TARGET,
                             method=Image.Resampling.LANCZOS,
                             centering=(focus_x, focus_y))

    encoded = None
    for quality in range(94, 24, -3):
        buf = io.BytesIO()
        final.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
        if buf.tell() <= max_bytes:
            encoded = buf.getvalue()
            break
    if encoded is None:
        raise ValueError("无法在大小限制内保证可用 JPEG；请降低原图复杂度")
    destination.write_bytes(encoded)
    return check_cover(destination, max_bytes=max_bytes)


def make_preview(source: str | Path, destination: str | Path) -> Path:
    """Non-official illustrative UI overlay, never an upload file."""
    destination = Path(destination)
    if Path(source).resolve() == destination.resolve():
        raise ValueError("预览必须另存为单独文件")
    with Image.open(source) as raw:
        img = ImageOps.exif_transpose(raw).convert("RGB")
        img = ImageOps.fit(img, TARGET, method=Image.Resampling.LANCZOS)
    base = img.convert("RGBA")
    ui = Image.new("RGBA", TARGET, (0, 0, 0, 0))
    draw = ImageDraw.Draw(ui, "RGBA")

    # Simple illustrative obscuration zones, deliberately not a copy of WeChat UI
    draw.rounded_rectangle((50, 60, 907, 262), radius=32, fill=(15, 10, 10, 135))
    draw.ellipse((82, 105, 180, 203), fill=(245, 233, 215, 240))
    draw.rounded_rectangle((212, 120, 650, 146), radius=8, fill=(255, 255, 255, 140))
    draw.rounded_rectangle((212, 170, 780, 188), radius=6, fill=(255, 255, 255, 90))
    draw.rounded_rectangle((240, 1025, 717, 1180), radius=78, fill=(190, 45, 40, 230))
    draw.ellipse((449, 1056, 508, 1115), fill=(255, 211, 115, 255))
    draw.rectangle((0, 1232, TARGET[0], TARGET[1]), fill=(25, 22, 22, 200))
    font = ImageFont.load_default()
    draw.text((20, 1246), "SIMULATION - NOT FOR UPLOAD", font=font, fill=(255, 255, 255, 255))
    base = Image.alpha_composite(base, ui).convert("RGB")
    destination.parent.mkdir(parents=True, exist_ok=True)
    base.save(destination, "PNG")
    return destination
