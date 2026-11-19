"""Procedural, non-generative animation of a still red-packet cover.

Deterministic effects; no semantic segmentation or ChatGPT/Flow API required.
"""

from __future__ import annotations

import math
import random
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps

from .video import FPS, VIDEO_SIZE, Validation, _binary, _duration_frames, check_video, make_poster

PRESETS = (
    "zoom", "pan", "festive-glow", "sparkle", "petals",
    "lantern-sway", "cloud-drift", "parallax",
)


def _sample_base(image: Image.Image, width: int, height: int,
                 focus_x: float, focus_y: float) -> Image.Image:
    """Crop to 3:4 with overscan for motion (no stretching)."""
    return ImageOps.fit(
        image, (width, height), method=Image.Resampling.LANCZOS,
        centering=(focus_x, focus_y),
    )


def _frame_from_base(base: Image.Image, angle: float, preset: str,
                     intensity: float) -> Image.Image:
    width, height = VIDEO_SIZE
    sx = math.sin(angle)
    sy = math.cos(angle)
    midx, midy = base.width / 2, base.height / 2
    zoom = 1.0
    if preset in ("zoom", "festive-glow", "parallax"):
        zoom += 0.027 * intensity * (1.0 - math.cos(angle)) / 2.0
    cropw = width / zoom
    croph = height / zoom
    dx = (13 if preset in ("pan", "parallax") else 5) * intensity * sx
    dy = (7 if preset in ("pan", "parallax") else 3) * intensity * sy
    x0 = int(round(midx - cropw / 2 + dx))
    y0 = int(round(midy - croph / 2 + dy))
    x0 = max(0, min(x0, base.width - math.ceil(cropw)))
    y0 = max(0, min(y0, base.height - math.ceil(croph)))
    return base.crop((x0, y0, x0 + int(cropw), y0 + int(croph))).resize(
        VIDEO_SIZE, resample=Image.Resampling.BICUBIC,
    )


def _points(seed: int, count: int) -> list[tuple[float, float, float, float, float, float]]:
    rng = random.Random(seed)
    points = []
    for _ in range(count):
        # Place effects at side margins, away from central subjects/faces.
        x = rng.uniform(0.02, 0.22) if rng.random() < .5 else rng.uniform(.78, .98)
        points.append((x, rng.random(), rng.uniform(1.0, 4.0),
                       rng.random() * math.tau, rng.uniform(.55, 1.5),
                       rng.uniform(-1.0, 1.0)))
    return points


def _sparkles(frame: Image.Image, angle: float, intensity: float,
              points: list[tuple]) -> None:
    draw = ImageDraw.Draw(frame, "RGBA")
    w, h = frame.size
    for x, y, r, phase, speed, _ in points:
        pulse = max(0.0, math.sin(int(1 + round(speed)) * angle + phase))
        alpha = int(150 * intensity * pulse ** 3)
        if alpha < 8:
            continue
        px, py = int(x * w), int(y * h)
        radius = max(1, int(r * (0.7 + .4 * pulse)))
        color = (255, 218, 141, alpha)
        draw.ellipse((px-radius, py-radius, px+radius, py+radius), fill=color)
        if radius >= 2:
            draw.line((px-radius*2, py, px+radius*2, py), fill=color, width=1)
            draw.line((px, py-radius*2, px, py+radius*2), fill=color, width=1)


def _petals(frame: Image.Image, progress: float, angle: float,
            intensity: float, points: list[tuple]) -> None:
    draw = ImageDraw.Draw(frame, "RGBA")
    w, h = frame.size
    for x, y, r, phase, _, tilt in points:
        px = x * w + 22 * intensity * math.sin(angle + phase)
        # One complete vertical cycle per video loop, with offscreen wrap.
        py = ((y * 1.2 + 1.2 * progress) % 1.2) * (h + 120) / 1.2 - 60
        radius = 2.5 + r * 1.1 * intensity
        draw.ellipse((px-radius, py-radius*2, px+radius, py+radius*2),
                     fill=(249, 198, 202, int(140 * intensity)),
                     outline=(255, 229, 221, int(100 * intensity)), width=1)
        if tilt > 0:
            draw.line((px, py-radius, px+radius*1.3, py+radius),
                      fill=(255, 237, 228, int(120 * intensity)), width=1)


