"""Offline dynamic WeChat red-packet cover tools.

Publicly documented target specs are conservative; the current platform upload
form remains authoritative. Never confuse a dynamic cover with a cover story.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path

from PIL import Image

VIDEO_SIZE = (960, 1280)  # even 3:4 dimensions: required by H.264 yuv420p
COVER_FRAMES_SIZE = (957, 1278)
ORNAMENT_FRAMES_SIZE = (1053, 1746)
FPS = 24
VIDEO_LIMIT = 20_000_000
ZIP_LIMITS = {"cover": 50_000_000, "ornament": 20_000_000}
FRAME_SIZES = {"cover": COVER_FRAMES_SIZE, "ornament": ORNAMENT_FRAMES_SIZE}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".webm", ".mkv", ".gif", ".m4v", ".avi"}


@dataclass(frozen=True)
class Validation:
    path: str
    kind: str
    valid: bool
    issues: tuple[str, ...]
    details: dict


def _binary(executable: str) -> str:
    found = shutil.which(executable)
    if not found:
        raise RuntimeError(f"未找到 {executable}；请先安装 FFmpeg（包括 ffprobe）并将其加入 PATH")
    return found


def _run(cmd: list[str], *, timeout: int = 180) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                check=False, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("FFmpeg 命令超时，请检查源文件") from exc
    if result.returncode:
        raise RuntimeError("FFmpeg 处理失败：" + (result.stderr or result.stdout)[-1600:])
    return result.stdout


def _inspect(source: Path) -> dict:
    if not source.is_file():
        raise FileNotFoundError(source)
    output = _run([_binary("ffprobe"), "-v", "error", "-show_streams",
                   "-show_format", "-of", "json", str(source)])
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError("无法解析 ffprobe 输出") from exc


def _rate(value: str | None) -> float:
    try:
        return float(Fraction(value or "0"))
    except (ValueError, ZeroDivisionError):
        return 0.0


def check_video(source: str | Path) -> Validation:
    source = Path(source)
    info = _inspect(source)
    streams = [s for s in info.get("streams", []) if s.get("codec_type") == "video"]
    issues: list[str] = []
    warnings: list[str] = []
    if len(streams) != 1:
        issues.append("必须恰好有一条视频轨")
    video = streams[0] if streams else {}
    fmt = info.get("format", {})
    width = int(video.get("width", 0))
    height = int(video.get("height", 0))
    fps = _rate(video.get("avg_frame_rate") or video.get("r_frame_rate"))
    duration = float(video.get("duration") or fmt.get("duration") or 0)
    bitrate = int(video.get("bit_rate") or fmt.get("bit_rate") or 0)
    size = source.stat().st_size
    if source.suffix.lower() != ".mp4" or "mp4" not in str(fmt.get("format_name", "")).lower():
        issues.append("应为 MP4 容器")
    if video.get("codec_name") != "h264":
        issues.append("视频编码需为 H.264/AVC")
    if video.get("pix_fmt") != "yuv420p":
        issues.append("视频像素格式需为 yuv420p (4:2:0)")
    if not (0.95 <= duration <= 3.05):
        issues.append("动态封面时长应为 1–3 秒（容许 0.05 秒封装误差）")
    if fps <= 0 or fps > 30.01:
        issues.append("帧率必须大于 0 且不超过 30fps")
    if size > VIDEO_LIMIT:
        issues.append(f"视频不得超过 {VIDEO_LIMIT} 字节")
    if width < 1 or height < 1 or max(width, height) >= 4096:
        issues.append("分辨率无效或不低于 4K")
    if width and height and abs(width / height - 0.75) > 0.035:
        warnings.append("建议采用 3:4 竖版画面，当前画幅比例可能需要在平台重新裁切")
    if bitrate <= 0:
        warnings.append("无法确定视频码率，请在平台中核查")
    elif bitrate > 3_000_000:
        issues.append("视频码率超过 3000 kbit/s")
    if any(s.get("codec_type") == "audio" for s in info.get("streams", [])):
        warnings.append("存在音轨，建议移除；本项目转码输出不保留音轨")
    return Validation(str(source), "mp4", not issues, tuple(issues),
                      {"duration": round(duration, 3), "fps": round(fps, 3),
                       "width": width, "height": height, "bitrate": bitrate,
                       "bytes": size, "warnings": warnings})


def _duration_frames(duration: float) -> int:
    if not (1 <= duration <= 3):
        raise ValueError("动态素材时长必须在 1–3 秒之间")
    frames = round(duration * FPS)
    return min(72, max(24, frames))


def _source_type(source: Path) -> str:
    if not source.is_file():
        raise FileNotFoundError(source)
    if source.suffix.lower() in VIDEO_SUFFIXES:
        return "video"
    if source.suffix.lower() in IMAGE_SUFFIXES:
        with Image.open(source) as img:
            img.verify()
        return "still"
    raise ValueError(f"不支持的文件类型：{source.suffix}")


def _input_args(source: Path, start: float, source_type: str) -> list[str]:
    if start < 0:
        raise ValueError("--start 不能为负")
    if source_type == "still":
        if start:
            raise ValueError("静态图片不能指定 --start")
        return ["-loop", "1", "-framerate", str(FPS), "-i", str(source)]
    args = []
    if source.suffix.lower() == ".gif":
        args += ["-stream_loop", "-1"]
    if start:
        args += ["-ss", str(start)]
    return [*args, "-i", str(source)]


def render_motion(source: str | Path, destination: str | Path, *,
                  start: float = 0, duration: float = 3,
                  effect: str = "zoom") -> Validation:
    """Convert a Flow video/GIF or still image into a short cover MP4."""
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve():
        raise ValueError("源文件与输出文件不能相同")
    if destination.suffix.lower() != ".mp4":
        raise ValueError("动态封面必须输出 .mp4")
    if destination.exists():
        raise ValueError("输出文件已存在，拒绝覆盖")
    total_frames = _duration_frames(duration)
    if effect not in {"zoom", "none"}:
        raise ValueError("effect 应为 zoom 或 none")
    source_type = _source_type(source)
    width, height = VIDEO_SIZE
    base = (f"scale={width}:{height}:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop={width}:{height},setsar=1")
    if source_type == "still" and effect == "zoom":
        # A gentle movement on the original art, not an AI-generated animation.
        filt = (base + ",zoompan=z='min(zoom+0.00065,1.045)':"
                "x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':"
                f"d=1:s={width}x{height}:fps={FPS},format=yuv420p")
    else:
        filt = base + f",fps={FPS},format=yuv420p"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="hongbao-motion-") as tmp:
        temporary = Path(tmp) / "video.mp4"
        _run([_binary("ffmpeg"), "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
              *_input_args(source, start, source_type),
              "-vf", filt, "-frames:v", str(total_frames), "-an",
              "-c:v", "libx264", "-preset", "fast", "-b:v", "2100k",
              "-maxrate", "2800k", "-bufsize", "5600k",
              "-pix_fmt", "yuv420p", "-movflags", "+faststart",
              str(temporary)])
        report = check_video(temporary)
        if not report.valid:
            raise ValueError("生成的视频未通过检查：" + "；".join(report.issues))
        shutil.move(str(temporary), str(destination))
    return check_video(destination)


def make_poster(source: str | Path, destination: str | Path, at: float = 0.0) -> Path:
    source, destination = Path(source), Path(destination)
    if not source.is_file():
        raise FileNotFoundError(source)
    if destination.exists() or source.resolve() == destination.resolve():
        raise ValueError("封面预览文件已存在或与源文件相同")
    if destination.suffix.lower() != ".png":
        raise ValueError("预览帧请选择 .png 格式")
    if at < 0:
        raise ValueError("取帧时间不能为负数")
    destination.parent.mkdir(parents=True, exist_ok=True)
    _run([_binary("ffmpeg"), "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
          "-ss", str(at), "-i", str(source), "-frames:v", "1",
          "-update", "1", str(destination)])
    if not destination.is_file():
        raise RuntimeError("未能提取预览帧")
    return destination


def check_frames(source: str | Path, *, kind: str = "cover") -> Validation:
    if kind not in FRAME_SIZES:
        raise ValueError("kind 必须为 cover 或 ornament")
    source = Path(source)
    if not source.is_file():
        raise FileNotFoundError(source)
    issues: list[str] = []
    expected_size = FRAME_SIZES[kind]
    limit = ZIP_LIMITS[kind]
    size_bytes = source.stat().st_size
    if size_bytes > limit:
        issues.append(f"ZIP 超过 {limit} 字节限制")
    if not zipfile.is_zipfile(source):
        return Validation(str(source), kind, False, ("文件不是有效 ZIP",), {})
    with zipfile.ZipFile(source) as archive:
        infos = archive.infolist()
        if len(infos) < 24 or len(infos) > 72:
            issues.append("PNG 序列帧需为 24–72 张（24fps，1–3 秒）")
        if sum(f.file_size for f in infos) > 250_000_000:
            return Validation(str(source), kind, False,
                              ("ZIP 解压后文件总量超过安全上限",), {})
        expected_names = [f"{i:05d}.png" for i in range(1, len(infos) + 1)]
        names = [f.filename for f in infos]
        if names != expected_names:
            issues.append("帧必须按顺序以 00001.png 开始连续命名，不含目录或其他文件")
        # Guard against duplicates and unsafe entries before reading.
        if len(set(names)) != len(names) or any(
                not re.fullmatch(r"\d{5}\.png", n) for n in names):
            issues.append("帧名称不安全或存在重复")
        if not issues:
            for item in infos:
                try:
                    with archive.open(item) as contents:
                        with Image.open(contents) as frame:
                            if frame.format != "PNG" or frame.size != expected_size:
                                issues.append(f"{item.filename} 不是 {expected_size} 的 PNG")
                                break
                            if kind == "ornament":
                                alpha = frame.getchannel("A") if "A" in frame.getbands() else None
                                if alpha is None or alpha.getextrema()[0] >= 255:
                                    issues.append(f"{item.filename} 没有可见透明区，挂件必须有透明底")
                                    break
                except (OSError, ValueError, RuntimeError):
                    issues.append(f"{item.filename} 无法解码")
                    break
    return Validation(str(source), kind, not issues, tuple(issues),
                      {"frames": len(infos), "fps": FPS, "width": expected_size[0],
                       "height": expected_size[1], "bytes": size_bytes})


def render_frames(source: str | Path, destination: str | Path, *,
                  kind: str = "cover", start: float = 0.0,
                  duration: float = 3.0) -> Validation:
    if kind not in FRAME_SIZES:
        raise ValueError("kind 必须为 cover 或 ornament")
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve():
        raise ValueError("源文件与输出文件不能相同")
    if destination.suffix.lower() != ".zip":
        raise ValueError("序列帧必须输出 .zip")
    if destination.exists():
        raise ValueError("输出文件已存在，拒绝覆盖")
    frame_count = _duration_frames(duration)
    source_type = _source_type(source)
    width, height = FRAME_SIZES[kind]
    if kind == "ornament":
        video_filter = (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease:flags=lanczos,"
            f"format=rgba,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black@0,"
            f"fps={FPS},format=rgba")
    else:
        video_filter = (
            f"scale={width}:{height}:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop={width}:{height},fps={FPS}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="hongbao-frames-") as tmp:
        folder = Path(tmp)
        _run([_binary("ffmpeg"), "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
              *_input_args(source, start, source_type),
              "-vf", video_filter, "-frames:v", str(frame_count), "-an",
              "-start_number", "1", str(folder / "%05d.png")])
        frames = sorted(folder.glob("*.png"))
        if len(frames) != frame_count:
            raise ValueError(f"需要 {frame_count} 张序列帧，实际输出 {len(frames)} 张；源片段可能过短")
        temporary = folder / "frames.zip"
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED,
                             compresslevel=6) as archive:
            for frame in frames:
                archive.write(frame, arcname=frame.name)
        result = check_frames(temporary, kind=kind)
        if not result.valid:
            raise ValueError("序列帧未通过检查：" + "；".join(result.issues))
        shutil.move(str(temporary), str(destination))
    return check_frames(destination, kind=kind)
