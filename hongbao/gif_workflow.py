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


def import_chatgpt_gif(source: str | Path, directory: str | Path = "output/chatgpt", *,
                       duration: float = 3.0) -> dict:
    """One local step: save original GIF, transcode MP4 and create preview.

    Works only on a GIF explicitly downloaded by the user. Never reads a
    browser, session or web page. Existing output files are not overwritten.
    """
    import json
    import shutil
    import tempfile
    from datetime import datetime, timezone
    from dataclasses import asdict
    from .video import _duration_frames, check_video, make_poster

    src = Path(str(source).strip().strip('"').strip("'")).expanduser()
    gif = check_gif(src)
    if not gif.valid:
        raise ValueError("GIF 检查未通过：" + "；".join(gif.issues))
    _duration_frames(duration)
    folder = Path(directory).expanduser()
    original = folder / "original.gif"
    mp4 = folder / "dynamic.mp4"
    poster = folder / "poster.png"
    for path in (original, mp4, poster):
        if path.exists():
            raise ValueError(f"目标文件已存在，请使用新的 --output-dir，避免覆盖：{path}")
    manifest_path = folder / "job.json"
    manifest = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("mode") not in (None, "gif"):
            raise ValueError("当前目录属于静态图片任务，请指定新的 --output-dir")
    folder.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".hongbao-gif-", dir=folder) as tmp:
        stage = Path(tmp)
        staged_gif = stage / "original.gif"
        staged_mp4 = stage / "dynamic.mp4"
        staged_poster = stage / "poster.png"
        shutil.copy2(src, staged_gif)
        gif_to_mp4(staged_gif, staged_mp4, duration=duration)
        make_poster(staged_mp4, staged_poster)
        for staged, target in ((staged_gif, original), (staged_mp4, mp4),
                               (staged_poster, poster)):
            shutil.move(str(staged), str(target))
    report = check_video(mp4)
    manifest.update({
        "workflow": manifest.get("workflow", "chatgpt-web-handoff"),
        "mode": "gif",
        "status": "locally_converted",
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "original_gif": str(original.resolve()),
        "mp4": str(mp4.resolve()),
        "poster": str(poster.resolve()),
        "gif_frames": gif.details["frames"],
    })
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    return {
        "step": "import-gif",
        "gif": str(original.resolve()),
        "mp4": str(mp4.resolve()),
        "poster": str(poster.resolve()),
        "gif_check": asdict(gif),
        "video_check": asdict(report),
        "note": "仅完成本地视频处理，尚未上传或通过微信平台审核。",
    }