def _glow(frame: Image.Image, angle: float, intensity: float) -> Image.Image:
    w, h = frame.size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    strength = int(48 * intensity * (.55 + .45 * (1 + math.cos(angle)) / 2))
    draw.ellipse((-180, -160, 240, 250), fill=(250, 186, 76, strength))
    draw.ellipse((w-250, h-300, w+180, h+120), fill=(255, 209, 104, strength))
    layer = layer.filter(ImageFilter.GaussianBlur(65))
    return Image.alpha_composite(frame.convert("RGBA"), layer).convert("RGB")


def _clouds(frame: Image.Image, angle: float, intensity: float) -> Image.Image:
    w, h = frame.size
    clouds = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(clouds, "RGBA")
    offset = 35 * intensity * math.sin(angle)
    for i, (cx, cy, rx, ry) in enumerate((
        (25, h*.25, 175, 58), (w-15, h*.67, 160, 68),
        (60, h*.86, 180, 52), (w-35, h*.12, 125, 40),
    )):
        cx += offset * (1 if i % 2 == 0 else -1)
        draw.ellipse((cx-rx, cy-ry, cx+rx, cy+ry),
                     fill=(235, 237, 235, int(45 * intensity)))
    clouds = clouds.filter(ImageFilter.GaussianBlur(45))
    return Image.alpha_composite(frame.convert("RGBA"), clouds).convert("RGB")


def _lanterns(frame: Image.Image, angle: float, intensity: float) -> None:
    """Draw decorative moving lanterns; does not detect/animate original lanterns."""
    w, _ = frame.size
    draw = ImageDraw.Draw(frame, "RGBA")
    for side, phase in ((0, 0), (1, 1.6)):
        origin_x = int(w*(.12 if side == 0 else .88))
        top_y = 50 if side == 0 else 110
        sway = int(14 * intensity * math.sin(angle + phase))
        x, y = origin_x + sway, top_y
        body_w, body_h = 29, 43
        draw.line((origin_x, 0, x, y+10), fill=(255, 214, 144, 130), width=2)
        draw.ellipse((x-body_w, y, x+body_w, y+body_h*2),
                     fill=(194, 40, 40, int(210*intensity)),
                     outline=(255, 196, 103, int(190*intensity)), width=3)
        draw.line((x, y, x, y+body_h*2),
                  fill=(249, 189, 97, 160), width=2)
        draw.line((x, y+body_h*2, x, y+body_h*2+27),
                  fill=(255, 187, 81, 190), width=2)


def _make_parallax_mask(size: tuple[int, int]) -> Image.Image:
    w, h = size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((int(.2*w), int(.18*h), int(.8*w), int(.84*h)), fill=240)
    return mask.filter(ImageFilter.GaussianBlur(65))


