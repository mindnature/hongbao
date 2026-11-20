"""GIF-first dynamic red-packet cover workflow.

Validates actual animation frames before reusing the existing MP4 transcoder.
No website scraping or API calls.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageSequence, UnidentifiedImageError
from .video import Validation, render_motion

def check_gif(source: str | Path) -> Validation:
    path = Path(source).expanduser()
    if not path.is_file():
        raise FileNotFoundError(path)
    issues: list[str] = []
    if path.suffix.lower() != ".gif":
        issues.append("请提供 .gif 动画文件")
    frames = 0
    width = height = duration_ms = 0
    try:
        with Image.open(path) as gif:
            if gif.format != "GIF":
                issues.append("文件内容不是 GIF")
            width, height = gif.size
            frames = getattr(gif, "n_frames", 1)
            if frames < 2:
                issues.append("GIF 只有一帧；请下载真正的多帧 GIF，或使用 animate")
            elif frames > 400:
                issues.append("GIF 超过 400 帧；请先缩短动画")
            if frames <= 400:
                for frame in ImageSequence.Iterator(gif):
                    frame.load()
                    duration_ms += int(frame.info.get("duration") or 0)
    except (UnidentifiedImageError, OSError, ValueError, EOFError) as exc:
        issues.append(f"无法完整解码 GIF：{exc}")
    if frames > 1 and duration_ms <= 0:
        issues.append("GIF 不包含有效播放时长")
    if width <= 0 or height <= 0:
        issues.append("GIF 尺寸无效")
    return Validation(str(path), "gif", not issues, tuple(issues),
                      {"frames": frames, "width": width, "height": height,
                       "duration_seconds": round(duration_ms / 1000, 3),
                       "bytes": path.stat().st_size})

def gif_to_mp4(source: str | Path, destination: str | Path, *,
               duration: float = 3.0) -> Validation:
    gif = check_gif(source)
    if not gif.valid:
        raise ValueError("GIF 检查未通过：" + "；".join(gif.issues))
    result = render_motion(source, destination, duration=duration, effect="none")
    if not result.valid:
        raise ValueError("MP4 校验未通过：" + "；".join(result.issues))
    return Validation(result.path, "mp4", True, (),
                      {**result.details, "source_format": "GIF",
                       "gif_frames": gif.details["frames"],
                       "gif_duration_seconds": gif.details["duration_seconds"]})