def render_animated_cover(source: str | Path, destination: str | Path, *,
                          preset: str = "festive-glow", duration: float = 3.0,
                          intensity: float = .55, seed: int = 7,
                          focus_x: float = .5, focus_y: float = .5,
                          fps: int = FPS, poster: str | Path | None = None) -> Validation:
    """Make an MP4 from a still. Refuses to overwrite and validates before delivery."""
    src, dst = Path(source).expanduser(), Path(destination).expanduser()
    if preset not in PRESETS:
        raise ValueError(f"未知动画预设 {preset!r}；可选：{', '.join(PRESETS)}")
    if not (0 <= intensity <= 1):
        raise ValueError("--intensity 必须介于 0 和 1 之间")
    if not (0 <= focus_x <= 1 and 0 <= focus_y <= 1):
        raise ValueError("--focus-x / --focus-y 必须介于 0 和 1 之间")
    if fps != FPS:
        raise ValueError(f"为确保规范，当前只支持 {FPS} fps")
    total_frames = _duration_frames(duration)
    if not src.is_file():
        raise FileNotFoundError(src)
    if src.resolve() == dst.resolve() or dst.suffix.lower() != ".mp4":
        raise ValueError("输出应为不同于输入文件的 .mp4 文件")
    if dst.exists():
        raise ValueError("输出文件已存在，拒绝覆盖")
    if poster is not None:
        poster = Path(poster).expanduser()
        if (poster.suffix.lower() != ".png" or poster.exists()
                or poster.resolve() in (src.resolve(), dst.resolve())):
            raise ValueError("--poster 必须是不存在且与原图/视频不同路径的 .png")
    _binary("ffmpeg")
    _binary("ffprobe")
    try:
        with Image.open(src) as raw:
            original = ImageOps.exif_transpose(raw).convert("RGB")
            overscan = _sample_base(original, int(VIDEO_SIZE[0]*1.07),
                                    int(VIDEO_SIZE[1]*1.07), focus_x, focus_y)
    except OSError as exc:
        raise ValueError("无法读取静态图片；请提供有效的 PNG、JPEG 或 WebP") from exc
    pixels = _points(seed, 18)
    w, h = VIDEO_SIZE
    mask = _make_parallax_mask(VIDEO_SIZE) if preset == "parallax" else None
    dst.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".hongbao-animate-", dir=dst.parent) as tmp:
        staging = Path(tmp) / "dynamic.mp4"
        log_path = Path(tmp) / "ffmpeg.log"
        command = [
            _binary("ffmpeg"), "-hide_banner", "-loglevel", "error", "-nostdin",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
            "-r", str(FPS), "-i", "pipe:0", "-an",
            "-c:v", "libx264", "-preset", "veryfast", "-b:v", "1800k",
            "-maxrate", "2700k", "-bufsize", "5400k", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", "-frames:v", str(total_frames), str(staging),
        ]
        with log_path.open("wb") as log:
            proc = subprocess.Popen(command, stdin=subprocess.PIPE,
                                    stdout=subprocess.DEVNULL, stderr=log)
            try:
                assert proc.stdin is not None
                for index in range(total_frames):
                    progress = index / total_frames
                    angle = 2 * math.pi * progress
                    frame = _frame_from_base(overscan, angle, preset, intensity)
                    if preset == "parallax":
                        back = _frame_from_base(
                            overscan, angle + math.pi, "pan", intensity * .4,
                        )
                        frame = Image.composite(frame, back, mask)
                    if preset == "festive-glow":
                        frame = _glow(frame, angle, intensity)
                        _sparkles(frame, angle, intensity*.75, pixels)
                    elif preset == "sparkle":
                        _sparkles(frame, angle, intensity, pixels)
                    elif preset == "petals":
                        _petals(frame, progress, angle, intensity, pixels)
                    elif preset == "cloud-drift":
                        frame = _clouds(frame, angle, intensity)
                    elif preset == "lantern-sway":
                        _lanterns(frame, angle, intensity)
                    proc.stdin.write(frame.tobytes())
                proc.stdin.close()
                code = proc.wait(timeout=180)
            except (BrokenPipeError, OSError, subprocess.TimeoutExpired) as exc:
                proc.kill()
                proc.wait()
                raise RuntimeError("FFmpeg 无法完成动画编码") from exc
            except BaseException:
                proc.kill()
                proc.wait()
                raise
        if code:
            raise RuntimeError("FFmpeg 编码失败：" + log_path.read_text(errors="replace")[-2000:])
        result = check_video(staging)
        if not result.valid:
            raise ValueError("动画未通过视频规范校验：" + "；".join(result.issues))
        if poster is not None:
            staged_poster = Path(tmp) / "poster.png"
            make_poster(staging, staged_poster)
            poster.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(staged_poster), str(poster))
        shutil.move(str(staging), str(dst))
    final = check_video(dst)
    return Validation(final.path, final.kind, final.valid, final.issues,
                      {**final.details, "preset": preset, "intensity": intensity,
                       "seed": seed, "generated_from_still": True,
                       "animation_type": "procedural"})
